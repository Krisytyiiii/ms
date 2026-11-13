"""Assemble the serrulata meadow: one mound, one rhizome, shoots across it."""

import math

import bpy
from mathutils import Vector

from pinifolia_next.config import (
    FPS,
    FRAME_END,
    FRAME_START,
    LEAF_THICK_M,
    LEAF_WIDTH_M,
    ROOT_RADIUS_M,
    SHOOT_COUNT,
)
from pinifolia_next.grow import key_grow
from pinifolia_next.layout import LEAF_COUNT, LEAF_LEN, NODES, SEGMENTS, node_axis, roots_for, stem_height
from pinifolia_next.organs import (
    leaf_object,
    rhizome_object,
    root_object,
    scar_object,
    sheath_object,
    stem_object,
)
from pinifolia_next.rig import build_armature
from pinifolia_next.sand import sand_object
from pinifolia_next.textures import make_materials


def _collection(name):
    col = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(col)
    return col


def _curve(name, points, collection):
    curve = bpy.data.curves.new(name, type="CURVE")
    curve.dimensions = "3D"
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for index, point in enumerate(points):
        knot = spline.bezier_points[index]
        knot.co = point
        knot.handle_left_type = "AUTO"
        knot.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, curve)
    collection.objects.link(obj)
    obj.hide_render = True
    obj["cr_width_m"] = LEAF_WIDTH_M
    return obj


def _leaf_direction(yaw, lean):
    direction = Vector((math.sin(yaw) * math.sin(lean), 0.0, math.cos(lean)))
    return direction.normalized()


def _prepare_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.render.fps = FPS
    scene.frame_start = FRAME_START
    scene.frame_end = FRAME_END
    return scene


