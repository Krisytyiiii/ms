"""Lesson words are burned in as bottom subtitles. This file does not build 3D text."""

import bpy


def clear():
    for obj in list(bpy.data.objects):
        if obj.type == "FONT" or obj.name.startswith(("SI_Caption_", "SI_Note_", "SI_Card", "SI_Rule", "SI_Species", "SI_More_")):
            data = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            if data is not None and getattr(data, "users", 0) == 0:
                if isinstance(data, bpy.types.Curve):
                    bpy.data.curves.remove(data)
                elif isinstance(data, bpy.types.Mesh):
                    bpy.data.meshes.remove(data)


def build(frame_end=900):
    del frame_end
    clear()
    print("no floating text")
