"""One armature. Every deform bone is a child of an unscaled base bone."""

import bpy
from mathutils import Vector


def build_armature(specs):
    arm_data = bpy.data.armatures.new("HU_Armature")
    arm = bpy.data.objects.new("HU_Armature", arm_data)
    bpy.context.scene.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    base = arm_data.edit_bones.new("base")
    base.head = Vector((0.0, 0.0, 0.0))
    base.tail = Vector((0.0, 0.0, 0.02))
    base.use_deform = True
    for name, head, tail, roll_hint in specs:
        bone = arm_data.edit_bones.new(name)
        bone.head = Vector(head)
        bone.tail = Vector(tail)
        bone.parent = base
        bone.use_connect = False
        bone.use_deform = True
        if roll_hint is not None:
            bone.align_roll(Vector(roll_hint))
    bpy.ops.object.mode_set(mode="POSE")
    for pb in arm.pose.bones:
        pb.rotation_mode = "XYZ"
    return arm
