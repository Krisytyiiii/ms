# Prompt — solid 3D model of *Cymodocea serrulata*

Hand this file to the agent that builds the model. Build this species in Blender. Stop when the checklist at the end passes. The other seven species wait.

The owner asked for this species on purpose. `AGENTS.md` says this repo only integrates 3D. Ignore that for this task, the same way `cymodocea_rotundata.md` did. `docs/21-3d-species-model-spec.md` §0 already records that a species is built here when the owner asks for it.

One species only. Out of scope: viewer changes, a growth clip, pitch audio, flowers, and any file under `assets/models-3d/cymodocea_rotundata/`.

## What already exists

*Cymodocea rotundata* is the reference and stays untouched. Its current files are named in `assets/models-3d/cymodocea_rotundata/RECORD.md`. Shared builders live in `assets/models-3d/rotundata_build/`. Entries:

- `assets/models-3d/_build_rotundata.py` — phone meadow, frames 1–330, action `Grow`
- `assets/models-3d/_build_rotundata_lesson.py` — lesson meadow, frames 1–900

Those entries open and save only the rotundata blends. A serrulata run uses the same builders with a species prefix and serrulata paths. It never calls `open_mainfile` or `save_as_mainfile` on a path that contains `cymodocea_rotundata`.

`cymodocea_serrulata/` currently has this brief and a `RECORD.md` that says the model is not built. No `.blend`, `.glb`, or lesson `.mp4` yet.

The Flutter viewer already resolves `assets/models-3d/<slug>.glb` and `assets/models-3d/<slug>_lesson.mp4` from `app/lib/data/model_3d_library.dart`. `app/pubspec.yaml` already includes the whole `assets/models-3d/` directory. Leave the viewer, the library, and the pubspec alone.

## Thread a prefix through the existing builders

Object code for this species is `CS`. Rotundata stays `CR`. Shared code keeps working for rotundata when the prefix and the paths are omitted: the default remains `CR` and the rotundata paths in `config.py`, `publish.py`, and `render.py`.

A serrulata run passes `CS` and these paths in, and does not leave the module-level constants pointing at serrulata afterwards:

| Role | Path |
|------|------|
| Phone blend | `assets/models-3d/cymodocea_serrulata/blender/cymodocea_serrulata.blend` |
| Lesson blend | `assets/models-3d/cymodocea_serrulata/blender/cymodocea_serrulata_lesson.blend` |
| Phone model | `app/assets/models-3d/cymodocea_serrulata.glb` and the same name under `assets/models-3d/cymodocea_serrulata/` |
| Lesson video | `assets/models-3d/cymodocea_serrulata/video/cymodocea_serrulata_lesson.mp4` and the same flat name under `app/assets/models-3d/` |

Hard-coded `CR_` names to parameterize (default `CR`):

- `rotundata_build/layout.py` — `CR_Controls`, `CR_Rhizome`, `CR_Shoot_`, `CR_Leaf_`, `CR_Root_`, `CR_Armature`, `CR_HOW_TO_EDIT`
- `rotundata_build/rig.py`, `meshes.py`, `checks.py`, `publish.py`
- `rotundata_build/lesson.py` — `CR_Shoot_` and `CR_LessonAim`
- `rotundata_build/lesson_cards.py` — `CR_Card`, `CR_Caption_`, `CR_Note_`
- `rotundata_build/scene.py` — `PLANT_PREFIXES` starts with `CR_`
- `rotundata_build/captions.py`, `reef.py`, `grow.py` where a name starts with `CR_`
- `_build_rotundata.py` — the reset test looks up `CR_Rhizome` and `CR_Armature`
- `_build_rotundata_lesson.py` — caption hide list and `CR_Shoot_00`

`scene.py` says the phone camera is never animated. Keep that for the phone blend. The lesson blend may animate its camera; that camera stays out of the `.glb` (`publish()` already sets `export_cameras` false).

`checks.py` `_lesson_shape` currently fails unless `leaf_width_m` is `0.004`. Rotundata keeps that 4 mm check. Serrulata expects `0.009`.

## Change only the tip, the sheath, and the scars

Reuse the rotundata meadow: one rhizome across a solid sand bed, shoots with flat strap leaves, roots down at the nodes, materials, rig, and the `Grow` story. Three organs change.

### Tip — serrated

`geometry.leaf_mesh` builds a semicircular tip (the degree steps near the end of the strap). Serrulata uses a serrated tip so a close view separates it from smooth ribbon seagrass.

