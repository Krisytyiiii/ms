"""Paired small ovals, smooth margins, and a wedge sheath. No upright fan."""

import math

from mathutils import Vector

from ovalis_next.config import (
    LEAF_THICK_M,
    LEAF_WIDTH_M,
    RHIZOME_RADIUS_M,
    STEM_RADIUS_M,
)
from ovalis_next.meshutil import add_prism, add_tube, finish_mesh, new_bmesh


def leaf_object(base, length, yaw, lean, name, material, collection, bone, arm):
    """Smooth oval. The margin has no teeth. Front view shows the face."""
    base = Vector(base)
    direction = Vector((math.sin(yaw) * math.sin(lean), 0.0, math.cos(lean))).normalized()
    front = Vector((0.0, 1.0, 0.0))
    width_axis = front.cross(direction)
    if width_axis.length < 1e-6:
        width_axis = Vector((1.0, 0.0, 0.0))
    width_axis.normalize()
    normal = width_axis.cross(direction).normalized()
    half_w = LEAF_WIDTH_M * 0.5
    along, across = 14, 8
    bm = new_bmesh()
    layers = []
    ts = []
    for i in range(along):
        t = i / (along - 1)
        ts.append(t)
        # Ellipse: zero at both ends, widest in the middle. Smooth margin.
        half = half_w * max(0.12, math.sin(math.pi * t))
        center = base + direction * (length * t)
        row = [center + width_axis * (((c / (across - 1)) * 2.0 - 1.0) * half) for c in range(across)]
        layers.append(row)
    thick = normal * LEAF_THICK_M
    low = [[bm.verts.new(p) for p in row] for row in layers]
    high = [[bm.verts.new(p + thick) for p in row] for row in layers]
    uv = bm.loops.layers.uv.new("UVMap")

    def put(face, pairs):
        for loop, pair in zip(face.loops, pairs):
            loop[uv].uv = pair

    def uv_at(row, col):
        return (col / (across - 1), ts[row])

    for r in range(along - 1):
        for c in range(across - 1):
            put(
                bm.faces.new((low[r][c], low[r][c + 1], low[r + 1][c + 1], low[r + 1][c])),
                (uv_at(r, c), uv_at(r, c + 1), uv_at(r + 1, c + 1), uv_at(r + 1, c)),
            )
            put(
                bm.faces.new((high[r][c + 1], high[r][c], high[r + 1][c], high[r + 1][c + 1])),
                (uv_at(r, c + 1), uv_at(r, c), uv_at(r + 1, c), uv_at(r + 1, c + 1)),
            )
    return finish_mesh(bm, name, material, collection, bone, arm)


def stem_object(head, tail, name, material, collection, bone, arm):
    bm = new_bmesh()
    add_tube(bm, head, tail, STEM_RADIUS_M, STEM_RADIUS_M, sides=6, steps=2, flat=1.0)
    return finish_mesh(bm, name, material, collection, bone, arm)


def sheath_object(origin, stem_h, name, material, collection, bone, arm):
    """Wedge in front view. Display size. The record gives no sheath measurement."""
    origin = Vector(origin)
    z0 = stem_h * 0.15
    z1 = stem_h * 0.95
    mouth = 0.0056  # display: wider than the minor wedge, matching the larger pair
    y = -STEM_RADIUS_M - 0.0002
    apex = origin + Vector((0.0, y, z0))
    left = origin + Vector((-mouth, y, z1))
    right = origin + Vector((mouth, y, z1))
    bm = new_bmesh()
    add_prism(bm, apex, left, right, Vector((0.0, -0.0006, 0.0)))
    return finish_mesh(bm, name, material, collection, bone, arm)


def rhizome_object(head, tail, name, material, collection, bone, arm):
    bm = new_bmesh()
    add_tube(bm, head, tail, RHIZOME_RADIUS_M, RHIZOME_RADIUS_M * 0.94, sides=6, steps=3, flat=0.8)
    return finish_mesh(bm, name, material, collection, bone, arm)


def root_object(head, tail, r0, r1, name, material, collection, bone, arm):
    bm = new_bmesh()
    add_tube(bm, head, tail, r0, r1, sides=5, steps=3, flat=1.0)
    return finish_mesh(bm, name, material, collection, bone, arm)
