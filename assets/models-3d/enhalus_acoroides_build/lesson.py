"""Lesson camera for tape seagrass. Thirty seconds at 30 fps.

The meadow is already the full plant, the same one as the phone file.
The camera stays low and looks up the long inrolled blades, then moves to
the cut face where the bristled rhizome and the cord roots are visible.
It does not orbit, and it does not push in on a ribbon tip.
No floating text lives in this scene. Subtitles are burned onto the film.
"""

import math

import bpy
from mathutils import Vector

from .util import collection, link, tag
from .config import px

# Kept so an old caption import still loads. The film does not use these beats.
BUD_END = 120
CREEP_END = 330
ROOT_END = 510
SHOOT_END = 750
END = 900

# Low on the blades until the spoken pause before the rhizome, then the cut.
# Blades through "roll inward", then the cut as the rhizome line begins.
BLADE_HOLD = 380
MARGIN = 430
CUT_IN = 455


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


def animate(arm, cfg):
    """Hold the full meadow. A slow sway keeps the blades alive. Scale stays 1."""
    from .grow import _key, _polish

    action = _action(arm)
    leaves = set(_names(arm, "leaf_"))
    sway_frames = [1, 120, 240, 360, 480, 600, 720, END]
    for pb in arm.pose.bones:
        if pb.name == "base":
            continue
        if pb.name not in leaves:
            _key(pb, 1, scale=1.0, loc=(0.0, 0.0, 0.0), rot=(0.0, 0.0, 0.0))
            _key(pb, END, scale=1.0, loc=(0.0, 0.0, 0.0), rot=(0.0, 0.0, 0.0))
            continue
        index = int(pb.name.split("_")[1]) + int(pb.name.split("_")[-1])
        for frame in sway_frames:
            phase = (frame / 110.0) + index * 0.55
            amp = 0.0 if frame in (1, END) else 0.04
            rot = (
                amp * math.sin(phase),
                amp * 0.30 * math.sin(phase * 0.8 + 0.4),
                amp * 0.18 * math.cos(phase),
            )
            _key(pb, frame, scale=1.0, rot=rot, loc=(0.0, 0.0, 0.0))
    _polish(action, END)
    action.use_frame_range = True
    action.frame_start = 1
    action.frame_end = END
    bpy.context.scene.frame_end = END
    return action


def _nodes():
    empties = sorted(
        (obj for obj in bpy.data.objects if obj.name.startswith(px("Shoot_"))),
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


def frame_camera(cam):
    """Low view up the long blades, then the cut face. Lens is not a tip close-up."""
    nodes = _nodes()
    if not nodes:
        return
    col = collection("Reef")
    previous = bpy.data.objects.get(px("LessonAim"))
    if previous is not None:
        bpy.data.objects.remove(previous, do_unlink=True)
    aim = bpy.data.objects.new(px("LessonAim"), None)
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

    origin = nodes[0]
    center = sum(nodes, Vector()) / len(nodes)
    # Look up the blades from in front of the bed. Then drop to the open cut.
    blade = Vector((origin.x, origin.y, 0.72))
    margin = Vector((origin.x + 0.02, origin.y, 0.30))
    cut = Vector((center.x, center.y - 0.01, -0.010))

    _key_loc(aim, 1, blade)
    _key_loc(aim, BLADE_HOLD, blade)
    _key_loc(aim, MARGIN, margin)
    _key_loc(aim, CUT_IN, cut)
    _key_loc(aim, END, cut + Vector((0.012, 0.0, 0.004)))

    _key_loc(cam, 1, Vector((0.04, -0.78, 0.08)))
    _key_loc(cam, BLADE_HOLD, Vector((0.07, -0.62, 0.10)))
    _key_loc(cam, MARGIN, Vector((0.10, -0.42, 0.11)))
    _key_loc(cam, CUT_IN, Vector((0.02, -0.32, 0.02)))
    _key_loc(cam, END, Vector((0.03, -0.36, 0.025)))

    track = cam.constraints.new("TRACK_TO")
    track.target = aim
    axes = [item.identifier for item in track.bl_rna.properties["track_axis"].enum_items]
    ups = [item.identifier for item in track.bl_rna.properties["up_axis"].enum_items]
    if "TRACK_NEGATIVE_Z" in axes:
        track.track_axis = "TRACK_NEGATIVE_Z"
    if "UP_Y" in ups:
        track.up_axis = "UP_Y"

    cam.data.lens = 32
    cam.data.keyframe_insert(data_path="lens", frame=1)
    cam.data.keyframe_insert(data_path="lens", frame=MARGIN)
    cam.data.lens = 48
    cam.data.keyframe_insert(data_path="lens", frame=CUT_IN)
    cam.data.keyframe_insert(data_path="lens", frame=END)
    _bezier(aim)
    _bezier(cam)
    print("lesson camera low-blades then cut, lens", cam.data.lens)
