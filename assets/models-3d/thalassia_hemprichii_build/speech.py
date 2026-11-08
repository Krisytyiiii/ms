"""English lesson speech for Thalassia hemprichii only.

Uses a desktop voice already installed on this PC. Does not download a voice
and does not list the installed voices. The words are the plan script.
"""

import json
import os
import subprocess
import wave

TIMING = os.path.join(os.path.dirname(__file__), "speech_timing.json")
SPEECH = r"C:\Users\reaga\AppData\Local\Temp\th_hemprichii_speech"
SRT = os.path.join(SPEECH, "captions.srt")

# Spoken in this order. Joined, they are the plan script.
LINES = (
    ("This is sickle seagrass, Thalassia hemprichii.", "name"),
    ("A display, not a scan of a meadow in Mati.", "plain"),
    ("The leaves are curved ribbons, not straight straps.", "curved"),
    ("In the blade you can see short black bars.", "bars"),
    ("Those are tannin cells.", "plain"),
    ("The rhizome is thick, with scars between the shoots.", "plain"),
    ("The patch spreads when that buried stem grows and sends up new shoots.", "plain"),
    ("Roots grow down at the nodes.", "plain"),
    ("It can also flower and set seed.", "plain"),
)

# Pause after each line. The long pause is the one before the black bars.
GAPS = (0.32, 0.36, 0.75, 0.26, 0.32, 0.28, 0.24, 0.22, 0.0)
LEAD = 0.22
VOICES = (
    "Microsoft David Desktop",
    "Microsoft Zira Desktop",
    "Microsoft David",
    "Microsoft Zira",
)


def _duration(path):
    with wave.open(path, "rb") as handle:
        return handle.getnframes() / float(handle.getframerate())


def _ssml(text, kind):
    body = text
    if kind == "curved":
        body = body.replace("curved", '<prosody rate="55%">curved</prosody>', 1)
    elif kind == "bars":
        body = body.replace("black bars", '<prosody rate="55%">black bars</prosody>', 1)
    else:
        return None
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">'
        + body
        + "</speak>"
    )


def _speak_file(voice, rate, wav, text, kind):
    os.makedirs(SPEECH, exist_ok=True)
    script = wav + ".ps1"
    text_path = wav + ".txt"
    ssml_path = wav + ".ssml"
    ssml = _ssml(text, kind)
    with open(text_path, "w", encoding="utf-8") as handle:
        handle.write(text)
    if ssml:
        with open(ssml_path, "w", encoding="utf-8") as handle:
            handle.write(ssml)
    ps = "\n".join([
        "Add-Type -AssemblyName System.Speech",
        "$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer",
        "$synth.SelectVoice('%s')" % voice.replace("'", "''"),
        "$synth.Rate = %d" % int(rate),
        "$synth.Volume = 100",
        "$synth.SetOutputToWaveFile('%s')" % wav.replace("'", "''"),
        "$plain = Get-Content -LiteralPath '%s' -Raw -Encoding UTF8" % text_path.replace("'", "''"),
        (
            "try { $synth.SpeakSsml((Get-Content -LiteralPath '%s' -Raw -Encoding UTF8)) } catch { Write-Output 'SSML_FALLBACK'; $synth.Speak($plain) }"
            % ssml_path.replace("'", "''")
        ) if ssml else "$synth.Speak($plain)",
        "$synth.Dispose()",
    ])
    with open(script, "w", encoding="utf-8-sig") as handle:
        handle.write(ps)
    subprocess.check_call(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script]
    )
    return wav


def _pick_voice():
    probe = os.path.join(SPEECH, "_voice_probe.wav")
    errors = []
    for voice in VOICES:
        try:
            _speak_file(voice, -2, probe, "Sickle seagrass.", "plain")
            if os.path.isfile(probe) and os.path.getsize(probe) > 1000:
                print("SPEECH_VOICE", voice)
                return voice
        except subprocess.CalledProcessError as exc:
            errors.append("%s (%s)" % (voice, exc.returncode))
    raise SystemExit("no English desktop voice: " + "; ".join(errors))


def _render_lines(voice):
    wavs = []
    durations = []
    for index, (text, kind) in enumerate(LINES):
        rate = 2 if kind in ("curved", "bars") else 4
        wav = os.path.join(SPEECH, "line_%d.wav" % index)
        _speak_file(voice, rate, wav, text, kind)
        dur = _duration(wav)
        print("SPEECH_LINE", index, round(dur, 2), text)
        wavs.append(wav)
        durations.append(dur)
    return wavs, durations


