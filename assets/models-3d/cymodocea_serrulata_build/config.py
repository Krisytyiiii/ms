"""Display layout for the Cymodocea serrulata meadow.

Strap width is 9 mm, the top of the Seagrass-Watch range already in the
species record (about 5–9 mm). stem_height_m and leaf_length_m are display
choices so the mesh has a length. They are not a Mati measurement and not
a Seagrass-Watch figure for this species. Vein count, tooth count, and
tooth size are not recorded here.
"""

CONFIG = {
    "shoot_count": 13,
    "leaf_counts": (4, 3, 4, 3, 3, 4, 3, 3, 4, 3, 3, 4, 3),
    "leaf_width_m": 0.009,
    "leaf_thickness_m": 0.00032,
    "leaf_length_m": (0.105, 0.175),
    "vein_count": 0,
    "vein_pattern": "none",
    "tip_style": "serrated",
    "sheath_style": "broad_triangle",
    "scar_style": "not_continuous",
    "vein_groove_m": 0.0,
    "leaf_crown_m": 0.00008,
    "stem_height_m": 0.042,
    "stem_radius_m": (0.00155, 0.00135),
    "scar_fracs": (0.10, 0.20, 0.30),
    "scar_proud_m": 0.00078,
    "scar_half_m": 0.00062,
    "sheath_wall_m": 0.00038,
    "leaf_base_frac": 0.58,
    "rhizome_radius_m": 0.00175,
    "rhizome_oval": 0.76,
    "rhizome_span_m": 0.32,
    "rhizome_sink_m": 0.0032,
    "root_radius_m": 0.00055,
    "sheath_rgb": (0.80, 0.76, 0.50),
    "scar_rgb": (0.34, 0.22, 0.12),
    "rhizome_rgb": (0.90, 0.82, 0.66),
    "root_rgb": (0.93, 0.88, 0.74),
    "sand_bottom_z": -0.032,
    "min_bone_scale": 0.02,
    "fps": 30,
    "frame_hold": 316,
    "frame_end": 330,
    "seed": 11,
}

BLEND_PATH = r"d:\pepot\marinesee\assets\models-3d\cymodocea_serrulata\cymodocea_serrulata.blend"
GLB_PATH = r"d:\pepot\marinesee\app\assets\models-3d\cymodocea_serrulata.glb"

HOW_TO = """Cymodocea serrulata - how to edit

Meadow holds the solid plant. That is the model that goes to the phone.
Authoring holds the curves and shoot empties that shape it.

1. Unhide Authoring, edit a curve, run rebuild_meshes().
   (Run cymodocea_serrulata/_build_phone.py inside Blender; that rebuilds the meshes.)
2. Width, thickness, and vein count are the controls on that curve or on
   CS_Controls: leaf_width_m, leaf_thickness_m, vein_count. Add cr_width_m
   or cr_thickness_m on one leaf curve to override only that leaf.
   Set cr_hand_edited = True on a curve or mesh to keep it as it is.
3. To change the open fan, pose the leaf bone at frame 300 and key the
   rotation. Leave the action in place.
4. Set RESET = True only when the plant should be replaced from scratch.
5. publish() writes the .glb and does not delete the curves.

Shoots stand on the CS_Shoot_NN empties: local Z is the stem, local X is the
fan side. Move an empty together with its rhizome node.
Growth is the Grow action on CS_Armature. Mesh scale stays (1, 1, 1).
After moving a curve a long way, set OVERWRITE_ANIM = True once so the
growth keys are made again for the new rest pose (this also resets fan keys).
"""


def leaf_count(i):
    counts = CONFIG["leaf_counts"]
    return counts[i % len(counts)]


def use_lesson():
    """Same meadow as the phone model. Only the lesson clock changes."""
    CONFIG["variant"] = "lesson"
    CONFIG["fps"] = 30
    CONFIG["frame_hold"] = 900
    CONFIG["frame_end"] = 900


import copy

# This package builds Cymodocea serrulata only.
PREFIX = "CS"

# Phone CONFIG as imported. Species runs mutate CONFIG in place, then restore this.
_STOCK = copy.deepcopy(CONFIG)


def oname(suffix=""):
    """CS_Rhizome, CS_Shoot_, and the rest. Reads PREFIX at call time."""
    return PREFIX + "_" + suffix


def apply_config(updates):
    """Reset to the serrulata phone stock, then overlay. The dict object stays put."""
    CONFIG.clear()
    CONFIG.update(copy.deepcopy(_STOCK))
    if updates:
        CONFIG.update(updates)


def restore_config():
    """Put the module defaults back. Paths in this file are not species-specific."""
    global PREFIX
    PREFIX = "CS"
    CONFIG.clear()
    CONFIG.update(copy.deepcopy(_STOCK))
