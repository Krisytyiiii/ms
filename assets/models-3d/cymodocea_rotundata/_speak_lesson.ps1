$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Speech

$root = "d:\pepot\marinesee\assets\models-3d\cymodocea_rotundata"
$work = Join-Path $root "voice_work"
New-Item -ItemType Directory -Force -Path $work | Out-Null

function Get-WavInfo([string]$Path) {
    $bytes = [System.IO.File]::ReadAllBytes($Path)
    if ($bytes.Length -lt 44) { throw "wav too small $Path" }
    $pos = 12
    $rate = 0
    $channels = 0
    $bits = 0
    $data = $null
    while (($pos + 8) -le $bytes.Length) {
        $id = [System.Text.Encoding]::ASCII.GetString($bytes, $pos, 4)
        $size = [BitConverter]::ToInt32($bytes, $pos + 4)
        $pos += 8
        if ($id -eq "fmt ") {
            $channels = [BitConverter]::ToInt16($bytes, $pos + 2)
            $rate = [BitConverter]::ToInt32($bytes, $pos + 4)
            $bits = [BitConverter]::ToInt16($bytes, $pos + 14)
        } elseif ($id -eq "data") {
            $data = New-Object byte[] $size
            [Array]::Copy($bytes, $pos, $data, 0, $size)
            break
        }
        if ($size -lt 0) { break }
        $pos += $size
        if (($size % 2) -eq 1) { $pos += 1 }
    }
    if ($null -eq $data) { throw "no data chunk in $Path" }
    $seconds = [double]$data.Length / ($rate * $channels * ($bits / 8.0))
    return @{ Rate = $rate; Channels = $channels; Bits = $bits; Data = $data; Seconds = $seconds }
}

function Format-Ass([double]$Time) {
    if ($Time -lt 0) { $Time = 0 }
    $cs = [int][Math]::Round($Time * 100.0)
    $total = [Math]::Floor($cs / 100)
    $frac = $cs % 100
    $sec = $total % 60
    $min = [Math]::Floor($total / 60) % 60
    $hour = [Math]::Floor($total / 3600)
    return "{0}:{1:00}:{2:00}.{3:00}" -f [int]$hour, [int]$min, [int]$sec, [int]$frac
}

function Wrap-Cue([string]$Text) {
    if ($Text.Length -le 42) { return $Text }
    $limit = 42
    $lines = New-Object System.Collections.Generic.List[string]
    $rest = $Text
    while ($rest.Length -gt $limit) {
        $cut = $rest.LastIndexOf(" ", [Math]::Min($limit, $rest.Length - 1))
        if ($cut -lt 12) { break }
        $lines.Add($rest.Substring(0, $cut))
        $rest = $rest.Substring($cut + 1)
    }
    $lines.Add($rest)
    return ($lines -join "\N")
}

# Same words as PLAN.md. Pauses sit between ideas. "rounded" and "closed ring" are spoken slowly.
$cues = @(
    @{ id = "name"; mark = ""; text = "This is smooth ribbon seagrass, Cymodocea rotundata."; say = 'This is smooth ribbon seagrass, <phoneme alphabet="x-microsoft-sapi" ph="S IH M AH D OW S IY AH">Cymodocea</phoneme> <phoneme alphabet="x-microsoft-sapi" ph="R OW T AH N D AA T AH">rotundata</phoneme>.'; gap = 0.42 },
    @{ id = "display"; mark = "intro"; text = "What you are seeing is a display, not a scan of a meadow in Mati."; say = "What you are seeing is a display, not a scan of a meadow in Mati."; gap = 0.72 },
    @{ id = "look"; mark = ""; text = "Look at the tip."; say = "Look at the tip."; gap = 0.38 },
    @{ id = "rounded"; mark = ""; text = "It is rounded and smooth."; say = "It is rounded and smooth."; gap = 0.42 },
    @{ id = "teeth"; mark = "tip"; text = "There are no teeth along the edge."; say = "There are no teeth along the edge."; gap = 0.78 },
    @{ id = "ring"; mark = ""; text = "On the short stem, the sheath scars join into a closed ring."; say = "On the short stem, the sheath scars join into a closed ring."; gap = 0.48 },
    @{ id = "tell"; mark = "ring"; text = "That ring is how you tell this plant from serrated ribbon seagrass, which does not close its scars."; say = "That ring is how you tell this plant from serrated ribbon seagrass, which does not close its scars."; gap = 0.78 },
    @{ id = "patch"; mark = ""; text = "The patch spreads when the buried stem grows through the sand and sends up new shoots."; say = "The patch spreads when the buried stem grows through the sand and sends up new shoots."; gap = 0.42 },
    @{ id = "roots"; mark = ""; text = "Roots grow down at each node."; say = "Roots grow down at each node."; gap = 0.40 },
    @{ id = "seed"; mark = ""; text = "The plant can also flower and set seed."; say = "The plant can also flower and set seed."; gap = 0.20 }
)

