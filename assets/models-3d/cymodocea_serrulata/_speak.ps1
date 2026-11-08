$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Speech

$root = "d:\pepot\marinesee\assets\models-3d\cymodocea_serrulata"
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
    if ($Text.Length -le 48) { return $Text }
    $cut = $Text.LastIndexOf(" ", [Math]::Min(48, $Text.Length - 1))
    if ($cut -lt 16) { return $Text }
    return $Text.Substring(0, $cut) + "\N" + $Text.Substring($cut + 1)
}

$cues = @(
    @{ id = "name"; text = "This is serrated ribbon seagrass, Cymodocea serrulata."; say = 'This is serrated ribbon seagrass, <phoneme alphabet="x-microsoft-sapi" ph="S IH M AH D OW S IY AH">Cymodocea</phoneme> <phoneme alphabet="x-microsoft-sapi" ph="S EH R UW L AA T AH">serrulata</phoneme>.'; gap = 0.36 },
    @{ id = "display"; text = "It is a display, not a scan of a meadow in Mati."; say = "It is a display, not a scan of a meadow in Mati."; gap = 0.55 },
    @{ id = "strap"; text = "The leaf is a flat strap, wider than smooth ribbon seagrass."; say = "The leaf is a flat strap, wider than smooth ribbon seagrass."; gap = 0.32 },
    @{ id = "eye"; text = "Run your eye to the tip."; say = "Run your eye to the tip."; gap = 0.28 },
    @{ id = "serrated"; text = "The edge is serrated."; say = "The edge is serrated."; gap = 0.55 },
    @{ id = "sheath"; text = "The sheath is broadly triangular."; say = "The sheath is broadly triangular."; gap = 0.34 },
    @{ id = "stem"; text = "Then look at the stem."; say = "Then look at the stem."; gap = 0.30 },
    @{ id = "scars"; text = "The leaf scars do not form a closed ring."; say = "The leaf scars do not form a closed ring."; gap = 0.42 },
    @{ id = "separate"; text = "That open scar line is how you separate this plant from smooth ribbon seagrass."; say = "That open scar line is how you separate this plant from smooth ribbon seagrass."; gap = 0.55 },
    @{ id = "patch"; text = "The patch spreads as the buried stem grows through the sand."; say = "The patch spreads as the buried stem grows through the sand."; gap = 0.32 },
    @{ id = "roots"; text = "Roots grow down at each node."; say = "Roots grow down at each node."; gap = 0.30 },
    @{ id = "seed"; text = "It can also flower and set seed."; say = "It can also flower and set seed."; gap = 0.20 }
)

$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$synth.Rate = 0
try {
    $synth.SelectVoice("Microsoft David Desktop")
    $voiceName = "Microsoft David Desktop"
} catch {
    $synth.SelectVoice("Microsoft Zira Desktop")
    $voiceName = "Microsoft Zira Desktop"
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
    $spoke = $false
    try {
        $synth.SpeakSsml($ssml)
        $spoke = $true
    } catch {
        Write-Output "SSML_FALLBACK $($cue.id) $($_.Exception.Message)"
        $synth.SetOutputToNull()
        if (Test-Path $path) { Remove-Item $path -Force }
        $synth.SetOutputToWaveFile($path)
        $synth.Speak($cue.text)
        $spoke = $true
    }
    $synth.SetOutputToNull()
    if (-not $spoke -or -not (Test-Path $path)) { throw "missing wav $($cue.id)" }
}

$chosen = 0
if ($env:ASSEMBLE_ONLY -ne "1") {
    $sum = 0.0
    for ($i = 0; $i -lt $cues.Count; $i++) {
        $path = Join-Path $work ("cue_{0:d2}.wav" -f $i)
        Speak-One $cues[$i] $chosen $path
        $info = Get-WavInfo $path
        $sum += $info.Seconds
    }
    Write-Output ("RATE {0} SPEECH {1:N2}" -f $chosen, $sum)
}

$infos = @()
$speech = 0.0
for ($i = 0; $i -lt $cues.Count; $i++) {
    $info = Get-WavInfo (Join-Path $work ("cue_{0:d2}.wav" -f $i))
    $infos += $info
    $speech += $info.Seconds
}
$gapSum = 0.0
foreach ($cue in $cues) { $gapSum += [double]$cue.gap }
$lead = 0.10
$tail = 0.20
# Keep the written pauses. Do not speed the voice up to force 30 seconds.
$scale = 1.0
Write-Output ("GAP_SCALE {0:N3} SPEECH {1:N2}" -f $scale, $speech)

$rate = $infos[0].Rate
$channels = $infos[0].Channels
$bits = $infos[0].Bits
$block = $channels * ($bits / 8)
$silenceUnit = New-Object byte[] $block

$chunks = New-Object System.Collections.Generic.List[byte[]]
$leadBytes = New-Object byte[] ([int][Math]::Round($lead * $rate) * $block)
$chunks.Add($leadBytes)

