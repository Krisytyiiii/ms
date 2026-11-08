"""Lesson growth and the teaching camera for Halophila ovalis.

Thirty seconds at 30 fps. Open on the bare uneven bed, then the first
pairs, then a close hold where the eight cross veins can be counted,
then the buried stem and the roots in the cut. No floating text.
The camera lives in this blend only. The phone file does not export it.
"""

import bpy
from mathutils import Vector

from .util import collection, control_points, link, smoothstep, tag

BARE = 48
VEIN_IN = 400
VEIN_HOLD = 460
VEIN_OUT = 700
END = 900
HERO = 2


def _names(arm, prefix):
    return sorted(name for name in arm.pose.bones.keys() if name.startswith(prefix))


def _window(i):
    """When shoot i lengthens. The hero pair is first, so the close view has a leaf."""
    if i == HERO:
        return 52, 150
    if i < 4:
        t0 = 86 + i * 28
        return t0, t0 + 78
    t0 = 168 + (i - 4) * 34
    return t0, min(360, t0 + 78)


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


def _grow(frame, t0, t1, tiny):
    if frame <= t0:
        return tiny
    if frame >= t1:
        return 1.0
    return tiny + (1.0 - tiny) * smoothstep((frame - t0) / float(t1 - t0))


def _hide_parts():
    from .grow import _reveal

    for obj in bpy.data.objects:
        name = obj.name
        if name == "Rhizome":
            _reveal(obj, BARE)
        elif name.startswith(("Shoot_", "Leaf_", "Root_")):
            i = int(name.split("_")[1])
            t0, _t1 = _window(i)
            _reveal(obj, max(BARE, t0))


