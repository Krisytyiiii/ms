"""Facts from the halodule_pinifolia record, and display sizes.

Record quotes are from app/assets/data/species.json for this slug only.
Every other number is a display choice.
"""

from pathlib import Path

ROOT = Path(r"D:\pepot\marinesee")
SLUG = "halodule_pinifolia"
PREFIX = "HP"
SPECIES_JSON = ROOT / "app" / "assets" / "data" / "species.json"

DRAFT = ROOT / "assets" / "models-3d" / "halodule_pinifolia_next"
BLEND = DRAFT / "blender" / "halodule_pinifolia_next.blend"
GLB = DRAFT / "models" / "halodule_pinifolia_next.glb"
PREVIEW = DRAFT / "preview"
PHONE_GLB = ROOT / "app" / "assets" / "models-3d" / "halodule_pinifolia.glb"
EARLIER = ROOT / "assets" / "models-3d" / "halodule_pinifolia" / "earlier"

# Record: fine leaves, up to about 20 cm. No width is given.
LEAF_WIDTH_M = 0.0016  # display choice: fine enough to read as a needle
LEAF_LENGTH_M = 0.180  # display choice: inside the "up to about 20 cm" record

# Record: one dark central vein that splits in two at a rounded tip.
# Record: the rhizome is usually pale, with clean black leaf scars.

# Display choices. The record gives no rhizome width or stem height.
LEAF_THICK_M = 0.00018
STEM_RADIUS_M = 0.00105
RHIZOME_RADIUS_M = 0.00155
ROOT_RADIUS_M = 0.00032

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
