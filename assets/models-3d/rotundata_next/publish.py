"""Write the draft glb from Meadow and CR_Armature. Curves stay in the blend."""

import os

import bpy

from . import checks
from .config import GLB_PATH
from .util import guard


def _choice(prop, prefer):
    items = []
    if prop is not None and getattr(prop, "enum_items", None):
        items = [item.identifier for item in prop.enum_items]
    print("choices", list(prefer), items)
    for name in prefer:
        if name in items or not items:
            return name
    for item in items:
        if any(name.lower() in item.lower() for name in prefer):
            return item
    return None


def publish(path=None):
    path = guard(path or GLB_PATH)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    try:
        import addon_utils

        addon_utils.enable("io_scene_gltf2")
    except (ImportError, RuntimeError, ValueError) as exc:
        print("gltf addon", exc)
    if not hasattr(bpy.ops.export_scene, "gltf"):
        raise RuntimeError("this Blender has no glTF exporter")

    arm = bpy.data.objects["CR_Armature"]
    meadow = bpy.data.collections["Meadow"]
    arm.hide_viewport = False
    arm.hide_render = False
    try:
        arm.hide_set(False)
    except RuntimeError:
        pass
    for obj in bpy.context.view_layer.objects:
        obj.select_set(False)
    arm.select_set(True)
    for obj in meadow.objects:
        if obj.type == "MESH":
            obj.select_set(True)
    for obj in bpy.context.view_layer.objects:
        if obj.select_get() and obj.type in {"CAMERA", "LIGHT", "CURVE"}:
            raise RuntimeError("refusing to export %s" % obj.name)
    bpy.context.view_layer.objects.active = arm

    op = bpy.ops.export_scene.gltf
    props = {p.identifier: p for p in op.get_rna_type().properties}
    wanted = {
        "export_format": _choice(props.get("export_format"), ("GLB",)),
        "use_selection": True,
        "export_animations": True,
        "export_skins": True,
        "export_morph": False,
        "export_lights": False,
        "export_cameras": False,
        "export_apply": False,
        "export_texcoords": True,
        "export_normals": True,
        "export_yup": True,
        "export_materials": "EXPORT",
        "export_bake_animation": True,
        "export_force_sampling": True,
        "export_frame_range": True,
        "export_anim_slide_to_zero": True,
    }
    mode = _choice(props.get("export_animation_mode"), ("ACTIVE_ACTIONS", "ACTIONS"))
    if mode:
        wanted["export_animation_mode"] = mode
    if "export_nla_strips_merged_animation_name" in props:
        wanted["export_nla_strips_merged_animation_name"] = "Grow"
    kwargs = {}
    for key, value in wanted.items():
        if key not in props or value is None:
            continue
        prop = props[key]
        if getattr(prop, "enum_items", None):
            allowed = {item.identifier for item in prop.enum_items}
            if value not in allowed:
                print("skip", key, value)
                continue
        kwargs[key] = value
    if "export_format" not in kwargs or "use_selection" not in kwargs:
        raise RuntimeError("glTF exporter is missing selection or GLB format")
    print("gltf export", kwargs)
    op(filepath=path, **kwargs)

    tris = 0
    for obj in meadow.objects:
        if obj.type == "MESH":
            obj.data.calc_loop_triangles()
            tris += len(obj.data.loop_triangles)
    curves = sum(1 for o in bpy.data.objects if o.type == "CURVE" and o.name.startswith("CR_"))
    print("TRIANGLE_COUNT", tris)
    print("authoring curves still in file:", curves)
    problems = checks.inspect_glb(path, tris)
    if curves < 3:
        problems.append("publish removed the curves")
    if problems:
        print("PUBLISH_FAIL", problems)
        raise RuntimeError("draft glb failed checks: %s" % problems[:8])
    print("PUBLISH_OK", path)
    return curves
