"""Lesson growth and the explainer camera. Thirty seconds at 30 fps.

Side angle so the sickle reads, then a close pass on the black bars,
then the thick rhizome and the roots in the cut. No orbit.
"""

import json
import os

import bpy
from mathutils import Vector

from .util import collection, dense_points, link, smoothstep, tag

MARKS_PATH = os.path.join(os.path.dirname(__file__), "speech_timing.json")
SPREAD_START = 540

# 30 seconds. Same five beats, half the original minute.
BUD_END = 120
CREEP_END = 330
ROOT_END = 510
SHOOT_END = 750
END = 900
BUD_OPEN = 100
TUCK = Vector((0.0, 0.0, -0.012))


def load_marks():
    """Frame numbers from the spoken lines. Defaults keep a build usable."""
    global BUD_OPEN, BUD_END, CREEP_END, ROOT_END, SHOOT_END, SPREAD_START, END
    seconds = {
        "intro": 0.4,
        "curve": 5.0,
        "curve_end": 8.5,
        "bars": 10.0,
        "tannin_end": 14.0,
        "rhizome": 15.0,
        "spread": 19.0,
        "roots": 23.0,
        "seed": 26.0,
    }
    if os.path.isfile(MARKS_PATH):
        with open(MARKS_PATH, encoding="utf-8") as handle:
            lines = json.load(handle)["lines"]

        def at(index, key):
            return float(lines[index][key])

        seconds = {
            "intro": at(0, "start"),
            "curve": at(2, "start"),
            "curve_end": at(2, "end"),
            "bars": at(3, "start"),
            "tannin_end": at(4, "end"),
            "rhizome": at(5, "start"),
            "spread": at(6, "start"),
            "roots": at(7, "start"),
            "seed": at(8, "start"),
        }

    def fr(t):
        return max(1, min(900, int(round(float(t) * 30.0)) + 1))

    frames = {key: fr(val) for key, val in seconds.items()}
    BUD_OPEN = max(36, frames["curve"] - 8)
    BUD_END = frames["curve"]
    CREEP_END = max(BUD_END + 20, frames["rhizome"])
    SPREAD_START = frames["spread"]
    ROOT_END = max(SPREAD_START + 12, frames["roots"])
    SHOOT_END = max(ROOT_END + 8, frames["seed"])
    END = 900
    frames["end"] = END
    print("LESSON_MARKS", frames)
    return frames


def _names(arm, prefix):
    return sorted(name for name in arm.pose.bones.keys() if name.startswith(prefix))


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


def _seg_scale(k, frame, windows, tiny):
    if frame <= windows[k]:
        return tiny
    if frame >= windows[k + 1]:
        return 1.0
    u = (frame - windows[k]) / max(1, windows[k + 1] - windows[k])
    return tiny + (1.0 - tiny) * u


def _bud(frame):
    if frame >= BUD_OPEN:
        return 1.0
    return 0.42 + 0.58 * smoothstep((frame - 1) / float(BUD_OPEN - 1))


