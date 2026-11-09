"""Scene clock, still camera, and the RESET wipe.

The camera and the lights stay in the blend. Nothing here keys the camera.
"""

import math

import bpy
from mathutils import Vector

from .config import CONFIG
from .util import look_at, sock, srgb

PLANT_PREFIXES = ("CR_", "Shoot_", "Leaf_", "Root_", "Rhizome", "Sand")


def setup_scene(cfg=CONFIG):
    scene = bpy.context.scene
    scene.render.fps = int(cfg["fps"])
    scene.render.fps_base = 1.0
    scene.frame_start = 1
    scene.frame_end = int(cfg["frame_end"])
    scene.tool_settings.use_keyframe_insert_auto = False
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    bg = next(node for node in world.node_tree.nodes if node.type == "BACKGROUND")
    # Viewer teal, so a still reads the way the phone backdrop does. Not exported.
    sock(bg, "Color").default_value = srgb(0.118, 0.549, 0.596)
    sock(bg, "Strength").default_value = 0.85

    sun = bpy.data.objects.get("Light")
    if sun and sun.type == "LIGHT":
        sun.data.type = "SUN"
        sun.data.energy = 3.6
        sun.data.angle = 0.55
        sun.data.color = (1.0, 0.97, 0.90)
        sun.rotation_euler = (math.radians(52), math.radians(-8), math.radians(28))
        sun.animation_data_clear()
    fill = bpy.data.objects.get("Fill")
    if fill is None:
        fill = bpy.data.objects.new("Fill", bpy.data.lights.new("Fill", "SUN"))
        scene.collection.objects.link(fill)
    fill.data.energy = 1.6
    fill.data.color = (0.78, 0.90, 0.92)
    fill.rotation_euler = (math.radians(72), math.radians(6), math.radians(160))
    fill.animation_data_clear()

    cam = bpy.data.objects.get("Camera")
    if cam is None or cam.type != "CAMERA":
        cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
        scene.collection.objects.link(cam)
    cam.location = (0.0, 0.72, 0.16)
    look_at(cam, Vector((0.0, 0.0, 0.04)))
    cam.data.type = "PERSP"
    cam.data.lens = 50
    cam.data.clip_start = 0.01
    cam.data.clip_end = 20
    cam.animation_data_clear()
    scene.camera = cam


def clear_plant():
    for obj in list(bpy.data.objects):
        if obj.type in {"CAMERA", "LIGHT"}:
            continue
        if obj.get("cr_plant") or obj.name == "Cube" or obj.name.startswith(PLANT_PREFIXES):
            bpy.data.objects.remove(obj, do_unlink=True)
    for name in ("Authoring", "Meadow", "Reef"):
        col = bpy.data.collections.get(name)
        if col is not None:
            bpy.data.collections.remove(col)
    action = bpy.data.actions.get("Grow")
    if action is not None:
        bpy.data.actions.remove(action)
    for blocks in (bpy.data.meshes, bpy.data.curves, bpy.data.armatures, bpy.data.materials, bpy.data.images):
        for block in list(blocks):
            if block.users == 0:
                blocks.remove(block)
