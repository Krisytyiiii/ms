"""Lesson camera for Halodule uninervis. Thirty seconds at 30 fps.

The meadow is already grown, the same plant as the phone file. The camera
holds on the trident, eases along the single vein, then rests on the ivory
rhizome and its black scars. No camera is written into the phone glb.
"""

import math

import bpy
from mathutils import Vector

from .util import collection, link, tag

# Names kept so an old card import still loads. The lesson does not use cards.
# Frames follow the spoken lesson. Patch, then the vein, then a hold on the trident, then the rhizome.
BUD_END = 300
CREEP_END = 408
ROOT_END = 520
SHOOT_END = 700
END = 900
VEIN_AT = 365
TIP_AT = 425
TIP_HOLD = 510
RHIZOME_AT = 560


def _action(arm):
    old = bpy.data.actions.get("Grow")
    if old:
        bpy.data.actions.remove(old)
    for pb in arm.pose.bones:
        pb.rotation_mode = "XYZ"
        pb.location = (0.0, 0.0, 0.0)
        pb.rotation_euler = (0.0, 0.0, 0.0)
        pb.scale = (1.0, 1.0, 1.0)
    action = bpy.data.actions.new("Grow")
    action.use_fake_user = True
    ad = arm.animation_data_create()
    ad.action = action
    try:
        ad.action_slot = action.slots.new("OBJECT", arm.name)
    except (AttributeError, TypeError, RuntimeError):
        pass
    return action


def animate(arm, cfg):
    """Hold the grown meadow. A small leaf sway keeps the patch alive."""
    from .grow import _key, _polish

    action = _action(arm)
    leaves = []
    for pb in arm.pose.bones:
        if pb.name == "base":
            continue
        _key(pb, 1, scale=1.0, rot=(0.0, 0.0, 0.0), loc=(0.0, 0.0, 0.0))
        if pb.name.startswith("leaf_"):
            leaves.append(pb.name)
        else:
            _key(pb, END, scale=1.0, rot=(0.0, 0.0, 0.0), loc=(0.0, 0.0, 0.0))
    for index, name in enumerate(leaves):
        pb = arm.pose.bones[name]
        for frame in range(1, END + 1, 12):
            phase = (frame / 48.0) * math.tau - index * 0.35
            amp = 0.018
            rot = (amp * math.sin(phase), amp * 0.45 * math.sin(phase + 0.8), amp * 0.25 * math.cos(phase))
            _key(pb, frame, scale=1.0, rot=rot, loc=(0.0, 0.0, 0.0))
        _key(pb, END, scale=1.0, rot=(0.0, 0.0, 0.0), loc=(0.0, 0.0, 0.0))
    _polish(action, END)
    action.use_frame_range = True
    action.frame_start = 1
    action.frame_end = END
    bpy.context.scene.frame_end = END
    return action


def _world_verts(obj):
    bpy.context.view_layer.update()
    return [obj.matrix_world @ v.co for v in obj.data.vertices]


def _hero():
    """The leaf whose three tooth tips are easiest to see from the front."""
    best = None
    for obj in bpy.data.objects:
        if obj.type != "MESH" or not obj.name.startswith("Leaf_"):
            continue
        verts = _world_verts(obj)
        if len(verts) < 12:
            continue
        anchor = min(verts, key=lambda p: p.z)
        ranked = sorted(verts, key=lambda p: (p - anchor).length, reverse=True)
        tips = [ranked[0]]
        for point in ranked[1:]:
            if all((point - kept).length > 0.0016 for kept in tips):
                tips.append(point)
            if len(tips) == 3:
                break
        if len(tips) < 3:
            continue
        tip = tips[0]
        axis = tip - anchor
        if axis.length < 1e-6:
            continue
        axis_n = axis.normalized()
        side = max(verts, key=lambda p: (p - anchor).cross(axis_n).length)
        lat = side - anchor
        lat = lat - axis_n * lat.dot(axis_n)
        if lat.length < 1e-8:
            continue
        normal = axis_n.cross(lat.normalized())
        span = (tips[1] - tips[2]).length
        score = tip.z * 4.0 + axis.length * 0.15 + abs(normal.y) + span * 8.0
        if best is None or score > best[0]:
            best = (score, obj.name, anchor, tip, tips, span)
    if best is None:
        raise RuntimeError("no leaf with a trident tip")
    _score, name, anchor, tip, tips, span = best
    print("HERO", name, "TIP_SPAN_MM", round(span * 1000.0, 1), "TIPS", len(tips))
    return anchor, tip


