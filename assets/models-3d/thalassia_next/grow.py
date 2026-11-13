"""Growth keys. Frame 300 is the full patch. Frame 330 matches frame 1."""

import math

import bpy
from mathutils import Euler, Vector

from thalassia_next.layout import NODES, SEGMENTS, root_window, shoot_window

_HOLD = 316


def _smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def _opened(frame):
    return 1 if frame == 330 else frame


def _span(frame, start, end, idle):
    frame = _opened(frame)
    if end <= start:
        return 1.0 if frame >= end else idle
    if frame < start:
        return idle
    if frame >= end:
        return 1.0
    t = _smooth((frame - start) / float(end - start))
    return idle + (1.0 - idle) * t


def _sway(frame, phase):
    frame = _opened(frame)
    frame = min(frame, _HOLD)
    return 0.05 * math.sin(2.0 * math.pi * (frame - 1) / 66.0 + phase)


def node_positions(frame):
    current = {0: Vector(NODES[0])}
    for parent, child, start, end, idle in SEGMENTS:
        grown = _span(frame, start, end, idle)
        current[child] = current[parent] + (Vector(NODES[child]) - Vector(NODES[parent])) * grown
    return current


def _local_delta(matrix_local, rest_head, head_now):
    delta = Vector(head_now) - Vector(rest_head)
    return matrix_local.to_3x3().inverted() @ delta


def pose_channels(frame, parts):
    """Return name -> (location, euler, scale) for every bone, including base."""
    nodes = node_positions(frame)
    out = {"base": (Vector((0.0, 0.0, 0.0)), Euler((0.0, 0.0, 0.0), "XYZ"), Vector((1.0, 1.0, 1.0)))}
    for part in parts:
        kind = part["kind"]
        if kind == "rhizome":
            parent, _child, start, end, idle = SEGMENTS[part["seg"]]
            grown = _span(frame, start, end, idle)
            head_now = nodes[parent]
            rot = Euler((0.0, 0.0, 0.0), "XYZ")
        elif kind == "shoot":
            start, end, _leaf_end, idle, _leaf_idle = shoot_window(part["node"])
            grown = _span(frame, start, end, idle)
            head_now = nodes[part["node"]]
            rot = Euler((_sway(frame, part["phase"]) * 0.25, 0.0, 0.0), "XYZ")
        elif kind == "leaf":
            start, stem_end, leaf_end, stem_idle, leaf_idle = shoot_window(part["node"])
            stem = _span(frame, start, stem_end, stem_idle)
            grown = _span(frame, start, leaf_end, leaf_idle)
            rest_node = Vector(NODES[part["node"]])
            head_now = Vector(part["rest_head"]) + (nodes[part["node"]] - rest_node)
            head_now.z += part["stem_h"] * (stem - 1.0)
            fold = 0.9 * (1.0 - grown) / (1.0 - leaf_idle)
            sway = _sway(frame, part["phase"])
            rot = Euler((fold + sway, 0.0, sway * 0.35), "XYZ")
        elif kind == "spread":
            start, spread_end, _drop_end = root_window(part["node"])
            grown = _span(frame, start, spread_end, 0.02)
            head_now = nodes[part["node"]]
            rot = Euler((0.0, 0.0, 0.0), "XYZ")
        elif kind == "drop":
            start, spread_end, drop_end = root_window(part["node"])
            spread = _span(frame, start, spread_end, 0.02)
            grown = _span(frame, start + 16, drop_end, 0.02)
            rest_node = Vector(NODES[part["node"]])
            head_now = Vector(part["rest_head"]) + (nodes[part["node"]] - rest_node)
            head_now += part["run"] * (spread - 1.0)
            rot = Euler((0.0, 0.0, 0.0), "XYZ")
        else:
            raise KeyError(kind)
        loc = _local_delta(part["matrix"], part["rest_head"], head_now)
        scale = Vector((1.0, max(0.02, grown), 1.0))
        out[part["name"]] = (loc, rot, scale)
    return out


def key_grow(arm, parts):
    bpy.context.view_layer.objects.active = arm
    if bpy.context.object.mode != "POSE":
        bpy.ops.object.mode_set(mode="POSE")
    arm.animation_data_create()
    action = bpy.data.actions.new("Grow")
    arm.animation_data.action = action
    if hasattr(action, "slots") and hasattr(arm.animation_data, "action_slot"):
        if arm.animation_data.action_slot is None and len(action.slots) == 0:
            action.slots.new("OBJECT", arm.name)
        if len(action.slots):
            arm.animation_data.action_slot = action.slots[0]
    frames = list(range(1, _HOLD + 1, 5))
    if frames[-1] != _HOLD:
        frames.append(_HOLD)
    frames.append(330)
    for index, frame in enumerate(frames):
        if index % 15 == 0:
            print(f"key {frame}")
        channels = pose_channels(frame, parts)
        for pb in arm.pose.bones:
            loc, rot, scale = channels[pb.name]
            pb.location = loc
            pb.rotation_euler = rot
            pb.scale = scale
            pb.keyframe_insert("location", frame=frame)
            pb.keyframe_insert("rotation_euler", frame=frame)
            pb.keyframe_insert("scale", frame=frame)
    _set_interpolation(action)
    return action


def _fcurves(action):
    found = []
    for layer in getattr(action, "layers", []):
        for strip in layer.strips:
            for bag in strip.channelbags:
                found.extend(bag.fcurves)
    if not found and getattr(action, "fcurves", None):
        found.extend(action.fcurves)
    return found


def _set_interpolation(action):
    curves = _fcurves(action)
    if not curves:
        raise RuntimeError("Grow has no fcurves")
    for fcurve in curves:
        for key in fcurve.keyframe_points:
            if abs(key.co[0] - _HOLD) < 0.1:
                key.interpolation = "CONSTANT"
            else:
                key.interpolation = "LINEAR"
        fcurve.update()
