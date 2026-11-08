"""Lesson meadow for Halodule pinifolia. Run inside Blender.

HP_LESSON_PHASE=stills builds the blend and writes check stills.
HP_LESSON_PHASE=render writes the silent 900-frame film.
This script does not publish the phone .glb.
"""

import os
import sys

import bpy
from mathutils import Vector

HERE = r"d:\pepot\marinesee\assets\models-3d"
SPECIES = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
# The private entry must win over assets/models-3d/_build_rotundata.py.
if SPECIES in sys.path:
    sys.path.remove(SPECIES)
sys.path.insert(0, SPECIES)
for _name in [n for n in sys.modules if n == "halodule_pinifolia_build" or n.startswith("halodule_pinifolia_build.")]:
    del sys.modules[_name]
sys.modules.pop("_build_rotundata", None)

import _build_rotundata as builder  # noqa: E402

BLEND = r"d:\pepot\marinesee\assets\models-3d\halodule_pinifolia\halodule_pinifolia_lesson.blend"
STILLS = r"C:\Users\reaga\AppData\Local\Temp\hp_lesson_checks"
PHASE = os.environ.get("HP_LESSON_PHASE", "stills")


def _eevee():
    from halodule_pinifolia_build.render import _eevee as use

    use(bpy.context.scene)


def _shot(path, frame):
    scene = bpy.context.scene
    scene.frame_set(frame)
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("STILL", path)
    return path


def _park(cam):
    parked = [(c, c.mute) for c in cam.constraints]
    for c, _mute in parked:
        c.mute = True
    action = None
    if cam.animation_data:
        action = cam.animation_data.action
        cam.animation_data.action = None
    hidden = []
    for obj in bpy.data.objects:
        if obj.name.startswith(("HP_Caption_", "HP_Note_", "HP_Species", "HP_Card")):
            hidden.append((obj, obj.animation_data.action if obj.animation_data else None))
            if obj.animation_data:
                obj.animation_data.action = None
            obj.hide_render = True
    return parked, action, hidden


def _unpark(cam, parked, action, hidden):
    for c, mute in parked:
        c.mute = mute
    if cam.animation_data is not None:
        cam.animation_data.action = action
    for obj, obj_action in hidden:
        if obj.animation_data is not None:
            obj.animation_data.action = obj_action


def _look(cam, eye, aim):
    cam.location = eye
    cam.rotation_euler = (aim - eye).to_track_quat("-Z", "Y").to_euler()


def render_checks():
    import math

    os.makedirs(STILLS, exist_ok=True)
    scene = bpy.context.scene
    _eevee()
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 100
    try:
        scene.eevee.taa_render_samples = 24
    except AttributeError:
        pass
    scene.render.image_settings.media_type = "IMAGE"
    scene.render.image_settings.file_format = "JPEG"
    scene.render.image_settings.quality = 92
    beats = (
        (80, "beat_patch.jpg"),
        (360, "beat_tip.jpg"),
        (480, "beat_tip_hold.jpg"),
        (700, "beat_scar.jpg"),
        (880, "beat_wide.jpg"),
    )
    saved = [_shot(os.path.join(STILLS, name), frame) for frame, name in beats]
    cam = bpy.data.objects["Camera"]
    parked, action, hidden = _park(cam)
    scene.frame_set(860)
    origin = bpy.data.objects["HP_Shoot_00"].matrix_world.translation.copy()
    _look(cam, origin + Vector((-0.02, -0.10, 0.18)), origin + Vector((0.0, 0.0, 0.14)))
    cam.data.lens = 70
    saved.append(_shot(os.path.join(STILLS, "close_shoot.jpg"), 860))
    center = Vector((0.01, 0.015, 0.06))
    elev = math.radians(15.0)
    dist = 0.78
    eye = Vector((center.x, center.y - dist * math.cos(elev), center.z + dist * math.sin(elev)))
    _look(cam, eye, center)
    saved.append(_shot(os.path.join(STILLS, "front_orbit.jpg"), 860))
    _unpark(cam, parked, action, hidden)
    bpy.context.scene.frame_set(860)
    return saved


def recaption(render=True):
    """Swap the on-screen words, then render. The meadow and the camera stay."""
    import os

    builder.config.use_lesson()
    if os.path.isfile(BLEND):
        bpy.ops.wm.open_mainfile(filepath=BLEND)
    from halodule_pinifolia_build import captions
    from halodule_pinifolia_build.render import render_lesson, render_stills

    captions.build(900)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)
    if render:
        render_lesson(900)
        bpy.ops.wm.save_as_mainfile(filepath=BLEND)
    else:
        os.makedirs(STILLS, exist_ok=True)
        render_stills(STILLS, frames=(420,), width=1920, height=1080, samples=16)
    print("RECAPTION_DONE")


