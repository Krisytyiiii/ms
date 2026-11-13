"""Facts from the syringodium_isoetifolium record, and display sizes.

Record quotes are from app/assets/data/species.json for this slug only.
Every other number is a display choice.
"""

from pathlib import Path

ROOT = Path(r"D:\pepot\marinesee")
SLUG = "syringodium_isoetifolium"
PREFIX = "SI"
SPECIES_JSON = ROOT / "app" / "assets" / "data" / "species.json"

DRAFT = ROOT / "assets" / "models-3d" / "syringodium_isoetifolium_next"
BLEND = DRAFT / "blender" / "syringodium_isoetifolium_next.blend"
GLB = DRAFT / "models" / "syringodium_isoetifolium_next.glb"
PREVIEW = DRAFT / "preview"
PHONE_GLB = ROOT / "app" / "assets" / "models-3d" / "syringodium_isoetifolium.glb"
EARLIER = ROOT / "assets" / "models-3d" / "syringodium_isoetifolium" / "earlier"

# Record: leaves are cylindrical, like spaghetti, and the tip tapers to a point.
# Record: leaves are about 7–30 cm long. No diameter is given.
LEAF_WIDTH_M = 0.0022  # display choice: diameter, so the leaf reads as a noodle
LEAF_LENGTH_M = 0.240  # display choice: inside the 7–30 cm record

# The record does not describe scars, bristles, or a vein count. None are built.

# Display choices. The record gives no rhizome width or stem height.
LEAF_THICK_M = 0.0022
STEM_RADIUS_M = 0.0014
RHIZOME_RADIUS_M = 0.0018
ROOT_RADIUS_M = 0.00036

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
