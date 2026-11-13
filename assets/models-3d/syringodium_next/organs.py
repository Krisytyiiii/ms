"""Larger needle leaf, trident tip, pale ivory rhizome, clean black scars."""

import math

from mathutils import Vector

from syringodium_next.config import (
    LEAF_THICK_M,
    LEAF_WIDTH_M,
    RHIZOME_RADIUS_M,
    ROOT_RADIUS_M,
    STEM_RADIUS_M,
)
from syringodium_next.meshutil import add_tube, finish_mesh, new_bmesh


def leaf_object(base, length, yaw, lean, name, material, collection, bone, arm):
    """Round leaf. Front and side both see a noodle, and the tip comes to a point."""
    base = Vector(base)
    direction = Vector((math.sin(yaw) * math.sin(lean), 0.0, math.cos(lean))).normalized()
    radius = LEAF_WIDTH_M * 0.5
    # Display: the point occupies the last couple of centimetres.
    point = min(0.35, 0.02 / max(length, 0.02))
    bm = new_bmesh()
    add_tube(
        bm,
        base,
        base + direction * (length * (1.0 - point)),
        radius,
        radius,
        sides=8,
        steps=6,
        flat=1.0,
    )
    add_tube(
        bm,
        base + direction * (length * (1.0 - point)),
        base + direction * length,
        radius,
        radius * 0.02,
        sides=8,
        steps=4,
        flat=1.0,
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
