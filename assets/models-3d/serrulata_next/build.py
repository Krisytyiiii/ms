"""Build the serrulata meadow, check it, and write the draft files."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from serrulata_next.checks import check_glb, check_scene
from serrulata_next.config import BLEND
from serrulata_next.preview import render_previews
from serrulata_next.publish import export_glb, save_blend
from serrulata_next.scene import build


def main():
    arm, _objects, _action = build()
    problems, blend_tris = check_scene(arm)
    for line in problems:
        print("FAIL", line)
    if problems:
        save_blend()
        raise SystemExit(1)
    curves = [obj for obj in bpy_curves()]
    export_glb(arm)
    if len(curves) < 4:
        print("FAIL curves disappeared")
        save_blend()
        raise SystemExit(1)
    glb_problems, glb_tris = check_glb()
    if glb_tris != blend_tris:
        glb_problems.append(f"triangle mismatch blend {blend_tris} glb {glb_tris}")
    for line in glb_problems:
        print("FAIL", line)
    if glb_problems:
        save_blend()
        raise SystemExit(1)
    render_previews(arm)
    save_blend()
    print(f"BUILD_DONE {BLEND}")


def bpy_curves():
    import bpy
    return [obj for obj in bpy.data.collections["Authoring"].objects if obj.type == "CURVE"]


if __name__ == "__main__":
    main()
