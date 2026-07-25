# Overhaul progress tracker

Living state for the work specified in [OVERHAUL-PLAN.md](OVERHAUL-PLAN.md). **Any agent picking this
up should read the plan first, then this file, then start the first phase that is not `done`.**

After finishing a phase you must, in this order: (1) run its verification and log the numbers below,
(2) update the status table, (3) rewrite the `## Continuation prompt` section for the next phase,
(4) commit as `Overhaul phase <N>: <description>`, (5) `git push origin main`. Never skip the commit;
if the push fails, mark the row `done (push pending)` and say so in the log.

**Hard rule, every phase:** do not rename internal identifiers (`hobbeWild`, `balverine`, `demonDoor`,
`willhub`, `guildspire`, `ALBION_ART`, `CONFIG` keys) or localStorage keys (`albion.settings`,
`albion.save.N`). They are invisible to players and load-bearing for saves.

---

## Status

| Phase | Scope | Status | Commit subject | Date |
|---|---|---|---|---|
| Bootstrap | `.gitignore`, baseline commit of the 68 MB asset/`index.html` backlog, these two docs, push | **done, pushed** | `dd3e70a` Bootstrap the overhaul: baseline commit, gitignore, and shared plan docs | 2026-07-25 |
| 0 | Instrumentation: frame timing ring buffer + `?perf` HUD, capture BEFORE numbers | **done, pushed** | `Overhaul phase 0: add frame timing instrumentation and perf HUD` | 2026-07-25 |
| 1 | Kill the three-state terrain pop-in (single preload gate, all-or-nothing material gate) | pending | | |
| 2 | Fix dark/low-contrast terrain (brightness normalization, softer washes/outlines, painterly relayer) | pending | | |
| 3 | Asset weight: `tools/downscale_terrain.py`, 384²/512² re-export, delete 2 dead PNGs | pending | | |
| 4 | Render hot path: pre-baked tinted atlases, aura/glow sprites, `shadowBlur` purge, minimap 10 Hz, cached atmosphere, `MAX_DPR` 1.5, remove PixiJS | pending | | |
| 5 | Sim hot path: spatial hash for `applySeparation`, allocation-free A\* costs | pending | | |
| 6 | Clean IP rebrand: decouple preset-name regexes, rename display strings + asset files, disclaimer, grep gate | pending | | |
| 7 | End-to-end verification: perf A/B, load payload, art screenshots, save compat, offline | pending | | |

Phase 4 is large. It is fine to land it as sub-commits (`Overhaul phase 4a: …`) as long as each one
updates this doc and pushes.

---

## Baseline measurements

Captured in Phase 0. Everything later is measured against these.

**Rig:** Windows 11, AMD Radeon integrated (`ANGLE (AMD, AMD Radeon(TM) Graphics (0x00001638)
Direct3D11)`), Edge windowed 1600×900, canvas 1578×625 CSS at `dpr` 1.5. Map: Greatwood Crossing,
4 players (player + 3 enemy factions), default settings.

| Metric | Baseline | Target |
|---|---|---|
| Idle pan, avg frame ms (4-player map, 26-29 units) | **255.1 ms (3.9 fps)** | < 16.7 |
| Idle pan, p95 frame ms | **399.8 ms** (p50 233.3, max 949.9) | < 25 |
| ~100 v 100 battle (202 units), avg frame ms | **1006.9 ms (1.0 fps)** — p95 2433.4 | < 25 |
| `applySeparation` self-time per tick | **2.49 ms of a 3.05 ms tick (82%)**, 188 units | near zero |
| `buildTerrainBackdrop` calls per load | **7** (32 Mbps cold HTTP, game started immediately) | 1 |
| Total page payload, cache disabled | **49.5 MB over 20 requests** (`assets/` on disk is 68 MB) | ~15 MB |
| Visible terrain states during load | 3 (by inspection — not visually re-verified in Phase 0) | 2 |

**Read `frameMs` and `renderMs` with care.** Canvas rasterization happens off the JS timeline, so
main-thread work per frame measures 5-8 ms at idle while the actual frame interval is 255 ms. Worse,
the split moves: when the raster queue applies back-pressure the same work is attributed to JS, and
`renderMs` for an identical scene swung between 5 ms and 251 ms across runs. **The frame interval
(`deltaMs` / fps) is the only stable render metric** — which is why the HUD shows it.

