"""Phone meadow. Run with blender.exe --background --python this file.

The object prefix lives only in this species folder.
"""

import os
import sys

os.environ["MARINESEE_CODE"] = "EA"

HERE = r"d:\pepot\marinesee\assets\models-3d"
if HERE not in sys.path:
    sys.path.insert(0, HERE)
for _name in list(sys.modules):
    if _name == "enhalus_acoroides_build" or _name.startswith("enhalus_acoroides_build."):
        del sys.modules[_name]

import bpy
from mathutils import Vector

from enhalus_acoroides_build import checks, config, grow, layout, meshes, reef, scene
from enhalus_acoroides_build import publish as pub

ROOT = r"d:\pepot\marinesee"
BLEND = ROOT + r"\assets\models-3d\enhalus_acoroides\enhalus_acoroides.blend"
config.GLB_PATH = ROOT + r"\app\assets\models-3d\enhalus_acoroides.glb"
config.MIRROR_GLB = ROOT + r"\assets\models-3d\enhalus_acoroides\enhalus_acoroides.glb"


def build():
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    scene.setup_scene()
    scene.clear_plant()
    layout.create_plant()
    meshes.rebuild_meshes()
    reef.build_presentation()
    arm = bpy.data.objects[config.px("Armature")]
    grow.animate(arm)
    report = checks.validate()
    bpy.context.scene.frame_set(1)
    os.makedirs(os.path.dirname(BLEND), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)
    print("PHONE_REPORT", report)
    if report["problems"]:
        print("PHONE_SKIP publish")
        return report
    pub.publish()
    shot = bpy.context.scene
    shot.frame_set(316)
    still_dir = r"C:\Users\reaga\AppData\Local\Temp\ea_phone_stills"
    os.makedirs(still_dir, exist_ok=True)
    shot.render.resolution_x = 1280
    shot.render.resolution_y = 720
    shot.render.resolution_percentage = 100
    shot.render.image_settings.file_format = "JPEG"
    shot.render.image_settings.quality = 90
    try:
        shot.eevee.taa_render_samples = 16
    except AttributeError:
        pass
    engines = [item.identifier for item in shot.render.bl_rna.properties["engine"].enum_items]
    for name in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        if name in engines:
            shot.render.engine = name
            break
    shot.render.filepath = os.path.join(still_dir, "full.jpg")
    bpy.ops.render.render(write_still=True)
    cam = bpy.data.objects.get("Camera")
    if cam is not None:
        cam.location = (0.02, -0.34, 0.02)
        aim = (0.0, -0.01, -0.01)
        cam.rotation_euler = (Vector(aim) - cam.location).to_track_quat("-Z", "Y").to_euler()
        cam.data.lens = 48
        shot.render.filepath = os.path.join(still_dir, "cut.jpg")
        bpy.ops.render.render(write_still=True)
        cam.location = (0.16, -0.22, 0.22)
        cam.rotation_euler = (Vector((0.0, 0.0, 0.22)) - cam.location).to_track_quat("-Z", "Y").to_euler()
        cam.data.lens = 60
        shot.render.filepath = os.path.join(still_dir, "leaf.jpg")
        bpy.ops.render.render(write_still=True)
        cam.location = (0.0, 0.02, 0.62)
        cam.rotation_euler = (Vector((0.0, 0.02, 0.0)) - cam.location).to_track_quat("-Z", "Y").to_euler()
        cam.data.lens = 35
        shot.render.filepath = os.path.join(still_dir, "bed.jpg")
        bpy.ops.render.render(write_still=True)
    shot.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)
    print("PHONE_DONE", report["triangles"], "leaves", report["leaves"])
    return report


if __name__ == "__main__":
    build()
