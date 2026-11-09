"""The Grow action. Bone scale Y lengthens a part from its base.

Scale X and Z stay 1. Frame 316 holds with constant interpolation.
Frame 330 copies frame 1, so playback jumps back and does not run backwards.
"""

import bpy
from mathutils import Euler, Quaternion, Vector

from . import timeline
from .config import CONFIG
from .util import set_mode
from . import rig


def _names(arm, prefix):
    return sorted(name for name in arm.data.bones.keys() if name.startswith(prefix))


def _local(bone, offset):
    return bone.matrix_local.to_3x3().transposed() @ Vector(offset)


def _key(pb, frame, scale=None, rot=None, loc=None):
    if scale is not None:
        pb.scale = (1.0, float(scale), 1.0)
        pb.keyframe_insert(data_path="scale", frame=frame)
    if rot is not None:
        pb.rotation_euler = Euler(rot, "XYZ")
        pb.keyframe_insert(data_path="rotation_euler", frame=frame)
    if loc is not None:
        pb.location = Vector(loc)
        pb.keyframe_insert(data_path="location", frame=frame)


def _mix(folded, opened, t):
    qa = Euler(folded, "XYZ").to_quaternion()
    qb = Euler(opened, "XYZ").to_quaternion()
    return tuple(qa.slerp(qb, max(0.0, min(1.0, t))).to_euler("XYZ"))


def _fold(bone, stem):
    rest = bone.matrix_local.to_3x3()
    y = rest.col[1].normalized()
    target = stem.normalized()
    q = y.rotation_difference(target)
    if q.angle > 1.05:
        q = Quaternion(q.axis, 1.05)
    local = rest.to_quaternion().inverted() @ q @ rest.to_quaternion()
    return tuple(local.to_euler("XYZ"))


def fcurves(action):
    out = []
    if hasattr(action, "layers"):
        slots = list(getattr(action, "slots", []) or [])
        for layer in action.layers:
            for strip in layer.strips:
                bags = []
                if hasattr(strip, "channelbags"):
                    bags.extend(list(strip.channelbags))
                for slot in slots:
                    try:
                        bag = strip.channelbag(slot)
                    except TypeError:
                        try:
                            bag = strip.channelbag(slot, ensure=False)
                        except TypeError:
                            bag = None
                    if bag is not None:
                        bags.append(bag)
                seen = set()
                for bag in bags:
                    if id(bag) in seen or not hasattr(bag, "fcurves"):
                        continue
                    seen.add(id(bag))
                    out.extend(bag.fcurves)
        if out:
            return out
    if hasattr(action, "fcurves"):
        out.extend(action.fcurves)
    return out


def _bind(arm):
    old = bpy.data.actions.get("Grow")
    if old is not None:
        bpy.data.actions.remove(old)
    action = bpy.data.actions.new("Grow")
    action.use_fake_user = True
    ad = arm.animation_data_create()
    ad.action = action
    if hasattr(action, "slots"):
        try:
            slot = action.slots.new("OBJECT", arm.name)
        except TypeError:
            slot = action.slots.new(id_type="OBJECT", name=arm.name)
        try:
            ad.action_slot = slot
        except (AttributeError, TypeError, RuntimeError) as exc:
            print("action_slot", exc)
    return action


def _polish(action, hold):
    curves = fcurves(action)
    if not curves:
        raise RuntimeError("Grow has no fcurves; the action API did not accept the keys")
    for fc in curves:
        linear = ("rhizome_" in fc.data_path) or fc.data_path.endswith(("scale", "location"))
        for kp in fc.keyframe_points:
            if abs(kp.co[0] - hold) < 0.1:
                kp.interpolation = "CONSTANT"
            elif linear:
                kp.interpolation = "LINEAR"
            else:
                kp.interpolation = "BEZIER"
                kp.handle_left_type = "AUTO_CLAMPED"
                kp.handle_right_type = "AUTO_CLAMPED"
        fc.update()
    return len(curves)


def _clock_frames(cfg):
    hold = int(cfg["frame_hold"])
    frames = set(range(1, hold + 1, 4))
    frames.update((1, 40, 120, 200, 300, hold, int(cfg["frame_end"])))
    return sorted(frames)


def _pose_frame(frame, end):
    """Frame 330 uses the frame-1 pose so the clip restarts instead of reversing."""
    return 1 if frame == end else frame


