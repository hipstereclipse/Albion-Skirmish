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
| 0 | Instrumentation: frame timing ring buffer + `?perf` HUD, capture BEFORE numbers | **done, pushed** | `a0dd101` Overhaul phase 0: add frame timing instrumentation and perf HUD | 2026-07-25 |
| 1 | Kill the three-state terrain pop-in (single preload gate, all-or-nothing material gate) | **done, pushed** | Overhaul phase 1: single art preload gate, one terrain rebuild | 2026-07-25 |
| 2 | Fix dark/low-contrast terrain (brightness normalization, softer washes/outlines, painterly relayer) | **done, pushed** | Overhaul phase 2: brighten terrain and restore painterly character | 2026-07-25 |
| 3 | Asset weight: `tools/downscale_terrain.py`, 384²/512² re-export, delete 2 dead PNGs | **done, pushed** | Overhaul phase 3: shrink terrain asset payload | 2026-07-25 |
| 4a | Pre-baked owner-tinted unit atlases (half-res, no per-unit `ctx.filter`) | **done, pushed** | Overhaul phase 4a: pre-bake owner-tinted unit atlases | 2026-07-25 |
| 4b | Pre-baked biome building atlases + baked resource-variant atlases | pending | | |
| 4c | Aura sprites, `shadowBlur` purge | pending | | |
| 4d | Minimap 10 Hz entity cache, cached atmosphere, `MAX_DPR` 1.5, `ents` hoist | pending | | |
| 4e | Remove PixiJS, canvas-native shore shimmer from precomputed `game.shoreTiles` | pending | | |
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

Two rows above have since been met and are no longer current: the rebuild count was fixed in Phase 1
(now 1) and the payload in Phase 3 (**now 12.34 MiB over 20 requests**, `assets/` 25.62 MB on disk).
The frame-time and `applySeparation` rows are still accurate — no phase has touched render or sim code.

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

---

## Continuation prompt

Copy this verbatim into a fresh agent/session to continue the work.

```
Continue the Albion Skirmish overhaul in c:\Users\Eclipse\.claude\Workspaces\Age Of Empires.

Read docs/OVERHAUL-PLAN.md (the full frozen spec) and docs/OVERHAUL-PROGRESS.md (status, baseline
numbers, phase log) before touching anything. Bootstrap and Phases 0–3 are complete and pushed.
Phase 3 shrank the terrain sources to 384x384 (materials + meadow) and 512x512 (transitions) via the
new `tools/downscale_terrain.py`, deleted the two dead PNGs, and cut the cache-disabled payload from
49.50 MiB to 12.34 MiB over the same 20 requests. No render code changed, so the fps baseline stands.

Execute **Phase 4 — Render hot path**, the biggest FPS win in the whole overhaul. Work in the plan's
impact order. Phase 4 is large: land it as sub-commits (`Overhaul phase 4a: …`, `4b`, …), and update
this doc + push after each one.

  1. Pre-baked owner-tinted unit atlases. This is the single most important change in the overhaul.
     After the Phase 1 preloader resolves, bake five offscreen canvases (owners 0-3 plus CREEP_OWNER)
     at HALF resolution (cell 128 — units render at <=64 px, so still 2x oversampled; five half-res
     copies ~26 MB versus ~105 MB at full res). Apply the owner filter string MINUS its `drop-shadow`
     term once per bake. `drawAnimatedAtlasFrame` (currently line 7732; it hardcodes
     `ALBION_ART.units` and `ALBION_ART.unitCellSize` at 7733) must take `image` and `cell`
     parameters and must no longer set `ctx.filter`. Restore the lost shadow with the existing cheap
     `drawShadow()` ellipse (line 6872) before the sprite blit.
  2. Pre-baked biome building atlases. `buildingBiomeFilter` (line 8227) never returns an empty
     string, so every building pays a filter today. Bake five variants (snow/forest/marsh/dry/default)
     of the buildings atlas at FULL resolution, remove the per-building `ctx.filter`, and select the
     atlas by `b.visualBiome`.
  3. Building aura: pre-render two 64x64 radial-gradient sprites (blue, red) once; per building
     `drawImage` them scaled to the ellipse rect with `globalAlpha`.
  4. `shadowBlur` purge: replace each with a second lower-alpha stroke (rings/rects) or a
     pre-rendered glow sprite (projectiles/effects). Real but small — Phase 0 measured it at under
     1.5x, so do not expect it to move the headline number.
  5. Minimap (`renderMinimap`, line 9711): keep the `mmTerrain` cache, add an `mmEntities` offscreen
     canvas rebuilt at 10 Hz or on `mmDirty`; per frame composite terrain + entities + pings + camera
     rect only.
  6. `drawAtmosphere` (line 7701): render both gradients once into a `viewW x viewH` offscreen canvas
     rebuilt only in `sizeCanvas()`; per frame do one `drawImage`.
  7. `MAX_DPR` 2.5 -> 1.5 (line 1272, `THEME.RENDER.MAX_DPR`; consumed at 6723 and 1912).
  8. Remove PixiJS: `PIXI_CDN` (1888) and `AlbionFramework` (1889-…) plus call sites (6741, 11525,
     11537), the `#pixi-layer` div and its CSS. Replace the shore shimmer with a canvas-native pass
     after `drawTerrain`, driven by a PRECOMPUTED `game.shoreTiles` list built at world-gen, in
     `deserializeGame`, and on bridge changes (carry over the existing bridge exclusions) — the
     per-frame 4-neighbour water scan is the cost, not the strokes. Grep for stray `PIXI` /
     `AlbionFramework` before deleting.
  9. Cheap: hoist the per-frame `ents` array (line 7654) to module scope and use `ents.length = 0`.
     Note there is an unrelated `ents` at 10118 — do not touch it.

