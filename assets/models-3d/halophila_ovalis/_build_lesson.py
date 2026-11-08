"""Lesson meadow for Halophila ovalis. Run inside Blender.

HO_PHASE=build saves the lesson blend and writes check stills.
HO_PHASE=video renders the silent 30-second film. It does not publish a glb.
"""

import os
import sys

import bpy
from mathutils import Vector

ROOT = r"d:\pepot\marinesee\assets\models-3d"
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from halophila_ovalis_build import checks, config, grow, layout, meshes, realism, reef, scene
from halophila_ovalis_build.render import LESSON_MP4, _eevee, render_lesson

BLEND = r"d:\pepot\marinesee\assets\models-3d\halophila_ovalis\halophila_ovalis_lesson.blend"
STILLS = r"C:\Users\reaga\AppData\Local\Temp\ho_ovalis_stills"
PHASE = os.environ.get("HO_PHASE", "build")
SILENT = os.environ.get("HO_SILENT", LESSON_MP4)


def _refuse(path):
    norm = os.path.abspath(path).replace("\\", "/").lower()
    if "cymodocea_rotundata" in norm or "halophila_minor" in norm:
        raise SystemExit("refusing to write " + path)
    base = os.path.basename(norm)
    if "growth" in base or "pitch" in base:
        raise SystemExit("refusing growth or pitch output: " + path)


def _shot(path, frame):
    view = bpy.context.scene
    view.frame_set(frame)
    view.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("STILL", path)


def _look(cam, eye, aim):
    cam.location = eye
    cam.rotation_euler = (aim - eye).to_track_quat("-Z", "Y").to_euler()


def render_stills():
    """Three check frames only. Not a preview sequence."""
    os.makedirs(STILLS, exist_ok=True)
    view = bpy.context.scene
    _eevee(view)
    view.render.resolution_x = 1280
    view.render.resolution_y = 720
    view.render.resolution_percentage = 100
    try:
        view.eevee.taa_render_samples = 8
    except AttributeError:
        pass
    view.render.image_settings.media_type = "IMAGE"
    view.render.image_settings.file_format = "JPEG"
    view.render.image_settings.quality = 85
    for frame, name in ((20, "sand.jpg"), (520, "veins.jpg"), (860, "roots.jpg")):
        _shot(os.path.join(STILLS, name), frame)


def build():
    _refuse(BLEND)
    config.use_lesson()
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    scene.setup_scene()
    scene.clear_plant()
    layout.create_plant()
    meshes.rebuild_meshes()
    reef.build_presentation()
    realism.lesson_shade()
    arm = bpy.data.objects["HO_Armature"]
    grow.animate(arm)
    report = checks.validate()
    print("LESSON_REPORT", report)
    os.makedirs(os.path.dirname(BLEND), exist_ok=True)
    bpy.context.scene.frame_set(520)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)
    if report["problems"]:
        print("LESSON_SKIP stills; checks failed")
        return report
    if os.environ.get("HO_STILLS") == "1":
        render_stills()
    return report


def video():
    _refuse(BLEND)
    _refuse(SILENT)
    if os.path.isfile(BLEND):
        bpy.ops.wm.open_mainfile(filepath=BLEND)
    out = render_lesson(900, path=SILENT)
    _refuse(out)
    print("LESSON_VIDEO", out)


if __name__ == "__main__":
    if PHASE == "video":
        video()
    else:
        build()
