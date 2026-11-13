"""Larger needle leaf, trident tip, pale ivory rhizome, clean black scars."""

import math

from mathutils import Vector

from uninervis_next.config import (
    LEAF_THICK_M,
    LEAF_WIDTH_M,
    RHIZOME_RADIUS_M,
    ROOT_RADIUS_M,
    STEM_RADIUS_M,
)
from uninervis_next.meshutil import add_tube, finish_mesh, new_bmesh


def _tip_start(length):
    # Display: the three points occupy about 1.4 cm. The record gives no tip length.
    return max(0.80, 1.0 - (0.014 / max(length, 0.02)))


def _half_width(t, length):
    half = LEAF_WIDTH_M * 0.5
    start = _tip_start(length)
    if t < start:
        return half
    u = (t - start) / (1.0 - start)
    # Side point, a deep notch, then a longer center point.
    if u < 0.22:
        return half
    if u < 0.34:
        return half * (1.0 + 0.7 * ((u - 0.22) / 0.12))
    if u < 0.50:
        return half * (1.7 - 1.52 * ((u - 0.34) / 0.16))
    return max(half * 0.04, half * 0.18 * (1.0 - (u - 0.50) / 0.50))


def _sample_t(length):
    start = _tip_start(length)
    body = [start * i / 12.0 for i in range(13)]
    us = (0.10, 0.22, 0.28, 0.34, 0.42, 0.50, 0.66, 0.82, 0.94, 1.0)
    tip = [start + (1.0 - start) * u for u in us]
    return body + tip


def leaf_object(base, length, yaw, lean, name, material, collection, bone, arm):
    """Wider needle. Front sees the vein and the three-point tip. Side sees the thin edge."""
    base = Vector(base)
    direction = Vector((math.sin(yaw) * math.sin(lean), 0.0, math.cos(lean))).normalized()
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
        row = [
            center + width_axis * (side * half)
            for side in (-1.0, 0.0, 1.0)
        ]
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
            put(
                bm.faces.new((low[r][c], low[r][c + 1], low[r + 1][c + 1], low[r + 1][c])),
                (uv_at(r, c), uv_at(r, c + 1), uv_at(r + 1, c + 1), uv_at(r + 1, c)),
            )
            put(
                bm.faces.new((high[r][c + 1], high[r][c], high[r + 1][c], high[r + 1][c + 1])),
                (uv_at(r, c + 1), uv_at(r, c), uv_at(r + 1, c), uv_at(r + 1, c + 1)),
            )
        put(
            bm.faces.new((low[r][0], low[r + 1][0], high[r + 1][0], high[r][0])),
            (uv_at(r, 0), uv_at(r + 1, 0), uv_at(r + 1, 0), uv_at(r, 0)),
        )
        put(
            bm.faces.new((low[r][2], high[r][2], high[r + 1][2], low[r + 1][2])),
            (uv_at(r, 1), uv_at(r, 1), uv_at(r + 1, 1), uv_at(r + 1, 1)),
        )
    last = rows - 1
    put(
        bm.faces.new((low[0][0], high[0][0], high[0][1], low[0][1])),
        (uv_at(0, 0), uv_at(0, 0), uv_at(0, 0.5), uv_at(0, 0.5)),
    )
    put(
        bm.faces.new((low[0][1], high[0][1], high[0][2], low[0][2])),
        (uv_at(0, 0.5), uv_at(0, 0.5), uv_at(0, 1), uv_at(0, 1)),
    )
    put(
        bm.faces.new((low[last][1], low[last][0], high[last][0], high[last][1])),
        (uv_at(last, 0.5), uv_at(last, 0), uv_at(last, 0), uv_at(last, 0.5)),
    )
    put(
        bm.faces.new((low[last][2], low[last][1], high[last][1], high[last][2])),
        (uv_at(last, 1), uv_at(last, 0.5), uv_at(last, 0.5), uv_at(last, 1)),
    )
    return finish_mesh(bm, name, material, collection, bone, arm)


def stem_object(head, tail, name, material, collection, bone, arm):
    bm = new_bmesh()
    add_tube(bm, head, tail, STEM_RADIUS_M, STEM_RADIUS_M * 0.9, sides=6, steps=3, flat=0.9)
    return finish_mesh(bm, name, material, collection, bone, arm)


def sheath_object(origin, stem_h, name, material, collection, bone, arm):
    """Short pale cuff. The record does not describe a sheath, so this is display only."""
    origin = Vector(origin)
    z0 = stem_h * 0.62
    z1 = stem_h * 0.98
    bm = new_bmesh()
    add_tube(
        bm,
        origin + Vector((0.0, 0.0, z0)),
        origin + Vector((0.0, 0.0, z1)),
        STEM_RADIUS_M * 1.7,
        STEM_RADIUS_M * 2.1,
        sides=6,
        steps=2,
        flat=0.72,
    )
    return finish_mesh(bm, name, material, collection, bone, arm)


def scar_object(origin, axis, name, material, collection, bone, arm):
    """Clean black bands on the pale rhizome. The record does not give a count."""
    origin = Vector(origin)
    axis = Vector(axis).normalized()
    bm = new_bmesh()
    radius = RHIZOME_RADIUS_M * 1.45
    for shift in (0.0, 0.0024):
        center = origin + axis * shift
        add_tube(
            bm,
            center - axis * 0.00028,
            center + axis * 0.00028,
            radius,
            radius,
            sides=8,
            steps=1,
            flat=1.0,
        )
    return finish_mesh(bm, name, material, collection, bone, arm)


def rhizome_object(head, tail, name, material, collection, bone, arm):
    bm = new_bmesh()
    add_tube(
        bm, head, tail,
        RHIZOME_RADIUS_M, RHIZOME_RADIUS_M * 0.96,
        sides=7, steps=4, flat=0.82,
    )
    return finish_mesh(bm, name, material, collection, bone, arm)


def root_object(head, tail, r0, r1, name, material, collection, bone, arm):
    bm = new_bmesh()
    add_tube(bm, head, tail, r0, r1, sides=5, steps=4, flat=1.0)
    return finish_mesh(bm, name, material, collection, bone, arm)
