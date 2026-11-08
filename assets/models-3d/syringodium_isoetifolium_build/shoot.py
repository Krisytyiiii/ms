"""Short round stem and a closed collar. Not a split strap sheath."""

import math

import bmesh

from .geometry import bm_to_mesh


def _ring(bm, origin, direction, side, normal, z, radius, sides):
    verts = []
    for k in range(sides):
        a = 2 * math.pi * k / sides
        verts.append(bm.verts.new(
            origin
            + direction * z
            + side * (math.sin(a) * radius)
            + normal * (math.cos(a) * radius)
        ))
    return verts


def shoot_mesh(name, origin, stem_dir, side_hint, cfg, sides=12, arc=12):
    del arc
    d = stem_dir.normalized()
    side = (side_hint - d * side_hint.dot(d)).normalized()
    normal = d.cross(side).normalized()
    height = cfg["stem_height_m"]
    radius = cfg["stem_radius_m"]
    flare = cfg["sheath_flare_m"]
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")

    levels = [
        (0.0, radius, 0),
        (0.22 * height, radius, 0),
        (0.34 * height, radius * 1.08, 2),
        (0.42 * height, radius, 0),
        (0.55 * height, radius, 0),
        (0.64 * height, radius + flare, 1),
        (1.0 * height, radius + flare * 1.15, 1),
        (1.04 * height, radius + flare * 0.35, 1),
    ]
    rings = [_ring(bm, origin, d, side, normal, z, rad, sides) for z, rad, _mat in levels]
    for i in range(len(rings) - 1):
        mat = levels[i][2] if levels[i][2] == levels[i + 1][2] else 0
        for k in range(sides):
            k2 = (k + 1) % sides
            face = bm.faces.new((rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]))
            face.material_index = mat
            v0 = levels[i][0] / height
            v1 = levels[i + 1][0] / height
            for loop, (kk, vv) in zip(face.loops, ((k, v0), (k + 1, v0), (k + 1, v1), (k, v1))):
                loop[uv].uv = (kk / sides, vv)
    for ring, rev, mat in ((rings[0], True, 0), (rings[-1], False, 1)):
        face = bm.faces.new(tuple(reversed(ring)) if rev else tuple(ring))
        face.material_index = mat
    return bm_to_mesh(bm, name)
