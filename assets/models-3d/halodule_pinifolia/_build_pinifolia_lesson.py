"""Lesson meadow for Halodule pinifolia. Run inside Blender.

This file is the species entry. It runs the builder that already lives
beside it. HP_LESSON_PHASE=stills builds the blend and writes check stills.
HP_LESSON_PHASE=render writes the silent 900-frame film.
"""

import runpy

runpy.run_path(
    r"d:\pepot\marinesee\assets\models-3d\halodule_pinifolia\_build_rotundata_lesson.py",
    run_name="__main__",
)
