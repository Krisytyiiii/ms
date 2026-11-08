"""Solid uneven sand bed for this species only.

The same warm pale bed is used by the phone model and the lesson. The top
has mounds, a dip, and small ridges. The front is cut so the rhizome and
the fine roots can be seen. The outline is lobed, not a flat sheet and not
an oval.
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
    """Irregular lip in front of the rhizome. The same cut on the phone and in the lesson."""
    del path
    # Grazes the front of the rhizome so the cord and the roots show in the wall.
    lip = -0.0206
    lip += 0.0011 * math.sin(x * 47.0)
    lip += 0.0008 * math.sin(x * 19.0 + 0.8)
    lip += 0.012 * max(0.0, (abs(x) - 0.10) / 0.05) ** 2
    return lip


def back_wall_y(x):
    """Lobed back edge. Not a straight wall and not an oval."""
    u = x / 0.17
    return (
        0.072
        + 0.012 * math.sin(x * 22.0 + 0.4)
        + 0.007 * math.cos(x * 9.5 + 1.2)
        - 0.018 * (u ** 4)
    )


def sand_height(x, y, path):
    """Mounds, one dip, and small ridges. A shallow trench shows the rhizome."""
    d = dist_to_path(x, y, path) if path else 1.0
    h = 0.0
    mounds = (
        (-0.100, 0.012, 0.016, 0.032),
        (0.102, 0.022, 0.014, 0.028),
        (-0.015, 0.052, 0.012, 0.024),
        (0.040, -0.008, 0.008, 0.020),
    )
    for cx, cy, amp, rad in mounds:
        h += amp * math.exp(-((x - cx) ** 2 + (y - cy) ** 2) / (2.0 * rad * rad))
    h -= 0.011 * math.exp(-((x - 0.028) ** 2 + (y - 0.040) ** 2) / (2.0 * 0.020 ** 2))
    calm = min(1.0, d / 0.016)
    h += calm * (
        0.0052 * math.sin(x * 88.0 + y * 26.0)
        + 0.0038 * math.sin(y * 102.0 - x * 18.0 + 0.5)
        + 0.0026 * math.sin(x * 40.0 + 0.7) * math.cos(y * 33.0)
    )
    if d < 0.012:
        h -= 0.0022 * 0.5 * (1.0 + math.cos(math.pi * d / 0.012))
    return h


def _add_pebble(bm, uv, center, rx, ry, rz, yaw):
    """Low-poly rounded limestone reef pebble mapped to the pebble band in CrSandGrain."""
    rings = 3
    segs = 8
    c, s = math.cos(yaw), math.sin(yaw)

    def place(lx, ly, lz):
        wx = center.x + lx * c - ly * s
        wy = center.y + lx * s + ly * c
        wz = center.z + lz
        return bm.verts.new((wx, wy, wz))

    top = place(0.0, 0.0, rz)
    bot = place(0.0, 0.0, -rz * 0.6)
    loops = []
    for r in range(1, rings + 1):
        phi = math.pi * 0.5 * (1.0 - r / (rings + 0.4))
        cz = math.sin(phi) * rz
        cr = math.cos(phi)
        ring = []
        for k in range(segs):
            a = 2 * math.pi * k / segs
            wobble = 1.0 + 0.08 * math.sin(3 * a + yaw)
            ring.append(place(math.cos(a) * rx * cr * wobble, math.sin(a) * ry * cr * wobble, cz))
        loops.append(ring)

    def set_pebble_uv(face):
        for loop in face.loops:
            u = (loop.vert.co.x - center.x) / (2.2 * rx) + 0.5
            v = 0.475 + 0.06 * max(0.0, min(1.0, (loop.vert.co.z - center.z + rz) / (2.0 * rz)))
            loop[uv].uv = (max(0.02, min(0.98, u)), v)

    for k in range(segs):
        k2 = (k + 1) % segs
        set_pebble_uv(bm.faces.new((top, loops[0][k], loops[0][k2])))
        set_pebble_uv(bm.faces.new(( loops[-1][k2], loops[-1][k], bot)))
    for r in range(rings - 1):
        for k in range(segs):
            k2 = (k + 1) % segs
            set_pebble_uv(bm.faces.new((loops[r][k], loops[r][k2], loops[r + 1][k2], loops[r + 1][k])))


def build_sand(name, path, bottom, cols=44, rows=24, wall_steps=4):
    path = path[::6] + [path[-1]] if len(path) > 12 else path
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    grid = []
    for j in range(rows + 1):
        v_frac = j / rows
        row = []
        center = 0.010 * math.sin(4.4 * v_frac) + 0.005 * math.cos(7.1 * v_frac + 0.4)
        half = 0.158 + 0.012 * math.sin(2.6 * v_frac + 0.2) + 0.008 * math.sin(6.4 * v_frac + 1.3)
        for i in range(cols + 1):
            u_frac = i / cols
            x = center - half + 2.0 * half * u_frac
            fy = front_cut_y(x, path)
            by = back_wall_y(x)
            y = fy + (by - fy) * v_frac
            y += 0.0035 * math.sin(u_frac * 8.0 + v_frac * 3.0)
            row.append(bm.verts.new((x, y, sand_height(x, y, path))))
        grid.append(row)

    # Top sand surface mapped to v in [0.57, 0.98]
    for j in range(rows):
        for i in range(cols):
            face = bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
            for loop in face.loops:
                u = (loop.vert.co.x + 0.19) / 0.38
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

    # A few grains at the back of the same bed. They stay off the front cut.
    pebble_specs = (
        (-0.118, 0.052, 0.009, 0.007, 0.0032, 0.4),
        (0.112, 0.046, 0.010, 0.008, 0.0034, 1.1),
        (-0.020, 0.062, 0.008, 0.006, 0.0028, 1.8),
        (0.055, 0.058, 0.007, 0.006, 0.0026, 0.7),
    )
    for px, py, rx, ry, rz, yaw in pebble_specs:
        pz = sand_height(px, py, path) + rz * 0.25
        _add_pebble(bm, uv, Vector((px, py, pz)), rx, ry, rz, yaw)

    return bm_to_mesh(bm, name)
