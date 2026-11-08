"""Solid warm-pale sand bed for this meadow only.

The top is uneven: mounds, dips, and small ridges. The footprint is lumpy,
with a front cut so the ivory rhizome and the fine roots can be seen.
Not a flat sheet and not a perfect oval.
"""

import math

import bmesh
from mathutils import Vector

from .geometry import bm_to_mesh


def dist_to_path(x, y, path):
    best = 1e9
    for (ax, ay), (bx, by) in zip(path, path[1:]):
        dx, dy = bx - ax, by - ay
        t = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy + 1e-12)))
        best = min(best, math.hypot(x - ax - dx * t, y - ay - dy * t))
    return best


def path_y_at(x, path):
    """Y of the rhizome at this X. The front cord wins where the path folds back."""
    if not path:
        return -0.012
    best_y = None
    for (ax, ay), (bx, by) in zip(path, path[1:]):
        lo, hi = (ax, bx) if ax <= bx else (bx, ax)
        if x < lo - 1e-6 or x > hi + 1e-6:
            continue
        span = bx - ax
        t = 0.0 if abs(span) < 1e-9 else (x - ax) / span
        y = ay + (by - ay) * max(0.0, min(1.0, t))
        if best_y is None or y < best_y:
            best_y = y
    if best_y is None:
        return path[0][1] if x < path[0][0] else path[-1][1]
    return best_y


def front_cut_y(x, path):
    """Cut just in front of the cord, with a small lip so the edge is not a ruler line."""
    py = path_y_at(x, path)
    lip = 0.0024 * math.sin(x * 34.0 + 0.4) + 0.0013 * math.sin(x * 15.0 + 1.1)
    return py - 0.0026 + lip


def back_wall_y(x):
    u = x / 0.16
    return (
        0.070
        + 0.011 * math.sin(x * 22.0 + 0.5)
        + 0.006 * math.sin(x * 9.0 + 1.4)
        - 0.010 * (u * u)
    )


def _gauss(x, y, cx, cy, sig):
    return math.exp(-((x - cx) ** 2 + (y - cy) ** 2) / (2.0 * sig * sig))


def sand_height(x, y, path):
    """Mounds, dips, and small ridges. The cord stays seated, not in a trench."""
    d = dist_to_path(x, y, path) if path else 1.0
    off = min(1.0, d / 0.018)
    fy = front_cut_y(x, path)
    by = back_wall_y(x)
    depth_u = max(0.0, min(1.0, (y - fy) / max(0.02, by - fy)))
    h = 0.0045 * depth_u
    mounds = (
        (-0.09, 0.028, 0.0085, 0.024),
        (0.055, 0.018, 0.0075, 0.022),
        (0.01, 0.052, 0.0060, 0.018),
        (-0.12, 0.040, 0.0050, 0.016),
    )
    dips = (
        (-0.02, 0.032, 0.0048, 0.018),
        (0.09, 0.046, 0.0036, 0.014),
        (-0.06, 0.008, 0.0028, 0.012),
    )
    for cx, cy, amp, sig in mounds:
        h += amp * _gauss(x, y, cx, cy, sig) * (0.45 + 0.55 * off)
    for cx, cy, amp, sig in dips:
        h -= amp * _gauss(x, y, cx, cy, sig) * off
    h += 0.0022 * math.sin(x * 48.0 + y * 16.0)
    h += 0.0015 * math.sin(-x * 19.0 + y * 42.0 + 0.7)
    h += 0.0018 * math.sin(x * 11.0 + 0.4) * math.cos(y * 15.0)
    if d < 0.009:
        h -= 0.0011 * 0.5 * (1.0 + math.cos(math.pi * d / 0.009))
    return h


def build_sand(name, path, bottom, cols=40, rows=22, wall_steps=3):
    path = path[::6] + [path[-1]] if len(path) > 12 else path
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    grid = []
    for j in range(rows + 1):
        v = j / rows
        row = []
        for i in range(cols + 1):
            u = i / cols
            x_guess = -0.150 + 0.300 * u
            y_guess = front_cut_y(x_guess, path)
            y_guess = y_guess + (back_wall_y(x_guess) - y_guess) * v
            left = -0.148 + 0.011 * math.sin(y_guess * 31.0) + 0.006 * math.sin(y_guess * 12.0 + 0.4)
            right = 0.142 + 0.013 * math.sin(y_guess * 27.0 + 1.2) + 0.005 * math.sin(y_guess * 14.0)
            x = left + (right - left) * u
            x += 0.0045 * math.sin(math.pi * v) * math.sin(u * 7.0 + v * 2.0)
            fy = front_cut_y(x, path)
            by = back_wall_y(x)
            y = fy + (by - fy) * v
            if u < 0.10:
                y += (fy - y) * ((0.10 - u) / 0.10) * 0.28
            if u > 0.88:
                y += (fy - y) * ((u - 0.88) / 0.12) * 0.18
            row.append(bm.verts.new((x, y, sand_height(x, y, path))))
        grid.append(row)

    for j in range(rows):
        for i in range(cols):
            face = bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
            for loop in face.loops:
                uu = (loop.vert.co.x + 0.16) / 0.32
                vv = 0.58 + 0.40 * max(0.0, min(1.0, (loop.vert.co.y + 0.04) / 0.14))
                loop[uv].uv = (uu, vv)

    rim = [(grid[0][i], True) for i in range(cols + 1)]
    rim += [(grid[j][cols], False) for j in range(1, rows + 1)]
    rim += [(grid[rows][i], False) for i in range(cols - 1, -1, -1)]
    rim += [(grid[j][0], False) for j in range(rows - 1, 0, -1)]
    n = len(rim)
    wall_rings = [[vert for vert, _front in rim]]
    for step in range(1, wall_steps + 1):
        s = 1.0 - step / wall_steps
        ring = []
        for vert, is_front in rim:
            x, y, z0 = vert.co.x, vert.co.y, vert.co.z
            z = bottom + (z0 - bottom) * s
            if is_front:
                z += 0.0011 * math.sin(x * 46.0 + s * 5.0)
                y += 0.0007 * math.sin(x * 28.0 + s * 3.0)
            ring.append(bm.verts.new((x, y, z)))
        wall_rings.append(ring)

    run = [0.0]
    for k in range(n):
        k2 = (k + 1) % n
        run.append(run[-1] + (rim[k2][0].co - rim[k][0].co).length)
    total = max(1e-6, run[-1])
    for st in range(wall_steps):
        v_hi = 0.05 + 0.42 * (1.0 - st / wall_steps)
        v_lo = 0.05 + 0.42 * (1.0 - (st + 1) / wall_steps)
        top_r, bot_r = wall_rings[st], wall_rings[st + 1]
        for k in range(n):
            k2 = (k + 1) % n
            u0 = (run[k] / total) * 2.4
            u1 = (run[k + 1] / total) * 2.4
            face = bm.faces.new((top_r[k], bot_r[k], bot_r[k2], top_r[k2]))
            for loop, coord in zip(face.loops, ((u0, v_hi), (u0, v_lo), (u1, v_lo), (u1, v_hi))):
                loop[uv].uv = coord
    low = wall_rings[-1]
    base = bm.faces.new(tuple(reversed(low)))
    for loop in base.loops:
        loop[uv].uv = (0.5, 0.08)
    return bm_to_mesh(bm, name)
