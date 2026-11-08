"""Oval blades on petioles, plus rhizome and root tubes, skinned from Authoring curves."""

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


def _oval_env(u):
    """Broad oval along the blade. Narrow only at the petiole, blunt at the tip."""
    neck = 0.42 + 0.58 * smoothstep(u / 0.16)
    x = (u - 0.42) / 0.62
    body = math.sqrt(max(0.20, 1.0 - x * x))
    if u < 0.16:
        return neck * body
    return body


def _blade_frame(tangent, twist):
    """Width runs across the sand. The oval face points up, not edge-on."""
    up = Vector((0.0, 0.0, 1.0))
    side = tangent.cross(up)
    if side.length < 1e-6:
        side = Vector((1.0, 0.0, 0.0))
    side.normalize()
    normal = side.cross(tangent).normalized()
    if normal.z < 0.0:
        side.negate()
        normal.negate()
    if twist:
        c, s = math.cos(twist), math.sin(twist)
        rolled_s = side * c + normal * s
        rolled_n = normal * c - side * s
        if rolled_n.z > 0.15:
            side, normal = rolled_s.normalized(), rolled_n.normalized()
    return side, normal


def leaf_mesh(name, dense, width, thickness, vein_count, side_hint, twist, groove=0.0, crown=0.0, body_rings=8):
    """Round petiole, then a spoon-shaped oval blade. Cross veins live in the image."""
    del side_hint, groove, body_rings
    if int(vein_count) >= 8:
        raise RuntimeError("cross-vein pairs must stay under eight")
    from .config import CONFIG

    cum = arc_table(dense)
    length = max(cum[-1], 1e-6)
    petiole_end = length * float(CONFIG.get("petiole_frac", 0.26))
    petiole_r = float(CONFIG.get("petiole_radius_m", 0.00055))
    spoon = float(crown) if crown else float(CONFIG.get("spoon_cup_m", 0.0014))
    stations = []
    for k in range(4):
        d = petiole_end * k / 3.0
        radius = petiole_r * (1.25 - 0.22 * k / 3.0)
        stations.append((d, radius, radius, 0.0))
    for u in (0.07, 0.18, 0.32, 0.46, 0.60, 0.72, 0.84, 0.93):
        env = _oval_env(u)
        hw = max(petiole_r * 1.15, 0.5 * width * env)
        ht = max(thickness * 0.70, 0.5 * thickness * (0.65 + 0.35 * env))
        cup = spoon * (env ** 2)
        stations.append((petiole_end + (length - petiole_end) * u, hw, ht, cup))

    around = 14
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    rings, ring_uv = [], []
    for d, hw, ht, cup in stations:
        d = min(d, length)
        point = point_at(dense, cum, d)
        side, normal = _blade_frame(tangent_at(dense, cum, d), twist * d / length)
        ring, coords = [], []
        for k in range(around):
            ang = 2.0 * math.pi * k / around
            x, y = math.cos(ang), math.sin(ang)
            lift = cup * (1.0 - x * x)
            ring.append(bm.verts.new(point + side * (x * hw) + normal * (y * ht + lift)))
            coords.append((0.5 + 0.5 * x, d / length))
        rings.append(ring)
        ring_uv.append(coords)

    for i in range(len(rings) - 1):
        for j in range(around):
            j2 = (j + 1) % around
            face = bm.faces.new((rings[i][j], rings[i][j2], rings[i + 1][j2], rings[i + 1][j]))
            for loop, coord in zip(face.loops, (ring_uv[i][j], ring_uv[i][j2], ring_uv[i + 1][j2], ring_uv[i + 1][j])):
                loop[uv].uv = coord
    base = bm.faces.new(tuple(reversed(rings[0])))
    for loop in base.loops:
        loop[uv].uv = ring_uv[0][rings[0].index(loop.vert)]
    apex = bm.verts.new(point_at(dense, cum, length))
    last = rings[-1]
    for j in range(around):
        j2 = (j + 1) % around
        face = bm.faces.new((last[j], last[j2], apex))
        for loop, coord in zip(face.loops, (ring_uv[-1][j], ring_uv[-1][j2], (0.5, 1.0))):
            loop[uv].uv = coord
    return bm_to_mesh(bm, name)


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
