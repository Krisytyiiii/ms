"""Lesson growth and the explainer camera. Thirty seconds at 30 fps.

One change at a time: a bud, the rhizome tip, one cut root, then shoots
rising in place. The camera stays on the front side and eases back.
It does not orbit. The phone is what the person rotates.
"""

import bpy
from mathutils import Vector

from .util import collection, link, smoothstep, tag

# 30 seconds. Same five beats, half the original minute.
BUD_END = 80
CREEP_END = 420
ROOT_END = 700
SHOOT_END = 820
END = 900
BUD_OPEN = 50
TUCK = Vector((0.0, 0.0, -0.012))


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
    """Shoot i (i > 0) lengthens while the patch spreads, after the first shoot is open."""
    others = max(1, count - 1)
    t_start, t_end = 300, 760
    room = max(40, t_end - t_start)
    step = max(4, room // others)
    t0 = t_start + (i - 1) * step
    t1 = min(t_end, t0 + min(80, room // 2))
    if frame <= t0:
        u = 0.0
    elif frame >= t1:
        u = 1.0
    else:
        u = smoothstep((frame - t0) / float(t1 - t0))
    return tiny + (1.0 - tiny) * u, TUCK * (1.0 - u), t0, t1


def _root_scale(frame, tiny, delay=0):
    start = CREEP_END + delay
    if frame <= start:
        return tiny
    if frame >= ROOT_END:
        return 1.0
    return tiny + (1.0 - tiny) * smoothstep((frame - start) / float(max(1, ROOT_END - start)))


def animate(arm, cfg):
    from .grow import _fold, _key, _local, _polish

    tiny = cfg["min_bone_scale"]
    action = _action(arm)
    bones = arm.data.bones
    rh = _names(arm, "rhizome_")
    nseg = len(rh)
    windows = [BUD_END + round((CREEP_END - BUD_END) * k / max(1, nseg)) for k in range(nseg + 1)]
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
        for j, leaf in enumerate(_names(arm, "leaf_%02d_" % i)):
            pb, lb = arm.pose.bones[leaf], bones[leaf]
            folded, opened = _fold(lb, stem), (0.0, 0.0, 0.0)
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
                world = sloc + stem * ((sv - 1.0) * lift)
                rot = _mix_tuple(folded, opened, u_open)
                _key(pb, frame, scale=sy, rot=rot, loc=_local(lb, world))
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
        (obj for obj in bpy.data.objects if obj.name.startswith("HP_Shoot_")),
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


def _hero_tip():
    """Tip of the mature shoot-0 leaf, and the direction back down the blade."""
    best = None
    best_len = -1.0
    for obj in bpy.data.objects:
        if obj.type != "CURVE" or not obj.name.startswith("HP_Leaf_00_"):
            continue
        if obj.get("cr_young"):
            continue
        pts = [obj.matrix_world @ bp.co for bp in obj.data.splines[0].bezier_points]
        length = sum((b - a).length for a, b in zip(pts, pts[1:]))
        if length > best_len:
            best_len = length
            best = pts
    if not best:
        origin = bpy.data.objects["HP_Shoot_00"].matrix_world.translation.copy()
        tip = origin + Vector((0.0, 0.0, 0.16))
        return tip, Vector((0.0, 0.0, 1.0))
    direction = (best[-1] - best[0]).normalized()
    return best[-1], direction


def frame_camera(cam):
    """Move in on the rounded tip, hold the split vein, then drop to the black scars."""
    nodes = _nodes()
    if not nodes:
        return
    col = collection("Reef")
    previous = bpy.data.objects.get("HP_LessonAim")
    if previous is not None:
        bpy.data.objects.remove(previous, do_unlink=True)
    aim = bpy.data.objects.new("HP_LessonAim", None)
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
    for constraint in list(cam.constraints):
        cam.constraints.remove(constraint)

    from .util import frame_at

    tip, direction = _hero_tip()
    shoot = bpy.data.objects["HP_Shoot_00"]
    right = shoot.matrix_world.to_3x3().col[0].copy()
    _side, normal = frame_at(direction, right, 0.0)
    # The dark vein is on the +normal face. Stay on that side.
    focus = tip - direction * 0.004
    vein = tip - direction * 0.028
    front = [p for p in nodes if p.y < -0.004] or nodes[:3]
    scar = sum(front, Vector()) / len(front)
    scar = Vector((scar.x, scar.y + 0.004, scar.z))
    center = sum(nodes, Vector()) / len(nodes)
    patch = center + Vector((0.0, 0.0, 0.07))

    def cam_at(frame, point, dist, lift, side=0.0):
        _key_loc(cam, frame, Vector((point.x + side, point.y - dist, point.z + lift)))

    def on_face(frame, point, dist):
        _key_loc(cam, frame, point + normal * dist)

    def _lens(frame, mm):
        cam.data.lens = mm
        cam.data.keyframe_insert("lens", frame=frame)

    _key_loc(aim, 1, patch)
    _key_loc(aim, 140, vein)
    _key_loc(aim, 250, focus)
    _key_loc(aim, 540, focus)
    _key_loc(aim, 680, scar)
    _key_loc(aim, 800, scar + Vector((0.012, 0.0, -0.006)))
    _key_loc(aim, 870, patch)
    _key_loc(aim, END, patch)

    cam_at(1, patch, 0.62, 0.08)
    on_face(140, vein, 0.07)
    on_face(250, focus, 0.058)
    on_face(340, focus, 0.050)
    on_face(540, focus, 0.046)
    # In front of the cut, a little below the cord, so the wall and the scars fill the frame.
    cam_at(680, scar, 0.22, -0.012)
    cam_at(800, scar, 0.20, -0.008)
    cam_at(870, patch, 0.58, 0.04)
    cam_at(END, patch, 0.56, 0.03)
    _lens(1, 50)
    _lens(140, 65)
    _lens(250, 85)
    _lens(540, 95)
    _lens(680, 50)
    _lens(END, 50)

    track = cam.constraints.new("TRACK_TO")
    track.target = aim
    axes = [item.identifier for item in track.bl_rna.properties["track_axis"].enum_items]
    ups = [item.identifier for item in track.bl_rna.properties["up_axis"].enum_items]
    if "TRACK_NEGATIVE_Z" in axes:
        track.track_axis = "TRACK_NEGATIVE_Z"
    if "UP_Y" in ups:
        track.up_axis = "UP_Y"
    cam.data.clip_start = 0.001
    _bezier(aim)
    _bezier(cam)
    _bezier(cam.data)
    print("lesson camera", len(nodes), "tip", [round(v, 4) for v in tip], "scar", [round(v, 4) for v in scar], "lens", cam.data.lens)