def build():
    _prepare_scene()
    meadow = _collection("Meadow")
    authoring = _collection("Authoring")
    mats = make_materials()
    specs = []
    pending = []

    for index, (parent, child, _start, _end, _idle) in enumerate(SEGMENTS):
        name = f"rhizome_{index:02d}"
        head = Vector(NODES[parent])
        tail = Vector(NODES[child])
        specs.append((name, head, tail, (0.0, 0.0, 1.0)))
        pending.append({
            "kind": "rhizome",
            "name": name,
            "seg": index,
            "rest_head": head,
            "make": ("rhizome", head, tail, f"Rhizome_{index:02d}"),
        })

    for node in range(SHOOT_COUNT):
        origin = Vector(NODES[node])
        height = stem_height(node)
        shoot = f"shoot_{node:02d}"
        specs.append((shoot, origin, origin + Vector((0.0, 0.0, height)), (0.0, 1.0, 0.0)))
        pending.append({
            "kind": "shoot",
            "name": shoot,
            "node": node,
            "phase": node * 0.65,
            "rest_head": origin,
            "make": ("shoot", origin, height, node),
        })
        count = LEAF_COUNT[node]
        for leaf in range(count):
            yaw = (leaf - (count - 1) / 2.0) * 0.07  # display: face stays toward the front
            lean = 0.04 + 0.035 * leaf  # display: needles stand nearly upright
            length = LEAF_LEN[node] * (0.78 + 0.22 * (leaf + 1) / count)  # display, still under 20 cm
            stagger = Vector((0.0, (leaf - (count - 1) / 2.0) * 0.0006, 0.0))
            base = origin + Vector((0.0, 0.0, height)) + stagger
            direction = _leaf_direction(yaw, lean)
            name = f"leaf_{node:02d}_{leaf}"
            specs.append((name, base, base + direction * length, (0.0, 1.0, 0.0)))
            pending.append({
                "kind": "leaf",
                "name": name,
                "node": node,
                "phase": node * 0.65 + leaf * 0.4,
                "stem_h": height,
                "rest_head": base,
                "make": ("leaf", base, length, yaw, lean, f"Leaf_{node:02d}_{leaf}", leaf == 0),
            })
        for root_index, (ang, spread, drop) in enumerate(roots_for(node)):
            run = Vector((math.cos(ang) * spread, math.sin(ang) * spread, -spread * 0.16))
            spread_name = f"root_{node:02d}_{root_index}"
            drop_name = f"root_{node:02d}_{root_index}d"
            spread_tail = origin + run
            drop_tail = spread_tail + Vector((0.0, 0.0, -drop))
            specs.append((spread_name, origin, spread_tail, (0.0, 0.0, 1.0)))
            specs.append((drop_name, spread_tail, drop_tail, (0.0, 1.0, 0.0)))
            pending.append({
                "kind": "spread",
                "name": spread_name,
                "node": node,
                "rest_head": origin,
                "make": ("root", origin, spread_tail, ROOT_RADIUS_M, ROOT_RADIUS_M * 0.7, f"Root_{node:02d}_{root_index}"),
            })
            pending.append({
                "kind": "drop",
                "name": drop_name,
                "node": node,
                "run": run,
                "rest_head": spread_tail,
                "make": ("root", spread_tail, drop_tail, ROOT_RADIUS_M * 0.7, ROOT_RADIUS_M * 0.35, f"Root_{node:02d}_{root_index}d"),
            })

    arm = build_armature(specs)
    meadow.objects.link(arm)
    bpy.context.scene.collection.objects.unlink(arm)

    objects = []
    for part in pending:
        part["matrix"] = arm.data.bones[part["name"]].matrix_local.copy()
        made = part["make"]
        kind = made[0]
        bone = part["name"]
        if kind == "rhizome":
            _head, tail, obj_name = made[1], made[2], made[3]
            obj = rhizome_object(part["rest_head"], tail, obj_name, mats["rhizome"], meadow, bone, arm)
        elif kind == "shoot":
            origin, height, node = made[1], made[2], made[3]
            top = origin + Vector((0.0, 0.0, height))
            obj = stem_object(origin, top, f"Shoot_{node:02d}", mats["stem"], meadow, bone, arm)
            objects.append(obj)
            objects.append(sheath_object(origin, height, f"Sheath_{node:02d}", mats["sheath"], meadow, bone, arm))
            objects.append(scar_object(origin, node_axis(node), f"Scar_{node:02d}", mats["scar"], meadow, bone, arm))
            continue
        elif kind == "leaf":
            _base, length, yaw, lean, obj_name, young = made[1:]
            mat = mats["young"] if young else mats["leaf"]
            obj = leaf_object(part["rest_head"], length, yaw, lean, obj_name, mat, meadow, bone, arm)
        else:
            head, tail, r0, r1, obj_name = made[1:]
            obj = root_object(head, tail, r0, r1, obj_name, mats["root"], meadow, bone, arm)
        objects.append(obj)

    objects.append(sand_object(mats["sand"], meadow))
    parts = [part for part in pending if part["kind"] != "base"]
    action = key_grow(arm, parts)

    _curve("HP_RhizomeMain", [Vector(NODES[i]) for i in range(6)], authoring)
    _curve("HP_RhizomeBranchA", [Vector(NODES[i]) for i in (2, 6, 7, 8)], authoring)
    _curve("HP_RhizomeBranchB", [Vector(NODES[i]) for i in (3, 10, 11, 12)], authoring)
    _curve("HP_LeafExample", [
        Vector(NODES[0]) + Vector((0.0, 0.0, stem_height(0))),
        Vector(NODES[0]) + Vector((0.0, 0.0, stem_height(0) + LEAF_LEN[0])),
    ], authoring)

    controls = bpy.data.objects.new("HP_Controls", None)
    controls.empty_display_size = 0.03
    controls["leaf_width_m"] = LEAF_WIDTH_M
    controls["leaf_thickness_m"] = LEAF_THICK_M
    controls["shoot_count"] = SHOOT_COUNT
    authoring.objects.link(controls)

    note_curve = bpy.data.curves.new("HP_HOW_TO_EDIT", type="FONT")
    note_curve.body = (
        "Unhide Authoring and move a curve, then rebuild the meadow. "
        "Width is leaf_width_m on HP_Controls. "
        "Pose a leaf bone at frame 300 to change the fan, and leave Grow in place. "
        "publish writes the glb and keeps these curves."
    )
    note = bpy.data.objects.new("HP_HOW_TO_EDIT", note_curve)
    note.location = (-0.2, -0.3, 0.0)
    note.scale = (0.02, 0.02, 0.02)
    authoring.objects.link(note)
    for obj in authoring.objects:
        obj.hide_set(True)
        obj.hide_render = True

    bpy.context.scene.frame_set(300)
    return arm, objects, action
