"""Solid strap leaves and smooth tubes. Veins are not cut into the mesh."""

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


def strap_profile():
    """Flat front, flat back, and a two-point rounded edge. No teeth."""
    pts = [("front", x, 1.0) for x in (-0.88, -0.44, 0.0, 0.44, 0.88)]
    pts += [("edge", 1.0, 0.35), ("edge", 1.0, -0.35)]
    pts += [("back", x, -1.0) for x in (0.88, 0.44, 0.0, -0.44, -0.88)]
    pts += [("edge", -1.0, -0.35), ("edge", -1.0, 0.35)]
    return pts


def profile_u(role, x):
    """Edge UVs stay in the plain margin of the leaf image. Veins stay on the faces."""
    if role == "edge":
        return 0.04 if x < 0.0 else 0.96
    return 0.50 + 0.42 * x


def leaf_mesh(name, dense, width, thickness, side_hint, twist, shoulder):
    """A solid strap. The front is flat, the side is a thin edge, the tip is a semicircle."""
    cum = arc_table(dense)
    length = max(cum[-1], 1e-6)
    half = 0.5 * width
    tip_start = max(0.5 * length, length - half)
    stations = []
    body = 8
    for k in range(body):
        d = tip_start * k / (body - 1)
        grow = smoothstep(d / max(1e-4, shoulder * length))
        stations.append((d, half * (0.36 + 0.64 * grow), 1.0))
    for deg in (16, 34, 52, 70, 84):
        phi = math.radians(deg)
        stations.append((
            tip_start + (length - tip_start) * math.sin(phi),
            half * math.cos(phi),
            0.22 + 0.78 * math.cos(phi),
        ))

    profile = strap_profile()
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    rings = []
    ring_uv = []
    for d, hw, tf in stations:
        p = point_at(dense, cum, d)
        side, normal = frame_at(tangent_at(dense, cum, d), side_hint, twist * d / length)
        ht = 0.5 * thickness * tf
        ring = []
        coords = []
        for role, x, y in profile:
            ring.append(bm.verts.new(p + side * (x * hw) + normal * (y * ht)))
            coords.append((profile_u(role, x), d / length))
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
    # Flat faces stay flat. Smooth shading would turn the strap into a tube.
    return bm_to_mesh(bm, name, smooth=False)


def tube_mesh(name, dense, ds, radii, sides, oval, side_hint, smooth=True):
    cum = arc_table(dense)
    length = max(cum[-1], 1e-9)
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    rings = []
    ring_of = []
    for i, d in enumerate(ds):
        p = point_at(dense, cum, d)
        side, normal = frame_at(tangent_at(dense, cum, d), side_hint)
        ring = []
        for k in range(sides):
            a = 2 * math.pi * k / sides
            ring.append(bm.verts.new(
                p + side * (math.cos(a) * radii[i] * oval) + normal * (math.sin(a) * radii[i])
            ))
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
    return bm_to_mesh(bm, name, smooth=smooth), ring_of


def rhizome_mesh(name, dense, node_ds, radius, oval, bone0=0, taper_start=True):
    """One smooth tube. Each vertex belongs to the internode it sits on."""
    import bisect

    end = arc_table(dense)[-1]
    marks = list(node_ds) + [end]
    ds = []
    for a, b in zip(marks, marks[1:]):
        count = max(2, round((b - a) / 0.007))
        ds.extend(a + (b - a) * s / count for s in range(count))
    ds.append(end)
    radii = []
    for d in ds:
        rr = radius
        if taper_start:
            rr *= 0.55 + 0.45 * smoothstep(d / 0.008)
        rr *= 0.62 + 0.38 * smoothstep((end - d) / 0.012)
        radii.append(rr)
    mesh, ring_of = tube_mesh(name, dense, ds, radii, 8, oval, Vector((0.0, 0.0, 1.0)), smooth=True)
    nseg = max(1, len(node_ds) - 1)
    groups = {}
    for vid, ring in enumerate(ring_of):
        seg = min(nseg - 1, max(0, bisect.bisect_right(node_ds, ds[ring] + 1e-7) - 1))
        groups.setdefault("rhizome_%02d" % (bone0 + seg), []).append(vid)
    return mesh, groups


def root_mesh(name, dense, radius):
    length = arc_table(dense)[-1]
    rings = 5
    ds = [length * k / (rings - 1) for k in range(rings)]
    radii = [radius * (1.0 - 0.72 * (d / max(length, 1e-6))) for d in ds]
    mesh, _ring = tube_mesh(name, dense, ds, radii, 5, 1.0, Vector((1.0, 0.0, 0.0)), smooth=True)
    return mesh
