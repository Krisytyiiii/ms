"""Checks that can be read from the blend and from the draft glb."""

import json
import os
import struct

import bpy
import numpy as np

from . import grow, timeline
from .config import CONFIG


STORY = (1, 40, 120, 200, 300, 316, 330)
BOUNDS = (1, 20, 40, 60, 80, 100, 120, 150, 180, 200, 230, 260, 300, 316, 330)


def _pose(arm, frame):
    bpy.context.scene.frame_set(int(frame))
    bpy.context.view_layer.update()
    return {pb.name: pb for pb in arm.pose.bones}


def _sy(pb):
    return float(pb.scale.y)


def _strap(arm):
    """Width, thickness, and tip of the hero strap, measured on one cross-section."""
    hero = next((o for o in bpy.data.objects if o.type == "MESH" and o.get("cr_hero")), None)
    if hero is None:
        return ["missing hero leaf"]
    bone_name = "leaf_" + hero.name[len("Leaf_"):]
    bone = arm.data.bones.get(bone_name)
    if bone is None:
        return ["hero has no bone"]
    head = bone.head_local
    x = bone.matrix_local.col[0].xyz.normalized()
    y = bone.matrix_local.col[1].xyz.normalized()
    z = bone.matrix_local.col[2].xyz.normalized()
    pts = []
    for v in hero.data.vertices:
        d = v.co - head
        pts.append((d.dot(x), d.dot(y), d.dot(z)))
    ys = [p[1] for p in pts]
    mid = min(ys) + 0.45 * (max(ys) - min(ys))
    anchor = min(pts, key=lambda p: abs(p[1] - mid))
    band = [p for p in pts if abs(p[1] - anchor[1]) <= 0.002]
    if len(band) < 6:
        return ["hero cross-section is too thin to measure (%d)" % len(band)]
    extent_x = max(p[0] for p in band) - min(p[0] for p in band)
    extent_z = max(p[2] for p in band) - min(p[2] for p in band)
    wide, thin = max(extent_x, extent_z), min(extent_x, extent_z)
    thin_axis = 0 if extent_x <= extent_z else 2
    hi = max(p[thin_axis] for p in band)
    front = [p for p in band if p[thin_axis] >= hi - 0.0002]
    tail = bone.tail_local
    apex = min(hero.data.vertices, key=lambda v: (v.co - tail).length)
    apex_y = max(p[1] for p in pts)
    tip_band = [p for p in pts if apex_y - p[1] <= 0.00045]
    problems = []
    target = float(bpy.data.objects["CR_Controls"]["leaf_width_m"])
    print("hero strap wide %.5f thin %.5f front_verts %d" % (wide, thin, len(front)))
    if abs(wide - target) > 0.0012:
        problems.append("hero width %.4f m" % wide)
    if thin > 0.0012 or wide / max(thin, 1e-6) < 8.0:
        problems.append("hero is not a thin strap width %.4f thick %.5f" % (wide, thin))
    if len(front) < 3:
        problems.append("front face is not flat")
    if (apex.co - tail).length > 0.004:
        problems.append("tip is not at the end of the leaf")
    if len(tip_band) >= 3:
        tip_w = max(p[0] for p in tip_band) - min(p[0] for p in tip_band)
        tip_t = max(p[2] for p in tip_band) - min(p[2] for p in tip_band)
        tip_span = max(tip_w, tip_t)
        print("hero tip span %.5f" % tip_span)
        if tip_span > wide * 0.62:
            problems.append("tip is not rounded")
    return problems


