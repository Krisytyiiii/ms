"""Lesson growth and a close camera looking down on the pairs.

Thirty seconds at 30 fps. The first pairs are already open. The buried
stem and the later pairs come in when the script reaches them. The camera
stays close. It does not pull back to a line, and it does not orbit.
"""

import json
import os

import bpy
from mathutils import Vector

from .util import collection, link, smoothstep, tag

END = 900
EARLY = 3
TIMINGS = r"C:\Users\reaga\AppData\Local\Temp\hm_minor_speech\timings.json"
TUCK = Vector((0.0, 0.0, -0.010))


def _frame_at(text, default_s):
    if os.path.isfile(TIMINGS):
        with open(TIMINGS, encoding="utf-8") as handle:
            data = json.load(handle)
        for row in data.get("sentences", []):
            if row.get("text", "").startswith(text):
                return max(1, min(END - 1, int(round(float(row["start"]) * 30))))
    return max(1, min(END - 1, int(round(default_s * 30))))


def beats():
    """Camera and growth marks, lined up with the spoken sentences."""
    pairs = _frame_at("The leaves come up", 7.0)
    veins = _frame_at("The cross veins", 16.0)
    spread = _frame_at("The patch spreads", 22.0)
    roots = _frame_at("Roots grow down", 25.0)
    veins = max(veins, pairs + 24)
    spread = max(spread, veins + 24)
    roots = max(roots, spread + 12)
    return pairs, veins, spread, roots


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


