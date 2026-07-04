# Albion Skirmish

Albion Skirmish is a browser-playable RTS prototype inspired by Fable: The Lost Chapters flavor and Age of Empires-style controls. Gather resources, build a Guild settlement, train fighters, forge equipment, cross consequential water, and destroy enemy strongholds.

![Start menu](docs/screenshots/start-menu.png)

![In-game view](docs/screenshots/in-game.png)

![Compact production queue](docs/screenshots/production-queue.png)

## Running

Open [index.html](index.html) in a modern browser. The game is self-contained and does not require a build step.

## Current Features

- HTML HUD with resource counters, production actions, selection details, minimap, and touch controls.
- Optional PixiJS overlay loaded from CDN for richer water/atmosphere effects while the Canvas renderer remains the fallback.
- Larger 72 x 72 tile battlefield with generated streams, ponds, bridges, and water-aware pathfinding.
- Land units cannot cross deep water except at bridges; larger bodies of water require ferries from an Albion Dock.
- Resource placement rejects water and shoreline-overlap tiles, so nodes no longer spawn inside visible water.
- Guild Apprentices wear white/gray hooded robes with blue accents and brown leather boots.
- Production buildings show compact square queue tiles with progress and click-to-cancel refunds.
- Blacksmith forging upgrades weapons and armor for military units, with visible equipment overlays and stat changes.
- Animated vector sprites with walk bob, leg stride, attack swing, ferry wake, and cargo pips.

## Screenshots

Screenshots are generated from the current local build and stored in [docs/screenshots](docs/screenshots):

- [Start menu](docs/screenshots/start-menu.png)
- [In-game view](docs/screenshots/in-game.png)
- [Compact production queue](docs/screenshots/production-queue.png)

## Notes

This is still a single-file prototype. The next sensible step is to split renderer, simulation, UI, and content config into modules before adding heavier art assets or more framework-specific rendering.
