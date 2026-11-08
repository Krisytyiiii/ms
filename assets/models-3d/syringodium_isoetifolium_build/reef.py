"""Lights and a still phone camera. The sand bed is the meadow, not a tank."""

import math

import bpy
from mathutils import Vector

from .util import sock, srgb


def _sea(strength=0.55):
    world = bpy.context.scene.world
    if world and world.use_nodes:
        bg = next(node for node in world.node_tree.nodes if node.type == "BACKGROUND")
        sock(bg, "Color").default_value = srgb(0.118, 0.549, 0.596)
        sock(bg, "Strength").default_value = strength


def _light():
    sun = bpy.data.objects.get("Light")
    if sun and sun.type == "LIGHT":
        sun.data.type = "SUN"
        sun.data.energy = 4.4
        sun.data.color = (1.0, 0.96, 0.88)
        sun.data.angle = 0.45
        sun.rotation_euler = (math.radians(48), math.radians(-18), math.radians(-28))
    fill = bpy.data.objects.get("Fill")
    if fill and fill.type == "LIGHT":
        fill.data.type = "SUN"
        fill.data.energy = 1.6
        fill.data.color = (0.78, 0.88, 0.92)
        fill.rotation_euler = (math.radians(78), math.radians(8), math.radians(18))
    rim = bpy.data.objects.get("Rim")
    if rim is None:
        rim = bpy.data.objects.new("Rim", bpy.data.lights.new("Rim", "SUN"))
        bpy.context.scene.collection.objects.link(rim)
    rim.data.energy = 2.2
    rim.data.color = (0.92, 0.96, 1.0)
    rim.rotation_euler = (math.radians(62), math.radians(24), math.radians(140))


def _still_camera():
    cam = bpy.data.objects.get("Camera")
    if cam is None or cam.type != "CAMERA":
        return
    for constraint in list(cam.constraints):
        cam.constraints.remove(constraint)
    if cam.animation_data:
        cam.animation_data_clear()
    eye = Vector((0.01, -0.52, 0.14))
    aim = Vector((0.0, 0.0, 0.06))
    cam.location = eye
    cam.rotation_euler = (aim - eye).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = 48
    cam.data.clip_start = 0.002
    cam.data.clip_end = 30
    bpy.context.scene.camera = cam


def build_presentation():
    from .config import CONFIG

    _sea(0.42 if CONFIG.get("presentation") == "phone" else 0.7)
    _light()
    if CONFIG.get("presentation") != "lesson":
        _still_camera()
    print("lights ready")
