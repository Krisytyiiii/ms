"""Display layout for the Halophila ovalis meadow.

Blade length and blade width are display choices so the spoon reads on a
phone. They are not a spoken millimetre and not a Mati measurement.
The blade is larger than a small oval. That smaller blade is Halophila minor.

cross_vein_pairs is 8, the bottom of the Seagrass-Watch "eight or more"
range for Halophila ovalis. Do not use fewer than 8: that is Halophila minor.
The leaf surface has no hairs. Leaves arise in pairs from the rhizome.
There is no erect strap fan.

Frames 1-40 may be bare sand before the bud. The record calls this species
an early coloniser. The beats after that stay on the same clock.
"""

import copy

CONFIG = {
    "shoot_count": 8,
    "leaf_counts": (2, 2, 2, 2, 2, 2, 2, 2),
    "root_counts": (2, 1, 2, 1, 2, 1, 2, 1),
    # Display blade width. Larger than a small oval. Not a spoken millimetre.
    "leaf_width_m": 0.026,
    "leaf_thickness_m": 0.00070,
    # Petiole plus blade. Display choice, not a spoken millimetre.
    "leaf_length_m": (0.058, 0.074),
    "petiole_frac": 0.38,
    "petiole_radius_m": 0.00072,
    # Bottom of the Seagrass-Watch "eight or more" range. Fewer than 8 is H. minor.
    "cross_vein_pairs": 8,
    "vein_count": 0,
    "vein_pattern": "cross",
    "hairs": 0,
    "vein_groove_m": 0.00015,
    "leaf_crown_m": 0.0,
    # Short node only. The pair rises from the rhizome; there is no erect fan.
    "stem_height_m": 0.0035,
    "stem_radius_m": (0.0015, 0.0012),
    "scar_fracs": (),
    "scar_proud_m": 0.0,
    "scar_half_m": 0.0,
    "sheath_wall_m": 0.0,
    "leaf_base_frac": 1.0,
    "rhizome_radius_m": 0.00155,
    "rhizome_oval": 0.72,
    "rhizome_span_m": 0.16,
    "rhizome_sink_m": 0.0012,
    "root_radius_m": 0.00042,
    "sand_bottom_z": -0.032,
    "min_bone_scale": 0.02,
    "fps": 30,
    "frame_hold": 316,
    "frame_end": 330,
    "seed": 11,
}

BLEND_PATH = r"d:\pepot\marinesee\assets\models-3d\halophila_ovalis\halophila_ovalis.blend"
GLB_PATH = r"d:\pepot\marinesee\app\assets\models-3d\halophila_ovalis.glb"
SPECIES_GLB_PATH = r"d:\pepot\marinesee\assets\models-3d\halophila_ovalis\halophila_ovalis.glb"

HOW_TO = """Halophila ovalis - how to edit

Meadow holds the solid plant. That is the model that goes to the phone.
Authoring holds the curves and node empties that shape it.

1. Unhide Authoring, edit a curve, run rebuild_meshes().
   (Run halophila_ovalis/_build_phone.py inside Blender.)
2. Blade width and thickness are the controls on HO_Controls:
   leaf_width_m, leaf_thickness_m. cross_vein_pairs stays 8.
   That is the bottom of the Seagrass-Watch "eight or more" range.
   Fewer than 8 is Halophila minor. The surface has no hairs.
3. Each node carries one pair of oval leaves. Do not add a strap fan.
4. publish() writes the .glb and does not delete the curves.

Nodes sit on the HO_Shoot_NN empties. Local Z is the short node, local X
is the pair axis. Move an empty together with its rhizome node.
Growth is the Grow action on HO_Armature. Mesh scale stays (1, 1, 1).
Frames 1-40 are bare sand before the bud.
"""


def leaf_count(i):
    """Halophila ovalis leaves arise in pairs. A fan count is not this species."""
    return 2


def cross_vein_us(pairs=None):
    """Blade positions, 0 at the petiole join and 1 at the tip, for each pair."""
    n = int(CONFIG["cross_vein_pairs"] if pairs is None else pairs)
    if n < 2:
        return [0.50]
    # Eight pairs sit on the oval, inset from the join and the rounded tip.
    return [0.18 + (0.82 - 0.18) * i / (n - 1) for i in range(n)]


# Lesson meadow. Same spoon, same eight cross-vein pairs, same pair rule.
# Blade size repeats the phone display choice. It is not a spoken millimetre.
# cross_vein_pairs is 8, the bottom of the Seagrass-Watch "eight or more"
# range. Fewer than 8 is Halophila minor.
# Same meadow as the phone. Only the clock and the lesson camera differ.
LESSON = {
    "variant": "lesson",
    "shoot_count": 8,
    "leaf_counts": (2, 2, 2, 2, 2, 2, 2, 2),
    "root_counts": (2, 1, 2, 1, 2, 1, 2, 1),
    "leaf_width_m": 0.026,
    "leaf_thickness_m": 0.00070,
    "leaf_length_m": (0.058, 0.074),
    "petiole_frac": 0.38,
    "petiole_radius_m": 0.00072,
    "cross_vein_pairs": 8,
    "vein_count": 0,
    "vein_pattern": "cross",
    "hairs": 0,
    "vein_groove_m": 0.00015,
    "leaf_crown_m": 0.0,
    "stem_height_m": 0.0035,
    "stem_radius_m": (0.0015, 0.0012),
    "scar_fracs": (),
    "scar_proud_m": 0.0,
    "scar_half_m": 0.0,
    "sheath_wall_m": 0.0,
    "leaf_base_frac": 1.0,
    "rhizome_radius_m": 0.00155,
    "rhizome_oval": 0.72,
    "rhizome_span_m": 0.16,
    "rhizome_sink_m": 0.0012,
    "root_radius_m": 0.00042,
    "sand_bottom_z": -0.032,
    "min_bone_scale": 0.02,
    "fps": 30,
    "frame_hold": 900,
    "frame_end": 900,
    "seed": 11,
}


def use_lesson():
    """Point CONFIG at the lesson meadow. Call once, before build()."""
    CONFIG.update(LESSON)


PREFIX = "HO"

_STOCK = copy.deepcopy(CONFIG)


def oname(suffix=""):
    """HO_Rhizome, HO_Shoot_, and the rest. Reads PREFIX at call time."""
    return PREFIX + "_" + suffix
