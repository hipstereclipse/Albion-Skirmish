# Overhaul plan — performance, terrain art, and clean IP rebrand

**Status:** approved, in execution. Live progress and the next-agent handoff prompt live in
[OVERHAUL-PROGRESS.md](OVERHAUL-PROGRESS.md). This file is the frozen specification — change it only
if the approach itself changes, and note the deviation in the progress log.

All line numbers refer to `index.html` **as of the baseline commit** (see progress doc). They will
drift as phases land; treat them as starting hints and confirm by reading the surrounding code.

---

## Context

The game is a single-file canvas RTS ([`index.html`](../index.html), ~11,350 lines) with three problems:

1. **It lags.** Verified root causes: per-unit and per-building `ctx.filter` with `drop-shadow` every
   frame, `shadowBlur` scattered through the render path, O(n²) unit separation, full minimap redraw
   every frame, per-frame gradient allocation, device pixel ratio up to 2.5 (6.25x pixel cost), and a
   second PixiJS renderer (CDN-loaded) that rebuilds water-shore geometry every frame for a cosmetic
   shimmer.
2. **Terrain loads in three ugly stages.** Each of ~12 terrain PNG `onload`s sets `terrainReady=false`
   (lines 1220/1223/1228), triggering repeated full 2880×2880 backdrop rebuilds.
   `drawHexTerrainMaterials` returns true when *any* pattern exists (line 7319), which kills the
   painterly passes while most hexes still show flat fallback colors — hence: painterly look → bare
   hex grid → dark textures. The final look is dark and low-contrast because of a near-black elevation
   wash (`#07100a` at up to 18% alpha, 7277-7280), visible hex outlines (7282-7287), heavy transition
   strokes (7308), the loss of the painterly highlight passes, dark source PNGs, and a strong vignette
   (7628). Also **68 MB of assets** — each terrain texture is 3.3 MB at 1254×1254, drawn into 26 px
   radius hexes (~24x oversampled per axis).
