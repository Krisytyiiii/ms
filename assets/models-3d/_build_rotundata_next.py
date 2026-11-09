"""One sandy plot of smooth ribbon seagrass. Run this inside Blender.

RESET, OVERWRITE_ANIM, and DO_PUBLISH default to false.
A normal run keeps every curve point and calls rebuild_meshes().
Set RESET only for a full replace. publish() writes the draft glb and keeps the curves.
"""

import os
import sys

import bpy

RESET = False
OVERWRITE_ANIM = False
DO_PUBLISH = False

HERE = r"d:\pepot\marinesee\assets\models-3d"
if not os.path.isdir(os.path.join(HERE, "rotundata_next")):
    HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
for _name in [n for n in sys.modules if n == "rotundata_next" or n.startswith("rotundata_next.")]:
    del sys.modules[_name]

from rotundata_next import checks, config, grow, layout, meshes, scene, timeline  # noqa: E402
from rotundata_next import publish as _publish  # noqa: E402
from rotundata_next.util import guard  # noqa: E402


def rebuild_meshes():
    return meshes.rebuild_meshes()


def publish():
    return _publish.publish()


def build(reset=None, overwrite_anim=None, do_publish=None, blend_path=None):
    reset = RESET if reset is None else reset
    overwrite_anim = OVERWRITE_ANIM if overwrite_anim is None else overwrite_anim
    do_publish = DO_PUBLISH if do_publish is None else do_publish
    blend_path = guard(blend_path or config.BLEND_PATH)
    print("blender", bpy.app.version_string)
    print("timeline", timeline.self_check(config.CONFIG["shoot_count"], config.CONFIG["min_bone_scale"]))
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    scene.setup_scene()
    if reset or bpy.data.objects.get("CR_Rhizome") is None:
        scene.clear_plant()
        layout.create_plant()
        overwrite_anim = True
    rebuild_meshes()
    arm = bpy.data.objects["CR_Armature"]
    if overwrite_anim or bpy.data.actions.get("Grow") is None:
        grow.animate(arm)
    report = checks.validate()
    os.makedirs(os.path.dirname(blend_path), exist_ok=True)
    bpy.context.scene.frame_set(300)
    rh = bpy.data.objects["CR_Rhizome"]
    p0 = rh.data.splines[0].bezier_points[0].co
    print("RHIZOME_P0", tuple(round(float(v), 6) for v in p0), "count", len(rh.data.splines[0].bezier_points))
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print("saved", blend_path)
    if report["problems"]:
        print("VALIDATE_FAIL", report["problems"])
    else:
        print("VALIDATE_OK", report["triangles"])
    if do_publish:
        if report["problems"]:
            raise RuntimeError("not publishing a meadow that failed checks")
        publish()
        bpy.ops.wm.save_as_mainfile(filepath=blend_path)
        still = sum(1 for o in bpy.data.objects if o.type == "CURVE" and o.name.startswith("CR_"))
        print("curves after publish", still)
    return report


if __name__ == "__main__":
    args = set(sys.argv)
    resetting = "--reset" in args
    blend = config.BLEND_PATH
    if not resetting and os.path.isfile(blend) and os.path.abspath(bpy.data.filepath) != os.path.abspath(blend):
        bpy.ops.wm.open_mainfile(filepath=blend)
    report = build(
        reset=True if resetting else False,
        overwrite_anim=True if "--overwrite-anim" in args else False,
        do_publish=True if "--publish" in args else False,
    )
    if "--preview" in args:
        from rotundata_next.preview import render_views

        render_views()
        bpy.ops.wm.save_as_mainfile(filepath=blend)
        cam = bpy.data.objects.get("Camera")
        if cam and cam.animation_data and cam.animation_data.action:
            raise RuntimeError("preview animated the camera")
