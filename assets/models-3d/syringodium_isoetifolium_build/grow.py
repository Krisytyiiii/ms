"""Grow on SI_Armature, frames 1-330.

The clip opens on the stand. Leaves lengthen a little, then settle.
Frame 330 matches frame 1 so the phone loop has no jump.
Scale is Y only, so a leaf stays round while it grows.
"""

import math

import bpy
from mathutils import Euler, Vector

from .config import CONFIG


def _names(arm, prefix):
    return sorted(name for name in arm.pose.bones.keys() if name.startswith(prefix))


def _key(pb, frame, scale, loc, rot=None):
    pb.scale = (1.0, float(scale), 1.0)
    pb.keyframe_insert(data_path="scale", frame=frame)
    pb.location = loc
    pb.keyframe_insert(data_path="location", frame=frame)
    if rot is not None:
        pb.rotation_euler = Euler(rot, "XYZ")
        pb.keyframe_insert(data_path="rotation_euler", frame=frame)


def _local(bone, offset):
    return bone.matrix_local.to_3x3().transposed() @ offset


def fcurves(action):
    out = []
    if not hasattr(action, "layers"):
        return list(getattr(action, "fcurves", []) or [])
    for layer in action.layers:
        for strip in layer.strips:
            for slot in action.slots:
                bag = strip.channelbag(slot)
                if bag is not None:
                    out.extend(bag.fcurves)
    return out


def _envelope(frame):
    """0.80 at the loop ends, full length through the middle."""
    if frame <= 1 or frame >= 330:
        return 0.80
    if frame < 120:
        u = (frame - 1) / 119.0
        u = u * u * (3.0 - 2.0 * u)
        return 0.80 + 0.20 * u
    if frame <= 240:
        return 1.0
    u = (frame - 240) / 90.0
    u = max(0.0, min(1.0, u))
    u = u * u * (3.0 - 2.0 * u)
    return 1.0 - 0.20 * u


def _sway(frame, phase):
    cycle = (int(frame) - 1) % 329
    ang = 2.0 * math.pi * cycle / 329.0
    w = 0.010 * math.sin(ang * 2.0 + phase)
    return (w, 0.0, 0.006 * math.sin(ang * 2.0 + phase + 0.8))


def _linear(action):
    for fc in fcurves(action):
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"
        fc.update()


def animate(arm, cfg=CONFIG):
    end = 330
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

    bpy.context.view_layer.objects.active = arm
    if bpy.context.object and bpy.context.object.mode != "POSE":
        bpy.ops.object.mode_set(mode="POSE")

    bones = arm.data.bones
    rh = _names(arm, "rhizome_")
    nseg = len(rh)
    chords = [bones[name].tail_local - bones[name].head_local for name in rh]
    shoots = _names(arm, "shoot_")
    lift = cfg["stem_height_m"] * cfg["leaf_base_frac"]
    frames = list(range(1, end, 10)) + [120, 240, end]

    def node_offset(i, scale):
        off = Vector((0.0, 0.0, 0.0))
        for k in range(min(i, nseg)):
            off += chords[k] * (scale - 1.0)
        return off

    for frame in frames:
        scale = _envelope(frame)
        for i, name in enumerate(rh):
            pb = arm.pose.bones[name]
            _key(pb, frame, scale, _local(bones[name], node_offset(i, scale)))
        for name in shoots:
            i = int(name.split("_")[1])
            sb = bones[name]
            stem = (sb.tail_local - sb.head_local)
            stem = stem.normalized() if stem.length else Vector((0.0, 0.0, 1.0))
            off = node_offset(i, scale)
            _key(arm.pose.bones[name], frame, scale, _local(sb, off))
            leaf_off = off + stem * (lift * (scale - 1.0))
            for j, leaf in enumerate(_names(arm, "leaf_%02d_" % i)):
                lb = bones[leaf]
                phase = i * 0.4 + j * 0.7
                _key(arm.pose.bones[leaf], frame, scale, _local(lb, leaf_off), _sway(frame, phase))
            for root in _names(arm, "root_%02d_" % i):
                rb = bones[root]
                _key(arm.pose.bones[root], frame, scale, _local(rb, off))

    _linear(action)
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    print("grow keys", len(fcurves(action)))
    action.use_frame_range = True
    action.frame_start = 1
    action.frame_end = end
    bpy.context.scene.frame_end = end
    bpy.context.scene.frame_start = 1
    return action