3. **Fable IP exposure.** ~11 player-visible Fable proper nouns (Albion, Bowerstone, Oakvale,
   Knothole, Brightwood, Snowspire, Hobbe, Balverine, Demon Door, Will magic, Heroes' Guild), the
   title "Albion Skirmish", and a README line saying "inspired by Fable: The Lost Chapters".
   Favorable facts: no publisher names or logos, no named Fable characters, no copied game assets
   (art is project-generated), no morality system.

**Decisions made by the owner:** keep the hex textures but fix contrast and loading (do *not* revert
to painterly-only); do a **clean rebrand** with original names (not parody riffs — what exists is
homage, and parody protection requires the work to actually comment on or mock the original, so a
rebrand is the strong position). *This is practical risk reduction, not legal advice.*

Phase ordering is deliberate: instrument → fix load and visuals → render perf → sim perf → rebrand
last, so performance diffs stay clean and measurable.

---

## Execution protocol — shared doc, auto-push, continuation prompts

This plan is executed phase by phase, possibly by different agents or sessions. Two in-repo documents
keep it on track (in-repo so every push carries them and any agent can recover state from GitHub):

- **`docs/OVERHAUL-PLAN.md`** — this file, the frozen specification.
- **`docs/OVERHAUL-PROGRESS.md`** — the living tracker: status table, phase log, and the current
  continuation prompt.

**Mandatory loop after completing each phase (no exceptions):**

1. Run that phase's verification (the relevant items from Phase 7) and record the results in the
   progress doc's phase log — actual numbers, not "looks fine".
2. Update the status table row to `done`, and rewrite the `## Continuation prompt` section for the
   *next* phase, filled in with the next phase number and name, any carry-over caveats discovered,
   and the current perf baseline numbers.
3. Commit everything for the phase as one commit: `Overhaul phase <N>: <short description>` (ending
   with the standard `Co-Authored-By` line), then `git push origin main`. If the push fails (auth or
   offline), record `push pending` in the status row and continue — never skip the commit.
4. Stop and report, or continue to the next phase if the session has budget. The doc must be correct
   either way, so an interrupted session loses nothing.

**Hard rule for every phase:** never rename internal identifiers (`hobbeWild`, `balverine`,
`demonDoor`, `willhub`, `guildspire`, `ALBION_ART`, CONFIG keys) or localStorage keys
(`albion.settings`, `albion.save.N`). They are invisible to players and load-bearing for saves.

---

## Bootstrap phase (before Phase 0)

- `.gitignore` for `.edge-art-preview/` (a 30 MB, 549-file browser-profile dump produced by
  `tools/capture_art_preview.mjs` that must never be pushed), plus Python bytecode and OS cruft.
- Commit the large uncommitted backlog as a baseline: modified `README.md`,
  `docs/screenshots/README.md`, `index.html` (a 3278-line diff), plus the entirely untracked
  `assets/` (68 MB), `tools/`, and new screenshots. Push the backlog to `origin/main`.
- Create `docs/OVERHAUL-PLAN.md` and `docs/OVERHAUL-PROGRESS.md`.
- Note for Phase 6: the GitHub repo itself is named `Albion-Skirmish`. Renaming it (for example to
  `eldervale-skirmish`) is part of the rebrand; GitHub auto-redirects the old URL, but the local
  remote needs `git remote set-url` afterward. Requires the owner's confirmation at that time,
  because it changes a public URL.

## Phase 0 — Instrumentation (do first, small)

- In `frame()` (11321-11340), time the sim `while` loop and `render()` with `performance.now()` into a
  fixed 120-sample ring buffer (`simMs`, `renderMs`, `frameMs`). Preallocate the buffer; no
  per-frame allocation.
- Perf HUD gated by `location.search.includes('perf')`: after the `renderMinimap()` call in `render()`
  (7621), `fillText` the avg and p95 of each timing plus the unit count.
- Temporary `console.count('buildTerrainBackdrop')` inside `buildTerrainBackdrop()` (7322) to prove
  the Phase 1 rebuild fix. Remove it at the end of Phase 1.
- **Capture the "before" numbers here** and record them in the progress doc — this is the baseline
  every later phase is measured against.

## Phase 1 — Kill the three-state pop-in (load sequencing)

- Replace the per-image `onload` handlers (1216-1228) with one preloader:
  `Promise.allSettled([...all ALBION_ART images].map(img => img.decode()))` — `allSettled` so a single
  404 cannot hang the game, and `decode()` to force off-main-thread decode. On resolve:
  `artReady = true; terrainReady = false;` → exactly **one** rebuild.
- `drawHexTerrainMaterials` (7244): make the gate all-or-nothing. Top becomes
  `if (!game.terrain || !artReady) return false;`; the return at 7319 becomes unconditional `true`
  (all patterns are guaranteed present once `artReady`). The pattern cache build now runs once.
- Result: two visual states only — the painterly procedural backdrop (already implemented as the
  `!drewSemanticTerrain` path, and what players see during load today) until art decodes, then one
  clean swap. The start menu masks most of it; optionally `notify('Painting the world…')` in
  `startGame()` (11217) when `!artReady`.

## Phase 2 — Fix the dark, low-contrast final look

Group these as named constants at the top of `buildTerrainBackdrop` so the look is tunable in one place.

1. **One-time brightness normalization at pattern build** (7247-7251): draw each material into a
   384×384 offscreen canvas; measure mean luminance from a 64×64 thumbnail via `getImageData`; redraw
   with `ctx.filter = 'brightness(k) saturate(1.05)'` where `k = clamp(0.52 / meanLuma, 0.95, 1.4)`;
   `createPattern` from that canvas. Store `k` per material for debugging. This lifts the muddy
   sources uniformly instead of hand-tuning eight files. (The same canvas is the Phase 3 downscale.)
2. **Elevation wash** (7277-7280): keep the highlight (`#f5ead0`) at `abs(e-.5)*.18`; drop the
   `#07100a` shadow to `abs(e-.5)*.09`.
3. **Hex outlines** (7282): alpha `.08 → .035`. This is the main "visible tile grid" offender.
4. **Transition strokes** (7308): `.68 → .48` for authored transition patterns, `.28 → .16` for
   generic material blends.
5. **Layer the painterly character back over the textures** (the part the owner liked): un-gate the
   meadow `soft-light` pass (7338) so it always runs, with
   `globalAlpha = drewSemanticTerrain ? .14 : .26`; likewise un-gate the sun-dapple ellipse pass and
   the painterly stroke pass at roughly 50% of their alphas. Keep gated (skipped over textures): the
   per-tile grass loop and the `multiply` shade-blob pass — `multiply` darkens, which is the complaint.
6. **Vignette** in `drawAtmosphere()` (7628): edge stop `rgba(8,7,5,0.42) → 0.20`.
7. Verify with `tools/capture_art_preview.mjs` screenshots (repeatable, same seed). Checklist: no
   visible hex lattice at default zoom; meadow reads green, not olive-black; snow and sand are not
   blown out (the per-material `k` clamp guards this); soft-light dapple still visible.

## Phase 3 — Asset weight (~68 MB → ~15 MB)

- **New `tools/downscale_terrain.py`** (PIL, mirroring the style of `build_sprite_atlases.py`):
  resize `assets/terrain/materials/hex-*.png` and `assets/art/albion-meadow-v2.png` to **384×384**,
  and `assets/terrain/transitions/*.png` to **512×512** (the strip crop at 7259 uses `naturalWidth`
  fractions, so it is resolution-independent — verified). Write with `optimize=True`. Targets: ≤150 KB
  per material, ≤250 KB per transition. Overwrite in place; the baseline commit keeps the originals
  and the relative paths do not change, so static hosting is unaffected. Terrain payload ~43 MB → ~2 MB.
- **Do not resize the sprite atlas files.** `buildingSlices` overhang offsets (1191-1197),
  `unitCellSize: 256` (1201), and `assets/sprites/atlas-manifest.json` are all in atlas pixels.
  Their runtime cost is handled by the Phase 4 half-resolution bake instead.
- Delete the two confirmed-unreferenced deployed assets (grep-verified: neither appears in
  `index.html`): `assets/art/albion-meadow.png` (3.2 MB, superseded by `-v2`) and
  `assets/sprites/albion-units.png` (1.4 MB, superseded by `-animated`). Keep
  `assets/sprites/albion-resources-v2.png` — it is a build input for `build_sprite_atlases.py`.
- Optional: a lossless or palette-reduction pass (`pngquant`-style) on the remaining sprite atlases.
  Color reduction does not change dimensions, so the offset contracts stay valid.

## Phase 4 — Render hot path (the biggest FPS wins, in impact order)

1. **Pre-baked owner-tinted unit atlases** — kills the number-one cost, the per-unit `ctx.filter` at
   7665 whose string is built at 8366-8371. After the Phase 1 preloader resolves, bake five offscreen
   canvases (owners 0-3 plus `CREEP_OWNER`) at **half resolution** (cell 128 — units render at ≤64 px,
   so this is still 2x oversampled; five half-res copies ≈ 26 MB, versus ~105 MB at full res). Apply
   the owner filter string *minus* the `drop-shadow` term once per bake.
   `drawAnimatedAtlasFrame` (7655-7669) takes `image` and `cell` parameters instead of hardcoding
   `ALBION_ART.units`/256, and no longer sets `ctx.filter`. Restore the lost drop-shadow with the
   existing cheap `drawShadow()` ellipse before the sprite blit.
2. **Pre-baked biome building atlases** — same trick for `buildingBiomeFilter` (8150-8156), which
   never returns an empty string, so every building pays a filter today. Bake five variants
   (snow/forest/marsh/dry/default) of the small buildings atlas at full resolution; remove
   `ctx.filter` at 8397 and 8423 and pick the atlas by `b.visualBiome`.
3. **Building aura** (8380-8384): pre-render two 64×64 radial-gradient sprites (blue and red) once;
   per building do a `drawImage` scaled to the ellipse rect with `globalAlpha`. Removes one
   `createRadialGradient` per building per frame.
4. **`shadowBlur` purge** (8388, 8787, 8851, 8935, 9335, 9353, 9414): replace each with either a
   second lower-alpha stroke (selection rings and rects) or a pre-rendered glow sprite (projectiles
   and effects). `shadowBlur` forces a blur pass per draw call.
5. **Minimap** (9634-9671): keep the existing `mmTerrain` cache; add an `mmEntities` offscreen canvas
   rebuilt at 10 Hz (or on `mmDirty`). Per frame, composite terrain + entities + pings + camera rect
   only. The buildings, sites, and units loops move into the 10 Hz rebuild.
6. **`drawAtmosphere`** (7624-7637): render both gradients once into an offscreen canvas sized
   `viewW × viewH`, rebuilt only in `sizeCanvas()`; per frame do a single `drawImage`.
7. **`MAX_DPR` 2.5 → 1.5** (1263): caps worst-case pixel fill at 2.25x instead of 6.25x. The HUD is
   HTML, so text stays crisp. Optionally expose it as a render-scale setting later.
8. **Remove PixiJS** — `PIXI_CDN` and `AlbionFramework` (1878-1963) plus call sites (6723-6724, 6731,
   11337, 11348) and the `#pixi-layer` div and CSS. Replace the shore shimmer with a canvas-native
   pass after `drawTerrain`, driven by a **precomputed `game.shoreTiles` list** built at world-gen,
   in `deserializeGame`, and on bridge changes (carrying over the bridge exclusions at 1944/1948) —
   the per-frame 4-neighbor water scan is the cost, not the strokes. Draw the same animated dashes
   with `ctx` strokes for visible shore tiles only. Also removes a CDN dependency that already breaks
   silently offline, plus a whole second WebGL context.
9. Cheap: hoist the per-frame `ents` array (7578) to module scope and use `ents.length = 0`.

## Phase 5 — Sim hot path

1. **Spatial hash for `applySeparation()`** (5111-5139): a reusable module-level grid (cleared, never
   reallocated) with cell size `CONFIG.SEPARATION.CHECK_DIST`. Insert all live, non-transported units,
   then test each unit only against its 3×3 cell neighborhood with an `indexA < indexB` guard so each
   pair runs once. The inner pair logic (5120-5136) is unchanged. At ~250 units this goes from ~31k
   pair tests per tick to a few hundred.
2. **Allocation-free A\* costs**: add `terrainStepCost(tx, ty, mode, equipment) -> number`
   (`Infinity` means blocked) mirroring the logic of `terrainTraversalAt` (2253-2270) without the
   per-call object literal. Resolve `movementModeForType` and `terrainEquipmentFor` once *before* the
   A\* loop (3428) and `followPath` (3505) and pass them in. Keep the object-returning version for UI
   tooltips and placement reasons.
3. Low priority: reuse a scratch array in `computePath` (3476) instead of `tiles.map(...)`.

## Phase 6 — Clean rebrand (display strings and filenames; internal ids stay)

**Principle: rename what players see and what files are called; keep internal ids and localStorage
keys.** `serializeGame` (10786-10831) stores entities whole, including their `type` and `role`
strings, so renaming ids breaks every existing save and every `CONFIG.BUILDINGS[b.type]` lookup.

1. **First, decouple rendering from display names** (tripwire): `buildTerrainBackdrop` branches on
   `/Snowspire/i` (7338) and `/Darkwood/i` (7342) against `preset.name`, and similar checks exist near
   2185-2186, 7482, 7491, and 2630 (`indexOf('Barrow')`). Add a `climate` (or `flavor`) key to the map
   presets — the `<option value>` ids at 548-552 are already stable — and switch those tests to it.
   Only then are display names safe to change.
2. **Rename table** (display strings only; per-term `grep -n` plus hand review — no blind `sed`,
   because "Will" collides with ordinary English):

   | Current | New |
   |---|---|
   | Albion Skirmish (title line 6; README H1) | **Eldervale Skirmish** |
   | Albion (world; Age "Albion Renown"; building prefixes) | Eldervale |
   | Bowerstone (Trade Hub / Market / School Shed) | Bridgemere |
   | Oakvale ("Oakvale refugees"; faction) | Elmshire |
   | Knothole (Guard Hub; Glade site) | Thornhollow |
   | Brightwood (Vale; Will Hub) | Sunglade |
   | Greatwood (Crossing; Oak) | Heartwood |
   | Darkwood (Marsh; biome) | Mirkfen |
   | Snowspire (Pass) | Frostcrag |
   | Barrow Fields | Cairn Fields |
   | Hobbe (Wild Hobbe; Den / Bruiser / Shaman / King) | Grubkin |
   | Balverine | Moorfang |
   | Demon Door (3 sites) | Riddle Gate |
   | Will (Adept / Hub / Studies / pool / -light) | Aether |
   | Heroes Guild Spire / Guild Hall / Guild Hero | Wardens' Lodge Spire / Lodge Hall / Warden |
   | Archon's Legacy (Age) | Sovereign's Legacy |
   | Old Kingdom (Ore / Obelisk / Shrine / Studies) | Elder Kingdom |

   Surfaces: line 6, 548-552, 855-964, 1027-1054, 1273-1321, 1478-1498, the hero-death string at
   ~3718, endgame text at ~11309-11310, plus `README.md`, `docs/implementation-notes.md`, and the
   asset READMEs.
3. **Asset and file renames**: `assets/**/albion-*.png` → `eldervale-*.png`; update the `src`
   assignments (1216-1219), the CSS title-vista background (line 352), output paths in
   `tools/build_sprite_atlases.py`, and `tools/capture_art_preview.mjs` (which writes
   `docs/screenshots/fable-*.png`). Regenerate `assets/sprites/atlas-manifest.json` via the tool.
   Rename `docs/screenshots/fable-*.png` and the references in `docs/screenshots/README.md`.
4. **README and docs rewrite**: remove "inspired by Fable: The Lost Chapters" and the "Age of
   Empires-style" phrasing (→ "an original fantasy RTS with classic RTS controls"). Rewrite the
   provenance section of `assets/sprites/README.md` so it stops art-directing against a "TLC character
   reference" going forward, while staying honest that the art is project-generated. If the hero
   sprite's blue cloak reads as the Fable Hero, adjust that palette at bake time or in the source art.
5. **Disclaimer**: add to the README and the start-menu footer — "An original fan-made game. Not
   affiliated with, endorsed by, or connected to Microsoft, Lionhead, or the Fable franchise."
6. **Verification gate**:
   `grep -rniE 'albion|bowerstone|oakvale|knothole|brightwood|snowspire|hobbe|balverine|demon ?door|heroes.{0,2}guild|fable'`
   (excluding `.git` and `.edge-art-preview`) must return only the documented keep-list — internal
   ids and storage keys. Land the rebrand as one dedicated commit after all perf work.

## Phase 7 — Verification (end to end)

- **Perf before and after**, using the Phase 0 HUD with the same map seed: (a) a four-player map,
  60 s of continuous panning while idle — record avg and p95 frame ms; (b) a battle stress test of
  roughly 100 v 100 units spawned near the camera via a console snippet using the game's own spawn
  path (do not commit the snippet) — record avg frame ms during the fight; (c) a check on the actual
  hi-DPI display, which matters for the `MAX_DPR` change. Take a 10-second DevTools Performance
  capture during (b) before and after: filtered `drawImage` and shadow-blur rasterization should
  disappear from the flame chart, and `applySeparation` self-time should collapse.
- **Load**: Network tab with cache disabled — total payload ~68 MB → ~15 MB; `buildTerrainBackdrop`
  fires exactly once; only two visual states appear.
- **Art**: same-seed screenshots before and after via `tools/capture_art_preview.mjs`, checked against
  the Phase 2.7 contrast checklist.
- **Saves**: save in the old build, load in the new build (must work, since ids and keys are
  unchanged); then a save/load round trip within the new build.
- **Offline**: serve with `python -m http.server`, disconnect the network, confirm no CDN fetch (Pixi
  is gone) and full playability.

## Risks

1. **Save compatibility** — any internal id or storage-key rename breaks loads. Mitigated by not
   renaming them. If ever required, it needs a `LEGACY_ID_MAP` applied in `deserializeGame` over
   `units[].type`, `sites[].type`, and `ambient[].role`, as a separate follow-up.
2. **Preset-name regexes** (7338, 7342, 2630) silently change terrain rendering if display names are
   renamed before Phase 6.1 lands.
3. **Tinted-atlas memory** — the unit atlas must be baked at cell 128; five full-resolution copies
   would cost ~105 MB. Also, `ctx.filter` on the bake canvas is a no-op on very old Safari, so sprites
   would render untinted there — no worse than today, since per-frame `ctx.filter` is equally
   unsupported.
4. **Atlas offsets** — never resize the sprite atlas files; `buildingSlices`, `unitCellSize`, and
   `atlas-manifest.json` all assume the current dimensions. Phase 3 explicitly avoids this.
5. **Pixi removal** — grep for stray `AlbionFramework` and `PIXI` references before deleting;
   re-verify the shimmer on lake shores and bridges; bridge construction must invalidate `shoreTiles`.
6. **Contrast is subjective** — keep every knob as a named constant so the owner can iterate, and keep
   the painterly-only path intact as a fallback (it is also the "drop the textures entirely" option).
7. **384² tiling artifacts** — materials repeat roughly every 7 hexes; if the repeat is visible, bump
   materials to 512² (still ~97% smaller than today).
8. **DPR 1.5 softness** on retina displays — if the owner objects, make it a settings toggle rather
   than reverting.
