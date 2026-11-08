"""publish(): write the phone .glb from Meadow and SI_Armature only. Curves stay in the blend."""

import os
import shutil

import bpy

from .config import GLB_PATH, SPECIES_GLB_PATH

ASSETS_GLB_PATH = SPECIES_GLB_PATH


def publish(path=GLB_PATH):
    norm = os.path.abspath(path).replace("\\", "/").lower()
    if "cymodocea_rotundata" in norm or "rotundata_build" in norm:
        raise RuntimeError("refusing to write a rotundata path: " + path)
    dest_norm = os.path.abspath(ASSETS_GLB_PATH).replace("\\", "/").lower()
    if "cymodocea_rotundata" in dest_norm or "rotundata_build" in dest_norm:
        raise RuntimeError("refusing to write a rotundata path: " + ASSETS_GLB_PATH)
    arm = bpy.data.objects["SI_Armature"]
    meadow = bpy.data.collections["Meadow"]
    for obj in bpy.context.view_layer.objects:
        obj.select_set(False)
    arm.select_set(True)
    for obj in meadow.objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = arm
    os.makedirs(os.path.dirname(path), exist_ok=True)
    op = bpy.ops.export_scene.gltf
    names = {p.identifier for p in op.get_rna_type().properties}
    wanted = {
        "export_format": "GLB",
        "use_selection": True,
        "export_animations": True,
        "export_skins": True,
        "export_morph": False,
        "export_lights": False,
        "export_cameras": False,
        "export_apply": False,
        "export_texcoords": True,
        "export_normals": True,
    }
    kwargs = {k: v for k, v in wanted.items() if k in names}
    op(filepath=path, **kwargs)
    if os.path.abspath(path) == os.path.abspath(GLB_PATH):
        os.makedirs(os.path.dirname(ASSETS_GLB_PATH), exist_ok=True)
        if os.path.abspath(path) != os.path.abspath(ASSETS_GLB_PATH):
            shutil.copy2(path, ASSETS_GLB_PATH)
    curves = sum(1 for obj in bpy.data.objects if obj.type == "CURVE" and obj.name.startswith("SI_"))
    print("exported", path, "and", ASSETS_GLB_PATH, "authoring curves still in file:", curves)
    return curves