The record says the tip is serrated. It does not say how many teeth or how large they are. Those two numbers are **OPEN** in `docs/21-3d-species-model-spec.md` §11. They stay out of the lesson, out of `species.json`, out of `RECORD.md`, and out of any sentence presented as a fact. A tooth count may exist only as an unlabeled display choice inside the mesh builder.

### Sheath — broadly triangular

`shoot.shoot_mesh` builds a C-shaped wrap that flares toward the top. Serrulata’s sheath reads as broadly triangular, which is the Seagrass-Watch shape in the species record. Wall thickness stays. The sheath is still solid, with an inner and an outer wall.

### Scars — not a closed ring

The same function builds each scar as a full loop around the stem (material slot 2). Serrulata’s scars are bands on the stem that do not meet. They stay a fraction of a millimetre proud, built into the stem, not separate tori or beads.

Spec names for the parameters, if a flag is cleaner than a fork: tip `serrated` versus `round`, scar style `not_continuous` versus `continuous_ring`.

## Width, and the numbers that are not facts

Strap width is **9 mm** (`leaf_width_m` `0.009` on both the phone `CONFIG` and the lesson dict). That is the top of the Seagrass-Watch range already in `species.json`: strap-like leaves about 5–9 mm wide. The rotundata lesson width is 4 mm and its phone script still has an older 7 mm block. Copy neither.

`docs/21` §11 marks these **OPEN** for *C. serrulata*: tooth count, tooth size, vein count, stem height. They stay out of the model as cited numbers until an adviser supplies a source.

- Vein count: the rotundata lesson sets `vein_count` to 11 and draws that many grooves (`geometry.strap_profile`, `textures.leaf_image`). Serrulata does not carry that count. Give the strap a plain face, with no counted vein grooves and no counted vein stripes. `textures.vein_xs` returns a single centre lane when the count is 1 or less; do not treat that as “one vein” in any text.
- Stem height and leaf length: the mesh needs a length. Put `stem_height_m` and `leaf_length_m` in `CONFIG` with a comment that each is a display choice, not a Mati measurement and not a Seagrass-Watch figure for this species. Do not copy the rotundata comments that cite 7–15 cm, 9–15 veins, a sheath of 1.5–5.5 cm, or an erect stem under 6 cm. Do not speak either number.
- The spoken lines and the on-screen cards do not mention width, tooth count, veins, stem height, or leaf length.

Lesson subtitle text lives in `rotundata_build/lesson_cards.py` `CARDS`. Point the serrulata lesson at the five lines below. Split a line across the two card rows only so it fits. Add no extra facts. The older `captions.py` `STAGES` text is the time-lapse, which this species does not ship.

## Species record

In `app/assets/data/species.json`, on `cymodocea_serrulata` only:

Remove the unsourced sentence from `botanicalCharacteristics`:

> A 2018 revision has also used the name Oceana serrulata for this plant.

Leave the Seagrass-Watch sentence that is already there (5–9 mm, serrated tip, broadly triangular sheath, scars that do not form a continuous ring).

Add the Mati source line rotundata already uses, as the last `sources` entry:

`Angsinco-Jimenez et al., 2003; Fortes, 2013; Sanchez-Delute et al., 2025, as cited in docs/11-species.md.`

Add `transcript` with the five spoken lines, separated by blank lines, the way rotundata’s `transcript` is stored. The viewer prints that field under the lesson. There is no `pitch` field and no `cymodocea_serrulata_pitch.mp3`.

## Phone file

Solid meadow. One action, named `Grow`. Frames 1–330 at 30 fps. Frame 330 matches frame 1, so playback jumps back to the bud. Mesh object scale stays `(1, 1, 1)`. Growth is bone scale on the long axis. Export `Meadow` and `CS_Armature` only. No curves, no controls, no camera, no lights, no reef. Under 40,000 triangles.

The phone clip is the 330-frame action from `grow.animate` when `variant` is not `lesson`. The lesson script’s `final` phase calls `publish()` on the 900-frame blend. Do not do that for this species. Publishing the lesson blend would put a 30-second clip that does not loop to the bud into the phone file.

`checks.validate` already compares pose at frame 1 with pose at `frame_end` for the phone variant, and rejects a triangle count over 40,000.

## Lesson

Thirty seconds, 1920×1080, 30 fps, frames 1–900. Five beats, already the constants in `rotundata_build/lesson.py`:

