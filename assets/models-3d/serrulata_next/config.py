"""Facts from the cymodocea_serrulata record, and display sizes.

Record quotes are from app/assets/data/species.json for this slug only.
Every other number is a display choice.
"""

from pathlib import Path

ROOT = Path(r"D:\pepot\marinesee")
SLUG = "cymodocea_serrulata"
PREFIX = "CS"
SPECIES_JSON = ROOT / "app" / "assets" / "data" / "species.json"

DRAFT = ROOT / "assets" / "models-3d" / "cymodocea_serrulata_next"
BLEND = DRAFT / "blender" / "cymodocea_serrulata_next.blend"
GLB = DRAFT / "models" / "cymodocea_serrulata_next.glb"
PREVIEW = DRAFT / "preview"
PHONE_GLB = ROOT / "app" / "assets" / "models-3d" / "cymodocea_serrulata.glb"
EARLIER = ROOT / "assets" / "models-3d" / "cymodocea_serrulata" / "earlier"

# Record: strap-like leaves about 5–9 mm wide.
LEAF_WIDTH_M = 0.009  # display choice: top of that range

# Record: serrated tip. No tooth count is stated, so none is chosen here.
# Record: the leaf sheath is broadly triangular.
# Record: the leaf scars do not form a continuous ring around the stem.

# Display choices. The record gives no leaf length, stem height, or rhizome width.
LEAF_THICK_M = 0.00035
SHEATH_MOUTH_M = 0.016
STEM_RADIUS_M = 0.0021
RHIZOME_RADIUS_M = 0.0024
ROOT_RADIUS_M = 0.00042

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
