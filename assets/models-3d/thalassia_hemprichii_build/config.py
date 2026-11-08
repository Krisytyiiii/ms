"""Display layout for the Thalassia hemprichii meadow.

Leaf length stays inside the record range. Leaf width and tannin-bar
density are display choices for the viewer. They are not spoken, and
they are not a Mati measurement.
"""

# One meadow for the phone model and the lesson. Length stays inside 10–40 cm.
# Width and tannin-bar density are display choices and are not spoken.
PLANT = {
    "shoot_count": 7,
    "leaf_counts": (3, 2, 3, 2, 2, 3, 2),
    "root_counts": (2, 3, 2, 2, 3, 2, 2),
    "leaf_width_m": 0.011,
    "leaf_thickness_m": 0.00070,
    "leaf_length_m": (0.13, 0.26),
    "vein_count": 1,
    "tannin_bars": 11,
    "sickle_rad": 1.18,
    "leaf_bones": 4,
    "vein_groove_m": 0.0,
    "leaf_crown_m": 0.00020,
    "stem_height_m": 0.026,
    "stem_radius_m": (0.0024, 0.0020),
    "scar_fracs": (0.28, 0.48),
    "scar_proud_m": 0.00030,
    "scar_half_m": 0.00035,
    "sheath_wall_m": 0.00028,
    "leaf_base_frac": 0.62,
    "rhizome_radius_m": 0.0066,
    "rhizome_oval": 0.78,
    "rhizome_span_m": 0.24,
    "rhizome_sink_m": 0.0022,
    "rhizome_scar_half_m": 0.0023,
    "root_radius_m": 0.00135,
    "sand_bottom_z": -0.016,
    "min_bone_scale": 0.02,
    "fps": 30,
    "seed": 17,
}

CONFIG = dict(PLANT)
CONFIG.update({"frame_hold": 316, "frame_end": 330})

BLEND_PATH = r"d:\pepot\marinesee\assets\models-3d\thalassia_hemprichii\blender\thalassia_hemprichii.blend"
GLB_PATH = r"d:\pepot\marinesee\app\assets\models-3d\thalassia_hemprichii.glb"

HOW_TO = """Thalassia hemprichii - how to edit

Meadow holds the solid plant. That is the model that goes to the phone.
Authoring holds the curves and shoot empties that shape it.

1. Unhide Authoring, edit a curve, run rebuild_meshes().
   (Run thalassia_hemprichii/_build_phone.py inside Blender; that rebuilds the meshes.)
2. Width, thickness, and tannin bars are the controls on TH_Controls:
   leaf_width_m, leaf_thickness_m, tannin_bars. Add th_width_m or
   th_thickness_m on one leaf curve to override only that leaf.
   Set cr_hand_edited = True on a curve or mesh to keep it as it is.
3. To change the open fan, pose the leaf bone at frame 300 and key the
   rotation. Leave the action in place.
4. Set RESET = True only when the plant should be replaced from scratch.
5. publish() writes the .glb and does not delete the curves.

Shoots stand on the TH_Shoot_NN empties: local Z is the stem, local X is the
fan side. Move an empty together with its rhizome node.
Growth is the Grow action on TH_Armature. Mesh scale stays (1, 1, 1).
After moving a curve a long way, set OVERWRITE_ANIM = True once so the
growth keys are made again for the new rest pose (this also resets fan keys).
"""


def leaf_count(i):
    counts = CONFIG["leaf_counts"]
    return counts[i % len(counts)]


# Same plant as the phone meadow. Only the clock is longer.
LESSON = dict(PLANT)
LESSON.update({"variant": "lesson", "frame_hold": 900, "frame_end": 900})


def use_lesson():
    """Point CONFIG at the lesson meadow. Call once, before build()."""
    CONFIG.update(LESSON)
