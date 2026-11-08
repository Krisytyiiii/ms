"""publish(): write the phone .glb from Meadow and the armature only. Curves stay in the blend."""

import os
import shutil

import bpy

from .config import GLB_PATH, MIRROR_GLB, px


def publish(path=GLB_PATH):
    arm = bpy.data.objects[px("Armature")]
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
    mirror = MIRROR_GLB
    if os.path.abspath(path) == os.path.abspath(GLB_PATH) and os.path.abspath(path) != os.path.abspath(mirror):
        shutil.copy2(path, mirror)
    curves = sum(1 for o in bpy.data.objects if o.type == "CURVE" and o.name.startswith(px("")))
    print("exported", path, "and", mirror, "authoring curves still in file:", curves)
    return curves