### Where the time actually goes (Phase 0 attribution)

Neutralising `ctx.filter` and `shadowBlur` at the `CanvasRenderingContext2D.prototype` level, as a
throwaway console experiment, isolates the cost:

| State | Idle (25 units) | Battle (~200 units) |
|---|---|---|
| baseline | 3.2 fps | 1.0 fps |
| `ctx.filter` neutralised | **44.1 fps** | **13.5 fps** |
| `shadowBlur` neutralised | 3.8 fps | 1.5 fps |
| both neutralised | 37.0 fps | 11.0 fps |

`ctx.filter` is not merely the largest render cost, it is essentially the *only* one: removing it is
worth **~14x** at idle and **~13x** in battle, while `shadowBlur` is worth under 1.5x. With `render()`
stubbed entirely the loop runs at 52 fps, and a plain full-screen `drawImage` in a clean page holds
60 fps — so the machine and the environment are fine, and Phase 4.1/4.2 (pre-baked tinted atlases,
killing the per-entity filter) carry nearly all of the render win. Phase 4.4's `shadowBlur` purge is
real but small; do not expect it to move the headline number.

---

## Phase log

### Bootstrap — done 2026-07-25

**What changed**

- Added `.gitignore`: `.edge-art-preview/` (30 MB, 549 files — a browser-profile dump regenerated by
  `tools/capture_art_preview.mjs`), plus `__pycache__/`, `*.pyc`, and OS cruft.
- Committed the outstanding backlog as the baseline: modified `README.md`,
  `docs/screenshots/README.md`, and `index.html` (a 3278-line diff), plus the previously **untracked**
  `assets/` (68 MB), `tools/`, and 8 new screenshots.
- Added `docs/OVERHAUL-PLAN.md` (frozen spec) and this tracker.

**Findings worth carrying forward**

- The repo had only **9 tracked files**. `assets/` had never been committed, and `origin/main` was at
  `2e9b1fe` — 11 commits plus this entire backlog behind local. Whatever is deployed from GitHub was a
  much older build without the art. Worth confirming how the live site is actually deployed.
- Committing the baseline puts 68 MB of full-size PNGs in git history permanently. That is deliberate:
  Phase 3 overwrites the terrain textures in place, and the baseline is the only rollback. The working
  tree drops to ~15 MB after Phase 3; history keeps the originals.
- Grep-verified for Phase 3: `assets/art/albion-meadow.png` (3.2 MB) and
  `assets/sprites/albion-units.png` (1.4 MB) are referenced **nowhere** — safe to delete.
  `assets/sprites/albion-resources-v2.png` is referenced only by `tools/build_sprite_atlases.py:55`
  as a build input — keep it.
- Line-number anchors in the plan are valid as of this baseline commit and will drift as phases land.

**Verification**

- `git status` no longer lists `.edge-art-preview/`; working tree clean after the commit.
- Baseline commit `dd3e70a`; pushed `2e9b1fe..dd3e70a main -> main`, so `origin/main` now carries the
  full game including art for the first time.
- **Baseline line-number anchor: `dd3e70a`.** Any plan line number can be resolved exactly with
  `git show dd3e70a:index.html`.

### Phase 0 — done 2026-07-25

**What changed** (all in `index.html`, one commit, no Phase 1 work mixed in)

- **Frame timing ring buffer** in the main-loop section above `frame()`: `PERF_SAMPLES = 120` and a
  `perf` object holding five preallocated `Float64Array`s (`sim`, `render`, `frame`, `delta`, plus a
  `scratch` sort buffer). `perfSample()` writes by index and advances `head`; nothing allocates per
  frame. `frame()` times the sim `while` loop and the `render()` call with `performance.now()`.
- Helpers: `perfAvg`, `perfPct` (insertion sort into `scratch`, allocation-free), `perfUnitCount`,
  `perfReset`, and `perfStats()` — a console helper, since the script is a classic `<script>` so
  top-level functions are global. `perf.total` counts samples ever taken so a harness can pull the
  ring gap-free across polls.
