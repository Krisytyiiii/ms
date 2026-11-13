"""Write the draft blend and the draft glb. Neither file goes in app/."""

import bpy

from ovalis_next.config import BLEND, GLB


def export_glb(arm):
    GLB.parent.mkdir(parents=True, exist_ok=True)
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")
    for obj in bpy.data.collections["Meadow"].all_objects:
        if obj.type in {"MESH", "ARMATURE"}:
            obj.hide_set(False)
            obj.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.export_scene.gltf(
        filepath=str(GLB),
        export_format="GLB",
        use_selection=True,
        export_animations=True,
        export_animation_mode="ACTIVE_ACTIONS",
        export_nla_strips=False,
        export_nla_strips_merged_animation_name="Grow",
        export_frame_range=True,
        export_force_sampling=True,
        export_optimize_animation_size=False,
        export_sampling_interpolation_fallback="STEP",
        export_cameras=False,
        export_lights=False,
        export_skins=True,
        export_yup=True,
        export_apply=False,
        export_morph=False,
    )
    print(f"wrote {GLB}")


def save_blend():
    BLEND.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    print(f"wrote {BLEND}")
