"""Solid warm pale sand for this meadow.

The bed is thick. The top is uneven: mounds, dips, and small ridges.
The outline is lumpy, so it is not a sheet and not an oval.
The front is a cut through the rhizome so the buried stem and cord roots show.
"""

import math

import bmesh
from mathutils import Vector

from .geometry import bm_to_mesh


def dist_to_path(x, y, path):
    best = 1e9
    for (ax, ay), (bx, by) in zip(path, path[1:]):
        dx, dy = bx - ax, by - ay
        denom = dx * dx + dy * dy
        if denom < 1e-12:
            best = min(best, math.hypot(x - ax, y - ay))
            continue
        t = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / denom))
        best = min(best, math.hypot(x - ax - dx * t, y - ay - dy * t))
    return best


def front_cut_y(x, path=None):
    """Wavy front lip. The rhizome sits just behind this line."""
    u = max(0.0, min(1.0, (x + 0.22) / 0.46))
    return -0.034 + 0.009 * math.sin(u * math.pi * 3.0) + 0.004 * math.sin(u * math.pi * 7.0 + 0.5)


def _bed_xy(u, v):
    """Irregular plan. Left and right do not mirror, so the bed is not an oval."""
    front = -0.034 + 0.009 * math.sin(u * math.pi * 3.0) + 0.004 * math.sin(u * math.pi * 7.0 + 0.5)
    back = 0.28 + 0.016 * math.sin(u * math.pi * 2.1 + 0.7) - 0.012 * math.sin(u * math.pi * 5.2)
    left = -0.26 + 0.020 * math.sin(v * math.pi * 1.55 + 0.3) + 0.008 * v
    right = 0.24 + 0.022 * math.sin(v * math.pi * 2.35 + 1.0) - 0.010 * v
    # A bite out of the left side, and a bulge on the right, so the rim is lumpy.
    if 0.28 < v < 0.70:
        left += 0.022 * math.sin((v - 0.28) / 0.42 * math.pi)
    if 0.15 < v < 0.55:
        right += 0.016 * math.sin((v - 0.15) / 0.40 * math.pi)
    x = left + (right - left) * u
    y = front + (back - front) * v
    return x, y


def sand_height(x, y, path=None):
    """Mounds, dips, and small ridges. Warm pale sand sits on this surface."""
    h = 0.0
    h += 0.028 * math.exp(-((x + 0.08) ** 2 + (y - 0.05) ** 2) / (2 * 0.034 ** 2))
    h += 0.022 * math.exp(-((x - 0.11) ** 2 + (y - 0.08) ** 2) / (2 * 0.028 ** 2))
    h += 0.014 * math.exp(-((x + 0.01) ** 2 + (y - 0.11) ** 2) / (2 * 0.020 ** 2))
    h -= 0.018 * math.exp(-((x - 0.02) ** 2 + (y - 0.025) ** 2) / (2 * 0.024 ** 2))
    h -= 0.012 * math.exp(-((x + 0.14) ** 2 + (y - 0.09) ** 2) / (2 * 0.018 ** 2))
    h += 0.006 * math.sin(x * 38.0 + y * 7.0)
    h += 0.0045 * math.sin(-x * 11.0 + y * 46.0 + 0.6)
    h += 0.0055 * math.sin(y * 22.0 + 0.4) * math.sin(x * 6.5 + 1.1)
    if path:
        d = dist_to_path(x, y, path)
        if d < 0.018:
            h -= 0.0035 * 0.5 * (1.0 + math.cos(math.pi * d / 0.018))
    return h


def build_sand(name, path, bottom, cols=40, rows=22, wall_steps=3):
    """Solid bed. Top grid, vertical sides, flat floor. The near side is the cut."""
    if path and len(path) > 12:
        path = path[::6] + [path[-1]]
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    top = []
    for j in range(rows + 1):
        v = j / rows
        row = []
        for i in range(cols + 1):
            u = i / cols
            x, y = _bed_xy(u, v)
            row.append(bm.verts.new((x, y, sand_height(x, y, path))))
        top.append(row)

    def uv_top(vert):
        u = (vert.co.x + 0.24) / 0.48
        v = 0.58 + 0.38 * max(0.0, min(1.0, (vert.co.y + 0.05) / 0.20))
        return (max(0.0, min(1.0, u)), max(0.58, min(0.98, v)))

    for j in range(rows):
        for i in range(cols):
            face = bm.faces.new((top[j][i], top[j][i + 1], top[j + 1][i + 1], top[j + 1][i]))
            for loop in face.loops:
                loop[uv].uv = uv_top(loop.vert)

    # Perimeter, starting at the front-left and walking the front cut first.
    rim = [top[0][i] for i in range(cols + 1)]
    rim += [top[j][cols] for j in range(1, rows + 1)]
    rim += [top[rows][i] for i in range(cols - 1, -1, -1)]
    rim += [top[j][0] for j in range(rows - 1, 0, -1)]
    n = len(rim)
    front_n = cols + 1

    floor = []
    for vert in rim:
        floor.append(bm.verts.new((vert.co.x, vert.co.y, bottom)))

    run = [0.0]
    for k in range(n):
        run.append(run[-1] + (rim[(k + 1) % n].co - rim[k].co).length)
    total = max(1e-6, run[-1])

    # A few steps down the cut so the face can carry a soft grain, still one sand.
    rings = [rim]
    for step in range(1, wall_steps):
        s = step / wall_steps
        ring = []
        for k, vert in enumerate(rim):
            z = vert.co.z + (bottom - vert.co.z) * s
            # A small horizontal nick on the front cut only. The lip stays uneven.
            y = vert.co.y
            if k < front_n:
                y += 0.0012 * math.sin(s * math.pi + vert.co.x * 22.0)
            ring.append(bm.verts.new((vert.co.x, y, z)))
        rings.append(ring)
    rings.append(floor)

    for st in range(wall_steps):
        v_hi = 0.06 + 0.40 * (1.0 - st / wall_steps)
        v_lo = 0.06 + 0.40 * (1.0 - (st + 1) / wall_steps)
        for k in range(n):
            k2 = (k + 1) % n
            u0 = (run[k] / total) * 2.0
            u1 = (run[k + 1] / total) * 2.0
            face = bm.faces.new((rings[st][k], rings[st + 1][k], rings[st + 1][k2], rings[st][k2]))
            for loop, coord in zip(face.loops, ((u0, v_hi), (u0, v_lo), (u1, v_lo), (u1, v_hi))):
                loop[uv].uv = coord

    # Floor from the boundary. Fan from a center so the n-gon stays a solid cap.
    center = Vector((0.0, 0.04, bottom))
    hub = bm.verts.new(center)
    for k in range(n):
        k2 = (k + 1) % n
        face = bm.faces.new((hub, floor[k2], floor[k]))
        for loop in face.loops:
            loop[uv].uv = (0.5, 0.04)

    return bm_to_mesh(bm, name)
