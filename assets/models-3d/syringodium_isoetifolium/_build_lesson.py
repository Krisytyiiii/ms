"""Lesson for Syringodium isoetifolium. Run inside Blender.

SI_PHASE=build saves the blend and writes stills.
SI_PHASE=video renders the 30 second film, then muxes speech and bottom subtitles.
No music. No floating 3D text.
"""

import json
import os
import shutil
import subprocess
import sys

import bpy

ROOT = r"d:\pepot\marinesee\assets\models-3d"
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from syringodium_isoetifolium_build import captions, checks, config, layout, meshes, realism, reef, scene
from syringodium_isoetifolium_build.lesson import frame_camera
from syringodium_isoetifolium_build.render import LESSON_MP4, _eevee, render_lesson
from syringodium_isoetifolium_build.script import TIMINGS, WAV

BLEND = r"d:\pepot\marinesee\assets\models-3d\syringodium_isoetifolium\syringodium_isoetifolium_lesson.blend"
LESSON_OUT = r"d:\pepot\marinesee\assets\models-3d\syringodium_isoetifolium\syringodium_isoetifolium_lesson.mp4"
APP_OUT = r"d:\pepot\marinesee\app\assets\models-3d\syringodium_isoetifolium_lesson.mp4"
STILLS = r"C:\Users\reaga\AppData\Local\Temp\si_isoetifolium_stills"
FFMPEG = (
    r"C:\Users\reaga\AppData\Local\Microsoft\WinGet\Packages"
    r"\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
    r"\ffmpeg-9.0.1-full_build\bin\ffmpeg.exe"
)
PHASE = os.environ.get("SI_PHASE", "build")


def _refuse(path):
    norm = os.path.abspath(path).replace("\\", "/").lower()
    if "cymodocea_rotundata" in norm or "rotundata_build" in norm:
        raise SystemExit("refusing to write a rotundata path: " + path)


def _probe():
    return os.path.join(os.path.dirname(FFMPEG), "ffprobe.exe")


def _run(cmd):
    done = subprocess.run(cmd, capture_output=True, text=True)
    if done.returncode != 0:
        sys.stderr.write(done.stderr[-2000:])
        raise SystemExit("command failed %s" % done.returncode)
    return done


def _duration(path):
    out = _run([
        _probe(), "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path,
    ])
    return float(out.stdout.strip())


def _ass_time(seconds):
    cs = int(round(max(0.0, seconds) * 100))
    seconds, cs = divmod(cs, 100)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return "%d:%02d:%02d.%02d" % (hours, minutes, seconds, cs)


def _ass(cues):
    lines = [
        "[Script Info]",
        "ScriptType: v4.00+",
        "PlayResX: 1920",
        "PlayResY: 1080",
        "WrapStyle: 0",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        "Style: Default,Arial,46,&H00FFFFFF,&H000000FF,&H00000000,&H96000000,-1,0,0,0,100,100,0,0,3,0,0,2,90,90,54,1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    for i, cue in enumerate(cues):
        start = float(cue["start"])
        end = float(cue["end"])
        if i + 1 < len(cues):
            end = min(end, float(cues[i + 1]["start"]) - 0.04)
        if end < start + 0.2:
            end = start + 0.2
        text = cue["text"].replace("\n", " ")
        lines.append("Dialogue: 0,%s,%s,Default,,0,0,0,,%s" % (_ass_time(start), _ass_time(end), text))
    path = os.path.join(os.path.dirname(WAV), "captions.ass")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")
    return path


def _mux(silent):
    _refuse(LESSON_OUT)
    _refuse(APP_OUT)
    with open(TIMINGS, "r", encoding="utf-8") as handle:
        cues = json.load(handle)["cues"]
    ass = _ass(cues)
    escaped = os.path.abspath(ass).replace("\\", "/").replace(":", "\\:")
    os.makedirs(os.path.dirname(LESSON_OUT), exist_ok=True)
    _run([
        FFMPEG, "-y",
        "-i", silent,
        "-i", WAV,
        "-vf", "subtitles='%s'" % escaped,
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "18",
        "-c:a", "aac",
        "-b:a", "160k",
        "-af", "apad=pad_dur=30,atrim=0:30",
        "-t", "30",
        "-movflags", "+faststart",
        LESSON_OUT,
    ])
    os.makedirs(os.path.dirname(APP_OUT), exist_ok=True)
    shutil.copy2(LESSON_OUT, APP_OUT)
    print("LESSON_VIDEO", LESSON_OUT, round(_duration(LESSON_OUT), 3))


def _shot(path, frame):
    scene = bpy.context.scene
    scene.frame_set(frame)
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("STILL", path, frame)


def render_stills(marks):
    os.makedirs(STILLS, exist_ok=True)
    scene = bpy.context.scene
    _eevee(scene)
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    try:
        scene.eevee.taa_render_samples = 8
    except AttributeError:
        pass
    scene.render.image_settings.media_type = "IMAGE"
    scene.render.image_settings.file_format = "JPEG"
    scene.render.image_settings.quality = 90
    captions.clear()
    _shot(os.path.join(STILLS, "meadow.jpg"), 1)
    for name in ("side", "end", "length", "cut", "roots"):
        _shot(os.path.join(STILLS, name + ".jpg"), marks[name])


def build():
    _refuse(BLEND)
    config.use_lesson()
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    scene.setup_scene()
    scene.clear_plant()
    layout.create_plant()
    bpy.context.view_layer.update()
    meshes.rebuild_meshes()
    reef.build_presentation()
    realism.lesson_shade()
    captions.clear()
    cam = bpy.data.objects["Camera"]
    marks = frame_camera(cam)
    bpy.context.view_layer.update()
    report = checks.validate()
    print("LESSON_REPORT", report)
    os.makedirs(os.path.dirname(BLEND), exist_ok=True)
    bpy.context.scene.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)
    if report["problems"]:
        print("LESSON_SKIP stills; checks failed")
        sys.exit(1)
    render_stills(marks)
    return report


def video():
    _refuse(BLEND)
    _refuse(LESSON_MP4)
    if os.path.isfile(BLEND):
        bpy.ops.wm.open_mainfile(filepath=BLEND)
    captions.clear()
    silent = render_lesson(900)
    _mux(silent)


if __name__ == "__main__":
    if PHASE == "video":
        video()
    else:
        build()
