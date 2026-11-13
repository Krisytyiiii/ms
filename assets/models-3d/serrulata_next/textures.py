"""Materials. Colors are a display choice; the record gives no palette."""

import math

import bpy

from serrulata_next.config import srgb_to_linear

# Display colors, sRGB 0–1. Kept dark enough that a sun does not turn the strap white.
LEAF = (0.08, 0.28, 0.10)
LEAF_YOUNG = (0.24, 0.42, 0.16)
SHEATH = (0.36, 0.38, 0.14)
SCAR = (0.32, 0.14, 0.05)
STEM = (0.12, 0.24, 0.08)
RHIZOME = (0.48, 0.36, 0.20)
ROOT = (0.55, 0.44, 0.28)
SAND = (0.76, 0.60, 0.36)


def _image(name, w, h, paint):
    img = bpy.data.images.new(name, w, h, alpha=False)
    buf = [0.0] * (w * h * 4)
    paint(buf, w, h)
    img.pixels.foreach_set(buf)
    img.pack()
    return img


def _leaf_paint(young):
    def paint(buf, w, h):
        top = LEAF_YOUNG if young else LEAF
        base = tuple(min(1.0, c + 0.10) for c in top)
        for y in range(h):
            v = y / (h - 1)
            for x in range(w):
                u = x / (w - 1)
                # Display: slightly paler at the base. The record gives no vein count.
                center = math.exp(-((u - 0.5) ** 2) / 0.12) * 0.02
                rgb = tuple(base[i] * (1.0 - v) + top[i] * v + center for i in range(3))
                rgb = srgb_to_linear(rgb)[:3]
                i = (y * w + x) * 4
                buf[i] = rgb[0]
                buf[i + 1] = rgb[1]
                buf[i + 2] = rgb[2]
                buf[i + 3] = 1.0

    return paint


def _sand_paint(buf, w, h):
    for y in range(h):
        for x in range(w):
            fine = math.sin(x * 12.9898 + y * 78.233) * 43758.5453
            fine = (fine - math.floor(fine)) - 0.5
            blot = math.sin(x * 0.11 + y * 0.07) * math.cos(y * 0.09)
            grain = fine * 0.045 + blot * 0.04
            rgb = srgb_to_linear(tuple(min(1.0, max(0.0, SAND[i] + grain)) for i in range(3)))[:3]
            i = (y * w + x) * 4
            buf[i] = rgb[0]
            buf[i + 1] = rgb[1]
            buf[i + 2] = rgb[2]
            buf[i + 3] = 1.0


def _principled(name, color, rough, image=None, double=False):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.use_backface_culling = not double
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value = rough
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.2
    if image is None:
        bsdf.inputs["Base Color"].default_value = srgb_to_linear(color)
    else:
        tex = mat.node_tree.nodes.new("ShaderNodeTexImage")
        tex.image = image
        mat.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    return mat


def make_materials():
    leaf_img = _image("CsLeafTex", 64, 256, _leaf_paint(False))
    young_img = _image("CsYoungTex", 64, 256, _leaf_paint(True))
    sand_img = _image("CsSandGrain", 256, 256, _sand_paint)
    return {
        "leaf": _principled("CsLeaf", LEAF, 0.48, leaf_img, double=True),
        "young": _principled("CsLeafYoung", LEAF_YOUNG, 0.42, young_img, double=True),
        "sheath": _principled("CsSheath", SHEATH, 0.62),
        "scar": _principled("CsScar", SCAR, 0.7),
        "stem": _principled("CsStem", STEM, 0.6),
        "rhizome": _principled("CsRhizome", RHIZOME, 0.72),
        "root": _principled("CsRoot", ROOT, 0.68),
        "sand": _principled("CsSand", SAND, 0.94, sand_img, double=True),
    }
