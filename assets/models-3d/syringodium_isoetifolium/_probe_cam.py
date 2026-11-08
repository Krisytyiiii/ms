"""Print lesson camera positions. Not part of the model."""

import bpy

BLEND = r"d:\pepot\marinesee\assets\models-3d\syringodium_isoetifolium\blender\syringodium_isoetifolium_lesson.blend"
bpy.ops.wm.open_mainfile(filepath=BLEND)
cam = bpy.data.objects["Camera"]
hero = next(obj for obj in bpy.data.objects if obj.get("cr_hero"))
tip = hero.matrix_world @ hero.data.splines[0].bezier_points[-1].co
print("TIP", tuple(round(v, 3) for v in tip))
for frame in (1, 260, 477, 566, 665, 761, 900):
    bpy.context.scene.frame_set(frame)
    loc = cam.matrix_world.translation
    print("FRAME", frame, "EYE", tuple(round(v, 3) for v in loc), "LENS", round(cam.data.lens, 1))
