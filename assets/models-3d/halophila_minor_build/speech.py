"""Speak the Halophila minor lesson with a voice already on this PC.

The words are the PLAN.md script. Subtitles use those same words.
No voice is downloaded. David or Zira is selected by name.
"""

import json
import os
import subprocess
import wave

FFPROBE = (
    r"C:\Users\reaga\AppData\Local\Microsoft\WinGet\Packages"
    r"\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
    r"\ffmpeg-9.0.1-full_build\bin\ffprobe.exe"
)
FFMPEG = FFPROBE.replace("ffprobe.exe", "ffmpeg.exe")
SPEECH_DIR = r"C:\Users\reaga\AppData\Local\Temp\hm_minor_speech"
TIMINGS = os.path.join(SPEECH_DIR, "timings.json")
MIX_WAV = os.path.join(SPEECH_DIR, "lesson.wav")
ASS_PATH = os.path.join(SPEECH_DIR, "subs.ass")

# Plain words, in order. These are also the bottom subtitles.
SENTENCES = (
    "This is small spoon seagrass, Halophila minor.",
    "A display, not a scan of a meadow in Mati.",
    "The leaves come up in pairs.",
    "Each one is a small oval, straight from the buried stem.",
    "There is no upright fan.",
    "The margin is smooth, and the sheath is wedge-shaped.",
    "The cross veins are fewer than eight pairs.",
    "That smaller leaf, and those fewer veins, are how you separate it from spoon seagrass, Halophila ovalis.",
    "The patch spreads as the buried stem grows.",
    "Roots grow down at the nodes.",
    "It can also flower and set seed.",
)

# Idea breaks. The vein sentence gets a longer pause in front of it.
PAUSE_AFTER = (0.34, 0.55, 0.28, 0.26, 0.24, 0.62, 0.32, 0.50, 0.30, 0.26, 0.20)
LEAD_IN = 0.22

TRANSCRIPT = (
    "This is small spoon seagrass, Halophila minor. "
    "A display, not a scan of a meadow in Mati.\n\n"
    "The leaves come up in pairs. "
    "Each one is a small oval, straight from the buried stem. "
    "There is no upright fan. "
    "The margin is smooth, and the sheath is wedge-shaped.\n\n"
    "The cross veins are fewer than eight pairs. "
    "That smaller leaf, and those fewer veins, are how you separate it from spoon seagrass, Halophila ovalis.\n\n"
    "The patch spreads as the buried stem grows. "
    "Roots grow down at the nodes. "
    "It can also flower and set seed."
)


def _ssml(text):
    body = (
        text.replace("pairs.", '<prosody rate="slow">pairs</prosody>.')
        .replace(
            "fewer than eight",
            '<prosody rate="x-slow">fewer than eight</prosody>',
        )
    )
    return (
        '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">'
        + body
        + "</speak>"
    )


def _duration(path):
    with wave.open(path, "rb") as handle:
        frames = handle.getnframes()
        rate = handle.getframerate() or 1
    return frames / float(rate)


def _speak_one(path, text, rate):
    ps1 = os.path.join(SPEECH_DIR, "speak.ps1")
    ssml_path = os.path.join(SPEECH_DIR, "line.ssml")
    with open(ssml_path, "w", encoding="utf-8-sig") as handle:
        handle.write(_ssml(text))
    with open(ps1, "w", encoding="utf-8") as handle:
        handle.write(
            "\n".join(
                [
                    "param([string]$Path, [string]$SsmlPath, [int]$Rate)",
                    "Add-Type -AssemblyName System.Speech",
                    "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer",
                    "$s.Rate = $Rate",
                    "$picked = $null",
                    "foreach ($name in @('Microsoft Zira Desktop', 'Microsoft David Desktop')) {",
                    "  try { $s.SelectVoice($name); $picked = $name; break } catch {}",
                    "}",
                    "if (-not $picked) { throw 'Microsoft Zira Desktop or Microsoft David Desktop is not installed' }",
                    "$ssml = Get-Content -Raw -Encoding UTF8 $SsmlPath",
                    "$s.SetOutputToWaveFile($Path)",
                    "$s.SpeakSsml($ssml)",
                    "$s.Dispose()",
                    "Write-Output $picked",
                    "",
                ]
            )
        )
    cmd = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        ps1,
        "-Path",
        path,
        "-SsmlPath",
        ssml_path,
        "-Rate",
        str(rate),
    ]
    last = None
    for _try in range(3):
        last = subprocess.run(cmd, capture_output=True, text=True)
        if last.returncode == 0 and os.path.isfile(path) and os.path.getsize(path) > 1000:
            return
    raise RuntimeError(last.stderr if last is not None else "speech failed")


def render_lines(rate=1):
    """Write one wav per sentence. Returns durations in seconds."""
    os.makedirs(SPEECH_DIR, exist_ok=True)
    durations = []
    for index, text in enumerate(SENTENCES):
        wav = os.path.join(SPEECH_DIR, "line_%02d.wav" % index)
        _speak_one(wav, text, rate)
        durations.append(_duration(wav))
        if durations[-1] < 0.25:
            raise RuntimeError("spoken line %d is empty" % index)
        print("SPEECH", index, "rate", rate, "sec", round(durations[-1], 2), text)
    return durations


