"""Solid strap leaves and tubes (rhizome, roots), skinned from Authoring curves."""

import bisect
import math

import bmesh
import bpy
from mathutils import Vector

from .util import arc_table, frame_at, point_at, smoothstep, tangent_at


def bm_to_mesh(bm, name, smooth=True):
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    for poly in mesh.polygons:
        poly.use_smooth = smooth
    return mesh


def _tape_centerline(hw, roll):
    """Wide channel with a thick inward roll on each margin.

    The flat middle stays wide. Each edge curls up and back over the face
    as a round lip, so the blade is a tape and not a smooth strap or a rod.
    """
    n = 25
    flat = 0.64
    pts = []
    curl = max(0.0045, 0.18 * hw) * min(max(roll, 0.2), 1.15)
    max_ang = math.radians(200.0)
    for i in range(n):
        u = -1.0 + 2.0 * i / (n - 1)
        au = abs(u)
        sign = 1.0 if u >= 0.0 else -1.0
        channel = 0.80 * hw
        if au <= flat or hw < 1e-5:
            x = 0.0 if flat < 1e-6 else (u / flat) * channel
            dish = 1.0 - (min(au, flat) / flat) ** 2 if flat > 1e-6 else 0.0
            pts.append((x, -0.08 * channel * max(dish, 0.0)))
            continue
        t = (au - flat) / (1.0 - flat)
        ang = t * max_ang
        x0 = sign * channel
        # Positive section-y is later flipped onto the near face.
        pts.append((x0 + sign * curl * math.sin(ang), curl * (1.0 - math.cos(ang))))
    return [(x, -y) for x, y in pts]


def _offset_loop(center, ht):
    """Closed strap: outer face, then the inner face, with real thickness."""
    outer, inner = [], []
    m = len(center)
    for i, (x, y) in enumerate(center):
        if i == 0:
            tx, ty = center[1][0] - x, center[1][1] - y
        elif i == m - 1:
            tx, ty = x - center[i - 1][0], y - center[i - 1][1]
        else:
            tx, ty = center[i + 1][0] - center[i - 1][0], center[i + 1][1] - center[i - 1][1]
        length = math.hypot(tx, ty) or 1.0
        nx, ny = -ty / length, tx / length
        outer.append((x + nx * ht, y + ny * ht))
        inner.append((x - nx * ht, y - ny * ht))
    return outer + list(reversed(inner))


