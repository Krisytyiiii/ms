"""Packed images. Leaf colour runs along the noodle. Sand is warm and pale."""

import bpy
import numpy as np

from .util import sock, srgb

LEAF = {"base": (0.15, 0.46, 0.22), "tip": (0.52, 0.66, 0.30), "pale": (0.40, 0.56, 0.28)}
YOUNG = {"base": (0.36, 0.64, 0.30), "tip": (0.62, 0.76, 0.40), "pale": (0.55, 0.72, 0.40)}


def _image(name, w, h):
    img = bpy.data.images.get(name)
    if img is not None and tuple(img.size) != (w, h):
        bpy.data.images.remove(img)
        img = None
    if img is None:
        img = bpy.data.images.new(name, w, h, alpha=False, float_buffer=False)
    img.colorspace_settings.name = "sRGB"
    return img


def _fill(img, rgb):
    h, w, _ = rgb.shape
    rgba = np.ones((h, w, 4), dtype=np.float32)
    rgba[..., :3] = np.clip(rgb, 0.0, 1.0)
    img.pixels.foreach_set(rgba.ravel())
    img.update()
    img.pack()


def leaf_image(name, pal, w=64, h=256):
    """Colour changes along the leaf only. No strap vein, no dark edge."""
    v = np.linspace(0.0, 1.0, h)[:, None]
    base, tip, pale = (np.array(pal[k]) for k in ("base", "tip", "pale"))
    t = np.clip(v / 0.14, 0.0, 1.0)
    s = (t * t * (3 - 2 * t))[..., None]
    col = pale * (1 - s) + base * s
    tt = np.clip((v - 0.72) / 0.28, 0.0, 1.0)[..., None]
    col = col * (1 - tt) + tip * tt
    col = np.broadcast_to(col, (h, w, 3)).copy()
    img = _image(name, w, h)
    _fill(img, col)
    img["cr_style"] = "noodle"
    return img


def _soft_grain(rng, n, cells):
    cells = max(4, int(cells))
    coarse = rng.normal(0.0, 1.0, (cells, cells))
    ys = np.linspace(0, cells - 1, n)
    xs = np.linspace(0, cells - 1, n)
    y0 = np.floor(ys).astype(int)
    x0 = np.floor(xs).astype(int)
    y1 = np.clip(y0 + 1, 0, cells - 1)
    x1 = np.clip(x0 + 1, 0, cells - 1)
    fy = (ys - y0)[:, None]
    fx = (xs - x0)[None, :]
    y0 = y0[:, None]
    x0 = x0[None, :]
    y1 = y1[:, None]
    x1 = x1[None, :]
    return (
        coarse[y0, x0] * (1 - fy) * (1 - fx)
        + coarse[y0, x1] * (1 - fy) * fx
        + coarse[y1, x0] * fy * (1 - fx)
        + coarse[y1, x1] * fy * fx
    )


def sand_image(name="CrSandGrain", n=256, seed=5):
    """Warm pale top. The cut face is the same sand, a little deeper."""
    rng = np.random.default_rng(seed)
    u = np.linspace(0.0, 1.0, n, endpoint=False)[None, :]
    v = np.linspace(0.0, 1.0, n, endpoint=False)[:, None]
    grain = _soft_grain(rng, n, n // 20)
    broad = _soft_grain(rng, n, n // 40)
    pale = np.array((0.91, 0.82, 0.66))
    crest = np.array((0.96, 0.89, 0.74))
    deep = np.array((0.74, 0.60, 0.42))
    face = np.array((0.80, 0.66, 0.46))
    mix = 0.5 + 0.5 * broad
    top = pale * (1 - mix[..., None]) + crest * mix[..., None]
    top = top * (0.97 + 0.05 * grain[..., None])
    wall = face * (0.94 + 0.08 * grain[..., None])
    wall = wall * (1 - (1 - v) * 0.18) + deep * ((1 - v) * 0.18)
    col = np.where((v >= 0.55)[..., None], top, wall)
    img = _image(name, n, n)
    _fill(img, col)
    img["cr_grain"] = 3
    return img


def _principled(name, color, rough, spec=0.22):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.use_backface_culling = False
    mat.diffuse_color = srgb(*color)
    bsdf = next(node for node in mat.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    sock(bsdf, "Base Color").default_value = srgb(*color)
    sock(bsdf, "Roughness").default_value = rough
    sock(bsdf, "Metallic").default_value = 0.0
    try:
        sock(bsdf, "Specular IOR Level").default_value = spec
    except KeyError:
        pass
    return mat


def _attach(mat, img):
    nodes = mat.node_tree.nodes
    bsdf = next(node for node in nodes if node.type == "BSDF_PRINCIPLED")
    tex = next((node for node in nodes if node.type == "TEX_IMAGE"), None) or nodes.new("ShaderNodeTexImage")
    tex.image = img
    mat.node_tree.links.new(tex.outputs["Color"], sock(bsdf, "Base Color"))
    return mat


def ensure_materials(vein_count=0):
    del vein_count
    leaf = leaf_image("CrLeafVeins", LEAF)
    young = leaf_image("CrYoungVeins", YOUNG)
    sand = sand_image()
    return {
        "leaf": _attach(_principled("CrLeaf", LEAF["base"], 0.38, 0.34), leaf),
        "young": _attach(_principled("CrLeafYoung", YOUNG["base"], 0.40, 0.30), young),
        "rhizome": _principled("CrRhizome", (0.74, 0.62, 0.42), 0.52, 0.14),
        "root": _principled("CrRoot", (0.86, 0.78, 0.60), 0.58, 0.10),
        "stem": _principled("CrStem", (0.46, 0.58, 0.30), 0.48, 0.16),
        "sheath": _principled("CrSheath", (0.70, 0.74, 0.46), 0.50, 0.14),
        "scar": _principled("CrScar", (0.40, 0.46, 0.26), 0.50, 0.12),
        "sand": _attach(_principled("CrSand", (0.91, 0.82, 0.66), 0.88, 0.06), sand),
    }
