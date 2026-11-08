"""First-time layout: TH_Controls, Authoring curves and shoot empties, the empty armature."""

import math
import random

import bpy
from mathutils import Matrix, Vector

from .config import CONFIG, HOW_TO, leaf_count
from .sand import back_wall_y, sand_height
from .util import collection, layer_collection, link, set_bezier, tag

UP = Vector((0.0, 0.0, 1.0))


def _lesson_xy(count):
    """Front row in the cut face, then a row behind it. Depth is a display choice."""
    front_n = min(4, count)
    back_n = count - front_n

    def row(n, y, x0, x1):
        if n <= 0:
            return []
        if n == 1:
            return [((x0 + x1) * 0.5, y)]
        return [(x0 + (x1 - x0) * i / (n - 1), y) for i in range(n)]

    pts = row(front_n, -0.018, -0.105, 0.105)
    pts += row(back_n, 0.038, 0.070, -0.070)
    return pts


def node_xy(count, span, rng):
    from .config import CONFIG

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
    if CONFIG.get("variant") == "lesson":
        return _lesson_xy(count)
    del count, span, rng
    out = []
    for x, y in (
        (-0.09, -0.010),
        (0.00, -0.016),
        (0.09, -0.006),
        (-0.10, 0.03),
        (-0.02, 0.05),
        (0.07, 0.03),
        (0.11, 0.07),
        (-0.07, 0.08),
        (0.02, 0.09),
        (0.10, 0.10),
        (-0.10, 0.11),
        (-0.01, 0.12),
        (0.06, 0.105),
    ):
        out.append((x, min(y, back_wall_y(x) - 0.010)))
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
    from .config import CONFIG

    if CONFIG.get("variant") == "lesson":
        yaw = 0.18 * math.sin(i * 1.15 + 0.35)
    else:
        yaw = 1.0 * math.sin(i * 1.6 + 0.25) + 0.6 * math.cos(i * 0.85)
    lean_x = 0.045 * math.sin(i * 0.9)
    lean_y = 0.028
    right = Vector((math.cos(yaw), math.sin(yaw), 0.0))
    forward = Vector((-math.sin(yaw), math.cos(yaw), 0.0))
    stem = (UP + right * lean_x + forward * lean_y).normalized()
    right = (right - stem * right.dot(stem)).normalized()
    forward = stem.cross(right).normalized()
    return stem, right, forward


def leaf_points(node, stem, right, forward, tilt, length, fwd, bow, cfg):
    """A sickle along the whole ribbon, not a straight strap with a hooked tip."""
    height = cfg["stem_height_m"]
    base = node + stem * (height * cfg["leaf_base_frac"])
    exit_ = node + stem * (height * 1.05) + right * (0.0018 * tilt)
    reach = max(0.05, length - (exit_ - base).length)
    bend = float(cfg.get("sickle_rad", 1.45))
    bend *= 0.92 + 0.08 * abs(math.sin(tilt * 2.1 + 0.3))
    steps = 7
    pts = [base, exit_]
    pos = exit_.copy()
    step_len = reach / float(steps)
    for s in range(1, steps + 1):
        u = s / float(steps)
        # Exponent below 1 bends the lower blade as well as the tip.
        ang = tilt + bend * (u ** 0.62)
        direc = stem * math.cos(ang) + right * math.sin(ang) + forward * (0.55 * tilt)
        pos = pos + direc.normalized() * step_len
        pts.append(pos)
    return pts


def plan_leaves(i, count, rng, cfg):
    n = leaf_count(i)
    spread = 0.34 if n > 2 else 0.18
    tilts = [(-spread + 2 * spread * j / (n - 1)) + rng.uniform(-0.09, 0.09) for j in range(n)]
    lo, hi = cfg["leaf_length_m"]
    age = 1.0 - 0.32 * max(0.0, (i - (count - 4)) / 3.0)
    young_shoot = i >= count - 3
    order = sorted(range(n), key=lambda j: abs(tilts[j]))
    leaves = []
    for j in range(n):
        rank = order.index(j) / max(1, n - 1)
        length = (lo + (hi - lo) * (0.32 + 0.68 * rank) * rng.uniform(0.84, 1.02)) * age
        if cfg.get("variant") == "realistic":
            length = 0.042 + 0.028 * rank
        rank_sign = 1.0 if j % 2 == 0 else -1.0
        fwd = 0.01 * rank_sign
        bow = 0.0
        twist = 0.06 * rank_sign
        leaves.append({
            "tilt": tilts[j],
            "length": length if cfg.get("variant") == "realistic" else max(lo, min(hi, length)),
            "young": young_shoot or order[0] == j,
            "fwd": fwd,
            "bow": bow,
            "twist": twist,
        })
    return leaves


