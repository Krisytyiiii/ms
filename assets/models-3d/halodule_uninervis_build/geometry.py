"""Needle leaves and tubes (rhizome, roots), skinned from Authoring curves."""

import bisect
import math

import bmesh
import bpy
from mathutils import Vector

from .util import arc_table, frame_at, point_at, smoothstep, tangent_at


def bm_to_mesh(bm, name):
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    for poly in mesh.polygons:
        poly.use_smooth = True
    return mesh


def needle_profile():
    """Narrow lenticular blade with one pinched midrib. Not a flat ribbon."""
    return (
        (-1.00, 0.00, False),
        (-0.70, 0.48, False),
        (-0.36, 0.92, False),
        (-0.12, 0.58, False),
        (0.00, 0.16, True),
        (0.12, 0.58, False),
        (0.36, 0.92, False),
        (0.70, 0.48, False),
        (1.00, 0.00, False),
        (0.52, -0.42, False),
        (0.00, -0.66, False),
        (-0.52, -0.42, False),
    )


def _tooth(bm, uv, origin, tangent, side, normal, x0, x1, tip_x, reach, ht, u0, u1, v0, v1):
    """One tooth of the trident. Lengths are metres along the leaf, not a cap bump."""
    def co(along, x, up):
        return origin + tangent * along + side * x + normal * (up * ht)

    mid = reach * 0.42
    xm = (x0 + x1) * 0.5
    half = max(0.00012, (x1 - x0) * 0.34)
    drift = tip_x - xm
    verts = [
        bm.verts.new(co(0.0, x0, 0.62)),
        bm.verts.new(co(0.0, x1, 0.62)),
        bm.verts.new(co(0.0, x1, -0.28)),
        bm.verts.new(co(0.0, x0, -0.28)),
        bm.verts.new(co(mid, xm - half + drift * 0.35, 0.30)),
        bm.verts.new(co(mid, xm + half + drift * 0.35, 0.30)),
        bm.verts.new(co(mid, xm + half + drift * 0.35, -0.12)),
        bm.verts.new(co(mid, xm - half + drift * 0.35, -0.12)),
        bm.verts.new(co(reach, tip_x, 0.04)),
    ]
    u_mid = 0.5 * (u0 + u1)
    v_mid = (v0 + v1) * 0.5
    coords = [
        (u0, v0), (u1, v0), (u1, v0), (u0, v0),
        (u0, v_mid), (u1, v_mid), (u1, v_mid), (u0, v_mid),
        (u_mid, v1),
    ]
    faces = (
        (0, 1, 5, 4),
        (1, 2, 6, 5),
        (2, 3, 7, 6),
        (3, 0, 4, 7),
        (4, 5, 8),
        (5, 6, 8),
        (6, 7, 8),
        (7, 4, 8),
    )
    for seq in faces:
        face = bm.faces.new(tuple(verts[i] for i in seq))
        for loop, i in zip(face.loops, seq):
            loop[uv].uv = coords[i]


def _trident(bm, uv, ring, center, tangent, side, normal, hw, ht, v0, mid_m, side_m, splay_m):
    """Three points on the end of the needle. The middle tooth is the long one.

    Tooth lengths are display choices so the fork reads in a still. This is
    not a rounded tip and not a vein drawn on a round end.
    """
    cap = bm.verts.new(center)
    m = len(ring)
    for j in range(m):
        j2 = (j + 1) % m
        face = bm.faces.new((ring[j], ring[j2], cap))
        for loop, c in zip(face.loops, ((0.15, v0), (0.85, v0), (0.5, v0))):
            loop[uv].uv = c
    v_side = v0 + 0.55 * (1.0 - v0)
    edge = hw * 0.92
    gap = min(hw * 0.28, 0.0005)
    _tooth(
        bm, uv, center, tangent, side, normal,
        -edge, -gap, -abs(splay_m), side_m, ht, 0.06, 0.28, v0, v_side,
    )
    _tooth(
        bm, uv, center, tangent, side, normal,
        gap, edge, abs(splay_m), side_m, ht, 0.72, 0.94, v0, v_side,
    )
    _tooth(
        bm, uv, center, tangent, side, normal,
        -gap * 0.8, gap * 0.8, 0.0, mid_m, ht, 0.40, 0.60, v0, 1.0,
    )


