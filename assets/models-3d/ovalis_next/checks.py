"""Numeric checks for the blend and the exported glb."""

import json
import struct

import bpy
from mathutils import Vector

from ovalis_next.config import FRAME_END, GLB
from ovalis_next.layout import NODES

_SAMPLE_FRAMES = (1, 20, 40, 60, 80, 100, 120, 150, 180, 200, 230, 260, 300, 316, 330)


def _tris(obj):
    obj.data.calc_loop_triangles()
    return len(obj.data.loop_triangles)


def check_scene(arm):
    problems = []
    meadow = [obj for obj in bpy.data.collections["Meadow"].objects if obj.type == "MESH"]
    total = 0
    for obj in meadow:
        total += _tris(obj)
        if tuple(round(v, 5) for v in obj.scale) != (1.0, 1.0, 1.0):
            problems.append(f"{obj.name} scale is {tuple(obj.scale)}")
    if total >= 40000:
        problems.append(f"triangles {total} are not under 40000")
    else:
        print(f"triangles {total}")

    curves = [obj for obj in bpy.data.collections["Authoring"].objects if obj.type == "CURVE"]
    if len(curves) < 4:
        problems.append(f"authoring curves {len(curves)}")
    action = arm.animation_data.action if arm.animation_data else None
    if action is None or action.name != "Grow":
        problems.append("Grow action missing")

    scene = bpy.context.scene
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    snap = {}
    for frame in _SAMPLE_FRAMES:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        for pb in arm.pose.bones:
            sx, sy, sz = pb.scale
            if abs(sx - 1.0) > 1e-4 or abs(sz - 1.0) > 1e-4 or sy < 0.019:
                problems.append(f"{pb.name} scale {tuple(pb.scale)} at frame {frame}")
                break
        if frame in (1, 330):
            snap[frame] = {
                pb.name: tuple(round(v, 4) for row in pb.matrix_basis for v in row)
                for pb in arm.pose.bones
            }
    if snap.get(1) != snap.get(330):
        bad = [name for name in snap.get(1, {}) if snap[1].get(name) != snap[330].get(name)]
        problems.append(f"frame 330 differs from frame 1 on {len(bad)} bones")

    scene.frame_set(300)
    bpy.context.view_layer.update()
    for node, rest in enumerate(NODES):
        head = arm.pose.bones[f"shoot_{node:02d}"].head
        if (head - Vector(rest)).length > 0.004:
            problems.append(f"shoot_{node:02d} not on its node at frame 300 ({tuple(head)})")
            break
    scene.frame_set(1)
    bpy.context.view_layer.update()
    bud = arm.pose.bones["shoot_05"].head
    if (bud - Vector(NODES[0])).length > 0.06:
        problems.append(f"late shoot is not tucked into the bud at frame 1 ({tuple(bud)})")
    return problems, total


def _load(path):
    blob = path.read_bytes()
    length = struct.unpack_from("<I", blob, 12)[0]
    payload = json.loads(blob[20:20 + length])
    offset = 20 + length
    while offset % 4:
        offset += 1
    bin_length = struct.unpack_from("<I", blob, offset)[0]
    return payload, blob[offset + 8:offset + 8 + bin_length]


def _values(payload, buf, index):
    acc = payload["accessors"][index]
    view = payload["bufferViews"][acc["bufferView"]]
    comps = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[acc["type"]]
    kind = {5120: "b", 5121: "B", 5122: "h", 5123: "H", 5125: "I", 5126: "f"}[acc["componentType"]]
    width = struct.calcsize("<" + kind)
    stride = view.get("byteStride", width * comps)
    start = view.get("byteOffset", 0) + acc.get("byteOffset", 0)
    out = []
    for i in range(acc["count"]):
        out.append(struct.unpack_from("<" + kind * comps, buf, start + i * stride))
    return out


def check_glb(path=GLB):
    problems = []
    payload, buf = _load(path)
    if payload.get("cameras"):
        problems.append("glb has a camera")
    if payload.get("extensions") and "KHR_lights_punctual" in payload.get("extensions", {}):
        problems.append("glb has a light")
    for node in payload.get("nodes", []):
        name = (node.get("name") or "").lower()
        if any(word in name for word in ("camera", "light", "curve", "reef")):
            problems.append(f"glb node {node.get('name')}")
    anims = payload.get("animations") or []
    if len(anims) != 1 or anims[0].get("name") != "Grow":
        problems.append(f"animations {[a.get('name') for a in anims]}")
    else:
        times = []
        for sampler in anims[0]["samplers"]:
            times = _values(payload, buf, sampler["input"])
            break
        flat = [t[0] for t in times]
        if not flat or abs(flat[-1] - 10.9666667) > 0.05:
            problems.append(f"Grow duration {flat[-1] if flat else None}")
        if any(sampler.get("interpolation") != "STEP" for sampler in anims[0]["samplers"]):
            problems.append("Grow is not STEP")
        _ends_match(payload, buf, anims[0], problems)
        _full_at_300(payload, buf, anims[0], flat, problems)
    if not payload.get("images"):
        problems.append("glb has no images")
    tri = 0
    for mesh in payload.get("meshes", []):
        for prim in mesh["primitives"]:
            tri += payload["accessors"][prim["indices"]]["count"] // 3
    print(f"glb triangles {tri}")
    return problems, tri


def _ends_match(payload, buf, anim, problems):
    nodes = payload["nodes"]
    checked = 0
    for channel in anim["channels"]:
        sampler = anim["samplers"][channel["sampler"]]
        values = _values(payload, buf, sampler["output"])
        if len(values) < 2:
            continue
        first, last = values[0], values[-1]
        if channel["target"]["path"] == "rotation":
            dot = abs(sum(a * b for a, b in zip(first, last)))
            if dot < 0.999:
                problems.append(f"rotation drifts on {nodes[channel['target']['node']].get('name')}")
                return
        else:
            if any(abs(a - b) > 2e-3 for a, b in zip(first, last)):
                problems.append(f"{channel['target']['path']} drifts on {nodes[channel['target']['node']].get('name')}")
                return
        checked += 1
    if checked < 10:
        problems.append("too few animation channels to compare")


def _full_at_300(payload, buf, anim, times, problems):
    names = [node.get("name") for node in payload["nodes"]]
    wanted = "leaf_00_3" if "leaf_00_3" in names else "leaf_00_0"
    for channel in anim["channels"]:
        node = channel["target"]["node"]
        if names[node] != wanted or channel["target"]["path"] != "scale":
            continue
        values = _values(payload, buf, anim["samplers"][channel["sampler"]]["output"])
        start = values[0][1]
        full = values[min(range(len(times)), key=lambda i: abs(times[i] - 9.9666667))][1]
        hold = values[min(range(len(times)), key=lambda i: abs(times[i] - 10.5))][1]
        if start > 0.5 or full < 0.95 or abs(hold - full) > 0.05:
            problems.append(f"leaf scale start {start:.3f} full {full:.3f} hold {hold:.3f}")
        return
    problems.append("leaf scale channel missing")