def _rise(i, frame, tiny, count):
    """Later shoots stay tucked, then lengthen while the patch-spread line is spoken."""
    others = max(1, count - 1)
    room = max(48, (END - 30) - SPREAD_START)
    step = max(8, room // others)
    t0 = max(CREEP_END, SPREAD_START - 12) + (i - 1) * max(4, step // 2)
    t1 = min(END - 24, t0 + step)
    if frame <= t0:
        u = 0.0
    elif frame >= t1:
        u = 1.0
    else:
        u = smoothstep((frame - t0) / float(t1 - t0))
    return tiny + (1.0 - tiny) * u, TUCK * (1.0 - u), t0, t1


def _root_scale(frame, tiny, delay=0):
    start = 70 + delay
    if frame <= start:
        return tiny
    if frame >= ROOT_END:
        return 1.0
    return tiny + (1.0 - tiny) * smoothstep((frame - start) / float(max(1, ROOT_END - start)))


def animate(arm, cfg):
    from .grow import _fold, _key, _leaf_chains, _local, _local_euler, _polish, _world_quat

    load_marks()
    tiny = cfg["min_bone_scale"]
    action = _action(arm)
    bones = arm.data.bones
    rh = _names(arm, "rhizome_")
    nseg = len(rh)
    grow_from = 10
    windows = [grow_from + round((CREEP_END - grow_from) * k / max(1, nseg)) for k in range(nseg + 1)]
    chords = [bones[name].tail_local - bones[name].head_local for name in rh]
    rh_frames = sorted(set([1, BUD_END] + windows + [END]))
    for i, name in enumerate(rh):
        pb = arm.pose.bones[name]
        for frame in rh_frames:
            scale = _seg_scale(i, frame, windows, tiny)
            off = Vector()
            for k in range(i):
                off += chords[k] * (_seg_scale(k, frame, windows, tiny) - 1.0)
            _key(pb, frame, scale=scale, loc=_local(bones[name], off))

    shoots = _names(arm, "shoot_")
    lift = cfg["stem_height_m"] * cfg["leaf_base_frac"] + 0.004 / (1.0 - tiny)
    for name in shoots:
        i = int(name.split("_")[1])
        sb = bones[name]
        stem = (sb.tail_local - sb.head_local).normalized()
        if i == 0:
            stem_frames = [1, 40, 70, BUD_OPEN, BUD_END, END]
        else:
            _sy, _tuck, t0, t1 = _rise(i, 1, tiny, len(shoots))
            stem_frames = [1, t0, (t0 + t1) // 2, t1, END]
        for frame in stem_frames:
            if i == 0:
                sv, sloc = _bud(frame), Vector((0.0, 0.0, 0.0))
            else:
                sv, sloc, _t0, _t1 = _rise(i, frame, tiny, len(shoots))
            _key(arm.pose.bones[name], frame, scale=sv, loc=_local(sb, sloc))
        for _j, (leaf_key, chain) in enumerate(_leaf_chains(arm, i)):
            b0 = bones[chain[0]]
            folded, opened = _fold(b0, stem), (0.0, 0.0, 0.0)
            chords = [bones[nm].tail_local - bones[nm].head_local for nm in chain]
            for frame in stem_frames:
                if i == 0:
                    sv, sloc = _bud(frame), Vector((0.0, 0.0, 0.0))
                    u_open = 0.0 if frame <= 1 else smoothstep((frame - 1) / float(BUD_OPEN - 1))
                    sy = 0.20 + 0.80 * u_open
                else:
                    sv, sloc, _t0, _t1 = _rise(i, frame, tiny, len(shoots))
                    grown = 0.0 if sv <= tiny + 1e-4 else (sv - tiny) / (1.0 - tiny)
                    u_open = smoothstep(min(1.0, grown * 1.8))
                    sy = sv
                lift_world = sloc + stem * ((sv - 1.0) * lift)
                world_q = _world_quat(b0, _mix_tuple(folded, opened, u_open))
                gap = Vector()
                for seg, leaf in enumerate(chain):
                    pb, lb = arm.pose.bones[leaf], bones[leaf]
                    _key(pb, frame, scale=sy, rot=_local_euler(lb, world_q), loc=_local(lb, lift_world + gap))
                    gap += chords[seg] * (sy - 1.0)
        for r_i, root in enumerate(_names(arm, "root_%02d_" % i)):
            rb = bones[root]
            delay = (i % 5) * 4 + r_i * 6
            marks = (1, CREEP_END, CREEP_END + delay, (CREEP_END + delay + ROOT_END) // 2, ROOT_END, END)
            for frame in sorted(set(marks)):
                _key(arm.pose.bones[root], frame, scale=_root_scale(frame, tiny, delay), loc=_local(rb, Vector()))

    _polish(action, END)
    action.use_frame_range = True
    action.frame_start = 1
    action.frame_end = END
    bpy.context.scene.frame_end = END
    return action


def _mix_tuple(a, b, t):
    from .grow import _mix

    return _mix(a, b, t)


def _nodes():
    empties = sorted(
        (obj for obj in bpy.data.objects if obj.name.startswith("TH_Shoot_")),
        key=lambda obj: obj.name,
    )
    return [obj.matrix_world.translation.copy() for obj in empties]


def _along(nodes, u):
    u = max(0.0, min(1.0, u))
    if len(nodes) < 2:
        return nodes[0].copy()
    lengths = [(b - a).length for a, b in zip(nodes, nodes[1:])]
    total = sum(lengths) or 1.0
    want = u * total
    acc = 0.0
    for (a, b), length in zip(zip(nodes, nodes[1:]), lengths):
        if acc + length >= want - 1e-9:
            t = 0.0 if length < 1e-9 else (want - acc) / length
            return a.lerp(b, t)
        acc += length
    return nodes[-1].copy()


def _look(point, lift=0.055, side=-0.035):
    """Aim above and left of the subject so the upper-left card sits in open water."""
    return point + Vector((side, 0.0, lift))


def _eye(aim, dist, lift):
    return Vector((aim.x, aim.y - dist, aim.z + lift))


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


def _hero_blade():
    obj = bpy.data.objects.get("TH_Leaf_00_1") or bpy.data.objects.get("TH_Leaf_00_0")
    if obj is None:
        leaves = [item for item in bpy.data.objects if item.type == "CURVE" and item.name.startswith("TH_Leaf_")]
        obj = leaves[0]
    pts = dense_points(obj, 10)
    index = max(1, min(len(pts) - 2, int(len(pts) * 0.46)))
    mid = pts[index]
    plane = Vector((
        float(obj.get("cr_px", 0.0)),
        float(obj.get("cr_py", 1.0)),
        float(obj.get("cr_pz", 0.0)),
    ))
    if plane.length < 1e-6:
        plane = Vector((0.0, 1.0, 0.0))
    plane.normalize()
    return mid, plane


def _lens(cam, frame, mm):
    cam.data.lens = float(mm)
    cam.data.keyframe_insert(data_path="lens", frame=frame)


def frame_camera(cam):
    """Side view of the sickle, then a close pass across the black bars."""
    nodes = _nodes()
    if not nodes:
        return
    marks = load_marks()
    col = collection("Reef")
    previous = bpy.data.objects.get("TH_LessonAim")
    if previous is not None:
        bpy.data.objects.remove(previous, do_unlink=True)
    aim = bpy.data.objects.new("TH_LessonAim", None)
    link(aim, col)
    kinds = [item.identifier for item in aim.bl_rna.properties["empty_display_type"].enum_items]
    if "PLAIN_AXES" in kinds:
        aim.empty_display_type = "PLAIN_AXES"
    aim.empty_display_size = 0.01
    tag(aim)
    if aim.animation_data:
        aim.animation_data_clear()
    if cam.animation_data:
        cam.animation_data_clear()
    if cam.data.animation_data:
        cam.data.animation_data_clear()

    mid, plane = _hero_blade()
    # The cut and the viewer sit on the negative-Y side of the row.
    front = Vector((0.0, -1.0, 0.0))
    if plane.y > 0.0:
        front = -plane
    side_view = (front + Vector((-0.42, 0.0, 0.16))).normalized()
    face_view = (front * 1.4 + Vector((-0.08, 0.0, 0.03))).normalized()
    low_view = Vector((-0.22, -1.0, 0.05)).normalized()

    side_aim = mid + Vector((0.0, 0.0, -0.03))
    close_aim = mid + Vector((0.004, 0.0, 0.0))
    center = sum(nodes, Vector()) / len(nodes)
    rhiz_aim = _along(nodes, 0.35) + Vector((0.0, -0.004, -0.002))
    root_aim = nodes[0] + Vector((0.0, -0.006, -0.012))
    wide_aim = center + Vector((0.0, 0.0, 0.055))

    def place(frame, target, view, dist, mm):
        frame = max(1, min(END, int(frame)))
        _key_loc(aim, frame, target)
        _key_loc(cam, frame, target + view * dist)
        _lens(cam, frame, mm)

    place(1, side_aim, side_view, 0.58, 50)
    place(marks["curve"], side_aim, side_view, 0.50, 50)
    place(marks["curve_end"], side_aim + Vector((0.0, 0.0, 0.01)), side_view, 0.42, 52)
    place(marks["bars"], close_aim, face_view, 0.075, 68)
    place(max(marks["bars"] + 2, marks["tannin_end"]), close_aim, face_view, 0.068, 72)
    place(marks["rhizome"], rhiz_aim, low_view, 0.20, 50)
    place(marks["spread"], wide_aim + Vector((0.0, 0.0, -0.02)), side_view, 0.52, 48)
    place(marks["roots"], root_aim, low_view, 0.16, 52)
    place(marks["seed"], wide_aim, (side_view + Vector((0.0, -0.2, 0.08))).normalized(), 0.78, 48)
    place(END, wide_aim, (side_view + Vector((0.0, -0.15, 0.1))).normalized(), 0.86, 46)

    track = cam.constraints.new("TRACK_TO")
    track.target = aim
    axes = [item.identifier for item in track.bl_rna.properties["track_axis"].enum_items]
    ups = [item.identifier for item in track.bl_rna.properties["up_axis"].enum_items]
    if "TRACK_NEGATIVE_Z" in axes:
        track.track_axis = "TRACK_NEGATIVE_Z"
    if "UP_Y" in ups:
        track.up_axis = "UP_Y"
    cam.data.clip_start = 0.004
    _bezier(aim)
    _bezier(cam)
    if cam.data.animation_data:
        _bezier(cam.data)
    print("lesson camera", len(nodes), "nodes")
