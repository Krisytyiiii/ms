"""Done-when checks that can be read from the file (the looks are checked by eye)."""

import bpy

from .config import px, CONFIG

SAMPLE_FRAMES = (1, 20, 40, 60, 80, 100, 120, 150, 180, 200, 230, 260, 300, 316, 330)


def _lesson_shape(cfg):
    """Shoots, leaves, and roots are present. Width matches the display control."""
    problems = []
    controls = bpy.data.objects.get(px("Controls"))
    if controls is None:
        return ["missing controls"]
    width = float(controls["leaf_width_m"])
    if abs(width - float(cfg["leaf_width_m"])) > 1e-6:
        problems.append("leaf width does not match the display control")
    shoots = {}
    roots = {}
    for obj in bpy.data.objects:
        if obj.name.startswith(px("Leaf_")):
            key = obj.name.split("_")[2]
            shoots[key] = shoots.get(key, 0) + 1
        elif obj.name.startswith(px("Root_")):
            key = obj.name.split("_")[2]
            roots[key] = roots.get(key, 0) + 1
    if len(shoots) != int(cfg["shoot_count"]):
        problems.append("shoot count %d" % len(shoots))
    for key, n in sorted(shoots.items()):
        if n < 2 or n > 4:
            problems.append("shoot %s has %d leaves" % (key, n))
    for key, n in sorted(roots.items()):
        if n < 1 or n > 3:
            problems.append("shoot %s has %d roots" % (key, n))
    ys = []
    for obj in bpy.data.objects:
        if obj.name.startswith(px("Shoot_")):
            ys.append(obj.matrix_world.translation.y)
    if ys and max(ys) - min(ys) < 0.006:
        problems.append("shoots are flat in depth")
    return problems


def validate(cfg=CONFIG):
    scene = bpy.context.scene
    arm = bpy.data.objects[px("Armature")]
    meadow = bpy.data.collections["Meadow"]
    tiny = cfg["min_bone_scale"]
    problems = []
    tris = 0
    leaves = 0
    for obj in meadow.objects:
        if obj.type != "MESH":
            continue
        obj.data.calc_loop_triangles()
        tris += len(obj.data.loop_triangles)
        leaves += obj.name.startswith("Leaf_")
        if any(abs(v - 1.0) > 1e-6 for v in obj.scale):
            problems.append("object scale %s %s" % (obj.name, tuple(obj.scale)))
    if tris > 40000:
        problems.append("triangles %d > 40000" % tris)
    if not any(obj.name == "RhizomeBristles" for obj in meadow.objects):
        problems.append("missing bristles")

    samples = list(SAMPLE_FRAMES)
    if cfg["frame_end"] not in samples:
        samples.append(cfg["frame_end"])
    poses = {}
    for f in samples:
        scene.frame_set(f)
        for pb in arm.pose.bones:
            if pb.name == "base":
                continue
            sx, sy, sz = pb.scale
            if sy < tiny - 1e-4 or abs(sx - 1) > 1e-4 or abs(sz - 1) > 1e-4:
                problems.append("bone %s frame %d scale %s" % (pb.name, f, tuple(pb.scale)))
            if f in (1, cfg["frame_end"]):
                poses.setdefault(pb.name, []).append(pb.matrix_basis.copy())
    # The lesson minute ends on the patch. The phone restarts the clip from the bud.
    if cfg.get("variant") != "lesson":
        for name, (a, b) in poses.items():
            if any(abs(a[r][c] - b[r][c]) > 1e-4 for r in range(4) for c in range(4)):
                problems.append("loop mismatch %s" % name)
    if cfg.get("variant") == "lesson":
        problems.extend(_lesson_shape(cfg))

    curves = sum(1 for o in bpy.data.objects if o.type == "CURVE" and o.name.startswith(px("")))
    if "Grow" not in bpy.data.actions:
        problems.append("missing Grow")
    report = {"triangles": tris, "leaves": leaves, "authoring_curves": curves, "problems": problems[:20]}
    print("validate", report)
    return report
