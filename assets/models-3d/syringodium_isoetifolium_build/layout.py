"""A stand of noodle shoots. Leaves lean in different directions, not in one flat fan."""

import math

import bpy
from mathutils import Matrix, Vector

from .config import CONFIG, HOW_TO
from .sand import front_lip_y, sand_height
from .util import collection, layer_collection, link, set_bezier, tag

UP = Vector((0.0, 0.0, 1.0))

# Order is the buried stem's path. on_cut shoots sit in the front face.
SHOOTS = (
    {"xy": (-0.08, None), "n": 2, "yaw": -0.3, "roots": 2, "on_cut": True},
    {"xy": (0.02, None), "n": 2, "yaw": 0.4, "roots": 2, "on_cut": True, "hero": 0},
    {"xy": (0.10, None), "n": 2, "yaw": -0.6, "roots": 2, "on_cut": True},
    {"xy": (-0.10, 0.03), "n": 2, "yaw": 1.1, "roots": 2},
    {"xy": (0.00, 0.045), "n": 2, "yaw": -1.0, "roots": 2},
    {"xy": (0.09, 0.03), "n": 2, "yaw": 0.7, "roots": 2},
    {"xy": (-0.06, 0.07), "n": 2, "yaw": 1.8, "roots": 2},
    {"xy": (0.05, 0.08), "n": 2, "yaw": -0.4, "roots": 2},
    {"xy": (0.11, 0.07), "n": 2, "yaw": 2.2, "roots": 2},
    {"xy": (-0.10, 0.10), "n": 2, "yaw": 0.2, "roots": 2},
    {"xy": (-0.02, 0.11), "n": 2, "yaw": -1.6, "roots": 2},
    {"xy": (0.07, 0.105), "n": 2, "yaw": 1.3, "roots": 2},
    {"xy": (-0.07, 0.05), "n": 2, "yaw": 0.9, "roots": 2},
    {"xy": (0.03, 0.06), "n": 2, "yaw": -0.8, "roots": 2},
)


def _node(spec):
    x, y = spec["xy"]
    if spec.get("on_cut"):
        y = front_lip_y(x) + 0.0006
        z = sand_height(x, y) - 0.011
    else:
        z = sand_height(x, y) - CONFIG["rhizome_sink_m"]
    return Vector((x, y, z))


def new_curve(name, points, col):
    data = bpy.data.curves.new(name, "CURVE")
    data.dimensions = "3D"
    spline = data.splines.new("BEZIER")
    set_bezier(spline, points)
    obj = bpy.data.objects.new(name, data)
    link(obj, col)
    obj.hide_render = True
    return tag(obj)


def shoot_frame(yaw):
    right = Vector((math.cos(yaw), math.sin(yaw), 0.0))
    forward = Vector((-math.sin(yaw), math.cos(yaw), 0.0))
    stem = UP.copy()
    return stem, right, forward


def leaf_points(node, stem, right, forward, leaf, cfg):
    height = cfg["stem_height_m"]
    base = node + stem * (height * cfg["leaf_base_frac"])
    horiz = (right * math.cos(leaf["azimuth"]) + forward * math.sin(leaf["azimuth"])).normalized()
    direction = (stem * math.cos(leaf["lean"]) + horiz * math.sin(leaf["lean"])).normalized()
    bend = stem.cross(horiz).normalized()
    length = leaf["length"]
    bow = leaf["bow"]
    # Almost along one line, with a small bend. The bone and the tube stay aligned,
    # so the cross-section stays a circle instead of an oblique oval.
    mid = base + direction * (length * 0.50) + bend * bow
    tip = base + direction * length + bend * (bow * 0.25)
    return [base, mid, tip]


