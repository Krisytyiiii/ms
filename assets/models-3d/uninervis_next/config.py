"""Facts from the halodule_uninervis record, and display sizes.

Record quotes are from app/assets/data/species.json for this slug only.
Every other number is a display choice.
"""

from pathlib import Path

ROOT = Path(r"D:\pepot\marinesee")
SLUG = "halodule_uninervis"
PREFIX = "HU"
SPECIES_JSON = ROOT / "app" / "assets" / "data" / "species.json"

DRAFT = ROOT / "assets" / "models-3d" / "halodule_uninervis_next"
BLEND = DRAFT / "blender" / "halodule_uninervis_next.blend"
GLB = DRAFT / "models" / "halodule_uninervis_next.glb"
PREVIEW = DRAFT / "preview"
PHONE_GLB = ROOT / "app" / "assets" / "models-3d" / "halodule_uninervis.glb"
EARLIER = ROOT / "assets" / "models-3d" / "halodule_uninervis" / "earlier"

# Record: usually larger than Halodule pinifolia. No width or length is given.
# The pinifolia display is 1.6 mm wide and 18 cm on the longest leaf.
LEAF_WIDTH_M = 0.0032  # display choice: visibly wider than that pinifolia leaf
LEAF_LENGTH_M = 0.220  # display choice: visibly longer than that pinifolia leaf

# Record: one central vein, and a trident tip.
# Record: the rhizome is usually pale ivory, with clean black leaf scars.

# Display choices. The record gives no rhizome width or stem height.
LEAF_THICK_M = 0.00028
STEM_RADIUS_M = 0.0015
RHIZOME_RADIUS_M = 0.0021
ROOT_RADIUS_M = 0.00038

FPS = 30
FRAME_START = 1
FRAME_FULL = 300
FRAME_HOLD = 316
FRAME_END = 330

# Display choice: 14 shoots, inside the plan's 12–16.
SHOOT_COUNT = 14


def srgb_to_linear(rgb):
    def channel(u):
        return u / 12.92 if u <= 0.04045 else ((u + 0.055) / 1.055) ** 2.4

    return tuple(channel(c) for c in rgb) + (1.0,)
