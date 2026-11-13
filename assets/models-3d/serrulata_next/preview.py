"""Still frames so the strap, tip, sheath, and open scars can be checked by eye."""

import bpy
from mathutils import Vector

from serrulata_next.config import PREVIEW


def _engine(scene):
    names = [item.identifier for item in scene.render.bl_rna.properties["engine"].enum_items]
    for choice in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        if choice in names:
            scene.render.engine = choice
            return
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 16


def _look(cam, place, target):
    cam.location = place
    cam.rotation_euler = (Vector(target) - Vector(place)).to_track_quat("-Z", "Y").to_euler()


def _shot(scene, cam, place, target, frame, filename, ortho=None):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    _look(cam, place, target)
    cam.data.type = "ORTHO" if ortho else "PERSP"
    if ortho:
        cam.data.ortho_scale = ortho
    else:
        cam.data.lens = 50
    scene.render.filepath = str(PREVIEW / filename)
    bpy.ops.render.render(write_still=True)
    print(f"preview {filename}")


def render_previews(arm):
    PREVIEW.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    _engine(scene)
    scene.render.resolution_x = 960
    scene.render.resolution_y = 540
    scene.render.image_settings.file_format = "PNG"
    if hasattr(scene, "eevee"):
        scene.eevee.taa_render_samples = 16
    try:
        scene.view_settings.view_transform = "Standard"
    except TypeError:
        pass
    world = bpy.data.worlds.new("PreviewWorld")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.12, 0.45, 0.48, 1.0)
    bg.inputs[1].default_value = 0.85

    col = bpy.data.collections.new("Preview")
    scene.collection.children.link(col)
    sun_data = bpy.data.lights.new("PreviewSun", "SUN")
    sun_data.energy = 2.0
    sun = bpy.data.objects.new("PreviewSun", sun_data)
    sun.rotation_euler = (0.55, 0.15, 0.6)
    col.objects.link(sun)
    fill_data = bpy.data.lights.new("PreviewFill", "AREA")
    fill_data.energy = 30
    fill = bpy.data.objects.new("PreviewFill", fill_data)
    fill.location = (0.1, -0.4, 0.2)
    fill.rotation_euler = (1.2, 0.0, 0.0)
    col.objects.link(fill)

    cam_data = bpy.data.cameras.new("PreviewCamera")
    cam_data.clip_start = 0.01
    cam_data.clip_end = 20
    cam = bpy.data.objects.new("PreviewCamera", cam_data)
    col.objects.link(cam)
    scene.camera = cam

    center = Vector((0.03, 0.02, 0.07))
    _shot(scene, cam, (0.03, -1.05, 0.16), center, 1, "frame_001_front.png")
    _shot(scene, cam, (1.05, 0.02, 0.16), center, 1, "frame_001_side.png")
    _shot(scene, cam, (0.03, -1.05, 0.16), center, 120, "frame_120_front.png")
    _shot(scene, cam, (0.03, -1.05, 0.16), center, 200, "frame_200_front.png")
    _shot(scene, cam, (0.03, -1.05, 0.16), center, 300, "frame_300_front.png")
    _shot(scene, cam, (1.05, 0.02, 0.16), center, 300, "frame_300_side.png")
    _shot(scene, cam, (0.03, 0.02, 1.15), (0.03, 0.02, 0.0), 300, "frame_300_top.png")

    scene.frame_set(300)
    bpy.context.view_layer.update()
    names = [pb.name for pb in arm.pose.bones if pb.name.startswith("leaf_00_")]
    tip_bone = arm.pose.bones[names[-1]]
    tip = tip_bone.tail
    _shot(scene, cam, tip + Vector((0.0, -0.06, 0.0)), tip, 300, "frame_300_tip.png", ortho=0.04)
    stem = arm.pose.bones["shoot_00"]
    scar = (stem.head + stem.tail) * 0.5
    _shot(scene, cam, scar + Vector((0.0, -0.05, 0.0)), scar, 300, "frame_300_stem.png", ortho=0.045)