Measure with the Phase 0 `?perf` HUD on the SAME map and seed as the baseline (Greatwood Crossing,
4 players) and report fps, not `renderMs` — see the "Read frameMs and renderMs with care" note in the
progress doc. Re-run `tools/capture_art_preview.mjs` and confirm the seeded gallery still matches the
Phase 2 checklist with 0 page errors. Syntax-check the inline script, run `git diff --check`, and
verify a save/load round trip still works.

Baseline to beat (Phase 0, still current — Phase 3 changed no render code): idle pan 255.1 ms avg /
399.8 ms p95 (3.9 fps) on a 4-player Greatwood map; ~100v100 battle 1006.9 ms avg (1.0 fps);
applySeparation 2.49 ms of a 3.05 ms sim tick. Targets: <16.7 ms avg idle, <25 ms p95 and battle.
Phase 0 measured that neutralising `ctx.filter` alone is worth ~14x at idle and ~13x in battle, so
items 1 and 2 carry nearly all of the win — do them first and measure before continuing.

Carry-overs:
  - Payload is now 12,939,974 B (12.34 MiB) over 20 requests, cache disabled; `assets/` on disk is
    25.62 MB. Record deployed payload and working-tree size distinctly. The remaining bulk is the
    three sprite atlases plus the title vista (9.7 MB of 12.34 MB) — the Phase 4.1 half-res bake is
    a runtime-memory win, not a payload win.
  - Do NOT resize any sprite atlas file. `buildingSlices`, `unitCellSize: 256` (line 1201), and
    `assets/sprites/atlas-manifest.json` are all in atlas pixels. Phase 4.1 bakes at half resolution
    at RUNTIME; the files on disk stay as they are.
  - `ctx.filter` on a bake canvas is a no-op on very old Safari, so sprites would render untinted
    there — no worse than today, since per-frame `ctx.filter` is equally unsupported.
  - Terrain sources are now palette PNGs (256/224 colours) at 384²/512². This is a deliberate Phase 3
    deviation, documented with a PSNR gate in the Phase 3 log. Do not "fix" it back to truecolor
    without also raising the size budgets in `tools/downscale_terrain.py`.
  - `tools/downscale_terrain.py` is idempotent and skips sources already at target size; re-running it
    is safe and will report `unchanged` for all 12.
  - `tools/capture_art_preview.mjs` loads `file://` and launches Edge with
    `--allow-file-access-from-files` because the Phase 2 `getImageData()` luminance audit otherwise
    taints the canvas. Do not remove that flag while Phase 2 normalization remains runtime code.
    Its seed is `overhaul-art-preview-v1`; the Phase 3 reference capture hashes SHA-256
    91A8C69D5E47266F5A738283C587A40F082F000E6D25082D0A77EFB1EDA7718C.
  - A `favicon.ico` 404 appears on every HTTP load. It is pre-existing and not yours to chase.
  - Line anchors above are current as of the Phase 3 commit and WILL drift as 4a/4b land. Re-resolve
    them by reading the surrounding code; `git show dd3e70a:index.html` still resolves plan anchors.
  - Do NOT rename internal ids or localStorage keys (breaks saves) — `serializeGame` stores entity
    `type`/`role` strings whole.
  - Do NOT start the rebrand (Phase 6) or the sim work (Phase 5, spatial hash + allocation-free A*).

When each Phase 4 sub-phase is done: log the before/after fps for that change, the verification
results, and any deviation in docs/OVERHAUL-PROGRESS.md; update the status table; commit as
"Overhaul phase 4<letter>: <description>"; and push to origin main. Regenerate this continuation
prompt when Phase 4 is fully complete.
```
