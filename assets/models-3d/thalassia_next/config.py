"""Facts from the thalassia_hemprichii record, and display sizes.

Record quotes are from app/assets/data/species.json for this slug only.
Every other number is a display choice.
"""

from pathlib import Path

ROOT = Path(r"D:\pepot\marinesee")
SLUG = "thalassia_hemprichii"
PREFIX = "TH"
SPECIES_JSON = ROOT / "app" / "assets" / "data" / "species.json"

DRAFT = ROOT / "assets" / "models-3d" / "thalassia_hemprichii_next"
BLEND = DRAFT / "blender" / "thalassia_hemprichii_next.blend"
GLB = DRAFT / "models" / "thalassia_hemprichii_next.glb"
PREVIEW = DRAFT / "preview"
PHONE_GLB = ROOT / "app" / "assets" / "models-3d" / "thalassia_hemprichii.glb"
EARLIER = ROOT / "assets" / "models-3d" / "thalassia_hemprichii" / "earlier"

# Record: curved ribbon leaves, about 10–40 cm. No width is given.
LEAF_WIDTH_M = 0.010  # display choice
LEAF_LENGTH_M = 0.280  # display choice: inside the 10–40 cm record

# Record: short black bars of tannin cells. The record gives no bar count.
TANNIN_BARS = 9  # display choice

# Record: the rhizome is thick, with scars between the shoots.
# Display choices. The record gives no rhizome width.
LEAF_THICK_M = 0.0004
STEM_RADIUS_M = 0.0024
RHIZOME_RADIUS_M = 0.0048
ROOT_RADIUS_M = 0.0005

FPS = 30
FRAME_START = 1
FRAME_FULL = 300
FRAME_HOLD = 316
FRAME_END = 330

SHOOT_COUNT = 14  # display choice, inside the plan's 12–16


def srgb_to_linear(rgb):
    def channel(u):
        return u / 12.92 if u <= 0.04045 else ((u + 0.055) / 1.055) ** 2.4

    return tuple(channel(c) for c in rgb) + (1.0,)