def _finish_leaf(bm, name, tip_v):
    mesh = bm_to_mesh(bm, name)
    uv_data = mesh.uv_layers["UVMap"].data
    for poly in mesh.polygons:
        acc = 0.0
        n = len(poly.loop_indices)
        for i in poly.loop_indices:
            acc += uv_data[i].uv.y
        if n and acc / n >= tip_v - 1e-4:
            poly.use_smooth = False
    return mesh


def leaf_mesh(
    name, dense, width, thickness, vein_count, side_hint, twist, groove, crown,
    trident_mid=0.016, trident_side=0.009, trident_splay=0.0055, body_rings=8,
):
    """Narrow needle with one midrib groove and a three-point tip."""
    cum = arc_table(dense)
    length = max(cum[-1], 1e-9)
    r = 0.5 * width
    mid_m = max(0.008, min(float(trident_mid), 0.24 * length))
    side_m = max(0.004, min(float(trident_side), mid_m * 0.72))
    shoulder = max(0.52 * length, length - mid_m)
    stations = []
    rings_n = max(4, body_rings)
    for k in range(rings_n):
        d = shoulder * k / (rings_n - 1)
        u = d / length
        base = 0.62 + 0.38 * smoothstep(min(1.0, u / 0.08))
        taper = 1.0 - 0.16 * max(0.0, (u - 0.70) / 0.30)
        stations.append((d, r * base * taper, 1.0))

    profile = needle_profile()
    t0 = tangent_at(dense, cum, 0.0)
    _s0, n0 = frame_at(t0, side_hint, 0.0)
    face_camera = n0.y > 0.0
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    rings, ring_uv = [], []
    frame = None
    for d, hw, tf in stations:
        p = point_at(dense, cum, d)
        tangent = tangent_at(dense, cum, d)
        side, normal = frame_at(tangent, side_hint, twist * d / length)
        if face_camera:
            side, normal = -side, -normal
        ht = 0.5 * thickness * tf
        ring, coords = [], []
        for x, face, is_vein in profile:
            y = face * ht + crown * tf * (1.0 - x * x)
            if is_vein and vein_count <= 1:
                y -= groove * 0.55 * tf
            ring.append(bm.verts.new(p + side * (x * hw) + normal * y))
            coords.append((0.5 + 0.5 * x, d / length))
        rings.append(ring)
        ring_uv.append(coords)
        frame = (p, tangent, side, normal, hw, ht, d / length)

    m = len(profile)
    for i in range(len(rings) - 1):
        for j in range(m):
            j2 = (j + 1) % m
            face = bm.faces.new((rings[i][j], rings[i][j2], rings[i + 1][j2], rings[i + 1][j]))
            for loop, c in zip(face.loops, (ring_uv[i][j], ring_uv[i][j2], ring_uv[i + 1][j2], ring_uv[i + 1][j])):
                loop[uv].uv = c
    base = bm.faces.new(tuple(reversed(rings[0])))
    for loop in base.loops:
        loop[uv].uv = ring_uv[0][rings[0].index(loop.vert)]
    p, tangent, side, normal, hw, ht, v0 = frame
    _trident(bm, uv, rings[-1], p, tangent, side, normal, hw, ht, v0, mid_m, side_m, trident_splay)
    return _finish_leaf(bm, name, v0)


