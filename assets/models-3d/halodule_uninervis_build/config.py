"""Display layout for the Halodule uninervis meadow.

Leaf width and leaf length below are display choices so the trident tip
and the single vein stay readable on a phone. They are not field
measurements and they are not spoken. The tip is a trident. One central
vein. The rhizome is pale ivory, with clean black leaf scars.
"""

# Shared plant. The phone plays frames 1-330. The lesson plays 900 frames.
_MEADOW = {
    "shoot_count": 9,
    "leaf_counts": (3, 2, 4, 3, 2, 3, 2, 4, 3),
    "root_counts": (3, 2, 3, 2, 2, 3, 1, 2),
    "leaf_width_m": 0.0028,
    "leaf_thickness_m": 0.00070,
    "leaf_length_m": (0.11, 0.16),
    "vein_count": 1,
    "tip_style": "trident",
    "vein_groove_m": 0.00016,
    "leaf_crown_m": 0.00008,
    "trident_mid_m": 0.012,
    "trident_side_m": 0.007,
    "trident_splay_m": 0.0042,
    "stem_height_m": 0.022,
    "stem_radius_m": (0.00135, 0.00115),
    "scar_fracs": (0.18, 0.34),
    "scar_proud_m": 0.00016,
    "scar_half_m": 0.00016,
    "rhizome_scar_half_m": 0.0021,
    "rhizome_scar_proud_m": 0.00042,
    "sheath_wall_m": 0.00022,
    "leaf_base_frac": 0.70,
    "rhizome_radius_m": 0.00205,
    "rhizome_oval": 0.86,
    "rhizome_span_m": 0.24,
    "rhizome_sink_m": 0.0055,
    "root_radius_m": 0.00042,
    "sand_bottom_z": -0.032,
    "min_bone_scale": 0.02,
    "fps": 30,
    "seed": 17,
}

CONFIG = {
    "variant": "phone",
    "frame_hold": 316,
    "frame_end": 330,
}
CONFIG.update(_MEADOW)

BLEND_PATH = r"d:\pepot\marinesee\assets\models-3d\halodule_uninervis\halodule_uninervis.blend"
GLB_PATH = r"d:\pepot\marinesee\app\assets\models-3d\halodule_uninervis.glb"
ASSETS_GLB_PATH = r"d:\pepot\marinesee\assets\models-3d\halodule_uninervis\halodule_uninervis.glb"

HOW_TO = """Halodule uninervis - how to edit

Meadow holds the solid plant. That is the model that goes to the phone.
Authoring holds the curves and shoot empties that shape it.

1. Unhide Authoring, edit a curve, run rebuild_meshes().
   (Run halodule_uninervis/_build_phone.py inside Blender; that rebuilds the meshes.)
2. Width, thickness, and vein count are the controls on that curve or on
   HU_Controls: leaf_width_m, leaf_thickness_m, vein_count. Add cr_width_m
   or cr_thickness_m on one leaf curve to override only that leaf.
   Set cr_hand_edited = True on a curve or mesh to keep it as it is.
3. To change the open fan, pose the leaf bone at frame 300 and key the
   rotation. Leave the action in place.
4. Set RESET = True only when the plant should be replaced from scratch.
5. publish() writes the .glb and does not delete the curves.

Shoots stand on the HU_Shoot_NN empties: local Z is the stem, local X is the
fan side. Move an empty together with its rhizome node.
Growth is the Grow action on HU_Armature. Mesh scale stays (1, 1, 1).
After moving a curve a long way, set OVERWRITE_ANIM = True once so the
growth keys are made again for the new rest pose (this also resets fan keys).
"""


def leaf_count(i):
    counts = CONFIG["leaf_counts"]
    return counts[i % len(counts)]


def use_lesson():
    """Same meadow as the phone. Only the frame range and the lesson camera change."""
    CONFIG.clear()
    CONFIG.update(_MEADOW)
    CONFIG["variant"] = "lesson"
    CONFIG["frame_hold"] = 900
    CONFIG["frame_end"] = 900
