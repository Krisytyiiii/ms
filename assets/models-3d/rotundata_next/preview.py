"""Still views of frames 1, 120, 200, and 300. The camera is not keyed."""

import os

import bpy
from mathutils import Vector

from .config import CONFIG, PREVIEW_DIR
from .util import look_at


def _engine():
    prop = bpy.types.RenderSettings.bl_rna.properties["engine"]
    names = [item.identifier for item in prop.enum_items]
    for name in names:
        if "EEVEE" in name:
            return name
    return names[0]


def _bounds():
    low = Vector((1e9, 1e9, 1e9))
    high = Vector((-1e9, -1e9, -1e9))
    for obj in bpy.data.collections["Meadow"].objects:
        if obj.type != "MESH":
            continue
        for corner in obj.bound_box:
            world = obj.matrix_world @ Vector(corner)
            low.x, low.y, low.z = min(low.x, world.x), min(low.y, world.y), min(low.z, world.z)
            high.x, high.y, high.z = max(high.x, world.x), max(high.y, world.y), max(high.z, world.z)
    return low, high


def _mesh_world(obj):
    """Deformed vertices, so a short bud is framed as it stands on that frame."""
    deps = bpy.context.evaluated_depsgraph_get()
    baked = obj.evaluated_get(deps)
    return [obj.matrix_world @ vert.co for vert in baked.data.vertices]


def _hero_points():
    hero = next(o for o in bpy.data.objects if o.type == "MESH" and o.get("cr_hero"))
    worlds = _mesh_world(hero)
    tip = max(worlds, key=lambda p: p.z)
    return tip


def _shoot_focus(name):
    obj = bpy.data.objects[name]
    worlds = _mesh_world(obj)
    low = Vector((min(p.x for p in worlds), min(p.y for p in worlds), min(p.z for p in worlds)))
    high = Vector((max(p.x for p in worlds), max(p.y for p in worlds), max(p.z for p in worlds)))
    return (low + high) * 0.5


def _shot(cam, location, target, ortho=None):
    cam.animation_data_clear()
    cam.location = location
    look_at(cam, target)
    if ortho is None:
        cam.data.type = "PERSP"
        cam.data.lens = 48
    else:
        cam.data.type = "ORTHO"
        cam.data.ortho_scale = ortho
    cam.animation_data_clear()


def render_views(cfg=CONFIG):
    os.makedirs(PREVIEW_DIR, exist_ok=True)
    scene = bpy.context.scene
    scene.tool_settings.use_keyframe_insert_auto = False
    scene.render.engine = _engine()
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = "PNG"
    scene.render.use_overwrite = True
    eevee = getattr(scene, "eevee", None)
    if eevee is not None:
        for attr in ("taa_render_samples", "taa_samples"):
            if hasattr(eevee, attr):
                setattr(eevee, attr, 16)
    cam = scene.camera or bpy.data.objects.get("Camera")
    scene.camera = cam
    scene.frame_set(300)
    bpy.context.view_layer.update()
    low, high = _bounds()
    center = (low + high) * 0.5
    size = high - low
    dist = max(size.x, size.y, size.z, 0.2) * 1.55
    front = Vector((center.x, high.y + dist, center.z + size.z * 0.15))
    side = Vector((high.x + dist * 0.95, center.y - size.y * 0.35, high.z * 0.15 + 0.12))
    jobs = []
    for frame in (1, 120, 200, 300):
        jobs.append((frame, "front", front, center, None))
        jobs.append((frame, "side", side, center, None))
    scene.frame_set(300)
    bpy.context.view_layer.update()
    tip = _hero_points()
    stem = _shoot_focus("Shoot_00")
    scene.frame_set(1)
    bpy.context.view_layer.update()
    bud = _shoot_focus("Shoot_00")
    jobs.append((300, "tip_front", tip + Vector((0.0, 0.05, 0.0)), tip, 0.028))
    jobs.append((300, "tip_side", tip + Vector((0.05, 0.0, 0.002)), tip, 0.028))
    jobs.append((300, "stem_front", stem + Vector((0.0, 0.06, 0.0)), stem, 0.045))
    jobs.append((1, "bud_front", bud + Vector((0.0, 0.07, 0.008)), bud, 0.055))
    jobs.append((1, "bud_side", bud + Vector((0.07, 0.0, 0.008)), bud, 0.055))
    for frame, label, location, target, ortho in jobs:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        _shot(cam, location, target, ortho)
        scene.render.filepath = os.path.join(PREVIEW_DIR, "frame_%03d_%s.png" % (frame, label))
        bpy.ops.render.render(write_still=True)
        print("preview", scene.render.filepath)
    _shot(cam, front, center, None)
    cam.animation_data_clear()
    print("PREVIEW_OK", PREVIEW_DIR)
