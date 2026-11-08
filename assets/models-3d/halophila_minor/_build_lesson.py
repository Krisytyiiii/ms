"""Lesson meadow for Halophila minor. Run inside Blender.

HM_PHASE=build saves the lesson blend and writes check stills.
HM_PHASE=video renders the silent film, then muxes English speech.
HM_PHASE=speech only writes the five voice lines.
"""

import os
import shutil
import subprocess
import sys

import bpy
from mathutils import Vector

ROOT = r"d:\pepot\marinesee\assets\models-3d"
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from halophila_minor_build import captions, checks, config, grow, layout, meshes, realism, reef, scene
from halophila_minor_build.publish import GLB_PATH
from halophila_minor_build.render import APP_LESSON_MP4, LESSON_MP4, SILENT_MP4, _eevee, render_lesson
from halophila_minor_build.speech import ASS_PATH, MIX_WAV, build as build_speech

BLEND = r"d:\pepot\marinesee\assets\models-3d\halophila_minor\blender\halophila_minor_lesson.blend"
STILLS = r"C:\Users\reaga\AppData\Local\Temp\hm_minor_stills"
SPEECH = r"C:\Users\reaga\AppData\Local\Temp\hm_minor_speech"
PHASE = os.environ.get("HM_PHASE", "build")
FFMPEG = (
    r"C:\Users\reaga\AppData\Local\Microsoft\WinGet\Packages"
    r"\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
    r"\ffmpeg-9.0.1-full_build\bin\ffmpeg.exe"
)
FFPROBE = FFMPEG.replace("ffmpeg.exe", "ffprobe.exe")

PHONE_BLEND = r"d:\pepot\marinesee\assets\models-3d\halophila_minor\blender\halophila_minor.blend"


def _refuse(path):
    norm = os.path.abspath(path).replace("\\", "/").lower()
    for banned in ("cymodocea_rotundata", "halophila_ovalis", "rotundata_build"):
        if banned in norm:
            raise SystemExit("refusing to write " + path)


def _shot(path, frame):
    scene = bpy.context.scene
    scene.frame_set(frame)
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("STILL", path)


def _look(cam, eye, aim):
    cam.location = eye
    cam.rotation_euler = (aim - eye).to_track_quat("-Z", "Y").to_euler()


def render_stills():
    os.makedirs(STILLS, exist_ok=True)
    view = bpy.context.scene
    _eevee(view)
    view.render.resolution_x = 1280
    view.render.resolution_y = 720
    view.render.resolution_percentage = 100
    try:
        view.eevee.taa_render_samples = 12
    except AttributeError:
        pass
    view.render.image_settings.media_type = "IMAGE"
    view.render.image_settings.file_format = "JPEG"
    view.render.image_settings.quality = 90
    for name, frame in (
        ("beat_bud", 50),
        ("beat_stem", 220),
        ("beat_leaves", 360),
        ("beat_veins", 520),
        ("beat_roots", 800),
        ("beat_patch", 890),
    ):
        _shot(os.path.join(STILLS, name + ".jpg"), frame)
    cam = bpy.data.objects["Camera"]
    parked = [(c, c.mute) for c in cam.constraints]
    for constraint, _mute in parked:
        constraint.mute = True
    action = cam.animation_data.action if cam.animation_data else None
    if cam.animation_data:
        cam.animation_data.action = None
    hidden = []
    for obj in bpy.data.objects:
        if obj.name.startswith(("HM_Caption_", "HM_Note_", "HM_Card")):
            hidden.append((obj, obj.hide_render))
            obj.hide_render = True
    view.frame_set(800)
    origin = bpy.data.objects["HM_Shoot_00"].matrix_world.translation.copy()
    _look(cam, origin + Vector((0.0, -0.055, 0.018)), origin + Vector((0.0, 0.0, 0.012)))
    cam.data.lens = 80
    _shot(os.path.join(STILLS, "close_pair.jpg"), 800)
    for constraint, mute in parked:
        constraint.mute = mute
    if cam.animation_data is not None:
        cam.animation_data.action = action
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
    arm = bpy.data.objects["HM_Armature"]
    grow.animate(arm)
    report = checks.validate()
    print("LESSON_REPORT", report)
    os.makedirs(os.path.dirname(BLEND), exist_ok=True)
    bpy.context.scene.frame_set(int(bpy.context.scene.frame_end))
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)
    if report["problems"]:
        print("LESSON_SKIP stills; checks failed")
        return report
    render_stills()
    from halophila_minor_build import publish as publish_mod

    publish_mod.publish(GLB_PATH)
    bpy.ops.wm.save_as_mainfile(filepath=PHONE_BLEND)
    print("PHONE_GLB", GLB_PATH)
    return report


