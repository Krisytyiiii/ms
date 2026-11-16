# Evaluation question spec

**IMPLEMENTATION.** These 29 statements are the user questionnaire in `MarineSee-Validation-Questions.txt`. A high score means a tester on a qualifying Android phone can do the pass check and would agree. Do not tell the team a question will score high while its status is `not-met` or `unmeasured`.

Checked against the app on 16 Nov 2026, after on-device inference replaced the laptop API: **5 met, 0 not-met, 24 unmeasured.** The open rows are listed for agents in `20-evaluation-gaps.md`. Read that file before changing the app.

## How to mark a row

| Status | Meaning |
|--------|---------|
| `met` | A tester can do the pass check on the installed app now. |
| `not-met` | The app contradicts the statement, or the pass check cannot be done. |
| `unmeasured` | The path may exist, but it has not been shown on a physical phone. |

When a change affects a row, update **Status** and **Evidence** in the same change. Evidence is the file plus what the tester sees. Do not mark `met` from a code comment alone.

Rotate/zoom of a supplied `.glb` is app integration. It does not require authoring a `.blend` file.

## Functional suitability

| ID | Statement | Pass check | Status | Evidence |
|----|-----------|------------|--------|----------|
| FS-1 | Camera or a saved photo | Identify offers Camera and Gallery, and the chosen photo is previewed. | met | `app/lib/screens/identify_screen.dart` |
| FS-2 | Library of the nine Mati species | Library lists the nine scientific names from `11-species.md`. | met | `app/assets/data/species.json` |
| FS-3 | Result opens that species’ profile and 3D view | After a successful identify, both buttons open the matching species. | unmeasured | `LocalClassifier` returns a slug with no network, and the Profile / 3D buttons follow that local result, so a phone in airplane mode can still open all nine bundled profiles and `.glb`/`.mp4` files. Not yet done on a phone. |
| FS-4 | Species name and confidence score | A finished identify shows the scientific name and a percent. | unmeasured | `LocalClassifier` computes both on-device from `app/assets/ml/svm_mobile.*`. `app/test/local_parity_test.dart` runs the full decode → crop → 256px → 148 features → SVM path on all nine bundled photos and asserts a slug and a 0–100% confidence each time. Not yet seen on a phone. |
| FS-5 | Uncertain result asks for a new photo | A low-confidence result shows the retake sentence. | unmeasured | The sentence is a notice on `result_screen.dart`, set by the on-device confidence against the exported threshold, locked at the frozen 0.44 (`retake_threshold` in `svm_mobile.json`). It now reads "Low confidence — this may not be one of the nine species. Retake closer to a leaf." so a low score stops implying the name is right. Six of the nine bundled photos fall below 0.44 in the test, so the branch is reachable. Not yet seen on a phone. |
| FS-6 | Profile shows the study fields | Each field shows real text: common name, botanical characteristics, ecological role, conservation status, habitat. | unmeasured | Cited text is in `app/assets/data/species.json` and the profile reads it. A tester has not opened a profile on a physical phone. |
| FS-7 | Rotate and zoom the 3D model | The tester can rotate and zoom at least one species model. | unmeasured | `app/assets/models-3d/cymodocea_rotundata.glb` is the *Cymodocea rotundata* meadow: one low sand mound, one smooth rhizome with a few branches, and 14 shoots spread across that sand, with straps 7 mm wide as a display choice (the record is 2–4 mm), rounded tips, faint veins, a pale sheath, closed scar rings, and fine roots at the nodes. The clip is `Grow`, about 11 seconds, 34,542 triangles. `app/assets/models-3d/cymodocea_serrulata.glb` is the *Cymodocea serrulata* meadow on that same plot: one low sand mound, one rhizome with a few branches, and 14 shoots, a display choice inside the plan's 12–16. The straps are 9 mm wide, the top of the record's 5–9 mm, with serrated tips, a broadly triangular sheath, and leaf scars that do not meet around the stem. Fine roots leave the nodes, spread, then go down. Its clip is `Grow`, about 11 seconds, 24,864 triangles. `app/assets/models-3d/halodule_pinifolia.glb` is the *Halodule pinifolia* meadow on that same plot: one low sand mound, one pale rhizome with a few branches and clean black leaf scars, and 14 shoots. The leaves are fine, 18 cm on the longest shoot, a display choice inside the record's "up to about 20 cm". One dark vein runs up each leaf and splits in two at a rounded tip. Fine roots leave the nodes, spread, then go down. Its clip is `Grow`, about 11 seconds, 21,572 triangles. `app/assets/models-3d/halodule_uninervis.glb` is the *Halodule uninervis* meadow on that same plot: one low sand mound, one pale ivory rhizome with a few branches and clean black leaf scars, and 14 shoots. The leaves are wider and longer than the pinifolia display, 3.2 mm and 22 cm on the longest shoot, both display choices because the record only says this plant is usually larger. One central vein runs into a trident tip. Fine roots leave the nodes, spread, then go down. Its clip is `Grow`, about 11 seconds, 20,804 triangles. `app/assets/models-3d/syringodium_isoetifolium.glb` is the *Syringodium isoetifolium* meadow on that same plot: one low sand mound, one rhizome with a few branches, and 14 shoots. The leaves are round in cross section, 2.2 mm across as a display choice, and the longest is 26 cm, inside the record's about 7–30 cm. The tip tapers to a point. The record does not describe scars, bristles, or veins, so none are on the mesh. Fine roots leave the nodes, spread, then go down. Its clip is `Grow`, about 11 seconds, 16,756 triangles. `app/assets/models-3d/thalassia_hemprichii.glb` is the *Thalassia hemprichii* meadow on that same plot: one low sand mound, one thick rhizome with a few branches and a scar between shoots, and 14 shoots. The leaves are curved ribbons. The longest is 28 cm, inside the record's about 10–40 cm, and the width is 10 mm, a display choice because the record gives no width. Nine short black tannin bars are a display choice because the record gives no bar count. Fine roots leave the nodes, spread, then go down. Its clip is `Grow`, about 11 seconds, 21,088 triangles. `app/assets/models-3d/halophila_minor.glb` is the *Halophila minor* meadow on that same plot: one low sand mound, one rhizome with a few branches, and 14 nodes. Each node has one pair of small ovals and no upright fan. The leaves are 14 mm long and 8 mm wide, a display choice because the record gives no size, kept small so *Halophila ovalis* can read larger. The margin is smooth, the sheath is wedge-shaped, and there are 6 pairs of cross veins, a display count inside the record's fewer than eight. Fine roots leave the nodes, spread, then go down. Its clip is `Grow`, about 11 seconds, 19,878 triangles. `app/assets/models-3d/halophila_ovalis.glb` is the *Halophila ovalis* meadow on that same plot: one low sand mound, one rhizome with a few branches, and 14 nodes. Each node has one pair of ovals and no upright fan. The leaves are 26 mm long and 15 mm wide, a display choice because the record gives no size, larger than the *Halophila minor* display. The surface has no hairs. There are 10 pairs of cross veins, a display count inside the record's eight or more. Frame 1 is a small bud on open sand. Fine roots leave the nodes, spread, then go down. Its clip is `Grow`, about 11 seconds, 19,878 triangles. `app/assets/models-3d/enhalus_acoroides.glb` is the *Enhalus acoroides* meadow on that same plot, with 8 shoots, a display choice kept low because the leaves are very long. The longest ribbon is 90 cm, inside the record's about 30–150 cm, and the width is 18 mm, a display choice. The margins roll inward. The rhizome is thick, with black bristles 28 mm long, a display choice. The roots are cords, thicker than the fine roots on the ribbon species. No flowers are in the mesh. Its clip is `Grow`, about 11 seconds, 13,388 triangles. All nine species have a bundled patch `.glb` and a lesson `.mp4`. `glb_viewer.dart` has drag, Rotate, Zoom in, and Zoom out, and Play starts the growth at time 0 and loops. See roots fades the sand so the buried roots show, and Hide roots puts the sand back. Growth speed is 0.5×, 1×, 1.5×, or 2×. A tester has not rotated or zoomed any of them on a physical phone. The web build turns with drag and zooms with the wheel, touchpad scroll, and pinch. |