def _veins():
    img = bpy.data.images.get("CrLeafVeins")
    if img is None:
        return ["missing leaf image"]
    w, h = int(img.size[0]), int(img.size[1])
    buf = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(buf)
    px = buf.reshape(h, w, 4)
    rgb = px[..., 0] * 0.30 + px[..., 1] * 0.55 + px[..., 2] * 0.15
    row = rgb[h // 2]
    edge = np.concatenate([row[: int(w * 0.08)], row[int(w * 0.92) :]])
    center = row[int(w * 0.34) : int(w * 0.66)]
    problems = []
    if float(center.max() - center.min()) < 0.015:
        problems.append("veins are not visible in the leaf image")
    if float(edge.max() - edge.min()) > 0.012:
        problems.append("veins wrap the leaf edge")
    base = float(rgb[: max(2, h // 20)].mean())
    middle = float(rgb[int(h * 0.4) : int(h * 0.6)].mean())
    if base <= middle:
        problems.append("leaf base is not paler than the blade")
    young = bpy.data.images.get("CrYoungVeins")
    if young is not None:
        ybuf = np.empty(w * h * 4, dtype=np.float32)
        young.pixels.foreach_get(ybuf)
        if float(ybuf.mean()) <= float(buf.mean()):
            problems.append("younger leaves are not lighter")
    return problems


def _constant(action, hold):
    problems = []
    curves = grow.fcurves(action)
    if not curves:
        return ["Grow has no keys"]
    for fc in curves:
        hit = [kp for kp in fc.keyframe_points if abs(kp.co[0] - hold) < 0.1]
        if not hit:
            problems.append("missing hold on %s" % fc.data_path)
        elif any(kp.interpolation != "CONSTANT" for kp in hit):
            problems.append("frame %s is not constant on %s" % (hold, fc.data_path))
    return problems[:8]


def validate(cfg=CONFIG):
    scene = bpy.context.scene
    arm = bpy.data.objects["CR_Armature"]
    meadow = bpy.data.collections["Meadow"]
    tiny = float(cfg["min_bone_scale"])
    problems = []
    tris = 0
    for obj in meadow.objects:
        if obj.type != "MESH":
            continue
        obj.data.calc_loop_triangles()
        tris += len(obj.data.loop_triangles)
        if any(abs(v - 1.0) > 1e-5 for v in obj.scale):
            problems.append("mesh scale %s" % obj.name)
    if tris > 40000:
        problems.append("triangles %d" % tris)
    if tris < 1000:
        problems.append("mesh is almost empty (%d)" % tris)

    count = len([b for b in arm.data.bones if b.name.startswith("shoot_")])
    nseg = len([b for b in arm.data.bones if b.name.startswith("rhizome_")])
    if not 12 <= count <= 16:
        problems.append("shoot count %d" % count)
    leaves = {}
    for obj in bpy.data.objects:
        if obj.name.startswith("CR_Leaf_"):
            key = obj.name.split("_")[2]
            leaves[key] = leaves.get(key, 0) + 1
    if len(leaves) != count:
        problems.append("leaf curves for %d shoots, rig has %d" % (len(leaves), count))
    for key, n in sorted(leaves.items()):
        if n < 2 or n > 5:
            problems.append("shoot %s has %d leaves" % (key, n))

    for bone in arm.data.bones:
        if bone.name == "base":
            if bone.parent is not None or bone.use_deform:
                problems.append("base bone is not a single undeformed root")
        elif bone.parent is None or bone.parent.name != "base":
            problems.append("bone %s is not a child of base" % bone.name)

    poses = {}
    for frame in BOUNDS:
        pbs = _pose(arm, frame)
        src = 1 if frame == cfg["frame_end"] else frame
        for name, pb in pbs.items():
            if name == "base":
                if any(abs(v - 1.0) > 1e-3 for v in pb.scale):
                    problems.append("base scale at %d" % frame)
                continue
            sx, sy, sz = pb.scale
            if sy < tiny - 1e-3 or abs(sx - 1.0) > 1e-3 or abs(sz - 1.0) > 1e-3 or sy > 1.02:
                problems.append("bone %s frame %d scale (%.3f, %.3f, %.3f)" % (name, frame, sx, sy, sz))
            if frame in (1, cfg["frame_end"]):
                poses.setdefault(name, []).append([round(pb.matrix_basis[r][c], 4) for r in range(4) for c in range(4)])
            if frame in STORY and frame != cfg["frame_end"]:
                if name.startswith("rhizome_"):
                    bone = arm.data.bones[name]
                    if bone.get("cr_count") is not None:
                        expect = timeline.segment_scale(
                            int(bone["cr_local"]),
                            int(bone["cr_count"]),
                            src,
                            tiny,
                            int(bone["cr_ready"]),
                            bool(int(bone.get("cr_stub", 0))),
                        )
                    else:
                        expect = timeline.rhizome_scale(int(name.split("_")[1]), nseg, src, tiny)
                elif name.startswith("shoot_"):
                    expect = timeline.shoot_scale(int(name.split("_")[1]), count, src, tiny)
                elif name.startswith("leaf_"):
                    i, j = name.split("_")[1:]
                    expect = timeline.leaf_scale(int(i), int(j), count, src, tiny)
                elif name.startswith("root_"):
                    i = int(name.split("_")[1])
                    shoot = bpy.data.objects.get("CR_Shoot_%02d" % i)
                    if shoot is not None and shoot.get("cr_ready") is not None:
                        expect = timeline.root_scale_at(src, tiny, int(shoot["cr_ready"]))
                    else:
                        expect = timeline.root_scale(i, nseg, src, tiny)
                else:
                    expect = None
                if expect is not None and abs(sy - expect) > 0.03:
                    problems.append("bone %s frame %d is %.3f, expected %.3f" % (name, frame, sy, expect))
    for name, pair in poses.items():
        if len(pair) == 2 and pair[0] != pair[1]:
            problems.append("frame 330 does not match frame 1 for %s" % name)

    sand = bpy.data.objects.get("Sand")
    if sand is None or sand.type != "MESH" or sand.hide_render:
        problems.append("sand is missing on frame 1")
    elif sand.animation_data and sand.animation_data.action:
        problems.append("sand is animated")
    cam = bpy.data.objects.get("Camera")
    if cam and cam.animation_data and cam.animation_data.action:
        problems.append("camera is animated")
    ctrl = bpy.data.objects.get("CR_Controls")
    if ctrl is None:
        problems.append("missing CR_Controls")
    else:
        for key in ("leaf_width_m", "vein_count", "shoot_count"):
            if key not in ctrl.keys():
                problems.append("controls missing %s" % key)
        ad = ctrl.animation_data
        if ad is not None and (ad.action is not None or len(ad.drivers) > 0):
            problems.append("controls are driven")
    needed = ("CR_Rhizome", "CR_Leaf_00_0", "CR_Root_00_0")
    for name in needed:
        if bpy.data.objects.get(name) is None or bpy.data.objects[name].type != "CURVE":
            problems.append("missing curve %s" % name)
    action = bpy.data.actions.get("Grow")
    if action is None:
        problems.append("missing Grow")
    else:
        problems.extend(_constant(action, int(cfg["frame_hold"])))
    extras = [a.name for a in bpy.data.actions if a.name != "Grow"]
    if extras:
        problems.append("extra actions %s" % extras[:4])
    problems.extend(_strap(arm))
    problems.extend(_veins())
    curves = sum(1 for o in bpy.data.objects if o.type == "CURVE" and o.name.startswith("CR_"))
    report = {"triangles": tris, "shoots": count, "authoring_curves": curves, "problems": problems[:24]}
    print("validate", report)
    return report


def read_glb(path):
    with open(path, "rb") as handle:
        magic, _version, _length = struct.unpack("<4sII", handle.read(12))
        if magic != b"glTF":
            raise RuntimeError("not a glb")
        chunk_len, chunk_type = struct.unpack("<I4s", handle.read(8))
        if chunk_type != b"JSON":
            raise RuntimeError("glb json chunk missing")
        return json.loads(handle.read(chunk_len))


def inspect_glb(path, blend_tris):
    gltf = read_glb(path)
    problems = []
    anims = gltf.get("animations") or []
    if len(anims) != 1 or anims[0].get("name") != "Grow":
        problems.append("glb animations %s" % [a.get("name") for a in anims])
    duration = 0.0
    for anim in anims:
        for sampler in anim.get("samplers", []):
            acc = gltf["accessors"][sampler["input"]]
            duration = max(duration, float(acc.get("max", [0])[0]))
    if not 10.9 <= duration <= 11.05:
        problems.append("Grow duration %.4f s" % duration)
    for node in gltf.get("nodes", []):
        name = (node.get("name") or "").lower()
        if "camera" in node or "camera" in name or "light" in name or "curve" in name or "reef" in name:
            problems.append("glb node %s" % node.get("name"))
        if name.startswith("cr_") and "armature" not in name:
            problems.append("glb node %s" % node.get("name"))
    if gltf.get("cameras") or gltf.get("extensions", {}).get("KHR_lights_punctual"):
        problems.append("glb has a camera or a light")
    tris = 0
    for mesh in gltf.get("meshes", []):
        for prim in mesh.get("primitives", []):
            idx = prim.get("indices")
            if idx is not None:
                tris += int(gltf["accessors"][idx]["count"]) // 3
    if tris > 40000 or abs(tris - blend_tris) > max(50, int(blend_tris * 0.05)):
        problems.append("glb triangles %d blend %d" % (tris, blend_tris))
    names = [n.get("name", "") for n in gltf.get("nodes", [])]
    if not any("sand" in name.lower() for name in names):
        problems.append("glb has no sand")
    print("glb", {"duration": round(duration, 4), "triangles": tris, "nodes": len(names), "problems": problems})
    return problems
