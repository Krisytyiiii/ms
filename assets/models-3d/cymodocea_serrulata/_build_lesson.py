"""Lesson meadow for Cymodocea serrulata. Run inside Blender.

CS_PHASE=build saves the lesson blend and writes check stills.
CS_PHASE=video renders the silent 30-second film. It does not publish a glb.
"""

import os
import sys

import bpy

ROOT = r"d:\pepot\marinesee\assets\models-3d"
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from cymodocea_serrulata_build import checks, config, grow, layout, meshes, realism, reef, scene
from cymodocea_serrulata_build.render import _eevee, render_lesson

BLEND = r"d:\pepot\marinesee\assets\models-3d\cymodocea_serrulata\blender\cymodocea_serrulata_lesson.blend"
STILLS = r"C:\Users\reaga\AppData\Local\Temp\cs_serrulata_stills"
PHASE = os.environ.get("CS_PHASE", "build")


def _refuse(path):
    norm = os.path.abspath(path).replace("\\", "/").lower()
    if "cymodocea_rotundata" in norm:
        raise SystemExit("refusing to write a rotundata path: " + path)


def _shot(path, frame):
    scene = bpy.context.scene
    scene.frame_set(frame)
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("STILL", path)


def _teach_frames():
    timing = r"d:\pepot\marinesee\assets\models-3d\cymodocea_serrulata\speech\lesson_timing.json"
    fallback = (("tip", 290), ("sheath", 370), ("scar", 500), ("patch", 690))
    if not os.path.isfile(timing):
        return fallback
    import json

    cues = {c["id"]: c for c in json.load(open(timing, encoding="utf-8-sig")).get("cues") or []}
    frames = []
    for cid, label in (("serrated", "tip"), ("sheath", "sheath"), ("scars", "scar"), ("patch", "patch")):
        if cid not in cues:
            continue
        frames.append((label, max(1, int(round(float(cues[cid]["start"]) * 30.0)) + 10)))
    return frames or fallback


def render_stills():
    os.makedirs(STILLS, exist_ok=True)
    scene = bpy.context.scene
    _eevee(scene)
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    try:
        scene.eevee.taa_render_samples = 16
    except AttributeError:
        pass
    scene.render.image_settings.media_type = "IMAGE"
    scene.render.image_settings.file_format = "JPEG"
    scene.render.image_settings.quality = 90
    for label, frame in _teach_frames():
        _shot(os.path.join(STILLS, label + ".jpg"), frame)


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
    arm = bpy.data.objects["CS_Armature"]
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


def frames():
    """One short range of JPEG frames. A fresh process avoids the GPU leak."""
    _refuse(BLEND)
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    start = int(os.environ.get("CS_START", "1"))
    end = int(os.environ.get("CS_END", "900"))
    out = os.environ["CS_OUT"]
    os.makedirs(out, exist_ok=True)
    scene = bpy.context.scene
    _eevee(scene)
    scene.frame_start = start
    scene.frame_end = end
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 100
    scene.render.fps = 30
    scene.render.use_persistent_data = False
    try:
        scene.eevee.taa_render_samples = 16
    except AttributeError:
        pass
    scene.render.image_settings.media_type = "IMAGE"
    scene.render.image_settings.file_format = "JPEG"
    scene.render.image_settings.quality = 92
    scene.render.filepath = os.path.join(out, "frame_")
    scene.render.use_overwrite = True
    bpy.ops.render.render(animation=True)
    print("FRAMES_DONE", start, end)


if __name__ == "__main__":
    if PHASE == "video":
        video()
    elif PHASE == "frames":
        frames()
    else:
        build()
