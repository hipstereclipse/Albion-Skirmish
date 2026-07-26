"""Re-export the terrain sources at the size the renderer actually samples.

The authored hex materials and transitions ship at 1254x1254 but are consumed at
a fraction of that: `drawHexTerrainMaterials` bakes every material into a 384x384
offscreen canvas before measuring luminance and calling `createPattern`, and each
transition is cropped to a narrow centre strip that is redrawn into a fixed
192x256 canvas.  Shipping the full-size plates therefore costs tens of megabytes
of payload to produce pixels the runtime immediately throws away.

This tool rewrites those sources in place at their sampling size.  Paths and
aspect ratios are unchanged, so no markup, manifest or offset contract moves.
Truecolor is preferred; a palette pass is used only where truecolor would blow
the payload budget, and every such file is held to a PSNR floor measured against
the truecolor downscale the runtime would have built itself.

Every output is encoded and validated before anything is written.  Re-quantizing
an already-reduced source compounds its error, so a rewriter that edits in place
must never leave a half-converted tree behind for the next run to chew on again.
"""

from __future__ import annotations

import io
import math
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
TERRAIN = ROOT / "assets" / "terrain"
MATERIALS = TERRAIN / "materials"
TRANSITIONS = TERRAIN / "transitions"
ART = ROOT / "assets" / "art"

# Matches MATERIAL_PATTERN_SIZE in `drawHexTerrainMaterials`.
MATERIAL_SIZE = 384
# The transition strip crop keeps 24% of the source width at full height and
# lands in a 192x256 canvas; 512 keeps that centre band comfortably oversampled.
TRANSITION_SIZE = 512

MATERIAL_BUDGET = 150 * 1024
TRANSITION_BUDGET = 250 * 1024

# Tried widest-first; the largest palette that fits the budget wins.
PALETTE_LADDER = (256, 224, 192, 160, 128)
# Palette output is only accepted well above the ~36 dB threshold at which
# dithered texture noise becomes distinguishable from its truecolor source.
MIN_PALETTE_PSNR = 34.0
# The runtime lifts muddy materials by up to brightness(1.4); banding has to stay
# below the floor after that amplification, not just at authored exposure.
RUNTIME_BRIGHTNESS_LIFT = 1.4


def downscale(path: Path, size: int) -> Image.Image:
    """Return the truecolor LANCZOS reduction the runtime would build itself."""
    with Image.open(path) as source:
        return source.convert("RGB").resize((size, size), Image.Resampling.LANCZOS)


def encode(image: Image.Image) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


def psnr(reference: Image.Image, candidate: Image.Image) -> float:
    """Peak signal-to-noise ratio in dB between two same-size RGB images."""
    reference_bytes = reference.convert("RGB").tobytes()
    candidate_bytes = candidate.convert("RGB").tobytes()
    squared_error = sum(
        (a - b) * (a - b) for a, b in zip(reference_bytes, candidate_bytes)
    )
    if not squared_error:
        return math.inf
    return 20 * math.log10(255.0 / math.sqrt(squared_error / len(reference_bytes)))


def brighten(image: Image.Image, factor: float) -> Image.Image:
    """Apply the runtime's brightness lift, the worst case for palette banding."""
    lut = [min(255, round(value * factor)) for value in range(256)] * 3
    return image.convert("RGB").point(lut)


def to_palette(image: Image.Image, colors: int) -> Image.Image:
    return image.quantize(
        colors=colors,
        method=Image.Quantize.MEDIANCUT,
        dither=Image.Dither.FLOYDSTEINBERG,
    )


def palette_quality(reference: Image.Image, palette: Image.Image) -> float:
    """Score a reduction at authored exposure and under the runtime's lift."""
    return min(
        psnr(reference, palette),
        psnr(
            brighten(reference, RUNTIME_BRIGHTNESS_LIFT),
            brighten(palette, RUNTIME_BRIGHTNESS_LIFT),
        ),
    )


