"""Display layout for the Halodule pinifolia meadow.

One fine pale patch: a slender rhizome, fine roots at the nodes, and
narrow leaves. Leaf width is OPEN in the record (it says fine, and gives
no number). leaf_width_m is a display choice so the rounded tip and the
split vein stay readable. It is not a Mati measurement and it is not a
published width. Leaf length uses the record's "up to about 20 cm" as
the top of the range. The short end of that range is a display choice.
"""

# Shared meadow. Phone plays frames 1-330. The lesson plays the same
# plant across 900 frames. Width is a display choice; the record has none.
_MEADOW = {
    "shoot_count": 8,
    "leaf_counts": (2, 3, 2, 2, 3, 2, 2, 2),
    "root_counts": (3, 2, 2, 3, 2, 2, 3, 2),
    "leaf_width_m": 0.00145,  # display choice; finer than a ribbon strap
    "leaf_thickness_m": 0.00022,  # display choice; keeps a thin edge
    "leaf_length_m": (0.07, 0.20),  # top is the record's "up to about 20 cm"
    "vein_count": 1,
    "vein_groove_m": 0.000035,
    "leaf_crown_m": 0.00002,
    "stem_height_m": 0.032,
    "stem_radius_m": (0.00085, 0.00072),
    # Black scars belong on the rhizome, not as rings around the stem.
    "scar_fracs": (),
    "scar_proud_m": 0.00012,
    "scar_half_m": 0.00012,
    "rhizome_scar_half_m": 0.0015,
    "rhizome_scar_proud_m": 0.00022,
    "sheath_wall_m": 0.00022,
    "leaf_base_frac": 0.82,
    "rhizome_radius_m": 0.00135,
    "rhizome_oval": 0.88,
    "rhizome_span_m": 0.22,
    "rhizome_sink_m": 0.0008,
    "root_radius_m": 0.00042,
    "sand_bottom_z": -0.032,
    "min_bone_scale": 0.02,
    "fps": 30,
    "seed": 31,
}

CONFIG = {
    "variant": "phone",
    "frame_hold": 316,
    "frame_end": 330,
}
CONFIG.update(_MEADOW)

BLEND_PATH = r"d:\pepot\marinesee\assets\models-3d\halodule_pinifolia\halodule_pinifolia.blend"
GLB_PATH = r"d:\pepot\marinesee\app\assets\models-3d\halodule_pinifolia.glb"

HOW_TO = """Halodule pinifolia - how to edit

Meadow holds the solid plant. That is the model that goes to the phone.
Authoring holds the curves and shoot empties that shape it.

1. Unhide Authoring, edit a curve, run rebuild_meshes().
   (Run _build_rotundata.py with RESET = False; that calls rebuild_meshes().)
2. Width, thickness, and vein count are the controls on that curve or on
   HP_Controls: leaf_width_m, leaf_thickness_m, vein_count. Add cr_width_m
   or cr_thickness_m on one leaf curve to override only that leaf.
   Set cr_hand_edited = True on a curve or mesh to keep it as it is.
3. To change the open fan, pose the leaf bone at frame 300 and key the
   rotation. Leave the action in place.
4. Set RESET = True only when the plant should be replaced from scratch.
5. publish() writes the .glb and does not delete the curves.

Shoots stand on the HP_Shoot_NN empties: local Z is the stem, local X is the
fan side. Move an empty together with its rhizome node.
Growth is the Grow action on HP_Armature. Mesh scale stays (1, 1, 1).
After moving a curve a long way, set OVERWRITE_ANIM = True once so the
growth keys are made again for the new rest pose (this also resets fan keys).
"""


def leaf_count(i):
    counts = CONFIG["leaf_counts"]
    return counts[i % len(counts)]


# Same plant as the phone meadow. The lesson clock runs 30 seconds.
# How far the rhizome sits behind the front cut is a display choice.
LESSON = {
    "variant": "lesson",
    "frame_hold": 900,
    "frame_end": 900,
}
LESSON.update(_MEADOW)


def cutaway(cfg=None):
    """Phone and lesson share the solid cutaway meadow."""
    cfg = CONFIG if cfg is None else cfg
    return cfg.get("variant") in ("lesson", "phone")


def use_lesson():
    """Point CONFIG at the 900-frame lesson. Call once, before build()."""
    CONFIG.clear()
    CONFIG.update(LESSON)