def _duration(path):
    out = subprocess.check_output(
        [
            FFPROBE,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=nokey=1:noprint_wrappers=1",
            path,
        ],
        text=True,
    )
    return float(out.strip())


def _mp4_duration(path):
    if not os.path.isfile(path) or os.path.getsize(path) < 50000:
        return None
    try:
        return _duration(path)
    except (subprocess.CalledProcessError, ValueError):
        return None


def mux():
    _refuse(LESSON_MP4)
    _refuse(APP_LESSON_MP4)
    _refuse(SILENT_MP4)
    if not os.path.isfile(MIX_WAV) or not os.path.isfile(ASS_PATH):
        build_speech()
    ass = ASS_PATH.replace("\\", "/").replace(":", "\\:")
    staged = LESSON_MP4 + ".muxing.mp4"
    cmd = [
        FFMPEG,
        "-y",
        "-i",
        SILENT_MP4,
        "-i",
        MIX_WAV,
        "-vf",
        "subtitles='%s'" % ass,
        "-map",
        "0:v",
        "-map",
        "1:a",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-crf",
        "18",
        "-c:a",
        "aac",
        "-b:a",
        "160k",
        "-t",
        "30",
        staged,
    ]
    done = subprocess.run(cmd, capture_output=True, text=True)
    if done.returncode != 0:
        print(done.stderr[-2000:])
        if os.path.isfile(staged):
            os.remove(staged)
        raise SystemExit("ffmpeg mux failed")
    os.replace(staged, LESSON_MP4)
    os.makedirs(os.path.dirname(APP_LESSON_MP4), exist_ok=True)
    shutil.copy2(LESSON_MP4, APP_LESSON_MP4)
    if os.path.isfile(SILENT_MP4):
        os.remove(SILENT_MP4)
    print("LESSON_MUXED", LESSON_MP4, APP_LESSON_MP4, "sec", round(_duration(LESSON_MP4), 2))


FRAMES = r"C:\Users\reaga\AppData\Local\Temp\hm_minor_frames"
DONE = os.path.join(FRAMES, "DONE")
BATCH = 80


def _frame_file(frame):
    return os.path.join(FRAMES, "f%04d.jpg" % frame)


def _first_missing(frame_end):
    os.makedirs(FRAMES, exist_ok=True)
    for frame in range(1, frame_end + 1):
        path = _frame_file(frame)
        if not os.path.isfile(path) or os.path.getsize(path) < 8000:
            return frame
    return frame_end + 1


def _encode_silent():
    staged = SILENT_MP4 + ".encoding.mp4"
    cmd = [
        FFMPEG,
        "-y",
        "-framerate",
        "30",
        "-i",
        os.path.join(FRAMES, "f%04d.jpg"),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-crf",
        "18",
        "-t",
        "30",
        staged,
    ]
    done = subprocess.run(cmd, capture_output=True, text=True)
    if done.returncode != 0:
        print(done.stderr[-2000:])
        raise SystemExit("could not encode the lesson pictures")
    os.replace(staged, SILENT_MP4)
    print("SILENT_READY", SILENT_MP4, round(_duration(SILENT_MP4), 2))


def video():
    _refuse(BLEND)
    _refuse(SILENT_MP4)
    if not os.path.isfile(MIX_WAV):
        build_speech()
    start = _first_missing(900)
    if start <= 900:
        if os.path.isfile(BLEND):
            bpy.ops.wm.open_mainfile(filepath=BLEND)
        view = bpy.context.scene
        _eevee(view)
        view.frame_start = start
        view.frame_end = min(900, start + BATCH - 1)
        view.render.resolution_x = 1920
        view.render.resolution_y = 1080
        view.render.resolution_percentage = 100
        view.render.fps = 30
        view.render.use_persistent_data = False
        try:
            view.eevee.taa_render_samples = 8
        except AttributeError:
            pass
        view.render.image_settings.media_type = "IMAGE"
        view.render.image_settings.file_format = "JPEG"
        view.render.image_settings.quality = 92
        view.render.filepath = os.path.join(FRAMES, "f####")
        view.render.use_file_extension = True
        print("FRAME_BATCH", view.frame_start, view.frame_end)
        bpy.ops.render.render(animation=True)
        print("FRAME_BATCH_DONE", view.frame_end)
        return
    if _mp4_duration(SILENT_MP4) is None or abs(_mp4_duration(SILENT_MP4) - 30.0) > 0.4:
        _encode_silent()
    mux()
    with open(DONE, "w", encoding="utf-8") as handle:
        handle.write("ok\n")
    print("LESSON_DONE")


if __name__ == "__main__":
    if PHASE == "video":
        video()
    elif PHASE == "speech":
        build_speech()
    else:
        build()
