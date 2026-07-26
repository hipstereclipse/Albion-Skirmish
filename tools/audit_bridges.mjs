import { spawn } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const root = path.resolve(import.meta.dirname, '..');
const edge = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'eldervale-bridge-audit-'));
const port = 9241 + Math.floor(Math.random() * 200);
const browser = spawn(edge, [
  '--headless=new', '--disable-gpu', '--hide-scrollbars',
  `--remote-debugging-port=${port}`, `--user-data-dir=${profile}`,
  pathToFileURL(path.join(root, 'index.html')).href,
], { stdio: 'ignore', windowsHide: true });
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));

let ws;
try {
  let target;
  for (let attempt = 0; attempt < 100 && !target; attempt++) {
    try {
      const targets = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
      target = targets.find(item => item.type === 'page' && item.url.includes('index.html'));
    } catch {}
    if (!target) await delay(100);
  }
  if (!target) throw new Error('Edge DevTools endpoint did not become ready');
  ws = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => {
    ws.addEventListener('open', resolve, { once:true });
    ws.addEventListener('error', reject, { once:true });
  });
  let nextId = 1;
  const pending = new Map();
  const pageErrors = [];
  ws.addEventListener('message', event => {
    const message = JSON.parse(event.data);
    if (message.method === 'Runtime.exceptionThrown') pageErrors.push(message.params.exceptionDetails.text || 'Uncaught exception');
    if (!message.id || !pending.has(message.id)) return;
    const waiter = pending.get(message.id);
    pending.delete(message.id);
    if (message.error) waiter.reject(new Error(message.error.message)); else waiter.resolve(message.result);
  });
  const send = (method, params = {}) => new Promise((resolve, reject) => {
    const id = nextId++;
    pending.set(id, { resolve, reject });
    ws.send(JSON.stringify({ id, method, params }));
  });
  await send('Runtime.enable');
  for (let attempt = 0; attempt < 100; attempt++) {
    const ready = await send('Runtime.evaluate', {
      expression:"document.readyState === 'complete' && typeof startGame === 'function'",
      returnByValue:true,
    });
    if (ready.result.value) break;
    await delay(100);
  }

  const auditExpression = `(() => {
    const cases = [];
    const maps = ['greatwood', 'darkwood', 'barrowfields', 'brightwood', 'snowspire'];
    for (let n = 0; n < 20; n++) {
      $('opt-map').value = maps[n % maps.length];
      $('opt-map-size').value = n % 4 === 0 ? 'huge' : (n % 3 === 0 ? 'large' : 'standard');
      $('opt-lake-prevalence').value = n % 2 ? 'wetlands' : 'high';
      $('opt-lake-size').value = n % 3 ? 'large' : 'standard';
      $('opt-stream-density').value = 'wet';
      $('opt-road-density').value = n % 5 === 0 ? 'sparse' : 'dense';
      $('opt-seed').value = 'bridge-audit-' + n;
      startGame();
      appState = 'paused';
      const spans = (game.decor && game.decor.bridgeSpans) || [];
      let bridgeTiles = 0, dryBridgeTiles = 0, badSpanBanks = 0, emptySpans = 0;
      for (let ty = 0; ty < ROWS; ty++) for (let tx = 0; tx < COLS; tx++) {
        const i = tIdx(tx, ty);
        if (!game.bridges[i]) continue;
        bridgeTiles++;
        if (!game.water[i]) dryBridgeTiles++;
      }
      for (const sp of spans) {
        if (![sp.ax, sp.ay, sp.bx, sp.by].every(Number.isFinite)) { emptySpans++; continue; }
        if (game.water[tIdx(sp.ax, sp.ay)] || game.water[tIdx(sp.bx, sp.by)]) badSpanBanks++;
        let hit = false;
        const radius = (sp.halfWidth || .72) + .1;
        for (let ty = Math.max(0, Math.floor(Math.min(sp.ay, sp.by) - 2)); ty <= Math.min(ROWS - 1, Math.ceil(Math.max(sp.ay, sp.by) + 2)) && !hit; ty++) {
          for (let tx = Math.max(0, Math.floor(Math.min(sp.ax, sp.bx) - 2)); tx <= Math.min(COLS - 1, Math.ceil(Math.max(sp.ax, sp.bx) + 2)); tx++) {
            const i = tIdx(tx, ty);
            if (game.water[i] && game.bridges[i] && distanceToSegment(tx + .5, ty + .5, sp.ax + .5, sp.ay + .5, sp.bx + .5, sp.by + .5) <= radius) { hit = true; break; }
          }
        }
        if (!hit) emptySpans++;
      }
      const tcs = game.buildings.filter(b => b.type === 'towncenter' && !b.dead);
      const start = tcAccessTile(tcs[0]);
      const disconnected = tcs.slice(1).filter(tc => !landReachable(start, tcAccessTile(tc))).length;
      const canvas = document.createElement('canvas');
      canvas.width = MAPW; canvas.height = MAPH;
      drawBridgeDecksOn(canvas.getContext('2d'));
      cases.push({ seed:n, map:maps[n % maps.length], bridgeTiles, spans:spans.length,
        dryBridgeTiles, badSpanBanks, emptySpans, disconnected });
    }
    return cases;
  })()`;
  const response = await send('Runtime.evaluate', { expression:auditExpression, returnByValue:true, awaitPromise:true });
  if (response.exceptionDetails) throw new Error(response.exceptionDetails.text || 'Bridge audit evaluation failed');
  if (pageErrors.length) throw new Error(`Page errors: ${pageErrors.join(' | ')}`);
  const cases = response.result.value;
  const failed = cases.filter(item => item.dryBridgeTiles || item.badSpanBanks || item.emptySpans || item.disconnected);
  console.log(JSON.stringify({ cases:cases.length, failed, totals:cases.reduce((sum, item) => ({
    bridgeTiles:sum.bridgeTiles + item.bridgeTiles, spans:sum.spans + item.spans,
  }), { bridgeTiles:0, spans:0 }) }, null, 2));
  if (failed.length) process.exitCode = 1;
} finally {
  try { ws?.close(); } catch {}
  browser.kill();
  await delay(150);
  fs.rmSync(profile, { recursive:true, force:true });
}
