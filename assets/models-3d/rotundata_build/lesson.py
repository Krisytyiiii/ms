"""Lesson growth and the explainer camera. Thirty seconds at 30 fps.

The first shoot opens during the introduction. The camera then sits on a
rounded leaf tip, then on the closed scar ring, then eases back while the
rhizome sends up the rest of the patch. No camera is exported in the phone file.
"""

import json
import os

import bpy
from mathutils import Vector

from .util import collection, link, smoothstep, tag

END = 900
# Kept so an older card module can still import. The lesson does not draw those cards.
BUD_END, CREEP_END, ROOT_END, SHOOT_END = 180, 420, 560, 780
SPEECH = r"d:\pepot\marinesee\assets\models-3d\cymodocea_rotundata\speech\lesson_speech.json"
TUCK = Vector((0.0, 0.0, -0.014))


def _beats():
    data = {"intro_end": 6.5, "tip_end": 13.5, "ring_end": 21.5, "duration": 29.0}
    if os.path.isfile(SPEECH):
        with open(SPEECH, encoding="utf-8-sig") as handle:
            data.update(json.load(handle))

    def frame_at(sec):
        return max(24, min(END - 30, int(round(float(sec) * 30)) + 1))

    return {
        "intro": frame_at(data["intro_end"]),
        "tip": frame_at(data["tip_end"]),
        "ring": frame_at(data["ring_end"]),
        "end": END,
    }


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


def _mix_tuple(a, b, t):
    from .grow import _mix

    return _mix(a, b, t)


def _linear(action):
    from .grow import fcurves

    if action is None:
        return
    for fc in fcurves(action):
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"
        fc.update()


def animate(arm, cfg):
    from .grow import _fold, _key, _local

    beats = _beats()
    tiny = cfg["min_bone_scale"]
    intro, tip, ring, end = beats["intro"], beats["tip"], beats["ring"], beats["end"]
    open_done = max(36, intro - 8)
    full = min(end - 20, ring + int(0.72 * (end - ring)))
    action = _action(arm)
    bones = arm.data.bones
    rh = _names(arm, "rhizome_")
    nseg = max(1, len(rh))
    chords = [bones[name].tail_local - bones[name].head_local for name in rh]

    def seg_scale(i, frame):
        if i == 0:
            if frame >= open_done:
                return 1.0
            u = smoothstep((frame - 1) / float(max(1, open_done - 1)))
            return 0.62 + 0.38 * u
        span = max(1, nseg - 1)
        slot = (full - ring) / float(span)
        start = ring + (i - 1) * slot * 0.62
        done = min(full, start + max(28.0, slot))
        if frame <= start:
            return tiny
        if frame >= done:
            return 1.0
        u = smoothstep((frame - start) / float(max(1.0, done - start)))
        return tiny + (1.0 - tiny) * u

    marks = [1, 30, open_done, intro, tip, ring, full, end]
    for i in range(1, nseg):
        span = max(1, nseg - 1)
        slot = (full - ring) / float(span)
        start = ring + (i - 1) * slot * 0.62
        done = min(full, start + max(28.0, slot))
        marks.extend((int(start), int((start + done) / 2), int(done)))
    frames = sorted(set(m for m in marks if 1 <= int(m) <= end))

    for i, name in enumerate(rh):
        pb = arm.pose.bones[name]
        for frame in frames:
            off = Vector()
            for k in range(i):
                off += chords[k] * (seg_scale(k, frame) - 1.0)
            _key(pb, frame, scale=seg_scale(i, frame), loc=_local(bones[name], off))

    shoots = _names(arm, "shoot_")
    count = len(shoots)
    lift = cfg["stem_height_m"] * cfg["leaf_base_frac"] + 0.004 / (1.0 - tiny)

    def shoot_window(i):
        if i == 0:
            return 1, open_done
        others = max(1, count - 1)
        slot = (full - ring) / float(others)
        start = ring + (i - 1) * slot * 0.55
        done = min(full - 4, start + max(40.0, slot))
        return start, done

    def stem_state(i, frame):
        start, done = shoot_window(i)
        if i == 0:
            if frame >= done:
                return 1.0, Vector()
            u = smoothstep((frame - 1) / float(max(1, done - 1)))
            return 0.55 + 0.45 * u, Vector()
        if frame <= start:
            return tiny, TUCK
        if frame >= done:
            return 1.0, Vector()
        u = smoothstep((frame - start) / float(max(1.0, done - start)))
        return tiny + (1.0 - tiny) * u, TUCK * (1.0 - u)

    for name in shoots:
        i = int(name.split("_")[1])
        sb = bones[name]
        stem = (sb.tail_local - sb.head_local).normalized()
        start, done = shoot_window(i)
        stem_frames = sorted(set(frames + [int(start), int(done), int((start + done) / 2)]))
        for frame in stem_frames:
            sv, sloc = stem_state(i, frame)
            _key(arm.pose.bones[name], frame, scale=sv, loc=_local(sb, sloc))
        for leaf in _names(arm, "leaf_%02d_" % i):
            pb, lb = arm.pose.bones[leaf], bones[leaf]
            folded, opened = _fold(lb, stem), (0.0, 0.0, 0.0)
            for frame in stem_frames:
                sv, sloc = stem_state(i, frame)
                if i == 0:
                    u_open = 0.0 if frame <= 1 else smoothstep((frame - 1) / float(max(1, done - 1)))
                    sy = 0.30 + 0.70 * u_open
                else:
                    grown = 0.0 if sv <= tiny + 1e-4 else (sv - tiny) / (1.0 - tiny)
                    u_open = smoothstep(min(1.0, grown * 1.7))
                    sy = max(tiny, sv)
                world = sloc + stem * ((sv - 1.0) * lift)
                _key(pb, frame, scale=sy, rot=_mix_tuple(folded, opened, u_open), loc=_local(lb, world))
        for r_i, root in enumerate(_names(arm, "root_%02d_" % i)):
            rb = bones[root]
            if i == 0:
                r0, r1 = 20, min(open_done, 140)
            else:
                r0 = start + 6 + r_i * 4
                r1 = min(full, done + 12)
            root_frames = sorted(set([1, int(r0), int((r0 + r1) / 2), int(r1), full, end]))
            for frame in root_frames:
                if frame <= r0:
                    sy = tiny
                elif frame >= r1:
                    sy = 1.0
                else:
                    sy = tiny + (1.0 - tiny) * smoothstep((frame - r0) / float(max(1.0, r1 - r0)))
                _key(arm.pose.bones[root], frame, scale=sy, loc=_local(rb, Vector()))

    _linear(action)
    action.use_frame_range = True
    action.frame_start = 1
    action.frame_end = end
    bpy.context.scene.frame_end = end
    print("lesson grow", beats, "open", open_done, "full", full)
    return action


