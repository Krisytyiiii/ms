"""Display layout for this species' meadow.

The object prefix is read from MARINESEE_CODE, which the species entry sets
before this package is imported. Lengths that the record states stay inside
that range. Width, bristle length, and bristle count are display choices:
the record does not give those numbers.
"""

CODE = "EA"


def px(tail):
    return CODE + "_" + tail


CONFIG = {
    "shoot_count": 4,
    "leaf_counts": (3, 2, 3, 2),
    "root_counts": (2, 2, 2, 2),
    # Record: ribbon leaves about 30-150 cm. These stay inside that range.
    "leaf_length_m": (0.52, 1.46),
    # Display choice. The record gives no leaf width.
    "leaf_width_m": 0.050,
    # Display choice. Thick enough that the rolled margin has a lip.
    "leaf_thickness_m": 0.0011,
    # The record does not state veins.
    "vein_count": 0,
    "vein_groove_m": 0.0,
    "leaf_crown_m": 0.0,
    # Display choice. The record says the margins are inrolled, not how far.
    "margin_roll": 1.0,
    # Display choice. The record says long black bristles, with no length.
    "bristle_length_m": 0.046,
    # Display choice. The record gives no bristle count.
    "bristle_count": 40,
    # Display choice. The record gives no stem height.
    "stem_height_m": 0.040,
    "stem_radius_m": (0.0052, 0.0044),
    # The record does not describe a closed scar ring on this species.
    "scar_fracs": (),
    "scar_proud_m": 0.00012,
    "scar_half_m": 0.00025,
    "sheath_wall_m": 0.00055,
    "leaf_base_frac": 0.72,
    # Display choice. The record says the rhizome is thick, with no diameter.
    "rhizome_radius_m": 0.015,
    "rhizome_oval": 0.78,
    # Display choice. How far the four shoots sit apart is not a Mati measurement.
    "rhizome_span_m": 0.24,
    "rhizome_sink_m": 0.008,
    # Display choice. The record says cord-like roots, with no diameter.
    "root_radius_m": 0.0044,
    "sand_bottom_z": -0.020,
    "min_bone_scale": 0.02,
    "fps": 30,
    "frame_hold": 316,
    "frame_end": 330,
    "seed": 43,
}

BLEND_PATH = r"d:\pepot\marinesee\assets\models-3d\enhalus_acoroides\blender\enhalus_acoroides.blend"
GLB_PATH = r"d:\pepot\marinesee\app\assets\models-3d\enhalus_acoroides.glb"
MIRROR_GLB = r"d:\pepot\marinesee\assets\models-3d\enhalus_acoroides\models\enhalus_acoroides.glb"


def how_to_text():
    p = CODE
    return """How to edit this meadow

Meadow holds the solid plant. That is the model that goes to the phone.
Authoring holds the curves and shoot empties that shape it.

1. Unhide Authoring, edit a curve, run rebuild_meshes().
2. Width, thickness, margin roll, bristle length, and bristle count are the
   controls on %sControls. Add cr_width_m or cr_thickness_m on one leaf
   curve to override only that leaf. Set cr_hand_edited = True on a curve
   or mesh to keep it as it is.
3. To change the open fan, pose the leaf bone at frame 300 and key the
   rotation. Leave the action in place.
4. Set RESET = True only when the plant should be replaced from scratch.
5. publish() writes the .glb and does not delete the curves.

Shoots stand on the %sShoot_NN empties: local Z is the stem, local X is the
fan side. Move an empty together with its rhizome node.
Growth is the Grow action on %sArmature. Mesh scale stays (1, 1, 1).
After moving a curve a long way, set OVERWRITE_ANIM = True once so the
growth keys are made again for the new rest pose (this also resets fan keys).
""" % (p + "_", p + "_", p + "_")


HOW_TO = how_to_text()


def leaf_count(i):
    counts = CONFIG["leaf_counts"]
    return counts[i % len(counts)]


LESSON = {
    "variant": "lesson",
    "frame_hold": 900,
    "frame_end": 900,
}


def use_lesson():
    """Point CONFIG at the lesson meadow. Call once, before build()."""
    CONFIG.update(LESSON)
    global HOW_TO
    HOW_TO = how_to_text()
