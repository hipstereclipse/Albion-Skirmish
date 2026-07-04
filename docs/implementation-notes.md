# Implementation Notes

## July 2026 Update

This checkpoint added framework support, gameplay systems, screenshots, and documentation.

## Rendering

- The existing HTML HUD and Canvas renderer remain active.
- A PixiJS overlay is loaded from CDN when available and falls back cleanly to Canvas-only rendering if it fails.
- The overlay currently augments water and atmosphere effects without taking over gameplay rendering.

## Water And Movement

- The map is now 72 x 72 tiles.
- Generated water is tracked in a tile grid separate from static blockers.
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

## Validation

Validated with a headless browser DOM load check against [index.html](../index.html) and regenerated screenshots with Playwright.