def _schedule(durations):
    gaps = list(GAPS)
    speech = sum(durations)
    total = LEAD + speech + sum(gaps)
    if total > 29.0:
        spare = 29.0 - LEAD - speech
        if spare < 2.0:
            return None
        bars = max(0.55, min(gaps[2], spare * 0.34))
        rest = spare - bars
        others = [g for i, g in enumerate(gaps) if i != 2]
        scale = rest / sum(others) if sum(others) else 1.0
        gaps = [g * scale for g in gaps]
        gaps[2] = bars
        total = LEAD + speech + sum(gaps)
    elif total < 26.2:
        extra = 26.2 - total
        gaps[2] += extra * 0.40
        share = extra * 0.60 / 7.0
        for i in range(8):
            if i != 2:
                gaps[i] += share
    cursor = LEAD
    rows = []
    for index, ((text, _kind), dur, wav) in enumerate(zip(LINES, durations, [])):
        rows.append({"text": text, "start": cursor, "end": cursor + dur})
        cursor += dur + gaps[index]
    return rows, cursor


def _schedule_with_wavs(wavs, durations):
    gaps = list(GAPS)
    speech = sum(durations)
    total = LEAD + speech + sum(gaps)
    if total > 29.0:
        spare = 29.0 - LEAD - speech
        if spare < 2.0:
            return None
        bars = max(0.55, min(gaps[2], spare * 0.34))
        rest = max(0.2, spare - bars)
        others = sum(g for i, g in enumerate(gaps) if i != 2)
        scale = rest / others if others else 1.0
        gaps = [g * scale for g in gaps]
        gaps[2] = bars
    elif total < 26.2:
        extra = 26.2 - total
        gaps[2] += extra * 0.40
        share = extra * 0.60 / 7.0
        for i in range(8):
            if i != 2:
                gaps[i] += share
    cursor = LEAD
    rows = []
    for index, ((text, _kind), dur, wav) in enumerate(zip(LINES, durations, wavs)):
        end = cursor + dur
        show = end
        rows.append({
            "text": text,
            "start": round(cursor, 3),
            "end": round(end, 3),
            "wav": wav,
        })
        cursor = end + gaps[index]
    for index, row in enumerate(rows):
        if index + 1 < len(rows):
            row["show_end"] = round(rows[index + 1]["start"], 3)
        else:
            row["show_end"] = round(min(29.6, row["end"] + 0.45), 3)
    return rows, cursor


def _write_srt(rows):
    def stamp(t):
        ms = int(round(max(0.0, t) * 1000))
        h, ms = divmod(ms, 3600000)
        m, ms = divmod(ms, 60000)
        s, ms = divmod(ms, 1000)
        return "%02d:%02d:%02d,%03d" % (h, m, s, ms)

    os.makedirs(SPEECH, exist_ok=True)
    blocks = []
    for index, row in enumerate(rows, start=1):
        blocks.append("%d\n%s --> %s\n%s\n" % (index, stamp(row["start"]), stamp(row["show_end"]), row["text"]))
    with open(SRT, "w", encoding="utf-8") as handle:
        handle.write("\n".join(blocks))
    return SRT


def _fresh():
    if not os.path.isfile(TIMING):
        return False
    with open(TIMING, encoding="utf-8") as handle:
        data = json.load(handle)
    rows = data.get("lines") or []
    texts = [text for text, _kind in LINES]
    if [row.get("text") for row in rows] != texts:
        return False
    return all(os.path.isfile(row.get("wav", "")) for row in rows)


def load():
    with open(TIMING, encoding="utf-8") as handle:
        return json.load(handle)


def ensure():
    if _fresh():
        data = load()
        _write_srt(data["lines"])
        print("SPEECH_REUSE", data.get("voice"), "tail", data.get("tail"))
        return data
    os.makedirs(SPEECH, exist_ok=True)
    voice = _pick_voice()
    wavs, durations = _render_lines(voice)
    packed = _schedule_with_wavs(wavs, durations)
    if packed is None:
        print("SPEECH_FASTER")
        wavs = []
        durations = []
        for index, (text, kind) in enumerate(LINES):
            rate = 5 if kind in ("curved", "bars") else 7
            wav = os.path.join(SPEECH, "line_%d.wav" % index)
            _speak_file(voice, rate, wav, text, kind)
            durations.append(_duration(wav))
            wavs.append(wav)
        packed = _schedule_with_wavs(wavs, durations)
    if packed is None:
        raise SystemExit("speech does not fit 30 seconds")
    rows, tail = packed
    if tail > 29.4:
        raise SystemExit("speech tail %.2f is past 29.4 seconds" % tail)
    data = {"voice": voice, "tail": round(tail, 3), "lines": rows, "srt": _write_srt(rows)}
    with open(TIMING, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)
    print("SPEECH_TAIL", round(tail, 3))
    return data


if __name__ == "__main__":
    ensure()
