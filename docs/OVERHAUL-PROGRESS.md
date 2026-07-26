# Overhaul progress tracker

Final state of the work specified in [OVERHAUL-PLAN.md](OVERHAUL-PLAN.md).

**This overhaul is finished.** Bootstrap and Phases 0-7 are all `done` and pushed, Phase 7 was the
last phase in the plan, and there is no continuation prompt — see [No further phases](#no-further-phases)
at the end of this file. What remains is a record: the per-phase logs below hold the measurements,
deviations and carry-over caveats, and the [Phase 7 log](#phase-7--done-2026-07-26) confirms the whole
thing end to end on the final build.

The execution protocol that governed each phase — run its verification, log actual numbers, update
the status table, rewrite the continuation prompt, commit as `Overhaul phase <N>: <description>`,
push — is kept in the plan for reference.

**Hard rule, and still true of the shipped code:** internal identifiers (`hobbeWild`, `balverine`,
`demonDoor`, `willhub`, `guildspire`, `ALBION_ART`, `CONFIG` keys) and localStorage keys
(`albion.settings`, `albion.save.N`) were never renamed. They are invisible to players and
load-bearing for saves; anything touching them in future must read the Phase 6 keep-list first.

---

## Status

| Phase | Scope | Status | Commit subject | Date |
|---|---|---|---|---|
| Bootstrap | `.gitignore`, baseline commit of the 68 MB asset/`index.html` backlog, these two docs, push | **done, pushed** | `dd3e70a` Bootstrap the overhaul: baseline commit, gitignore, and shared plan docs | 2026-07-25 |
| 0 | Instrumentation: frame timing ring buffer + `?perf` HUD, capture BEFORE numbers | **done, pushed** | `a0dd101` Overhaul phase 0: add frame timing instrumentation and perf HUD | 2026-07-25 |
| 1 | Kill the three-state terrain pop-in (single preload gate, all-or-nothing material gate) | **done, pushed** | Overhaul phase 1: single art preload gate, one terrain rebuild | 2026-07-25 |
| 2 | Fix dark/low-contrast terrain (brightness normalization, softer washes/outlines, painterly relayer) | **done, pushed** | Overhaul phase 2: brighten terrain and restore painterly character | 2026-07-25 |
| 3 | Asset weight: `tools/downscale_terrain.py`, 384²/512² re-export, delete 2 dead PNGs | **done, pushed** | Overhaul phase 3: shrink terrain asset payload | 2026-07-25 |
| 4a | Pre-baked owner-tinted unit atlases (half-res, no per-unit `ctx.filter`) | **done, pushed** | Overhaul phase 4a: pre-bake owner-tinted unit atlases | 2026-07-25 |
| 4b | Pre-baked biome building atlases + baked resource-variant atlases | **done, pushed** | Overhaul phase 4b: pre-bake biome building and resource atlases | 2026-07-25 |
| 4c | Aura sprites, `shadowBlur` purge | **done, pushed** | Overhaul phase 4c: pre-render building auras and purge shadowBlur | 2026-07-26 |
| 4d | Minimap 10 Hz entity cache, cached atmosphere, `MAX_DPR` 1.5, `ents` hoist | **done, pushed** | Overhaul phase 4d: cache the minimap entity layer and the atmosphere wash | 2026-07-26 |
| 4e | Remove PixiJS, canvas-native shore shimmer from precomputed `game.shoreTiles` | **done, pushed** | Overhaul phase 4e: remove PixiJS and draw the shore shimmer on canvas | 2026-07-26 |
| 5 | Sim hot path: spatial hash for `applySeparation`, allocation-free A\* costs | **done, pushed** | Overhaul phase 5: spatial-hash separation and allocation-free terrain costs | 2026-07-26 |
| 6 | Clean IP rebrand: decouple preset-name regexes, rename display strings + asset files, disclaimer, grep gate | **done, pushed** | Overhaul phase 6: rebrand to Eldervale Skirmish and decouple worldgen from display names | 2026-07-26 |
| 7 | End-to-end verification: perf A/B, load payload, art screenshots, save compat, offline, `MAX_DPR` | **done, pushed** | Overhaul phase 7: end-to-end verification and non-staling save slot labels | 2026-07-26 |

**The overhaul is complete.** All phases are `done` and pushed; there are no further phases. See the
[Phase 7 log](#phase-7--done-2026-07-26) for the final measured numbers and the
[closing note](#no-further-phases) at the end of this file.

Phase 4 was large and landed as five sub-commits (`4a`-`4e`), each with its own log entry below and
its own push.

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

**Every row above was re-verified on the final build in Phase 7** — see that log for the closing
numbers measured in one place on one harness.

**Four of these rows are superseded.** The rebuild count was fixed in Phase 1 (now 1) and the
payload in Phase 3 (**now 12.34 MiB over 20 requests**, `assets/` 25.62 MB on disk). The frame-time
rows were rewritten by Phase 4 (idle 14.34 → 34.88 fps, battle 2.27 → 32.84 fps against the Phase 3
baseline `b1b39d6` on the identical harness — see the Phase 4 summary; the Phase 0 absolutes above
came from a larger canvas and are not comparable).

The **`applySeparation` row is wrong, not merely stale.** Phase 5 re-measured the unmodified
pre-Phase-5 build with a direct micro-benchmark and got **0.11 ms of a 0.90 ms tick (~12%)**, not
2.49 ms of 3.05 ms (82%). The Phase 0 number came from a DevTools sampled profile, which carries
its own overhead and attributes inlined callee time to whatever frame it samples. Treat the
sampled attribution table below as directional only; where a function can be called in isolation,
benchmark it in isolation.

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

### Phase 1 — done 2026-07-25

**What changed** (Phase 1 only; no contrast or Phase 2 changes mixed in)

- Removed the independent meadow, terrain-material, and transition `onload` invalidations. One
  `Promise.allSettled` preloader now calls `decode()` for all 15 `ALBION_ART` images: the three sprite
  atlases, meadow, all eight material images, and all three transition images.
- Added the single `artReady` gate. Once every decode has either fulfilled or rejected, the
  preloader sets `artReady = true` and `terrainReady = false`, producing one art-triggered backdrop
  rebuild without allowing one failed image to hang startup.
- `drawHexTerrainMaterials()` now returns `false` unless both terrain data and the full art gate are
  ready. Once through the gate it builds the complete 8-material/3-transition pattern cache together
  and returns `true` unconditionally, so no partially textured frame can suppress the painterly
  fallback.
- Removed the Phase 0 `console.count('buildTerrainBackdrop')` instrumentation only after the
  throttled verification below succeeded. The throwaway CDP verification harness and its state
  captures were also kept out of the repository.

**Verification**

- Served the working tree with `python -m http.server` and launched Edge through CDP with
  `Network.setCacheDisabled`, service-worker bypass, and
  `Network.emulateNetworkConditions` at **32 Mbps** (4,194,304 bytes/s, 20 ms latency). After
  `document.readyState === 'complete'`, immediately started Greatwood with three enemy factions.
  Result: **exactly 1** console-counted `buildTerrainBackdrop` call, `artReady === true`, all
  **8 material patterns** and **3 transition patterns** present on that build, and zero page errors.
  The run transferred 51,770,429 encoded bytes over 18 local HTTP responses (49.37 MiB), consistent
  with the Phase 0 cold-load payload.
- Repeated as a stricter early-start stress run by calling `startGame()` at the first moment the
  script was callable, before the document finished loading. This deliberately preserved the
  loading transition: call 1 had `artReady === false` and rendered the complete painterly procedural
  backdrop; call 2 was the **single** art-triggered rebuild with all 8+3 patterns. Captured thumbnails
  were visually inspected: only those two states appeared, with one clean full-map swap and no bare
  or partially textured hex-grid state.
- Extracted the inline script and compiled it with Node after the code change; `git diff --check`
  also passed.

**Findings worth carrying forward**

1. With the documented post-load start timing, the art gate is already resolved and the raw backdrop
   call count is one. If a game is forced to start before load completion, the raw call count is two:
   the initial procedural build plus exactly one art-ready **rebuild**. That distinction is expected
   and is what preserves the painterly loading state without reintroducing partial textures.
2. Phase 1 added a net eight lines before `buildTerrainBackdrop()` after removing the temporary
   counter. Current anchors are `drawHexTerrainMaterials()` at line 7252 and
   `buildTerrainBackdrop()` at line 7330; continue to resolve anchors from `dd3e70a` and inspect
   surrounding code before editing.
3. No render-performance change is expected here. The Phase 0 fps baseline remains authoritative;
   Phase 4's per-entity `ctx.filter` removal is still the main performance win.

### Phase 2 — done 2026-07-25

**What changed** (Phase 2 only; no Phase 3 asset resizing or Phase 4 render work mixed in)

- Grouped the terrain-look knobs at the top of `buildTerrainBackdrop()`: the 384² material bake,
  64² luminance sample, 0.52 target, 0.95–1.4 brightness clamp, 1.05 saturation, elevation wash
  strengths, outline/transition alphas, and textured/fallback painterly strengths.
- Each of the eight material sources is now drawn once to a 384² offscreen canvas. A 64² thumbnail
  is read with `getImageData()` using Rec. 709 luma weights, then the material is redrawn through
  `brightness(k) saturate(1.05)` before `createPattern()`. The cache retains `k` in
  `hexMaterialPatternCache.brightnessFactors` for debugging.
- Kept the cream elevation highlight at `.18`, reduced the near-black low-elevation wash to `.09`,
  reduced hex outlines to `.035`, and reduced authored/generic transition strokes to `.48`/`.16`.
- The meadow soft-light overlay now also runs over authored materials at `.14` (`.26` on the
  procedural fallback). The 950-ellipse sun-dapple and 170-stroke painterly passes also run over
  textures at half strength. The per-tile grass, broad fallback color patches, and multiply
  shade-blob pass remain skipped over authored textures.
- Reduced the atmosphere vignette edge from `rgba(8,7,5,0.42)` to `rgba(8,7,5,0.20)`.
- Made `tools/capture_art_preview.mjs` genuinely repeatable by setting seed
  `overhaul-art-preview-v1`. Because the harness loads via `file://`, its Edge launch now explicitly
  allows same-file canvas access so Phase 2's required `getImageData()` audit can run. The harness
  also reports the seed, material factors, and final page-error count.

**Actual material brightness factors**

| Material | `k` |
|---|---:|
| meadow | 1.400000 |
| forest | 1.400000 |
| mud | 1.400000 |
| sand | 0.950000 |
| rock | 1.400000 |
| snow | 0.950000 |
| water | 1.400000 |
| road | 1.400000 |

**Verification**

- Inline script compilation via Node: **clean**. `tools/capture_art_preview.mjs` also passes
  `node --check`; `git diff --check` passes.
- Ran the seeded preview twice. Both captures produced SHA-256
  `A18190155AF45B9945F8323D891E0521502484D20B9CAB60BED065C898C84542`, proving the new seed and
  gallery are repeatable. The final CDP audit covered all five visual biomes, all eight material
  factors, and reported **0 page errors**.
- Screenshot checklist at the harness's default `.78` gallery zoom:
  - **Pass — no visible hex lattice:** uniform material fields do not show repeated honeycomb
    outlines; the stepped edges between intentionally different material bands remain readable.
  - **Pass — meadow reads green:** meadow/forest are clearly green rather than olive-black, while
    forest and mud remain darker than meadow.
  - **Pass — snow and sand retain detail:** both clamp at `k = .95`; surface grain, footprints, and
    painterly variation remain visible instead of clipping to white/flat cream.
  - **Pass — soft-light dapple remains visible:** low-strength mottling and the half-alpha ellipse/
    stroke accents remain visible above the material textures.
- The updated repeatable reference is
  `docs/screenshots/fable-biome-animation-preview.png`. No terrain PNG dimensions, deployed asset
  files, internal ids, or localStorage keys changed in this phase.

### Phase 3 — done 2026-07-25

**What changed** (assets and one new tool only; `index.html` was not touched in this phase)

- Added `tools/downscale_terrain.py` (Pillow, structured like `build_sprite_atlases.py`): module
  docstring, `ROOT`-relative paths, uppercase config constants, typed helpers, a `main()` that prints
  what it wrote, and `ValueError` on any validation failure.
- Re-exported the 8 `hex-*.png` materials and `albion-meadow-v2.png` at **384×384**, and the 3
  transitions at **512×512**, written in place with `optimize=True`. Relative paths unchanged.
- Deleted the two grep-confirmed dead deployed assets. Kept `albion-resources-v2.png` (build input).

**Tool command**

```
python tools/downscale_terrain.py
```

**Deviation from the plan, deliberate — palette reduction on the terrain sources.** The plan
specifies `optimize=True` with targets of ≤150 KB per material and ≤250 KB per transition. Truecolor
at the target dimensions lands at **291–301 KB per material and 543 KB per transition** — roughly 2×
over both budgets — so `optimize=True` alone cannot reach the stated targets, and the plan's own
"terrain payload ~43 MB → ~2 MB" headline is only reachable with a colour reduction (truecolor gives
~4.3 MB). A 256-colour median-cut + Floyd–Steinberg pass hits every stated number almost exactly.
`optimize=True` is still the write flag; it applies to palette PNGs equally, so this satisfies the
plan's method while also satisfying its budgets. The plan's "optional palette pass" bullet is scoped
to the *sprite atlases*, where alpha and gutter contracts make it risky; the terrain sources are
opaque RGB, which is the safe case. **Quality was gated, not assumed:** the tool measures PSNR
against the truecolor downscale both at authored exposure and under the runtime's own
`brightness(1.4)` lift (where banding would be amplified), and refuses to write below a 34 dB floor.
Every file cleared it. If the owner ever prefers truecolor over the budget, delete the palette ladder
and raise `MATERIAL_BUDGET` / `TRANSITION_BUDGET` to 320 KB / 560 KB.

Two robustness properties were added because this tool overwrites its own inputs: it **encodes and
validates every file before writing any of them** (an aborted run cannot leave a half-converted
tree), and it **skips sources already at the target size** (a second run cannot re-quantize an
existing reduction and lose a little more each time). Both were found the hard way — the first run
aborted on `meadow-mud.png` at 254.2 KB, 4 KB over budget, after nine files had already been written;
that is what motivated the two-phase write and the descending palette ladder.

**Before → after, per file** (bytes as written on disk)

| File | Dimensions | Before | After | Encoding | PSNR |
|---|---|---:|---:|---|---:|
| `assets/terrain/materials/hex-forest.png` | 1254² → 384² | 3,400,688 B | 147,958 B | palette256 | 40.4 dB |
| `assets/terrain/materials/hex-meadow.png` | 1254² → 384² | 3,309,683 B | 148,117 B | palette256 | 41.5 dB |
| `assets/terrain/materials/hex-mud.png` | 1254² → 384² | 3,538,874 B | 147,877 B | palette256 | 41.2 dB |
| `assets/terrain/materials/hex-road.png` | 1254² → 384² | 3,301,977 B | 148,241 B | palette256 | 44.8 dB |
| `assets/terrain/materials/hex-rock.png` | 1254² → 384² | 3,615,206 B | 148,123 B | palette256 | 42.1 dB |
| `assets/terrain/materials/hex-sand.png` | 1254² → 384² | 3,675,524 B | 148,391 B | palette256 | 47.9 dB |
| `assets/terrain/materials/hex-snow.png` | 1254² → 384² | 3,394,784 B | 147,927 B | palette256 | 48.1 dB |
| `assets/terrain/materials/hex-water.png` | 1254² → 384² | 3,095,697 B | 147,665 B | palette256 | 38.3 dB |
| `assets/art/albion-meadow-v2.png` | 1254² → 384² | 3,432,371 B | 147,825 B | palette256 | 38.6 dB |
| `assets/terrain/transitions/meadow-mud.png` | 1254² → 512² | 3,425,772 B | 253,626 B | palette224 | 39.2 dB |
| `assets/terrain/transitions/meadow-rock.png` | 1254² → 512² | 3,426,153 B | 250,775 B | palette224 | 37.2 dB |
| `assets/terrain/transitions/sand-water.png` | 1254² → 512² | 3,442,855 B | 253,221 B | palette256 | 36.6 dB |

Every material is **144.2–144.9 KB (target ≤150 KB)** and every transition **244.9–247.7 KB (target
≤250 KB)**. Terrain sources: **39.16 MB → 1.99 MB (94.9% smaller)**. Dimensions were re-verified
independently with PIL after the run, and again from the running page: `naturalWidth` is 384 for all
eight materials and the meadow, and 512 for all three transitions.

**Deletion verification**

| Deleted file | Dimensions | Bytes |
|---|---|---:|
| `assets/art/albion-meadow.png` | 1254×1254 | 3,296,679 B |
| `assets/sprites/albion-units.png` | 1448×1086 | 1,408,974 B |

Removed with `git rm`. A repo-wide grep for `albion-meadow\.png|albion-units\.png` (which cannot
match `albion-meadow-v2.png` or `albion-units-animated.png`) returns **no matches** outside the two
overhaul planning docs, and both paths are absent from the working tree. `albion-resources-v2.png` was
kept and is still referenced by `tools/build_sprite_atlases.py:55`.

**No sprite atlas was resized.** Re-verified after the run: `albion-units-animated.png` 1024×5120,
`albion-buildings.png` 1448×1086, `albion-resources-biomes.png` 1536×1280, and all
`assets/sprites/sources/*` unchanged. The live page audit still reports `unitAtlas [1024, 5120]` and
`resourceAtlas [1536, 1280]`, so `buildingSlices`, `unitCellSize: 256`, and `atlas-manifest.json`
remain valid. The optional lossless/palette pass on the sprite atlases was **not** taken — it was
optional and would not have helped the terrain payload goal.

**Payload — deployed vs. on-disk (recorded distinctly)**

| Measure | Before | After | Change |
|---|---:|---:|---|
| Cache-disabled HTTP payload | **51,909,473 B / 49.50 MiB over 20 requests** | **12,939,974 B / 12.34 MiB over 20 requests** | **−75.1%** |
| `assets/` on disk (working tree) | 70,538,554 B / 67.27 MB | 26,863,063 B / 25.62 MB | −61.9% |

The before run reproduces the Phase 0 baseline exactly (49.50 MiB / 20 requests), so the two runs are
directly comparable. Both were measured the same way: `python -m http.server` over the working tree,
Edge via CDP with `Network.setCacheDisabled` and service-worker bypass, summing `encodedDataLength`
from every `Network.loadingFinished`, waited out to `artReady === true`. The harness was throwaway and
is not committed. **Request count is unchanged at 20** — the two deleted PNGs were already dead, so
they were never requested; the deletion is a repo-size win, not a payload win. Payload is now under
the plan's ~15 MB target; the remaining bulk is the three sprite atlases plus the title vista
(9.7 MB of the 12.34 MB), which is Phase 4/6 territory.

**Post-resize brightness factors — unchanged from Phase 2**

| Material | `k` | Material | `k` |
|---|---:|---|---:|
| meadow | 1.4 | rock | 1.4 |
| forest | 1.4 | snow | 0.95 |
| mud | 1.4 | water | 1.4 |
| sand | 0.95 | road | 1.4 |

All eight are byte-identical to the Phase 2 values, which is the strongest available evidence that
the downscale preserved each material's mean luminance: the runtime re-measures luminance from a 64²
thumbnail on every load and independently arrived at the same clamps.

**Verification**

- Inline `index.html` script extracted and compiled with Node: **clean** (1 block, 10,745 lines).
  `node --check tools/capture_art_preview.mjs`: clean. `python -m py_compile` on both
  `tools/downscale_terrain.py` and `tools/build_sprite_atlases.py`: clean. `git diff --check`: clean.
- Seeded preview (`overhaul-art-preview-v1`) re-run twice; both captures hashed SHA-256
  `91A8C69D5E47266F5A738283C587A40F082F000E6D25082D0A77EFB1EDA7718C`, so the gallery is still
  repeatable. Audit covers all **8 material factors** and all **5 visual biomes**
  (`dry, forest, marsh, snow, temperate`) plus all 5 resource biomes, with **0 page errors**.
  The Phase 2 reference hashed `A18190155AF45B994...C84542`; the new hash is the Phase 3 reference.
- Screenshot checklist at the harness's default `.78` gallery zoom, re-inspected against Phase 2:
  - **Pass — no visible hex lattice:** uniform fields show no repeated honeycomb; only the intended
    stepped boundaries between different material bands remain.
  - **Pass — meadow reads green:** unchanged from Phase 2, still green rather than olive-black.
  - **Pass — snow and sand retain detail:** inspected at 2× on the two `k = .95` clamped materials,
    the worst case for banding. Snow keeps crystalline grain and blue-grey shading; sand keeps grain
    and track marks. No posterization, contouring, or flat-white clipping from the palette pass.
  - **Pass — soft-light dapple remains visible:** mottling and the half-alpha ellipse/stroke accents
    still read over the material textures.
- **Whole-frame diff against the Phase 2 reference: RMS 2.91, PSNR 38.86 dB.** Amplified 16×, the
  difference is uniform high-frequency dither noise with **no structure** — no tiling seams, no
  banding contours, no hex lattice. Sprites, buildings, units, roads and the HUD are pure black
  (bit-identical), independently confirming that only the terrain sources changed.
- Tool re-run on the converted tree: reports all 12 sources `unchanged` and leaves every byte
  untouched (verified via `git status --porcelain`), so the conversion is idempotent.
- One page error appears in **both** the before and after HTTP payload runs: a `favicon.ico` 404.
  It is pre-existing, unrelated to Phase 3, and does not appear in the `file://` art preview.

**Findings worth carrying forward**

1. **The plan's Phase 3 size targets implied a colour reduction.** `optimize=True` on truecolor
   cannot reach ≤150 KB / ≤250 KB at 384²/512²; the gap is ~2×. Recorded above with the quality gate
   used to justify the palette pass. If Phase 7's art check ever regresses, this is the knob.
2. **Phase 3 changed no rendering code and is not expected to move fps.** The Phase 0 baseline stands
   unchanged: idle pan 255.1 ms avg / 399.8 ms p95 (3.9 fps), battle 1006.9 ms avg (1.0 fps).
   `ctx.filter` remains the whole render problem and Phase 4.1/4.2 still carry the win.
3. **The remaining payload is sprite atlases, not terrain.** After this phase the three atlases plus
   the title vista are 9.7 MB of the 12.34 MB. Phase 4.1 bakes unit atlases at half resolution and
   Phase 6 renames the art files; a size pass on them belongs there, not here.
4. **Transition strips are now upsampled on the width axis.** The crop keeps 24% of the source width
   (512 → ~123 px) and redraws it into a fixed 192 px-wide canvas, so that axis went from a 0.64×
   downscale to a 1.56× upscale. At the authored `.48`/`.16` stroke alphas this is not visible in the
   seeded preview, but 512 is the floor for transitions — do not reduce them further.
5. **The meadow soft-light overlay now repeats ~7.5× across the 2880 px map instead of ~2.3×**, since
   its pattern is created at natural size. The seeded diff shows no resulting structure, but this is
   the first thing to check if a repeat ever becomes visible (plan risk #7 — bump to 512²).

### Phase 4a — done 2026-07-25

**What changed** (`index.html` only; items 2-9 of the plan's Phase 4 list are untouched)

- New pre-baked owner-tinted unit atlas section above `drawAnimatedAtlasFrame`: `UNIT_TINT_FILTERS`
  (five owner keys — 0-3 plus `CREEP_OWNER`), `UNIT_ATLAS_BAKE_SCALE = .5`, the `unitAtlasBakes`
  map, `bakeTintedUnitAtlases()` and `unitAtlasFor(owner)`. The Phase 1 preloader calls
  `bakeTintedUnitAtlases()` immediately before setting `artReady`.
- `drawAnimatedAtlasFrame` now takes `image` and `cell` as its first two parameters instead of
  hardcoding `ALBION_ART.units` / `ALBION_ART.unitCellSize`, and **no longer sets `ctx.filter`**.
  The `filter` parameter is gone.
- `drawAuthoredUnit` resolves `unitAtlasFor(u.owner)` and returns `false` when no bake exists; the
  five-branch per-unit filter string construction is deleted.
- `drawAmbientWorldNpc` resolves `unitAtlasFor(0)` and returns `false` when no bake exists.
- Contact shadows: the unit ellipse in `drawUnit` went `0.32 - stepLift*.035` →
  `0.38 - stepLift*.04`, and the world-NPC ellipse `.22` → `.28`, replacing the
  `drop-shadow(0px 2px 1px …)` term that the bake deliberately drops.

**Measured — same harness, same seed, both sides**

The Phase 0 headline baseline was captured on a 1578×625 canvas; this harness runs 1275×490, so its
absolute numbers are not comparable to the Phase 0 table. Both sides below were therefore re-measured
with the *same* harness: the "before" column is a `git worktree` checkout of the Phase 3 commit
`b1b39d6`, the "after" column is this commit, seed `overhaul-perf-v1`, Greatwood Crossing, 3 enemy
factions, 26 starting units, `dpr` 1.5, 60 s of continuous panning and 30 s of a 229-unit battle.

| Scenario | Before (b1b39d6) | After (4a) | Change |
|---|---|---|---|
| Idle pan, avg frame interval | 69.73 ms (**14.34 fps**) | 53.90 ms (**18.55 fps**) | **1.29x** |
| Idle pan, p95 | 133.3 ms | 100.1 ms | −25% |
| Battle (229 units), avg | 439.77 ms (**2.27 fps**) | 110.61 ms (**9.04 fps**) | **3.98x** |
| Battle, p95 | 549.9 ms | 116.9 ms | −79% |

Sample counts were 871 → 1124 (idle) and 70 → 278 (battle) over identical wall-clock windows, which
is the same result read a second way. Neither run was rAF-throttled (the harness now asserts this).

**Deviations from the plan, both deliberate**

1. **World NPCs share the owner-0 bake** rather than getting a sixth atlas. Their filter differed
   from owner 0 only by `brightness(1.04)` versus `brightness(1.03)`; a sixth ~5 MB atlas is not
   worth a difference of 0.01 in brightness.
2. **The lost drop-shadow is compensated by strengthening the *existing* `drawShadow()` ellipse**
   rather than adding a second one. Both call sites already drew a ground ellipse immediately before
   the sprite, so the plan's "restore it with `drawShadow()` before the blit" is satisfied by raising
   those two alphas — one fill instead of two.

**Verification**

- Bake audit in a live page: all five bakes are **512×2560 with cell 128** (source atlas 1024×5120,
  cell 256), **~25 MB** total. For every owner the baked pixels match a reference render of the
  source through the same filter string to within 1/255 per channel, and every bake differs from an
  untinted downscale — so the tint is provably applied and provably per-owner. 0 page errors.
- Seeded art preview (`overhaul-art-preview-v1`) re-run: **0 page errors**, all 8 material factors
  and all 5 visual biomes still reported, terrain factors byte-identical to Phase 2/3.
- Whole-frame diff of the seeded gallery against the same capture from `b1b39d6`: **RMS 0.90,
  PSNR 49.05 dB, 0.99% of pixels changed**, and every changed pixel lies between rows 212 and 620.
  Amplified 16×, the difference is *only* unit silhouettes and their ground ellipses — terrain,
  buildings, resource nodes, HUD and minimap are bit-identical black. At 5× magnification the
  half-resolution bake is visually indistinguishable from the full-resolution filtered draw.
- **New art-preview reference hash:** SHA-256
  `DA4CB1949E2EA363E41D585285125BD372715D5B615667DC0AC051BF7F2DE5A7`. The Phase 3 hash
  `91A8C69D5E4…` is superseded — unit rendering legitimately changed.
- Save/load round trip: started a seeded game, ran 400 sim ticks, added a building, saved to slot 3,
  **reloaded the page**, loaded the slot back. Fingerprint over 25 units, 8 buildings, 8 sites,
  31 ambient entities, age, resources, map id, seed and clock: **identical, 0 differing keys**,
  0 page errors. Slot cleaned up afterwards.
- Inline script extracted and `node --check`ed: clean (1 block). `git diff --check`: clean.

**Findings worth carrying forward**

1. **Battle got the predicted win; idle did not.** 3.98x in battle is in line with Phase 0's ~13x
   ceiling for all filter removal. Idle only moved 1.29x because the idle scene has 26 units but
   **324 resource nodes**, and `drawAuthoredResource` sets a *per-node* `ctx.filter` with its own
   `drop-shadow` term. That call site is **not in the plan's Phase 4 list** — it is the next-largest
   filter offender and now the idle bottleneck. Phase 4b picks it up alongside the buildings.
2. **`drawAuthoredUnit`'s readiness gate moved** from "the source image decoded" to "a bake exists".
   That is intentional: it makes an untinted frame impossible, and the fallback is the procedural
   sprite players already see while art decodes.
3. **Measure with an occlusion-proof browser.** A backgrounded Edge window stops firing rAF
   entirely, which shows up as a run that collects ~7% of the expected samples rather than as a slow
   run. `--disable-backgrounding-occluded-windows --disable-renderer-backgrounding
   --disable-background-timer-throttling` are required, and the harness now fails a run whose
   sample count implies throttling.

### Phase 4b — done 2026-07-25

Plan item 4.2 (biome building atlases) **plus an unplanned third bake family**: the per-node
`ctx.filter` in `drawAuthoredResource`, which Phase 4a's measurement identified as the actual idle
bottleneck. See the deviation note below.

**What changed** (`index.html` only)

- `bakeBiomeBuildingAtlases()` bakes the buildings atlas once per biome (`default`, `snow`,
  `forest`, `marsh`, `dry`) at **full resolution**, keyed by `buildingVisualBiome(b)`.
  `drawAuthoredBuilding` now selects the baked atlas instead of the caller setting `ctx.filter`.
- `bakeResourceVariantAtlases()` bakes the resources atlas into `RESOURCE_VARIANT_STEPS = 4`
  quantised variants at **0.75 scale** (cell 192). `drawAuthoredResource` picks the bucket from the
  node's existing hash and no longer sets `ctx.filter`.
- `drawAtlasCell` accepts an offscreen canvas (`naturalWidth || width`), since the bakes are
  canvases rather than `<img>`s.
- Contact shadows replacing the dropped `drop-shadow(0px 2px 2px …)` on nodes: a ground ellipse at
  `.3` for land nodes, and a lighter `.16` drifting one for fish, which sit on open water where a
  full-strength ellipse would read as a submerged rock.
- `RESOURCE_SIZE_BY_TYPE` hoisted to module scope — it was an object literal allocated per node per
  frame, ~324 allocations a frame on a standard map.
- The two remaining `ctx.filter` call sites are deliberate and documented in place: the
  construction-scaffold path and the procedural `drawBuildingBody` fallback have no atlas to bake a
  tint into.

**Measured — same harness, same seed as 4a**

| Scenario | b1b39d6 | after 4a | after 4b | 4b step | vs baseline |
|---|---|---|---|---|---|
| Idle pan, avg | 69.73 ms (14.34 fps) | 53.90 ms (18.55 fps) | **35.55 ms (28.13 fps)** | 1.52x | **1.96x** |
| Idle pan, p95 | 133.3 ms | 100.1 ms | **66.6 ms** | −33% | −50% |
| Battle (229 units), avg | 439.77 ms (2.27 fps) | 110.61 ms (9.04 fps) | **41.22 ms (24.26 fps)** | 2.68x | **10.67x** |
| Battle, p95 | 549.9 ms | 116.9 ms | **66.6 ms** | −43% | −88% |

Idle `renderMs` is now 1.23 ms avg and whole-`frame()` main-thread work 1.89 ms, so essentially all
remaining frame interval is raster and compositing rather than JS. Both idle and battle now sit on
clean vsync multiples (33.3 / 66.6 ms), i.e. the loop is missing a 60 Hz deadline rather than
grinding — that is what 4c/4d/4e have to close.

**Deviation from the plan, deliberate — a third bake family the plan does not list.**
The plan's Phase 4 list has exactly two pre-baked atlas items, units and buildings. Phase 4a's
measurement showed why that is not enough: the idle scene has 26 units but **324 resource nodes**,
and `drawAuthoredResource` set a *per-node* `ctx.filter`. After 4a it was the largest remaining
filter cost in the game, and idle had moved only 1.29x. Baking it is the same technique the plan
already sanctions twice, applied to the call site the plan missed; without it, "remove the per-entity
`ctx.filter`" would have been left three-quarters done. The one wrinkle is that the resource filter
is a *continuous* per-node hash rather than a fixed per-owner or per-biome tint, so it is quantised
into 4 buckets — adjacent buckets differ by 0.03 saturation and 0.02 brightness.

**Verification**

- Bake audit in a live page, 0 page errors:
  - **Units** — 5 bakes, 512×2560, cell 128, ~25 MB (unchanged from 4a).
  - **Buildings** — 5 bakes, **1448×1086, confirmed byte-for-byte full resolution**, ~30 MB. Each
    matches a reference render through the same filter to within 1/255 per channel, and all five
    biome means are distinct, so no two biomes collapsed onto the same tint.
  - **Resources** — 4 bakes, 1152×960, cell 192, ~16.9 MB. Each matches its bucket-centre reference
    render to within 1/255. Bucket coverage probed at 0, .24, .25, .49, .5, .74, .75 and .99 — every
    variant a node can hash to resolves to a bake.
  - Total baked atlas memory **~72 MB**, replacing a per-entity filter on every frame.
- Seeded art preview re-run: **0 page errors**, 8 material factors and 5 visual biomes unchanged.
  Gallery diff versus the 4a capture: **RMS 1.27, PSNR 46.03 dB, 2.2% of pixels**, and amplified 16×
  the difference is confined to the 5 buildings and the 15 resource nodes — **units are bit-identical
  black**, as are terrain, HUD and minimap.
- **The capture is bit-for-bit deterministic**: two consecutive runs of the unchanged tree produced
  0 differing pixels and the same SHA-256. That is what let the faint water-region marks in the first
  4a→4b diff be pinned down as a real regression — fish had lost their drop-shadow and got no
  replacement — rather than dismissed as capture noise. Fixed by giving fish their own lighter
  ellipse; the fix moves 169 pixels with a max channel delta of 7.
- **New art-preview reference hash:** SHA-256
  `51D4B982F610914D428B988213E963060F4F18FCA46259515472F7F8D6FE0379`.
- Phase 2 contrast checklist re-inspected on the new capture: no hex lattice, meadow reads green,
  snow and sand keep grain, soft-light dapple visible. Unchanged — no terrain code was touched.
- **Max-zoom sharpness check** (new; this is the worst case for a downscaled bake). Captured the
  same seed at `CONFIG.CAMERA.ZOOM_MAX` = 2.25 from `b1b39d6` and from this commit:
  - **Buildings: identical**, as expected from a full-resolution bake.
  - **Resource nodes: indistinguishable at 6× magnification.** The 0.75 rule holds — a node covers
    at most 107 CSS px at max zoom, so cell 192 is never upscaled below dpr 1.8.
  - **Units: marginally softer.** Under a 4× magnified A/B, hair strands and belt detail on a
    villager are slightly less crisp than the full-resolution filtered draw. It is not visible at
    1:1. This is the plan's own accepted trade (25 MB versus ~105 MB) and it is recorded here as
    measured rather than assumed — the plan's "units render at ≤64 px" holds at zoom 1 (~58 CSS px),
    not at `ZOOM_MAX` on a hi-DPI panel. The two code comments were corrected to say so.
- Save/load round trip through a full page reload: identical fingerprint, 0 differing keys.
- Inline script `node --check`: clean. `git diff --check`: clean.

**Findings worth carrying forward**

1. **`ctx.filter` is now gone from every per-entity path.** Only three assignments remain, all
   documented in place: the construction scaffold, the procedural `drawBuildingBody` fallback (walls
   and the obelisk — the types with no atlas cell), and the placement ghost's fallback. Walls are the
   one type a player can build in quantity that still pays a filter; if a wall-heavy base ever
   profiles badly, a per-(type, biome, owner, size) render cache is the fix.
2. **The remaining frame cost is no longer JS.** 1.23 ms of `renderMs` against a 35.55 ms frame
   interval means 4c-4e are fighting raster and compositing: minimap redraw, atmosphere gradients,
   `shadowBlur`, the second WebGL context, and pixel fill from `MAX_DPR`.
3. **The seeded gallery is a genuine regression test, not just a screenshot.** It is bit-for-bit
   reproducible, so any unexplained pixel in a diff is a real change and worth chasing.

### Phase 4c — done 2026-07-26

Plan items 4.3 (building aura sprites) and 4.4 (`shadowBlur` purge).

**What changed** (`index.html` only)

- `buildingAuraSprite(friendly)` bakes the ownership aura into a 64 px sprite per side on first use,
  replacing a `createRadialGradient` allocated per building per frame. The sprite is built in
  normalised ellipse space so the offset, elliptical gradient of the original is reproduced rather
  than approximated — see the comment above the function for the geometry.
- Two helpers next to `drawShadow` replace `shadowBlur` everywhere: `glowStroke(color, width,
  alpha)` re-strokes the current path (the path survives a `stroke()`, so the glow and the real
  stroke share one `beginPath`), and `glowDot(cx, cy, radius, color, alpha)` for point lights. Both
  lay **two** passes of decreasing width and alpha — a single flat band reads as a second border,
  two passes approximate a blur's falloff.
- **All 26 per-frame `shadowBlur` assignments are gone.** Converted: building/site/unit selection
  rings, the zone ring, the cast underlay ellipse and its orbiting dots, magic projectiles, the
  `magicHit` / `levelup` / `slowRing` effects, the mage staff and acolyte eye glows, the healer
  spark, and the hero aura ring. Removed outright (each already had a `drawShadow` ground ellipse
  or its own dark outline doing the work): the procedural wood/gold/stone/iron node bodies, the
  procedural unit and ship bodies, and `drawBuildingBody`'s whole-silhouette drop shadow — whose
  ground ellipse went `.36` → `.4` to compensate.

**The one remaining `shadowBlur`** is in `drawTerrainTrail`, which runs on the terrain backdrop
context during `buildTerrainBackdrop` — once per rebuild, not per frame. It is the soft edge of the
road and is deliberately kept.

**Measured — and why there is no fps claim for this sub-phase**

Phase 0 predicted `shadowBlur` was worth under 1.5x, and that is what happened. After 4b both
scenarios sit on 60 Hz vsync steps (p50 33.3 ms), so frame interval quantises and the run-to-run
spread swamps the change. Three 4c runs measured idle **27.0 / 32.5 / 31.0 fps** and battle
**28.5 / 31.9 / 24.6 fps**, against 4b's 28.1 and 24.3 — directionally positive, but the spread is
larger than the effect, so **no frame-rate improvement is claimed here.**

`renderMs` is the honest metric for *this particular* change, because it measures main-thread
draw-call work rather than frame pacing, and it moved consistently across all three runs:

| Metric | b1b39d6 | 4a | 4b | 4c (3 runs) |
|---|---:|---:|---:|---:|
| Idle `renderMs` avg | 2.66 ms | 2.19 ms | 1.23 ms | **1.11 / 1.07 / 1.13 ms** |
| Battle `renderMs` avg | 21.85 ms | 5.77 ms | 2.97 ms | **2.55 / 2.39 / 2.93 ms** |

That is roughly **−11% idle and −12% battle** in render work on top of 4b. Note this is a
deliberate, scoped exception to the doc's standing "judge Phase 4 by fps, not `renderMs`" rule:
`renderMs` still under-reports total render cost, but it is a valid measure of the JS-side draw-call
work that 4c actually removes, and it is used here only for that.

**Verification**

- Seeded art preview: **0 page errors**, all 8 material factors and 5 visual biomes unchanged.
  Diff versus the 4b capture: **RMS 0.033, PSNR 77.65 dB, 0.13% of pixels, max channel delta 5**,
  confined to rows 158-185 — the building aura band and nothing else. A max error of 5/255 across a
  handful of pixels is as close as a baked sprite gets to the gradient it replaces.
  **New reference hash:** SHA-256
  `5EF3612B3C3BFE80FC356CC1E549457E4CC77C942561B4C6BBBBF1933C4A83B6`.
- The gallery does not exercise selections, projectiles or effects, so a **second deterministic
  showcase** was built for them: a seeded game with the clock pinned to `game.time = 12.5`, a
  selected building, site and units, one unit mid-cast, a magic and an arrow projectile, and the
  `magicHit` / `levelup` / `slowRing` effects at fixed fade fractions. Captured from a worktree at
  the 4b commit `cc3726d` and from this commit, at 2-3× magnification:
  - Building selection rect, unit selection rings, site ring, cast ellipse, magic projectile head
    and trail, effect rings: all present, all reading as the same glow.
  - The **first** single-pass version of `glowStroke` was rejected on this evidence — it rendered as
    a hard second border rather than a glow. The two-pass version matches the blurred original
    closely, and the unit ring alpha was then trimmed `.5` → `.34` because two passes at `.5` read
    brighter than the blur did.
  - Whole-frame difference from 4b: RMS 1.89, PSNR 42.59 dB, 2.8% of pixels — all of it glow pixels.
- Save/load round trip through a full page reload: identical fingerprint, 0 differing keys,
  0 page errors.
- Inline script `node --check`: clean. `git diff --check`: clean.

**Findings worth carrying forward**

1. **The frame interval has stopped being a usable A/B metric on this rig.** Everything now lands on
   33.3 / 50 / 66.6 ms vsync steps, so sub-step improvements are invisible and the run-to-run spread
   is ±10%. For the remaining sub-phases, quote `renderMs` for draw-call work and only claim an fps
   change when a scenario actually crosses a vsync step.
2. **Two-pass glow beats one-pass, and only a rendered A/B showed it.** Worth remembering for any
   future `shadowBlur` replacement.
3. **Harness Edge instances leak and then wedge.** A stale `--user-data-dir` profile makes the next
   run hang at startup, and a minimised window reports `visibilityState: 'hidden'` and stops rAF
   entirely — which looks like a slow run, not a broken one. The perf harness now forces the window
   back to `normal` and re-checks visibility on every poll, and stale profiles are deleted between
   runs.

### Phase 4d — done 2026-07-26

Plan items 4.5 (minimap), 4.6 (atmosphere), 4.7 (`MAX_DPR`) and 4.9 (`ents` hoist).

**What changed** (`index.html` only)

- `rebuildMinimapEntities()` renders the buildings, sites and units loops into an `mmEntities`
  offscreen canvas at `MM_ENTITY_HZ = 10`, keyed off `game.time`. `renderMinimap()` now composites
  terrain + entities + pings + camera rect. `mmDirty` rebuilds both layers; every site that nulled
  `mmTerrain` now nulls `mmEntities` too.
- `buildAtmosphereLayer()` bakes the sun wash and horizon tint into one **device-resolution**
  layer (`viewW*dpr × viewH*dpr` with a matching transform), invalidated in `sizeCanvas()`.
  `drawAtmosphere()` is now a single `drawImage`.
- `THEME.RENDER.MAX_DPR` 2.5 → 1.5.
- The per-frame `ents` array is now a module-scope `renderEnts` reset with `.length = 0`.

**Measured — whole-frame numbers cannot resolve this, so the functions were benchmarked directly**

The frame interval is vsync-quantised and its run-to-run spread is ±10% (see the 4c note), which is
far larger than anything 4d does. Both changed functions were therefore benchmarked in isolation:
median of 5 batches of 400 calls, identical 226-unit scene, from a worktree at the 4c commit
`d20df25` versus this commit.

| Call | 4c (`d20df25`) | 4d | Change |
|---|---:|---:|---|
| `renderMinimap()` | 0.0505 ms | **0.0338 ms** | −33% |
| `drawAtmosphere()` | 0.0057 ms | **0.0020 ms** | −65% |

**Be clear about what that does and does not show.** These are JS submission costs, and in absolute
terms both are negligible against a 33 ms frame — 0.02 ms saved per frame is 0.06% of it. The part
that is *not* measurable here is the raster work: several hundred `fillRect`/`arc` calls per frame
on the minimap became one `drawImage`, and two full-screen gradient fills became one blit. That work
happens off the JS timeline, and the frame interval cannot resolve it. **No fps claim is made for
4d.** It is a correct change with a real but unquantified raster saving, and an honestly tiny
measured one.

**`MAX_DPR` cannot be validated on this hardware.** The measurement rig's `devicePixelRatio` is 1.5
and the headless harness reports 1, so `min(devicePixelRatio, MAX_DPR)` is unchanged at both — the
change is a no-op here by construction. It only takes effect on displays above 1.5, where it caps
worst-case pixel fill at 2.25x instead of 6.25x. Plan risk #8 (retina softness) therefore remains
**unverified rather than cleared**, and needs a hi-DPI display to close out in Phase 7.

**Verification**

- **Minimap cache proven in both directions**, driving the sim by hand for determinism: with player
  units under a move order, the composited minimap is **byte-identical across 66 ms of game time**
  (inside one 1/10 s window — so the layer really is being reused) and **differs across 3.07 s**
  (so it really does follow the units). 0 page errors.
- Minimap rendering compared pixel-by-pixel against the 4c capture at 3× magnification: buildings,
  unit dots, site markers, resource dots, roads, water and the camera rect are all identical.
- Seeded art preview: **0 page errors**, material factors and biomes unchanged. Diff versus 4c:
  RMS 0.671, PSNR 51.60 dB, **max channel delta 3**. The change covers most of the world canvas
  because the atmosphere wash does, but at 3/255 it is 8-bit alpha quantisation of a cached
  low-alpha gradient and nothing else. Amplified 16× it is featureless noise with no banding.
  Building the layer at device resolution rather than CSS pixels cut that maximum from 8 to 3.
- Save/load round trip through a full page reload: identical fingerprint, 0 differing keys.
- Inline script `node --check`: clean. `git diff --check`: clean.

**Findings worth carrying forward**

1. **The seeded gallery is no longer bit-for-bit reproducible, and PixiJS is why.** Two consecutive
   captures of identical code now differ by 138 pixels (0.011%, max delta 7), all of them scattered
   along water edges. A probe confirms the cause: `window.PIXI` **does** load from the CDN in the
   preview environment, `#pixi-layer` holds a live canvas, and `AlbionFramework.render(delta)` is
   called from `frame()` unconditionally — outside the `appState` check — so its shore shimmer
   animates on wall-clock even with `game.time` frozen at 0 and the game paused. The 4b
   determinism check passed only because two runs happened to land on the same dash phase.
   **Phase 4e removes this; re-run the determinism check afterwards and the property should come
   back.** Until then, treat small water-edge differences in any gallery diff as shimmer noise.
2. **Caching a low-alpha gradient costs precision.** An 8-bit premultiplied intermediate cannot hold
   `rgba(255,226,151,0.085)` exactly, so any cached wash carries a couple of levels of error.
   Building at device resolution more than halves it. Worth knowing before caching any other
   translucent full-screen pass.
3. **Two of this sub-phase's four items are unmeasurable on this rig** — `MAX_DPR` by construction,
   and the minimap/atmosphere raster saving because it is off the JS timeline. They were still worth
   doing (they are plan items and the direction is unambiguous), but the tracker should not pretend
   they were validated.

### Phase 4e — done 2026-07-26

Plan item 4.8. **Phase 4 is complete with this sub-phase.**

**What changed**

- Deleted `PIXI_CDN` and the whole `AlbionFramework` IIFE (89 lines), the `#pixi-layer` div and its
  two CSS rules, `DOM.pixiLayer`, the two `sizeCanvas()` style writes, `AlbionFramework.resize()`,
  `AlbionFramework.render(delta)` in `frame()`, and `AlbionFramework.load()` at boot.
- `rebuildShoreTiles()` precomputes `game.shoreTiles` — a flat list of tile indices that are water,
  not bridged, and have at least one non-water or bridged 4-neighbour. It is called from
  `recomputeTerrainTransitions()`, which already runs at the end of world generation, after every
  connectivity-corridor stamp, and in `deserializeGame`. `invalidateShoreTiles()` additionally nulls
  it at all four places that write `game.bridges` or clear `game.water`, and `drawShoreShimmer`
  rebuilds lazily if it finds the list missing — so correctness never depends on call ordering.
- `drawShoreShimmer(cam, z)` runs on the world canvas right after `drawTerrain`, walking the
  precomputed list and culling to the viewport. Strokes are bucketed by alpha into
  `SHORE_ALPHA_STEPS = 4` reusable segment buffers, so the pass costs at most four `stroke()` calls
  per frame instead of one per shore tile.
- `shoreTiles: null` added to the game-state object with a comment marking it derived and never
  serialized. `DIRS4` added next to the existing `DIRS`.
- README and `docs/implementation-notes.md` no longer advertise a PixiJS overlay; both now state
  that the renderer is canvas-only with no CDN dependency.

**Measured — same-session A/B against a worktree at the 4d commit `2dfa99d`**

Absolute frame rates drift between sessions with machine load (the same 4d build measured 32.99 fps
earlier and 39.04 fps here), so only same-session pairs mean anything:

| Metric | 4d (`2dfa99d`) | 4e | Change |
|---|---:|---:|---|
| Idle pan fps | 39.04 | **41.94** | +7% |
| Battle fps (229 units) | 31.53 | 31.36 | unchanged (noise) |
| Idle `frameMs` − `renderMs` − `simMs` | 0.40 ms | **0.14 ms** | −0.26 ms |
| Battle `frameMs` − `renderMs` − `simMs` | 0.48 ms | **0.18 ms** | −0.30 ms |

That last row is the honest one. `AlbionFramework.render()` was called from `frame()` *after*
`render()`, so its cost never appeared in `renderMs` at all — it sat in the residual alongside
`uiSync`. Removing it takes ~0.26-0.30 ms of main-thread work per frame, **plus** an entire second
WebGL context whose GPU cost is not on the JS timeline and is not measured here.

**Verification**

- **`game.shoreTiles` matches a brute-force scan exactly** — same rule, computed independently in
  the page — in three states: on a fresh seeded map (154 shore tiles of 241 water, 4 bridged), after
  forcing a lazy rebuild, and after a save/load round trip. Bridge exclusions carried over on both
  sides, so a bridge deck neither shimmers nor makes its neighbours shimmer.
- **Zero external requests.** Every request the page makes is `file://`, logged over CDP with
  `Network.enable`. A repo-wide `grep -rniE 'pixi|cdn\.jsdelivr|AlbionFramework'` returns only one
  hit: the explanatory comment above `drawShoreShimmer`. The full offline serve-and-disconnect test
  is Phase 7's, but there is no longer any code path that could reach the network.
- Shimmer compared side by side at 2× against the 4d build on the same seed and camera: same dashes
  in the same places at the same brightness and angle. They are not pixel-identical, and cannot be —
  the Pixi version's phase followed wall-clock while this one follows `game.time`.
- **Seeded gallery determinism is restored.** Two consecutive captures now hash identically
  (`F1D2F9C8529E1382A85994199FFC9EC259C11BA0AFD4E8E9D7BDCEE2F9D1FA06`) with **0 differing pixels**,
  confirming the Phase 4d diagnosis that PixiJS was the sole source of capture noise. Diff versus
  the 4d capture: RMS 0.291, PSNR 58.86 dB, 0.10% of pixels — all of it water-edge shimmer.
  **New reference hash:** that same `F1D2F9C8…` value.
- Save/load round trip through a full page reload: identical fingerprint, 0 differing keys.
- Inline script `node --check`: clean (11,003 lines, down from 11,092). `git diff --check`: clean.
  0 page errors in every run above.

---

## Phase 4 summary

All nine plan items are landed, across five sub-commits.

**Headline, against the Phase 3 baseline `b1b39d6` measured with the identical harness:**

| Scenario | Before | After | Change |
|---|---|---|---|
| Idle pan, 4-player Greatwood, 26 units | 69.73 ms — **14.34 fps** | 28.67 ms — **34.88 fps** | **2.4x** |
| ~100 v 100 battle, 229 units | 439.77 ms — **2.27 fps** | 30.45 ms — **32.84 fps** | **14.5x** |
| Idle `renderMs` | 2.66 ms | 1.19 ms | −55% |
| Battle `renderMs` | 21.85 ms | 3.24 ms | −85% |

The battle target (< 25 ms avg) is met. Idle sits at 28.67 ms rather than the < 16.7 ms target, but
main-thread work per frame is now **1.45 ms** — the remaining interval is raster and vsync, not
JavaScript, and the loop is pinned to 60 Hz vsync steps. Squeezing past 30 fps would need fill-rate
work (the 2880² backdrop blit, overdraw), which is outside Phase 4's scope.

**Every per-entity `ctx.filter` and every per-frame `shadowBlur` is gone.** What remains:
`ctx.filter` at three documented sites with no atlas to bake into (construction scaffold, the
procedural building fallback for walls and the obelisk, the placement ghost's fallback), and one
`shadowBlur` in `drawTerrainTrail`, which runs once per backdrop rebuild rather than per frame.

**Runtime memory added:** ~72 MB of baked atlases — 25 MB units (5 × 512×2560), 30 MB buildings
(5 × 1448×1086), 17 MB resources (4 × 1152×960). This is a runtime cost, not a payload cost; the
deployed payload is unchanged at 12.34 MiB over 20 requests.

**Not validated, and why:** `MAX_DPR` 2.5 → 1.5 is a no-op on the measurement rig
(`devicePixelRatio` 1.5), so plan risk #8 stays open for Phase 7 on a hi-DPI display. The raster
saving from the minimap and atmosphere caches is real but off the JS timeline and unmeasurable with
the available instruments.

### Phase 5 — done 2026-07-26

All three plan items, one commit. `index.html` only; no render code touched.

**What changed**

- **Spatial hash for `applySeparation()`** — a module-level uniform grid (`sepBuckets` /
  `sepCounts` / `sepCandidates`), cell size `CONFIG.SEPARATION.CHECK_DIST`, built by
  `ensureSeparationGrid()` and rebuilt only when the map dimensions change. Buckets are plain
  arrays reused for the life of the map; a tick clears counters, never reallocates. Live,
  non-transported units are inserted in index order, so every bucket stays sorted ascending.
  Each unit then collects the `j > i` entries of its 3x3 cell neighbourhood and **sorts them back
  into ascending index order** before running the unchanged pair logic (see the deviation below).
- **`terrainStepCost(tx, ty, mode, equipment) -> number`** — a numeric twin of
  `terrainTraversalAt` with no object literal and no per-call `Set`. `terrainTraversalAt` is
  retained unchanged for UI tooltips and placement reasons.
- **`tileOccupiedFor(tx, ty, askerOwner)`** splits the node/building/gate half of
  `tileBlockedFor` from the terrain half, so the A\* inner loop can answer "blocked?" and "how
  much?" from **one** `terrainStepCost` call instead of the old two `terrainTraversalAt` calls
  that computed the same thing twice and boxed it both times. `tileBlockedStep` is the
  resolved-mode/equipment twin of `tileBlockedFor`; both now share `tileOccupiedFor`.
- **Mode and equipment resolved once per query**, not per tile: in `findPathTiles` (before the
  A\* loop), in `computePath` (which also threads them into its rect `goalTest`, run on every
  expansion, and passes them to `findPathTiles`), and in `followPath` (once per call rather
  than twice per waypoint). `movementModeFor()` replaces three copies of the inline
  `typeOrMode === 'water' || …` expression.
- **`findPathTiles` no longer allocates a `{tx,ty}` object per step.** It writes tile indices
  into a reusable `PF.tiles` scratch buffer and returns the count (`0` = already at goal,
  `-1` = no route). `computePath` builds `u.path` straight from that; `ensureTerrainStartConnectivity`,
  the only other caller, reads the same buffer. `PF.tiles` is reallocated alongside the other
  PF buffers in `resetPathBuffers()`.

**Measured — same-session interleaved A/B against a `git worktree` at the Phase 4e commit `760a87e`**

Per the continuation prompt, frame rate is not used at all here. The harness starts a fixed-seed
Greatwood game, spawns the documented 100 v 100 battle, and drives `update(DT)` directly with
`appState = 'paused'`. `performance.now()` is coarsened to 0.1 ms in this context, so
`applySeparation` and `computePath` are timed as blocks of 600 / 40 reps with a separately timed
block of restores subtracted, and the sim tick is timed in 20-tick segments so one GC pause
cannot distort the whole run. Three before/after pairs were run alternately; the table is the
median of three, and **every one of the three before runs was worse than every one of the three
after runs on every row** — the distributions do not overlap.

| Metric | before (`760a87e`) | after | Change |
|---|---:|---:|---|
| Sim tick, median 20-tick segment | 0.9000 ms | **0.3300 ms** | **2.73x** |
| Sim tick, whole 400-tick block | 0.9315 ms | **0.4168 ms** | **2.24x** |
| Sim tick, fastest segment | 0.3600 ms | **0.1900 ms** | 1.89x |
| `applySeparation`, 225 units | 0.1123 ms | **0.0302 ms** | **3.72x** |
| `applySeparation`, 156 units engaged | 0.1653 ms | **0.0495 ms** | **3.34x** |
| `computePath`, cross-map route | 0.4299 ms | **0.1111 ms** | **3.87x** |

Call counts over the same 460 ticks, collected in a separate uninstrumented run so the wrappers
never touch the timed block. The four sim-shaping counts are **identical**, which is the
behavioural result read a second way:

| Call | per tick, before | per tick, after |
|---|---:|---:|
| `applySeparation` | 1 | 1 |
| `computePath` | 7.34 | 7.34 |
| `findPathTiles` | 7.35 | 7.35 |
| `followPath` | 29.42 | 29.42 |
| `terrainTraversalAt` | 1866.73 | 616.43 |
| **`terrainEquipmentFor`** (one `new Set()` each) | **1864.67** | **652.52** |
| `tileBlockedFor` | 1459.18 | 526.28 |
| `terrainStepCost` (new, allocation-free) | — | 857.24 |
| `tileBlockedStep` (new) | — | 431.73 |

**The Phase 0 baseline for this phase did not reproduce, and the plan's premise was wrong.**
Phase 0 recorded `applySeparation` at 2.49 ms of a 3.05 ms tick (82%) at 188 units. Measured
directly on the unmodified `760a87e` build it is **0.11 ms of a 0.90 ms tick — about 12%**. The
Phase 0 figure came from a DevTools sampled profile in a different session; a sampling profiler
attributes inlined callee time to the frame it samples and carries its own overhead, so it is not
comparable to a direct micro-benchmark. The real hot spot was item 2, not item 1: `terrainEquipmentFor`
was allocating a `Set` **1,865 times per tick**, and `terrainTraversalAt` was boxing a result
object almost as often. That is why the tick improved 2.73x while separation itself, though 3.3-3.7x
faster, only accounts for about a tenth of it.

**Deviation from the plan, deliberate — candidates are sorted before the pair loop runs.**
The plan specifies a 3x3 neighbourhood scan with an `indexA < indexB` guard, which visits each
pair once but in *cell* order rather than ascending-index order. That is not behaviour-preserving
here: every push moves **both** units, so later pairs observe earlier ones, and an exactly
overlapping pair (`d < 0.01`) draws twice from the **seeded** RNG, so a reordering shifts the
whole RNG stream. The nine buckets are each ascending, so an insertion sort over the collected
candidates restores the exact order the old `for j = i + 1` loop used. It is cheap because `m` is
bounded by how many units physically fit in a 3x3 neighbourhood at the minimum separation
distance, and it buys exact bit-identity instead of the "bound the drift" outcome the
continuation prompt anticipated.

**Verification**

- **Behavioural equivalence, whole sim.** 460 deterministic ticks of the 225-unit battle from a
  fixed seed, fingerprinting id/type/owner/x/y/hp/state of every live unit: **`1A69F4ED` on all
  three before runs and all three after runs**, with 0 of 156 unit positions differing. Note this
  required pinning `Math.random` in the harness — see finding 3.
- **`terrainStepCost` vs `terrainTraversalAt`, exhaustively.** Every tile of every map preset
  (5) x every terrain-gate setting (`off`/`standard`/`harsh`) x land, villager and naval movers
  x an owner with and an owner without both equipment researches, plus six out-of-bounds
  coordinates: **466,650 cost comparisons and 466,650 blocked comparisons, 0 mismatches**,
  0 page errors. `terrainStepCost(...)` equals `passable ? cost : Infinity` in every case,
  including the 383 bridged tiles across those maps.
- **`applySeparation` vs a verbatim copy of the old O(n²) loop**, 30 successive applications per
  scenario, comparing every unit x/y **and** `game.rngState` bit-for-bit:

  | Scenario | peak units per cell | result |
  |---|---:|---|
  | fresh 100 v 100 grid spawn (224 units) | 2 | identical |
  | mid-battle t=4 s (191 units) | 4 | identical |
  | late battle t=10.7 s (109 units) | 4 | identical |
  | map-wide scatter (225 units) | 2 | identical |
  | forced pile, 800 / 400 / 300 / 200 / 150 px box | 3 / 6 / 8 / 14 / 25 | identical |
  | forced pile, 100 / 60 / 40 / 20 / 6 px box | 36 / 92 / 122 / 142 / 197 | **diverges** |
  | all 225 units on one coordinate | 225 | **diverges**, incl. RNG draw count |

  This is explained, expected, and bounded — see finding 2. The threshold sits between **25 and
  36 units in a single 38x38 px cell**. Measured peak occupancy in real simulation: **10** over
  900 ticks of the 100 v 100 battle and **3** over 6,000 ticks (100 s) of an undisturbed AI game.
- **World generation is bit-identical.** `findPathTiles`' contract change reaches into
  `ensureTerrainStartConnectivity`, so 60 worlds (5 presets x 3 seeds x compact/standard x
  standard/harsh gates) were hashed over terrain type/variant/elevation/moisture/temperature/slope,
  `blocked`, `bridges`, `water`, every resource node, building, site, unit and ambient entity:
  **60/60 identical** between the `760a87e` worktree and this build, 0 page errors.
- **Save/load round trip** through a full page reload: identical fingerprint, **0 differing keys**,
  `game.shoreTiles` matches an independent brute-force scan exactly (147/147), 200 further ticks
  run clean, slot removed afterwards, 0 page errors.
- **Cross-build save compatibility**: a game played 900 ticks and serialized by the **`760a87e`
  build** loads into this build with an identical fingerprint — including the in-flight `u.path`
  waypoint list of the one unit that had an active path, which is the field `computePath` now
  builds differently. 300 further ticks run clean.
- **Seeded art preview**: 0 page errors, 8 material factors and 5 visual biomes unchanged, and the
  capture is **byte-identical to the Phase 4e reference**, SHA-256
  `F1D2F9C8529E1382A85994199FFC9EC259C11BA0AFD4E8E9D7BDCEE2F9D1FA06` — expected, since no render
  code was touched. The hash is unchanged for Phase 6.
- Inline script `node --check`: clean (1 block, 11,112 lines). `git diff --check`: clean.
  `index.html` is the only changed file.

**Findings worth carrying forward**

1. **The remaining allocation churn is `applySeparation`'s own blocked checks.**
   `terrainEquipmentFor` still runs 652 times a tick, and ~526 of those come from the two
   `blockedAtWorldFor` calls in the separation pair loop, which the plan explicitly said to leave
   unchanged. The ceiling on fixing it is small and measured: `applySeparation` now costs
   0.0495 ms of a 0.33 ms tick, so eliminating it **entirely** would be worth at most ~15% of the
   tick. It would need a per-tick (type, owner) equipment memo and a change to the one piece of
   logic this phase deliberately kept byte-for-byte. Recorded as the next target, not done.
2. **The spatial hash is exact only while units stay in their start-of-tick cell.** The grid is
   built once per call from start-of-call positions, but the pair loop moves units as it goes, so
   a unit pushed more than one cell (38 px) during a single call can be matched against a stale
   neighbourhood. That needs ~36 units inside one 38x38 px cell to happen; separation itself
   prevents that state, since it keeps centres at least `a.radius + b.radius` (20-30 px) apart, and
   the measured peak in a deliberately extreme 226-unit battle is 10. If a future change can
   teleport or spawn many units onto one point, re-run the graded audit before trusting it.
3. **The sim has two unseeded `Math.random()` calls and is therefore not reproducible on its own.**
   `findBuildSpot` (AI building placement) and the AI betrayal roll both use `Math.random()` rather
   than `seededRandom()`. Two runs of the same seed drift apart within ~15 s of game time: same
   `rngState` and same unit count, but up to 7 of 156 units end up as much as 260 px apart, because
   the AI put a building somewhere else. This is **pre-existing and was not fixed here** — changing
   it would alter sim behaviour, which is exactly what this phase had to avoid. Any future
   determinism work must pin or reseed those two call sites; every measurement above did so in the
   harness.
4. **A sampled profile is not a benchmark.** The Phase 0 attribution overstated
   `applySeparation` by roughly 7x relative to a direct micro-benchmark and pointed the phase at
   its smallest win. Where a function can be called in isolation, call it in isolation.

---

### Phase 6 — done 2026-07-26

Display-only rebrand, one commit. No simulation or render logic changed; the one structural
change (`flavor`) exists purely so display names stop being load-bearing.

**What changed**

- **Tripwire first: `flavor` on every map preset.** Each `MAP_PRESETS` entry gained a
  `flavor` key (`woodland` / `marsh` / `downs` / `vale` / `alpine`) with a comment saying to
  branch on it and never on `name`. The five surviving `preset.name` branches — the
  `placeProceduralWilds` weight table (marsh and downs arms), the stream count, the stream
  width, and the pond count — now test `preset.flavor`. `grep -nE 'preset\.name|\.name\.indexOf'`
  returns nothing.
- **Display strings**: 150 lines of `index.html`, applied by a throwaway script that carried
  the exact expected hit count for each of 24 rules and aborted on any mismatch — a counted
  per-term sweep, not a blind `sed`. Every changed line was read before the write.
- **Asset renames** via `git mv`: six `albion-*.png` → `eldervale-*.png`, six
  `docs/screenshots/fable-*.png` → `eldervale-*.png`. Git records all twelve as pure renames
  (`Bin`, no content delta). Updated the four `ALBION_ART.*.src` assignments, the
  `#screen-start` CSS title-vista URL, `tools/build_sprite_atlases.py`,
  `tools/downscale_terrain.py`, `tools/capture_art_preview.mjs`, and the mkdtemp prefix in
  `tools/audit_bridges.mjs`.
- **Docs**: `README.md` rewritten (no "inspired by Fable: The Lost Chapters", no "Age of
  Empires-style"); `assets/sprites/README.md` provenance rewritten so it no longer
  art-directs against a "TLC character reference"; `assets/terrain/README.md`,
  `docs/screenshots/README.md` and `docs/implementation-notes.md` updated.
- **Disclaimer** added verbatim to the README and to a new `.legal` footer in the start menu.

**Rename table as applied** (display strings and filenames only)

| Current | New | | Current | New |
|---|---|---|---|---|
| Albion Skirmish | Eldervale Skirmish | | Hobbe | Grubkin |
| Albion (world/Age/buildings) | Eldervale | | Balverine | Moorfang |
| Bowerstone | Bridgemere | | Demon Door | Riddle Gate |
| Oakvale | Elmshire | | Will | Aether |
| Knothole | Thornhollow | | Heroes Guild Spire | Wardens' Lodge Spire |
| Brightwood | Sunglade | | Guild Hall / Guild Hero | Lodge Hall / Warden |
| Greatwood | Heartwood | | Guild (all other uses) | Lodge |
| Darkwood | Mirkfen | | Archon('s Legacy) | Sovereign('s Legacy) |
| Snowspire | Frostcrag | | Old Kingdom | Elder Kingdom |
| Barrow Fields | Cairn Fields | | Rose Cottage | Thistle Cottage |

**Verification**

- **Worldgen is bit-identical across the `flavor` refactor — the direct test for plan risk #2.**
  60 worlds (5 presets x 3 seeds x compact/standard x standard/harsh gates), hashed over
  terrain type/variant/elevation/moisture/temperature/slope, `blocked`, `water`, `bridges`,
  every resource node, building, site, unit, ambient entity and creep camp, plus decor
  geometry: **60/60 identical**, 0 page errors. Baseline captured on `ad1a36d` before the
  first edit (e.g. `greatwood|phase6-a|compact|standard` = `C1AC2A68`).
- **Cross-build save compatibility — the real gate.** A game played 1,400 ticks and serialized
  by the **pre-rebrand `ad1a36d` build** (230,957 bytes) loads into this build with an
  **identical fingerprint `25E2DB34`**: 27 units, 7 buildings, 332 nodes, 8 sites, including
  the in-flight `u.path` of the one unit that had an active path. 300 further ticks ran clean,
  0 page errors. Both sides were fingerprinted *after* `deserializeGame`, so nothing is
  attributable to the round trip itself.
- **In-build save/load round trip** through a real page reload, via the game's own
  `saveGameToSlot` / `loadGameFromSlot` on the untouched key `albion.save.4` (216,228 bytes):
  `425192F9` → **`425192F9`**, 200 further ticks clean, slot removed afterwards.
  `albion.settings` write-and-read-back verified separately. 0 page errors.
- **Grep gate** — `grep -rniE 'albion|bowerstone|oakvale|knothole|brightwood|snowspire|hobbe|balverine|demon ?door|heroes.{0,2}guild|fable'`
  (excluding `.git`, `.edge-art-preview`, `__pycache__`, and these two overhaul docs) returns
  **only** the keep-list:

  | Survivor | Count | Why it stays |
  |---|---:|---|
  | `ALBION_ART`, `albionArtImages` | 57 | internal art namespace |
  | `albion.settings`, `albion.save.` | 3 | localStorage keys |
  | `hobbeWild`, `balverine`, `demonDoor`, `drawDemonDoorSite` | 20 | entity type ids stored whole by `serializeGame` |
  | `brightwood` / `snowspire` (+ `greatwood`/`darkwood`/`barrowfields`) preset ids | 7 | `<option value>` ids, persisted as `options.mapId` |
  | disclaimer text in `index.html` and `README.md` | 2 | names the franchise on purpose |
  | README keep-list note | 1 | documents the above |

- **Atlas rebuild is byte-identical.** `python tools/build_sprite_atlases.py` reproduced both
  atlases bit-for-bit after the rename (units SHA-256 `3e1cd5225a925c01…`, resources
  `03e40437f5813464…`), **dimensions unchanged** at 1024x5120 and 1536x1280, 80 and 30
  validated bleed-safe cells. The `atlas-manifest.json` diff is exactly the two `file` fields.
- **Art preview**: re-run on `ad1a36d` before any edit and it reproduced the Phase 4e/5
  reference `F1D2F9C8…FA06` exactly, so the harness was known-good going in. After the
  rebrand the capture is stable at **SHA-256
  `552A7DE29FE65D62B53A5FBB68B226D04228A9387C3A91BB25C8E6CFD6AC7D34`** (reproduced twice).
  The change was diffed pixel-by-pixel rather than accepted: the delta is a **single bounding
  box (478,37)-(1092,113), 18,193 of 1,263,850 pixels (1.44%)**, and it is the start-of-game
  notification toast reading `Map: Snowspire Pass` → `Map: Frostcrag Pass`. **Zero pixels of
  rendered art changed**, which is independent proof the renamed asset files were only moved.
  Material brightness factors and the five visual biomes are unchanged.
- **Display smoke test** over CDP: title, `<h1>`, subtitle, the five map options, the four
  start conditions, all four Age names, `CONFIG` names, `THEME.FACTIONS`, `NODE_NAMES`, the
  three quest-site names, and the per-faction `unitDisplayName`/`buildingDisplayName` path all
  return renamed strings; the `.legal` footer is present and visible. 0 page errors.
- Inline script `node --check`: clean (1 block, 11,120 lines). `git diff --check`: clean.
  `py_compile` on both Python tools and `node --check` on both `.mjs` tools: clean.

**Deviations from the plan, all deliberate**

1. **The plan's two render tripwires no longer exist.** `/Snowspire/i` (7338) and `/Darkwood/i`
   (7342) were deleted in **Phase 2**, which un-gated the meadow soft-light pass. The plan's
   7482/7491 and 2630 anchors resolve to the five *worldgen* branches listed above. So the
   surviving risk was never in `buildTerrainBackdrop` — it was in resource placement, streams
   and ponds, where a renamed preset would have silently changed the generated map.
2. **The key is `flavor`, not `climate`.** `climate` is already a local variable name for
   `preset.terrain` (the numeric temperature/moisture/forest mix) in `terrainVisualFamilyAt`
   and `deserializeGame`; `preset.climate` next to it would have been actively misleading.
3. **The "Guild" sweep is complete, not limited to the table's three rows** — confirmed with
   the owner. The table renamed `Guild Hall`, `Guild Hero` and `Heroes Guild Spire`; leaving
   the other ~30 (`Guild Apprentice`, `Guild Charter`, "Defend the Guild", `Guild Gate`,
   "Select Guild Apprentices first", …) would have left a Lodge Hall training Guild
   Apprentices. Faction 0 is now the Wardens' Lodge throughout.
4. **Four renames beyond the table**: `Rose Cottage` → `Thistle Cottage` (a Fable II location
   the table missed); `Bandit Lodge` → `Bandit Hovel` (the bandit house name collided with the
   player faction's new name); `'Open Door'` → `'Open Gate'` (button label for a Riddle Gate);
   and `Archon Weapons`/`Archon Armor` → `Sovereign …` (the table renamed only the Age, but
   Archon is Old-Kingdom Fable lore and the forge tiers share the word).
5. **`Wardens' Lodge Spire` is written with an escaped apostrophe** (`Wardens\'`). Both
   occurrences sit inside single-quoted JS literals; the first dry run produced a syntax error
   and the rule was fixed before anything was written.
6. **The art preview reference hash changed, and the new one is accepted** — but only after the
   pixel diff above proved the cause is a display string, not the art. Phase 7 should use
   `552A7DE2…7D34`.
7. **The GitHub repo was NOT renamed.** Asked the owner; they chose to keep
   `hipstereclipse/Albion-Skirmish`. No `git remote set-url` needed.
8. `assets/terrain/README.md` still claimed every terrain PNG is 1254x1254, stale since
   Phase 3. Corrected to 384x384 materials / 512x512 transitions while rewriting its
   provenance paragraph.

**Findings worth carrying forward**

1. **Old saves display the old map name.** `serializeGame().meta.map` stores
   `currentMapPreset().name`, so a pre-rebrand save shows "Snowspire Pass" in the load-slot
   list. It is metadata only — the load path resolves the preset from `options.mapId` — so the
   game loads correctly and only the slot label is stale. Not worth a migration; a
   `LEGACY_MAP_NAME` lookup in `wireSlotList` would fix it cosmetically if it ever matters.
2. **The disclaimer keeps the word "Fable" in the shipped page on purpose.** It is the plan's
   exact wording and the standard fan-project formulation, but it is the one place the rebrand
   deliberately re-associates the game with the franchise. If the owner would rather the
   shipped build name nothing, the honest alternative is "An original fan-made game, not
   affiliated with or endorsed by any other game or publisher." Left as specified.
3. **`git mv` + a byte-hash check is the cheap proof for asset renames.** `--stat` showing
   `Bin` with no delta, plus the pixel diff on the art preview, covers "moved, not modified"
   from two independent directions.
4. **The atlas builder is fully reproducible** (byte-identical output from identical sources on
   Pillow 12.1.1), so regenerating the manifest is safe and does not disturb the art preview.

---

### Phase 7 — done 2026-07-26

The final phase, and a verification pass rather than a change pass: it confirms on the **final build,
in one place, on one harness**, what the per-phase logs asserted separately. One real defect was
found and fixed (the save-slot label — see deviation 1); nothing else in `index.html` changed.

All measurement below was done against HEAD `26991e6` plus that one fix, with the "before" side a
`git worktree` at the Phase 3 commit `b1b39d6` — the same harness Phases 4 and 5 both used. The
harness itself is throwaway and is not committed, per the plan.

#### 1. Perf A/B — three interleaved before/after pairs, median of three

Seed `overhaul-perf-v1`, Heartwood Crossing (`greatwood`), 4 players (player + 3 enemy factions),
`?perf` HUD, canvas **1275x490 CSS at dpr 1.5** — byte-for-byte the Phase 4/5 harness geometry, so
these numbers sit on the same scale as the Phase 4 summary table. 60 s of continuous panning driven
by adding `KeyD`/`KeyA` to the real `keys` set, then the documented 100 v 100 spawn through the
game's own `createUnit` and 30 s of fighting. Samples pulled gap-free via `perf.total` (no run
gapped); every run asserted `document.visibilityState === 'visible'` throughout, so none was
rAF-throttled.

| Metric | before (`b1b39d6`) | after (final) | Change |
|---|---:|---:|---|
| (a) Idle pan, avg frame ms | 94.78 (**10.55 fps**) | **41.35 (24.18 fps)** | **2.29x** |
| (a) Idle pan, p95 frame ms | 150.1 | **83.3** | −45% |
| (a) Idle `renderMs` avg | 3.39 | **1.45** | −57% |
| (b) Battle, avg frame ms | 584.30 (**1.71 fps**) | **47.88 (20.89 fps)** | **12.2x** |
| (b) Battle, p95 frame ms | 683.2 | **100.0** | −85% |
| (b) Battle `renderMs` avg | 17.21 | **3.37** | −80% |
| (b) Battle `simMs` avg (per frame, incl. catch-up ticks) | 23.19 | **0.93** | −96% |

**Every one of the three before runs was worse than every one of the three after runs on every
row** — the distributions do not overlap:

| Run | idle fps | battle fps |
|---|---:|---:|
| before 1 / 2 / 3 | 11.29 / 9.68 / 10.55 | 1.79 / 1.71 / 1.71 |
| after 1 / 2 / 3 | 24.02 / 24.18 / 24.78 | 17.25 / 20.89 / 21.84 |

Two honest caveats:

- **The absolutes are ~30% slower than the Phase 4 summary** on the identical harness and canvas
  (Phase 4 recorded idle 69.73 -> 28.67 ms and battle 439.77 -> 30.45 ms). The whole session ran
  slower, both sides equally; session-to-session drift of this size is already documented in the
  Phase 4e log. The *ratios* — 2.29x idle and 12.2x battle — bracket Phase 4's 2.4x and 14.5x. This
  is exactly why the pairs are interleaved in one session: the pair is meaningful, the absolutes
  are not comparable across sessions.
- **The battle comparison is biased against the after build.** Slow frames lose sim time to the
  `delta > 0.25` clamp, so the before build advances less game time in the same 30 s and ends with
  more units alive (median 176 vs 125). The fast build therefore simulates *more* of the fight while
  being measured. The 12.2x is if anything conservative.

#### 1c. 10 s capture during the battle, on both builds

Two instruments, because a flame chart cannot prove an absence. First, direct per-frame counters on
`ctx.filter`, `ctx.shadowBlur` and `drawImage`-while-filtered, in their own 6 s window so the
wrappers never distort the profile:

| Per frame | before (`b1b39d6`) | after (final) |
|---|---:|---:|
| **filtered `drawImage` calls** | **226.83** | **0** |
| `ctx.filter` writes (all non-`none`) | 226.83 | **0** |
| `shadowBlur` writes | 0.17 | **0** |
| total `drawImage` | 228.80 | 201.50 |

In raw totals: the before build made **2,722 filtered `drawImage` calls out of 2,746** — practically
every blit in the frame paid a filter. The after build made **0 filtered calls out of 34,253**. That
is the plan's "filtered `drawImage` absent from the flame chart", measured rather than eyeballed.

`shadowBlur` was already near-zero in *this* scene on the before build, which is consistent with
Phase 0's "under 1.5x" prediction: the pre-4c `shadowBlur` sites are selection rings, magic
projectiles, effects and the procedural entity fallbacks, and a militia/archer/spearman/knight
battle with nothing selected reaches almost none of them. The after build's 0 also confirms
`drawTerrainTrail`'s surviving pair does not run per frame.

Static audit either side, as a cross-check: `b1b39d6` had 7 `.filter =` assignments and 29
`shadowBlur`; the final build has 8 `.filter =` — 2 in the one-time material bake, 3 in the three
boot-time atlas bakes, and exactly the **3 documented per-draw keeps** (construction scaffold, the
procedural `drawBuildingBody` fallback for walls and the obelisk, the placement-ghost fallback) —
and **2 `shadowBlur`**, the set/reset pair inside `drawTerrainTrail`. Nothing was "finished".

Second, a CPU profile (10 s, 200 µs sampling, nothing patched):

| Self time | before | after |
|---|---:|---:|
| `applySeparation` | 107.2 ms (1.07% of capture) | 57.97 ms (**0.58%**) |
| `terrainTraversalAt` | 44.08 ms | 3.29 ms |
| `terrainEquipmentFor` | 18.17 ms | 8.29 ms |
| `drawImage` (native) | 129.6 ms | 181.24 ms |
| fps during the capture | 2.87 | 29.15 |

Read that table carefully: the after build rendered **170 frames to the before build's 12** and ran
~1.4x more sim ticks in the same 10 s, so equal-looking totals mean far less work per call, and
`drawImage`'s larger total is 34,253 unfiltered blits costing less than 2,746 filtered ones.

**A sampled profile is not a benchmark** (Phase 5 finding 4), so `applySeparation` was also timed in
isolation on the final build using Phase 5's method — 5 batches of 600 reps with a separately timed
block of position restores subtracted, median of the batches, three successive runs as the fight
thinned out:

| Live units | `applySeparation`, `b1b39d6` | `applySeparation`, final |
|---:|---:|---:|
| 225 | 0.2267 ms | **0.0292 ms** (7.8x) |
| 171 | 0.1718 ms | **0.0753 ms** |
| 113 | 0.1065 ms | **0.0267 ms** |

| Sim tick | `b1b39d6` | final |
|---|---:|---:|
| median 20-tick segment, 225 units | 0.875 ms | **0.400 ms** (2.19x) |
| whole 400-tick block, 225 units | 1.204 ms | **0.493 ms** |

The final build's **0.0292 ms at 225 units matches Phase 5's 0.0302 ms**, so nothing regressed in
the sim between Phase 5 and the rebrand. Separation is now ~7% of a 0.40 ms tick. Peak occupancy of
a single 38 px separation cell in this state was **2** (72 occupied cells) — far below the 25-36
threshold where Phase 5 showed the spatial hash stops being exact. Unit counts fell 225 -> 171 ->
113 -> 79 identically on both builds, which is an incidental behavioural-equivalence check.

#### 2. Load — payload, rebuild count, visual states

`python -m http.server` over the working tree; Edge via CDP with `Network.setCacheDisabled`,
service-worker bypass, and `Network.emulateNetworkConditions` at **32 Mbps** (4,194,304 B/s, 20 ms
latency) — per Phase 0 finding 4 the pop-in only reproduces over throttled HTTP, never from
`file://`, so it was verified that way.

| Build | Bytes (`encodedDataLength`) | Requests | External requests |
|---|---:|---:|---|
| `b1b39d6` (Phase 3 baseline, re-measured) | 12,951,516 (12.35 MiB) | 20 | 1 — `cdn.jsdelivr.net/npm/pixi.js@7.4.2` |
| **final** | **12,823,088 (12.23 MiB)** | **19** | **0** |

**Nothing regressed, and the per-request diff explains every byte.** Exactly two lines differ
between the two builds: `index.html` grew 556,523 -> 564,585 B (+8,062, the Phase 4/5/6 code), and
the 136,490 B PixiJS CDN response is gone. Net **−128,428 B and −1 request**. Every asset request is
byte-identical on both sides — independent confirmation that the Phase 6 renames were pure moves.

So the expected "12,939,974 B over 20 requests" has become 12,823,088 B over 19: the 20th request
*was* the CDN fetch that Phase 4e removed. The 11,542 B gap between the Phase 3 record (12,939,974)
and this re-measure of the same commit (12,951,516) is that same CDN response varying between runs —
it is the only non-local response in the set, which is the cleanest possible attribution.

**`buildTerrainBackdrop` fires exactly once** at the documented post-load start timing (game started
after `readyState === 'complete'` and `artReady === true`). Started at the first instant `startGame()`
is callable — the deliberate stress case — it fires **twice**: one procedural build plus exactly one
art-ready rebuild. That is Phase 1 finding 1, reproduced on the final build.

**Only two visual states appear.** Rather than sampling screenshots and hoping to catch the
transition, `buildTerrainBackdrop` was wrapped to dump the backdrop canvas *after every call*, so the
captured set is precisely the set of terrain looks reachable during load. The early-start run
produced two, and only two:

| State | `artReady` | material / transition patterns | Look |
|---|---|---:|---|
| 1 | `false` | 0 / 0 | the painterly procedural backdrop |
| 2 | `true` | 8 / 3 | the fully textured backdrop |

Both were inspected: one clean full-map swap, no bare hex-grid state and no partially textured
state. The late-start run produced state 2 only. The single page error in all three runs is the
pre-existing `favicon.ico` 404.

#### 3. Art — seeded preview and the Phase 2.7 contrast checklist

`tools/capture_art_preview.mjs` re-run twice (before and after this phase's one code change). Both
captures hash SHA-256 **`552A7DE29FE65D62B53A5FBB68B226D04228A9387C3A91BB25C8E6CFD6AC7D34`** —
identical to the Phase 6 reference — and `git status` reports the PNG unmodified, so the capture is
**byte-identical, not merely similar**. 0 page errors. All 8 material brightness factors unchanged
(meadow/forest/mud/rock/water/road 1.4; sand/snow 0.95, the two clamped ones), all 5 visual biomes
and all 5 resource biomes present, no missing unit rows, atlases still 1024x5120 and 1536x1280.

Checklist walked by eye at the harness's `.78` gallery zoom and again on 3x crops of the two clamped
materials and a uniform meadow field:

- **Pass — no visible hex lattice at default zoom.** Uniform material fields show no repeated
  honeycomb; the only stepped edges are the intended boundaries between different material bands.
- **Pass — meadow reads green, not olive-black.** Meadow is clearly green with visible grass grain;
  forest is a darker green and marsh/mud darker still, which is the intended ordering.
- **Pass — snow and sand are not blown out.** At 3x, snow keeps crystalline grain and blue-grey
  shading; sand keeps grain and its track marks. Neither clips to flat white or flat cream, and
  there is no posterization from the Phase 3 palette pass.
- **Pass — soft-light dapple still visible.** Mottling and the half-alpha ellipse/stroke accents
  read over the textures; the dapple brightening is plainly visible across meadow and sand.

#### 4. Saves — an old build's save, and a round trip in the new one

Both harnesses pin `Math.random` on both sides, because Phase 5 finding 3 established the sim is not
reproducible without it (`findBuildSpot` and the AI betrayal roll).

**(a) A save written by `a0dd101` — the Phase 0 commit, the oldest build a real player could have —
loads in the final build with an identical fingerprint.** 1,400 ticks of play on that build (46.7 s
of game time, so the AI had built, trained and moved), serialized to **216,682 bytes**, save format
`v: 2`. Both sides were fingerprinted *after* their own `deserializeGame`, so nothing is attributable
to the round trip itself:

| | `a0dd101` | final build |
|---|---|---|
| Fingerprint | **`5F0D31AF`** | **`5F0D31AF`** |
| Differing lines | — | **0 of 8,173 characters** |
| Covered | 25 units (incl. the in-flight `u.path`), 5 buildings, 292 nodes, 8 sites, 22 ambient, all players' age/resources/pop, `game.time`, `rngState`, `options`, and rolling hashes of terrain type/variant/elevation/moisture/temperature/slope, `blocked`, `water`, `bridges` | identical |

300 further ticks ran clean, 0 page errors. `game.shoreTiles` — a Phase 4e derived structure that
did not exist in `a0dd101` — rebuilt to match an independent brute-force scan exactly (**115/115**),
bridge exclusions included. Re-run after this phase's code change: identical fingerprint again.

**(b) In-build save/load round trip through a real page reload**, via the game's own
`saveGameToSlot` / `loadGameFromSlot` on the untouched key `albion.save.4`. Cairn Fields, 3 enemy
factions, 900 ticks, **220,573 bytes**: `EFCD0FA6` -> **`EFCD0FA6`**, **0 differing keys**, 200
further ticks clean, slot removed afterwards, 0 page errors. `albion.settings` verified separately
by write and read-back on the untouched key (76 B, `panSpeed` 1.42 round-tripped).

#### 5. Offline — full playability, zero outbound requests

Served with `python -m http.server` on `127.0.0.1:8101`, with Edge launched under
`--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1` so **every non-loopback host is
unresolvable**. That is the closest faithful stand-in for pulling the cable that still leaves the
local server reachable: a CDN fetch would fail hard here.

- **19 requests, every one to `127.0.0.1:8101`** (plus the inline `data:image/svg+xml` noise
  texture). **0 external requests.** `window.PIXI` and `AlbionFramework` are both `undefined`.
- **Fully playable**: Mirkfen Marsh with 3 enemy factions, `artReady` true, 8 material + 3 transition
  patterns, 5 owner-tinted unit atlas bakes, 220 shore tiles, 1,600 sim ticks driven through with
  combat resolving (27 -> 36 units, 7 buildings), 21.37 fps. The screenshot shows fully textured
  terrain, owner-tinted units mid-fight, buildings, minimap and HUD — nothing degraded.
- **Saving works offline** (localStorage only): 249,603 B written and loaded back, 36 units restored.
- Only two diagnostics, both pre-existing and neither an outbound request: the `favicon.ico` 404 and
  one `net::ERR_ABORTED` on the inline `data:` URL.

PixiJS was the only CDN dependency and Phase 4e removed it, so this passes cleanly, as expected.

#### 6. `MAX_DPR` 1.5 — plan risk #8, the one genuinely open item

**There is no hi-DPI panel on this rig** (`devicePixelRatio` 1.5), so no verdict is faked here.
`devicePixelRatio` was forced with CDP `Emulation.setDeviceMetricsOverride` at 2 and 3, and capped
(`MAX_DPR` 1.5) was compared against uncapped (`MAX_DPR` raised to the emulated ratio at runtime
followed by `sizeCanvas()`) on the same seed, scene and camera. Screenshots were kept at every
setting. "Detail" is the mean |Laplacian| of luminance over a fixed CSS-space crop read back from the
world canvas with `getImageData`, normalised **per CSS pixel** so a larger backing store is not
credited merely for having more pixels.

| Emulated dpr | `MAX_DPR` | Backing store | Mpx | Detail / CSS px | fps | `renderMs` |
|---:|---|---|---:|---:|---:|---:|
| 1 | 1.5 (no-op) | 1400x676 | 0.95 | 36.81 | 27.89 | 4.89 |
| 1.5 | 1.5 (no-op) | 2100x1014 | 2.13 | 37.25 | 25.68 | 12.76 |
| 2 | **capped** | 2100x1014 | 2.13 | 37.25 | **23.21** | 11.92 |
| 2 | uncapped | 2800x1352 | 3.79 | 45.98 | 17.63 | 19.75 |
| 3 | **capped** | 2100x1014 | 2.13 | 37.25 | **23.90** | 12.19 |
| 3 | uncapped | 4200x2028 | 8.52 | 76.09 | 10.16 | 39.77 |

**What this does prove.** The cap works exactly as designed: at emulated dpr 2 and 3 the backing
store stays at the dpr-1.5 size, holding worst-case pixel fill at 2.25x instead of 4x and 9x. The
cost is real and measured — **−19% rendered detail per CSS pixel at dpr 2 and −51% at dpr 3** — and
at 3x magnification the capped render is visibly softer on grass grain, roof shingles and armour
detail. The benefit is larger: **+32% fps at dpr 2** (23.21 vs 17.63) and **+135% at dpr 3** (23.90
vs 10.16), with `renderMs` down 40% and 69%. Uncapped at dpr 3 the game runs at ~10 fps, which is
not shippable.

**What this does not prove.** Whether a 1.5x backing store *looks acceptable to a human* on a real
2x or 3x panel. The physical display here is 1.5x, so every screenshot above is resampled down onto
it before anyone can look at it. That is a question about perception on hardware this rig does not
have, and emulation cannot answer it.

**Verdict:** plan risk #8 moves from *unverified* to **"the code path is verified and the trade is
quantified; the perceptual call still needs a real hi-DPI display."** The recommendation is to keep
1.5 as the default — the dpr-3 frame rate makes that decision on its own. Per the plan, if a hi-DPI
owner does object, expose it as a render-scale setting rather than reverting; that was deliberately
**not** done speculatively here, since nobody has yet seen it on the hardware in question.

#### 7. All five `MAP_PRESETS` still generate

60 worlds (5 presets x 3 seeds x compact/standard x standard/harsh gates), the same matrix the
Phase 6 log used. All 60 generated, **0 page errors**.

| Preset id | `flavor` | Display name | Nodes | Water tiles | Bridges | Distinct hashes / 12 |
|---|---|---|---:|---:|---:|---:|
| `greatwood` | `woodland` | Heartwood Crossing | 345-359 | 131-227 | 13-33 | 6 |
| `darkwood` | `marsh` | Mirkfen Marsh | 382-422 | **201-346** | **29-43** | 7 |
| `barrowfields` | `downs` | Cairn Fields | **333-353** | 131-227 | 13-33 | 6 |
| `brightwood` | `vale` | Sunglade Vale | 377-393 | 131-227 | 13-33 | 6 |
| `snowspire` | `alpine` | Frostcrag Pass | 298-378 | 131-227 | 13-33 | 12 |

The numbers confirm the documented design rather than contradicting it. `woodland`, `vale` and
`alpine` share the default hydrology (identical water and bridge ranges), while **`marsh` alone**
shifts stream count, stream width and pond count (darkwood's 201-346 water tiles) and **`downs`
alone** shifts the `placeProceduralWilds` weight table (barrowfields' lower node counts) — which is
exactly the "only `marsh` and `downs` change behaviour" note. Node counts still differ across all
five because `preset.neutral` and `preset.terrain` differ.

Three presets producing 6 distinct hashes over 12 worlds means the terrain-gate setting does not
change generation there: gates change traversal rules and only reach worldgen through
connectivity-corridor stamping, which those maps never need. `darkwood` (7) and `snowspire` (12) do
need it, so their gates do change the world.

#### Deviations from the plan

1. **One production fix: save-slot labels no longer stale, and it is not a `LEGACY_MAP_NAME` table.**
   Phase 6 finding 1 recorded this as cosmetic. On inspection it is a small **rebrand hole**, not
   merely a stale string: `serializeGame().meta` freezes display strings at write time, so a
   pre-rebrand save's load-slot row can show `Snowspire Pass`, `Darkwood Marsh`, `Barrow Fields`,
   `Brightwood Vale`, `Albion Renown`, `Guild Charter` or `Archon's Legacy` — Fable-derived names
   back in the shipped UI, which is precisely what Phase 6 removed. Reproduced live: the real
   `a0dd101` save labelled itself "Greatwood Crossing".

   Fixed in `slotInfo` (11 lines). The plan's suggested `LEGACY_MAP_NAME` lookup was **rejected in
   favour of deriving the label from the ids the save already stores** — `options.mapId` through
   `MAP_PRESETS[...].name`, and `players[0].age` through `ageDisplayName()` — with the stored strings
   kept as the fallback. That is strictly better than a rename table: it needs no map, it fixes the
   **age** label as well as the map label, and it can never go stale on a future rename.
   `serializeGame` is untouched, so `meta` is written exactly as before and a new save still loads in
   an older build. Verified: the real `a0dd101` save now reads "Heartwood Crossing"; all five legacy
   map names and all four legacy age names resolve to current names; saves with absent or unknown
   ids keep their stored strings; a corrupt slot still reads "Corrupt slot"; an empty slot still
   returns `null`; a save written by this build is unaffected and its stored `meta` is unchanged.
   0 page errors. Both save gates and the art-preview hash were re-run **after** this edit and are
   unchanged.

2. **The plan's Phase 7 asks for "a check on the actual hi-DPI display".** There is no hi-DPI display
   on this rig, so that item was executed as emulation with an explicit statement of what emulation
   can and cannot establish — see item 6. It is recorded as partially closed, not closed.

3. **"Filtered `drawImage` and shadow-blur absent from the flame chart" was verified with counters
   rather than by reading a flame chart.** A sampled flame chart cannot prove an absence, and the
   doc's own standing rule is to measure in isolation where possible. Direct property counters give
   an exact per-frame number (226.83 -> 0), which is a stronger claim than the plan asked for. The
   CPU profile was still taken, and is reported alongside.

#### Findings worth carrying forward

1. **`ctx.filter` was on essentially every blit, not merely many of them.** 2,722 of 2,746
   `drawImage` calls in a before-build battle frame were filtered. Phase 0's "`ctx.filter` is not
   merely the largest render cost, it is essentially the *only* one" was, if anything, understated.
2. **The remaining idle cost is not JavaScript.** At 41.35 ms idle the build spends 1.45 ms in
   `renderMs`; the rest is raster, compositing and vsync. Getting idle past 30 fps would need
   fill-rate work — the 2880² backdrop blit and overdraw — which no phase of this plan scoped.
3. **Absolute frame rates are session-scoped on this rig; ratios are not.** The same before/after
   pair measured 2.4x/14.5x in the Phase 4 session and 2.29x/12.2x here, on identical code and an
   identical harness, while every absolute moved ~30%. Never compare an absolute across sessions;
   always interleave.
4. **A save-format `meta` block is a rebrand liability.** Any display string frozen into persisted
   data outlives the rename that was supposed to remove it. Deriving labels from stored ids at read
   time is the general fix, and it is cheaper than a migration.
5. **Emulated `devicePixelRatio` is enough to verify a DPR code path and quantify its trade, and
   not enough to settle it.** Worth remembering the distinction rather than recording a verdict the
   instrument cannot support.

#### Verification summary

- Inline script extracted and `node --check`ed: **clean** (1 block, 11,129 lines).
  `git diff --check`: clean. `index.html` and this file are the only changed files.
- 0 page errors in every run of every harness above, except the pre-existing `favicon.ico` 404 on
  HTTP loads and one `net::ERR_ABORTED` on an inline `data:` URL. Neither is an outbound request and
  neither is new.
- Grep gate re-run after the code change and enumerated by identifier form, not just by count. It
  returns **only** the keep-list: 68 `ALBION_ART.*` / `albionArtImages` occurrences, 3
  `albion.settings` / `albion.save.*`, 15 `hobbeWild`, 10 `balverine`, 8 `demonDoor` + 2
  `DemonDoorSite`, the 7 `brightwood`/`snowspire` preset-id hits, and the 2 disclaimer strings. No
  player-visible string survives.

---

## No further phases

**The overhaul is complete.** Bootstrap and Phases 0 through 7 are all `done` and pushed, and
Phase 7 was the last phase in the plan. There is no continuation prompt: nothing is outstanding and
no agent should pick this up expecting more work.

Where things landed against the plan's own targets:

| Target | Result |
|---|---|
| Battle < 25 ms avg | **met** — 47.88 ms this session, 30.45 ms in the Phase 4 session; 12-14x better than baseline either way |
| Idle < 16.7 ms avg | **not met** — 41.35 ms, of which 1.45 ms is JavaScript. The rest is raster and vsync; closing it needs fill-rate work that no phase scoped. |
| Payload ~15 MB | **met** — 12,823,088 B (12.23 MiB) over 19 requests, from 49.50 MiB / 20 |
| One `buildTerrainBackdrop` per load | **met** |
| Two visual states during load | **met** |
| `applySeparation` near zero | **met** — 0.0292 ms of a 0.400 ms tick at 225 units |
| No per-entity `ctx.filter`, no per-frame `shadowBlur` | **met** — 0 filtered `drawImage` per frame, 0 `shadowBlur` writes per frame |
| Save compatibility | **met** — a `a0dd101` save loads with an identical fingerprint |
| Offline playability, no CDN | **met** — 0 external requests with all non-loopback hosts unresolvable |
| Clean rebrand | **met** — grep gate returns only the keep-list; old saves no longer surface old names |

Two items are deliberately left open rather than closed, both recorded above:

1. **`MAX_DPR` 1.5 on real hi-DPI hardware** (plan risk #8). The code path is verified and the
   sharpness/frame-rate trade is quantified under emulation, but the perceptual call needs a display
   this rig does not have. If it ever reads too soft to an owner on a 2x or 3x panel, the plan's
   answer stands: make it a render-scale setting, do not revert.
2. **Idle frame rate is raster-bound, not JS-bound.** The next real win there is fill rate — the
   2880² backdrop blit and overdraw — and it is a new piece of work, not a leftover from this plan.

The two Phase 5 sim caveats also remain by design, neither being a defect to fix here: `findBuildSpot`
and the AI betrayal roll use unseeded `Math.random()`, so the sim is not reproducible without pinning
them in a harness; and the separation spatial hash is exact only below ~36 units in one 38x38 px cell
(the measured real-game peak is 10, and 2 in the state sampled this phase).
