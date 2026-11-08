"""Solid warm sand bed. Uneven top, irregular outline, and a front cut."""

import math

import bmesh

from .geometry import bm_to_mesh


def dist_to_path(x, y, path):
    best = 1e9
    for (ax, ay), (bx, by) in zip(path, path[1:]):
        dx, dy = bx - ax, by - ay
        t = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy + 1e-12)))
        best = min(best, math.hypot(x - ax - dx * t, y - ay - dy * t))
    return best


def path_y_at(x, path):
    """Interpolate the rhizome Y coordinate at X along the front cutaway."""
    if not path:
        return -0.034
    if x <= path[0][0]:
        return path[0][1]
    if x >= path[-1][0]:
        return path[-1][1]
    for (ax, ay), (bx, by) in zip(path, path[1:]):
        if ax <= x <= bx or bx <= x <= ax:
            span = bx - ax
            t = 0.0 if abs(span) < 1e-9 else (x - ax) / span
            return ay + (by - ay) * max(0.0, min(1.0, t))
    return path[-1][1]


def front_cut_y(x, path):
    """Uneven front lip. Not a straight cut and not an oval arc."""
    del path
    return -0.046 + 0.0045 * math.sin(x * 38.0) + 0.0028 * math.sin(x * 15.0 + 0.7)


def back_wall_y(x):
    return (
        0.078
        + 0.016 * math.sin(x * 11.0 + 0.4)
        + 0.009 * math.sin(x * 23.0 + 1.2)
        + 0.005 * math.cos(x * 37.0)
    )


def _mound(x, y, cx, cy, amp, rad):
    return amp * math.exp(-((x - cx) ** 2 + (y - cy) ** 2) / (2.0 * rad * rad))


def sand_height(x, y, path):
    """Warm bed with mounds, dips, and small ridges. Not a flat sheet."""
    h = 0.004
    for cx, cy, amp, rad in (
        (-0.09, 0.045, 0.0120, 0.026),
        (0.09, 0.030, 0.0130, 0.030),
        (0.00, 0.070, 0.0090, 0.022),
        (-0.08, -0.030, 0.0080, 0.018),
        (0.08, -0.020, 0.0075, 0.016),
    ):
        h += _mound(x, y, cx, cy, amp, rad)
    for cx, cy, amp, rad in (
        (-0.01, 0.006, 0.0048, 0.020),
        (0.04, 0.028, 0.0036, 0.016),
        (-0.04, 0.036, 0.0032, 0.015),
    ):
        h -= _mound(x, y, cx, cy, amp, rad)
    h += 0.0036 * math.sin(x * 58.0 + y * 19.0)
    h += 0.0024 * math.sin(-x * 24.0 + y * 71.0 + 0.8)
    h += 0.0018 * math.cos(x * 36.0 - y * 14.0 + 1.3)
    if path:
        d = dist_to_path(x, y, path)
        if d < 0.014:
            h -= 0.0042 * 0.5 * (1.0 + math.cos(math.pi * d / 0.014))
    return h


def _side_pinch(x):
    """Pull the left and right rims in by different amounts. Not an oval."""
    ax = abs(x) / 0.145
    if ax <= 0.58:
        return 0.0
    t = (ax - 0.58) / 0.42
    pinch = t * t * (0.70 if x < 0.0 else 0.46)
    pinch *= 1.0 + 0.22 * math.sin(x * 40.0)
    return max(0.0, min(0.85, pinch))


def build_sand(name, path, bottom, cols=40, rows=24, wall_steps=4):
    path = path[::6] + [path[-1]] if len(path) > 12 else path
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    x_half = 0.145
    grid = []
    for j in range(rows + 1):
        v_frac = j / rows
        row = []
        for i in range(cols + 1):
            u_frac = i / cols
            x = -x_half + 2.0 * x_half * u_frac
            x += 0.006 * math.sin(v_frac * 9.0 + u_frac * 14.0) * (0.25 + v_frac)
            fy = front_cut_y(x, path)
            by = back_wall_y(x)
            pinch = _side_pinch(x)
            mid = 0.5 * (fy + by)
            fy = fy + (mid - fy) * pinch * 0.25
            by = by - (by - mid) * pinch
            y = fy + (by - fy) * v_frac
            row.append(bm.verts.new((x, y, sand_height(x, y, path))))
        grid.append(row)

    # Top sand surface mapped to v in [0.57, 0.98]
    for j in range(rows):
        for i in range(cols):
            face = bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
            for loop in face.loops:
                u = (loop.vert.co.x + x_half) / (2.0 * x_half)
                v = 0.57 + 0.41 * max(0.0, min(1.0, (loop.vert.co.y + 0.05) / 0.16))
                loop[uv].uv = (u, v)

    # Perimeter rim (front cutaway + right + back + left)
    rim = [(grid[0][i], True) for i in range(cols + 1)]
    rim += [(grid[j][cols], False) for j in range(1, rows + 1)]
    rim += [(grid[rows][i], False) for i in range(cols - 1, -1, -1)]
    rim += [(grid[j][0], False) for j in range(rows - 1, 0, -1)]
    n = len(rim)

    wall_rings = [[v for v, _is_front in rim]]
    for step in range(1, wall_steps + 1):
        s = 1.0 - step / wall_steps  # 1 at top, 0 at bottom
        ring = []
        for vert, is_front in rim:
            x, y, z0 = vert.co.x, vert.co.y, vert.co.z
            z = bottom + (z0 - bottom) * s
            if is_front:
                y = y + 0.00015 * math.sin(s * math.pi * 2.0 + x * 18.0)
            ring.append(bm.verts.new((x, y, z)))
        wall_rings.append(ring)

    run = [0.0]
    for k in range(n):
        k2 = (k + 1) % n
        run.append(run[-1] + (rim[k2][0].co - rim[k][0].co).length)
    total_run = max(1e-6, run[-1])

    # Stratified cutaway walls mapped to v in [0.02, 0.44]
    for st in range(wall_steps):
        v_hi = 0.02 + 0.42 * (1.0 - st / wall_steps)
        v_lo = 0.02 + 0.42 * (1.0 - (st + 1) / wall_steps)
        top_r = wall_rings[st]
        bot_r = wall_rings[st + 1]
        for k in range(n):
            k2 = (k + 1) % n
            u0 = (run[k] / total_run) * 3.0
            u1 = (run[k + 1] / total_run) * 3.0
            face = bm.faces.new((top_r[k], bot_r[k], bot_r[k2], top_r[k2]))
            for loop, coord in zip(face.loops, ((u0, v_hi), (u0, v_lo), (u1, v_lo), (u1, v_hi))):
                loop[uv].uv = coord

    low = wall_rings[-1]
    base = bm.faces.new(tuple(reversed(low)))
    for loop in base.loops:
        loop[uv].uv = (0.5, 0.04)

    return bm_to_mesh(bm, name)
