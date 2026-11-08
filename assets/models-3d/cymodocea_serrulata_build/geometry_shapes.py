"""Leaf tips and organs the strap builder does not cover.

Tooth count on a serrated tip is a display choice. It is not a measurement.
"""

import math

import bmesh
from mathutils import Vector

from .geometry import bm_to_mesh
from .util import arc_table, frame_at, point_at, tangent_at


def _saw_stations(length, r):
    """Long parallel strap. Small teeth only on the apical margin.

    The tooth count is a display choice. It is not a measurement.
    A tooth is a short nick in the edge, not a zigzag of the whole blade.
    """
    tip0 = 0.80 * length
    out = []
    for k in range(12):
        d = tip0 * k / 11.0
        grow = min(1.0, d / max(1e-4, 0.035 * length))
        out.append((d, r * (0.90 + 0.10 * grow), 1.0, False))
    teeth = 8
    span = max(length - tip0, 1e-4)
    for i in range(teeth):
        for local, kind in ((0.0, 0.0), (0.36, 1.0), (0.74, 0.0)):
            u = (i + local) / teeth
            if u > 0.96:
                continue
            d = tip0 + span * u
            close = 1.0 - 0.28 * (u ** 1.1)
            hw = r * close * (0.84 + 0.30 * kind)
            out.append((d, max(hw, r * 0.08), 0.88, True))
    out.append((min(length * 0.996, length - 1e-5), r * 0.10, 0.40, True))
    cleaned = [out[0]]
    for item in out[1:]:
        if item[0] <= cleaned[-1][0] + 1e-5:
            continue
        cleaned.append(item)
    return cleaned


def serrated_strap_mesh(name, dense, width, thickness, side_hint, twist, crown):
    """Wide flat strap. Sides stay parallel. The tip is a saw, not a round end."""
    import bmesh

    from .geometry import bm_to_mesh
    from .util import arc_table, frame_at, point_at, tangent_at

    cum = arc_table(dense)
    length = max(cum[-1], 1e-9)
    r = 0.5 * float(width)
    stations = _saw_stations(length, r)
    profile = (
        (-1.0, 0.0),
        (-0.55, 1.0),
        (0.0, 1.0),
        (0.55, 1.0),
        (1.0, 0.0),
        (0.5, -0.9),
        (0.0, -0.9),
        (-0.5, -0.9),
    )
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    rings, ring_uv, sharp = [], [], []
    for d, hw, tf, is_saw in stations:
        p = point_at(dense, cum, d)
        side, normal = frame_at(tangent_at(dense, cum, d), side_hint, twist * d / length)
        ht = 0.5 * float(thickness) * tf
        ring, coords = [], []
        for x, face in profile:
            yy = face * ht + float(crown) * tf * (1.0 - x * x)
            ring.append(bm.verts.new(p + side * (x * hw) + normal * yy))
            coords.append((0.5 + 0.5 * x, d / length))
        rings.append(ring)
        ring_uv.append(coords)
        sharp.append(is_saw)
    m = len(profile)
    for i in range(len(rings) - 1):
        for j in range(m):
            j2 = (j + 1) % m
            face = bm.faces.new((rings[i][j], rings[i][j2], rings[i + 1][j2], rings[i + 1][j]))
            face.smooth = not (sharp[i] or sharp[i + 1])
            for loop, c in zip(face.loops, (ring_uv[i][j], ring_uv[i][j2], ring_uv[i + 1][j2], ring_uv[i + 1][j])):
                loop[uv].uv = c
    base = bm.faces.new(tuple(reversed(rings[0])))
    base.smooth = False
    for loop in base.loops:
        loop[uv].uv = ring_uv[0][rings[0].index(loop.vert)]
    apex = bm.verts.new(point_at(dense, cum, length))
    last = rings[-1]
    for j in range(m):
        j2 = (j + 1) % m
        face = bm.faces.new((last[j], last[j2], apex))
        face.smooth = False
        for loop, c in zip(face.loops, (ring_uv[-1][j], ring_uv[-1][j2], (0.5, 1.0))):
            loop[uv].uv = c
    return bm_to_mesh(bm, name)