| Frames | On screen | Spoken line |
|--------|-----------|-------------|
| 1–120 | One bud | Serrated ribbon seagrass. A display, not a scan of a Mati meadow. |
| 120–330 | Buried stem extends | The buried stem grows through the sand. That is how the patch spreads. |
| 330–510 | Roots at the nodes | Roots grow down at each node and spread in the sand. |
| 510–750 | Leaves and sheath | Each leaf is a flat strap with a serrated tip. The sheath is broadly triangular. |
| 750–900 | Scars, then the patch | The leaf scars do not form a closed ring. That separates it from smooth ribbon seagrass. It can flower and set seed. |

English speech of those lines, timed to those beats. No music. `render.render_lesson` writes a silent H.264 file (`LESSON_MP4` is hard-coded to the rotundata lesson; pass the serrulata path). Mux the voice afterwards. ffmpeg on this machine is the executable named in `assets/models-3d/_day_cycle.py`. No script in the repo generates the rotundata voice; generate this one locally and mux it. The picture keeps the five beats above.

The lesson blend may contain the camera, the cards, and the reef set. None of those go into the `.glb`.

No `cymodocea_serrulata_growth.mp4`. No pitch audio. No `.blend` under `app/`.

## Where the files go

Authoring, in the folder that already exists:

`assets/models-3d/cymodocea_serrulata/`

- `cymodocea_serrulata.blend`
- `cymodocea_serrulata_lesson.blend`
- `cymodocea_serrulata.glb`
- `cymodocea_serrulata_lesson.mp4`
- this brief
- `RECORD.md` updated so it names those four current files, in the same shape as `cymodocea_rotundata/RECORD.md`

Flutter copies, flat names only:

- `app/assets/models-3d/cymodocea_serrulata.glb`
- `app/assets/models-3d/cymodocea_serrulata_lesson.mp4`

Older tries, if a rebuild replaces a file, go in `cymodocea_serrulata/earlier/`.

## Evaluation rows

When the `.glb` is in the app, update **Evidence** only for FS-3, FS-7, US-3, and PE-4. Same sentences in `docs/19-evaluation-question-spec.md` and the matching lists in `docs/20-evaluation-gaps.md`. Leave every Status as it is. Leave the snapshot counts as they are. A new `.glb` does not mark a row `met`.

Facts the evidence can state after the checks pass:

- FS-3 stays `not-met`. Profile and 3D still open only after the identify API returns a slug. *Cymodocea rotundata* and *Cymodocea serrulata* each have a bundled patch `.glb`. The other seven species still open a clip or a placeholder.
- FS-7 stays `unmeasured`. Name `app/assets/models-3d/cymodocea_serrulata.glb` as the serrated-ribbon patch: 9 mm straps, a serrated tip, a broadly triangular sheath, scars that do not close, roots from each node, clip `Grow`. Say a tester has not rotated or zoomed it on a physical phone. Keep the existing sentence about the rotundata patch and about the web viewer.
- US-3 stays `unmeasured`. Rotate and zoom exist on the rotundata and serrulata patch viewers. A tester has not scored them on a phone.
- PE-4 stays `unmeasured`. Both patch models are bundled. Lag has not been timed on a physical phone.

Do not edit FS-6. Do not add security or maintainability items to the questionnaire.

## Done when

- Phone `.glb`: solid meadow, one clip `Grow`, frames 1–330 at 30 fps, frame 330 equals frame 1, no camera, under 40,000 triangles. `checks.validate` reports no problems. Authoring curves are still in the phone blend after export.
- A close view shows a serrated tip, a broadly triangular sheath, and scars that do not meet around the stem. The strap is 9 mm wide. The face has no 11-vein pattern.
- Lesson `.mp4`: 30 seconds, 1920×1080, the five beats above, English speech of those lines, no music.
- `species.json` `transcript` is those five lines and nothing else. The Oceana sentence is gone. The Mati source line is present.
- `RECORD.md` names the current blend, lesson blend, lesson video, and phone model.
- No path written by the run sits under `cymodocea_rotundata/`.
- The viewer code is unchanged.

## After this species passes

Same folders and the same checklist, and only then, in this order:

1. *Halodule pinifolia*
2. *Halodule uninervis* — trident tip, checked side by side with *H. pinifolia*
3. *Thalassia hemprichii*
4. *Syringodium isoetifolium*
5. *Halophila minor*
6. *Halophila ovalis* — cross-vein count checked against *H. minor*
7. *Enhalus acoroides* — fewer shoots so the meadow stays under 40,000 triangles

Anything marked **OPEN** in `docs/21-3d-species-model-spec.md` §11 stays out of that model until the adviser supplies a source. Do not swap the two *Halodule* tips. Do not swap the two *Halophila* vein counts (*H. minor* fewer than eight cross-vein pairs, *H. ovalis* eight or more).
