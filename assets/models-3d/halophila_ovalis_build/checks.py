"""Done-when checks that can be read from the file (the looks are checked by eye)."""

import bpy

from .config import CONFIG

SAMPLE_FRAMES = (1, 20, 40, 60, 80, 100, 120, 150, 180, 200, 230, 260, 300, 316, 330)


def _ovalis(cfg):
    """Paired oval leaves and eight cross-vein pairs. No hairs. No strap fan."""
    problems = []
    controls = bpy.data.objects.get("HO_Controls")
    if controls is None:
        return ["missing HO_Controls"]
    pairs = int(controls.get("cross_vein_pairs", 0))
    if pairs != 8:
        problems.append("cross-vein pairs %s is not 8" % pairs)
    if int(controls.get("hairs", 1)) != 0:
        problems.append("leaf surface has hairs")
    width = float(controls.get("leaf_width_m", 0.0))
    want = float(cfg["leaf_width_m"])
    if abs(width - want) > 1e-6:
        problems.append("blade width %.4f is not the display width %.4f" % (width, want))
    img = bpy.data.images.get("HoLeafVeins")
    if img is None or int(img.get("ho_cross_pairs", 0)) != 8 or int(img.get("ho_hairs", 1)) != 0:
        problems.append("leaf image is not 8 hairless cross-vein pairs")
    shoots = {}
    stamped = None
    for obj in bpy.data.objects:
        if obj.type == "MESH" and obj.name.startswith("Leaf_"):
            if stamped is None:
                stamped = int(obj.data.get("ho_cross_pairs", 0))
        if obj.name.startswith("HO_Leaf_"):
            key = obj.name.split("_")[2]
            shoots[key] = shoots.get(key, 0) + 1
    if stamped != 8:
        problems.append("leaf mesh cross-vein pairs %s is not 8" % stamped)
    if len(shoots) < 2:
        problems.append("need more than one pair")
    for key, n in sorted(shoots.items()):
        if n != 2:
            problems.append("shoot %s has %d leaves, not a pair" % (key, n))
    return problems


def _lesson_shape(cfg):
    """Internodes and root counts for the lesson meadow."""
    from .util import arc_table, dense_points

    problems = []
    rh = bpy.data.objects.get("HO_Rhizome")
    if rh is None:
        return ["missing rhizome"]
    dense = dense_points(rh)
    cum = arc_table(dense)
    count = int(rh.get("cr_nodes", 0))
    per = 48
    spans = []
    for k in range(count - 1):
        a = min(len(cum) - 1, 2 * k * per)
        b = min(len(cum) - 1, 2 * (k + 1) * per)
        spans.append(cum[b] - cum[a])
    for i, span in enumerate(spans):
        if span < 0.010 - 1e-4 or span > 0.045 + 1e-4:
            problems.append("internode %d is %.2f cm" % (i, span * 100))
    roots = {}
    for obj in bpy.data.objects:
        if obj.name.startswith("HO_Root_"):
            key = obj.name.split("_")[2]
            roots[key] = roots.get(key, 0) + 1
    for key, n in sorted(roots.items()):
        if n < 1 or n > 3:
            problems.append("shoot %s has %d roots" % (key, n))
    ys = []
    for obj in bpy.data.objects:
        if obj.name.startswith("HO_Shoot_"):
            ys.append(obj.matrix_world.translation.y)
    if ys and max(ys) - min(ys) < 0.04:
        problems.append("shoots span only %.1f cm in depth" % ((max(ys) - min(ys)) * 100))
    print("lesson spans_cm", [round(s * 100, 2) for s in spans])
    return problems


def validate(cfg=CONFIG):
    scene = bpy.context.scene
    arm = bpy.data.objects["HO_Armature"]
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
    problems.extend(_ovalis(cfg))
    if cfg.get("variant") == "lesson":
        problems.extend(_lesson_shape(cfg))

    curves = sum(1 for o in bpy.data.objects if o.type == "CURVE" and o.name.startswith("HO_"))
    if "Grow" not in bpy.data.actions:
        problems.append("missing Grow")
    report = {
        "triangles": tris,
        "leaves": leaves,
        "cross_vein_pairs": 8,
        "authoring_curves": curves,
        "problems": problems[:20],
    }
    print("validate", report)
    return report
