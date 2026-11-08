"""Speak the lesson with an English voice already on this PC. No download."""

import json
import os
import subprocess
import wave

from .script import BEATS, TIMINGS, WAV, assert_words

VOICES = (
    "Microsoft David Desktop",
    "Microsoft David",
    "Microsoft Zira Desktop",
    "Microsoft Zira",
)


def _ps_quote(text):
    return text.replace("'", "''")


def _speak_clip(path, text, rate):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tries = []
    for name in VOICES:
        tries.append(
            "try { $synth.SelectVoice('%s'); $chose = '%s' } catch { }"
            % (_ps_quote(name), _ps_quote(name))
        )
    body = "\n".join([
        "Add-Type -AssemblyName System.Speech",
        "$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer",
        "$chose = ''",
        "\n".join(tries),
        "if (-not $chose) { throw 'No David or Zira voice' }",
        "$synth.Rate = %d" % int(rate),
        "$synth.SetOutputToWaveFile('%s')" % _ps_quote(path),
        "$synth.Speak('%s')" % _ps_quote(text),
        "$synth.Dispose()",
        "Write-Output $chose",
    ])
    script = path + ".ps1"
    with open(script, "w", encoding="utf-8-sig") as handle:
        handle.write(body)
    out = subprocess.check_output(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script],
        text=True,
    )
    return out.strip().splitlines()[-1]


def _silence(nframes, sampwidth, nchannels):
    return b"\x00" * (nframes * sampwidth * nchannels)


def _read(path):
    with wave.open(path, "rb") as handle:
        params = handle.getparams()
        frames = handle.readframes(handle.getnframes())
    return params, frames


def build():
    assert_words()
    folder = os.path.dirname(WAV)
    os.makedirs(folder, exist_ok=True)
    cues = []
    pieces = []
    voice = ""
    clock = 0.0
    pending = None
    for index, (text, rate, pause, subtitle) in enumerate(BEATS):
        clip = os.path.join(folder, "beat_%02d.wav" % index)
        voice = _speak_clip(clip, text, rate)
        params, frames = _read(clip)
        seconds = len(frames) / (params.sampwidth * params.nchannels * params.framerate)
        start = clock
        clock += seconds
        pieces.append(frames)
        if pause > 0:
            gap = _silence(int(params.framerate * pause), params.sampwidth, params.nchannels)
            pieces.append(gap)
            clock += pause
        label = text if subtitle is None else subtitle
        if label:
            if pending is not None:
                cues.append(pending)
            pending = {"text": label, "start": round(start, 3), "end": round(clock, 3)}
        elif pending is not None:
            pending["end"] = round(clock, 3)
    if pending is not None:
        cues.append(pending)
    with wave.open(WAV, "wb") as handle:
        handle.setparams(params)
        handle.writeframes(b"".join(pieces))
    payload = {"voice": voice, "duration": round(clock, 3), "cues": cues}
    with open(TIMINGS, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    print("SPEECH", voice, "seconds", round(clock, 3))
    for cue in cues:
        print("CUE", round(cue["start"], 2), round(cue["end"], 2), cue["text"])
    return payload


if __name__ == "__main__":
    build()
