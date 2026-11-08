# Halodule uninervis

These four files are the current ones. Older tries, if a rebuild replaces a file, go in `earlier/`.

| Role | File |
|------|------|
| Blender for the phone model | `halodule_uninervis.blend` |
| Blender for the lesson | `halodule_uninervis_lesson.blend` |
| Lesson video | `halodule_uninervis_lesson.mp4` |
| Phone model | `halodule_uninervis.glb` |

The app plays the copies in `app/assets/models-3d/`:

- `halodule_uninervis.glb` — the plant you rotate
- `halodule_uninervis_lesson.mp4` — the lesson, with the five spoken lines

The lesson film is 30.000 seconds, 1920×1080, 30 fps, frames 1–900. English speech, no music. ffprobe shows H.264 video and AAC audio on this copy and on `app/assets/models-3d/halodule_uninervis_lesson.mp4`. The leaf tip in the lesson blend stays a trident.

Build scripts live in `assets/models-3d/halodule_uninervis_build/`. Entry scripts live in this folder. The note is `halodule_uninervis.md`.
