"""First-time layout: HM_Controls, Authoring curves and shoot empties, the empty armature."""

import math
import random

import bpy
from mathutils import Matrix, Vector

from .config import CONFIG, HOW_TO
from .sand import sand_height
from .util import collection, layer_collection, link, set_bezier, tag

UP = Vector((0.0, 0.0, 1.0))


# A short meander, not one straight row. Spacing is a display choice.
LESSON_XY = (
    (-0.062, -0.034),
    (-0.022, -0.018),
    (0.016, -0.038),
    (0.052, -0.014),
    (0.074, 0.018),
    (0.036, 0.042),
    (-0.008, 0.022),
    (-0.046, 0.046),
)


def node_xy(count, span, rng):
    from .config import CONFIG

    if CONFIG.get("variant") == "lesson":
        return list(LESSON_XY)
    if CONFIG.get("variant") == "realistic":
        # Three tufts, not one row. The rhizome still connects them.
        spots = ((-0.10, 0.012), (-0.01, -0.028), (0.09, 0.018))
        groups = (count // 3, count // 3, count - 2 * (count // 3))
        out = []
        n = 0
        for (cx, cy), group in zip(spots, groups):
            for k in range(group):
                ang = k * 2.2 + n * 0.4
                out.append((cx + 0.016 * math.cos(ang), cy + 0.013 * math.sin(ang)))
                n += 1
        return out
    del count, span, rng
    return [
        (-0.06, -0.036),
        (-0.01, -0.028),
        (0.05, -0.038),
        (-0.07, -0.008),
        (0.01, 0.00),
        (0.07, -0.012),
        (-0.04, 0.02),
        (0.03, 0.03),
        (-0.07, 0.045),
        (0.00, 0.05),
        (0.06, 0.055),
        (-0.03, 0.07),
        (0.04, 0.075),
        (-0.06, 0.03),
        (0.07, 0.03),
        (0.00, 0.025),
    ]


def new_curve(name, points, col):
    data = bpy.data.curves.new(name, "CURVE")
    data.dimensions = "3D"
    spline = data.splines.new("BEZIER")
    set_bezier(spline, points)
    obj = bpy.data.objects.new(name, data)
    link(obj, col)
    obj.hide_render = True
    return tag(obj)


def shoot_frame(i, count):
    from .config import CONFIG

    if CONFIG.get("variant") == "lesson":
        # Pairs yaw in the sand so the patch is not a comb. The sheath stays short.
        yaw = 0.42 * math.sin(i * 1.7 + 0.3)
        lean_x = 0.03 * math.sin(i * 0.9)
        lean_y = 0.015
    else:
        yaw = 0.48 * math.sin(i * 1.7 + 0.3) + 0.18 * math.cos(i * 0.8) + 0.02 * (i - 0.5 * (count - 1))
        lean_x = 0.06 * math.sin(i * 0.95)
        lean_y = 0.04 + 0.03 * math.cos(i * 1.1)
    right = Vector((math.cos(yaw), math.sin(yaw), 0.0))
    forward = Vector((-math.sin(yaw), math.cos(yaw), 0.0))
    stem = (UP + right * lean_x + forward * lean_y).normalized()
    right = (right - stem * right.dot(stem)).normalized()
    forward = stem.cross(right).normalized()
    return stem, right, forward


def leaf_points(node, stem, right, forward, tilt, length, fwd, bow, cfg):
    """A pair lying off the rhizome. The blade is an oval, not an upright strap."""
    del bow
    height = cfg["stem_height_m"]
    sign = 1.0 if tilt >= 0.0 else -1.0
    base = node + stem * (height * cfg["leaf_base_frac"]) + right * (0.0014 * sign)
    # tilt is measured from the short sheath, out toward the sand.
    direction = (stem * math.cos(tilt) + right * math.sin(tilt) + forward * (0.08 * sign)).normalized()
    frac = float(cfg.get("petiole_frac", 0.26))
    petiole_len = length * frac
    blade = max(0.006, length - petiole_len)
    lift = UP * 0.0032 + forward * fwd
    neck = base + direction * petiole_len + lift * 0.35
    mid = neck + direction * (blade * 0.48) + lift
    tip = neck + direction * blade + lift * 0.45
    return [base, neck, mid, tip]


def plan_leaves(i, count, rng, cfg):
    """One pair of opposite petioles at this node."""
    del count
    lo, hi = cfg["leaf_length_m"]
    spread = float(cfg.get("pair_spread", 0.72))
    leaves = []
    for j, sign in enumerate((-1.0, 1.0)):
        tilt = sign * spread + rng.uniform(-0.03, 0.03)
        rank = 0.35 + 0.60 * ((i * 2 + j) % 5) / 4.0
        length = lo + (hi - lo) * rank * rng.uniform(0.96, 1.02)
        leaves.append({
            "tilt": tilt,
            "length": max(lo, min(hi, length)),
            "young": j == 1 and i % 4 == 1,
            "fwd": 0.0008 * sign,
            "bow": 0.0,
            "twist": 0.05 * sign,
        })
    return leaves


def _root_points(node, i, r, bottom, rng):
    """Roots grow down. On the lesson cut, one root stays in the wall; the rest stay buried."""
    from .config import CONFIG

    if CONFIG.get("variant") == "lesson":
        from .sand import front_cut_y

        max_len = max(0.012, node.z - (bottom + 0.004))
        on_cut = node.y < -0.010
        if on_cut:
            # Down the exposed face, just proud of the wall, so the root can be seen.
            fan = -1.0 if r % 2 == 0 else 1.0
            length = min(max_len, 0.030 + 0.004 * (r % 2))
            cut = front_cut_y(node.x, None)
            # Most of the root runs down the open face, not inside the sand.
            return [
                node + Vector((0.0004 * fan, -0.0005, -0.0004)),
                Vector((node.x + 0.004 * fan, cut - 0.0018, node.z - 0.005)),
                Vector((node.x + 0.008 * fan, cut - 0.0024, node.z - length)),
            ]
        ang = i * 0.85 + r * 2.15
        length = min(max_len, 0.014 + 0.005 * (r % 2))
        dx = math.cos(ang) * (0.005 + 0.004 * r)
        dy = 0.003 + abs(math.sin(ang)) * 0.007
        return [
            node + Vector((0.0003, 0.0002, -0.0005)),
            node + Vector((dx * 0.45, dy * 0.4, -length * 0.5)),
            node + Vector((dx, dy, -length)),
        ]
    short = CONFIG.get("variant") == "realistic"
    max_len = max(0.010, node.z - (bottom + 0.0035))
    length = min(max_len, (0.011 if short else 0.020) + 0.003 * ((i + r) % 3))
    down = Vector((0.0, 0.0, -1.0))
    if r < 2:
        side_sign = -1.0 if r == 0 else 1.0
        dx1 = side_sign * (0.0032 + 0.0015 * rng.random())
        dx2 = side_sign * (0.0065 + 0.0030 * rng.random()) + 0.0015 * math.sin(i + r)
        # Keep Y slightly in front of the cutaway wall (node.y + 0.0005) so the root never hides inside the sand
        p0 = node + Vector((side_sign * 0.0008, -0.0009, -0.0006))
        p1 = node + Vector((dx1, -0.0010, -length * 0.42))
        p2 = node + Vector((dx2, -0.0007, -length))
        return [p0, p1, p2]
    ang = 0.6 + 0.5 * math.sin(i * 1.3)
    out = Vector((math.cos(ang) * 0.005, abs(math.sin(ang)) * 0.009 + 0.005, 0.0))
    return [
        node + Vector((0.0, 0.001, -0.0008)),
        node + out * 0.55 + down * (length * 0.45),
        node + out + down * length,
    ]


def create_plant(cfg=CONFIG):
    rng = random.Random(cfg["seed"])
    count = cfg["shoot_count"]
    scene_col = bpy.context.scene.collection

    controls = bpy.data.objects.new("HM_Controls", None)
    scene_col.objects.link(controls)
    controls.empty_display_size = 0.015
    controls["leaf_width_m"] = cfg["leaf_width_m"]
    controls["leaf_thickness_m"] = cfg["leaf_thickness_m"]
    controls["cross_vein_pairs"] = cfg["cross_vein_pairs"]
    controls["shoot_count"] = count
    tag(controls)

    authoring = collection("Authoring")
    collection("Meadow")

    xy = node_xy(count, cfg["rhizome_span_m"], rng)
    count = len(xy)
    sink = cfg["rhizome_sink_m"]
    nodes = [Vector((x, y, sand_height(x, y, xy) - sink)) for x, y in xy]
    points = []
    for k, node in enumerate(nodes):
        points.append(node)
        if k < count - 1:
            m = (node + nodes[k + 1]) * 0.5
            m.z = sand_height(m.x, m.y, xy) - sink
            points.append(m)
    lead = (nodes[-1] - nodes[-2]).normalized()
    tip = nodes[-1] + lead * 0.012
    tip.z = sand_height(tip.x, tip.y, xy) - sink * 1.3
    points.append(tip)
    rhizome = new_curve("HM_Rhizome", points, authoring)
    rhizome["cr_nodes"] = count

    bottom = cfg["sand_bottom_z"]
    for i, node in enumerate(nodes):
        stem, right, forward = shoot_frame(i, count)
        emp = bpy.data.objects.new("HM_Shoot_%02d" % i, None)
        link(emp, authoring)
        emp.empty_display_type = "SINGLE_ARROW"
        emp.empty_display_size = max(0.01, cfg["stem_height_m"])
        emp.matrix_world = Matrix.Translation(node) @ Matrix((right, forward, stem)).transposed().to_4x4()
        tag(emp)
        for j, leaf in enumerate(plan_leaves(i, count, rng, cfg)):
            pts = leaf_points(node, stem, right, forward, leaf["tilt"], leaf["length"], leaf["fwd"], leaf["bow"], cfg)
            obj = new_curve("HM_Leaf_%02d_%d" % (i, j), pts, authoring)
            obj["cr_shoot"] = i
            obj["cr_young"] = 1 if leaf["young"] else 0
            obj["cr_twist"] = leaf["twist"]
        root_counts = cfg.get("root_counts")
        n_roots = root_counts[i % len(root_counts)] if root_counts else 2
        for r in range(n_roots):
            pts = _root_points(node, i, r, bottom, rng)
            new_curve("HM_Root_%02d_%d" % (i, r), pts, authoring)
    if cfg.get("variant") == "lesson":
        for a, b in zip(nodes, nodes[1:]):
            print("lesson chord_cm", round((a - b).length * 100, 2))

    arm = bpy.data.objects.new("HM_Armature", bpy.data.armatures.new("HM_Armature"))
    scene_col.objects.link(arm)
    arm.show_in_front = True
    tag(arm)

    text = bpy.data.texts.get("HM_HOW_TO_EDIT") or bpy.data.texts.new("HM_HOW_TO_EDIT")
    text.clear()
    text.write(HOW_TO)

    lc = layer_collection("Authoring")
    if lc:
        lc.hide_viewport = True
    authoring.hide_render = True
    return arm
