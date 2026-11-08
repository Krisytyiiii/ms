# One Blender at a time

Nine background Blenders filled an 8 GB machine and the jobs stalled. That way of working is retired.

The Blender window already open is the only Blender. Do not start `blender.exe`. Do not start a second Blender. Eight species wait while one species is built and checked.

## After each species, stop

Do not start the next slug until all of these are true:

1. The phone `.glb` is under 40,000 triangles, with one Grow clip and no camera, and the same file is in `app/assets/models-3d/` and the species folder.
2. The lesson is 30 seconds, 1920×1080, with speech and bottom subtitles, no music, and both `.mp4` copies are real files of the same size.
3. `app/assets/data/species.json` has that slug’s transcript and no other slug was rewritten.
4. The plant matches that slug’s own `PLAN.md`.
5. Shoots cover the bed, including the back. A turn must not show a bald back. One front row fails.

## Queue

1. `cymodocea_rotundata` — checked. 19,970 triangles, one Grow clip, no camera. Both `.glb` copies match. Both lessons are 30.000 seconds, 1920×1080, with audio, and they match. Do not rebuild it.
2. `cymodocea_serrulata` — checked after the bed fix. 36,170 triangles, one Grow clip, no camera. Shoots span the bed, back rank faces away. Both lessons are 30.000 seconds, 1920×1080, with audio, and they match. Do not rebuild it.
3. `halodule_uninervis` — the lesson is from 01:18 and the model is from 06:37.
4. `halodule_pinifolia` — 30-second lesson with voice was written at 06:54. Check it. Rebuild only if the check fails.
5. `enhalus_acoroides` — lesson at 07:10 is after the model. Check it. Rebuild only if the check fails.
6. `halophila_ovalis` — same rule.
7. `syringodium_isoetifolium` — same rule.
8. `thalassia_hemprichii` — same rule.
9. `halophila_minor` — same rule.

Each agent reads only its own `PLAN.md`. No evaluation row is marked met.
