# 3D assets

One folder per species. Slugs match `docs/11-species.md`.

Each folder has a `RECORD.md`. That file names the current Blender file, the current lesson video, and the current phone model. Older tries go in that species' `earlier/` folder and are not what the app shows.

The app does not read these folders. Copy the current `.glb` and the current lesson `.mp4` into `app/assets/models-3d/` using the flat names `<slug>.glb` and `<slug>_lesson.mp4`.

| Folder | State |
|--------|--------|
| `cymodocea_rotundata/` | Built. This is the reference. |
| `cymodocea_serrulata/` | Built. |
| `enhalus_acoroides/` | Built. |
| `halodule_pinifolia/` | Built. |
| `halodule_uninervis/` | Built. |
| `halophila_minor/` | Built. |
| `halophila_ovalis/` | Built. |
| `syringodium_isoetifolium/` | Built. |
| `thalassia_hemprichii/` | Built. |

Shared build code for the reference species stays in `rotundata_build/`.
