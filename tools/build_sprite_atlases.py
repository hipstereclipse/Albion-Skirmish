"""Pack generated Albion art into bleed-safe runtime atlases.

The image generator produces presentation grids whose silhouettes can overhang
the nominal row/column divisions.  This packer isolates connected artwork on
the whole source sheet before normalizing cells, uses one shared crop/scale per
animation row, and pastes the result inside a fixed transparent gutter.  Both
source-grid contamination and runtime sampling bleed are therefore excluded.
"""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
SPRITES = ROOT / "assets" / "sprites"
SOURCES = SPRITES / "sources"

UNIT_CELL = 256
UNIT_GUTTER = 24
RESOURCE_CELL = 256
RESOURCE_GUTTER = 18
NORMALIZED_CELL = 512
SOURCE_ALPHA_THRESHOLD = 4
SOURCE_COMPONENT_DILATION = 2
SOURCE_CELL_PADDING = 0.35

UNIT_ROWS = [
    ("villager", "npc-civilians-alpha.png", 0),
    ("scout", "npc-civilians-alpha.png", 1),
    ("settler", "npc-civilians-alpha.png", 2),
    ("hero", "npc-civilians-alpha.png", 3),
    ("militia", "npc-military-alpha.png", 0),
    ("archer", "npc-military-alpha.png", 1),
    ("spearman", "npc-military-alpha.png", 2),
    ("knight", "npc-military-alpha.png", 3),
    ("mage", "npc-special-alpha.png", 0),
    ("acolyte", "npc-special-alpha.png", 1),
    ("cavarcher", "npc-special-alpha.png", 2),
    ("ballista", "npc-special-alpha.png", 3),
    ("wolf", "npc-creeps-alpha.png", 0),
    ("hobbeWild", "npc-creeps-alpha.png", 1),
    ("balverine", "npc-creeps-alpha.png", 2),
    ("ram", "npc-creeps-alpha.png", 3),
    ("ship", "npc-world-alpha.png", 0),
    ("trader", "npc-world-alpha.png", 1),
    ("blacksmithNpc", "npc-world-alpha.png", 2),
    ("barkeep", "npc-world-alpha.png", 3),
]

RESOURCE_SHEETS = [
    ("temperate", SPRITES / "albion-resources-v2.png"),
    ("forest", SOURCES / "resources-forest-alpha.png"),
    ("marsh", SOURCES / "resources-marsh-alpha.png"),
    ("dry", SOURCES / "resources-dry-alpha.png"),
    ("snow", SOURCES / "resources-snow-alpha.png"),
]
RESOURCE_TYPES = ["food", "wood", "gold", "stone", "iron", "fish"]


def alpha_weighted_centroid(
    alpha: Image.Image,
    component_mask: Image.Image,
    bbox: tuple[int, int, int, int],
) -> tuple[float, float, int]:
    """Return a component's alpha-weighted centre and visible-pixel count."""
    width = bbox[2] - bbox[0]
    alpha_bytes = alpha.crop(bbox).tobytes()
    mask_bytes = component_mask.crop(bbox).tobytes()
    total_weight = weighted_x = weighted_y = visible_pixels = 0
    for index, (value, member) in enumerate(zip(alpha_bytes, mask_bytes)):
        if not member or value < SOURCE_ALPHA_THRESHOLD:
            continue
        x = bbox[0] + index % width
        y = bbox[1] + index // width
        total_weight += value
        weighted_x += x * value
        weighted_y += y * value
        visible_pixels += 1
    if not total_weight:
        raise ValueError("Source component contains no visible pixels")
    return weighted_x / total_weight, weighted_y / total_weight, visible_pixels