def tube_mesh(name, dense, ds, radii, sides, oval, side_hint):
    """Closed oval tube through the stations `ds` (arc distances). Returns mesh and ring index per vertex."""
    cum = arc_table(dense)
    length = max(cum[-1], 1e-9)
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    rings, ring_of = [], []
    for i, d in enumerate(ds):
        p = point_at(dense, cum, d)
        side, normal = frame_at(tangent_at(dense, cum, d), side_hint)
        ring = []
        for k in range(sides):
            a = 2 * math.pi * k / sides
            ring.append(bm.verts.new(p + side * (math.cos(a) * radii[i] * oval) + normal * (math.sin(a) * radii[i])))
            ring_of.append(i)
        rings.append(ring)
    for i in range(len(rings) - 1):
        for k in range(sides):
            k2 = (k + 1) % sides
            face = bm.faces.new((rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]))
            for loop, (kk, ii) in zip(face.loops, ((k, i), (k + 1, i), (k + 1, i + 1), (k, i + 1))):
                loop[uv].uv = (kk / sides, ds[ii] / length)
    for ring, rev in ((rings[0], True), (rings[-1], False)):
        face = bm.faces.new(tuple(reversed(ring)) if rev else tuple(ring))
        for loop in face.loops:
            loop[uv].uv = (0.5, 0.0 if rev else 1.0)
    return bm_to_mesh(bm, name), ring_of


def _scar_weight(d, node_ds, scar_half):
    best = 0.0
    for nd in node_ds:
        dist = abs(d - nd)
        if dist < scar_half:
            best = max(best, 1.0 - dist / scar_half)
    return best


def rhizome_mesh(name, dense, node_ds, radius, oval, step=0.006, sides=8, scar_half=0.00055, scar_proud=0.00032):
    """Pale tube. Clean black scar rings sit on the nodes. Material 1 is the scar."""
    end = arc_table(dense)[-1]
    ds = []
    marks = list(node_ds) + [end]
    for k in range(len(marks) - 1):
        a, b = marks[k], marks[k + 1]
        count = max(2, round((b - a) / step))
        ds.extend(a + (b - a) * s / count for s in range(count))
    ds.append(end)
    for nd in node_ds:
        for delta in (-scar_half, -0.45 * scar_half, 0.45 * scar_half, scar_half):
            ds.append(min(end, max(0.0, nd + delta)))
    ds = sorted(set(round(d, 6) for d in ds))
    radii = []
    for d in ds:
        rr = radius
        for nd in node_ds:
            rr *= 1.0 + 0.05 * math.exp(-((d - nd) ** 2) / (2 * 0.0022 ** 2))
        rr *= 0.7 + 0.3 * smoothstep(d / 0.004)
        rr *= 0.4 + 0.6 * smoothstep((end - d) / 0.012)
        rr += scar_proud * _scar_weight(d, node_ds, scar_half)
        radii.append(rr)
    mesh, ring_of = tube_mesh(name, dense, ds, radii, sides, oval, Vector((0.0, 0.0, 1.0)))
    length = max(end, 1e-9)
    uv_data = mesh.uv_layers["UVMap"].data
    for poly in mesh.polygons:
        mid = 0.0
        for loop in poly.loop_indices:
            mid += uv_data[loop].uv[1]
        mid /= max(1, len(poly.loop_indices))
        if _scar_weight(mid * length, node_ds, scar_half) > 0.28:
            poly.material_index = 1
    nseg = max(1, len(node_ds) - 1)
    groups = {}
    for vid, ring in enumerate(ring_of):
        seg = min(nseg - 1, max(0, bisect.bisect_right(node_ds, ds[ring] + 1e-7) - 1))
        groups.setdefault("rhizome_%02d" % seg, []).append(vid)
    return mesh, groups


def root_mesh(name, dense, radius, rings=6, sides=5):
    length = arc_table(dense)[-1]
    ds = [length * k / (rings - 1) for k in range(rings)]
    radii = [radius * (1.0 - 0.7 * (d / length)) for d in ds]
    mesh, _ring_of = tube_mesh(name, dense, ds, radii, sides, 1.0, Vector((1.0, 0.0, 0.0)))
    return mesh