def _root_points(node, i, r, bottom, rng):
    """Smooth roots leave the node and stay in the sand. No bristles."""
    from .config import CONFIG

    rad = float(CONFIG.get("rhizome_radius_m", 0.006))
    under = max(0.0022, rad * 0.9)
    max_len = max(0.012, node.z - (bottom + 0.005))
    length = min(max_len, 0.022 + 0.006 * ((i + r) % 3))
    fan = (-1.0, 0.15, 1.0)[r % 3]
    reach = 0.005 + 0.008 * abs(fan)
    return [
        node + Vector((0.15 * rad * fan, -0.20 * rad, -under)),
        node + Vector((reach * fan * 0.42, -0.0022, -under - length * 0.48)),
        node + Vector((reach * fan, -0.0032, -under - length)),
    ]


def create_plant(cfg=CONFIG):
    rng = random.Random(cfg["seed"])
    count = cfg["shoot_count"]
    scene_col = bpy.context.scene.collection

    controls = bpy.data.objects.new("TH_Controls", None)
    scene_col.objects.link(controls)
    controls.empty_display_size = 0.015
    controls["leaf_width_m"] = cfg["leaf_width_m"]
    controls["leaf_thickness_m"] = cfg["leaf_thickness_m"]
    controls["vein_count"] = cfg["vein_count"]
    controls["tannin_bars"] = int(cfg.get("tannin_bars") or 0)
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
    rhizome = new_curve("TH_Rhizome", points, authoring)
    rhizome["cr_nodes"] = count

    bottom = cfg["sand_bottom_z"]
    for i, node in enumerate(nodes):
        stem, right, forward = shoot_frame(i, count)
        emp = bpy.data.objects.new("TH_Shoot_%02d" % i, None)
        link(emp, authoring)
        emp.empty_display_type = "SINGLE_ARROW"
        emp.empty_display_size = cfg["stem_height_m"]
        emp.matrix_world = Matrix.Translation(node) @ Matrix((right, forward, stem)).transposed().to_4x4()
        tag(emp)
        for j, leaf in enumerate(plan_leaves(i, count, rng, cfg)):
            pts = leaf_points(node, stem, right, forward, leaf["tilt"], leaf["length"], leaf["fwd"], leaf["bow"], cfg)
            obj = new_curve("TH_Leaf_%02d_%d" % (i, j), pts, authoring)
            obj["cr_shoot"] = i
            obj["cr_young"] = 1 if leaf["young"] else 0
            obj["cr_twist"] = leaf["twist"]
            obj["cr_px"] = float(forward.x)
            obj["cr_py"] = float(forward.y)
            obj["cr_pz"] = float(forward.z)
        root_counts = cfg.get("root_counts")
        n_roots = root_counts[i % len(root_counts)] if root_counts else (2 if i % 3 == 2 else 3)
        for r in range(n_roots):
            pts = _root_points(node, i, r, bottom, rng)
            new_curve("TH_Root_%02d_%d" % (i, r), pts, authoring)
    if cfg.get("variant") == "lesson":
        for a, b in zip(nodes, nodes[1:]):
            print("lesson chord_cm", round((a - b).length * 100, 2))

    arm = bpy.data.objects.new("TH_Armature", bpy.data.armatures.new("TH_Armature"))
    scene_col.objects.link(arm)
    arm.show_in_front = True
    tag(arm)

    text = bpy.data.texts.get("TH_HOW_TO_EDIT") or bpy.data.texts.new("TH_HOW_TO_EDIT")
    text.clear()
    text.write(HOW_TO)

    lc = layer_collection("Authoring")
    if lc:
        lc.hide_viewport = True
    authoring.hide_render = True
    return arm
