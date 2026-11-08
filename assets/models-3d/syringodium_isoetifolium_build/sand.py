"""Solid uneven sand bed for this species only.

Warm pale sand. The top has mounds, dips, and small ridges.
The outline is irregular. A front cut shows the buried stem and the roots.
"""

import math

import bmesh

from .geometry import bm_to_mesh


def front_lip_y(x):
    """Front cut. Slightly uneven, so the lip is not a ruled straight edge."""
    return -0.044 + 0.0032 * math.sin(x * 23.0) + 0.0022 * math.sin(x * 9.5 + 0.6)


def _bounds_x(v):
    """Width along the bed. Not a sine oval: the two sides bulge in different places."""
    left = 0.104 + 0.018 * math.sin(2.1 * v + 0.4) + 0.012 * math.sin(9.0 * v)
    right = 0.118 + 0.022 * math.sin(3.3 * v + 1.1) + 0.009 * math.cos(7.4 * v)
    if v < 0.20:
        right *= 0.78 + 0.22 * (v / 0.20)
        left *= 0.90 + 0.10 * (v / 0.20)
    if v > 0.70:
        left += 0.020 * ((v - 0.70) / 0.30)
        right -= 0.010 * ((v - 0.70) / 0.30)
    return -left, right


def back_y(x):
    return (
        0.082
        + 0.014 * math.sin(x * 8.5 + 0.5)
        + 0.009 * math.cos(x * 19.0)
        + 0.014 * max(0.0, -x / 0.12)
    )


def _y_at(x, v):
    lip = front_lip_y(x)
    back = back_y(x)
    t = v ** 0.82
    return lip + (back - lip) * t


def _dist_to_path(x, y, path):
    best = 1e9
    for (ax, ay), (bx, by) in zip(path, path[1:]):
        dx, dy = bx - ax, by - ay
        denom = dx * dx + dy * dy + 1e-12
        t = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / denom))
        best = min(best, math.hypot(x - ax - dx * t, y - ay - dy * t))
    return best


def sand_height(x, y, path=None):
    """Mounds, one dip, and small ridges. Calmer on the cut lip."""
    h = 0.0
    h += 0.016 * math.exp(-((x + 0.038) ** 2 + (y - 0.018) ** 2) / (2 * 0.028 ** 2))
    h += 0.012 * math.exp(-((x - 0.048) ** 2 + (y - 0.030) ** 2) / (2 * 0.020 ** 2))
    h -= 0.011 * math.exp(-((x - 0.004) ** 2 + (y - 0.006) ** 2) / (2 * 0.016 ** 2))
    h += 0.0042 * math.sin(x * 46.0 + y * 14.0)
    h += 0.0031 * math.sin(-x * 18.0 + y * 52.0 + 0.7)
    h += 0.0024 * math.sin(x * 27.0 - y * 22.0 + 0.3)
    if path:
        dist = _dist_to_path(x, y, path)
        if dist < 0.018 and y > front_lip_y(x) + 0.012:
            h -= 0.0018 * (1.0 - dist / 0.018)
    lip = front_lip_y(x)
    near = max(0.0, min(1.0, (y - lip) / 0.014))
    if y - lip < 0.014:
        h *= 0.40 + 0.60 * near
    return h


def build_sand(name, path, bottom, cols=40, rows=22, wall_steps=3):
    path = path or []
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    grid = []
    for j in range(rows + 1):
        v = j / rows
        x0, x1 = _bounds_x(v)
        row = []
        for i in range(cols + 1):
            u = i / cols
            x = x0 + (x1 - x0) * u
            y = _y_at(x, v)
            row.append(bm.verts.new((x, y, sand_height(x, y, path))))
        grid.append(row)

    for j in range(rows):
        for i in range(cols):
            face = bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
            for loop in face.loops:
                u = (loop.vert.co.x + 0.16) / 0.32
                v = 0.62 + 0.34 * max(0.0, min(1.0, (loop.vert.co.y + 0.06) / 0.16))
                loop[uv].uv = (u, v)

    rim = [grid[0][i] for i in range(cols + 1)]
    rim += [grid[j][cols] for j in range(1, rows + 1)]
    rim += [grid[rows][i] for i in range(cols - 1, -1, -1)]
    rim += [grid[j][0] for j in range(rows - 1, 0, -1)]
    n = len(rim)
    rings = [rim]
    for step in range(1, wall_steps + 1):
        s = 1.0 - step / wall_steps
        ring = []
        for vert in rim:
            z = bottom + (vert.co.z - bottom) * s
            ring.append(bm.verts.new((vert.co.x, vert.co.y, z)))
        rings.append(ring)

    run = [0.0]
    for k in range(n):
        run.append(run[-1] + (rim[(k + 1) % n].co - rim[k].co).length)
    total = max(1e-6, run[-1])
    for st in range(wall_steps):
        v_hi = 0.06 + 0.36 * (1.0 - st / wall_steps)
        v_lo = 0.06 + 0.36 * (1.0 - (st + 1) / wall_steps)
        top_r, bot_r = rings[st], rings[st + 1]
        for k in range(n):
            k2 = (k + 1) % n
            u0 = (run[k] / total) * 2.4
            u1 = (run[k + 1] / total) * 2.4
            face = bm.faces.new((top_r[k], bot_r[k], bot_r[k2], top_r[k2]))
            for loop, coord in zip(face.loops, ((u0, v_hi), (u0, v_lo), (u1, v_lo), (u1, v_hi))):
                loop[uv].uv = coord

    base = bm.faces.new(tuple(reversed(rings[-1])))
    for loop in base.loops:
        loop[uv].uv = (0.5, 0.08)
    return bm_to_mesh(bm, name)