def _fit_rate():
    """Zira at rate 4 still slows the two teaching phrases and leaves room for pauses."""
    rate = 4
    durations = render_lines(rate)
    spoken = sum(durations)
    print("SPEECH_TOTAL", "rate", rate, "spoken", round(spoken, 2))
    return rate, durations


def _timeline(durations, pauses):
    cursor = LEAD_IN
    rows = []
    for text, duration, pause in zip(SENTENCES, durations, pauses):
        start = cursor
        end = cursor + duration
        rows.append({"text": text, "start": round(start, 3), "end": round(end, 3)})
        cursor = end + pause
    return rows, cursor


def _scale_pauses(durations):
    spoken = sum(durations)
    room = 29.45 - LEAD_IN - spoken
    base = list(PAUSE_AFTER)
    # Keep a clear stop before the vein sentence (index 6).
    if room < sum(base):
        scale = max(0.35, room / sum(base))
        pauses = [value * scale for value in base]
        pauses[5] = max(pauses[5], min(0.45, room * 0.22))
    else:
        extra = room - sum(base)
        weight = (0.6, 1.4, 0.7, 0.6, 0.5, 1.8, 0.7, 1.2, 0.8, 0.6, 0.4)
        total_w = sum(weight)
        pauses = [base[i] + extra * weight[i] / total_w for i in range(len(base))]
    return pauses


def _silence(path, seconds, template):
    with wave.open(template, "rb") as source:
        params = source.getparams()
        rate = source.getframerate()
    frames = int(max(0.0, seconds) * rate)
    with wave.open(path, "wb") as target:
        target.setparams(params)
        width = params.sampwidth
        target.writeframes(b"\x00" * frames * params.nchannels * width)


def mix(rows):
    """One wav: lead-in, each sentence, and the pause after it."""
    template = os.path.join(SPEECH_DIR, "line_00.wav")
    parts = []
    lead = os.path.join(SPEECH_DIR, "lead.wav")
    _silence(lead, rows[0]["start"], template)
    parts.append(lead)
    for index, row in enumerate(rows):
        parts.append(os.path.join(SPEECH_DIR, "line_%02d.wav" % index))
        pause = 0.0 if index + 1 == len(rows) else rows[index + 1]["start"] - row["end"]
        if index + 1 == len(rows):
            pause = max(0.0, 30.0 - row["end"])
        gap = os.path.join(SPEECH_DIR, "gap_%02d.wav" % index)
        _silence(gap, pause, template)
        parts.append(gap)
    list_path = os.path.join(SPEECH_DIR, "concat.txt")
    with open(list_path, "w", encoding="utf-8") as handle:
        for part in parts:
            handle.write("file '%s'\n" % part.replace("\\", "/"))
    subprocess.check_call(
        [
            FFMPEG,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            list_path,
            "-c",
            "copy",
            MIX_WAV,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return MIX_WAV


def _ass_time(seconds):
    seconds = max(0.0, seconds)
    whole = int(seconds)
    hours, rem = divmod(whole, 3600)
    minutes, secs = divmod(rem, 60)
    centis = int(round((seconds - whole) * 100))
    if centis == 100:
        secs += 1
        centis = 0
    return "%d:%02d:%02d.%02d" % (hours, minutes, secs, centis)


def _wrap(text):
    if len(text) <= 62:
        return text
    cut = text.rfind(" ", 0, 62)
    if cut < 24:
        cut = text.find(" ", 40)
    if cut < 0:
        return text
    return text[:cut] + r"\N" + text[cut + 1 :]


def write_ass(rows):
    lines = [
        "[Script Info]",
        "ScriptType: v4.00+",
        "PlayResX: 1920",
        "PlayResY: 1080",
        "WrapStyle: 0",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        "Style: Sub,Arial,48,&H00FFFFFF,&H000000FF,&H00000000,&H96000000,0,0,0,0,100,100,0,0,3,0,0,2,80,80,56,1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    for row in rows:
        lines.append(
            "Dialogue: 0,%s,%s,Sub,,0,0,0,,%s"
            % (_ass_time(row["start"]), _ass_time(row["end"]), _wrap(row["text"]))
        )
    with open(ASS_PATH, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")
    return ASS_PATH


def build():
    _rate, durations = _fit_rate()
    pauses = _scale_pauses(durations)
    rows, cursor = _timeline(durations, pauses)
    if cursor > 29.6:
        # Last resort: trim the tail pauses evenly and keep the vein stop.
        overflow = cursor - 29.45
        for index in range(len(pauses)):
            if index == 5:
                continue
            pauses[index] = max(0.12, pauses[index] - overflow / 10.0)
        rows, cursor = _timeline(durations, pauses)
    payload = {"voice_rate": _rate, "ends": round(cursor, 3), "sentences": rows, "transcript": TRANSCRIPT}
    with open(TIMINGS, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    mix(rows)
    write_ass(rows)
    print("SPEECH_READY", TIMINGS, "ends", round(cursor, 3))
    return payload


if __name__ == "__main__":
    build()