- **Perf HUD** gated by `PERF_HUD = location.search.includes('perf')`, drawn from `drawPerfHUD()`
  right after the `renderMinimap()` call in `render()`. Five monospace lines below the top bar:
  avg/p95 of frame, sim and render, then fps with the mean interval, then the live unit count. The
  strings are rebuilt every 15 frames into a preallocated array so the HUD text stays readable.
- **Temporary** `console.count('buildTerrainBackdrop')` as the first line of `buildTerrainBackdrop()`,
  tagged `TEMP (phase 0)`. **Phase 1 must delete this line.**

**Deviation from the plan, deliberate:** the plan specified three buffers (`simMs`, `renderMs`,
`frameMs`). A fourth, `deltaMs`, was added, and it turned out to be the only trustworthy render
metric — see the note under the baseline table. It records the raw gap between frames *before* the
`delta > 0.25` clamp; recording it after the clamp made every slow frame read as exactly 250 ms and
hid a 1007 ms battle frame entirely.

**Findings worth carrying forward**

1. **`ctx.filter` is the whole render problem** (~14x at idle, ~13x in battle — see the attribution
   table). This raises confidence in Phase 4.1/4.2 and lowers the expected value of Phase 4.4.
2. **JS-side timing under-reports render cost.** Do not judge Phase 4 by `renderMs`; judge it by fps.
3. **`applySeparation` is 82% of a sim tick** (2.49 ms of 3.05 ms at 188 units), which is a stronger
   case for Phase 5.1 than the plan assumed.
4. **The rebuild count is load-speed dependent.** Over a throttled 32 Mbps HTTP load with the game
   started immediately: **7** rebuilds. On a local `file://` load: **1** — every image decodes before
   the first frame, so the pop-in does not reproduce locally. Phase 1 must be verified over throttled
   HTTP (`python -m http.server` + CDP `Network.emulateNetworkConditions`), never from `file://`.
5. **Actual load payload is 49.5 MB over 20 requests**, not the 68 MB of `assets/` on disk — the rest
   are build inputs and the two dead PNGs. Phase 3's "~68 MB → ~15 MB" should be restated against the
   49.5 MB figure.
6. Sim work is small at idle (0.64 ms/frame) and only becomes visible in battle (22.9 ms/frame), and
   even that is inflated because a 1 fps frame runs 10 catch-up ticks. Per-tick cost is the honest
   sim metric.

**Verification**

- Syntax checked by extracting the inline script and running `node --check` — clean.
- Ran the instrumented build repeatedly under CDP with `Runtime.exceptionThrown` and error-level
  `Log.entryAdded` captured: **zero page errors** across all runs, with and without `?perf`.
- HUD confirmed by screenshot during a live 206-unit battle: all five lines render correctly below
  the top bar and the numbers track the fight.
- `console.count('buildTerrainBackdrop')` confirmed firing and counting (7 on a throttled load).
- Measurement harness (throwaway, kept out of the repo per the plan): drove Edge over CDP, set
  `#opt-enemies` to 3, called `startGame()`, panned by adding `KeyD`/`KeyA` to the `keys` set — the
  real `updateCamera` path — for 60 s, then spawned 100 v 100 through the game's own `createUnit`
  and measured 30 s of combat. Samples were pulled gap-free via `perf.total`, so the avg/p95 are true
  over the whole window rather than over one 120-sample slice.

**Reproducing the battle stress test by hand** (per the plan, this snippet is not committed) — paste
into the console with a game running:

```js
(() => { const cam=game.camera, cx=cam.x+visibleWorldW()/2, cy=cam.y+visibleWorldH()/2;
  const roster=['militia','archer','spearman','knight'];
  for (let i=0;i<100;i++) for (const owner of [0,1]) {
    const side=owner===0?-1:1, col=i%10, row=Math.floor(i/10);
    const u=createUnit(roster[(i+owner)%roster.length], owner,
      cx+side*(T*3+col*T*0.9), cy-T*4.5+row*T*0.9);
    u.autoCombat='aggressive'; }
  return game.units.length; })()
```

