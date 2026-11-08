$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Speech

$outDir = "D:\pepot\marinesee\assets\models-3d\enhalus_acoroides_build\speech"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$voice = $null
foreach ($name in @("Microsoft David Desktop", "Microsoft Zira Desktop")) {
    try {
        $synth.SelectVoice($name)
        $voice = $name
        break
    } catch {
        $voice = $null
    }
}
if (-not $voice) {
    throw "Microsoft David Desktop and Microsoft Zira Desktop are both missing"
}
Write-Output "USING $voice"

# rate is the SAPI rate (-10..10). gap is silence after the phrase, in seconds.
# A slower rate is only on the two features that separate this plant.
$phrases = @(
    @{ text = "This is tape seagrass, Enhalus acoroides."; rate = 3; gap = 0.36 },
    @{ text = "A display, not a scan of a meadow in Mati."; rate = 3; gap = 0.40 },
    @{ text = "The leaves are very long ribbons."; rate = 2; gap = 0.22 },
    @{ text = "Their edges "; rate = 2; gap = 0.02 },
    @{ text = "roll inward."; rate = -2; gap = 0.28 },
    @{ text = "They are not the short flat straps of the ribbon seagrasses."; rate = 3; gap = 0.55 },
    @{ text = "The rhizome is thick, with long "; rate = 2; gap = 0.02 },
    @{ text = "black bristles"; rate = -2; gap = 0.04 },
    @{ text = ", and the roots are cord-like."; rate = 2; gap = 0.28 },
    @{ text = "The meadow spreads by that thick buried stem."; rate = 3; gap = 0.24 },
    @{ text = "Male and female flowers grow on separate plants."; rate = 3; gap = 0.22 },
    @{ text = "This model does not show the flowers."; rate = 3; gap = 0.16 }
)

$synth.Volume = 100
$i = 0
foreach ($phrase in $phrases) {
    $wav = Join-Path $outDir ("p{0:d2}.wav" -f $i)
    $synth.Rate = [int]$phrase.rate
    $synth.SetOutputToWaveFile($wav)
    $synth.Speak($phrase.text)
    $synth.SetOutputToNull()
    Write-Output ("PHRASE {0} rate {1} gap {2} {3}" -f $i, $phrase.rate, $phrase.gap, $phrase.text)
    $i++
}
$synth.Dispose()
Write-Output "SPOKEN $i"
