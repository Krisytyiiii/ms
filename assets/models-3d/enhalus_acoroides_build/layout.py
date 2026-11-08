"""First-time layout: controls, Authoring curves and shoot empties, the empty armature."""

import math
import random

import bpy
from mathutils import Matrix, Vector

from .config import px, CONFIG, HOW_TO, leaf_count
from .sand import sand_height
from .util import collection, layer_collection, link, set_bezier, tag

UP = Vector((0.0, 0.0, 1.0))


# Three passes across the bed, not a clump in the middle.
# Spacing stays inside 1–4.5 cm. Depth is a display choice, not a Mati measurement.
LESSON_XY = (
    (-0.1320, -0.0166),
    (-0.0943, -0.0166),
    (-0.0566, -0.0166),
    (-0.0189, -0.0166),
    (0.0189, -0.0166),
    (0.0566, -0.0166),
    (0.0943, -0.0166),
    (0.1320, -0.0166),
    (0.1180, 0.0220),
    (0.0823, 0.0231),
    (0.0466, 0.0243),
    (0.0109, 0.0254),
    (-0.0249, 0.0266),
    (-0.0606, 0.0277),
    (-0.0963, 0.0289),
    (-0.1320, 0.0300),
    (-0.1180, 0.0580),
    (-0.0770, 0.0587),
    (-0.0360, 0.0593),
    (0.0050, 0.0600),
    (0.0460, 0.0607),
    (0.0870, 0.0613),
    (0.1280, 0.0620),
)


def node_xy(count, span, rng):
    """Four shoots just behind the cut, with a little depth so the row is not flat."""
    from .sand import front_cut_y

    out = []
    count = max(1, int(count))
    for i in range(count):
        t = 0.0 if count == 1 else i / (count - 1)
        x = (t - 0.5) * span
        # Proud of the wavy cut. The cut's own curve supplies the depth.
        y = front_cut_y(x) - 0.014
        out.append((x, y))
    return out


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
    # Same pose in the phone file and the lesson, so the meadow matches.
    yaw = 0.22 * math.sin(i * 1.4 + 0.4) + 0.04 * (i - 0.5 * (count - 1))
    lean_x = 0.04 * math.sin(i * 0.9)
    lean_y = 0.015
    right = Vector((math.cos(yaw), math.sin(yaw), 0.0))
    forward = Vector((-math.sin(yaw), math.cos(yaw), 0.0))
    stem = (UP + right * lean_x + forward * lean_y).normalized()
    right = (right - stem * right.dot(stem)).normalized()
    forward = stem.cross(right).normalized()
    return stem, right, forward


def leaf_points(node, stem, right, forward, tilt, length, fwd, bow, cfg):
    """Mostly upright tapes. A small lean shows the rolled edge without folding the blade flat."""
    height = cfg["stem_height_m"]
    base = node + stem * (height * cfg["leaf_base_frac"])
    exit_ = node + stem * (height * 1.04) + right * (0.0016 * tilt)
    direction = (stem * math.cos(tilt) + right * math.sin(tilt)).normalized()
    reach = max(0.05, length - (exit_ - base).length)
    mid = exit_ + direction * (reach * 0.46) + forward * (fwd * 0.25)
    tip = exit_ + direction * reach + forward * (fwd * 0.45)
    return [base, exit_, mid, tip]


def plan_leaves(i, count, rng, cfg):
    """Long tapes inside the record's 30–150 cm. None of them is a short strap."""
    n = leaf_count(i)
    spread = 0.58 if n > 2 else 0.34
    tilts = [(-spread + 2 * spread * j / (n - 1)) + rng.uniform(-0.04, 0.04) for j in range(n)]
    lo, hi = cfg["leaf_length_m"]
    age = 1.0 - 0.18 * (i / max(1, count - 1))
    order = sorted(range(n), key=lambda j: abs(tilts[j]))
    leaves = []
    for j in range(n):
        rank = order.index(j) / max(1, n - 1)
        length = (lo + (hi - lo) * (0.20 + 0.80 * rank) * rng.uniform(0.96, 1.0)) * age
        span = max(lo, min(hi, length))
        rank_sign = 1.0 if j % 2 == 0 else -1.0
        fwd = 0.035 * span * rank_sign
        bow = 0.012 * span
        twist = 0.85 if j == n // 2 else 0.42 * rank_sign
        leaves.append({
            "tilt": tilts[j],
            "length": span,
            "young": i == count - 1 and j == 0,
            "fwd": fwd,
            "bow": bow,
            "twist": twist,
        })
    return leaves


