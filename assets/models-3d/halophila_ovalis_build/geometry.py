"""Flat oval spoons and thin tubes (rhizome, fine roots), skinned from Authoring curves."""

import bisect
import math

import bmesh
import bpy
from mathutils import Vector

from .textures import vein_xs
from .util import arc_table, frame_at, point_at, smoothstep, tangent_at


def bm_to_mesh(bm, name):
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    for poly in mesh.polygons:
        poly.use_smooth = True
    return mesh


def strap_profile(vein_count):
    """Closed cross-section: (x across width, face side, is_vein). Upper face carries the vein lanes."""
    xs = vein_xs(vein_count)
    upper = []
    for k, x in enumerate(xs):
        upper.append((x, 1.0, True))
        if k < len(xs) - 1:
            upper.append((0.5 * (x + xs[k + 1]), 1.0, False))
    lower = [(x, -1.0, False) for x in (0.9, 0.3, -0.3, -0.9)]
    return [(-1.0, 0.0, False)] + upper + [(1.0, 0.0, False)] + lower


def leaf_mesh(name, dense, width, thickness, vein_count, side_hint, twist, groove, crown, body_rings=8):
    """Flat strap about `width` wide and `thickness` thick with a semicircular tip."""
    cum = arc_table(dense)
    length = cum[-1]
    r = 0.5 * width
    tip_start = max(0.5 * length, length - r)
    stations = []
    for k in range(body_rings):
        d = tip_start * k / (body_rings - 1)
        hw = r * (0.80 + 0.20 * smoothstep(d / (0.10 * length)))
        stations.append((d, hw, 1.0))
    for deg in (22, 42, 58, 71, 81):
        phi = math.radians(deg)
        stations.append((tip_start + (length - tip_start) * math.sin(phi), r * math.cos(phi), 0.55 + 0.45 * math.cos(phi)))

    profile = strap_profile(vein_count)
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    rings, ring_uv = [], []
    for d, hw, tf in stations:
        p = point_at(dense, cum, d)
        side, normal = frame_at(tangent_at(dense, cum, d), side_hint, twist * d / length)
        ht = 0.5 * thickness * tf
        ring, coords = [], []
        for x, face, is_vein in profile:
            y = face * ht + crown * tf * (1.0 - x * x)
            if is_vein:
                y -= groove * tf
            ring.append(bm.verts.new(p + side * (x * hw) + normal * y))
            coords.append((0.5 + 0.5 * x, d / length))
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
        loop[uv].uv = ring_uv[0][rings[0].index(loop.vert)]
    apex = bm.verts.new(point_at(dense, cum, length))
    last = rings[-1]
    for j in range(m):
        j2 = (j + 1) % m
        face = bm.faces.new((last[j], last[j2], apex))
        for loop, c in zip(face.loops, (ring_uv[-1][j], ring_uv[-1][j2], (0.5, 1.0))):
            loop[uv].uv = c
    return bm_to_mesh(bm, name)


# Closed section of the spoon. x is across the blade, y is the face.
# The walk goes across the upper face, then back along the underside.
_SPOON = (
    (-1.00, 0.00),
    (-0.78, 0.55),
    (-0.48, 0.92),
    (-0.20, 1.05),
    (0.00, 1.08),
    (0.20, 1.05),
    (0.48, 0.92),
    (0.78, 0.55),
    (1.00, 0.00),
    (0.62, -0.42),
    (0.22, -0.62),
    (-0.22, -0.62),
    (-0.62, -0.42),
)


def _ellipse(t):
    """True ellipse along the blade. 0 at the join and the tip, 1 in the middle."""
    u = (t - 0.5) / 0.5
    return math.sqrt(max(0.0, 1.0 - u * u))


def _spoon_frame(tangent, twist):
    """Face the blade toward the front of the bed and a little upward.

    Width stays perpendicular to the petiole, so the outline is an oval
    in that facing plane. A strap's edge-on ribbon is a different plant.
    """
    view = Vector((0.0, -0.78, 0.58))
    view.normalize()
    normal = view - tangent * view.dot(tangent)
    if normal.length < 1e-6:
        normal = Vector((0.0, 0.0, 1.0))
    normal.normalize()
    side = normal.cross(tangent)
    if side.length < 1e-6:
        side = tangent.orthogonal()
    side.normalize()
    if side.z < 0.0:
        side.negate()
        normal.negate()
    if twist:
        c, s = math.cos(twist), math.sin(twist)
        side, normal = side * c + normal * s, normal * c - side * s
        side.normalize()
        normal.normalize()
    return side, normal


def _ridge(t, veins):
    """Separate cross-vein ridges. They fade out between the eight lines."""
    best = 0.0
    for vu in veins:
        best = max(best, math.exp(-((t - vu) ** 2) / (2.0 * 0.011 ** 2)))
    return best


