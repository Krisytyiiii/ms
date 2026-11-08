"""Short erect stem with flush scar rings and a solid split sheath.

Material slots: 0 stem, 1 sheath, 2 scar.
"""

import math

import bmesh

from .geometry import bm_to_mesh


def shoot_mesh(name, origin, stem_dir, side_hint, cfg, sides=10, arc=12):
    d = stem_dir.normalized()
    side = (side_hint - d * side_hint.dot(d)).normalized()
    normal = d.cross(side).normalized()
    height = cfg["stem_height_m"]
    rx, ry = cfg["stem_radius_m"]
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")

    def vert(z, a, ax, ay):
        return bm.verts.new(origin + d * z + side * (math.sin(a) * ax) + normal * (math.cos(a) * ay))

    # Open scar line on the bare stem. The gap is centered on the camera side
    # (local angle 0.5, which is -normal). The raised band stops on both sides
    # of that gap, so the scar does not meet around the stem.
    half = cfg["scar_half_m"]
    proud = cfg["scar_proud_m"]

    def on_scar(k):
        ang = k / float(sides)
        delta = abs(ang - 0.5)
        if delta > 0.5:
            delta = 1.0 - delta
        return delta >= 0.26

    levels = [(0.0, 0.0, None)]
    for g, frac in enumerate(cfg["scar_fracs"]):
        z = frac * height
        levels += [(z - half, 0.0, g), (z, proud, g), (z + half, 0.0, g)]
    levels.append((0.56 * height, 0.0, None))
    rings = []
    for z, extra, _g in levels:
        ring = []
        for k in range(sides):
            bump = extra if on_scar(k) else 0.0
            ring.append(vert(z, 2 * math.pi * k / sides, rx + bump, ry + bump))
        rings.append(ring)
    for i in range(len(rings) - 1):
        g0, g1 = levels[i][2], levels[i + 1][2]
        for k in range(sides):
            k2 = (k + 1) % sides
            mat = 2 if g0 is not None and g0 == g1 and on_scar(k) and on_scar(k2) else 0
            face = bm.faces.new((rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]))
            face.material_index = mat
            for loop, (kk, ii) in zip(face.loops, ((k, i), (k + 1, i), (k + 1, i + 1), (k, i + 1))):
                loop[uv].uv = (kk / sides, levels[ii][0] / height)
    for ring, rev in ((rings[0], True), (rings[-1], False)):
        face = bm.faces.new(tuple(reversed(ring)) if rev else tuple(ring))
        face.material_index = 0

    # Broad triangle: narrow where it grips the stem, wide and flat at the top.
    # A large slit keeps it a plate facing the camera, not a round sleeve.
    wall = cfg["sheath_wall_m"]
    fracs = (0.38, 0.60, 0.82, 1.0)
    outer = (
        (rx * 1.45, ry * 1.05),
        (rx * 2.6, ry * 1.08),
        (rx * 3.9, ry * 1.12),
        (rx * 5.2, ry * 1.15),
    )
    slit = (2.48, 2.38, 2.28, 2.16)
    zs = [f * height for f in fracs]
    walls = {"o": [], "i": []}
    for z, (ax, ay), s in zip(zs, outer, slit):
        angles = [s + (2 * math.pi - 2 * s) * k / arc for k in range(arc + 1)]
        walls["o"].append([vert(z, a, ax, ay) for a in angles])
        walls["i"].append([vert(z, a, max(rx * 0.9, ax - wall), max(ry * 0.9, ay - wall)) for a in angles])

    def quad(a, b, c, e, u0, u1, v0, v1):
        face = bm.faces.new((a, b, c, e))
        face.material_index = 1
        for loop, coord in zip(face.loops, ((u0, v0), (u1, v0), (u1, v1), (u0, v1))):
            loop[uv].uv = coord

    o, n = walls["o"], walls["i"]
    for j in range(len(zs) - 1):
        v0, v1 = j / 3, (j + 1) / 3
        for k in range(arc):
            u0, u1 = k / arc, (k + 1) / arc
            quad(o[j][k], o[j][k + 1], o[j + 1][k + 1], o[j + 1][k], u0, u1, v0, v1)
            quad(n[j][k + 1], n[j][k], n[j + 1][k], n[j + 1][k + 1], u1, u0, v0, v1)
        quad(o[j][0], o[j + 1][0], n[j + 1][0], n[j][0], 0, 0.02, v0, v1)
        quad(n[j][arc], n[j + 1][arc], o[j + 1][arc], o[j][arc], 0.98, 1, v0, v1)
    for j in (0, len(zs) - 1):
        for k in range(arc):
            quad(o[j][k], n[j][k], n[j][k + 1], o[j][k + 1], k / arc, (k + 1) / arc, j / 3, j / 3)
    return bm_to_mesh(bm, name)