$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$names = @($synth.GetInstalledVoices() | ForEach-Object { $_.VoiceInfo.Name })
Write-Output ("VOICES " + ($names -join " | "))
$voiceName = "Microsoft David Desktop"
if ($names -contains "Microsoft David Desktop") {
    $synth.SelectVoice("Microsoft David Desktop")
} elseif ($names -contains "Microsoft Zira Desktop") {
    $voiceName = "Microsoft Zira Desktop"
    $synth.SelectVoice("Microsoft Zira Desktop")
} else {
    $english = $synth.GetInstalledVoices() | Where-Object { $_.VoiceInfo.Culture.Name -like "en*" } | Select-Object -First 1
    if ($null -eq $english) { throw "no English voice installed" }
    $voiceName = $english.VoiceInfo.Name
    $synth.SelectVoice($voiceName)
}
Write-Output "VOICE $voiceName"

function Speak-One($cue, $rateValue, $path) {
    $synth.Rate = [int]$rateValue
    if (Test-Path $path) { Remove-Item $path -Force }
    $ssml = @"
<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
$($cue.say)
</speak>
"@
    $synth.SetOutputToWaveFile($path)
    try {
        $synth.SpeakSsml($ssml)
    } catch {
        Write-Output "SSML_FALLBACK $($cue.id) $($_.Exception.Message)"
        $synth.SetOutputToNull()
        if (Test-Path $path) { Remove-Item $path -Force }
        $synth.SetOutputToWaveFile($path)
        $synth.Speak($cue.text)
    }
    $synth.SetOutputToNull()
    if (-not (Test-Path $path)) { throw "missing wav $($cue.id)" }
}

# Rate 0 is the normal Windows pace. Do not speed the voice up to force 30 seconds.
$chosen = 0
$sum = 0.0
for ($i = 0; $i -lt $cues.Count; $i++) {
    $path = Join-Path $work ("cue_{0:d2}.wav" -f $i)
    Speak-One $cues[$i] $chosen $path
    $info = Get-WavInfo $path
    $sum += $info.Seconds
}
Write-Output ("RATE {0} SPEECH {1:N2}" -f $chosen, $sum)

$infos = @()
$speech = 0.0
for ($i = 0; $i -lt $cues.Count; $i++) {
    $info = Get-WavInfo (Join-Path $work ("cue_{0:d2}.wav" -f $i))
    $infos += $info
    $speech += $info.Seconds
}
$gapSum = 0.0
foreach ($cue in $cues) { $gapSum += [double]$cue.gap }
$lead = 0.25
# Keep the written pauses. The film can run past 30 seconds.
$scale = 1.0
Write-Output ("GAP_SCALE {0:N3} SPEECH {1:N2}" -f $scale, $speech)

$rate = $infos[0].Rate
$channels = $infos[0].Channels
$bits = $infos[0].Bits
$block = $channels * ($bits / 8)
$chunks = New-Object System.Collections.Generic.List[byte[]]
$leadBytes = New-Object byte[] ([int][Math]::Round($lead * $rate) * $block)
$chunks.Add($leadBytes)

