"""First-time layout: CS_Controls, Authoring curves and shoot empties, the empty armature."""

import math
import random

import bpy
from mathutils import Matrix, Vector

from .config import CONFIG, HOW_TO, leaf_count
from .sand import sand_height
from .util import collection, layer_collection, link, set_bezier, tag

UP = Vector((0.0, 0.0, 1.0))


# A patch across the bed, not a front row. The back rank sits near the
# back wall and faces the other way, so a turn does not show bare sand.
# Neighbour spacing stays inside 1–4.5 cm. Depth is a display choice.
PATCH_XY = (
    (-0.072, -0.010),
    (-0.036, -0.006),
    (0.000, -0.012),
    (0.036, -0.008),
    (0.072, -0.010),
    (0.072, 0.024),
    (0.036, 0.030),
    (0.000, 0.026),
    (-0.036, 0.022),
    (-0.036, 0.058),
    (0.000, 0.064),
    (0.036, 0.060),
    (0.072, 0.066),
)

def node_xy(count, span, rng):
    """The phone model and the lesson use this same patch."""
    return list(PATCH_XY)


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
    # Front rank faces the lesson camera. Middle rank turns sideways.
    # Back rank faces the far side of the bed.
    if i < 5:
        yaw = 0.18 * math.sin(i * 1.35 + 0.25)
    elif i < 9:
        yaw = 1.35 if i % 2 == 0 else -1.35
    else:
        yaw = math.pi + 0.16 * math.sin(i * 0.8)
    lean_x = 0.035 * math.sin(i * 0.9)
    lean_y = 0.012 + 0.008 * math.cos(i * 1.1)
    right = Vector((math.cos(yaw), math.sin(yaw), 0.0))
    forward = Vector((-math.sin(yaw), math.cos(yaw), 0.0))
    stem = (UP + right * lean_x + forward * lean_y).normalized()
    right = (right - stem * right.dot(stem)).normalized()
    forward = stem.cross(right).normalized()
    return stem, right, forward


def leaf_points(node, stem, right, forward, tilt, length, fwd, bow, cfg):
    height = cfg["stem_height_m"]
    base = node + stem * (height * cfg["leaf_base_frac"])
    exit_ = node + stem * (height * 1.02) + right * (0.0012 * tilt)
    direction = (stem * math.cos(tilt) + right * math.sin(tilt)).normalized()
    out = (right * math.cos(tilt) - stem * math.sin(tilt)) * (1.0 if tilt >= 0 else -1.0)
    reach = length - (exit_ - base).length
    mid = exit_ + direction * (reach * 0.52) - out * (bow * 0.45) + forward * (fwd * 0.7)
    tip = exit_ + direction * reach + out * (bow * 0.85) + forward * (fwd * 1.15)
    return [base, exit_, mid, tip]


def plan_leaves(i, count, rng, cfg):
    n = leaf_count(i)
    spread = 0.82 if n > 2 else 0.46
    tilts = [(-spread + 2 * spread * j / (n - 1)) + rng.uniform(-0.05, 0.05) for j in range(n)]
    lo, hi = cfg["leaf_length_m"]
    order = sorted(range(n), key=lambda j: abs(tilts[j]))
    leaves = []
    for j in range(n):
        rank = order.index(j) / max(1, n - 1)
        length = lo + (hi - lo) * (0.55 + 0.45 * rank) * rng.uniform(0.94, 1.02)
        rank_sign = 1.0 if j % 2 == 0 else -1.0
        # Stiff wide straps. A floppy ribbon bow would read as the smooth species.
        leaves.append({
            "tilt": tilts[j],
            "length": max(lo, min(hi, length)),
            "young": order[0] == j,
            "fwd": 0.004 * rank_sign,
            "bow": 0.0025 + 0.0015 * rng.random(),
            "twist": 0.05 * rank_sign,
        })
    return leaves


def _root_points(node, i, r, bottom, rng):
    """Fine roots at the node, down and toward the front cut. Not cord roots."""
    max_len = max(0.010, node.z - (bottom + 0.004))
    length = min(max_len, 0.012 + 0.005 * ((i + r) % 3))
    fan = (-1.0, 0.12, 1.0)[r % 3]
    reach = 0.0035 + 0.0045 * abs(fan)
    return [
        node + Vector((0.0003 * fan, -0.0005, -0.0004)),
        node + Vector((reach * fan * 0.45, -0.0035, -length * 0.48)),
        node + Vector((reach * fan, -0.0080, -length)),
    ]


def create_plant(cfg=CONFIG):
    rng = random.Random(cfg["seed"])
    count = cfg["shoot_count"]
    scene_col = bpy.context.scene.collection

    controls = bpy.data.objects.new("CS_Controls", None)
    scene_col.objects.link(controls)
    controls.empty_display_size = 0.015
    controls["leaf_width_m"] = cfg["leaf_width_m"]
    controls["leaf_thickness_m"] = cfg["leaf_thickness_m"]
    controls["vein_count"] = cfg["vein_count"]
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
    rhizome = new_curve("CS_Rhizome", points, authoring)
    rhizome["cr_nodes"] = count

    bottom = cfg["sand_bottom_z"]
    for i, node in enumerate(nodes):
        stem, right, forward = shoot_frame(i, count)
        emp = bpy.data.objects.new("CS_Shoot_%02d" % i, None)
        link(emp, authoring)
        emp.empty_display_type = "SINGLE_ARROW"
        emp.empty_display_size = cfg["stem_height_m"]
        emp.matrix_world = Matrix.Translation(node) @ Matrix((right, forward, stem)).transposed().to_4x4()
        tag(emp)
        for j, leaf in enumerate(plan_leaves(i, count, rng, cfg)):
            pts = leaf_points(node, stem, right, forward, leaf["tilt"], leaf["length"], leaf["fwd"], leaf["bow"], cfg)
            obj = new_curve("CS_Leaf_%02d_%d" % (i, j), pts, authoring)
            obj["cr_shoot"] = i
            obj["cr_young"] = 1 if leaf["young"] else 0
            obj["cr_twist"] = leaf["twist"]
        root_counts = cfg.get("root_counts")
        n_roots = root_counts[i % len(root_counts)] if root_counts else (2 if i % 3 == 2 else 3)
        for r in range(n_roots):
            pts = _root_points(node, i, r, bottom, rng)
            new_curve("CS_Root_%02d_%d" % (i, r), pts, authoring)
    if cfg.get("variant") == "lesson":
        for a, b in zip(nodes, nodes[1:]):
            print("lesson chord_cm", round((a - b).length * 100, 2))

    arm = bpy.data.objects.new("CS_Armature", bpy.data.armatures.new("CS_Armature"))
    scene_col.objects.link(arm)
    arm.show_in_front = True
    tag(arm)

    text = bpy.data.texts.get("CS_HOW_TO_EDIT") or bpy.data.texts.new("CS_HOW_TO_EDIT")
    text.clear()
    text.write(HOW_TO)

    lc = layer_collection("Authoring")
    if lc:
        lc.hide_viewport = True
    authoring.hide_render = True
    return arm
