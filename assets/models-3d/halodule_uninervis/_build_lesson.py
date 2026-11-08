"""Lesson meadow for Halodule uninervis. Run inside Blender.

HU_PHASE=build saves the lesson blend and writes check stills.
HU_PHASE=video renders the silent 30-second film. It does not publish a glb.
"""

import os
import sys

import bpy

ROOT = r"d:\pepot\marinesee\assets\models-3d"
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from halodule_uninervis_build import captions, checks, config, grow, layout, meshes, realism, reef, scene
from halodule_uninervis_build.lesson import RHIZOME_AT, TIP_AT, VEIN_AT
from halodule_uninervis_build.render import _eevee, render_lesson

BLEND = r"d:\pepot\marinesee\assets\models-3d\halodule_uninervis\halodule_uninervis_lesson.blend"
STILLS = r"C:\Users\reaga\AppData\Local\Temp\hu_uninervis_stills"
PHASE = os.environ.get("HU_PHASE", "build")


def _refuse(path):
    norm = os.path.abspath(path).replace("\\", "/").lower()
    if "cymodocea_rotundata" in norm or "halodule_pinifolia" in norm:
        raise SystemExit("refusing to write another species path: " + path)


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
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    try:
        scene.eevee.taa_render_samples = 12
    except AttributeError:
        pass
    scene.render.image_settings.media_type = "IMAGE"
    scene.render.image_settings.file_format = "JPEG"
    scene.render.image_settings.quality = 90
    hidden = []
    for obj in bpy.data.objects:
        if obj.name.startswith(("HU_Caption_", "HU_Note_", "HU_Card")):
            hidden.append((obj, obj.hide_render))
            obj.hide_render = True
    _shot(os.path.join(STILLS, "patch.jpg"), 120)
    _shot(os.path.join(STILLS, "vein.jpg"), VEIN_AT)
    _shot(os.path.join(STILLS, "leaf_tip.jpg"), TIP_AT + 30)
    _shot(os.path.join(STILLS, "rhizome.jpg"), RHIZOME_AT)
    for obj, was_hidden in hidden:
        obj.hide_render = was_hidden


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
    captions.build(900)
    arm = bpy.data.objects["HU_Armature"]
    grow.animate(arm)
    report = checks.validate()
    print("LESSON_REPORT", report)
    os.makedirs(os.path.dirname(BLEND), exist_ok=True)
    bpy.context.scene.frame_set(860)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)
    if report["problems"]:
        print("LESSON_SKIP stills; checks failed")
        return report
    render_stills()
    return report


def video():
    _refuse(BLEND)
    if os.path.isfile(BLEND):
        bpy.ops.wm.open_mainfile(filepath=BLEND)
    out = render_lesson(900)
    _refuse(out)
    print("LESSON_VIDEO", out)


if __name__ == "__main__":
    if PHASE == "video":
        video()
    else:
        build()