$timeline = @()
$cursor = $lead
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
    $gap = [double]$cues[$i].gap * $scale
    $cursor += $gap
    if ($i -lt ($cues.Count - 1)) {
        $gapBytes = New-Object byte[] ([int][Math]::Round($gap * $rate) * $block)
        $chunks.Add($gapBytes)
    }
}
$endAt = [Math]::Max(30.0, $cursor + $tail)
$tailBytes = New-Object byte[] ([int][Math]::Round(($endAt - $cursor) * $rate) * $block)
if ($tailBytes.Length -gt 0) { $chunks.Add($tailBytes) }
$cursor = $endAt

$ms = New-Object System.IO.MemoryStream
foreach ($chunk in $chunks) { $ms.Write($chunk, 0, $chunk.Length) }
$data = $ms.ToArray()
$wavPath = Join-Path $root "lesson_voice.wav"
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

$jsonPath = Join-Path $root "lesson_timing.json"
$payload = [ordered]@{
    voice = $voiceName
    pace = $chosen
    duration = [Math]::Round($cursor, 3)
    cues = $timeline
}
$payload | ConvertTo-Json -Depth 5 | Set-Content -Path $jsonPath -Encoding utf8

$assPath = Join-Path $root "lesson_voice.ass"
$ass = @"
[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Arial,46,&H00FFFFFF,&H000000FF,&H00101010,&H96000000,-1,0,0,0,100,100,0,0,3,0,0,2,70,70,62,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"@
foreach ($cue in $timeline) {
    $line = Wrap-Cue $cue.text
    $ass += "`r`nDialogue: 0,$($(Format-Ass $cue.start)),$($(Format-Ass $cue.end)),Sub,,0,0,0,,$line"
}
Set-Content -Path $assPath -Value $ass -Encoding utf8
Write-Output "VOICE_DONE $wavPath"
Write-Output ("DURATION {0:N2}" -f (Get-WavInfo $wavPath).Seconds)
foreach ($cue in $timeline) {
    Write-Output ("CUE {0} {1:N2}-{2:N2} {3}" -f $cue.id, $cue.start, $cue.end, $cue.text)
}

$ffmpeg = "C:\Users\reaga\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.1-full_build\bin\ffmpeg.exe"
$ffprobe = Join-Path (Split-Path $ffmpeg) "ffprobe.exe"
$picture = "C:\Users\reaga\AppData\Local\Temp\cs_serrulata_steady.mp4"
$speciesOut = Join-Path $root "cymodocea_serrulata_lesson.mp4"
$appOut = "d:\pepot\marinesee\app\assets\models-3d\cymodocea_serrulata_lesson.mp4"
$staged = Join-Path $root "cymodocea_serrulata_lesson.muxing.mp4"
if (-not (Test-Path $picture)) { throw "missing steady picture $picture" }
if (-not (Test-Path $ffmpeg)) { throw "missing ffmpeg $ffmpeg" }

$voiceSeconds = (Get-WavInfo $wavPath).Seconds
$probed = & $ffprobe -v error -show_entries format=duration -of csv=p=0 $picture
if ($LASTEXITCODE -ne 0) { throw "ffprobe failed for $picture" }
$pictureSeconds = [double](($probed | Out-String).Trim())
# Keep the spoken pace. Hold the last frame only when the words run past the picture.
$outSeconds = [Math]::Max($pictureSeconds, $voiceSeconds)
$extra = [Math]::Max(0.0, $outSeconds - $pictureSeconds)
$inv = [System.Globalization.CultureInfo]::InvariantCulture
$extraText = $extra.ToString("0.000", $inv)
$outText = $outSeconds.ToString("0.000", $inv)
$escaped = ($assPath -replace "\\", "/") -replace ":", "\:"
$filter = "[0:v]tpad=stop_mode=clone:stop_duration=${extraText},subtitles='${escaped}'[v];[1:a]apad[a]"

if (Test-Path $staged) { Remove-Item $staged -Force }
& $ffmpeg -y -i $picture -i $wavPath `
    -filter_complex $filter `
    -map "[v]" -map "[a]" `
    -c:v libx264 -pix_fmt yuv420p -crf 18 `
    -c:a aac -b:a 160k -ac 1 `
    -t $outText -movflags +faststart `
    $staged
if ($LASTEXITCODE -ne 0) { throw "ffmpeg mux failed: $LASTEXITCODE" }

Copy-Item $staged $speciesOut -Force
Copy-Item $staged $appOut -Force
Remove-Item $staged -Force
$speciesSize = (Get-Item $speciesOut).Length
$appSize = (Get-Item $appOut).Length
Write-Output "MUX_DONE $speciesOut"
Write-Output "MUX_COPY $appOut"
Write-Output "SIZES $speciesSize $appSize"
if ($speciesSize -ne $appSize) { throw "lesson copies differ" }
