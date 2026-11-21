# Evaluation gaps

**IMPLEMENTATION.** Read this before changing the MarineSee app. The user questionnaire is frozen at 29 statements in `MarineSee-Validation-Questions.txt`. Pass checks, statuses, and evidence live in `19-evaluation-question-spec.md`. This file is the open-work list so an app change does not skip a statement that is still `not-met` or `unmeasured`.

Snapshot copied from the spec (checked 16 Nov 2026, after on-device inference): **5 met, 0 not-met, 24 unmeasured.**

A high user-evaluation score is not available while any row is `not-met` or `unmeasured`.

## How an agent uses this file

1. Before editing `app/` or the evaluation docs, read this file and `19-evaluation-question-spec.md`.
2. Restyle screens freely. Keep every behavior a statement requires. Do not drop camera, gallery, the nine-species library, a result with a name and a percent, the retake sentence, profile fields, or rotate/zoom.
3. In the same edit that changes what a tester can do, update that row’s **Status** and **Evidence** in `19-evaluation-question-spec.md`, then update the lists and the snapshot line in this file.
4. `met` means a tester on a physical Android phone can do the pass check now. Code that only looks ready stays `not-met` or `unmeasured`.
5. Do not invent species text to close FS-6. Use a cited source, or leave `TBD — adviser source`.
6. Do not add security or maintainability items to the user questionnaire.

## Already met — do not break

| ID | Keep this true |
|----|----------------|
| FS-1 | Identify offers Camera and Gallery, and the chosen photo is previewed. |
| FS-2 | The library lists the nine scientific names from `11-species.md`. |
| RE-3 | After onboarding, Scan and Library are both reachable from the pill nav and its separate Scan button. |
| RE-5 | The library is still there after the app is closed and opened again. |
| RE-6 | Leaving a profile and opening it again shows the same field text. |

## Not implemented (`not-met`)

None. The last four — FS-3, FS-4, FS-5, US-4 — were blocked on identify needing the laptop API. On-device inference removed that blocker on 16 Nov 2026, so they moved to `unmeasured`: the app can do them, no tester has done them on the phone yet.

## Not shown on a phone (`unmeasured`)

These paths may already exist. They stay `unmeasured` until a tester does the pass check on a physical phone. Shipping a new layout does not mark them `met`.