def _rh_scale(k, frame, nseg, spread):
    """The first two internodes stay put. The rest lengthen with the last idea."""
    from .config import CONFIG

    tiny = CONFIG["min_bone_scale"]
    if k <= 1:
        return 1.0
    span = max(1, nseg - 2)
    slot = k - 2
    step = max(14, (END - 30 - spread) // span)
    t0 = spread + slot * step
    t1 = min(END - 12, t0 + max(28, step))
    if frame <= t0:
        return tiny
    if frame >= t1:
        return 1.0
    u = smoothstep((frame - t0) / float(t1 - t0))
    return tiny + (1.0 - tiny) * u


def _offset(node_index, frame, chords, nseg, spread):
    off = Vector()
    for k in range(min(node_index, nseg)):
        off += chords[k] * (_rh_scale(k, frame, nseg, spread) - 1.0)
    return off


def _shoot_span(i, pairs, spread, nseg):
    if i == 0:
        return 1, 1
    if i < EARLY:
        t0 = pairs + (i - 1) * 28
        return t0, min(spread - 8, t0 + 64)
    t0 = spread + max(0, i - EARLY) * 18
    return t0, min(END - 16, t0 + 56)


def _reveal(obj, show, end):
    from .grow import _constant_hide

    if obj.animation_data:
        obj.animation_data_clear()
    obj.hide_render = True
    obj.keyframe_insert("hide_render", frame=1)
    if show > 2:
        obj.keyframe_insert("hide_render", frame=show - 1)
    obj.hide_render = False
    obj.keyframe_insert("hide_render", frame=max(1, show))
    obj.keyframe_insert("hide_render", frame=end)
    _constant_hide(obj)


def conceal_waiting(count, pairs, spread, nseg):
    """Keep later pairs out of the picture until their node is in place."""
    for i in range(count):
        t0, _t1 = _shoot_span(i, pairs, spread, nseg)
        if i == 0:
            continue
        prefix = "%02d" % i
        for obj in bpy.data.objects:
            name = obj.name
            if name.startswith("Shoot_" + prefix) or name.startswith("Leaf_" + prefix + "_") or name.startswith("Root_" + prefix + "_"):
                _reveal(obj, t0, END)


def animate(arm, cfg, conceal=True):
    from .grow import _fold, _key, _local, _polish

    tiny = cfg["min_bone_scale"]
    pairs, _veins, spread, roots = beats()
    action = _action(arm)
    bones = arm.data.bones
    rh = _names(arm, "rhizome_")
    nseg = len(rh)
    chords = [bones[name].tail_local - bones[name].head_local for name in rh]
    marks = [1, 18, pairs, spread, roots, END]
    for k in range(nseg):
        t0 = spread + max(0, k - 2) * 18
        marks.extend((t0, min(END - 12, t0 + 56)))
    rh_frames = sorted(set(frame for frame in marks if 1 <= frame <= END))
    for i, name in enumerate(rh):
        pb = arm.pose.bones[name]
        for frame in rh_frames:
            scale = _rh_scale(i, frame, nseg, spread)
            off = _offset(i, frame, chords, nseg, spread)
            _key(pb, frame, scale=scale, loc=_local(bones[name], off))

    shoots = _names(arm, "shoot_")
    for name in shoots:
        i = int(name.split("_")[1])
        sb = bones[name]
        t0, t1 = _shoot_span(i, pairs, spread, nseg)
        stem = (sb.tail_local - sb.head_local).normalized()

        def stem_state(frame, i=i, t0=t0, t1=t1):
            off = _offset(i, frame, chords, nseg, spread)
            if i == 0 or frame >= t1:
                return 1.0, off
            if frame <= t0:
                return tiny, off + TUCK
            u = smoothstep((frame - t0) / float(max(1, t1 - t0)))
            return tiny + (1.0 - tiny) * u, off + TUCK * (1.0 - u)

        frames = sorted(set([1, t0, (t0 + t1) // 2, t1, spread, END]))
        for frame in frames:
            sv, sloc = stem_state(frame)
            _key(arm.pose.bones[name], frame, scale=sv, loc=_local(sb, sloc))
        for leaf in _names(arm, "leaf_%02d_" % i):
            pb, lb = arm.pose.bones[leaf], bones[leaf]
            folded, opened = _fold(lb, stem), (0.0, 0.0, 0.0)
            for frame in frames:
                sv, sloc = stem_state(frame)
                if i == 0 or frame >= t1:
                    u_open = 1.0
                    sy = 1.0
                elif frame <= t0:
                    u_open = 0.0
                    sy = tiny
                else:
                    u_open = smoothstep((frame - t0) / float(max(1, t1 - t0)))
                    sy = tiny + (1.0 - tiny) * u_open
                _key(pb, frame, scale=sy, rot=_mix_tuple(folded, opened, u_open), loc=_local(lb, sloc))
        for r_i, root in enumerate(_names(arm, "root_%02d_" % i)):
            rb = bones[root]
            r0 = roots + (i % 4) * 4 + r_i * 6
            r1 = min(END - 8, r0 + 50)
            r_frames = sorted(set([1, r0, (r0 + r1) // 2, r1, END]))
            for frame in r_frames:
                off = _offset(i, frame, chords, nseg, spread)
                if frame >= r1:
                    sy = 1.0
                elif frame <= r0:
                    sy = tiny
                else:
                    u = smoothstep((frame - r0) / float(max(1, r1 - r0)))
                    sy = tiny + (1.0 - tiny) * u
                _key(arm.pose.bones[root], frame, scale=sy, loc=_local(rb, off))

    if conceal:
        conceal_waiting(len(shoots), pairs, spread, nseg)
        for obj in bpy.data.objects:
            if obj.name.startswith("Root_"):
                _reveal(obj, roots, END)
    _polish(action, END)
    action.use_frame_range = True
    action.frame_start = 1
    action.frame_end = END
    bpy.context.scene.frame_end = END
    print("lesson beats", "pairs", pairs, "veins", _veins, "spread", spread, "roots", roots)
    return action


def _mix_tuple(a, b, t):
    from .grow import _mix

    return _mix(a, b, t)


def _nodes():
    empties = sorted(
        (obj for obj in bpy.data.objects if obj.name.startswith("HM_Shoot_")),
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


def _eye(aim, front, height):
    return Vector((aim.x, aim.y - front, aim.z + height))


def frame_camera(cam):
    """Look down on the ovals. Stay close enough that the patch is not one line."""
    nodes = _nodes()
    if not nodes:
        return
    pairs, veins, spread, roots = beats()
    col = collection("Reef")
    previous = bpy.data.objects.get("HM_LessonAim")
    if previous is not None:
        bpy.data.objects.remove(previous, do_unlink=True)
    aim = bpy.data.objects.new("HM_LessonAim", None)
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

    emp = bpy.data.objects["HM_Shoot_00"]
    origin = emp.matrix_world.translation.copy()
    right = emp.matrix_world.col[0].xyz.normalized()
    pair = origin + Vector((0.0, 0.0, 0.008))
    vein = origin + right * 0.014 + Vector((0.0, 0.001, 0.005))
    early = sum(nodes[:EARLY], Vector()) / float(EARLY) + Vector((0.0, 0.0, 0.008))
    center = sum(nodes, Vector()) / len(nodes) + Vector((0.0, -0.006, 0.004))

    # Front distance, then height. Low enough to see the cut, close enough that the ovals stay large.
    shots = [
        (1, pair, 0.052, 0.040),
        (pairs, pair, 0.056, 0.044),
        (pairs + 36, early, 0.078, 0.050),
        (veins, vein, 0.030, 0.026),
        (max(veins + 24, spread - 16), vein, 0.032, 0.028),
        (spread + 6, center + Vector((0.0, -0.014, -0.008)), 0.100, 0.048),
        (roots, center + Vector((0.0, -0.020, -0.012)), 0.088, 0.038),
        (END, center + Vector((0.0, -0.012, -0.006)), 0.110, 0.052),
    ]
    ordered = []
    for frame, point, front, height in shots:
        frame = max(1, min(END, int(frame)))
        if ordered and frame <= ordered[-1][0]:
            frame = min(END, ordered[-1][0] + 1)
        ordered.append((frame, point, front, height))
        if frame == END:
            break

    for frame, point, _front, _height in ordered:
        _key_loc(aim, frame, point)

    track = cam.constraints.new("TRACK_TO")
    track.target = aim
    axes = [item.identifier for item in track.bl_rna.properties["track_axis"].enum_items]
    ups = [item.identifier for item in track.bl_rna.properties["up_axis"].enum_items]
    if "TRACK_NEGATIVE_Z" in axes:
        track.track_axis = "TRACK_NEGATIVE_Z"
    if "UP_Y" in ups:
        track.up_axis = "UP_Y"

    for frame, point, front, height in ordered:
        _key_loc(cam, frame, _eye(point, front, height))
    cam.data.lens = 50
    _bezier(aim)
    _bezier(cam)
    print("lesson camera", len(nodes), "nodes, lens", cam.data.lens)
