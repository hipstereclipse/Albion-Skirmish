# Implementation Notes

## July 2026 Tranquil Kite Expansion

This pass extends the single-file RTS across building lifecycle controls, water generation/rendering, farming, automation, start configuration, pause/settings/statistics, diplomacy, touch input, and local save/load.

### Building Lifecycle And Economy
- Box select now follows an AoE-style rule: owned units win the marquee, otherwise owned buildings in the rectangle are selected.
- Own buildings expose cancel/demolish controls with armed confirmation; foundations refund full cost, completed buildings refund 30%.
- Same-type building selections can batch upgrade, and completed wall segments can convert in place to gates or compact watch towers while preserving HP fraction.
- Farms are regular buildings with linked renewable food nodes, so villager gathering, carrying, drop-off, stats, and auto-needs all reuse the existing resource pipeline.
- Guild Hall priority presets now drive player `resourceNeedOrder`, with per-resource low/normal/high bias chips.

### Map, Rendering, And Controls
- Pond placement is deterministic rejection sampling that avoids roads, town-center clearings, and tiny one-tile lakes.
- Bridges are derived from trail-water runs and stored as `bridgeSpans`; a connectivity fix-up stamps bridge runs when land BFS cannot reach an enemy town center.
- Terrain, minimap, and shoreline effects now draw from the water/bridge tile masks instead of translucent pond ellipses.
- Touch input supports select-mode marquee selection, command-mode pan, and two-finger pan/pinch zoom.

### UI, Automation, And Persistence
- The pause menu now opens settings, save/load, diplomacy, and statistics overlays while keeping simulation paused.
- Statistics are sampled every five seconds with bounded decimation and rendered as faction-colored canvas line charts.
- Idle-unit badges on the left edge cycle through workers, fighters, and scouts/other units; `.` cycles idle workers.
- Auto Patrol assigns selected fighters to patrol routes around clusters of working apprentices.
- Start configuration supports per-NPC difficulty, color, and initial relation, with per-player faction styles used by rendering.
- Save/load uses four localStorage slots with versioned JSON; derived grids, selection, transient effects/projectiles, and `byId` are rebuilt on load.

### Validation
- JavaScript parse check passed with Node by extracting the inline script from [index.html](../index.html).
- A mocked DOM/canvas boot smoke test passed.
- A mocked simulation smoke test started a game, generated the world, advanced 30 ticks, and rendered without exceptions.
- A mocked save/load round-trip advanced, serialized, deserialized, advanced again, and rendered without exceptions.
- Playwright/Puppeteer were not installed in this environment, so screenshot regeneration was skipped.

## July 2026 Major Expansion

Eight-phase pass adding fortifications, diplomacy, progression, magic, and a deeper tech tree. Each phase was committed and smoke-tested independently; see git log for the full breakdown.

### Economy And AI Pacing
- Stone/iron/fish were configured but never seeded, tracked, or spent by any code path — the six-resource economy is now real for every player, including the AI's villager job assignment and the HUD.
- Fish shoals now spawn on shoreline water tiles, kept clear of every town center's build-out radius (an earlier version of this boxed AI bases in and stalled their economy).
- `areHostile`/`areAllied` predicates replace ad hoc `owner !==` comparisons everywhere targeting is decided, in preparation for diplomacy.
- AI wave timing, size growth, and army caps are tuned down; difficulty presets rescaled so Heroic/Nightmare keep roughly their old bite.

### Fortifications
- Palisade -> Stone Wall -> Fortified Wall, upgradeable in place with HP fraction preserved. Drag-placement paints a Manhattan line of segments in one click-drag.
- Gates resolve passability per-unit: `tileBlockedFor` takes an optional asker-owner argument so a gate reads as open for the owner's (and allies') units and solid for everyone else, without changing behavior for any caller that omits it.
- Watch/Guard Towers fire on a per-building combat tick (buildings previously never attacked) that reuses the existing projectile pipeline.
- AI whose chase target becomes walled off retargets to the nearest reachable hostile asset instead of repathing against a sealed route forever.