## Usability

| ID | Statement | Pass check | Status | Evidence |
|----|-----------|------------|--------|----------|
| US-1 | Easy to see what MarineSee is for | A first-time user can tell it identifies and teaches Mati seagrass. | unmeasured | Onboarding, Home, and Profile say MarineSee identifies and teaches Mati seagrass. No tester has scored it. |
| US-2 | Identify and library after a short explanation | After one short brief, the tester finishes both tasks with no step-by-step guide. | unmeasured | Not run with a tester. |
| US-3 | Camera, upload, library, and 3D controls are easy | All four controls work and are obvious on a phone. | unmeasured | Camera, gallery, and library work. Rotate, zoom, See roots, and growth speed are on all nine patch viewers. A tester has not scored them on a phone. The web build turns with drag and zooms with the wheel, touchpad scroll, and pinch. |
| US-4 | Retake message is clear | The tester understands they should take the photo again. | unmeasured | The retake sentence is reachable offline now that FS-5 is on-device, but a tester has not read it on a phone or said it was clear. The scanner also states "Only the nine Mati species are supported", and the result screen offers "None of these" for a photo that is not a target seagrass. No tester has seen either on a phone. |
| US-5 | Text, colors, and layout are comfortable | Tester agrees the phone screens are readable. | unmeasured | Not scored on a phone. |
| US-6 | Labels and buttons are large enough | Tester can read and tap them without difficulty. | unmeasured | Not scored on a phone. |