$timeline = @()
$cursor = $lead
$introEnd = 0.0
$tipEnd = 0.0
$ringEnd = 0.0
for ($i = 0; $i -lt $cues.Count; $i++) {
    $chunks.Add($infos[$i].Data)
    $start = $cursor
    $cursor += $infos[$i].Seconds
    $timeline += [ordered]@{
        id = $cues[$i].id
        text = $cues[$i].text
        start = [Math]::Round($start, 3)
        end = [Math]::Round($cursor, 3)
    }
    if ($cues[$i].mark -eq "intro") { $introEnd = $cursor }
    if ($cues[$i].mark -eq "tip") { $tipEnd = $cursor }
    if ($cues[$i].mark -eq "ring") { $ringEnd = $cursor }
    $gap = [double]$cues[$i].gap * $scale
    $cursor += $gap
    if ($i -lt ($cues.Count - 1)) {
        $gapBytes = New-Object byte[] ([int][Math]::Round($gap * $rate) * $block)
        $chunks.Add($gapBytes)
    }
}
$lastGap = [double]$cues[$cues.Count - 1].gap * $scale
$audioAt = $cursor - $lastGap
$cursor += 0.35
$tail = [Math]::Max(0.0, $cursor - $audioAt)
$tailBytes = New-Object byte[] ([int][Math]::Round($tail * $rate) * $block)
if ($tailBytes.Length -gt 0) { $chunks.Add($tailBytes) }

$ms = New-Object System.IO.MemoryStream
foreach ($chunk in $chunks) { $ms.Write($chunk, 0, $chunk.Length) }
$data = $ms.ToArray()
$wavPath = Join-Path $root "lesson_speech.wav"
$fs = [System.IO.File]::Create($wavPath)
$bw = New-Object System.IO.BinaryWriter($fs)
function Write-Ascii([System.IO.BinaryWriter]$w, [string]$s) {
    $w.Write([System.Text.Encoding]::ASCII.GetBytes($s))
}
Write-Ascii $bw "RIFF"
$bw.Write([int](36 + $data.Length))
Write-Ascii $bw "WAVE"
Write-Ascii $bw "fmt "
$bw.Write([int]16)
$bw.Write([int16]1)
$bw.Write([int16]$channels)
$bw.Write([int]$rate)
$bw.Write([int]($rate * $block))
$bw.Write([int16]$block)
$bw.Write([int16]$bits)
Write-Ascii $bw "data"
$bw.Write([int]$data.Length)
$bw.Write($data)
$bw.Close()
$fs.Close()

$jsonPath = Join-Path $root "lesson_speech.json"
$cueJson = ($timeline | ForEach-Object {
    '    {"start": ' + $_.start + ', "end": ' + $_.end + ', "text": ' + ($_.text | ConvertTo-Json) + '}'
}) -join ",`r`n"
$json = @"
{
  "voice": "$voiceName",
  "rate": $chosen,
  "duration": $([Math]::Round($cursor, 3)),
  "intro_end": $([Math]::Round($introEnd, 3)),
  "tip_end": $([Math]::Round($tipEnd, 3)),
  "ring_end": $([Math]::Round($ringEnd, 3)),
  "cues": [
$cueJson
  ]
}
"@
Set-Content -Path $jsonPath -Value $json -Encoding utf8

$assPath = Join-Path $root "lesson.ass"
$ass = @"
[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Arial,46,&H00FFFFFF,&H000000FF,&H00101010,&H96000000,-1,0,0,0,100,100,0,0,3,0,0,2,80,80,56,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"@
foreach ($cue in $timeline) {
    $line = Wrap-Cue $cue.text
    $ass += "`r`nDialogue: 0,$(Format-Ass $cue.start),$(Format-Ass $cue.end),Sub,,0,0,0,,$line"
}
Set-Content -Path $assPath -Value $ass -Encoding utf8
$spoken = (Get-WavInfo $wavPath).Seconds
Write-Output "VOICE_DONE $wavPath"
Write-Output ("DURATION {0:N3} INTRO {1:N3} TIP {2:N3} RING {3:N3}" -f $spoken, $introEnd, $tipEnd, $ringEnd)
