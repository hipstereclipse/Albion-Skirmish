import { spawn } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const root = path.resolve(import.meta.dirname, '..');
const edge = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const profile = path.join(root, '.edge-art-preview');
const output = path.join(root, 'docs', 'screenshots', 'fable-biome-animation-preview.png');
const port = 9237;

fs.mkdirSync(profile, { recursive: true });
const browser = spawn(edge, [
  '--headless=new',
  '--disable-gpu',
  '--hide-scrollbars',
  '--window-size=1600,900',
  `--remote-debugging-port=${port}`,
  `--user-data-dir=${profile}`,
  pathToFileURL(path.join(root, 'index.html')).href,
], { stdio: 'ignore', windowsHide: true });

const delay = ms => new Promise(resolve => setTimeout(resolve, ms));

async function targetInfo() {
  for (let attempt = 0; attempt < 80; attempt++) {
    try {
      const targets = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
      const page = targets.find(target => target.type === 'page' && target.url.includes('index.html'));
      if (page) return page;
    } catch {}
    await delay(100);
  }
  throw new Error('Edge DevTools endpoint did not become ready');
}

const target = await targetInfo();
const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((resolve, reject) => {
  ws.addEventListener('open', resolve, { once: true });
  ws.addEventListener('error', reject, { once: true });
});

let nextId = 1;
const pending = new Map();
const pageErrors = [];
ws.addEventListener('message', event => {
  const message = JSON.parse(event.data);
  if (message.method === 'Runtime.exceptionThrown') {
    pageErrors.push(message.params.exceptionDetails.text || 'Uncaught page exception');
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

await send('Page.enable');
await send('Runtime.enable');
await send('Log.enable');
for (let attempt = 0; attempt < 80; attempt++) {
  const ready = await send('Runtime.evaluate', {
    expression: "document.readyState === 'complete' && typeof startGame === 'function'",
    returnByValue: true,
  });
  if (ready.result.value) break;
  await delay(100);
}

const gallery = `(() => {
  document.querySelector('#opt-map').value = 'snowspire';
  startGame();
  appState = 'paused';
  game.units = [];
  game.buildings = [];
  game.nodes = [];
  game.sites = [];
  game.ambient = (game.ambient || []).filter(item => item.kind === 'worldNpc');
  game.byId = new Map();
  game.nodeGrid = new Array(NTILES).fill(null);
  game.buildingGrid = new Array(NTILES).fill(null);
  game.blocked = new Uint8Array(NTILES);
  const families = [
    ['temperate', TERRAIN_BY_KEY.meadow.id],
    ['forest', TERRAIN_BY_KEY.forest.id],
    ['marsh', TERRAIN_BY_KEY.marsh.id],
    ['dry', TERRAIN_BY_KEY.sand.id],
    ['snow', TERRAIN_BY_KEY.snow.id],
  ];
  const originX = 12, originY = 17;
  game.decor.groves = [];
  for (let familyIndex = 0; familyIndex < families.length; familyIndex++) {
    const [family, terrainId] = families[familyIndex];
    const bx = originX + familyIndex * 9;
    for (let ty = originY - 2; ty < originY + 9; ty++) {
      for (let tx = bx - 2; tx < bx + 7; tx++) {
        if (!inBounds(tx, ty)) continue;
        const index = tIdx(tx, ty);
        game.terrain.type[index] = terrainId;
        game.terrain.slope[index] = 0;
        game.water[index] = 0;
      }
    }
    const building = createBuilding('house', 0, bx, originY, true);
    building.visualBiome = family;
    createNode('wood', bx + 3, originY + 1, { visualBiome:family });
    createNode('food', bx + 1, originY + 4, { visualBiome:family });
    createNode(familyIndex % 2 ? 'iron' : 'gold', bx + 4, originY + 4, { visualBiome:family });
    game.decor.groves.push({
      x:tileCenter(bx + 4), y:tileCenter(originY + 7), r:T*.72, n:3,
      hue:familyIndex*.19, visualBiome:family,
    });
  }
  const unitTypes = ['villager','scout','settler','militia','archer','spearman','knight','mage','hero','acolyte','cavarcher','ballista','wolf','hobbeWild','balverine','ram','ship'];
  unitTypes.forEach((type, index) => {
    const col = index % 9, row = Math.floor(index / 9);
    const unit = createUnit(type, type === 'wolf' || type === 'hobbeWild' || type === 'balverine' ? CREEP_OWNER : 0,
      tileCenter(11 + col * 5), tileCenter(29 + row * 5));
    if (index % 4 === 1) unit.state = 'move';
    if (index % 4 === 2) {
      unit.state = 'attack';
      unit.cooldown = CONFIG.UNITS[type].attackCooldown * .5;
    }
  });
  terrainReady = false;
  game.mmDirty = true;
  game.camera.zoom = game.camera.targetZoom = .78;
  game.camera.x = 360;
  game.camera.y = 520;
  game.selection.length = 0;
  return { units:game.units.length, buildings:game.buildings.length, nodes:game.nodes.length };
})()`;

const result = await send('Runtime.evaluate', { expression: gallery, returnByValue: true, awaitPromise: true });
if (result.exceptionDetails) throw new Error(result.exceptionDetails.text || 'Gallery setup failed');
await delay(2200);
const audit = await send('Runtime.evaluate', {
  expression: `({
    unitAtlas:[ALBION_ART.units.naturalWidth, ALBION_ART.units.naturalHeight],
    resourceAtlas:[ALBION_ART.resources.naturalWidth, ALBION_ART.resources.naturalHeight],
    missingUnitRows:Object.keys(CONFIG.UNITS).filter(type => ALBION_ART.unitRows[type] == null),
    ambientNpcs:(game.ambient || []).filter(item => item.kind === 'worldNpc').length,
    visualBiomes:Array.from(new Set(game.buildings.map(buildingVisualBiome))).sort(),
    resourceBiomes:Array.from(new Set(game.nodes.slice(-15).map(node => node.visualBiome || terrainVisualFamilyAt(node.tx,node.ty)))).sort(),
  })`,
  returnByValue: true,
});
const shot = await send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false });
fs.writeFileSync(output, Buffer.from(shot.data, 'base64'));
if (pageErrors.length) throw new Error(`Page errors: ${pageErrors.join(' | ')}`);
console.log(`Captured ${path.relative(root, output)} ${JSON.stringify(result.result.value)}`);
console.log(`Audit ${JSON.stringify(audit.result.value)}`);

await send('Browser.close').catch(() => {});
ws.close();
browser.kill();