def trident_stations(length, r, tip_start):
    """Three-point tip: side teeth, a notch, then a longer middle tooth."""
    span = max(length - tip_start, 1e-4)
    specs = (
        (0.06, 0.90, 0.82),
        (0.20, 1.06, 0.78),
        (0.34, 0.20, 0.48),
        (0.48, 0.18, 0.44),
        (0.68, 0.14, 0.38),
        (0.86, 0.07, 0.30),
        (1.00, 0.012, 0.18),
    )
    return [(tip_start + span * t, r * hw, tf) for t, hw, tf in specs]


def cylinder_leaf_mesh(name, dense, diameter, side_hint, twist, body_rings=8):
    """Round leaf. The last stretch tapers to a point. Diameter is the caller's width."""
    cum = arc_table(dense)
    length = max(cum[-1], 1e-9)
    radius = 0.5 * diameter
    sides = 8
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    rings, ring_uv = [], []
    for k in range(body_rings):
        t = k / (body_rings - 1)
        d = length * t
        if t > 0.80:
            u = (t - 0.80) / 0.20
            rad = radius * (1.0 - u)
        else:
            rad = radius * (0.82 + 0.18 * min(1.0, t / 0.08))
        p = point_at(dense, cum, d)
        side, normal = frame_at(tangent_at(dense, cum, d), side_hint, twist * t)
        ring, coords = [], []
        for s in range(sides):
            a = 2 * math.pi * s / sides
            ring.append(bm.verts.new(p + side * (math.cos(a) * rad) + normal * (math.sin(a) * rad)))
            coords.append((s / sides, t))
        rings.append(ring)
        ring_uv.append(coords)
    for i in range(len(rings) - 1):
        for j in range(sides):
            j2 = (j + 1) % sides
            face = bm.faces.new((rings[i][j], rings[i][j2], rings[i + 1][j2], rings[i + 1][j]))
            for loop, c in zip(face.loops, (ring_uv[i][j], ring_uv[i][j2], ring_uv[i + 1][j2], ring_uv[i + 1][j])):
                loop[uv].uv = c
    base = bm.faces.new(tuple(reversed(rings[0])))
    for loop in base.loops:
        loop[uv].uv = (0.5, 0.0)
    apex = bm.verts.new(point_at(dense, cum, length))
    last = rings[-1]
    for j in range(sides):
        j2 = (j + 1) % sides
        face = bm.faces.new((last[j], last[j2], apex))
        for loop, c in zip(face.loops, (ring_uv[-1][j], ring_uv[-1][j2], (0.5, 1.0))):
            loop[uv].uv = c
    return bm_to_mesh(bm, name)


def oval_leaf_mesh(name, dense, width, thickness, side_hint, twist, body_rings=8):
    """Paired-leaf blade. The narrow base is a display petiole, not a measured length."""
    cum = arc_table(dense)
    length = max(cum[-1], 1e-9)
    r = 0.5 * width
    profile = [(-1.0, 0.0), (-0.55, 1.0), (0.0, 1.0), (0.55, 1.0), (1.0, 0.0), (0.55, -1.0), (0.0, -1.0), (-0.55, -1.0)]
    petiole = 0.24
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    rings, ring_uv = [], []
    steps = max(body_rings, 8)
    for k in range(steps):
        t = k / (steps - 1)
        d = length * t
        if t < petiole:
            hw = r * (0.16 + 0.10 * (t / petiole))
            tf = 0.85
        else:
            u = (t - petiole) / (1.0 - petiole)
            hw = r * math.sin(math.pi * u) ** 0.72
            tf = 1.0
        p = point_at(dense, cum, d)
        side, normal = frame_at(tangent_at(dense, cum, d), side_hint, twist * t)
        ht = 0.5 * thickness * tf
        ring, coords = [], []
        for x, face in profile:
            ring.append(bm.verts.new(p + side * (x * hw) + normal * (face * ht)))
            coords.append((0.5 + 0.5 * x, t))
        rings.append(ring)
        ring_uv.append(coords)
    m = len(profile)
    for i in range(len(rings) - 1):
        for j in range(m):
            j2 = (j + 1) % m
            face = bm.faces.new((rings[i][j], rings[i][j2], rings[i + 1][j2], rings[i + 1][j]))
            for loop, c in zip(face.loops, (ring_uv[i][j], ring_uv[i][j2], ring_uv[i + 1][j2], ring_uv[i + 1][j])):
                loop[uv].uv = c
    base = bm.faces.new(tuple(reversed(rings[0])))
    for loop in base.loops:
        loop[uv].uv = (0.5, 0.0)
    apex = bm.verts.new(point_at(dense, cum, length))
    last = rings[-1]
    for j in range(m):
        j2 = (j + 1) % m
        face = bm.faces.new((last[j], last[j2], apex))
        for loop, c in zip(face.loops, (ring_uv[-1][j], ring_uv[-1][j2], (0.5, 1.0))):
            loop[uv].uv = c
    return bm_to_mesh(bm, name)


