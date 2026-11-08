"""Short node collar where a pair of oval leaves will arise.

Not an erect stem, not a strap fan, and not a ring of sheath scars.
Material slot 0 is the node. Slots 1 and 2 stay on the mesh unused.
"""

import math

import bmesh

from .geometry import bm_to_mesh


def shoot_mesh(name, origin, stem_dir, side_hint, cfg, sides=8, arc=6):
    """A low collar on the rhizome node. The oval pair is a separate mesh."""
    d = stem_dir.normalized()
    side = (side_hint - d * side_hint.dot(d)).normalized()
    normal = d.cross(side).normalized()
    height = cfg["stem_height_m"]
    rx, ry = cfg["stem_radius_m"]
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    levels = (0.0, 0.42, 0.78, 1.0)
    flares = (1.15, 1.0, 0.82, 0.55)
    rings = []
    for zfrac, flare in zip(levels, flares):
        z = zfrac * height
        ring = []
        for k in range(sides):
            a = 2 * math.pi * k / sides
            ring.append(bm.verts.new(
                origin + d * z + side * (math.sin(a) * rx * flare) + normal * (math.cos(a) * ry * flare)
            ))
        rings.append(ring)
    for i in range(len(rings) - 1):
        for k in range(sides):
            k2 = (k + 1) % sides
            face = bm.faces.new((rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]))
            face.material_index = 0
            for loop, (kk, ii) in zip(face.loops, ((k, i), (k + 1, i), (k + 1, i + 1), (k, i + 1))):
                loop[uv].uv = (kk / sides, levels[ii])
    for ring, rev, v in ((rings[0], True, 0.0), (rings[-1], False, 1.0)):
        face = bm.faces.new(tuple(reversed(ring)) if rev else tuple(ring))
        face.material_index = 0
        for loop in face.loops:
            loop[uv].uv = (0.5, v)
    return bm_to_mesh(bm, name)