def animate(arm, cfg=CONFIG):
    tiny = float(cfg["min_bone_scale"])
    hold = int(cfg["frame_hold"])
    end = int(cfg["frame_end"])
    count = len(_names(arm, "shoot_"))
    nseg = len(_names(arm, "rhizome_"))
    if count < 1 or nseg < 1:
        raise RuntimeError("nothing to animate")
    for pb in arm.pose.bones:
        pb.rotation_mode = "XYZ"
        pb.location = (0.0, 0.0, 0.0)
        pb.rotation_euler = (0.0, 0.0, 0.0)
        pb.scale = (1.0, 1.0, 1.0)
    set_mode(arm, "POSE")
    action = _bind(arm)
    data = arm.data.bones
    chains = rig.chain_table()
    chords = {}
    bone_info = {}
    for chain in chains:
        for local, name in enumerate(chain["bones"]):
            chords[name] = data[name].tail_local - data[name].head_local
            bone_info[name] = (local, chain)

    def bone_scale(name, frame):
        local, chain = bone_info[name]
        return timeline.segment_scale(
            local, chain["nseg"], frame, tiny, chain["ready"], chain["stub"]
        )

    def node_offset(chain_i, node_i, frame):
        chain = chains[chain_i]
        off = Vector((0.0, 0.0, 0.0))
        if chain["join"] >= 0:
            off += node_offset(0, chain["join"], frame)
        for s in range(min(int(node_i), len(chain["bones"]))):
            name = chain["bones"][s]
            off += chords[name] * (bone_scale(name, frame) - 1.0)
        return off

    frames = _clock_frames(cfg)
    shoot_names = _names(arm, "shoot_")
    for name in chords:
        pb = arm.pose.bones[name]
        bone = data[name]
        local, chain = bone_info[name]
        chain_i = chains.index(chain)
        for frame in frames:
            src = _pose_frame(frame, end)
            _key(pb, frame, scale=bone_scale(name, src), loc=_local(bone, node_offset(chain_i, local, src)))

    for name in shoot_names:
        i = int(name.split("_")[1])
        emp = bpy.data.objects.get("CR_Shoot_%02d" % i)
        chain_i = int(emp.get("cr_chain", 0)) if emp else 0
        at = int(emp.get("cr_at", i)) if emp else i
        ready = int(emp.get("cr_ready", 40)) if emp else 40
        pb = arm.pose.bones[name]
        bone = data[name]
        stem = (bone.tail_local - bone.head_local)
        for frame in frames:
            src = _pose_frame(frame, end)
            sy = timeline.shoot_scale(i, count, src, tiny)
            tuck = Vector((0.0, 0.0, -timeline.TUCK_Z * timeline.tuck(i, count, src)))
            _key(pb, frame, scale=sy, loc=_local(bone, node_offset(chain_i, at, src) + tuck))

        for j, leaf in enumerate(_names(arm, "leaf_%02d_" % i)):
            lpb = arm.pose.bones[leaf]
            lb = data[leaf]
            folded = _fold(lb, stem.normalized())
            opened = (0.0, 0.0, 0.0)
            for frame in frames:
                src = _pose_frame(frame, end)
                sy = timeline.leaf_scale(i, j, count, src, tiny)
                stem_sy = timeline.shoot_scale(i, count, src, tiny)
                lift = stem * (cfg["leaf_base_frac"] * (stem_sy - 1.0))
                tuck = Vector((0.0, 0.0, -timeline.TUCK_Z * timeline.tuck(i, count, src)))
                rot = _mix(folded, opened, timeline.leaf_open(i, j, count, src))
                _key(lpb, frame, scale=sy, rot=rot, loc=_local(lb, node_offset(chain_i, at, src) + tuck + lift))

        for r_i, root in enumerate(_names(arm, "root_%02d_" % i)):
            rpb = arm.pose.bones[root]
            rb = data[root]
            for frame in frames:
                src = _pose_frame(frame, end)
                _key(
                    rpb,
                    frame,
                    scale=timeline.root_scale_at(src, tiny, ready),
                    loc=_local(rb, node_offset(chain_i, at, src)),
                )

    set_mode(arm, "OBJECT")
    ncurves = _polish(action, hold)
    try:
        action.use_frame_range = True
        action.frame_start = 1
        action.frame_end = end
    except (AttributeError, TypeError):
        pass
    bpy.context.scene.frame_end = end
    bpy.context.view_layer.update()
    print("animate Grow curves", ncurves, "shoots", count)
    return action