def _root_points(node, i, r, bottom, rng):
    """Thick unbranched cords in the open cut, still attached to the rhizome."""
    from .sand import front_cut_y

    fan = (-0.7, 0.55)[r % 2]
    end_z = max(bottom + 0.030, node.z - 0.042)
    end_x = max(-0.18, min(0.18, node.x + 0.016 * fan))
    end_y = front_cut_y(node.x) - 0.018 - 0.004 * r
    start = node + Vector((0.003 * fan, -0.004, -0.006))
    mid = Vector((node.x + 0.008 * fan, node.y - 0.010, node.z - 0.016))
    low = Vector(((node.x + end_x) * 0.5, (node.y + end_y) * 0.5, (node.z + end_z) * 0.45))
    end = Vector((end_x, end_y, end_z))
    return [start, mid, low, end]


def create_plant(cfg=CONFIG):
    rng = random.Random(cfg["seed"])
    count = cfg["shoot_count"]
    scene_col = bpy.context.scene.collection

    controls = bpy.data.objects.new(px("Controls"), None)
    scene_col.objects.link(controls)
    controls.empty_display_size = 0.015
    controls["leaf_width_m"] = cfg["leaf_width_m"]
    controls["leaf_thickness_m"] = cfg["leaf_thickness_m"]
    controls["vein_count"] = cfg["vein_count"]
    controls["shoot_count"] = count
    controls["margin_roll"] = cfg["margin_roll"]
    controls["bristle_length_m"] = cfg["bristle_length_m"]
    controls["bristle_count"] = cfg["bristle_count"]
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
    tip = nodes[-1] + lead * 0.028
    tip.z = sand_height(tip.x, tip.y, xy) - sink * 1.3
    points.append(tip)
    rhizome = new_curve(px("Rhizome"), points, authoring)
    rhizome["cr_nodes"] = count

    bottom = cfg["sand_bottom_z"]
    for i, node in enumerate(nodes):
        stem, right, forward = shoot_frame(i, count)
        emp = bpy.data.objects.new(px("Shoot_%02d") % i, None)
        link(emp, authoring)
        emp.empty_display_type = "SINGLE_ARROW"
        emp.empty_display_size = cfg["stem_height_m"]
        emp.matrix_world = Matrix.Translation(node) @ Matrix((right, forward, stem)).transposed().to_4x4()
        tag(emp)
        for j, leaf in enumerate(plan_leaves(i, count, rng, cfg)):
            pts = leaf_points(node, stem, right, forward, leaf["tilt"], leaf["length"], leaf["fwd"], leaf["bow"], cfg)
            obj = new_curve(px("Leaf_%02d_%d") % (i, j), pts, authoring)
            obj["cr_shoot"] = i
            obj["cr_young"] = 1 if leaf["young"] else 0
            obj["cr_twist"] = leaf["twist"]
        root_counts = cfg.get("root_counts")
        n_roots = root_counts[i % len(root_counts)] if root_counts else (2 if i % 3 == 2 else 3)
        for r in range(n_roots):
            pts = _root_points(node, i, r, bottom, rng)
            new_curve(px("Root_%02d_%d") % (i, r), pts, authoring)
    if cfg.get("variant") == "lesson":
        for a, b in zip(nodes, nodes[1:]):
            print("lesson chord_cm", round((a - b).length * 100, 2))

    arm = bpy.data.objects.new(px("Armature"), bpy.data.armatures.new(px("Armature")))
    scene_col.objects.link(arm)
    arm.show_in_front = True
    tag(arm)

    text = bpy.data.texts.get(px("HOW_TO_EDIT")) or bpy.data.texts.new(px("HOW_TO_EDIT"))
    text.clear()
    text.write(HOW_TO)

    lc = layer_collection("Authoring")
    if lc:
        lc.hide_viewport = True
    authoring.hide_render = True
    return arm
