"""Burn the spoken words onto the lesson film and add the voice. No music."""

import os
import shutil
import subprocess
import sys

ROOT = r"D:\pepot\marinesee"
SPEECH = os.path.join(ROOT, r"assets\models-3d\enhalus_acoroides_build\speech")
VIDEO = os.path.join(ROOT, r"assets\models-3d\enhalus_acoroides\enhalus_acoroides_lesson.mp4")
APP = os.path.join(ROOT, r"app\assets\models-3d\enhalus_acoroides_lesson.mp4")
WAV = os.path.join(SPEECH, "lesson.wav")
SRT = os.path.join(SPEECH, "lesson.srt")
OUT = os.path.join(SPEECH, "lesson_muxed.mp4")


def run(args):
    print("RUN", " ".join(args))
    done = subprocess.run(args, capture_output=True, text=True)
    if done.stdout:
        print(done.stdout[-2000:])
    if done.returncode != 0:
        print(done.stderr[-4000:])
        raise SystemExit(done.returncode)
    return done


def probe(path):
    done = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-show_entries", "stream=codec_type,width,height", "-of", "default=nw=1", path],
        capture_output=True,
        text=True,
    )
    print(path)
    print(done.stdout)
    if done.returncode != 0:
        print(done.stderr[-2000:])
        raise SystemExit("ffprobe failed")
    return done.stdout


def esc(path):
    return path.replace("\\", "/").replace(":", "\\:")


def main():
    if not os.path.isfile(VIDEO) or os.path.getsize(VIDEO) < 100000:
        raise SystemExit("silent lesson mp4 is missing or too small")
    probe(VIDEO)
    style = "Alignment=2,Fontname=Arial,Fontsize=28,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=3,Shadow=0,MarginV=52"
    vf = "subtitles='%s':force_style='%s'" % (esc(SRT), style)
    run([
        "ffmpeg", "-y",
        "-i", VIDEO,
        "-i", WAV,
        "-vf", vf,
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "160k",
        "-shortest",
        OUT,
    ])
    info = probe(OUT)
    if "codec_type=audio" not in info or "1920" not in info:
        raise SystemExit("muxed film is missing picture or voice")
    os.makedirs(os.path.dirname(APP), exist_ok=True)
    shutil.copy2(OUT, VIDEO)
    shutil.copy2(OUT, APP)
    print("PUBLISHED", VIDEO)
    print("PUBLISHED", APP)


if __name__ == "__main__":
    main()
