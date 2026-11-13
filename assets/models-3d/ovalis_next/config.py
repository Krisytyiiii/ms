"""Facts from the halophila_ovalis record, and display sizes.

Record quotes are from app/assets/data/species.json for this slug only.
Every other number is a display choice.
"""

from pathlib import Path

ROOT = Path(r"D:\pepot\marinesee")
SLUG = "halophila_ovalis"
PREFIX = "HO"
SPECIES_JSON = ROOT / "app" / "assets" / "data" / "species.json"

DRAFT = ROOT / "assets" / "models-3d" / "halophila_ovalis_next"
BLEND = DRAFT / "blender" / "halophila_ovalis_next.blend"
GLB = DRAFT / "models" / "halophila_ovalis_next.glb"
PREVIEW = DRAFT / "preview"
PHONE_GLB = ROOT / "app" / "assets" / "models-3d" / "halophila_ovalis.glb"
EARLIER = ROOT / "assets" / "models-3d" / "halophila_ovalis" / "earlier"

# Record: oval leaves in pairs, larger than the small-spoon display. No millimetre size.
# The minor display is 14 mm long and 8 mm wide.
LEAF_LENGTH_M = 0.026  # display choice: longer than that minor leaf
LEAF_WIDTH_M = 0.015  # display choice: wider than that minor leaf

# Record: eight or more cross veins. No hairs on the surface.
CROSS_VEIN_PAIRS = 10  # display choice

# Record: wedge-shaped leaf sheath. No sheath size is given.
LEAF_THICK_M = 0.00025
STEM_RADIUS_M = 0.0007
RHIZOME_RADIUS_M = 0.0013
ROOT_RADIUS_M = 0.00028

FPS = 30
FRAME_START = 1
FRAME_FULL = 300
FRAME_HOLD = 316
FRAME_END = 330

# Display choice: 14 nodes, inside the plan's 12–16. Each node is one pair.
SHOOT_COUNT = 14


def srgb_to_linear(rgb):
    def channel(u):
        return u / 12.92 if u <= 0.04045 else ((u + 0.055) / 1.055) ** 2.4

    return tuple(channel(c) for c in rgb) + (1.0,)