## Performance efficiency

| ID | Statement | Pass check | Status | Evidence |
|----|-----------|------------|--------|----------|
| PE-1 | Result within about five seconds | On a qualifying phone, identify returns in about five seconds. | unmeasured | No timed phone run. |
| PE-2 | Profile opens without a long wait | Opening a species from the library feels immediate. | unmeasured | Profile is bundled JSON. Not timed. |
| PE-3 | Library to profile to 3D does not take long | That path completes without a long wait. | unmeasured | Not timed. |
| PE-4 | Rotate and zoom without freezing | The 3D gesture stays smooth on a qualifying phone. | unmeasured | All nine patch `.glb` files are bundled. The *Cymodocea rotundata* file is the new meadow, 34,542 triangles, clip `Grow`. The *Cymodocea serrulata* file is the same kind of meadow, 24,864 triangles, clip `Grow`. The *Halodule pinifolia* file is the same kind of meadow, 21,572 triangles, clip `Grow`. The *Halodule uninervis* file is the same kind of meadow, 20,804 triangles, clip `Grow`. The *Syringodium isoetifolium* file is the same kind of meadow, 16,756 triangles, clip `Grow`. The *Thalassia hemprichii* file is the same kind of meadow, 21,088 triangles, clip `Grow`. The *Halophila minor* file is the same kind of meadow, 19,878 triangles, clip `Grow`. The *Halophila ovalis* file is the same kind of meadow, 19,878 triangles, clip `Grow`. The *Enhalus acoroides* file is the same kind of meadow, 13,388 triangles, clip `Grow`. Lag has not been timed on a physical phone. The web build turns with drag and zooms with the wheel, touchpad scroll, and pinch. |
| PE-5 | Several species in one session do not lag | Browsing several species stays responsive. | unmeasured | Not tried as a timed session. |

## Reliability

| ID | Statement | Pass check | Status | Evidence |
|----|-----------|------------|--------|----------|
| RE-1 | Identify and open a profile without crashing | One full identify plus profile does not close the app. | unmeasured | Not run on a phone. |
| RE-2 | A second photo does not crash the app | Identify again after the first result. The app stays open. | unmeasured | Not run on a phone. |
| RE-3 | Library and identify are available on open | After onboarding, both are reachable. | met | After onboarding, Scan and Library are tabs in `app/lib/screens/shell.dart`. |
| RE-4 | A failed identify can be tried again | The app stays open and the tester can submit another photo. | unmeasured | `result_screen.dart` shows Try again, which returns to Identify. Not shown on a phone. |
| RE-5 | Library remains after close and reopen | Force-close, open again, library is still there. | met | Library is the bundled asset. |
| RE-6 | Leaving a profile and reopening shows the same text | The same field text is still there. | met | Same bundled asset. The text may still be `TBD`. |

## Compatibility

| ID | Statement | Pass check | Status | Evidence |
|----|-----------|------------|--------|----------|
| CO-1 | Identify and library work while other apps stay installed | Do both tasks with other apps still installed. | unmeasured | Not shown on a phone. |
| CO-2 | No need to uninstall other apps first | MarineSee opens without removing other apps. | unmeasured | Not shown on a phone. |

## Portability

| ID | Statement | Pass check | Status | Evidence |
|----|-----------|------------|--------|----------|
| PO-1 | Screens stay usable on different phone sizes | Identify, library, and profile are usable on two different Android screen sizes. | unmeasured | Not checked on two phones. |
| PO-2 | Runs on Android 8.0 or newer | The installed app opens on a phone at or above Android 8.0. | unmeasured | `minSdk` is 26. No install has been recorded here. |
| PO-3 | Installs on a second qualifying phone without extra tools | A second phone installs and opens the APK with no extra toolchain. | unmeasured | Not done. |

## What this spec does not add

Security and maintainability stay off the user form. They are not in the 29 statements. Do not add account, source-code, or “feels well tested” questions to raise the count.
