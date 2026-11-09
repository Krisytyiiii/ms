"""A solid low mound: ripples, one groove, and a closed bottom.

The mound is finished on frame 1. It does not grow.
"""

import math

import bmesh
from mathutils import Vector

from .config import CONFIG
from .geometry import bm_to_mesh


def _bounds(xy, cfg):
    xs = [p[0] for p in xy]
    ys = [p[1] for p in xy]
    mx, my = cfg["sand_margin_m"]
    minx, maxx = min(xs) - mx, max(xs) + mx
    miny, maxy = min(ys) - my, max(ys) + my
    return (minx + maxx) * 0.5, (miny + maxy) * 0.5, (maxx - minx) * 0.5, (maxy - miny) * 0.5


def mound_z(x, y, xy, cfg=CONFIG):
    """Smooth dome the rhizome follows. Ripples and the groove are sand only."""
    cx, cy, rx, ry = _bounds(xy, cfg)
    nx = (x - cx) / max(rx, 1e-4)
    ny = (y - cy) / max(ry, 1e-4)
    r2 = nx * nx + ny * ny
    if r2 >= 1.0:
        return 0.0
    return cfg["mound_height_m"] * ((1.0 - r2) ** 1.15)


def _ripples(x, y):
    # Display choice. Gentle ripples, a couple of millimetres.
    return (
        0.0015 * math.sin(x * 46.0 + y * 14.0)
        + 0.0009 * math.sin(-x * 18.0 + y * 52.0 + 0.6)
    )


def dist_to_path(x, y, path):
    best = 1e9
    for (ax, ay), (bx, by) in zip(path, path[1:]):
        dx, dy = bx - ax, by - ay
        denom = dx * dx + dy * dy
        t = 0.0 if denom < 1e-12 else max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / denom))
        best = min(best, math.hypot(x - ax - dx * t, y - ay - dy * t))
    return best


def dist_to_paths(x, y, paths):
    best = 1e9
    for path in paths:
        best = min(best, dist_to_path(x, y, path))
    return best


def sand_height(x, y, xy, paths, cfg=CONFIG):
    h = mound_z(x, y, xy, cfg) + _ripples(x, y)
    d = dist_to_paths(x, y, paths) if paths else 1.0
    width = cfg["groove_width_m"]
    if d < width:
        h -= cfg["groove_depth_m"] * 0.5 * (1.0 + math.cos(math.pi * d / width))
    return h


def _surface_z(x, y, xy, paths, rf, cfg):
    """Full height over the plants, then a slope down to the bottom at the rim."""
    z = sand_height(x, y, xy, paths, cfg)
    if rf <= 0.78:
        return z
    t = (rf - 0.78) / 0.22
    t = t * t * (3.0 - 2.0 * t)
    return z * (1.0 - t) + cfg["sand_bottom_z"] * t


def build_sand(name, xy, paths, cfg=CONFIG):
    """Closed oval mound. path and xy are (x, y) samples of the rhizome."""
    cx, cy, rx, ry = _bounds(xy, cfg)
    rings_n, segs = 28, 72
    bottom = cfg["sand_bottom_z"]
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    center = bm.verts.new((cx, cy, _surface_z(cx, cy, xy, paths, 0.0, cfg)))
    rings = []
    for j in range(1, rings_n + 1):
        rf = j / rings_n
        ring = []
        for i in range(segs):
            ang = 2.0 * math.pi * i / segs
            x = cx + rx * rf * math.cos(ang)
            y = cy + ry * rf * math.sin(ang)
            ring.append(bm.verts.new((x, y, _surface_z(x, y, xy, paths, rf, cfg))))
        rings.append(ring)

    def set_uv(face, coords):
        for loop, coord in zip(face.loops, coords):
            loop[uv].uv = coord

    for i in range(segs):
        i2 = (i + 1) % segs
        ang = 2.0 * math.pi * (i + 0.5) / segs
        face = bm.faces.new((center, rings[0][i], rings[0][i2]))
        set_uv(face, ((0.5, 0.5), (0.5 + 0.02 * math.cos(ang), 0.5 + 0.02 * math.sin(ang)), (0.5, 0.5)))
    for j in range(rings_n - 1):
        rf0 = (j + 1) / rings_n
        rf1 = (j + 2) / rings_n
        for i in range(segs):
            i2 = (i + 1) % segs
            a0 = 2.0 * math.pi * i / segs
            a1 = 2.0 * math.pi * i2 / segs
            face = bm.faces.new((rings[j][i], rings[j][i2], rings[j + 1][i2], rings[j + 1][i]))
            set_uv(face, (
                (0.5 + 0.5 * rf0 * math.cos(a0), 0.5 + 0.5 * rf0 * math.sin(a0)),
                (0.5 + 0.5 * rf0 * math.cos(a1), 0.5 + 0.5 * rf0 * math.sin(a1)),
                (0.5 + 0.5 * rf1 * math.cos(a1), 0.5 + 0.5 * rf1 * math.sin(a1)),
                (0.5 + 0.5 * rf1 * math.cos(a0), 0.5 + 0.5 * rf1 * math.sin(a0)),
            ))
    rim = rings[-1]
    cap = bm.verts.new((cx, cy, bottom))
    for i in range(segs):
        i2 = (i + 1) % segs
        face = bm.faces.new((cap, rim[i2], rim[i]))
        set_uv(face, ((0.5, 0.04), (0.5, 0.04), (0.5, 0.04)))
    return bm_to_mesh(bm, name, smooth=True)
