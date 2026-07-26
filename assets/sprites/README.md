# Eldervale Sprite Atlases

The runtime art uses fixed, padded cells so canvas filtering cannot sample a
neighbouring sprite.

## Runtime atlases

- `eldervale-units-animated.png`: 4 columns x 20 rows, 256 px cells, 24 px minimum
  transparent gutter. Columns are idle, walk A, walk B, and action. The first 17
  rows cover every `CONFIG.UNITS` type; the final three are the trader,
  blacksmith, and barkeep used at world sites.
- `eldervale-resources-biomes.png`: 6 columns x 5 rows, 256 px cells, 18 px minimum
  transparent gutter. Columns are food, wood, gold, stone, iron, and fish. Rows
  are temperate, evergreen forest, marsh, dry/coastal, and frozen.
- `eldervale-buildings.png`: the existing base structure paintings. Runtime filters
  and details add temperate growth, forest moss/vines, marsh damp/rot, dry sand
  and bleaching, or frozen snow/icicles according to the construction tile.
- `atlas-manifest.json`: machine-readable row/column metadata and validated cell
  counts. Its row keys are the game's internal entity type ids, which are
  load-bearing for saves and are deliberately not renamed.

Rebuild the packed atlases with:

```powershell
python tools\build_sprite_atlases.py
```

The packer identifies artwork on each whole source sheet before cropping. It
uses a labelling-only two-pixel dilation, assigns each alpha component to the
nearest logical cell centre, reconstructs the cell with a 35% safety pad, then
applies one shared crop and scale per animation row/resource category. Results
are bottom-aligned, and the build fails if a source component exceeds its cell
pad or any visible pixel enters the protected runtime gutter. The rebuild is
byte-for-byte reproducible from the sources in `sources/`.

## Provenance

Every sprite here is a project-generated asset. Nothing was copied, traced, or
derived from a third-party game, and no external art files are redistributed.
The source grids were produced with the built-in image-generation workflow using
earlier sheets from this project as the only style reference.

## Art direction

The house style for any future sheet is: chunky caricatured proportions;
oversized, readable hands, heads, feet and equipment; warm hand-painted colour;
soft low-poly-inspired forms; and a three-quarter top-down RTS camera. Technical
requirements are a flat removable chroma background, no shadows, text or grid
lines, full silhouettes, generous per-cell padding, and no element crossing a
cell boundary.

Describe new work against this project's own vocabulary and existing sheets —
never against another game's characters or locations.

NPC groups:

1. Lodge Apprentice, Scout, Settler, and Warden.
2. Lodge Guard, Archer, Spearman, and oversized lightning Champion.
3. dark-robed Aether Adept with blue aether-lines, Temple Acolyte, mounted
   Outrider, and Lodge Ballista.
4. Forest Wolf, Wild Grubkin, Moorfang, and Battering Ram.
5. Lodge Ferry, wide-hatted Trader, burly Blacksmith, and jovial Barkeep.

Every NPC row needs four identity-consistent poses: idle, two opposite walk or
movement phases, and a role-specific action.

Resource groups:

1. Evergreen woodland: forest food, spruce, mossy ores/stones, clear lily-pad
   fish pool.
2. Marsh: thorn berries, dead twisted tree, wet dark ores, black-water fish pool.
3. Dry coastal: autumn orchard, gnarled sparse tree, sandstone nodes, turquoise
   tide pool.
4. Frozen highlands: winterberries, snow-laden spruce, snow-capped minerals,
   blue-ice fishing hole.

The temperate row is repacked from the original project resource sheet.
Generated alpha sources are retained in `sources/` so the final atlases remain
reproducible.
