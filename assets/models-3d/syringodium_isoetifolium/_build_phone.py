"""Phone meadow for Syringodium isoetifolium. Run inside Blender:

blender.exe --background --python syringodium_isoetifolium/_build_phone.py

Writes the phone blend and the phone glb. Does not open a rotundata file.
"""

import json
import os
import sys

import bpy

ROOT = r"d:\pepot\marinesee\assets\models-3d"
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from syringodium_isoetifolium_build import checks, config, grow, layout, meshes, reef, scene
from syringodium_isoetifolium_build import publish as publish_mod

BLEND = config.BLEND_PATH
GLB = config.GLB_PATH


def _refuse(path):
    norm = os.path.abspath(path).replace("\\", "/").lower()
    if "cymodocea_rotundata" in norm or "rotundata_build" in norm:
        raise SystemExit("refusing to write a rotundata path: " + path)


def _glb_report(path):
    problems = []
    blob = open(path, "rb").read()
    if blob[:4] != b"glTF":
        return ["glb header missing"]
    length = int.from_bytes(blob[12:16], "little")
    if blob[16:20] != b"JSON":
        return ["glb json chunk missing"]
    data = json.loads(blob[20:20 + length].decode("utf-8"))
    if data.get("cameras"):
        problems.append("glb contains a camera")
    names = [anim.get("name") for anim in data.get("animations", [])]
    if "Grow" not in names:
        problems.append("glb missing Grow, found %s" % names)
    return problems


def build():
    _refuse(BLEND)
    _refuse(GLB)
    _refuse(config.SPECIES_GLB_PATH)
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    scene.setup_scene()
    scene.clear_plant()
    layout.create_plant()
    meshes.rebuild_meshes()
    reef.build_presentation()
    arm = bpy.data.objects["SI_Armature"]
    grow.animate(arm)
    bpy.context.view_layer.update()
    report = checks.validate()
    os.makedirs(os.path.dirname(BLEND), exist_ok=True)
    bpy.context.scene.frame_set(300)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)
    print("PHONE_REPORT", report)
    if report["problems"]:
        print("PHONE_SKIP publish; checks failed")
        sys.exit(1)
    publish_mod.publish(GLB)
    extra = _glb_report(GLB)
    if extra:
        print("PHONE_GLB", extra)
        sys.exit(1)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)
    print("PHONE_SAVED", BLEND, GLB, config.SPECIES_GLB_PATH)
    return report


if __name__ == "__main__":
    build()
