"""Lesson meadow for Thalassia hemprichii. Run inside Blender.

TH_PHASE=build saves the lesson blend and writes check stills.
TH_PHASE=video renders the silent 30-second film, then muxes English speech
and bottom subtitles. It does not publish a glb.
"""

import os
import shutil
import subprocess
import sys

import bpy

ROOT = r"d:\pepot\marinesee\assets\models-3d"
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from thalassia_hemprichii_build import captions, checks, config, grow, layout, meshes, realism, reef, scene, speech
from thalassia_hemprichii_build.lesson import load_marks
from thalassia_hemprichii_build.render import APP_MP4, LESSON_MP4, SILENT_MP4, _eevee, prepare_picture, render_lesson

BLEND = r"d:\pepot\marinesee\assets\models-3d\thalassia_hemprichii\thalassia_hemprichii_lesson.blend"
STILLS = r"C:\Users\reaga\AppData\Local\Temp\th_hemprichii_stills"
FFMPEG = (
    r"C:\Users\reaga\AppData\Local\Microsoft\WinGet\Packages"
    r"\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
    r"\ffmpeg-9.0.1-full_build\bin\ffmpeg.exe"
)
PHASE = os.environ.get("TH_PHASE", "build")


def _refuse(path):
    norm = os.path.abspath(path).replace("\\", "/").lower()
    if "cymodocea_rotundata" in norm or "rotundata_build" in norm:
        raise SystemExit("refusing to write a rotundata path: " + path)
    if "thalassia_hemprichii" not in norm and "th_hemprichii" not in norm:
        raise SystemExit("refusing to write outside this species: " + path)


def _shot(path, frame):
    shot = bpy.context.scene
    shot.frame_set(frame)
    shot.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("STILL", path)


def render_stills():
    os.makedirs(STILLS, exist_ok=True)
    marks = load_marks()
    shot = bpy.context.scene
    prepare_picture(shot)
    _eevee(shot)
    shot.render.resolution_x = 960
    shot.render.resolution_y = 540
    shot.render.resolution_percentage = 100
    try:
        shot.eevee.taa_render_samples = 4
    except AttributeError:
        pass
    shot.render.image_settings.media_type = "IMAGE"
    shot.render.image_settings.file_format = "JPEG"
    shot.render.image_settings.quality = 88
    frames = (
        ("beat_side", marks["curve"] + 8),
        ("beat_bars", marks["bars"] + 6),
        ("beat_rhizome", marks["rhizome"] + 8),
        ("beat_wide", 860),
    )
    for name, frame in frames:
        _shot(os.path.join(STILLS, name + ".jpg"), frame)


def build():
    _refuse(BLEND)
    speech.ensure()
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
    arm = bpy.data.objects["TH_Armature"]
    grow.animate(arm)
    report = checks.validate()
    print("LESSON_REPORT", report)
    os.makedirs(os.path.dirname(BLEND), exist_ok=True)
    bpy.context.scene.frame_set(860)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)
    if report["problems"]:
        print("LESSON_SKIP stills; checks failed")
        sys.exit(1)
    render_stills()
    return report


def _probe():
    return os.path.join(os.path.dirname(FFMPEG), "ffprobe.exe")


def _duration(path):
    out = subprocess.check_output(
        [_probe(), "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
        text=True,
    )
    return float(out.strip())


def _video_ok(path):
    if not os.path.isfile(path) or os.path.getsize(path) < 100000:
        return False
    if os.path.isfile(BLEND) and os.path.getmtime(path) + 1 < os.path.getmtime(BLEND):
        return False
    try:
        dur = _duration(path)
    except (subprocess.CalledProcessError, OSError, ValueError):
        return False
    return dur > 29.0


def _subtitle_filter(path):
    escaped = os.path.abspath(path).replace("\\", "/").replace(":", "\\:")
    style = (
        "Alignment=2,FontName=Arial,FontSize=16,MarginL=70,MarginR=70,MarginV=26,"
        "BorderStyle=3,Outline=6,Shadow=0,PrimaryColour=&H00FFFFFF,OutlineColour=&HAA101410"
    )
    return "subtitles='%s':force_style='%s'" % (escaped, style)


def _mux(silent, rows):
    _refuse(LESSON_MP4)
    _refuse(APP_MP4)
    _refuse(silent)
    srt = speech.SRT
    parts, labels = [], []
    for i, row in enumerate(rows):
        lab = "a%d" % i
        delay = int(round(float(row["start"]) * 1000))
        parts.append(
            "[%d:a]aresample=48000,aformat=channel_layouts=stereo,adelay=%d:all=1,apad=pad_dur=30[%s]"
            % (i + 1, delay, lab)
        )
        labels.append("[%s]" % lab)
    mix = (
        ";".join(parts)
        + ";"
        + "".join(labels)
        + "amix=inputs=%d:duration=longest:dropout_transition=0:normalize=0,atrim=0:30,apad=whole_dur=30[a]"
        % len(rows)
    )
    os.makedirs(os.path.dirname(LESSON_MP4), exist_ok=True)
    staged = LESSON_MP4 + ".muxing.mp4"
    cmd = [FFMPEG, "-y", "-i", silent]
    for row in rows:
        cmd.extend(["-i", row["wav"]])
    cmd.extend([
        "-filter_complex", mix,
        "-vf", _subtitle_filter(srt),
        "-map", "0:v:0",
        "-map", "[a]",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "18",
        "-c:a", "aac",
        "-b:a", "160k",
        "-t", "30",
        "-movflags", "+faststart",
        staged,
    ])
    subprocess.check_call(cmd)
    if not _video_ok(staged):
        raise SystemExit("muxed lesson is not a 30 second video")
    os.replace(staged, LESSON_MP4)
    os.makedirs(os.path.dirname(APP_MP4), exist_ok=True)
    shutil.copy2(LESSON_MP4, APP_MP4)
    print("LESSON_VIDEO", LESSON_MP4, APP_MP4, "duration", round(_duration(LESSON_MP4), 3))


def stills_only():
    _refuse(BLEND)
    if not os.path.isfile(BLEND):
        raise SystemExit("lesson blend missing")
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    render_stills()


def video():
    _refuse(BLEND)
    _refuse(LESSON_MP4)
    _refuse(APP_MP4)
    timing = speech.load()
    if not os.path.isfile(BLEND):
        raise SystemExit("lesson blend missing")
    if not _video_ok(SILENT_MP4):
        bpy.ops.wm.open_mainfile(filepath=BLEND)
        silent = render_lesson(900)
    else:
        silent = SILENT_MP4
        print("SILENT_REUSE", silent, round(_duration(silent), 3))
    _refuse(silent)
    _mux(silent, timing["lines"])


if __name__ == "__main__":
    if PHASE == "video":
        video()
    elif PHASE == "stills":
        stills_only()
    else:
        build()