def plan_leaves(spec, cfg):
    n = spec["n"]
    lo, hi = cfg["leaf_length_m"]
    hero = spec.get("hero")
    leaves = []
    for j in range(n):
        rank = j / max(1, n - 1)
        az = (j - (n - 1) / 2.0) * 0.72
        lean = 0.10 + 0.07 * (j % 3)
        length = lo + (hi - lo) * (0.15 + 0.80 * rank)
        bow = 0.002 if j % 2 == 0 else -0.0016
        is_hero = hero == j
        if hero is not None and not is_hero:
            az = 0.9 + j * 0.35
            lean = 0.14
        if is_hero:
            az = -0.85
            lean = 0.26
            length = 0.195
            bow = 0.0012
        leaves.append({
            "azimuth": az,
            "lean": lean,
            "length": max(lo, min(hi, length)),
            "bow": bow,
            "hero": is_hero,
            "young": (not is_hero) and j == 0,
        })
    return leaves


def _root_points(node, index, r, on_cut):
    """Fine roots grow down from the node. On the cut they hang in front of the face."""
    side = -1.0 if r % 2 == 0 else 1.0
    if r == 2:
        side = 0.15
    length = 0.016 + 0.003 * ((index + r) % 3)
    reach = 0.004 + 0.002 * r
    if on_cut:
        return [
            node + Vector((0.001 * side, -0.0016, -0.001)),
            node + Vector((reach * side * 0.55, -0.0045, -length * 0.48)),
            node + Vector((reach * side, -0.0075, -length)),
        ]
    return [
        node + Vector((0.0006 * side, 0.0004, -0.001)),
        node + Vector((reach * side * 0.6, 0.002, -length * 0.5)),
        node + Vector((reach * side, 0.003, -length)),
    ]


def create_plant(cfg=CONFIG):
    scene_col = bpy.context.scene.collection
    controls = bpy.data.objects.new("SI_Controls", None)
    scene_col.objects.link(controls)
    controls.empty_display_size = 0.015
    controls["leaf_diameter_m"] = cfg["leaf_diameter_m"]
    controls["sheath_shape"] = cfg["sheath_shape"]
    controls["shoot_count"] = len(SHOOTS)
    tag(controls)

    authoring = collection("Authoring")
    collection("Meadow")
    nodes = [_node(spec) for spec in SHOOTS]
    points = []
    for k, node in enumerate(nodes):
        points.append(node)
        if k < len(nodes) - 1:
            mid = (node + nodes[k + 1]) * 0.5
            mid.z = min(node.z, nodes[k + 1].z) - 0.0015
            points.append(mid)
    rhizome = new_curve("SI_Rhizome", points, authoring)
    rhizome["cr_nodes"] = len(nodes)

    for i, (spec, node) in enumerate(zip(SHOOTS, nodes)):
        stem, right, forward = shoot_frame(spec["yaw"])
        emp = bpy.data.objects.new("SI_Shoot_%02d" % i, None)
        link(emp, authoring)
        emp.empty_display_type = "SINGLE_ARROW"
        emp.empty_display_size = cfg["stem_height_m"]
        emp.matrix_world = Matrix.Translation(node) @ Matrix((right, forward, stem)).transposed().to_4x4()
        tag(emp)
        for j, leaf in enumerate(plan_leaves(spec, cfg)):
            pts = leaf_points(node, stem, right, forward, leaf, cfg)
            obj = new_curve("SI_Leaf_%02d_%d" % (i, j), pts, authoring)
            obj["cr_shoot"] = i
            obj["cr_young"] = 1 if leaf["young"] else 0
            obj["cr_twist"] = 0.0
            obj["cr_hero"] = 1 if leaf["hero"] else 0
        for r in range(spec["roots"]):
            pts = _root_points(node, i, r, spec.get("on_cut", False))
            new_curve("SI_Root_%02d_%d" % (i, r), pts, authoring)

    arm = bpy.data.objects.new("SI_Armature", bpy.data.armatures.new("SI_Armature"))
    scene_col.objects.link(arm)
    arm.show_in_front = True
    tag(arm)
    text = bpy.data.texts.get("SI_HOW_TO_EDIT") or bpy.data.texts.new("SI_HOW_TO_EDIT")
    text.clear()
    text.write(HOW_TO)
    lc = layer_collection("Authoring")
    if lc:
        lc.hide_viewport = True
    authoring.hide_render = True
    return arm
