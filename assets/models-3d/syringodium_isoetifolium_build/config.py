"""One meadow for the phone model and the lesson. Length stays inside 7–30 cm.

leaf_diameter_m and sheath_shape are display choices. They are not spoken as facts.
"""

CONFIG = {
    "presentation": "phone",
    "shoot_count": 7,
    "leaf_length_m": (0.075, 0.125),
    "leaf_diameter_m": 0.0058,
    "sheath_shape": "round_collar",
    "stem_height_m": 0.024,
    "stem_radius_m": 0.00215,
    "sheath_flare_m": 0.00115,
    "leaf_base_frac": 0.62,
    "rhizome_radius_m": 0.00245,
    "rhizome_oval": 1.0,
    "rhizome_sink_m": 0.010,
    "root_radius_m": 0.00085,
    "sand_bottom_z": -0.016,
    "min_bone_scale": 0.02,
    "fps": 30,
    "frame_hold": 240,
    "frame_end": 330,
    "seed": 8,
}

BLEND_PATH = r"d:\pepot\marinesee\assets\models-3d\syringodium_isoetifolium\blender\syringodium_isoetifolium.blend"
GLB_PATH = r"d:\pepot\marinesee\app\assets\models-3d\syringodium_isoetifolium.glb"
SPECIES_GLB_PATH = r"d:\pepot\marinesee\assets\models-3d\syringodium_isoetifolium\models\syringodium_isoetifolium.glb"

HOW_TO = """Syringodium isoetifolium - how to edit

Meadow holds the solid plant. That is the model that goes to the phone.
Authoring holds the curves and shoot empties that shape it.

Leaves are round in every direction. Do not flatten a leaf into a strap.
Growth is the Grow action on SI_Armature. Mesh scale stays (1, 1, 1).
"""


def use_lesson():
    """Same plant. The lesson only changes the clock and the camera."""
    CONFIG["presentation"] = "lesson"
    CONFIG["frame_hold"] = 900
    CONFIG["frame_end"] = 900
