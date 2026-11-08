"""Display layout for a Halophila minor patch.

Paired small oval leaves on petioles, a wedge-shaped sheath, and a smooth
margin. There is no erect strap fan. Leaf length, leaf width, and petiole
length are display choices so the mesh has a size. They are not a Mati
measurement and not a Seagrass-Watch figure.

Cross-vein pairs are a display choice inside the Seagrass-Watch range of
fewer than eight. Not a Mati count. Eight or more would be Halophila ovalis.
"""

CONFIG = {
    "variant": "lesson",
    "shoot_count": 8,
    "leaf_counts": (2, 2, 2, 2, 2, 2, 2, 2),
    "root_counts": (2, 2, 2, 2, 2, 2, 2, 2),
    "leaf_width_m": 0.0135,
    "leaf_thickness_m": 0.00038,
    "leaf_length_m": (0.022, 0.030),
    "petiole_frac": 0.26,
    "petiole_radius_m": 0.00055,
    "pair_spread": 1.20,
    "spoon_cup_m": 0.0015,
    # Display choice inside the Seagrass-Watch fewer-than-eight range.
    "cross_vein_pairs": 6,
    "stem_height_m": 0.0048,
    "sheath_wall_m": 0.00036,
    "leaf_base_frac": 0.78,
    "rhizome_radius_m": 0.0019,
    "rhizome_oval": 0.82,
    "rhizome_span_m": 0.16,
    "rhizome_sink_m": 0.0009,
    "root_radius_m": 0.00072,
    "sand_bottom_z": -0.016,
    "min_bone_scale": 0.02,
    "fps": 30,
    "frame_hold": 900,
    "frame_end": 900,
    "seed": 21,
}

BLEND_PATH = r"d:\pepot\marinesee\assets\models-3d\halophila_minor\blender\halophila_minor.blend"
GLB_PATH = r"d:\pepot\marinesee\app\assets\models-3d\halophila_minor.glb"

HOW_TO = """Halophila minor - how to edit

Meadow holds the solid plant. That is the model that goes to the phone.
Authoring holds the curves and node empties that shape it.

1. Unhide Authoring, edit a curve, run rebuild_meshes().
   (Run halophila_minor/_build_phone.py inside Blender; that rebuilds the meshes.)
2. Width and thickness are the controls on HM_Controls: leaf_width_m and
   leaf_thickness_m. Add cr_width_m or cr_thickness_m on one leaf curve to
   override only that leaf. cross_vein_pairs is the display choice for the
   cross veins, and it stays inside the fewer-than-eight range.
   Set cr_hand_edited = True on a curve or mesh to keep it as it is.
3. Pose a leaf bone only to adjust the pair. Leave the Grow action in place.
4. Replace the plant from scratch by running the phone entry again.
5. publish() writes the .glb and does not delete the curves.

Each node is an HM_Shoot_NN empty. Local Z is the short sheath axis, local X
is the pair axis. Move an empty together with its rhizome node.
Leaves arise as one pair of ovals on petioles. There is no erect strap fan.
Growth is the Grow action on HM_Armature. Mesh scale stays (1, 1, 1).
"""


def leaf_count(i):
    counts = CONFIG["leaf_counts"]
    return counts[i % len(counts)]


# Lesson meadow. Same display sizes as the phone patch.
# How far the buried stem wanders is a display choice, not a Mati measurement.
LESSON = {
    "variant": "lesson",
    "shoot_count": 8,
    "leaf_counts": (2, 2, 2, 2, 2, 2, 2, 2),
    "root_counts": (2, 2, 2, 2, 2, 2, 2, 2),
    "leaf_width_m": 0.0135,
    "leaf_thickness_m": 0.00038,
    "leaf_length_m": (0.022, 0.030),
    "petiole_frac": 0.26,
    "petiole_radius_m": 0.00055,
    "pair_spread": 1.20,
    "spoon_cup_m": 0.0015,
    "cross_vein_pairs": 6,
    "stem_height_m": 0.0048,
    "sheath_wall_m": 0.00036,
    "leaf_base_frac": 0.78,
    "rhizome_radius_m": 0.0019,
    "rhizome_oval": 0.82,
    "rhizome_span_m": 0.16,
    "rhizome_sink_m": 0.0009,
    "root_radius_m": 0.00072,
    "sand_bottom_z": -0.016,
    "min_bone_scale": 0.02,
    "fps": 30,
    "frame_hold": 900,
    "frame_end": 900,
    "seed": 21,
}


def use_lesson():
    """Point CONFIG at the lesson meadow. Call once, before build()."""
    CONFIG.update(LESSON)
