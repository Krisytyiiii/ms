"""Halodule pinifolia as a solid 3D meadow. Run inside Blender.

Authoring holds the Bezier curves and shoot empties a person edits.
Meadow holds the solid meshes built from them, skinned to HP_Armature.
Growth is the Grow action: bone scale Y only, mesh object scale stays (1, 1, 1).

A normal run keeps every curve point already in the file and calls
rebuild_meshes(). Set RESET = True to replace the plant from scratch.
The modules live in halodule_pinifolia_build/ next to this file; layout numbers are
in halodule_pinifolia_build/config.py.
"""

import os
import sys

import bpy

RESET = True
OVERWRITE_ANIM = True
DO_PUBLISH = True

HERE = r"d:\pepot\marinesee\assets\models-3d"
if not os.path.isdir(os.path.join(HERE, "halodule_pinifolia_build")):
    HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
for _name in [n for n in sys.modules if n == "halodule_pinifolia_build" or n.startswith("halodule_pinifolia_build.")]:
    del sys.modules[_name]

from halodule_pinifolia_build import captions, checks, grow, layout, meshes, realism, reef, scene  # noqa: E402
from halodule_pinifolia_build import publish as _publish  # noqa: E402
from halodule_pinifolia_build import config  # noqa: E402


def rebuild_meshes():
    return meshes.rebuild_meshes()


def publish():
    return _publish.publish()


def build(reset=None, overwrite_anim=None, do_publish=None, blend_path=None):
    reset = RESET if reset is None else reset
    overwrite_anim = OVERWRITE_ANIM if overwrite_anim is None else overwrite_anim
    do_publish = DO_PUBLISH if do_publish is None else do_publish
    blend_path = blend_path or config.BLEND_PATH
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    scene.setup_scene()
    if reset or bpy.data.objects.get("HP_Rhizome") is None:
        scene.clear_plant()
        layout.create_plant()
        overwrite_anim = True
    rebuild_meshes()
    reef.build_presentation()
    variant = config.CONFIG.get("variant")
    if variant == "realistic":
        realism.apply()
        captions.build(int(config.CONFIG.get("frame_end", 1800)))
    elif variant == "lesson":
        realism.lesson_shade()
        captions.build(int(config.CONFIG.get("frame_end", 1800)))
    elif variant == "phone":
        realism.lesson_shade()
    arm = bpy.data.objects["HP_Armature"]
    if overwrite_anim or bpy.data.actions.get("Grow") is None:
        grow.animate(arm)
    report = checks.validate()
    bpy.context.scene.frame_set(300)
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print("saved", blend_path)
    if do_publish and not report["problems"]:
        publish()
        bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    elif do_publish:
        print("SKIP publish; checks failed")
    return report


if __name__ == "__main__":
    build()
