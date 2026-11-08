# Thalassia hemprichii

Current files. Older tries go in `earlier/` and are not what the app shows.

| Role | File |
|------|------|
| Blender for the phone model | `thalassia_hemprichii.blend` |
| Blender for the lesson | `thalassia_hemprichii_lesson.blend` |
| Lesson video | `thalassia_hemprichii_lesson.mp4` |
| Phone model | `thalassia_hemprichii.glb` |

The app plays the copies in `app/assets/models-3d/`:

- `thalassia_hemprichii.glb` — the plant you rotate
- `thalassia_hemprichii_lesson.mp4` — the lesson, with the five spoken lines

The lesson video is 30.0 seconds, 1920x1080, English speech and no music. ffprobe reads 30.000 seconds with an AAC audio stream. The same file is in this folder and in `app/assets/models-3d/`. The phone blend and phone model were already built and were not written again.

No growth clip. No pitch audio. No blend under `app/`.

Build scripts live in `assets/models-3d/thalassia_hemprichii_build/`. Entries are `_build_phone.py` and `_build_lesson.py` in this folder. The short note is `thalassia_hemprichii.md`.
