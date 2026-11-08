"""Read the serrulata phone glb. Does not open or write a rotundata file."""

import os
import sys

import bpy

GLB = r"d:\pepot\marinesee\app\assets\models-3d\cymodocea_serrulata.glb"
if "cymodocea_rotundata" in os.path.abspath(GLB).replace("\\", "/").lower():
    raise SystemExit("refusing rotundata path")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)

cams = [obj.name for obj in bpy.data.objects if obj.type == "CAMERA"]
curves = [obj.name for obj in bpy.data.objects if obj.type == "CURVE"]
tris = 0
for obj in bpy.data.objects:
    if obj.type != "MESH":
        continue
    obj.data.calc_loop_triangles()
    tris += len(obj.data.loop_triangles)

actions = []
for action in bpy.data.actions:
    actions.append((action.name, getattr(action, "frame_start", None), getattr(action, "frame_end", None)))

print("GLB_TRIS", tris)
print("GLB_CAMERAS", cams)
print("GLB_CURVES", curves)
print("GLB_ACTIONS", actions)
print("GLB_FPS", bpy.context.scene.render.fps)
