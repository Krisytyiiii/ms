$ErrorActionPreference = "Continue"
$blender = "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
$py = "d:\pepot\marinesee\assets\models-3d\cymodocea_serrulata\_build_lesson.py"
$out = "C:\Users\reaga\AppData\Local\Temp\cs_serrulata_frames"
New-Item -ItemType Directory -Force -Path $out | Out-Null
$env:CS_PHASE = "frames"
$env:CS_OUT = $out
for ($s = 1; $s -le 900; $s += 40) {
    $e = [Math]::Min(900, $s + 39)
    $dest = Join-Path $out ("frame_{0:d4}.jpg" -f $e)
    if (Test-Path $dest) {
        Write-Output "SKIP $s $e"
        continue
    }
    $env:CS_START = "$s"
    $env:CS_END = "$e"
    Write-Output "CHUNK $s $e"
    & $blender --background --python $py
    if (-not (Test-Path $dest)) {
        Write-Output "RETRY $s $e"
        & $blender --background --python $py
    }
    if (-not (Test-Path $dest)) {
        Write-Output "CHUNK_FAIL $s $e"
        exit 1
    }
    Write-Output "CHUNK_OK $s $e"
}
$count = (Get-ChildItem $out -Filter "frame_*.jpg").Count
Write-Output "ALL_FRAMES $count"
