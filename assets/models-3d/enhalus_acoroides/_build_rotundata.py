"""Phone meadow for Enhalus acoroides. Run inside Blender:

blender.exe --background --python enhalus_acoroides/_build_rotundata.py

Writes the phone blend and the phone glb. Does not open a rotundata file.
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

from enhalus_acoroides_build import checks, config, grow, layout, meshes, reef, scene  # noqa: E402
from enhalus_acoroides_build import publish as publish_mod  # noqa: E402

BLEND = config.BLEND_PATH
GLB = config.GLB_PATH


def _refuse(path):
    norm = os.path.abspath(path).replace("\\", "/").lower()
    if "cymodocea_rotundata" in norm or "/rotundata_build/" in norm:
        raise SystemExit("refusing to write a rotundata path: " + path)


def build():
    _refuse(BLEND)
    _refuse(GLB)
    _refuse(config.MIRROR_GLB)
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    scene.setup_scene()
    scene.clear_plant()
    layout.create_plant()
    meshes.rebuild_meshes()
    reef.build_presentation()
    arm = bpy.data.objects["EA_Armature"]
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