### Progression
- Units gain XP from kills and level up (Heroes to 8, everyone else to 5) with a multiplicative HP/damage bonus, rank-pip rendering, and out-of-combat regen (faster near a friendly building, or from a Temple Acolyte's aura even mid-fight).
- Villagers repair damaged complete buildings through the existing build state machine, paying a fraction of build cost.
- Research was pure config before this pass — nothing tracked or enforced it. It's now a real per-player system with its own production-queue kind. **Barracks trains militia/spearman/archer/knight/mage but their unlock research previously only existed on guardhub/willhub**, buildings the AI never constructs; barracks now carries its own copy of every unlock it needs.
- A 4th Age (Archon's Legacy) and four new units (Battering Ram, Guild Ballista, Temple Acolyte, Guild Outrider) round out the tech tree, gated by new research entries.

### Diplomacy
- A per-pair relations matrix (war/peace/ally) starts everyone at war, matching prior behavior exactly until a relation changes.
- AI accepts peace when weaker or recently battered, alliance after a peace duration plus a strength edge or cumulative tribute, and may break a long peace if it grows much stronger than the player.
- AI wave targeting is relations-driven instead of hardcoded to the player, so factions can raid each other.
- Victory requires every surviving town-center faction to be allied, not just the player's survival.

### Magic
- Casters get a mana pool with passive regen; spells are cast via the same click-to-target flow as building placement (`game.spellTarget`).
- Fireball is a point-targeted, non-homing projectile — the projectile pipeline was extended to deal area damage on arrival even without a primary unit target.
- The Will Hub grants a per-player Will pool (scales with hub count) for global, map-anywhere powers (Firestorm, Guild Blessing), resolved through a new ticking `game.zones` list.

### Sentinel-Owner Safety (Neutral Creeps)
- Wildlife camps use a sentinel owner outside the real player range. `unitMaxHp`/`unitDamageValue` and every `FACTION[owner]` rendering/color lookup now guard against a missing player or faction-palette entry (`factionStyle()` falls back to a dedicated `CREEP_STYLE`).
- Two previously-unhandled unit types (any type not in the draw function's if-chain) rendered as an invisible sprite — this was latent before creeps/Hero existed since every prior type had a branch; both new type families now have their own render branches.

### Combat Feel
- Melee slashes point along the actual attack angle instead of a fixed X; a new spark burst plays on impact, and a throttled dust puff on building hits. Damage remains fully instant — these are additive visual effects, not a timing change.

### Validation
Each phase was checked with headless-browser scripts driving the live simulation (`update()`/`render()` called directly, no timers) rather than relying on visual inspection alone: multi-minute, multi-faction stability runs watching for console errors and NaN resource values; targeted checks per system (gate passability with and without a matching owner, turret fire-and-damage, wall-drag line geometry, diplomacy accept/refuse/betray thresholds, market spread, mana spend and cooldowns, hero XP-to-level-8 and revive-at-correct-level, creep camp bounty payout); and a multi-seed sweep specifically to catch AI pacing regressions from the new research gating. Regenerated `in-game`, `fortifications`, `diplomacy`, and `production-queue` screenshots with Playwright.

## July 2026 Update

This checkpoint added framework support, gameplay systems, screenshots, and documentation.

## Rendering

- The HTML HUD and the Canvas renderer are the whole renderer; there is no second graphics stack.
- Water and atmosphere effects are canvas-native. The shore shimmer walks a precomputed
  `game.shoreTiles` list rebuilt only when water or bridges change, and the sun/horizon wash is a
  cached viewport-sized layer rebuilt only on resize.
- There is no CDN dependency, so the game is fully playable offline from a static directory.

## Water And Movement

- The map is now 72 x 72 tiles.
- Generated water is tracked in a tile grid separate from static blockers.
- Visible stream width now uses the same generated width as the movement water grid.
- Resource placement rejects tiles that touch unbridged water or bridges, and generation prunes any remaining overlaps before play starts.
- Land units treat unbridged water as impassable.
- Ferry units treat water as passable and bridges/land as blocked.
- Trail-water intersections create bridge tiles, and large ponds remain ferry-relevant.
- Docks must be placed on shore and train ferries.
- Ferries can load nearby friendly land units and unload them at shoreline tiles.

## NPC Equipment

- Guild Apprentices use a white/gray hooded robe silhouette with blue accents and brown boots.
- The Blacksmith unlocks weapon and armor forging.
- Weapon upgrades increase military damage.
- Armor upgrades increase military max HP and update existing units.
- Military sprites show equipment overlays after forging.

## Production Queue

- Production queues are compact square tiles rather than full-width rows.
- The active queue tile shows percentage progress with a conic progress ring.
- Queued items show their queue position.
- Clicking a queue tile cancels that item and refunds its cost.

## Validation

Validated with a headless browser DOM load check against [index.html](../index.html), an in-page generation audit confirming zero resources touching unbridged water, a queue cancel/refund audit, and regenerated screenshots with Playwright.
