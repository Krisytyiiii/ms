# 3D assets

One folder per species. The name of the folder is the species slug.

## Which Blender file to open

Open the phone file. That is the meadow in the 3D viewer. The lesson file is the film only. Do not open a file in `earlier/`. Do not open a file whose name ends in `.blend1`. Those are Blender backups.

| Species | Open this | Lesson film only |
|---|---|---|
| Cymodocea rotundata | `cymodocea_rotundata/blender/cymodocea_rotundata.blend` | `cymodocea_rotundata/blender/cymodocea_rotundata_lesson.blend` |
| Cymodocea serrulata | `cymodocea_serrulata/blender/cymodocea_serrulata.blend` | `cymodocea_serrulata/blender/cymodocea_serrulata_lesson.blend` |
| Halodule uninervis | `halodule_uninervis/blender/halodule_uninervis.blend` | `halodule_uninervis/blender/halodule_uninervis_lesson.blend` |
| Halodule pinifolia | `halodule_pinifolia/blender/halodule_pinifolia.blend` | `halodule_pinifolia/blender/halodule_pinifolia_lesson.blend` |
| Enhalus acoroides | `enhalus_acoroides/blender/enhalus_acoroides.blend` | `enhalus_acoroides/blender/enhalus_acoroides_lesson.blend` |
| Halophila ovalis | `halophila_ovalis/blender/halophila_ovalis.blend` | `halophila_ovalis/blender/halophila_ovalis_lesson.blend` |
| Halophila minor | `halophila_minor/blender/halophila_minor.blend` | `halophila_minor/blender/halophila_minor_lesson.blend` |
| Syringodium isoetifolium | `syringodium_isoetifolium/blender/syringodium_isoetifolium.blend` | `syringodium_isoetifolium/blender/syringodium_isoetifolium_lesson.blend` |
| Thalassia hemprichii | `thalassia_hemprichii/blender/thalassia_hemprichii.blend` | `thalassia_hemprichii/blender/thalassia_hemprichii_lesson.blend` |

The newest file in a folder is not always the right one. Use the phone name in the table.

## Folders inside each species

| Folder | What is in it |
|---|---|
| `blender/` | The Blender files. `<slug>.blend` is the phone model. `<slug>_lesson.blend` is the lesson film. |
| `models/` | The exported `<slug>.glb`. |
| `video/` | The lesson `<slug>_lesson.mp4`. |
| `speech/` | The spoken track, subtitles, and timing. |
| `earlier/` | Old tries. Not current. Only rotundata has this. |

`PLAN.md` and `RECORD.md` stay in the species folder. The Python that builds the meadow stays in `<slug>_build/` next to the species folder.

The app does not read these folders. It plays the flat copies in `app/assets/models-3d/`: `<slug>.glb` and `<slug>_lesson.mp4`.
