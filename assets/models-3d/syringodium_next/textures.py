"""Materials. Colors are a display choice; the record gives no palette."""

import math

import bpy

from syringodium_next.config import srgb_to_linear

# Display colors, sRGB 0–1. Kept dark enough that a sun does not turn the strap white.
# Display colors. The rhizome is pale and the scars are black, as the record says.
LEAF = (0.10, 0.34, 0.14)
LEAF_YOUNG = (0.28, 0.48, 0.20)
VEIN = (0.01, 0.02, 0.01)
SHEATH = (0.72, 0.70, 0.52)
SCAR = (0.03, 0.03, 0.025)
STEM = (0.55, 0.58, 0.36)
RHIZOME = (0.93, 0.88, 0.74)
ROOT = (0.78, 0.70, 0.52)
SAND = (0.82, 0.70, 0.48)


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
        base = tuple(min(1.0, c + 0.08) for c in top)
        for y in range(h):
            v = y / (h - 1)
            for x in range(w):
                u = x / (w - 1)
                rgb = [base[i] * (1.0 - v) + top[i] * v for i in range(3)]
                # One central vein, into the middle point. It does not split.
                if abs(u - 0.5) < 0.07:
                    rgb = list(VEIN)
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
    leaf_img = _image("SiLeafTex", 64, 512, _leaf_paint(False))
    young_img = _image("SiYoungTex", 64, 512, _leaf_paint(True))
    sand_img = _image("SiSandGrain", 256, 256, _sand_paint)
    return {
        "leaf": _principled("SiLeaf", LEAF, 0.62, None, double=True),
        "young": _principled("SiLeafYoung", LEAF_YOUNG, 0.58, None, double=True),
        "sheath": _principled("SiSheath", SHEATH, 0.62),
        "scar": _principled("SiScar", SCAR, 0.7),
        "stem": _principled("SiStem", STEM, 0.6),
        "rhizome": _principled("SiRhizome", RHIZOME, 0.72),
        "root": _principled("SiRoot", ROOT, 0.68),
        "sand": _principled("SiSand", SAND, 0.94, sand_img, double=True),
    }