def _nodes():
    empties = sorted(
        (obj for obj in bpy.data.objects if obj.name.startswith("HU_Shoot_")),
        key=lambda obj: obj.name,
    )
    return [obj.matrix_world.translation.copy() for obj in empties]


def _bezier(obj):
    from .grow import fcurves

    action = obj.animation_data.action if obj.animation_data else None
    if action is None:
        return
    for fc in fcurves(action):
        for kp in fc.keyframe_points:
            kp.interpolation = "BEZIER"
            kp.handle_left_type = "AUTO_CLAMPED"
            kp.handle_right_type = "AUTO_CLAMPED"
        fc.update()


def _key_loc(obj, frame, point):
    obj.location = point
    obj.keyframe_insert("location", frame=frame)


def _rhizome_aim(nodes):
    """A point on the ivory cord where the front cut opens it."""
    from .sand import front_cut_y

    obj = bpy.data.objects.get("Rhizome")
    path = [(n.x, n.y) for n in nodes]
    if obj is None or obj.type != "MESH" or not path:
        front = min(nodes, key=lambda p: p.y)
        return front + Vector((0.0, -0.001, 0.0))
    verts = _world_verts(obj)
    ranked = sorted(verts, key=lambda p: p.y - front_cut_y(p.x, path))
    band = [p for p in ranked[:100] if -0.05 < p.x < 0.06] or ranked[:40]
    aim = sum(band, Vector()) / len(band)
    print("RHIZOME_AIM", tuple(round(c, 4) for c in aim), "BAND", len(band))
    return aim


def _eye(aim, dist, lift, x_off=0.0):
    return Vector((aim.x + x_off, aim.y - dist, aim.z + lift))


def frame_camera(cam):
    """Front camera. Trident, then the vein, then the ivory rhizome. No orbit."""
    anchor, tip = _hero()
    nodes = _nodes()
    if not nodes:
        return
    col = collection("Reef")
    previous = bpy.data.objects.get("HU_LessonAim")
    if previous is not None:
        bpy.data.objects.remove(previous, do_unlink=True)
    aim = bpy.data.objects.new("HU_LessonAim", None)
    link(aim, col)
    kinds = [item.identifier for item in aim.bl_rna.properties["empty_display_type"].enum_items]
    if "PLAIN_AXES" in kinds:
        aim.empty_display_type = "PLAIN_AXES"
    aim.empty_display_size = 0.008
    tag(aim)
    if aim.animation_data:
        aim.animation_data_clear()
    if cam.animation_data:
        cam.animation_data_clear()
    for constraint in list(cam.constraints):
        if constraint.type == "TRACK_TO":
            cam.constraints.remove(constraint)

    center = sum(nodes, Vector()) / len(nodes)
    patch = center + Vector((0.0, 0.0, 0.045))
    vein = anchor.lerp(tip, 0.55)
    fork = anchor.lerp(tip, 0.90)
    rhizome = _rhizome_aim(nodes)

    _key_loc(aim, 1, patch)
    _key_loc(aim, BUD_END, patch)
    _key_loc(aim, VEIN_AT, vein)
    _key_loc(aim, CREEP_END, vein)
    _key_loc(aim, TIP_AT, fork)
    _key_loc(aim, TIP_HOLD, fork)
    _key_loc(aim, RHIZOME_AT, rhizome)
    _key_loc(aim, END, rhizome)

    track = cam.constraints.new("TRACK_TO")
    track.target = aim
    axes = [item.identifier for item in track.bl_rna.properties["track_axis"].enum_items]
    ups = [item.identifier for item in track.bl_rna.properties["up_axis"].enum_items]
    if "TRACK_NEGATIVE_Z" in axes:
        track.track_axis = "TRACK_NEGATIVE_Z"
    if "UP_Y" in ups:
        track.up_axis = "UP_Y"

    _key_loc(cam, 1, _eye(patch, 0.40, 0.035))
    _key_loc(cam, BUD_END, _eye(patch, 0.38, 0.032))
    _key_loc(cam, VEIN_AT, _eye(vein, 0.16, 0.018, 0.006))
    _key_loc(cam, CREEP_END, _eye(vein, 0.155, 0.016, 0.006))
    _key_loc(cam, TIP_AT, _eye(fork, 0.10, 0.016, 0.004))
    _key_loc(cam, TIP_HOLD, _eye(fork, 0.096, 0.014, 0.004))
    _key_loc(cam, RHIZOME_AT, _eye(rhizome, 0.13, 0.004))
    _key_loc(cam, END, _eye(rhizome, 0.145, 0.003))
    cam.data.lens = 50
    _bezier(aim)
    _bezier(cam)
    print("lesson camera holds trident, vein, rhizome")
