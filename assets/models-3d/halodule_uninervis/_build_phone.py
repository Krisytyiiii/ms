"""Phone meadow for Halodule uninervis. Run inside Blender:

blender.exe --background --python halodule_uninervis/_build_phone.py

Writes the phone blend and the phone glb. Does not open another species file.
"""

import os
import sys

import bpy

ROOT = r"d:\pepot\marinesee\assets\models-3d"
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from halodule_uninervis_build import checks, config, grow, layout, meshes, reef, scene
from halodule_uninervis_build import publish as publish_mod

BLEND = config.BLEND_PATH
GLB = config.GLB_PATH


def _refuse(path):
    norm = os.path.abspath(path).replace("\\", "/").lower()
    if "cymodocea_rotundata" in norm or "halodule_pinifolia" in norm:
        raise SystemExit("refusing to write another species path: " + path)


def build():
    _refuse(BLEND)
    _refuse(GLB)
    _refuse(config.ASSETS_GLB_PATH)
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    scene.setup_scene()
    scene.clear_plant()
    layout.create_plant()
    meshes.rebuild_meshes()
    reef.build_presentation()
    arm = bpy.data.objects["HU_Armature"]
    grow.animate(arm)
    report = checks.validate()
    bpy.context.scene.frame_set(300)
    os.makedirs(os.path.dirname(BLEND), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)
    print("PHONE_REPORT", report)
    if report["problems"]:
        print("PHONE_SKIP publish; checks failed")
        return report
    publish_mod.publish(GLB)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)
    print("PHONE_SAVED", BLEND, GLB)
    return report


if __name__ == "__main__":
    build()
