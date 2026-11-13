"""Serrated strap, triangular sheath, open scars, rhizome, and fine roots."""

import math

from mathutils import Vector

from thalassia_next.config import (
    LEAF_THICK_M,
    LEAF_WIDTH_M,
    RHIZOME_RADIUS_M,
    ROOT_RADIUS_M,
    STEM_RADIUS_M,
)
from thalassia_next.meshutil import add_prism, add_tube, finish_mesh, new_bmesh

def _half_width(t, length):
    half = LEAF_WIDTH_M * 0.5
    if t < 0.94:
        return half
    u = (t - 0.94) / 0.06
    return half * math.sqrt(max(0.08, 1.0 - u * u))


def _sample_t(length):
    return [i / 18.0 for i in range(19)]


def leaf_object(base, length, yaw, lean, name, material, collection, bone, arm):
    """Flat strap. Front sees the face and the serrated tip. Side sees the thin edge."""
    base = Vector(base)
    direction = Vector((math.sin(yaw) * math.sin(lean), 0.0, math.cos(lean)))
    direction.normalize()
    front = Vector((0.0, 1.0, 0.0))
    width_axis = front.cross(direction)
    if width_axis.length < 1e-6:
        width_axis = Vector((1.0, 0.0, 0.0))
    width_axis.normalize()
    normal = width_axis.cross(direction).normalized()
    ts = _sample_t(length)
    bm = new_bmesh()
    layers = []
    for t in ts:
        half = _half_width(t, length)
        center = base + direction * (length * t)
        # Display sickle. The record says the ribbon is curved and gives no arc.
        center = center + width_axis * (math.sin(t * math.pi) * 0.045)
        # Display bow, a couple of millimetres, so the strap is not a flat card.
        center = center + normal * (math.sin(t * math.pi) * 0.0016)
        ridge = normal * (LEAF_THICK_M * 0.35)
        row = []
        for side, lift in ((-1.0, 0.0), (0.0, 1.0), (1.0, 0.0)):
            point = center + width_axis * (side * half) + ridge * lift
            row.append(point)
        layers.append(row)
    thick = normal * LEAF_THICK_M
    low = [[bm.verts.new(p) for p in row] for row in layers]
    high = [[bm.verts.new(p + thick) for p in row] for row in layers]
    uv = bm.loops.layers.uv.new("UVMap")

    def put(face, pairs):
        for loop, pair in zip(face.loops, pairs):
            loop[uv].uv = pair

    def uv_at(row, col):
        return (col / 2.0, ts[row])

    rows = len(ts)
    for r in range(rows - 1):
        for c in range(2):
            put(bm.faces.new((low[r][c], low[r][c + 1], low[r + 1][c + 1], low[r + 1][c])),
                (uv_at(r, c), uv_at(r, c + 1), uv_at(r + 1, c + 1), uv_at(r + 1, c)))
            put(bm.faces.new((high[r][c + 1], high[r][c], high[r + 1][c], high[r + 1][c + 1])),
                (uv_at(r, c + 1), uv_at(r, c), uv_at(r + 1, c), uv_at(r + 1, c + 1)))
        put(bm.faces.new((low[r][0], low[r + 1][0], high[r + 1][0], high[r][0])),
            (uv_at(r, 0), uv_at(r + 1, 0), uv_at(r + 1, 0), uv_at(r, 0)))
        put(bm.faces.new((low[r][2], high[r][2], high[r + 1][2], low[r + 1][2])),
            (uv_at(r, 1), uv_at(r, 1), uv_at(r + 1, 1), uv_at(r + 1, 1)))
    put(bm.faces.new((low[0][0], high[0][0], high[0][1], low[0][1])),
        (uv_at(0, 0), uv_at(0, 0), uv_at(0, 0.5), uv_at(0, 0.5)))
    put(bm.faces.new((low[0][1], high[0][1], high[0][2], low[0][2])),
        (uv_at(0, 0.5), uv_at(0, 0.5), uv_at(0, 1), uv_at(0, 1)))
    last = rows - 1
    put(bm.faces.new((low[last][1], low[last][0], high[last][0], high[last][1])),
        (uv_at(last, 0.5), uv_at(last, 0), uv_at(last, 0), uv_at(last, 0.5)))
    put(bm.faces.new((low[last][2], low[last][1], high[last][1], high[last][2])),
        (uv_at(last, 1), uv_at(last, 0.5), uv_at(last, 0.5), uv_at(last, 1)))
    return finish_mesh(bm, name, material, collection, bone, arm)


def stem_object(head, tail, name, material, collection, bone, arm):
    bm = new_bmesh()
    add_tube(bm, head, tail, STEM_RADIUS_M, STEM_RADIUS_M * 0.92, sides=8, steps=5, flat=0.92)
    return finish_mesh(bm, name, material, collection, bone, arm)


def sheath_object(origin, stem_h, name, material, collection, bone, arm):
    """Broad triangle on the front of the stem. It does not wrap into a ring."""
    origin = Vector(origin)
    z0 = stem_h * 0.55
    z1 = stem_h * 1.02
    mouth = SHEATH_MOUTH_M * 0.5
    y = -STEM_RADIUS_M - 0.0004
    apex = origin + Vector((0.0, y, z0))
    left = origin + Vector((-mouth, y - 0.0003, z1))
    right = origin + Vector((mouth, y - 0.0003, z1))
    # Display thickness so a side view stays a thin wedge.
    offset = Vector((0.0, -0.0013, 0.0))
    bm = new_bmesh()
    add_prism(bm, apex, left, right, offset)
    clasp = stem_h * 0.78
    add_prism(
        bm,
        origin + Vector((-0.0024, -0.0002, z0 + 0.002)),
        origin + Vector((-0.0034, 0.0016, clasp)),
        origin + Vector((-0.0010, 0.0016, z1)),
        Vector((-0.0006, 0.0, 0.0)),
    )
    add_prism(
        bm,
        origin + Vector((0.0024, -0.0002, z0 + 0.002)),
        origin + Vector((0.0010, 0.0016, z1)),
        origin + Vector((0.0034, 0.0016, clasp)),
        Vector((0.0006, 0.0, 0.0)),
    )
    return finish_mesh(bm, name, material, collection, bone, arm)


def scar_object(origin, axis, name, material, collection, bone, arm):
    """A scar on the thick rhizome, between shoots. Not a count from the record."""
    origin = Vector(origin)
    axis = Vector(axis)
    if axis.length < 1e-6:
        axis = Vector((1.0, 0.0, 0.0))
    axis.normalize()
    bm = new_bmesh()
    radius = RHIZOME_RADIUS_M * 1.12
    add_tube(
        bm,
        origin - axis * 0.0014,
        origin + axis * 0.0014,
        radius,
        radius,
        sides=8,
        steps=1,
        flat=0.85,
    )
    return finish_mesh(bm, name, material, collection, bone, arm)


def rhizome_object(head, tail, name, material, collection, bone, arm):
    bm = new_bmesh()
    add_tube(
        bm, head, tail,
        RHIZOME_RADIUS_M, RHIZOME_RADIUS_M * 0.96,
        sides=7, steps=4, flat=0.70,
    )
    return finish_mesh(bm, name, material, collection, bone, arm)


def root_object(head, tail, r0, r1, name, material, collection, bone, arm):
    bm = new_bmesh()
    add_tube(bm, head, tail, r0, r1, sides=5, steps=4, flat=1.0)
    return finish_mesh(bm, name, material, collection, bone, arm)
