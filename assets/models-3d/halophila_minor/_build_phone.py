"""Phone meadow for Halophila minor. Run inside Blender:

blender.exe --background --python halophila_minor/_build_phone.py

Writes the phone blend and the phone glb. Does not open another species file.
"""

import os
import sys

import bpy

ROOT = r"d:\pepot\marinesee\assets\models-3d"
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from halophila_minor_build import checks, config, grow, layout, meshes, reef, scene
from halophila_minor_build import publish as publish_mod
from halophila_minor_build.render import _eevee

BLEND = config.BLEND_PATH
GLB = config.GLB_PATH
STILL = r"C:\Users\reaga\AppData\Local\Temp\hm_phone_f300.jpg"


def _refuse(path):
    norm = os.path.abspath(path).replace("\\", "/").lower()
    for banned in ("cymodocea_rotundata", "halophila_ovalis", "rotundata_build"):
        if banned in norm:
            raise SystemExit("refusing to write " + path)


def build():
    _refuse(BLEND)
    _refuse(GLB)
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    scene.setup_scene()
    config.CONFIG["variant"] = "phone"
    scene.clear_plant()
    layout.create_plant()
    meshes.rebuild_meshes()
    reef.build_presentation()
    arm = bpy.data.objects["HM_Armature"]
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
    view = bpy.context.scene
    _eevee(view)
    view.render.resolution_x = 1280
    view.render.resolution_y = 720
    view.render.image_settings.file_format = "JPEG"
    view.render.image_settings.quality = 90
    try:
        view.eevee.taa_render_samples = 8
    except AttributeError:
        pass
    view.frame_set(300)
    view.render.filepath = STILL
    bpy.ops.render.render(write_still=True)
    print("PHONE_STILL", STILL)
    print("PHONE_SAVED", BLEND, GLB)
    return report


if __name__ == "__main__":
    build()
