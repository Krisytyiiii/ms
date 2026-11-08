"""First-time layout: HO_Controls, Authoring curves and shoot empties, the empty armature."""

import math
import random

import bpy
from mathutils import Matrix, Vector

from .config import CONFIG, HOW_TO, leaf_count
from .sand import sand_height
from .util import collection, layer_collection, link, set_bezier, tag

UP = Vector((0.0, 0.0, 1.0))


# One patch for the phone and the lesson. Not a distant line.
# Spacing stays inside 1–4.5 cm. Depth is a display choice, not a Mati measurement.
# Shoot 2 sits at the front so the lesson can count veins on that pair.
MEADOW_XY = (
    (-0.060, -0.019),
    (-0.022, -0.021),
    (0.016, -0.018),
    (0.052, -0.020),
    (0.070, 0.006),
    (0.042, 0.020),
    (0.006, 0.016),
    (-0.032, 0.026),
)


def node_xy(count, span, rng):
    from .config import CONFIG

    del count, span, rng
    if CONFIG.get("variant") == "lesson":
        return list(MEADOW_XY)
    return [
        (-0.08, -0.012),
        (0.00, -0.016),
        (0.08, -0.008),
        (-0.09, 0.03),
        (-0.01, 0.045),
        (0.07, 0.03),
        (0.10, 0.07),
        (-0.06, 0.08),
        (0.03, 0.09),
        (-0.10, 0.11),
        (-0.02, 0.12),
        (0.06, 0.105),
        (0.01, 0.06),
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
    # Same pose on the phone and in the lesson. A small yaw keeps the pairs
    # from being copies. The pair axis stays across the front of the bed.
    from .config import CONFIG

    del count
    if CONFIG.get("variant") == "lesson":
        yaw = 0.10 * math.sin(i * 1.17 + 0.4)
    else:
        yaw = 0.9 * math.sin(i * 1.5 + 0.3) + 0.5 * math.cos(i * 0.8)
    lean_x = 0.025 * math.sin(i * 0.9)
    lean_y = 0.012 * math.cos(i * 0.7)
    right = Vector((math.cos(yaw), math.sin(yaw), 0.0))
    forward = Vector((-math.sin(yaw), math.cos(yaw), 0.0))
    stem = (UP + right * lean_x + forward * lean_y).normalized()
    right = (right - stem * right.dot(stem)).normalized()
    forward = stem.cross(right).normalized()
    return stem, right, forward


def leaf_points(node, stem, right, forward, tilt, length, fwd, bow, cfg):
    """One oval of a pair. The petiole leaves the node and the blade spreads out.

    The pair is not an upright strap fan. `stem` and `forward` stay in the
    signature so a hand-edited curve can still be rebuilt.
    """
    del stem, forward, fwd
    sign = 1.0 if tilt >= 0.0 else -1.0
    spread = min(1.15, abs(float(tilt)))
    up = Vector((0.0, 0.0, 1.0))
    direction = (up * math.cos(spread) + right * (sign * math.sin(spread))).normalized()
    base = node + up * (cfg["stem_height_m"] * 0.9) + right * (0.0011 * sign)
    petiole = base + direction * (length * 0.30) + up * (bow * 0.35)
    mid = base + direction * (length * 0.64) + up * bow
    tip = base + direction * length + up * (bow * 0.25)
    return [base, petiole, mid, tip]


def plan_leaves(i, count, rng, cfg):
    """One opposite pair of ovals. Not a strap fan."""
    del rng
    n = leaf_count(i)
    if n != 2:
        raise RuntimeError("Halophila ovalis leaves arise in pairs, not a fan")
    lo, hi = cfg["leaf_length_m"]
    # Shoot 2 is the leaf the lesson moves in on. It uses the long display blade.
    span = 1.0 if i == 2 else 0.20 + 0.70 * ((i * 3) % 5) / 4.0
    length = lo + (hi - lo) * span
    tilt = 0.98
    leaves = []
    for j in range(2):
        sign = -1.0 if j == 0 else 1.0
        leaves.append({
            "tilt": sign * tilt,
            "length": length * (0.96 if j == 0 else 1.0),
            "young": i == count - 1,
            "fwd": 0.0,
            "bow": 0.0035,
            "twist": 0.14 * sign,
        })
    return leaves


def _root_points(node, i, r, bottom, rng):
    """Fine roots at the node. Front nodes cross the cut so they can be seen."""
    del rng
    max_len = max(0.010, node.z - (bottom + 0.004))
    length = min(max_len, 0.014 + 0.003 * ((i + r) % 3))
    fan = -1.0 if r % 2 == 0 else 1.0
    if node.y < 0.0:
        reach = 0.004 + 0.003 * r
        return [
            node + Vector((0.0004 * fan, -0.0006, -0.0005)),
            node + Vector((reach * fan * 0.45, -0.008, -length * 0.45)),
            node + Vector((reach * fan, -0.022, -length)),
        ]
    ang = i * 0.7 + r * 1.8
    dx = math.cos(ang) * 0.005
    dy = 0.004 + 0.004 * abs(math.sin(ang))
    return [
        node + Vector((0.0003 * fan, 0.0002, -0.0004)),
        node + Vector((dx * 0.45, dy * 0.35, -length * 0.5)),
        node + Vector((dx, dy, -length)),
    ]


def create_plant(cfg=CONFIG):
    rng = random.Random(cfg["seed"])
    count = cfg["shoot_count"]
    scene_col = bpy.context.scene.collection

    controls = bpy.data.objects.new("HO_Controls", None)
    scene_col.objects.link(controls)
    controls.empty_display_size = 0.015
    controls["leaf_width_m"] = cfg["leaf_width_m"]
    controls["leaf_thickness_m"] = cfg["leaf_thickness_m"]
    controls["vein_count"] = cfg["vein_count"]
    # 8 is the bottom of the Seagrass-Watch "eight or more" range.
    controls["cross_vein_pairs"] = int(cfg["cross_vein_pairs"])
    controls["hairs"] = 0
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
    rhizome = new_curve("HO_Rhizome", points, authoring)
    rhizome["cr_nodes"] = count

    bottom = cfg["sand_bottom_z"]
    for i, node in enumerate(nodes):
        stem, right, forward = shoot_frame(i, count)
        emp = bpy.data.objects.new("HO_Shoot_%02d" % i, None)
        link(emp, authoring)
        emp.empty_display_type = "SINGLE_ARROW"
        emp.empty_display_size = cfg["stem_height_m"]
        emp.matrix_world = Matrix.Translation(node) @ Matrix((right, forward, stem)).transposed().to_4x4()
        tag(emp)
        for j, leaf in enumerate(plan_leaves(i, count, rng, cfg)):
            pts = leaf_points(node, stem, right, forward, leaf["tilt"], leaf["length"], leaf["fwd"], leaf["bow"], cfg)
            obj = new_curve("HO_Leaf_%02d_%d" % (i, j), pts, authoring)
            obj["cr_shoot"] = i
            obj["cr_young"] = 1 if leaf["young"] else 0
            obj["cr_twist"] = leaf["twist"]
        root_counts = cfg.get("root_counts")
        n_roots = root_counts[i % len(root_counts)] if root_counts else (2 if i % 3 == 2 else 3)
        for r in range(n_roots):
            pts = _root_points(node, i, r, bottom, rng)
            new_curve("HO_Root_%02d_%d" % (i, r), pts, authoring)
    if cfg.get("variant") == "lesson":
        for a, b in zip(nodes, nodes[1:]):
            print("lesson chord_cm", round((a - b).length * 100, 2))

    arm = bpy.data.objects.new("HO_Armature", bpy.data.armatures.new("HO_Armature"))
    scene_col.objects.link(arm)
    arm.show_in_front = True
    tag(arm)

    text = bpy.data.texts.get("HO_HOW_TO_EDIT") or bpy.data.texts.new("HO_HOW_TO_EDIT")
    text.clear()
    text.write(HOW_TO)

    lc = layer_collection("Authoring")
    if lc:
        lc.hide_viewport = True
    authoring.hide_render = True
    return arm
