"""Small mesh helpers. Object scale stays 1."""

import math

import bmesh
import bpy
from mathutils import Vector


def new_bmesh():
    return bmesh.new()


def finish_mesh(bm, name, material, collection, bone_name=None, armature=None, normals="recalc"):
    if normals == "up":
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        if sum(face.normal.z for face in bm.faces) < 0.0:
            bmesh.ops.reverse_faces(bm, faces=list(bm.faces))
    else:
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    for poly in mesh.polygons:
        poly.use_smooth = True
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    obj.scale = (1.0, 1.0, 1.0)
    if material is not None:
        obj.data.materials.append(material)
    if bone_name and armature is not None:
        group = obj.vertex_groups.new(name=bone_name)
        group.add(list(range(len(mesh.vertices))), 1.0, "REPLACE")
        mod = obj.modifiers.new("Armature", "ARMATURE")
        mod.object = armature
        obj.parent = armature
        obj.matrix_parent_inverse = armature.matrix_world.inverted()
    return obj


def add_tube(bm, head, tail, r0, r1, sides=7, steps=4, flat=1.0):
    head = Vector(head)
    tail = Vector(tail)
    direction = tail - head
    length = direction.length
    if length < 1e-6:
        return
    y_axis = direction / length
    up = Vector((0.0, 0.0, 1.0))
    if abs(y_axis.dot(up)) > 0.92:
        up = Vector((0.0, 1.0, 0.0))
    x_axis = y_axis.cross(up).normalized()
    z_axis = x_axis.cross(y_axis).normalized()
    rings = []
    for step in range(steps + 1):
        t = step / steps
        center = head.lerp(tail, t)
        radius = r0 + (r1 - r0) * t
        ring = []
        for i in range(sides):
            ang = 2.0 * math.pi * i / sides
            radial = x_axis * math.cos(ang) + z_axis * (math.sin(ang) * flat)
            ring.append(bm.verts.new(center + radial * radius))
        rings.append(ring)
    for step in range(steps):
        for i in range(sides):
            j = (i + 1) % sides
            bm.faces.new((rings[step][i], rings[step][j], rings[step + 1][j], rings[step + 1][i]))
    bm.faces.new(tuple(reversed(rings[0])))
    bm.faces.new(tuple(rings[-1]))


def add_prism(bm, a, b, c, offset):
    offset = Vector(offset)
    verts = [bm.verts.new(p) for p in (a, b, c, Vector(a) + offset, Vector(b) + offset, Vector(c) + offset)]
    bm.faces.new((verts[0], verts[1], verts[2]))
    bm.faces.new((verts[5], verts[4], verts[3]))
    bm.faces.new((verts[0], verts[3], verts[4], verts[1]))
    bm.faces.new((verts[1], verts[4], verts[5], verts[2]))
    bm.faces.new((verts[2], verts[5], verts[3], verts[0]))