def _tape_leaf(name, dense, width, thickness, side_hint, twist, roll):
    """Long tape blade. Margins stay rolled. The end is blunt, not a ribbon point."""
    cum = arc_table(dense)
    length = max(cum[-1], 1e-6)
    # `width` is the visual span. The curl sits inside that span.
    half_w = 0.5 * width
    tip0 = length * 0.988
    rings_n = 12 if length < 0.85 else 15
    stations = []
    for k in range(rings_n):
        stations.append((tip0 * k / (rings_n - 1), 1.0))
    # Short blunt end. The width stays broad; it does not run out to a ribbon point.
    stations.append((tip0 + (length - tip0) * 0.55, 0.90))
    stations.append((tip0 + (length - tip0) * 0.88, 0.72))
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    rings, ring_uv = [], []
    for d, width_scale in stations:
        hw = max(half_w * width_scale, 1e-5)
        roll_here = roll if width_scale > 0.6 else roll * (width_scale / 0.6)
        ht = 0.5 * thickness * (0.65 + 0.35 * width_scale)
        section = _offset_loop(_tape_centerline(hw, roll_here), ht)
        p = point_at(dense, cum, d)
        side, normal = frame_at(tangent_at(dense, cum, d), side_hint, twist * d / length)
        ring, coords = [], []
        half = max(1, len(section) // 2)
        for j, (dx, dy) in enumerate(section):
            ring.append(bm.verts.new(p + side * dx + normal * dy))
            if j < half:
                u = j / max(1, half - 1)
            else:
                u = 1.0 - (j - half) / max(1, half - 1)
            coords.append((u, d / length))
        rings.append(ring)
        ring_uv.append(coords)
    m = len(rings[0])
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
    return bm_to_mesh(bm, name, smooth=True)


def leaf_mesh(name, dense, width, thickness, vein_count, side_hint, twist, groove, crown, body_rings=8):
    """Inrolled tape. Width, veins, and a pointed strap tip are not used."""
    from .config import CONFIG

    roll = float(CONFIG.get("margin_roll", 1.0))
    return _tape_leaf(name, dense, width, thickness, side_hint, twist, roll)


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


def root_mesh(name, dense, radius, rings=8, sides=8):
    """Cord: thick to the tip. A fine thread would disappear beside this rhizome."""
    length = max(arc_table(dense)[-1], 1e-6)
    ds = [length * k / (rings - 1) for k in range(rings)]
    radii = []
    for d in ds:
        taper = 1.0 - 0.16 * (d / length)
        swell = 1.0 + 0.05 * math.sin((d / length) * math.pi * 2.0)
        radii.append(radius * taper * swell)
    mesh, _ring_of = tube_mesh(name, dense, ds, radii, sides, 0.90, Vector((1.0, 0.0, 0.0)))
    return mesh


def bristle_mesh(name, dense, node_ds, rhizome_radius, length, count, seed=1):
    """Long bristles standing off the rhizome. One mesh, weighted per internode."""
    import random

    rng = random.Random(int(seed) + 17)
    cum = arc_table(dense)
    end = max(cum[-1], 1e-6)
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    groups = {}
    sides = 4
    index = 0

    def add(co):
        nonlocal index
        bm.verts.new(co)
        current = index
        index += 1
        return current

    made = 0
    guard = 0
    target = max(0, int(count))
    while made < target and guard < target * 6:
        guard += 1
        d = end * (0.06 + 0.88 * ((made + 0.5) / max(1, target)))
        d = min(end * 0.96, max(end * 0.04, d + rng.uniform(-0.004, 0.004)))
        p = point_at(dense, cum, d)
        tangent = tangent_at(dense, cum, d)
        side, normal = frame_at(tangent, Vector((0.0, 0.0, 1.0)))
        ang = rng.uniform(-2.2, 2.2)
        direction = normal * math.cos(ang) + side * math.sin(ang)
        if direction.length < 1e-8:
            continue
        direction.normalize()
        # Up, and out of the cut (negative Y), so the fibers are not buried in the bed.
        if direction.y > 0.05:
            direction.y *= 0.2
        direction.z = abs(direction.z) * 0.35 + 0.72
        if direction.length < 1e-8:
            continue
        direction.normalize()
        base = p + direction * (rhizome_radius * 0.92)
        span = length * rng.uniform(0.82, 1.18)
        bend = tangent * (span * rng.uniform(-0.28, 0.05)) + Vector((0.0, -0.15, 0.35)).normalized() * (span * 0.22)
        mid = base + direction * (span * 0.55) + bend * 0.45
        tip = base + direction * span + bend
        samples = (base, mid, tip)
        rad = max(0.00035, rhizome_radius * 0.055) * rng.uniform(0.8, 1.2)
        ids = []
        rings = []
        for along, rr, center in ((0.0, rad, base), (0.58, rad * 0.55, mid), (0.86, rad * 0.28, mid.lerp(tip, 0.72))):
            axis = (samples[min(2, int(along * 2) + 1)] - center)
            if axis.length < 1e-8:
                axis = tip - base
            axis_n = axis.normalized()
            ortho = axis_n.orthogonal().normalized()
            bit = axis_n.cross(ortho).normalized()
            ring = []
            for k in range(sides):
                a = 2 * math.pi * k / sides
                vid = add(center + ortho * (math.cos(a) * rr) + bit * (math.sin(a) * rr))
                ring.append(vid)
                ids.append(vid)
            rings.append(ring)
        apex = add(tip)
        ids.append(apex)
        bm.verts.ensure_lookup_table()
        for r in range(len(rings) - 1):
            for k in range(sides):
                k2 = (k + 1) % sides
                face = bm.faces.new((bm.verts[rings[r][k]], bm.verts[rings[r][k2]], bm.verts[rings[r + 1][k2]], bm.verts[rings[r + 1][k]]))
                for loop in face.loops:
                    loop[uv].uv = (0.5, 0.2 + 0.5 * r)
        for k in range(sides):
            k2 = (k + 1) % sides
            face = bm.faces.new((bm.verts[rings[-1][k]], bm.verts[rings[-1][k2]], bm.verts[apex]))
            for loop in face.loops:
                loop[uv].uv = (0.5, 0.85)
        cap = bm.faces.new(tuple(bm.verts[v] for v in reversed(rings[0])))
        for loop in cap.loops:
            loop[uv].uv = (0.5, 0.0)
        nseg = max(1, len(node_ds) - 1)
        seg = min(nseg - 1, max(0, bisect.bisect_right(node_ds, d + 1e-7) - 1))
        groups.setdefault("rhizome_%02d" % seg, []).extend(ids)
        made += 1
    if index == 0:
        add(Vector((0.0, 0.0, 0.0)))
        add(Vector((0.0002, 0.0, 0.0)))
        add(Vector((0.0, 0.0002, 0.0)))
        bm.verts.ensure_lookup_table()
        bm.faces.new((bm.verts[0], bm.verts[1], bm.verts[2]))
    return bm_to_mesh(bm, name), groups