def render_frames():
    """Write one JPEG per frame. A later run skips frames already on disk."""
    import os

    out = r"C:\Users\reaga\AppData\Local\Temp\cr_lesson_frames"
    os.makedirs(out, exist_ok=True)
    if os.path.isfile(BLEND):
        bpy.ops.wm.open_mainfile(filepath=BLEND)
    from halodule_pinifolia_build.render import _eevee, _frame

    scene = bpy.context.scene
    _eevee(scene)
    _frame(scene, 1920, 1080, 48)
    scene.render.image_settings.media_type = "IMAGE"
    scene.render.image_settings.file_format = "JPEG"
    scene.render.image_settings.quality = 90
    scene.render.use_persistent_data = True
    for frame in range(1, 901):
        fp = os.path.join(out, "f%04d.jpg" % frame)
        if os.path.isfile(fp) and os.path.getsize(fp) > 1000:
            continue
        scene.frame_set(frame)
        scene.render.filepath = fp
        bpy.ops.render.render(write_still=True)
        if frame % 30 == 0:
            print("FRAME", frame)
    print("FRAMES_DONE")


def reframe_wide():
    """Move only the wide-shot camera back onto the meadow. The plant stays."""
    import math

    bpy.ops.wm.open_mainfile(filepath=BLEND)
    scene = bpy.context.scene
    scene.frame_set(860)
    deps = bpy.context.evaluated_depsgraph_get()
    pts = []
    for obj in bpy.data.collections["Meadow"].objects:
        if obj.type != "MESH":
            continue
        ev = obj.evaluated_get(deps)
        for corner in ev.bound_box:
            pts.append(ev.matrix_world @ Vector(corner))
    xs = [p.x for p in pts]
    ys = [p.y for p in pts]
    zs = [p.z for p in pts]
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    minz, maxz = min(zs), max(zs)
    aim = Vector(((minx + maxx) * 0.5, (miny + maxy) * 0.5, (minz + maxz) * 0.5))
    half_w = (maxx - minx) * 0.5
    half_h = (maxz - minz) * 0.5
    lens = 50.0
    tan_x = (36.0 * 0.5) / lens
    tan_y = tan_x * (9.0 / 16.0)
    dist = 1.16 * max(half_w / tan_x, half_h / tan_y, 0.2)
    eye = Vector((aim.x, aim.y - dist, aim.z))
    limit = 1.00
    if math.hypot(eye.x, eye.y) > limit:
        eye.y = -math.sqrt(max(0.0, limit * limit - eye.x * eye.x))
        dist = aim.y - eye.y
        need = 1.16 * max(half_w / tan_x, half_h / tan_y, 0.2)
        if dist < need:
            lens = max(28.0, 50.0 * (dist / need))
    cam = bpy.data.objects["Camera"]
    aim_obj = bpy.data.objects["HP_LessonAim"]
    cam.data.lens = lens
    print(
        "WIDE bounds",
        [round(v, 3) for v in (minx, maxx, miny, maxy, minz, maxz)],
        "dist", round(dist, 3),
        "lens", round(lens, 2),
    )
    print("WIDE aim", [round(v, 4) for v in aim], "eye", [round(v, 4) for v in eye])
    for frame in (790, 900):
        aim_obj.location = aim
        aim_obj.keyframe_insert("location", frame=frame)
        cam.location = eye
        cam.keyframe_insert("location", frame=frame)
    from halodule_pinifolia_build.lesson import _bezier

    _bezier(aim_obj)
    _bezier(cam)
    bpy.context.view_layer.update()
    scene.frame_set(860)
    here = cam.matrix_world.translation
    print("WIDE cam860", [round(v, 4) for v in here], "radial", round(math.hypot(here.x, here.y), 3))
    _eevee()
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 100
    try:
        scene.eevee.taa_render_samples = 16
    except AttributeError:
        pass
    scene.render.image_settings.media_type = "IMAGE"
    scene.render.image_settings.file_format = "JPEG"
    scene.render.image_settings.quality = 90
    os.makedirs(STILLS, exist_ok=True)
    path = os.path.join(STILLS, "beat_patch.jpg")
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("STILL", path)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)
    print("REFRAME_DONE")


def build():
    if PHASE == "reframe":
        return reframe_wide()
    if PHASE == "render":
        bpy.ops.wm.open_mainfile(filepath=BLEND)
        from halodule_pinifolia_build.render import render_lesson

        render_lesson(900)
        bpy.ops.wm.save_as_mainfile(filepath=BLEND)
        print("LESSON_RENDER_DONE")
        return
    if PHASE == "captions":
        return recaption(render=False)
    if PHASE == "video":
        return recaption(render=True)
    if PHASE == "frames":
        return render_frames()
    builder.config.use_lesson()
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    report = builder.build(reset=True, overwrite_anim=True, do_publish=False, blend_path=BLEND)
    print("LESSON_REPORT", report)
    if PHASE == "render":
        if report["problems"]:
            print("LESSON_SKIP render; checks failed")
            return report
        from halodule_pinifolia_build.render import render_lesson

        render_lesson(900)
        bpy.ops.wm.save_as_mainfile(filepath=BLEND)
    else:
        render_checks()
        bpy.ops.wm.save_as_mainfile(filepath=BLEND)
    return report


if __name__ == "__main__":
    build()
