"""Phone meadow for Thalassia hemprichii. Run inside Blender:

blender.exe --background --python thalassia_hemprichii/_build_phone.py

Writes the phone blend and the phone glb. Does not open a rotundata file.
"""

import json
import os
import struct
import sys

import bpy

ROOT = r"d:\pepot\marinesee\assets\models-3d"
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from thalassia_hemprichii_build import checks, config, grow, layout, meshes, reef, scene
from thalassia_hemprichii_build import publish as publish_mod

BLEND = config.BLEND_PATH
GLB = config.GLB_PATH
STILL = r"C:\Users\reaga\AppData\Local\Temp\th_phone_f300.jpg"


def _refuse(path):
    norm = os.path.abspath(path).replace("\\", "/").lower()
    if "cymodocea_rotundata" in norm or "rotundata_build" in norm:
        raise SystemExit("refusing to write a rotundata path: " + path)


def _glb_note(path):
    with open(path, "rb") as handle:
        blob = handle.read(12)
        if blob[:4] != b"glTF":
            return {"error": "not glb"}
        length, kind = struct.unpack("<I4s", handle.read(8))
        if kind != b"JSON":
            return {"error": "no json chunk"}
        doc = json.loads(handle.read(length))
    return {
        "cameras": len(doc.get("cameras") or []),
        "animations": [item.get("name") for item in doc.get("animations") or []],
        "scenes": len(doc.get("scenes") or []),
    }


def build():
    _refuse(BLEND)
    _refuse(GLB)
    _refuse(publish_mod.ASSETS_GLB_PATH)
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    scene.setup_scene()
    scene.clear_plant()
    layout.create_plant()
    meshes.rebuild_meshes()
    reef.build_presentation()
    arm = bpy.data.objects["TH_Armature"]
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
    print("PHONE_GLB", _glb_note(GLB))
    shot = bpy.context.scene
    shot.render.filepath = STILL
    shot.render.image_settings.media_type = "IMAGE"
    shot.render.image_settings.file_format = "JPEG"
    shot.render.image_settings.quality = 85
    shot.render.resolution_x = 960
    shot.render.resolution_y = 540
    shot.render.resolution_percentage = 100
    try:
        shot.eevee.taa_render_samples = 8
    except AttributeError:
        pass
    bpy.ops.render.render(write_still=True)
    print("PHONE_STILL", STILL)
    cam = bpy.data.objects.get("Camera")
    if cam is not None:
        from mathutils import Vector

        cam.location = (-0.01, -0.14, 0.11)
        cam.rotation_euler = (Vector((0.02, -0.03, 0.09)) - Vector(cam.location)).to_track_quat("-Z", "Y").to_euler()
        close = r"C:\Users\reaga\AppData\Local\Temp\th_phone_close.jpg"
        shot.render.resolution_x = 1280
        shot.render.resolution_y = 720
        shot.render.filepath = close
        bpy.ops.render.render(write_still=True)
        print("PHONE_CLOSE", close)
    print("PHONE_SAVED", BLEND, GLB)
    return report


if __name__ == "__main__":
    build()
