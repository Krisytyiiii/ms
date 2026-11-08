"""publish(): write the phone .glb from Meadow and CS_Armature only. Curves stay in the blend."""

import os
import shutil

import bpy

from .config import GLB_PATH

ASSETS_GLB_PATH = r"d:\pepot\marinesee\assets\models-3d\cymodocea_serrulata\cymodocea_serrulata.glb"


def publish(path=GLB_PATH):
    norm = os.path.abspath(path).replace("\\", "/").lower()
    if "cymodocea_rotundata" in norm:
        raise RuntimeError("refusing to write a rotundata path")
    arm = bpy.data.objects["CS_Armature"]
    meadow = bpy.data.collections["Meadow"]
    for obj in bpy.context.view_layer.objects:
        obj.select_set(False)
    arm.select_set(True)
    for obj in meadow.objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = arm
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
    # The phone export is mirrored into assets/. A named variant (realistic, aquarium)
    # keeps its own file and does not replace that mirror.
    if os.path.abspath(path) == os.path.abspath(GLB_PATH):
        shutil.copy2(path, ASSETS_GLB_PATH)
    curves = sum(1 for o in bpy.data.objects if o.type == "CURVE" and o.name.startswith("CS_"))
    print("exported", path, "and", ASSETS_GLB_PATH, "authoring curves still in file:", curves)
    return curves