def isolate_grid_cells(image: Image.Image, cols: int, rows: int, label: str) -> list[Image.Image]:
    """Assign whole-sheet connected artwork to its nearest logical grid cell.

    Generated silhouettes sometimes cross a nominal grid boundary.  Cropping the
    rectangles first would turn that overhang into a detached fragment in the
    neighbouring sprite.  A two-pixel, labelling-only dilation joins tiny gaps in
    one authored object; the original (undilated) RGBA pixels are what we retain.
    """
    source = image.convert("RGBA")
    alpha = source.getchannel("A")
    clean_alpha = alpha.point(
        lambda value: 0 if value < SOURCE_ALPHA_THRESHOLD else value
    )
    source.putalpha(clean_alpha)
    visible = clean_alpha.point(lambda value: 255 if value else 0)
    filter_size = SOURCE_COMPONENT_DILATION * 2 + 1
    remaining = visible.filter(ImageFilter.MaxFilter(filter_size))

    # Flood-fill each dilated component.  The fill mask is only used to identify
    # membership; component pieces retain the source's untouched antialiasing.
    component_lut = [0] * 256
    component_lut[128] = 255
    cell_width = source.width / cols
    cell_height = source.height / rows
    assigned: list[list[tuple[tuple[int, int, int, int], Image.Image, int]]] = [
        [] for _ in range(cols * rows)
    ]
    while True:
        remaining_bbox = remaining.getbbox()
        if not remaining_bbox:
            break
        first_row = remaining.crop((
            remaining_bbox[0],
            remaining_bbox[1],
            remaining_bbox[2],
            remaining_bbox[1] + 1,
        )).tobytes()
        seed_x = remaining_bbox[0] + next(
            index for index, value in enumerate(first_row) if value
        )
        ImageDraw.floodfill(remaining, (seed_x, remaining_bbox[1]), 128, thresh=0)
        component_mask = remaining.point(component_lut)
        remaining.paste(0, mask=component_mask)

        # Ignore dilation-only pixels when measuring and cropping the component.
        visible_component = Image.new("L", source.size, 0)
        visible_component.paste(visible, mask=component_mask)
        component_bbox = visible_component.getbbox()
        if not component_bbox:
            continue
        center_x, center_y, visible_pixels = alpha_weighted_centroid(
            clean_alpha, component_mask, component_bbox
        )
        cell_index = min(
            range(cols * rows),
            key=lambda index: (
                (center_x - (index % cols + 0.5) * cell_width) ** 2 / cell_width ** 2
                + (center_y - (index // cols + 0.5) * cell_height) ** 2 / cell_height ** 2
            ),
        )
        piece = Image.new(
            "RGBA",
            (component_bbox[2] - component_bbox[0], component_bbox[3] - component_bbox[1]),
            (0, 0, 0, 0),
        )
        piece.paste(source.crop(component_bbox), (0, 0), component_mask.crop(component_bbox))
        assigned[cell_index].append((component_bbox, piece, visible_pixels))

    normalized: list[Image.Image] = []
    for row in range(rows):
        for col in range(cols):
            pieces = assigned[row * cols + col]
            if not pieces:
                raise ValueError(f"{label} source cell ({col}, {row}) has no assigned artwork")
            x0 = round((col - SOURCE_CELL_PADDING) * cell_width)
            x1 = round((col + 1 + SOURCE_CELL_PADDING) * cell_width)
            y0 = round((row - SOURCE_CELL_PADDING) * cell_height)
            y1 = round((row + 1 + SOURCE_CELL_PADDING) * cell_height)
            cell = Image.new("RGBA", (x1 - x0, y1 - y0), (0, 0, 0, 0))
            for component_bbox, piece, _ in pieces:
                if (
                    component_bbox[0] < x0
                    or component_bbox[1] < y0
                    or component_bbox[2] > x1
                    or component_bbox[3] > y1
                ):
                    raise ValueError(
                        f"{label} component assigned to ({col}, {row}) exceeds "
                        f"the {SOURCE_CELL_PADDING:.0%} safety pad: {component_bbox}"
                    )
                cell.alpha_composite(piece, (component_bbox[0] - x0, component_bbox[1] - y0))
            normalized.append(
                cell.resize((NORMALIZED_CELL, NORMALIZED_CELL), Image.Resampling.LANCZOS)
            )
    return normalized


def union_bbox(cells: list[Image.Image]) -> tuple[int, int, int, int]:
    boxes = [cell.getchannel("A").getbbox() for cell in cells]
    boxes = [box for box in boxes if box]
    if not boxes:
        raise ValueError("Generated row contains no visible pixels")
    return (
        min(box[0] for box in boxes),
        min(box[1] for box in boxes),
        max(box[2] for box in boxes),
        max(box[3] for box in boxes),
    )


def place_shared_crop(
    atlas: Image.Image,
    cells: list[Image.Image],
    bbox: tuple[int, int, int, int],
    output_cells: list[tuple[int, int]],
    cell_size: int,
    gutter: int,
) -> None:
    crop_width = bbox[2] - bbox[0]
    crop_height = bbox[3] - bbox[1]
    usable = cell_size - gutter * 2
    scale = min(usable / crop_width, usable / crop_height)
    target = (
        max(1, round(crop_width * scale)),
        max(1, round(crop_height * scale)),
    )
    for source, (col, row) in zip(cells, output_cells):
        frame = source.crop(bbox).resize(target, Image.Resampling.LANCZOS)
        x = col * cell_size + (cell_size - target[0]) // 2
        # A stable bottom baseline keeps feet, wheels and roots from swimming.
        y = row * cell_size + cell_size - gutter - target[1]
        atlas.alpha_composite(frame, (x, y))


def validate_gutters(
    atlas: Image.Image,
    cols: int,
    rows: int,
    cell_size: int,
    gutter: int,
    label: str,
) -> list[dict[str, int]]:
    report: list[dict[str, int]] = []
    for row in range(rows):
        for col in range(cols):
            cell = atlas.crop((
                col * cell_size,
                row * cell_size,
                (col + 1) * cell_size,
                (row + 1) * cell_size,
            ))
            bbox = cell.getchannel("A").getbbox()
            if not bbox:
                raise ValueError(f"{label} cell ({col}, {row}) is empty")
            left, top, right, bottom = bbox
            margins = {
                "left": left,
                "top": top,
                "right": cell_size - right,
                "bottom": cell_size - bottom,
            }
            if min(margins.values()) < gutter - 2:
                raise ValueError(f"{label} cell ({col}, {row}) violates gutter: {margins}")
            report.append({"col": col, "row": row, **margins})
    return report


def build_units() -> tuple[Path, list[dict[str, int]]]:
    loaded: dict[str, list[Image.Image]] = {}
    atlas = Image.new("RGBA", (UNIT_CELL * 4, UNIT_CELL * len(UNIT_ROWS)), (0, 0, 0, 0))
    for atlas_row, (_, filename, source_row) in enumerate(UNIT_ROWS):
        if filename not in loaded:
            with Image.open(SOURCES / filename) as image:
                loaded[filename] = isolate_grid_cells(image, 4, 4, filename)
        source_cells = loaded[filename]
        cells = [source_cells[source_row * 4 + col] for col in range(4)]
        place_shared_crop(
            atlas,
            cells,
            union_bbox(cells),
            [(col, atlas_row) for col in range(4)],
            UNIT_CELL,
            UNIT_GUTTER,
        )
    path = SPRITES / "albion-units-animated.png"
    atlas.save(path, optimize=True)
    report = validate_gutters(atlas, 4, len(UNIT_ROWS), UNIT_CELL, UNIT_GUTTER, "unit")
    return path, report


def resource_source_cell(cells: list[Image.Image], resource_index: int) -> Image.Image:
    col = resource_index % 3
    row = resource_index // 3
    return cells[row * 3 + col]


def build_resources() -> tuple[Path, list[dict[str, int]]]:
    sheets: list[tuple[str, list[Image.Image]]] = []
    for name, path in RESOURCE_SHEETS:
        with Image.open(path) as image:
            sheets.append((name, isolate_grid_cells(image, 3, 2, path.name)))
    atlas = Image.new(
        "RGBA",
        (RESOURCE_CELL * len(RESOURCE_TYPES), RESOURCE_CELL * len(sheets)),
        (0, 0, 0, 0),
    )
    # Keep each resource category at one scale across all biomes.
    for resource_index, _ in enumerate(RESOURCE_TYPES):
        cells = [
            resource_source_cell(source_cells, resource_index)
            for _, source_cells in sheets
        ]
        place_shared_crop(
            atlas,
            cells,
            union_bbox(cells),
            [(resource_index, biome_row) for biome_row in range(len(sheets))],
            RESOURCE_CELL,
            RESOURCE_GUTTER,
        )
    path = SPRITES / "albion-resources-biomes.png"
    atlas.save(path, optimize=True)
    report = validate_gutters(
        atlas,
        len(RESOURCE_TYPES),
        len(sheets),
        RESOURCE_CELL,
        RESOURCE_GUTTER,
        "resource",
    )
    return path, report


def main() -> None:
    units_path, unit_report = build_units()
    resources_path, resource_report = build_resources()
    manifest = {
        "units": {
            "file": units_path.name,
            "cell": UNIT_CELL,
            "gutter": UNIT_GUTTER,
            "columns": ["idle", "walkA", "walkB", "action"],
            "rows": {name: row for row, (name, _, _) in enumerate(UNIT_ROWS)},
            "validatedCells": len(unit_report),
        },
        "resources": {
            "file": resources_path.name,
            "cell": RESOURCE_CELL,
            "gutter": RESOURCE_GUTTER,
            "columns": {name: col for col, name in enumerate(RESOURCE_TYPES)},
            "rows": {name: row for row, (name, _) in enumerate(RESOURCE_SHEETS)},
            "validatedCells": len(resource_report),
        },
    }
    manifest_path = SPRITES / "atlas-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {units_path.relative_to(ROOT)} ({len(unit_report)} bleed-safe cells)")
    print(f"Wrote {resources_path.relative_to(ROOT)} ({len(resource_report)} bleed-safe cells)")
    print(f"Wrote {manifest_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
