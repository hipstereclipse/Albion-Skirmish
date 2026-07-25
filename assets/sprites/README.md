# Albion Sprite Atlases

The runtime art uses fixed, padded cells so canvas filtering cannot sample a
neighbouring sprite.

## Runtime atlases

- `albion-units-animated.png`: 4 columns x 20 rows, 256 px cells, 24 px minimum
  transparent gutter. Columns are idle, walk A, walk B, and action. The first 17
  rows cover every `CONFIG.UNITS` type; the final three are the trader,
  blacksmith, and barkeep used at world sites.
- `albion-resources-biomes.png`: 6 columns x 5 rows, 256 px cells, 18 px minimum
  transparent gutter. Columns are food, wood, gold, stone, iron, and fish. Rows
  are temperate, evergreen forest, Darkwood marsh, dry/coastal, and frozen.
- `albion-buildings.png`: the existing base structure paintings. Runtime filters
  and details add temperate growth, forest moss/vines, marsh damp/rot, dry sand
  and bleaching, or frozen snow/icicles according to the construction tile.
- `atlas-manifest.json`: machine-readable row/column metadata and validated cell
  counts.

Rebuild the packed atlases with:

```powershell
python tools\build_sprite_atlases.py
```

The packer identifies artwork on each whole source sheet before cropping. It
uses a labelling-only two-pixel dilation, assigns each alpha component to the
nearest logical cell centre, reconstructs the cell with a 35% safety pad, then
applies one shared crop and scale per animation row/resource category. Results
are bottom-aligned, and the build fails if a source component exceeds its cell
pad or any visible pixel enters the protected runtime gutter.

## Generation prompt set

The source grids were generated with the built-in image-generation workflow and
the previous project sheets as style references. All prompts specified the
original 2005 storybook direction: chunky caricatured proportions, oversized
readable hands/heads/feet and equipment, warm hand-painted colour, soft
low-poly-inspired forms, and a three-quarter top-down RTS camera. They also
required a flat removable chroma background, no shadows/text/grid lines, full
silhouettes, generous per-cell padding, and no element crossing a cell boundary.

NPC groups:

1. Guild Apprentice, Scout, Settler, and Hero of Oakvale.
2. Guild Guard, Archer, Spearman, and oversized lightning Champion.
3. dark-robed Will Adept with blue Will-lines, Temple Acolyte, mounted Outrider,
   and Guild Ballista.
4. Forest Wolf, Wild Hobbe, Balverine, and Battering Ram.
5. Guild Ferry, wide-hatted Trader, burly Blacksmith, and jovial Barkeep.

Every NPC row requested four identity-consistent poses: idle, two opposite walk
or movement phases, and a role-specific action. Appearance and mannerism cues
come from the supplied TLC character reference, including the mute blue-cloaked
Hero, stern Albion guards, staff-casting Will-user, wide-brim trader silhouette,
practical forge worker, and broad tavern keeper.

Resource groups:

1. Evergreen/Greatwood-Witchwood: forest food, spruce, mossy ores/stones, clear
   lily-pad fish pool.
2. Darkwood/Lychfield marsh: thorn berries, dead twisted tree, wet dark ores,
   black-water fish pool.
3. Oakvale/coastal dry: autumn orchard, gnarled sparse tree, sandstone nodes,
   turquoise tide pool.
4. Hook Coast/Northern Wastes: winterberries, snow-laden spruce, snow-capped
   minerals, blue-ice fishing hole.

The temperate row is repacked from the original project resource sheet. Generated
alpha sources are retained in `sources/` so the final atlases remain reproducible.
