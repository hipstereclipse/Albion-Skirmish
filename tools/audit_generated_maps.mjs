import { spawn } from 'node:child_process';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const root = path.resolve(import.meta.dirname, '..');
const edge = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const profile = path.join(root, '.edge-generation-audit');
const port = 9239;
const browser = spawn(edge, [
  '--headless=new', '--disable-gpu', '--hide-scrollbars',
  `--remote-debugging-port=${port}`,
  `--user-data-dir=${profile}`,
  pathToFileURL(path.join(root, 'index.html')).href,
], { stdio:'ignore', windowsHide:true });

const delay = ms => new Promise(resolve => setTimeout(resolve, ms));

async function pageTarget() {
  for (let attempt = 0; attempt < 100; attempt++) {
    try {
      const targets = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
      const page = targets.find(target => target.type === 'page' && target.url.includes('index.html'));
      if (page) return page;
    } catch {}
    await delay(100);
  }
  throw new Error('Edge DevTools endpoint did not become ready');
}

const target = await pageTarget();
const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((resolve, reject) => {
  ws.addEventListener('open', resolve, { once:true });
  ws.addEventListener('error', reject, { once:true });
});

let nextId = 1;
const pending = new Map();
const pageErrors = [];
ws.addEventListener('message', event => {
  const message = JSON.parse(event.data);
  if (message.method === 'Runtime.exceptionThrown') {
    pageErrors.push(message.params.exceptionDetails.exception?.description || message.params.exceptionDetails.text);
  }
  if (message.method === 'Log.entryAdded' && message.params.entry.level === 'error') {
    pageErrors.push(message.params.entry.text);
  }
  if (!message.id || !pending.has(message.id)) return;
  const { resolve, reject } = pending.get(message.id);
  pending.delete(message.id);
  if (message.error) reject(new Error(message.error.message));
  else resolve(message.result);
});

function send(method, params = {}) {
  const id = nextId++;
  return new Promise((resolve, reject) => {
    pending.set(id, { resolve, reject });
    ws.send(JSON.stringify({ id, method, params }));
  });
}

await send('Runtime.enable');
await send('Log.enable');
for (let attempt = 0; attempt < 100; attempt++) {
  const ready = await send('Runtime.evaluate', {
    expression:"document.readyState === 'complete' && typeof startGame === 'function'",
    returnByValue:true,
  });
  if (ready.result.value) break;
  await delay(100);
}

const auditSource = `(() => {
  const scenarios = [];
  for (const mapId of Object.keys(MAP_PRESETS)) {
    for (const seedText of ['crossing-11', 'crossing-29', 'crossing-47']) {
      scenarios.push({ mapId, seedText, lakePrevalence:'standard', lakeSize:'standard', streamDensity:'standard' });
    }
  }
  scenarios.push({ mapId:'darkwood', seedText:'wetlands-stress', lakePrevalence:'wetlands', lakeSize:'large', streamDensity:'wet' });

  const results = [];
  for (const scenario of scenarios) {
    document.querySelector('#opt-map').value = scenario.mapId;
    document.querySelector('#opt-seed').value = scenario.seedText;
    document.querySelector('#opt-lake-prevalence').value = scenario.lakePrevalence;
    document.querySelector('#opt-lake-size').value = scenario.lakeSize;
    document.querySelector('#opt-stream-density').value = scenario.streamDensity;
    document.querySelector('#opt-map-size').value = 'standard';
    document.querySelector('#opt-enemies').value = '1';
    startGame();
    appState = 'paused';

    const seen = new Uint8Array(NTILES);
    const components = [];
    for (let start = 0; start < NTILES; start++) {
      if (!game.water[start] || seen[start]) continue;
      let size = 0;
      const queue = [start];
      seen[start] = 1;
      for (let head = 0; head < queue.length; head++) {
        const cur = queue[head];
        size++;
        const tx = cur % COLS, ty = (cur / COLS) | 0;
        for (const d of [[1,0],[-1,0],[0,1],[0,-1]]) {
          const nx = tx + d[0], ny = ty + d[1];
          if (!inBounds(nx, ny)) continue;
          const ni = tIdx(nx, ny);
          if (!game.water[ni] || seen[ni]) continue;
          seen[ni] = 1;
          queue.push(ni);
        }
      }
      components.push(size);
    }
    components.sort((a, b) => b - a);
    let waterTiles = 0, bridgeTiles = 0, bridgeWithoutWater = 0;
    for (let i = 0; i < NTILES; i++) {
      waterTiles += game.water[i] ? 1 : 0;
      bridgeTiles += game.bridges[i] ? 1 : 0;
      if (game.bridges[i] && !game.water[i]) bridgeWithoutWater++;
    }
    const diagnostics = game.terrain?.diagnostics || {};
    results.push({
      ...scenario,
      waterRatio:+(waterTiles / NTILES).toFixed(4),
      bridgeTiles,
      bridgeWithoutWater,
      bridgeSpans:(game.decor?.bridgeSpans || []).length,
      components:components.slice(0, 8),
      connected:diagnostics.connected,
      resourceFair:diagnostics.resourceFair,
    });
  }
  return results;
})()`;

const evaluated = await send('Runtime.evaluate', { expression:auditSource, returnByValue:true });
if (evaluated.exceptionDetails) {
  throw new Error(evaluated.exceptionDetails.exception?.description || evaluated.exceptionDetails.text || 'Audit failed');
}
const results = evaluated.result.value;
const failures = [];
for (const result of results) {
  if (result.connected === false) failures.push(`${result.mapId}/${result.seedText}: disconnected starts`);
  if (result.bridgeWithoutWater) failures.push(`${result.mapId}/${result.seedText}: bridge outside water`);
  if (result.waterRatio <= 0 || result.waterRatio > .52) failures.push(`${result.mapId}/${result.seedText}: water ratio ${result.waterRatio}`);
  if (result.components.some(size => size < 2)) failures.push(`${result.mapId}/${result.seedText}: isolated water tile`);
}
if (pageErrors.length) failures.push(...pageErrors.map(error => `page: ${error}`));

console.log(JSON.stringify(results, null, 2));
await send('Browser.close').catch(() => {});
ws.close();
browser.kill();
if (failures.length) throw new Error(`Generated-map audit failed:\n${failures.join('\n')}`);
console.log(`Generated-map audit passed (${results.length} scenarios).`);
