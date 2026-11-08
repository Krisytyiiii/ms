"""Lesson meadow. Run with blender.exe --background --python this file.

EA_PHASE=stills writes check frames. EA_PHASE=video renders the minute.
The phone .glb is not published from this 900-frame blend.
"""

import os
import sys

os.environ["MARINESEE_CODE"] = "EA"

HERE = r"d:\pepot\marinesee\assets\models-3d"
if HERE not in sys.path:
    sys.path.insert(0, HERE)
for _name in list(sys.modules):
    if _name == "enhalus_acoroides_build" or _name.startswith("enhalus_acoroides_build."):
        del sys.modules[_name]

import bpy

from enhalus_acoroides_build import checks, config, grow, layout, meshes, reef, scene
from enhalus_acoroides_build.render import _eevee, render_lesson

ROOT = r"d:\pepot\marinesee"
BLEND = ROOT + r"\assets\models-3d\enhalus_acoroides\enhalus_acoroides_lesson.blend"
LESSON_MP4 = ROOT + r"\assets\models-3d\enhalus_acoroides\enhalus_acoroides_lesson.mp4"
STILLS = r"C:\Users\reaga\AppData\Local\Temp\ea_lesson_stills"
PHASE = os.environ.get("EA_PHASE", "stills")


def _shot(path, frame):
    scene = bpy.context.scene
    scene.frame_set(frame)
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("STILL", path)


def render_stills():
    os.makedirs(STILLS, exist_ok=True)
    scene = bpy.context.scene
    _eevee(scene)
    scene.render.resolution_x = 960
    scene.render.resolution_y = 540
    scene.render.resolution_percentage = 100
    try:
        scene.eevee.taa_render_samples = 16
    except AttributeError:
        pass
    scene.render.image_settings.media_type = "IMAGE"
    scene.render.image_settings.file_format = "JPEG"
    scene.render.image_settings.quality = 90
    for frame, name in (
        (60, "beat_blades.jpg"),
        (360, "beat_margin.jpg"),
        (520, "beat_to_cut.jpg"),
        (640, "beat_cut.jpg"),
        (800, "beat_roots.jpg"),
        (890, "beat_hold.jpg"),
    ):
        _shot(os.path.join(STILLS, name), frame)


def build():
    config.use_lesson()
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    scene.setup_scene()
    scene.clear_plant()
    layout.create_plant()
    meshes.rebuild_meshes()
    reef.build_presentation()
    arm = bpy.data.objects[config.px("Armature")]
    grow.animate(arm)
    report = checks.validate()
    bpy.context.scene.frame_set(1)
    os.makedirs(os.path.dirname(BLEND), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)
    print("LESSON_REPORT", report)
    if report["problems"]:
        print("LESSON_SKIP stills")
        return report
    if PHASE == "video":
        render_lesson(900, out_path=LESSON_MP4, samples=10)
        bpy.ops.wm.save_as_mainfile(filepath=BLEND)
    else:
        render_stills()
        bpy.context.scene.frame_set(1)
        bpy.ops.wm.save_as_mainfile(filepath=BLEND)
    return report


if __name__ == "__main__":
    build()