def _ring(bm, center, side, normal, radius, sides):
    verts = []
    for k in range(sides):
        a = 2 * math.pi * k / sides
        verts.append(bm.verts.new(center + side * (math.cos(a) * radius) + normal * (math.sin(a) * radius)))
    return verts


def scar_bands(name, dense, node_ds, radius):
    """Proud bands on the rhizome between nodes. One mesh, weighted per internode."""
    cum = arc_table(dense)
    end = cum[-1]
    bm = bmesh.new()
    groups = {}
    sides = 8
    nseg = max(1, len(node_ds) - 1)
    for seg in range(nseg):
        a = node_ds[seg]
        b = node_ds[seg + 1] if seg + 1 < len(node_ds) else end
        d = min(end, a + 0.42 * (b - a))
        p = point_at(dense, cum, d)
        tangent = tangent_at(dense, cum, d)
        side, normal = frame_at(tangent, Vector((0.0, 0.0, 1.0)))
        rings = []
        owned = []
        for step, extra in ((-0.00045, 0.0), (0.0, max(0.00025, radius * 0.28)), (0.00045, 0.0)):
            ring = _ring(bm, p + tangent * step, side, normal, radius + extra, sides)
            rings.append(ring)
            owned.extend(ring)
        for i in range(len(rings) - 1):
            for k in range(sides):
                k2 = (k + 1) % sides
                bm.faces.new((rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]))
        bm.verts.ensure_lookup_table()
        groups["rhizome_%02d" % min(seg, nseg - 1)] = [v.index for v in owned]
    return bm_to_mesh(bm, name), groups


def bristle_mesh(name, dense, node_ds, radius):
    """Black hairs on the rhizome. How many, and how long, is a display choice."""
    cum = arc_table(dense)
    end = cum[-1]
    bm = bmesh.new()
    groups = {}
    hairs = 4
    sides = 4
    length = max(0.004, radius * 2.6)
    nseg = max(1, len(node_ds) - 1)
    for seg in range(nseg):
        a = node_ds[seg]
        b = node_ds[seg + 1] if seg + 1 < len(node_ds) else end
        owned = []
        for h in range(hairs):
            d = min(end, a + (b - a) * (0.22 + 0.56 * h / max(1, hairs - 1)))
            p = point_at(dense, cum, d)
            tangent = tangent_at(dense, cum, d)
            side, normal = frame_at(tangent, Vector((0.0, 0.0, 1.0)))
            ang = h * 1.7 + seg * 0.4
            direction = (side * math.cos(ang) + normal * math.sin(ang) + Vector((0.0, 0.0, 0.55))).normalized()
            base = _ring(bm, p, side, normal, radius * 0.16, sides)
            tip = bm.verts.new(p + direction * length)
            owned.extend(base)
            owned.append(tip)
            for k in range(sides):
                k2 = (k + 1) % sides
                bm.faces.new((base[k], base[k2], tip))
        bm.verts.ensure_lookup_table()
        groups["rhizome_%02d" % min(seg, nseg - 1)] = [v.index for v in owned]
    return bm_to_mesh(bm, name), groups
