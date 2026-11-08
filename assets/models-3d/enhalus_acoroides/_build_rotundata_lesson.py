"""Lesson meadow for Enhalus acoroides. Run inside Blender.

Builds the 900-frame lesson and renders the 30-second film.
Does not publish a phone glb.
"""

import os
import sys

import bpy

ROOT = r"d:\pepot\marinesee\assets\models-3d"
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
for _name in list(sys.modules):
    if _name == "enhalus_acoroides_build" or _name.startswith("enhalus_acoroides_build."):
        del sys.modules[_name]

from enhalus_acoroides_build import captions, checks, config, grow, layout, meshes, realism, reef, scene  # noqa: E402
from enhalus_acoroides_build.render import render_lesson  # noqa: E402

BLEND = r"d:\pepot\marinesee\assets\models-3d\enhalus_acoroides\enhalus_acoroides_lesson.blend"


def _refuse(path):
    norm = os.path.abspath(path).replace("\\", "/").lower()
    if "cymodocea_rotundata" in norm or "/rotundata_build/" in norm:
        raise SystemExit("refusing to write a rotundata path: " + path)


def build():
    _refuse(BLEND)
    config.use_lesson()
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    scene.setup_scene()
    scene.clear_plant()
    layout.create_plant()
    meshes.rebuild_meshes()
    reef.build_presentation()
    realism.lesson_shade()
    captions.build(900)
    arm = bpy.data.objects["EA_Armature"]
    grow.animate(arm)
    report = checks.validate()
    print("LESSON_REPORT", report)
    os.makedirs(os.path.dirname(BLEND), exist_ok=True)
    bpy.context.scene.frame_set(860)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)
    if report["problems"]:
        print("LESSON_SKIP render; checks failed")
        return report
    out = render_lesson(900)
    _refuse(out)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)
    print("LESSON_VIDEO", out)
    return report


if __name__ == "__main__":
    build()
