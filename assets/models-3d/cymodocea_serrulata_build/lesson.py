"""Lesson camera for Cymodocea serrulata.

The meadow is already grown. The camera stays at one distance and one lens.
It only shifts its aim from the tip to the sheath, the scar, and the patch.
It does not zoom. Subtitles are burned on later. There is no floating 3D text.
"""

import json
import os

import bpy
from mathutils import Vector

from .util import collection, link, tag

END = 900
BUD_END = 120
CREEP_END = 330
ROOT_END = 510
SHOOT_END = 750

TIMING = r"d:\pepot\marinesee\assets\models-3d\cymodocea_serrulata\lesson_timing.json"


def _load_cues():
    if not os.path.isfile(TIMING):
        return []
    with open(TIMING, encoding="utf-8-sig") as handle:
        return json.load(handle).get("cues") or []


def _at(cues, cid, fallback):
    for cue in cues:
        if cue.get("id") == cid:
            return max(1, int(round(float(cue["start"]) * 30.0)) + 1)
    return fallback


def _action(arm):
    from .grow import _clock

    _clock["at"] = lambda frame: int(frame)
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
    """Hold the open meadow. The phone file is the one that plays Grow from the bud."""
    from .grow import _key, _polish

    action = _action(arm)
    for pb in arm.pose.bones:
        if pb.name == "base":
            continue
        _key(pb, 1, scale=1.0, rot=(0.0, 0.0, 0.0), loc=(0.0, 0.0, 0.0))
        _key(pb, END, scale=1.0, rot=(0.0, 0.0, 0.0), loc=(0.0, 0.0, 0.0))
    _polish(action, END)
    action.use_frame_range = True
    action.frame_start = 1
    action.frame_end = END
    bpy.context.scene.frame_end = END
    return action


def _hero():
    from .config import CONFIG
    from .rig import shoot_axes

    emp = bpy.data.objects["CS_Shoot_00"]
    origin, stem, _side, _fwd = shoot_axes(emp)
    height = float(CONFIG["stem_height_m"])
    best = None
    best_len = -1.0
    for obj in bpy.data.objects:
        if obj.type != "CURVE" or not obj.name.startswith("CS_Leaf_00_"):
            continue
        pts = obj.data.splines[0].bezier_points
        a = obj.matrix_world @ pts[0].co
        b = obj.matrix_world @ pts[-1].co
        length = (b - a).length
        if length > best_len:
            best_len = length
            best = obj
    pts = best.data.splines[0].bezier_points
    world = best.matrix_world
    mid = world @ pts[2].co
    end = world @ pts[-1].co
    return {
        "strap": mid.lerp(end, 0.35),
        "tip": mid.lerp(end, 0.78),
        "sheath": origin + stem * (height * 0.78) + Vector((0.0, -0.004, 0.0)),
        "scar": origin + stem * (height * 0.20) + Vector((0.0, -0.002, 0.0)),
    }


def _center():
    pts = [
        obj.matrix_world.translation.copy()
        for obj in bpy.data.objects
        if obj.name.startswith("CS_Shoot_")
    ]
    return sum(pts, Vector()) / len(pts)


def _eye(aim, dist, lift, xoff):
    return Vector((aim.x + xoff, aim.y - dist, aim.z + lift))


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


def frame_camera(cam):
    """Teach the tip, the sheath, the open scar, then the patch. No zoom."""
    cues = _load_cues()
    hero = _hero()
    center = _center()
    col = collection("Reef")
    previous = bpy.data.objects.get("CS_LessonAim")
    if previous is not None:
        bpy.data.objects.remove(previous, do_unlink=True)
    aim = bpy.data.objects.new("CS_LessonAim", None)
    link(aim, col)
    kinds = [item.identifier for item in aim.bl_rna.properties["empty_display_type"].enum_items]
    if "PLAIN_AXES" in kinds:
        aim.empty_display_type = "PLAIN_AXES"
    aim.empty_display_size = 0.01
    tag(aim)
    for obj in (aim, cam, cam.data):
        if obj.animation_data:
            obj.animation_data_clear()
    for name in ("CameraAction", "CS_LessonAimAction"):
        old = bpy.data.actions.get(name)
        if old is not None:
            bpy.data.actions.remove(old)

    wide = center + Vector((0.0, 0.0, 0.012))
    # One distance and one lens. The old list stepped from 4 cm to 50 cm
    # and from 38 mm to 82 mm, so the film zoomed on every sentence.
    dist = 0.32
    lens = 50
    shots = (
        ("name", hero["strap"], dist, 0.04, 0.0, lens),
        ("display", hero["strap"], dist, 0.04, 0.0, lens),
        ("strap", hero["strap"], dist, 0.04, 0.0, lens),
        ("eye", hero["tip"], dist, 0.045, 0.0, lens),
        ("serrated", hero["tip"], dist, 0.045, 0.0, lens),
        ("sheath", hero["sheath"], dist, 0.035, 0.0, lens),
        ("stem", hero["scar"], dist, 0.03, 0.0, lens),
        ("scars", hero["scar"], dist, 0.03, 0.0, lens),
        ("separate", hero["scar"], dist, 0.03, 0.0, lens),
        ("patch", wide, dist, 0.05, 0.0, lens),
        ("roots", wide, dist, 0.05, 0.0, lens),
        ("seed", wide, dist, 0.05, 0.0, lens),
    )
    fallback = {
        "name": 1,
        "display": 80,
        "strap": 150,
        "eye": 230,
        "serrated": 290,
        "sheath": 370,
        "stem": 440,
        "scars": 500,
        "separate": 580,
        "patch": 690,
        "roots": 780,
        "seed": 850,
    }
    keys = []
    last = 0
    for cid, point, dist, lift, xoff, lens in shots:
        frame = _at(cues, cid, fallback[cid])
        if frame <= last:
            frame = last + 1
        last = frame
        keys.append((frame, point, dist, lift, xoff, lens))
    end_point, end_dist, end_lift, end_x, end_lens = keys[-1][1:]
    if keys[-1][0] < END:
        keys.append((END, end_point, end_dist, end_lift, end_x, end_lens))

    track = cam.constraints.new("TRACK_TO")
    track.target = aim
    axes = [item.identifier for item in track.bl_rna.properties["track_axis"].enum_items]
    ups = [item.identifier for item in track.bl_rna.properties["up_axis"].enum_items]
    if "TRACK_NEGATIVE_Z" in axes:
        track.track_axis = "TRACK_NEGATIVE_Z"
    if "UP_Y" in ups:
        track.up_axis = "UP_Y"

    for frame, point, dist, lift, xoff, lens in keys:
        _key_loc(aim, frame, point)
        _key_loc(cam, frame, _eye(point, dist, lift, xoff))
        cam.data.lens = lens
        cam.data.keyframe_insert(data_path="lens", frame=frame)
    _bezier(aim)
    _bezier(cam)
    print("lesson camera", len(keys), "keys")