def oval_leaf_mesh(name, dense, width, thickness, side_hint, twist, petiole_frac, pairs, petiole_radius):
    """Thin petiole plus a flat oval blade with eight cross-vein ridges.

    `pairs` is 8, the bottom of the "eight or more" range. The surface has
    no hairs. The blade is an ellipse, wider through the middle, rounded
    at the tip, and larger than a small oval. It is not a strap.
    `side_hint` is unused: the face is aimed at the front of the meadow.
    """
    from .config import cross_vein_us

    del side_hint
    cum = arc_table(dense)
    length = max(cum[-1], 1e-9)
    frac = max(0.2, min(0.7, float(petiole_frac)))
    pet = frac * length
    pr = float(petiole_radius)
    half_w = 0.5 * float(width)
    half_t = 0.5 * float(thickness)
    n_pairs = int(pairs)
    veins = cross_vein_us(n_pairs)

    ts = [0.0, 0.12]
    for i, vu in enumerate(veins):
        if i:
            ts.append(round(0.5 * (veins[i - 1] + vu), 5))
        ts.append(round(vu, 5))
    ts.extend((0.90, 0.965))
    blade_ts = sorted({round(t, 5) for t in ts if 0.0 <= t <= 0.965})

    stations = []
    for k in range(4):
        stations.append((pet * k / 4.0, None))
    for t in blade_ts:
        stations.append((pet + (length - pet) * t, t))

    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    rings, ring_uv = [], []
    for d, blade_t in stations:
        p = point_at(dense, cum, min(d, length * 0.992))
        side, normal = _spoon_frame(tangent_at(dense, cum, d), twist)
        ring, coords = [], []
        if blade_t is None:
            blend = 0.0
            ridge = 0.0
            ell = 0.0
        else:
            blend = smoothstep(min(1.0, blade_t / 0.12))
            ridge = _ridge(blade_t, veins) * blend
            ell = _ellipse(blade_t)
        hw = max(pr, half_w * max(ell, 0.04))
        ht = half_t * (0.55 + 0.45 * max(ell, 0.35))
        for px, py in _SPOON:
            ang = math.atan2(py, px if abs(px) + abs(py) > 1e-8 else 1.0)
            cx = math.cos(ang) * pr
            cy = math.sin(ang) * pr
            face = py
            if py >= -0.01:
                span = math.sqrt(max(0.0, 1.0 - (px * 0.94) ** 2))
                face = py + ridge * 2.4 * span
                face += 0.70 * math.exp(-(px * px) / (2.0 * 0.10 ** 2))
            ex = px * hw
            ey = face * ht
            x = cx * (1.0 - blend) + ex * blend
            y = cy * (1.0 - blend) + ey * blend
            ring.append(bm.verts.new(p + side * x + normal * y))
            coords.append((0.5 + 0.5 * px, d / length))
        rings.append(ring)
        ring_uv.append(coords)

    m = len(_SPOON)
    for i in range(len(rings) - 1):
        for j in range(m):
            j2 = (j + 1) % m
            face = bm.faces.new((rings[i][j], rings[i][j2], rings[i + 1][j2], rings[i + 1][j]))
            for loop, c in zip(face.loops, (ring_uv[i][j], ring_uv[i][j2], ring_uv[i + 1][j2], ring_uv[i + 1][j])):
                loop[uv_layer].uv = c
    base = bm.faces.new(tuple(reversed(rings[0])))
    for loop in base.loops:
        loop[uv_layer].uv = (0.5, 0.0)
    apex = bm.verts.new(point_at(dense, cum, length))
    last = rings[-1]
    for j in range(m):
        j2 = (j + 1) % m
        face = bm.faces.new((last[j], last[j2], apex))
        for loop, c in zip(face.loops, (ring_uv[-1][j], ring_uv[-1][j2], (0.5, 1.0))):
            loop[uv_layer].uv = c
    mesh = bm_to_mesh(bm, name)
    mesh["ho_cross_pairs"] = n_pairs
    mesh["ho_hairs"] = 0
    mesh["ho_outline"] = "oval"
    return mesh


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


def rhizome_mesh(name, dense, node_ds, radius, oval, step=0.006, sides=8):
    """One welded tube. Each vertex is weighted to the internode bone it sits on."""
    end = arc_table(dense)[-1]
    ds = []
    marks = list(node_ds) + [end]
    for k in range(len(marks) - 1):
        a, b = marks[k], marks[k + 1]
        count = max(2, round((b - a) / step))
        ds.extend(a + (b - a) * s / count for s in range(count))
    ds.append(end)
    radii = []
    for d in ds:
        rr = radius
        for nd in node_ds:
            rr *= 1.0 + 0.14 * math.exp(-((d - nd) ** 2) / (2 * 0.0025 ** 2))
        rr *= 0.7 + 0.3 * smoothstep(d / 0.004)
        rr *= 0.4 + 0.6 * smoothstep((end - d) / 0.012)
        radii.append(rr)
    mesh, ring_of = tube_mesh(name, dense, ds, radii, sides, oval, Vector((0.0, 0.0, 1.0)))
    nseg = len(node_ds) - 1
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