def _ctrl(obj):
    from .util import control_points

    return control_points(obj)


def _hero_tip():
    best = None
    best_len = -1.0
    for obj in bpy.data.objects:
        if not obj.name.startswith("CR_Leaf_00_"):
            continue
        pts = _ctrl(obj)
        length = sum((b - a).length for a, b in zip(pts, pts[1:]))
        if length > best_len:
            best_len = length
            best = pts
    tip = best[-1].copy()
    direction = (tip - best[-2]).normalized()
    return tip, direction


def _shoot_stem():
    emp = bpy.data.objects["CR_Shoot_00"]
    origin = emp.matrix_world.translation.copy()
    stem = emp.matrix_world.col[2].xyz.normalized()
    return origin, stem


def _key_loc(obj, frame, point):
    obj.location = point
    obj.keyframe_insert("location", frame=frame)


def _lens(cam, frame, value):
    cam.data.lens = value
    cam.data.keyframe_insert(data_path="lens", frame=frame)


def frame_camera(cam):
    """Close on the rounded tip, then the closed scar ring, then the whole patch."""
    beats = _beats()
    intro, tip, ring, end = beats["intro"], beats["tip"], beats["ring"], beats["end"]
    col = collection("Reef")
    previous = bpy.data.objects.get("CR_LessonAim")
    if previous is not None:
        bpy.data.objects.remove(previous, do_unlink=True)
    aim = bpy.data.objects.new("CR_LessonAim", None)
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

    origin, stem = _shoot_stem()
    from .config import CONFIG

    height = CONFIG["stem_height_m"]
    leaf_tip, leaf_dir = _hero_tip()
    tip_aim = leaf_tip - leaf_dir * 0.004
    right = bpy.data.objects["CR_Shoot_00"].matrix_world.col[0].xyz.normalized()
    face_n = leaf_dir.cross(right)
    if face_n.length < 1e-6:
        face_n = Vector((0.0, -1.0, 0.0))
    else:
        face_n.normalize()
    if face_n.y > 0.0:
        face_n = -face_n
    scar_aim = origin + stem * (0.34 * height)
    nodes = [obj.matrix_world.translation.copy() for obj in sorted(
        (o for o in bpy.data.objects if o.name.startswith("CR_Shoot_")),
        key=lambda o: o.name,
    )]
    center = sum(nodes, Vector()) / len(nodes)
    wide_aim = center + Vector((0.0, -0.006, 0.055))
    root_aim = origin + Vector((0.03, -0.004, 0.012))

    def eye(point, back, lift, side=0.0):
        return point + Vector((side, -back, lift))

    intro_aim = origin + stem * 0.07
    intro_eye = eye(intro_aim, 0.28, 0.045, 0.012)
    tip_eye = tip_aim + face_n * 0.062 + Vector((0.0, 0.0, 0.008))
    scar_eye = eye(scar_aim, 0.105, 0.006, 0.016)
    root_eye = eye(root_aim, 0.30, 0.055, 0.02)
    wide_eye = eye(wide_aim, 0.48, 0.10, 0.015)

    move = 12

    def hold(frame, point, loc, lens):
        _key_loc(aim, frame, point)
        _key_loc(cam, frame, loc)
        _lens(cam, frame, lens)

    hold(1, intro_aim, intro_eye, 50)
    hold(max(2, intro - move), intro_aim, intro_eye, 50)
    hold(intro, tip_aim, tip_eye, 85)
    hold(max(intro + 1, tip - move), tip_aim, tip_eye, 85)
    hold(tip, scar_aim, scar_eye, 70)
    hold(max(tip + 1, ring - move), scar_aim, scar_eye, 70)
    hold(ring, root_aim, root_eye, 50)
    spread_mid = ring + max(move + 1, int(0.45 * (end - ring)))
    hold(spread_mid, wide_aim, wide_eye, 50)
    hold(end, wide_aim, wide_eye, 50)

    track = cam.constraints.new("TRACK_TO")
    track.target = aim
    axes = [item.identifier for item in track.bl_rna.properties["track_axis"].enum_items]
    ups = [item.identifier for item in track.bl_rna.properties["up_axis"].enum_items]
    if "TRACK_NEGATIVE_Z" in axes:
        track.track_axis = "TRACK_NEGATIVE_Z"
    if "UP_Y" in ups:
        track.up_axis = "UP_Y"
    _linear(aim.animation_data.action if aim.animation_data else None)
    _linear(cam.animation_data.action if cam.animation_data else None)
    data_action = cam.data.animation_data.action if cam.data.animation_data else None
    _linear(data_action)
    print("lesson camera tip", tuple(round(v, 4) for v in tip_aim), "scar", tuple(round(v, 4) for v in scar_aim))
