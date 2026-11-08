$ErrorActionPreference = "Stop"
$ffmpeg = "C:\Users\reaga\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.1-full_build\bin\ffmpeg.exe"
$ffprobe = Join-Path (Split-Path $ffmpeg) "ffprobe.exe"
$root = "d:\pepot\marinesee\assets\models-3d\cymodocea_rotundata"
$frames = "C:\Users\reaga\AppData\Local\Temp\cr_lesson_frames\f%04d.jpg"
$wav = Join-Path $root "speech\lesson_speech.wav"
$ass = Join-Path $root "speech\lesson.ass"
$species = Join-Path $root "video\cymodocea_rotundata_lesson.mp4"
$app = "d:\pepot\marinesee\app\assets\models-3d\cymodocea_rotundata_lesson.mp4"
$staged = Join-Path $root "cymodocea_rotundata_lesson.muxing.mp4"
$speechJson = Get-Content (Join-Path $root "speech\lesson_speech.json") -Raw -Encoding utf8 | ConvertFrom-Json
$inv = [System.Globalization.CultureInfo]::InvariantCulture
# These cuts are the camera beats already rendered into the 900 frames.
$old = @(0.0, 6.274, 12.117, 20.923, 30.0)
$new = @(0.0, [double]$speechJson.intro_end, [double]$speechJson.tip_end, [double]$speechJson.ring_end, [double]$speechJson.duration)
for ($i = 1; $i -lt $new.Count; $i++) {
    if ($new[$i] -le $new[$i - 1]) { throw "speech beats are not in order" }
}
$parts = @()
for ($i = 0; $i -lt 4; $i++) {
    $oldSpan = $old[$i + 1] - $old[$i]
    $newSpan = $new[$i + 1] - $new[$i]
    $factor = ($newSpan / $oldSpan).ToString("0.000000", $inv)
    $a = $old[$i].ToString("0.000", $inv)
    $b = $old[$i + 1].ToString("0.000", $inv)
    $parts += "[0:v]trim=start=${a}:end=${b},setpts=(PTS-STARTPTS)*${factor}[v$i]"
}
$escaped = ($ass -replace "\\", "/") -replace ":", "\:"
$dur = $new[4].ToString("0.000", $inv)
$filter = ($parts -join ";") + ";[v0][v1][v2][v3]concat=n=4:v=1:a=0[vcat];[vcat]fps=30,subtitles='${escaped}'[v]"

if (Test-Path $staged) { Remove-Item $staged -Force }
& $ffmpeg -y -framerate 30 -start_number 1 -i $frames -i $wav `
    -filter_complex $filter `
    -map "[v]" -map "1:a:0" `
    -c:v libx264 -pix_fmt yuv420p -crf 18 `
    -c:a aac -b:a 160k -ac 1 `
    -t $dur -movflags +faststart `
    $staged
if ($LASTEXITCODE -ne 0) { throw "ffmpeg mux failed: $LASTEXITCODE" }

Copy-Item $staged $species -Force
Copy-Item $staged $app -Force
Remove-Item $staged -Force

function Show-Movie($path) {
    $json = & $ffprobe -v error -show_entries "format=duration,size" -show_entries "stream=codec_type,codec_name,width,height,sample_rate,channels" -of json $path
    if ($LASTEXITCODE -ne 0) { throw "ffprobe failed $path" }
    Write-Output "FILE $path"
    Write-Output $json
}

Show-Movie $species
Show-Movie $app
$a = (Get-Item $species).Length
$b = (Get-Item $app).Length
Write-Output "SIZES $a $b"
if ($a -ne $b) { throw "lesson copies differ" }
