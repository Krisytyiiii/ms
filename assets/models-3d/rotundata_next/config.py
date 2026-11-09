"""Display layout for one sandy plot.

Facts, from the species record only: flat straps about 2-4 mm wide, a rounded
smooth tip, a closed sheath-scar ring, and a smooth rhizome. Every other
number in CONFIG is a display choice for the phone viewer.
"""

CONFIG = {
    # Display choice. One snaking rhizome, inside 12-16 shoots.
    "shoot_count": 14,
    # Display choice. 2-5 leaves on each shoot.
    "leaf_counts": (5, 3, 4, 2, 4, 3, 5, 2, 3, 4, 2, 5, 3, 4),
    # Real leaves are 2-4 mm wide. 7 mm is a display choice so the strap stays readable.
    "leaf_width_m": 0.007,
    # Display choice. About 0.35 mm, so the side view is a thin edge.
    "leaf_thickness_m": 0.00035,
    # Display choice. Blade length stays inside 7-15 cm. Younger leaves use the short end.
    "leaf_length_m": (0.07, 0.15),
    # Display choice. Faint long veins live in the leaf image. Not a measured count.
    "vein_count": 11,
    # Display choice. How wide the fan opens, in radians.
    "leaf_spread": 0.46,
    # Display choice. Fraction of the blade used to widen out of the sheath.
    "leaf_shoulder": 0.12,
    # Display choice. Short stem the sheath and the scar rings sit on.
    "stem_height_m": 0.028,
    # Display choice. Where the bare stem mesh stops, inside the sheath.
    "stem_top_frac": 0.66,
    # Display choice. Horizontal and vertical stem radius.
    "stem_radius_m": (0.0017, 0.00145),
    # Display choice. Closed rings on the bare stem, below the sheath.
    "scar_fracs": (0.16, 0.30, 0.44, 0.56),
    # Display choice. A fraction of a millimetre proud of the stem.
    "scar_proud_m": 0.00025,
    # Display choice. Half the height of a thin scar band.
    "scar_half_m": 0.00020,
    # Display choice. Sheath wall thickness.
    "sheath_wall_m": 0.00030,
    # Display choice. Sheath stations along the stem.
    "sheath_fracs": (0.58, 0.74, 0.90, 1.02),
    # Display choice. Sheath flare (wide, thick), in metres.
    "sheath_outer_m": (
        (0.0021, 0.0017),
        (0.0028, 0.0020),
        (0.0038, 0.0023),
        (0.0046, 0.0027),
    ),
    # Display choice. Sheath opening, in radians, tighter near the stem.
    "sheath_slit": (0.26, 0.34, 0.46, 0.60),
    # Display choice. Leaf bases start inside the sheath.
    "leaf_base_frac": 0.70,
    # Display choice. Smooth rhizome radius.
    "rhizome_radius_m": 0.0022,
    # Display choice. Slightly wider than tall, still a smooth tube.
    "rhizome_oval": 0.86,
    # Display choice. One rhizome crosses the plot. Two branches leave it,
    # so the shoots sit across the sand instead of along one line.
    "main_xy": (
        (-0.16, 0.00),
        (-0.08, 0.02),
        (0.00, -0.01),
        (0.08, 0.02),
        (0.15, -0.01),
        (0.21, 0.04),
    ),
    # Display choice. (node on the main rhizome, branch shoot positions).
    "branch_xy": (
        (2, ((-0.05, 0.07), (0.03, 0.10), (0.11, 0.08), (0.02, 0.13))),
        (3, ((0.03, -0.06), (-0.05, -0.09), (-0.13, -0.06), (0.10, -0.09))),
    ),
    # Display choice. How far the rhizome center sits under the smooth mound.
    "rhizome_sink_m": 0.0023,
    # Display choice. Short tip past the last shoot.
    "rhizome_tip_m": 0.012,
    # Display choice. Fine roots. Thinner than the rhizome.
    "root_radius_m": 0.0007,
    # Display choice. Several roots leave each node and spread across the sand.
    "root_count": 4,
    # Display choice. How far a root runs out from the shoot before it turns down.
    "root_spread_m": (0.028, 0.048),
    # Display choice. How far the tip then goes down, kept inside the mound.
    "root_length_m": 0.010,
    # Display choice. Bottom of the solid mound.
    "sand_bottom_z": -0.012,
    # Display choice. Extra sand past the rhizome, so the plot has a rim.
    "sand_margin_m": (0.12, 0.11),
    # Display choice. Groove depth and half-width where the rhizome sits.
    "groove_depth_m": 0.0036,
    "groove_width_m": 0.012,
    # Display choice. Height of the low dome at its middle.
    "mound_height_m": 0.007,
    # Locked growth floor. Bone scale Y never goes below this.
    "min_bone_scale": 0.02,
    # Locked clock.
    "fps": 30,
    "frame_hold": 316,
    "frame_end": 330,
    # Display choice. Kept so a rebuild from RESET is the same plot.
    "seed": 11,
}

ROOT = r"d:\pepot\marinesee\assets\models-3d"
BLEND_PATH = ROOT + r"\cymodocea_rotundata_next\blender\cymodocea_rotundata_next.blend"
GLB_PATH = ROOT + r"\cymodocea_rotundata_next\models\cymodocea_rotundata_next.glb"
PREVIEW_DIR = ROOT + r"\cymodocea_rotundata_next\preview"

HOW_TO = """Cymodocea rotundata - how to edit

Unhide Authoring and run rebuild_meshes().
Change width on the controls. CR_Controls holds leaf_width_m, vein_count, and shoot_count. They are not driven every frame.
Pose a leaf bone at frame 300.
Set RESET only for a full replace.
publish() keeps the curves.
"""


def leaf_count(i, cfg=None):
    cfg = CONFIG if cfg is None else cfg
    counts = cfg["leaf_counts"]
    return int(counts[i % len(counts)])
