"""Open the saved lesson and render it. Clears subsurface so Eevee can finish."""

import os
import sys

import bpy

ROOT = r"d:\pepot\marinesee\assets\models-3d"
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

BLEND = r"d:\pepot\marinesee\assets\models-3d\enhalus_acoroides\enhalus_acoroides_lesson.blend"
bpy.ops.wm.open_mainfile(filepath=BLEND)

for mat in bpy.data.materials:
    if not mat.use_nodes:
        continue
    bsdf = next((node for node in mat.node_tree.nodes if node.type == "BSDF_PRINCIPLED"), None)
    if bsdf is None:
        continue
    for name in ("Subsurface Weight", "Subsurface"):
        sock = bsdf.inputs.get(name)
        if sock is not None and not sock.is_linked:
            sock.default_value = 0.0

scene = bpy.context.scene
eevee = getattr(scene, "eevee", None)
if eevee is not None and hasattr(eevee, "use_raytracing"):
    eevee.use_raytracing = False

from enhalus_acoroides_build.render import render_lesson  # noqa: E402

out = render_lesson(900, samples=12)
print("LESSON_VIDEO", out)
bpy.ops.wm.save_as_mainfile(filepath=BLEND)
