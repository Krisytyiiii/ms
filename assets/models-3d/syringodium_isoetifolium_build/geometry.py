"""Round leaves and fine tubes. A leaf is a circle in every cross-section."""

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


def _leaf_radius(d, length, radius):
    """Same radius all the way around. The last fifth closes to a point."""
    wave = 1.0 + 0.028 * math.sin(2.0 * math.pi * d / max(length, 1e-6))
    tip0 = 0.90 * length
    if d <= tip0:
        base = 0.90 + 0.10 * smoothstep(d / max(1e-6, 0.07 * length))
        return radius * base * wave
    u = (d - tip0) / max(1e-6, length - tip0)
    return radius * math.cos(u * math.pi * 0.5) * wave


def leaf_mesh(name, dense, diameter, side_hint, twist=0.0, body_rings=10, sides=16):
    """Closed noodle. The cross-section is a circle, and the tip is a point."""
    cum = arc_table(dense)
    length = max(cum[-1], 1e-6)
    radius = 0.5 * float(diameter)
    sides = max(10, int(sides))
    tip0 = 0.90 * length
    stations = []
    rings_n = max(4, int(body_rings))
    for k in range(rings_n):
        d = tip0 * k / (rings_n - 1)
        stations.append(d)
    for k in range(1, 7):
        stations.append(tip0 + (length * 0.985 - tip0) * k / 6.0)

    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    rings, ring_d = [], []
    for d in stations:
        rad = max(radius * 0.045, _leaf_radius(d, length, radius))
        p = point_at(dense, cum, d)
        side, normal = frame_at(tangent_at(dense, cum, d), side_hint, twist * d / length)
        ring = []
        for k in range(sides):
            a = 2 * math.pi * k / sides
            ring.append(bm.verts.new(p + side * (math.cos(a) * rad) + normal * (math.sin(a) * rad)))
        rings.append(ring)
        ring_d.append(d)

    for i in range(len(rings) - 1):
        v0, v1 = ring_d[i] / length, ring_d[i + 1] / length
        for k in range(sides):
            k2 = (k + 1) % sides
            face = bm.faces.new((rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]))
            for loop, coord in zip(
                face.loops,
                ((k / sides, v0), ((k + 1) / sides, v0), ((k + 1) / sides, v1), (k / sides, v1)),
            ):
                loop[uv].uv = coord
    base = bm.faces.new(tuple(reversed(rings[0])))
    for loop in base.loops:
        loop[uv].uv = (0.5, 0.0)
    apex = bm.verts.new(point_at(dense, cum, length))
    last = rings[-1]
    vend = ring_d[-1] / length
    for k in range(sides):
        k2 = (k + 1) % sides
        face = bm.faces.new((last[k], last[k2], apex))
        for loop, coord in zip(face.loops, ((k / sides, vend), ((k + 1) / sides, vend), (0.5, 1.0))):
            loop[uv].uv = coord
    return bm_to_mesh(bm, name)


def tube_mesh(name, dense, ds, radii, sides, oval, side_hint):
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


def rhizome_mesh(name, dense, node_ds, radius, oval, step=0.007, sides=10):
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
            rr *= 1.0 + 0.10 * math.exp(-((d - nd) ** 2) / (2 * 0.0032 ** 2))
        rr *= 0.72 + 0.28 * smoothstep(d / 0.005)
        rr *= 0.55 + 0.45 * smoothstep((end - d) / 0.012)
        radii.append(rr)
    mesh, ring_of = tube_mesh(name, dense, ds, radii, sides, oval, Vector((0.0, 0.0, 1.0)))
    nseg = max(1, len(node_ds) - 1)
    groups = {}
    for vid, ring in enumerate(ring_of):
        seg = min(nseg - 1, max(0, bisect.bisect_right(node_ds, ds[ring] + 1e-7) - 1))
        groups.setdefault("rhizome_%02d" % seg, []).append(vid)
    return mesh, groups


def root_mesh(name, dense, radius, rings=5, sides=6):
    """A fine root. It tapers. It is not a cord and it has no bristles."""
    length = arc_table(dense)[-1]
    ds = [length * k / (rings - 1) for k in range(rings)]
    radii = [radius * (1.0 - 0.72 * (d / max(length, 1e-6))) for d in ds]
    mesh, _ring_of = tube_mesh(name, dense, ds, radii, sides, 1.0, Vector((1.0, 0.0, 0.0)))
    return mesh