| ID | What a phone pass still has to show |
|----|--------------------------------------|
| FS-3 | After a successful identify, the tester must open that species’ profile **and** an interactive 3D view. Identify no longer needs the laptop: `LocalClassifier` returns a slug offline and the Profile / 3D buttons follow that local result, so all nine species and their bundled `.glb`/`.mp4` are reachable with the phone in airplane mode. Pass check not yet done on a phone. |
| FS-4 | A finished identify must show the scientific name and a percent. `LocalClassifier` computes both from the bundled `assets/ml/svm_mobile.*` with no network. `app/test/local_parity_test.dart` runs decode → crop → 256px → 148 features → SVM on all nine bundled photos and asserts a slug plus a 0–100% confidence each time. Not yet seen on a phone. |
| FS-5 | A low-confidence result must tell the tester to take the photo again. The sentence is a notice in `result_screen.dart`; `LocalClassifier` sets it when the on-device confidence is under the exported threshold, which is locked at the frozen 0.44. The copy now adds "this may not be one of the nine species", and the scanner says only the nine Mati species are supported, because the SVM has no way to refuse a photo. Six of the nine bundled photos fall below it in the test, so the branch is reachable. Not yet seen on a phone. |
| US-4 | Same path as FS-5: the retake sentence is now reachable offline, but a tester has not read it on a phone and not said it was clear. The result screen also has "None of these" for a photo that is not one of the nine, which a tester has not tried. |
| FS-6 | Each profile field shows cited text for common name, botanical characteristics, ecological role, conservation status, and habitat. The text is in `species.json`. A tester has not opened a profile on a phone. |
| FS-7 | Rotate and zoom a bundled patch. All nine species have a `.glb` (clip `Grow`) and a lesson `.mp4`. The *Cymodocea rotundata* file is the new meadow: one rhizome with a few branches, 14 shoots across the sand, 34,542 triangles. The *Cymodocea serrulata* file is the same plot with serrated 9 mm straps, a triangular sheath, open scars, and 24,864 triangles. The *Halodule pinifolia* file is the same plot with fine leaves, a rounded tip where the dark vein splits in two, black scars on a pale rhizome, and 21,572 triangles. The *Halodule uninervis* file is the same plot with a wider leaf, one central vein, a trident tip, black scars on a pale ivory rhizome, and 20,804 triangles. The *Syringodium isoetifolium* file is the same plot with round leaves, pointed tips, no scars or veins, and 16,756 triangles. The *Thalassia hemprichii* file is the same plot with curved ribbons, nine short black tannin bars, a thick rhizome with scars between shoots, and 21,088 triangles. The *Halophila minor* file is the same plot with paired small ovals, smooth margins, a wedge sheath, 6 cross-vein pairs, and 19,878 triangles. The *Halophila ovalis* file is the same plot with larger paired ovals, no hairs, 10 cross-vein pairs, and 19,878 triangles. The *Enhalus acoroides* file is the same plot with long inrolled ribbons, a thick bristled rhizome, cord-like roots, 8 shoots, and 13,388 triangles. The viewer controls are in the app, including See roots and growth speed at 0.5×, 1×, 1.5×, and 2×. Play loops the growth from the bud. A tester has not done that on a phone. The web build turns with drag and zooms with the wheel, touchpad scroll, and pinch. |
| US-3 | Camera, gallery, library, rotate/zoom, and See roots on all nine patch viewers are in the app. A tester has not scored them on a phone. The web build turns with drag and zooms with the wheel, touchpad scroll, and pinch. |
| PE-4 | Time rotate and zoom on a physical phone. All nine patch models are bundled. The *Cymodocea rotundata* meadow is 34,542 triangles. The *Cymodocea serrulata* meadow is 24,864 triangles. The *Halodule pinifolia* meadow is 21,572 triangles. The *Halodule uninervis* meadow is 20,804 triangles. The *Syringodium isoetifolium* meadow is 16,756 triangles. The *Thalassia hemprichii* meadow is 21,088 triangles. The *Halophila minor* meadow is 19,878 triangles. The *Halophila ovalis* meadow is 19,878 triangles. The *Enhalus acoroides* meadow is 13,388 triangles. Lag has not been timed. The web build turns with drag and zooms with the wheel, touchpad scroll, and pinch. |
| US-1 | A first-time user can tell MarineSee identifies and teaches Mati seagrass. The Home hero banner states it and offers Scan, three stacked photo decks under "Seagrass species" preview the nine species, and the card below shows the photo → features → SVM → match path; onboarding and profile repeat it. |
| US-2 | After one short brief, the tester identifies a photo and opens the library with no step-by-step guide. |
| US-5 | The tester agrees the text, colors, and layout are comfortable on a phone. |
| US-6 | Labels and buttons are large enough to read and tap. |
| PE-1 | Identify returns within about five seconds on a qualifying phone. |
| PE-2 | A profile opened from the library does not make the tester wait. |
| PE-3 | Library → profile → 3D completes without a long wait. |
| PE-5 | Opening several species in one session stays responsive. |
| RE-1 | One full identify plus a profile does not close the app. |
| RE-2 | A second photo after the first result does not crash the app. |
| RE-4 | A failed identify stays in the app and can be tried again. `result_screen.dart` has **Try again**, which returns to Identify. That control has not been shown on a phone. |
| CO-1 | Identify and library both work while other apps stay installed. |
| CO-2 | MarineSee opens without uninstalling other apps. |
| PO-1 | Identify, library, and profile are usable on two different Android screen sizes. |
| PO-2 | The installed app opens on Android 8.0 or newer. `minSdk` is 26. A release APK installed and launched on a TECNO BG6 (16 Nov 2026), but that build still called the laptop API. The on-device build has not been installed yet. |
| PO-3 | A second qualifying phone installs and opens the APK with no extra toolchain. |

## Counts

When a status changes, replace the snapshot line at the top of this file and the snapshot line in `19-evaluation-question-spec.md` in the same edit. Recount `met`, `not-met`, and `unmeasured`. The total stays 29.
