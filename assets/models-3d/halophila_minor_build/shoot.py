"""Wedge-shaped sheath scales at a rhizome node.

Halophila minor has no erect strap stem and no scar rings. Each scale is
narrow at the buried stem and wider at the top. Material slot 0 is the sheath.
"""

import math

import bmesh

from .geometry import bm_to_mesh


def shoot_mesh(name, origin, stem_dir, side_hint, cfg, sides=10, arc=12):
    """One wedge: narrow on the buried stem, wide where the two petioles leave."""
    del arc
    d = stem_dir.normalized()
    side = (side_hint - d * side_hint.dot(d)).normalized()
    normal = d.cross(side).normalized()
    height = max(0.002, float(cfg["stem_height_m"]))
    wall = float(cfg["sheath_wall_m"])
    around = max(8, int(sides))
    levels = 6
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    rings = []
    for i in range(levels):
        f = i / (levels - 1)
        half_w = 0.00045 + 0.0028 * (f ** 0.80)
        half_t = wall * (1.35 - 0.55 * f)
        center = origin + d * (height * f)
        ring = []
        for k in range(around):
            ang = 2.0 * 3.14159265 * k / around
            ring.append(bm.verts.new(center + side * (half_w * math.cos(ang)) + normal * (half_t * math.sin(ang))))
        rings.append(ring)
    for i in range(levels - 1):
        v0 = i / (levels - 1)
        v1 = (i + 1) / (levels - 1)
        for k in range(around):
            k2 = (k + 1) % around
            face = bm.faces.new((rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]))
            face.material_index = 0
            for loop, coord in zip(face.loops, ((k / around, v0), (k2 / around, v0), (k2 / around, v1), (k / around, v1))):
                loop[uv].uv = coord
    for ring, reverse, v in ((rings[0], True, 0.0), (rings[-1], False, 1.0)):
        face = bm.faces.new(tuple(reversed(ring)) if reverse else tuple(ring))
        face.material_index = 0
        for loop in face.loops:
            loop[uv].uv = (0.5, v)
    return bm_to_mesh(bm, name)
