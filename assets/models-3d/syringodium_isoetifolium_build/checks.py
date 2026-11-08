"""Done-when checks that can be read from the file (the looks are checked by eye)."""

import bpy
from mathutils import Vector

from .config import CONFIG

SAMPLE_FRAMES = (1, 20, 40, 60, 80, 100, 120, 150, 180, 200, 230, 260, 300, 316, 330)
LENGTH_LO = 0.07
LENGTH_HI = 0.30


def _leaf_curves():
    return [obj for obj in bpy.data.objects if obj.type == "CURVE" and obj.name.startswith("SI_Leaf_")]


def _lengths(cfg):
    from .util import arc_table, dense_points

    problems = []
    pair = cfg["leaf_length_m"]
    if pair[0] < LENGTH_LO - 1e-9 or pair[1] > LENGTH_HI + 1e-9 or pair[0] > pair[1]:
        problems.append("leaf length pair is outside the record range")
    arcs = []
    for obj in _leaf_curves():
        arcs.append(arc_table(dense_points(obj))[-1])
        if arcs[-1] < LENGTH_LO - 0.002 or arcs[-1] > LENGTH_HI + 0.002:
            problems.append("%s length is outside the record range" % obj.name)
            if len(problems) > 8:
                break
    if arcs:
        print("leaf arc m", round(min(arcs), 3), round(max(arcs), 3))
    else:
        problems.append("missing leaf curves")
    return problems, (round(min(arcs), 4), round(max(arcs), 4)) if arcs else (0.0, 0.0)


def _round_section():
    """A strap is thin one way. A noodle leaf is round in a mid-leaf ring."""
    arm = bpy.data.objects.get("SI_Armature")
    if arm is None:
        return ["missing armature"], 0.0
    leaf = next((obj for obj in bpy.data.collections["Meadow"].objects if obj.name.startswith("Leaf_") and obj.get("cr_plant")), None)
    if leaf is None or leaf.type != "MESH":
        leaf = next((obj for obj in bpy.data.collections["Meadow"].objects if obj.name.startswith("Leaf_")), None)
    if leaf is None or leaf.type != "MESH":
        return ["missing leaf mesh"], 0.0
    bone = arm.data.bones.get("leaf_" + leaf.name[len("Leaf_"):])
    if bone is None:
        return ["missing leaf bone"], 0.0
    # Measure the open leaf, not the shortened start of Grow.
    bpy.context.scene.frame_set(200 if CONFIG.get("presentation") != "lesson" else 1)
    bpy.context.view_layer.update()
    head = arm.matrix_world @ bone.head_local
    tail = arm.matrix_world @ bone.tail_local
    axis = tail - head
    span = axis.length
    if span < 1e-6:
        return ["leaf bone has no length"], 0.0
    axis = axis.normalized()
    pairs = []
    target = 0.45 * span
    for vert in leaf.data.vertices:
        world = leaf.matrix_world @ vert.co
        along = (world - head).dot(axis)
        pairs.append((along, world))
    pairs.sort(key=lambda item: abs(item[0] - target))
    anchor = pairs[0][0]
    samples = [world for along, world in pairs if abs(along - anchor) <= 0.003]
    if len(samples) < 10:
        return ["leaf ring was not found"], 0.0
    center = Vector((0.0, 0.0, 0.0))
    for point in samples:
        center += point
    center /= len(samples)
    radii = [(point - center).length for point in samples]
    rmax = max(radii)
    rmin = min(radii)
    ratio = rmin / rmax if rmax > 1e-8 else 0.0
    print("leaf section", leaf.name, "ratio", round(ratio, 3), "rmin", round(rmin, 5), "rmax", round(rmax, 5))
    if ratio < 0.80:
        return ["leaf cross section is not round"], ratio
    return [], ratio


def _lesson_shape():
    problems = []
    shoots, roots = {}, {}
    for obj in bpy.data.objects:
        if obj.type != "CURVE":
            continue
        if obj.name.startswith("SI_Leaf_"):
            key = obj.name.split("_")[2]
            shoots[key] = shoots.get(key, 0) + 1
        elif obj.name.startswith("SI_Root_"):
            key = obj.name.split("_")[2]
            roots[key] = roots.get(key, 0) + 1
    if len(shoots) < 2:
        problems.append("need more than one shoot")
    for key in sorted(set(shoots) | set(roots)):
        if shoots.get(key, 0) < 1:
            problems.append("shoot %s has no leaves" % key)
        if roots.get(key, 0) < 1:
            problems.append("shoot %s has no roots" % key)
    ys = [obj.matrix_world.translation.y for obj in bpy.data.objects if obj.name.startswith("SI_Shoot_")]
    if ys and max(ys) - min(ys) < 0.04:
        problems.append("shoots have no depth")
    return problems


def validate(cfg=CONFIG):
    bpy.context.view_layer.update()
    scene = bpy.context.scene
    arm = bpy.data.objects["SI_Armature"]
    meadow = bpy.data.collections["Meadow"]
    tiny = cfg["min_bone_scale"]
    problems = []
    length_problems, leaf_arc = _lengths(cfg)
    problems.extend(length_problems)
    round_problems, ratio = _round_section()
    problems.extend(round_problems)
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

    lesson = cfg.get("presentation") == "lesson"
    if not lesson:
        if int(scene.frame_end) != 330 or int(scene.render.fps) != 30:
            problems.append("phone clock is not frames 1-330 at 30 fps")
        cam = bpy.data.objects.get("Camera")
        if cam and cam.animation_data and cam.animation_data.action:
            problems.append("phone camera is animated")
    else:
        fonts = [obj.name for obj in bpy.data.objects if obj.type == "FONT" or obj.name.startswith(("SI_Caption_", "SI_Card", "SI_Note_"))]
        if fonts:
            problems.append("floating text still in the lesson")
        if not any(obj.get("cr_hero") for obj in bpy.data.objects):
            problems.append("hero leaf missing")

    samples = list(SAMPLE_FRAMES)
    if cfg["frame_end"] not in samples:
        samples.append(cfg["frame_end"])
    poses = {}
    for frame in samples:
        scene.frame_set(frame)
        for pb in arm.pose.bones:
            if pb.name == "base":
                continue
            sx, sy, sz = pb.scale
            if sy < tiny - 1e-4 or abs(sx - 1) > 1e-4 or abs(sz - 1) > 1e-4:
                problems.append("bone %s frame %d scale %s" % (pb.name, frame, tuple(pb.scale)))
            if frame in (1, cfg["frame_end"]):
                poses.setdefault(pb.name, []).append(pb.matrix_basis.copy())
    if not lesson:
        # The phone clip grows from a bud and holds the full stand.
        if "Grow" not in bpy.data.actions:
            problems.append("missing Grow")
    else:
        problems.extend(_lesson_shape())

    curves = sum(1 for obj in bpy.data.objects if obj.type == "CURVE" and obj.name.startswith("SI_"))
    if curves < 1:
        problems.append("authoring curves missing")
    sand = bpy.data.objects.get("ReefSand")
    if sand and sand.type == "MESH":
        zs = [sand.matrix_world @ v.co for v in sand.data.vertices]
        top = [p.z for p in zs if p.z > -0.02]
        if top and max(top) - min(top) < 0.004:
            problems.append("sand top is flat")
    report = {
        "triangles": tris,
        "leaves": leaves,
        "authoring_curves": curves,
        "leaf_arc_m": leaf_arc,
        "section_ratio": round(ratio, 3),
        "problem_count": len(problems),
        "problems": problems[:20],
    }
    print("validate", report)
    return report