def animate(arm, cfg):
    from .grow import _fold, _key, _local, _mix, _polish

    tiny = cfg["min_bone_scale"]
    action = _action(arm)
    bones = arm.data.bones
    rh = _names(arm, "rhizome_")
    nseg = max(1, len(rh))
    windows = [BARE + round((320 - BARE) * k / nseg) for k in range(nseg + 1)]
    chords = [bones[name].tail_local - bones[name].head_local for name in rh]
    rh_frames = sorted(set([1, BARE] + windows + [END]))
    for i, name in enumerate(rh):
        pb = arm.pose.bones[name]
        for frame in rh_frames:
            scale = _seg_scale(i, frame, windows, tiny)
            off = Vector()
            for k in range(i):
                off += chords[k] * (_seg_scale(k, frame, windows, tiny) - 1.0)
            _key(pb, frame, scale=scale, loc=_local(bones[name], off))

    lift = cfg["stem_height_m"] * cfg["leaf_base_frac"] + 0.004 / (1.0 - tiny)
    for name in _names(arm, "shoot_"):
        i = int(name.split("_")[1])
        sb = bones[name]
        stem = (sb.tail_local - sb.head_local).normalized()
        t0, t1 = _window(i)
        stem_frames = [1, t0, (t0 + t1) // 2, t1, VEIN_IN, END]
        for frame in stem_frames:
            _key(arm.pose.bones[name], frame, scale=_grow(frame, t0, t1, tiny), loc=_local(sb, Vector()))
        for leaf in _names(arm, "leaf_%02d_" % i):
            pb, lb = arm.pose.bones[leaf], bones[leaf]
            folded, opened = _fold(lb, stem), (0.0, 0.0, 0.0)
            for frame in stem_frames:
                sv = _grow(frame, t0, t1, tiny)
                grown = 0.0 if sv <= tiny + 1e-4 else (sv - tiny) / (1.0 - tiny)
                world = stem * ((sv - 1.0) * lift)
                _key(pb, frame, scale=sv, rot=_mix(folded, opened, grown), loc=_local(lb, world))
        for r_i, root in enumerate(_names(arm, "root_%02d_" % i)):
            rb = bones[root]
            rs0 = t0 + 16 + r_i * 8
            rs1 = min(430, rs0 + 90)
            for frame in (1, rs0, (rs0 + rs1) // 2, rs1, END):
                _key(arm.pose.bones[root], frame, scale=_grow(frame, rs0, rs1, tiny), loc=_local(rb, Vector()))

    _hide_parts()
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
        (obj for obj in bpy.data.objects if obj.name.startswith("HO_Shoot_")),
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


def _lens(cam, frame, mm):
    cam.data.lens = mm
    cam.data.keyframe_insert("lens", frame=frame)


def frame_camera(cam):
    """Bare sand, then the pairs, then a steady close view of one oval, then the cut."""
    nodes = _nodes()
    if not nodes:
        return
    col = collection("Reef")
    previous = bpy.data.objects.get("HO_LessonAim")
    if previous is not None:
        bpy.data.objects.remove(previous, do_unlink=True)
    aim = bpy.data.objects.new("HO_LessonAim", None)
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

    hero = nodes[min(HERO, len(nodes) - 1)]
    leaf_obj = bpy.data.objects.get("HO_Leaf_%02d_1" % HERO)
    if leaf_obj is not None:
        pts = control_points(leaf_obj)
        leaf = pts[0].lerp(pts[-1], 0.62)
    else:
        leaf = hero + Vector((0.02, 0.0, 0.02))
    # Look down onto the upper face. The oval sits above the subtitle band.
    face = Vector((0.02, -0.80, 0.62)).normalized()
    vein_aim = leaf + Vector((0.0, 0.0, -0.006))
    vein_eye = leaf + face * 0.102
    bare_aim = Vector((0.0, 0.004, 0.002))
    pair_aim = hero + Vector((0.0, 0.0, 0.016))
    root_aim = nodes[1] + Vector((0.0, -0.006, -0.008))
    patch = sum(nodes, Vector()) / len(nodes)
    wide_aim = Vector((patch.x, patch.y, 0.006))

    _key_loc(aim, 1, bare_aim)
    _key_loc(aim, BARE, bare_aim)
    _key_loc(aim, 120, pair_aim)
    _key_loc(aim, 280, pair_aim)
    _key_loc(aim, VEIN_IN, vein_aim)
    _key_loc(aim, VEIN_HOLD, vein_aim)
    _key_loc(aim, VEIN_OUT, vein_aim)
    _key_loc(aim, 780, root_aim)
    _key_loc(aim, END, wide_aim)

    track = cam.constraints.new("TRACK_TO")
    track.target = aim
    axes = [item.identifier for item in track.bl_rna.properties["track_axis"].enum_items]
    ups = [item.identifier for item in track.bl_rna.properties["up_axis"].enum_items]
    if "TRACK_NEGATIVE_Z" in axes:
        track.track_axis = "TRACK_NEGATIVE_Z"
    if "UP_Y" in ups:
        track.up_axis = "UP_Y"

    def cam_at(frame, point, dist, lift, mm):
        _key_loc(cam, frame, Vector((point.x, point.y - dist, point.z + lift)))
        _lens(cam, frame, mm)

    cam_at(1, bare_aim, 0.30, 0.16, 48)
    cam_at(BARE, bare_aim, 0.28, 0.15, 48)
    cam_at(150, pair_aim, 0.26, 0.07, 50)
    cam_at(320, pair_aim, 0.24, 0.06, 52)
    _key_loc(cam, VEIN_IN, vein_eye)
    _lens(cam, VEIN_IN, 78)
    _key_loc(cam, VEIN_HOLD, vein_eye)
    _lens(cam, VEIN_HOLD, 80)
    _key_loc(cam, VEIN_OUT, vein_eye)
    _lens(cam, VEIN_OUT, 80)
    cam_at(820, root_aim, 0.24, 0.07, 50)
    cam_at(END, wide_aim, 0.34, 0.09, 46)
    _bezier(aim)
    _bezier(cam)
    _bezier(cam.data)
    print("lesson camera", len(nodes), "nodes, hero", HERO)
