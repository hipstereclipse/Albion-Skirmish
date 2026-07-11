# Albion Skirmish

Albion Skirmish is a browser-playable RTS prototype inspired by Fable: The Lost Chapters flavor and Age of Empires-style controls. Gather resources, build a fortified Guild settlement, research your way through four Ages, train a roster of fighters and a leveling Hero, cast Will magic, manage war/peace/alliance with up to three rival factions, and destroy or outlast every hostile stronghold.

![Start menu](docs/screenshots/start-menu.png)

![In-game view](docs/screenshots/in-game.png)

![Fortifications: walls, gate, and towers](docs/screenshots/fortifications.png)

![Diplomacy panel](docs/screenshots/diplomacy.png)

![Compact production queue](docs/screenshots/production-queue.png)

## Running

Open [index.html](index.html) in a modern browser. The game is self-contained and does not require a build step.

## Current Features

### Core
- HTML HUD with resource counters (food/wood/gold/stone/iron/fish), production actions, selection details, minimap, and touch controls.
- Optional PixiJS overlay loaded from CDN for richer water/atmosphere effects while the Canvas renderer remains the fallback.
- Larger 72 x 72 tile battlefield with generated streams, ponds, bridges, fish shoals, and water-aware pathfinding.
- Land units cannot cross deep water except at bridges; larger bodies of water require ferries from an Albion Dock.
- Production buildings show compact square queue tiles with progress and click-to-cancel refunds.
- Animated vector sprites with walk bob, leg stride, directional attack swings, impact sparks, building dust puffs, ferry wake, and cargo pips.

### Fortifications
- Palisade, Stone, and Fortified walls — drag-build a whole line in one click-drag, upgrade a tier in place without losing HP%.
- Guild Gates let friendly units (and allies) pass through while blocking hostiles; lockable, with an animated door swing.
- Watch Towers and Guard Towers fire arrows at hostiles automatically.

### Progression
- Units gain XP from kills and level up (Heroes to 8, everyone else to 5), with rank-pip indicators, out-of-combat HP regen, and Temple Acolytes who heal allies even mid-fight.
- A real research tree gates units, forge tiers, and Age advancement — blacksmith forging upgrades weapons/armor with visible equipment overlays.
- Four Ages, from Apprentice Years to Archon's Legacy, each unlocking new units: Battering Rams and Ballistae (bonus damage vs. buildings), Guild Outriders (mounted archers).
- A trainable Guild Hero levels independently, auto-learns Will magic (Fireball, Heal Life, Slow Time) at levels 2/3/5, and revives at the Guild Hall for gold instead of being retrained.
- Villagers can repair damaged buildings, not just construct new ones.

### Diplomacy & economy
- War / peace / alliance relations with every AI faction, managed from a Diplomacy panel (top-bar button or `P`) — offer peace, propose alliance, declare war, or send tribute.
- AI factions can make peace, ally, or betray a peace based on relative strength — and will raid each other, not just the player.
- Victory requires every surviving faction to be allied, not just the player's own survival.
- A Bowerstone Market buys and sells every resource at a fixed spread.

### Magic & threats
- Mages and Heroes cast targeted spells (Fireball AoE, Heal Life, Slow Time) with mana pools and cooldowns, via the same click-to-target flow as building placement.
- A Will Hub lets the player cast global powers (Firestorm, Guild Blessing) anywhere on the map once built, fed by a Will pool.
- Neutral wildlife camps (wolves, wild hobbes, balverines) guard the map and pay a resource bounty when cleared.
- Enemy AI is deliberately less relentless than earlier builds — slower first wave, smaller escalation, and it now needs research to unlock its own units and Ages just like the player.

## Screenshots

Screenshots are generated from the current local build and stored in [docs/screenshots](docs/screenshots):

- [Start menu](docs/screenshots/start-menu.png)
- [In-game view](docs/screenshots/in-game.png)
- [Fortifications: walls, gate, and towers](docs/screenshots/fortifications.png)
- [Diplomacy panel](docs/screenshots/diplomacy.png)
- [Compact production queue](docs/screenshots/production-queue.png)

## Notes

This is still a single-file prototype. The next sensible step is to split renderer, simulation, UI, and content config into modules before adding heavier art assets or more framework-specific rendering.
