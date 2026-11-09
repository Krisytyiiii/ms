"""First layout of the curves. A later run does not move these points."""

import math

import bpy
from mathutils import Matrix, Vector

from .config import CONFIG, HOW_TO, leaf_count
from .sand import mound_z
from . import timeline
from .util import collection, layer_collection, link, set_bezier, tag

UP = Vector((0.0, 0.0, 1.0))


def _runner_points(xy, all_xy, cfg, first=None):
    """Bezier samples for one runner. first is the shared node where a branch leaves."""
    sink = cfg["rhizome_sink_m"]
    nodes = []
    if first is not None:
        nodes.append(first.copy())
    for x, y in xy:
        nodes.append(Vector((x, y, mound_z(x, y, all_xy, cfg) - sink)))
    points = []
    for k, node in enumerate(nodes):
        points.append(node)
        if k < len(nodes) - 1:
            mid = (node + nodes[k + 1]) * 0.5
            mid.z = mound_z(mid.x, mid.y, all_xy, cfg) - sink
            points.append(mid)
    if len(nodes) >= 2:
        lead = (nodes[-1] - nodes[-2]).normalized()
        tip = nodes[-1] + lead * cfg["rhizome_tip_m"]
        tip.z = mound_z(tip.x, tip.y, all_xy, cfg) - sink
        points.append(tip)
    return points, nodes


def _place_shoot(i, count, node, chain, at_node, ready, authoring, cfg):
    stem, right, forward = shoot_frame(i, count)
    emp = bpy.data.objects.new("CR_Shoot_%02d" % i, None)
    link(emp, authoring)
    emp.empty_display_type = "SINGLE_ARROW"
    emp.empty_display_size = cfg["stem_height_m"]
    emp.matrix_world = Matrix.Translation(node) @ Matrix((right, forward, stem)).transposed().to_4x4()
    emp.hide_render = True
    emp["cr_chain"] = int(chain)
    emp["cr_at"] = int(at_node)
    emp["cr_ready"] = int(ready)
    tag(emp)
    for j, leaf in enumerate(plan_leaves(i, count, cfg)):
        pts = leaf_points(node, stem, right, forward, leaf["tilt"], leaf["length"], leaf["fwd"], leaf["bow"], cfg)
        obj = new_curve("CR_Leaf_%02d_%d" % (i, j), pts, authoring)
        obj["cr_shoot"] = i
        obj["cr_young"] = 1 if leaf["young"] else 0
        obj["cr_twist"] = float(leaf["twist"])
        if leaf["hero"]:
            obj["cr_hero"] = 1
    for r in range(int(cfg["root_count"])):
        new_curve("CR_Root_%02d_%d" % (i, r), root_points(node, i, r, cfg), authoring)


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
    """Shoot 0 faces +Y, so a front view meets the flat face and a side view meets the edge."""
    if i == 0:
        yaw, lean_x, lean_y = 0.0, 0.0, 0.0
    else:
        yaw = 0.62 * math.sin(i * 1.7 + 0.4) + 0.28 * math.cos(i * 0.85)
        lean_x = 0.045 * math.sin(i * 0.95)
        lean_y = 0.05 * math.cos(i * 1.15)
    right = Vector((math.cos(yaw), math.sin(yaw), 0.0))
    forward = Vector((-math.sin(yaw), math.cos(yaw), 0.0))
    stem = (UP + right * lean_x + forward * lean_y).normalized()
    right = (right - stem * right.dot(stem)).normalized()
    forward = stem.cross(right).normalized()
    return stem, right, forward


def leaf_points(node, stem, right, forward, tilt, length, fwd, bow, cfg):
    height = cfg["stem_height_m"]
    base = node + stem * (height * cfg["leaf_base_frac"])
    exit_ = node + stem * (height * 1.02) + right * (0.0014 * math.sin(tilt))
    direction = (stem * math.cos(tilt) + right * math.sin(tilt)).normalized()
    reach = max(0.01, length - (exit_ - base).length)
    mid = exit_ + direction * (reach * 0.52) + forward * (fwd + bow * 0.35)
    tip = exit_ + direction * reach + forward * (fwd + bow)
    return [base, exit_, mid, tip]


