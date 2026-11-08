"""Phone meadow for Halophila ovalis. Run inside Blender:

blender.exe --background --python halophila_ovalis/_build_phone.py

Writes the phone blend and the phone glb. Does not open a rotundata file.
"""

import os
import sys

import bpy

ROOT = r"d:\pepot\marinesee\assets\models-3d"
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from halophila_ovalis_build import checks, config, grow, layout, meshes, reef, scene
from halophila_ovalis_build import publish as publish_mod
from halophila_ovalis_build.render import _eevee

BLEND = config.BLEND_PATH
GLB = config.GLB_PATH
STILLS = r"C:\Users\reaga\AppData\Local\Temp\ho_ovalis_phone"


def _refuse(path):
    norm = os.path.abspath(path).replace("\\", "/").lower()
    if "cymodocea_rotundata" in norm or "halophila_minor" in norm:
        raise SystemExit("refusing to write " + path)


def _still(path, frame):
    view = bpy.context.scene
    view.frame_set(frame)
    view.render.filepath = path
    view.render.resolution_x = 960
    view.render.resolution_y = 540
    view.render.resolution_percentage = 100
    try:
        view.eevee.taa_render_samples = 8
    except AttributeError:
        pass
    view.render.image_settings.media_type = "IMAGE"
    view.render.image_settings.file_format = "JPEG"
    view.render.image_settings.quality = 85
    bpy.ops.render.render(write_still=True)
    print("STILL", path)


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
    arm = bpy.data.objects["HO_Armature"]
    grow.animate(arm)
    report = checks.validate()
    bpy.context.scene.frame_set(300)
    os.makedirs(os.path.dirname(BLEND), exist_ok=True)
    os.makedirs(os.path.dirname(GLB), exist_ok=True)
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
