"""Facts from the enhalus_acoroides record, and display sizes.

Record quotes are from app/assets/data/species.json for this slug only.
Every other number is a display choice.
"""

from pathlib import Path

ROOT = Path(r"D:\pepot\marinesee")
SLUG = "enhalus_acoroides"
PREFIX = "EA"
SPECIES_JSON = ROOT / "app" / "assets" / "data" / "species.json"

DRAFT = ROOT / "assets" / "models-3d" / "enhalus_acoroides_next"
BLEND = DRAFT / "blender" / "enhalus_acoroides_next.blend"
GLB = DRAFT / "models" / "enhalus_acoroides_next.glb"
PREVIEW = DRAFT / "preview"
PHONE_GLB = ROOT / "app" / "assets" / "models-3d" / "enhalus_acoroides.glb"
EARLIER = ROOT / "assets" / "models-3d" / "enhalus_acoroides" / "earlier"

# Record: very long ribbon leaves, about 30–150 cm. No width is given.
LEAF_LENGTH_M = 0.80  # display choice: inside that range
LEAF_WIDTH_M = 0.018  # display choice

# Record: margins roll inward. The record gives no roll depth.
# Record: thick rhizome with long black bristles. No bristle length is given.
# Record: cord-like roots.
LEAF_THICK_M = 0.0006
STEM_RADIUS_M = 0.004
RHIZOME_RADIUS_M = 0.008
ROOT_RADIUS_M = 0.0022  # display: thicker than the fine roots on the ribbon species
BRISTLE_M = 0.028  # display choice: long enough to stand out of the sand

FPS = 30
FRAME_START = 1
FRAME_FULL = 300
FRAME_HOLD = 316
FRAME_END = 330

# Display choice: 8 shoots, more than one, kept low for the long leaves.
SHOOT_COUNT = 8


def srgb_to_linear(rgb):
    def channel(u):
        return u / 12.92 if u <= 0.04045 else ((u + 0.055) / 1.055) ** 2.4

    return tuple(channel(c) for c in rgb) + (1.0,)