def plan_leaves(i, count, cfg):
    n = leaf_count(i, cfg)
    spread = cfg["leaf_spread"] if n > 2 else cfg["leaf_spread"] * 0.62
    mid = 0.5 * (n - 1)
    tilts = [spread * ((j - mid) / max(mid, 1.0)) for j in range(n)]
    order = sorted(range(n), key=lambda j: abs(tilts[j]))
    lo, hi = cfg["leaf_length_m"]
    shoot_t = 0.0 if count == 1 else i / (count - 1)
    leaves = []
    for j in range(n):
        t = order.index(j) / max(1, n - 1)
        length = hi - (hi - lo) * (0.62 * t + 0.38 * shoot_t)
        length *= 1.0 + 0.02 * math.sin(i * 2.1 + j * 1.7)
        length = max(lo, min(hi, length))
        hero = i == 0 and order[0] == j
        leaves.append({
            "tilt": tilts[j],
            "length": length,
            "young": (not hero) and (t > 0.45 or shoot_t > 0.72),
            "fwd": 0.0 if hero else 0.004 * (1.0 if j % 2 == 0 else -1.0),
            "bow": 0.006 if hero else 0.008 + 0.006 * (1.0 - t),
            "twist": 0.0 if hero else 0.10 * math.sin(i + j),
            "hero": hero,
        })
    return leaves


def root_points(node, i, r, cfg):
    """Roots leave the node and spread across the sand, then turn down."""
    n = max(1, int(cfg["root_count"]))
    ang = (2.0 * math.pi * r / n) + i * 0.55
    lo, hi = cfg["root_spread_m"]
    reach = lo + (hi - lo) * ((i + r) % 3) / 2.0
    drop = cfg["root_length_m"] * (0.75 + 0.25 * (r % 2))
    dx, dy = math.cos(ang), math.sin(ang)
    # The node sits under the mound surface by rhizome_sink_m.
    surface = node.z + cfg["rhizome_sink_m"]
    return [
        node + Vector((0.0012 * dx, 0.0012 * dy, -0.0005)),
        Vector((node.x + dx * reach * 0.5, node.y + dy * reach * 0.5, surface - 0.0012)),
        Vector((node.x + dx * reach, node.y + dy * reach, surface - drop)),
    ]


def create_plant(cfg=CONFIG):
    scene_col = bpy.context.scene.collection
    controls = bpy.data.objects.new("CR_Controls", None)
    scene_col.objects.link(controls)
    controls.empty_display_size = 0.02
    controls["leaf_width_m"] = float(cfg["leaf_width_m"])
    controls["vein_count"] = int(cfg["vein_count"])
    controls["shoot_count"] = int(cfg["shoot_count"])
    controls.hide_render = True
    tag(controls)

    authoring = collection("Authoring")
    collection("Meadow")
    main_xy = [tuple(p) for p in cfg["main_xy"]]
    branches = []
    for join, pts in cfg["branch_xy"]:
        branches.append((int(join), [tuple(p) for p in pts]))
    all_xy = list(main_xy)
    for _join, pts in branches:
        all_xy.extend(pts)
    _points, main_nodes = _runner_points(main_xy, all_xy, cfg)
    rhizome = new_curve("CR_Rhizome", _points, authoring)
    rhizome["cr_nodes"] = len(main_nodes)
    rhizome["cr_join"] = -1
    main_nseg = max(1, len(main_nodes) - 1)

    shoot_i = 0
    total = len(main_nodes) + sum(len(pts) for _j, pts in branches)
    for i, node in enumerate(main_nodes):
        ready = 40 if i == 0 else timeline.node_arrived(i, main_nseg, 40, True)
        _place_shoot(shoot_i, total, node, 0, i, max(40, ready), authoring, cfg)
        shoot_i += 1
    for chain_i, (join, pts) in enumerate(branches, start=1):
        if join < 0 or join >= len(main_nodes):
            continue
        branch_ready = max(40, timeline.node_arrived(join, main_nseg, 40, True))
        _points, nodes = _runner_points(pts, all_xy, cfg, first=main_nodes[join])
        curve = new_curve("CR_Rhizome_%02d" % chain_i, _points, authoring)
        curve["cr_nodes"] = len(nodes)
        curve["cr_join"] = join
        nseg = max(1, len(nodes) - 1)
        for at, node in enumerate(nodes):
            if at == 0:
                continue
            ready = timeline.node_arrived(at, nseg, branch_ready, False)
            _place_shoot(shoot_i, total, node, chain_i, at, max(40, ready), authoring, cfg)
            shoot_i += 1
    cfg["shoot_count"] = shoot_i
    controls["shoot_count"] = shoot_i

    arm = bpy.data.objects.new("CR_Armature", bpy.data.armatures.new("CR_Armature"))
    scene_col.objects.link(arm)
    arm.location = (0.0, 0.0, 0.0)
    arm.rotation_euler = (0.0, 0.0, 0.0)
    arm.scale = (1.0, 1.0, 1.0)
    arm.show_in_front = True
    tag(arm)

    text = bpy.data.texts.get("CR_HOW_TO_EDIT") or bpy.data.texts.new("CR_HOW_TO_EDIT")
    text.clear()
    text.write(HOW_TO)
    authoring.hide_render = True
    lc = layer_collection("Authoring")
    if lc is not None:
        lc.hide_viewport = True
    return arm