def plan_export(path: Path, size: int, budget: int) -> dict[str, object]:
    """Encode one source at `size` within `budget` bytes, without writing it.

    Truecolor wins whenever it already fits.  Otherwise the widest palette that
    fits is taken, and only if it clears the PSNR floor under the runtime's own
    brightness lift -- a silent quality cliff is worse than an oversized file.

    A source already at the target size is left untouched.  This tool overwrites
    its own inputs, so without that guard a second run would re-quantize an
    existing reduction and lose a little more of the image every time.
    """
    before = path.stat().st_size
    with Image.open(path) as source:
        before_size = source.size
    if before_size == (size, size):
        return {
            "path": path,
            "before_size": before_size,
            "after_size": (size, size),
            "before_bytes": before,
            "payload": None,
            "mode": "unchanged",
            "psnr": math.inf,
        }
    reference = downscale(path, size)

    payload = encode(reference)
    if len(payload) <= budget:
        return {
            "path": path,
            "before_size": before_size,
            "after_size": (size, size),
            "before_bytes": before,
            "payload": payload,
            "mode": "truecolor",
            "psnr": math.inf,
        }

    for colors in PALETTE_LADDER:
        palette = to_palette(reference, colors)
        payload = encode(palette)
        if len(payload) > budget:
            continue
        quality = palette_quality(reference, palette)
        if quality < MIN_PALETTE_PSNR:
            raise ValueError(
                f"{path.name}: {colors}-colour reduction scores {quality:.1f} dB, "
                f"below the {MIN_PALETTE_PSNR:.0f} dB floor"
            )
        return {
            "path": path,
            "before_size": before_size,
            "after_size": (size, size),
            "before_bytes": before,
            "payload": payload,
            "mode": f"palette{colors}",
            "psnr": quality,
        }

    raise ValueError(
        f"{path.name}: no encoding in the palette ladder fits the "
        f"{budget / 1024:.0f} KB budget at {size}x{size}"
    )


def targets() -> list[tuple[Path, int, int]]:
    plan: list[tuple[Path, int, int]] = [
        (path, MATERIAL_SIZE, MATERIAL_BUDGET)
        for path in sorted(MATERIALS.glob("hex-*.png"))
    ]
    plan.append((ART / "eldervale-meadow-v2.png", MATERIAL_SIZE, MATERIAL_BUDGET))
    plan += [
        (path, TRANSITION_SIZE, TRANSITION_BUDGET)
        for path in sorted(TRANSITIONS.glob("*.png"))
    ]
    missing = [path for path, _, _ in plan if not path.is_file()]
    if missing:
        raise ValueError(f"Missing terrain sources: {[str(p) for p in missing]}")
    return plan


def main() -> None:
    # Encode and validate every source first, then commit the batch, so a
    # rejected file can never leave the tree half-rewritten.
    reports = [plan_export(path, size, budget) for path, size, budget in targets()]
    written = [report for report in reports if report["payload"] is not None]
    for report in written:
        report["path"].write_bytes(report["payload"])

    before_total = sum(report["before_bytes"] for report in reports)
    after_total = sum(
        report["before_bytes"] if report["payload"] is None else len(report["payload"])
        for report in reports
    )
    for report in reports:
        path: Path = report["path"]
        before_w, before_h = report["before_size"]
        after_w, after_h = report["after_size"]
        quality = report["psnr"]
        detail = "" if quality == math.inf else f"  {quality:.1f} dB"
        after_bytes = (
            report["before_bytes"] if report["payload"] is None else len(report["payload"])
        )
        print(
            f"{path.relative_to(ROOT).as_posix():44s} "
            f"{before_w}x{before_h} -> {after_w}x{after_h}  "
            f"{report['before_bytes'] / 1024:8.1f} KB -> {after_bytes / 1024:7.1f} KB  "
            f"{report['mode']}{detail}"
        )
    if not written:
        print(f"All {len(reports)} terrain sources are already at their target size.")
        return
    print(
        f"Rewrote {len(written)} of {len(reports)} terrain sources: "
        f"{before_total / 1048576:.2f} MB -> {after_total / 1048576:.2f} MB "
        f"({100 - after_total / before_total * 100:.1f}% smaller)"
    )


if __name__ == "__main__":
    main()
