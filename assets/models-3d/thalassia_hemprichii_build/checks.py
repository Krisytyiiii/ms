"""Done-when checks that can be read from the file (the looks are checked by eye)."""

import bpy

from .config import CONFIG

SAMPLE_FRAMES = (1, 20, 40, 60, 80, 100, 120, 150, 180, 200, 230, 260, 300, 316, 330)


def _shape(cfg):
    """Record range for the ribbons, thick rhizome, scars, and the tannin image."""
    from .util import arc_table, dense_points

    problems = []
    lengths = []
    for obj in bpy.data.objects:
        if obj.type == "CURVE" and obj.name.startswith("TH_Leaf_"):
            pts = dense_points(obj)
            length = arc_table(pts)[-1]
            lengths.append((obj.name, length))
            if length < 0.10 - 1e-3 or length > 0.40 + 1e-3:
                problems.append("leaf %s length %.3f m is outside the record range" % (obj.name, length))
            chord = pts[-1] - pts[0]
            lateral = (chord.x * chord.x + chord.y * chord.y) ** 0.5
            if lateral < 0.02:
                problems.append("leaf %s is straight (lateral %.3f m)" % (obj.name, lateral))
    if not lengths:
        problems.append("no leaves")
    if float(cfg.get("rhizome_radius_m", 0.0)) < 0.0035:
        problems.append("rhizome is not the thick cord")
    if bpy.data.objects.get("RhizomeScars") is None:
        problems.append("missing scars between shoots")
    img = bpy.data.images.get("THLeafBars")
    bars = int(img.get("cr_bars") or 0) if img is not None else 0
    if img is None or img.get("cr_pattern") != "tannin" or bars < 1:
        problems.append("leaf image has no tannin bars")
    controls = bpy.data.objects.get("TH_Controls")
    if controls is not None:
        width = float(controls["leaf_width_m"])
        if abs(width - float(cfg["leaf_width_m"])) > 1e-6:
            problems.append("leaf width does not match the display choice")
        if int(controls.get("tannin_bars", -1)) != int(cfg.get("tannin_bars") or 0):
            problems.append("tannin density does not match the display choice")
    shoots = {}
    roots = {}
    for obj in bpy.data.objects:
        if obj.name.startswith("TH_Leaf_"):
            key = obj.name.split("_")[2]
            shoots[key] = shoots.get(key, 0) + 1
        elif obj.name.startswith("TH_Root_"):
            key = obj.name.split("_")[2]
            roots[key] = roots.get(key, 0) + 1
    if len(shoots) < 2:
        problems.append("need more than one shoot")
    for key, n in sorted(shoots.items()):
        if n < 2 or n > 5:
            problems.append("shoot %s has %d leaves" % (key, n))
    for key, n in sorted(roots.items()):
        if n < 1 or n > 3:
            problems.append("shoot %s has %d roots" % (key, n))
    print("leaf_length_m", [round(length, 3) for _name, length in lengths])
    return problems


def validate(cfg=CONFIG):
    scene = bpy.context.scene
    arm = bpy.data.objects["TH_Armature"]
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
    if int(scene.render.fps) != int(cfg["fps"]):
        problems.append("fps %s" % scene.render.fps)
    if cfg.get("variant") != "lesson" and int(scene.frame_end) != 330:
        problems.append("frame_end %s" % scene.frame_end)
    problems.extend(_shape(cfg))

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
    curves = sum(1 for o in bpy.data.objects if o.type == "CURVE" and o.name.startswith("TH_"))
    if "Grow" not in bpy.data.actions:
        problems.append("missing Grow")
    report = {"triangles": tris, "leaves": leaves, "authoring_curves": curves, "problems": problems[:20]}
    print("validate", report)
    return report
