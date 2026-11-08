"""Close stills of the grown phone meadow. Not a lesson render."""

import os

import bpy
from mathutils import Vector

BLEND = r"d:\pepot\marinesee\assets\models-3d\cymodocea_serrulata\blender\cymodocea_serrulata.blend"
OUT = r"C:\Users\reaga\AppData\Local\Temp\cs_serrulata_preview"


def _engines():
    return [item.identifier for item in bpy.context.scene.render.bl_rna.properties["engine"].enum_items]


def main():
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    scene = bpy.context.scene
    engines = _engines()
    for name in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        if name in engines:
            scene.render.engine = name
            break
    scene.frame_set(300)
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    try:
        scene.eevee.taa_render_samples = 16
    except AttributeError:
        pass
    scene.render.image_settings.media_type = "IMAGE"
    scene.render.image_settings.file_format = "JPEG"
    scene.render.image_settings.quality = 90
    os.makedirs(OUT, exist_ok=True)

    cam = bpy.data.objects["Camera"]
    for constraint in list(cam.constraints):
        cam.constraints.remove(constraint)
    if cam.animation_data:
        cam.animation_data_clear()
    cam.data.clip_start = 0.002

    best = None
    best_len = -1.0
    for obj in bpy.data.objects:
        if obj.type != "CURVE" or not obj.name.startswith("CS_Leaf_00_"):
            continue
        pts = obj.data.splines[0].bezier_points
        length = ((obj.matrix_world @ pts[-1].co) - (obj.matrix_world @ pts[0].co)).length
        if length > best_len:
            best_len = length
            best = obj
    pts = best.data.splines[0].bezier_points
    world = best.matrix_world
    mid = world @ pts[2].co
    end = world @ pts[-1].co
    tip = mid.lerp(end, 0.78)
    strap = mid.lerp(end, 0.35)
    shoot = bpy.data.objects["CS_Shoot_00"]
    origin = shoot.matrix_world.translation.copy()
    stem = shoot.matrix_world.col[2].xyz.normalized()
    sheath = origin + stem * (0.042 * 0.78) + Vector((0.0, -0.004, 0.0))
    scar = origin + stem * (0.042 * 0.20) + Vector((0.0, -0.002, 0.0))
    shoots = [obj.matrix_world.translation.copy() for obj in bpy.data.objects if obj.name.startswith("CS_Shoot_")]
    center = sum(shoots, Vector()) / len(shoots)

    def look(eye, aim, lens, name):
        cam.location = eye
        cam.rotation_euler = (Vector(aim) - Vector(eye)).to_track_quat("-Z", "Y").to_euler()
        cam.data.lens = lens
        scene.render.filepath = os.path.join(OUT, name + ".jpg")
        bpy.ops.render.render(write_still=True)
        print("STILL", scene.render.filepath)

    look(center + Vector((0.0, -0.48, 0.08)), center + Vector((0.0, 0.0, 0.01)), 40, "patch")
    look(strap + Vector((0.01, -0.09, 0.012)), strap, 55, "strap")
    look(tip + Vector((0.014, -0.058, 0.008)), tip, 70, "tip")
    look(sheath + Vector((0.006, -0.07, 0.008)), sheath, 60, "sheath")
    look(scar + Vector((0.002, -0.046, 0.003)), scar, 80, "scar")
    look(center + Vector((0.0, -0.16, 0.01)), center + Vector((0.0, -0.01, -0.01)), 48, "cut")


if __name__ == "__main__":
    main()
