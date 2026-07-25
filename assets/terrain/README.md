# Hex Terrain Textures

This directory contains high-resolution terrain sources for the procedural map renderer. Every PNG is 1254 x 1254 pixels and is intended to be sampled at varying offsets and rotations, then clipped by the runtime into overlapping hexagonal cells.

## Materials

The eight seamless material sources live in `materials/`:

| File | Intended terrain |
| --- | --- |
| `hex-meadow.png` | Open grass and fertile clearings |
| `hex-forest.png` | Dense woodland floor |
| `hex-mud.png` | Marsh, bog, and slow wet ground |
| `hex-road.png` | Packed dirt roads and trails |
| `hex-rock.png` | Stony ground, ridges, and difficult slopes |
| `hex-sand.png` | Beaches and dry sandy ground |
| `hex-snow.png` | Snowfields and frozen high ground |
| `hex-water.png` | Lakes, streams, and deep water |

The sources are direction-neutral and designed for seamless repetition. Deterministic crop offsets and 60-degree rotations may be used to reduce visible repetition without changing a tile's material identity.

## Transitions

The three pairwise boundary sources live in `transitions/`:

| File | Left side | Right side |
| --- | --- | --- |
| `meadow-mud.png` | Meadow | Mud |
| `meadow-rock.png` | Meadow | Rock |
| `sand-water.png` | Sand | Water |

Each transition has a vertical boundary in its source orientation. Rotate it around the sample center to align that boundary with any of the six hex edges; rotate it 180 degrees to reverse the material order. The edges are intended to repeat along a boundary, while runtime hex clipping and neighboring-cell overlap hide the unused corners.

## Runtime Model

The hexes are a rendering tessellation, not a replacement for the simulation grid. The renderer clips these material and transition sources into visual hexagons, but buildings, placement, hit testing, water masks, and pathfinding continue to use the existing square tile grid for compatibility.

## Provenance

These terrain assets were generated with the built-in image-generation workflow, using the existing Albion meadow artwork as the visual style reference. They are project-local generated assets rather than third-party texture files.