Then read `perfStats()` in the console, or load with `?perf` for the HUD. The `ctx.filter`
attribution experiment used this prototype patch, also console-only:

```js
const d=Object.getOwnPropertyDescriptor(CanvasRenderingContext2D.prototype,'filter');
Object.defineProperty(CanvasRenderingContext2D.prototype,'filter',
  {configurable:true, get:d.get, set(v){ d.set.call(this,'none'); }});
```

---

## Continuation prompt

Copy this verbatim into a fresh agent/session to continue the work.

```
Continue the Albion Skirmish overhaul in c:\Users\Eclipse\.claude\Workspaces\Age Of Empires.

Read docs/OVERHAUL-PLAN.md (the full frozen spec) and docs/OVERHAUL-PROGRESS.md (status, baseline
numbers, phase log) before touching anything. Bootstrap and Phase 0 are complete and pushed:
frame-timing instrumentation, a ?perf HUD, perfStats() in the console, and a measured baseline are
all in place.

Execute **Phase 1 — Kill the three-state pop-in (load sequencing)** exactly as specified in the plan:
  - Replace the per-image onload handlers (baseline lines 1216-1228 — meadow, every ALBION_ART.terrain
    material, every ALBION_ART.transitions image, each currently setting terrainReady = false) with a
    single preloader: Promise.allSettled over all ALBION_ART images calling img.decode(). allSettled
    so one 404 cannot hang the game; decode() to force off-main-thread decode. On resolve set
    artReady = true; terrainReady = false; -> exactly one rebuild.
  - drawHexTerrainMaterials (baseline line 7244): make the gate all-or-nothing. Top becomes
    `if (!game.terrain || !artReady) return false;` and the return at 7319 becomes unconditional
    `true`, so the pattern cache builds once instead of partially.
  - Optionally notify('Painting the world…') in startGame() when !artReady.
  - REMOVE the temporary console.count('buildTerrainBackdrop') line from buildTerrainBackdrop() —
    but only after you have used it to verify the rebuild count dropped to 1.

Verification for this phase, and it matters how you run it: a local file:// load already shows only
1 rebuild because every image decodes before the first frame, so it proves nothing. You MUST verify
over throttled HTTP — `python -m http.server` plus CDP Network.emulateNetworkConditions at ~32 Mbps
with Network.setCacheDisabled, starting a game immediately after load. Baseline there is 7 rebuilds;
the target is 1. Also confirm only two visual states appear (painterly procedural backdrop, then one
clean swap to textures).

Baseline to beat (full detail in the progress doc): idle pan 255.1 ms avg / 399.8 ms p95 (3.9 fps) on
a 4-player Greatwood map; ~100v100 battle 1006.9 ms avg (1.0 fps); applySeparation 2.49 ms of a
3.05 ms sim tick; 49.5 MB over 20 requests; 7 terrain rebuilds per throttled load.

Carry-overs:
  - Plan line numbers are exact as of dd3e70a; Phase 0 added ~115 lines to index.html, all after
    line 7322, so anchors below that have shifted. Resolve with `git show dd3e70a:index.html` and
    confirm by reading the surrounding code before editing.
  - Judge render performance by fps / the HUD's interval line, NOT by frameMs or renderMs. Canvas
    raster runs off the JS timeline, so those two under-report badly and swing run to run.
  - ctx.filter is worth ~14x at idle and ~13x in battle; shadowBlur under 1.5x. That is Phase 4, not
    Phase 1 — do not start it early, but do not be surprised when Phase 1 and 2 barely move fps.
  - Do NOT rename internal ids or localStorage keys (breaks saves).
  - Do not mix Phase 2 changes into the Phase 1 commit.

When Phase 1 is done: log the results (actual rebuild count over throttled HTTP, plus whether the
two-state load holds) in docs/OVERHAUL-PROGRESS.md, flip the Phase 1 row to done, regenerate this
"Continuation prompt" section for Phase 2, commit as "Overhaul phase 1: single art preload gate,
one terrain rebuild", and push to origin main. Do not begin the next phase until the doc is updated
and pushed.
```
