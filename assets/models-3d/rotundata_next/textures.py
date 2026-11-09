"""Packed images and materials.

Leaf veins are stripes in the image. They fade out before the edge of the
texture, and the strap maps its thin edge into that plain margin.
"""

import bpy
import numpy as np

from .util import sock, srgb

# Locked palette: seagrass green, younger leaves lighter, leaf base paler.
LEAF = {"base": (0.20, 0.46, 0.18), "vein": (0.10, 0.27, 0.10), "tip": (0.34, 0.56, 0.26), "pale": (0.72, 0.76, 0.50)}
YOUNG = {"base": (0.48, 0.70, 0.34), "vein": (0.30, 0.48, 0.22), "tip": (0.60, 0.78, 0.42), "pale": (0.82, 0.86, 0.60)}
REV = 1


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


def leaf_image(name, pal, vein_count, w=256, h=512):
    u = np.linspace(0.0, 1.0, w)[None, :]
    v = np.linspace(0.0, 1.0, h)[:, None]
    lanes = np.linspace(0.34, 0.66, int(vein_count))
    dist = np.min(np.abs(u[..., None] - lanes), axis=-1)
    stripe = np.exp(-(dist ** 2) / (2.0 * 0.0065 ** 2))
    fade_in = np.clip((u - 0.30) / 0.04, 0.0, 1.0)
    fade_out = np.clip((0.70 - u) / 0.04, 0.0, 1.0)
    stripe = stripe * fade_in * fade_out
    base, vein, tip, pale = (np.array(pal[k]) for k in ("base", "vein", "tip", "pale"))
    t = np.clip(v / 0.16, 0.0, 1.0)
    t = t * t * (3.0 - 2.0 * t)
    col = pale * (1.0 - t[..., None]) + base * t[..., None]
    col = np.broadcast_to(col, (h, w, 3)).copy()
    k = stripe[..., None] * 0.22
    col = col * (1.0 - k) + vein * k
    tt = np.clip((v - 0.84) / 0.16, 0.0, 1.0)[..., None] * 0.10
    col = col * (1.0 - tt) + tip * tt
    img = _image(name, w, h)
    _fill(img, col)
    img["cr_veins"] = int(vein_count)
    img["cr_rev"] = REV
    return img


def sand_image(name="CrSandGrain", n=256):
    """Warm pale sand. Soft mottling only."""
    rng = np.random.default_rng(5)
    u = np.linspace(0.0, 1.0, n, endpoint=False)[None, :]
    v = np.linspace(0.0, 1.0, n, endpoint=False)[:, None]
    waves = 0.5 + 0.5 * np.sin((7.0 * u + 2.0 * v) * 2.0 * np.pi)
    cells = n // 24
    coarse = rng.normal(0.0, 1.0, (cells, cells)).astype(np.float32)
    ys = np.linspace(0, cells - 1, n)
    xs = np.linspace(0, cells - 1, n)
    y0 = np.floor(ys).astype(int)
    x0 = np.floor(xs).astype(int)
    y1 = np.clip(y0 + 1, 0, cells - 1)
    x1 = np.clip(x0 + 1, 0, cells - 1)
    fy = (ys - y0)[:, None]
    fx = (xs - x0)[None, :]
    grain = (
        coarse[y0[:, None], x0[None, :]] * (1 - fy) * (1 - fx)
        + coarse[y0[:, None], x1[None, :]] * (1 - fy) * fx
        + coarse[y1[:, None], x0[None, :]] * fy * (1 - fx)
        + coarse[y1[:, None], x1[None, :]] * fy * fx
    )
    dry = np.array((0.90, 0.82, 0.64))
    col = dry * (0.94 + 0.08 * waves[..., None])
    col = col * (0.97 + 0.045 * grain[..., None])
    img = _image(name, n, n)
    _fill(img, col)
    img["cr_rev"] = REV
    return img


def _principled(name, color, rough):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.use_backface_culling = False
    mat.diffuse_color = (*color, 1.0)
    bsdf = next(node for node in mat.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    sock(bsdf, "Base Color").default_value = srgb(*color)
    sock(bsdf, "Roughness").default_value = rough
    try:
        sock(bsdf, "Metallic").default_value = 0.0
    except KeyError:
        pass
    for spec in ("Specular IOR Level", "Specular"):
        try:
            sock(bsdf, spec).default_value = 0.18
            break
        except KeyError:
            continue
    return mat


def _attach(mat, img):
    nodes = mat.node_tree.nodes
    bsdf = next(node for node in nodes if node.type == "BSDF_PRINCIPLED")
    tex = next((node for node in nodes if node.type == "TEX_IMAGE"), None)
    if tex is None:
        tex = nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.interpolation = "Linear"
    base = sock(bsdf, "Base Color")
    for link in list(base.links):
        mat.node_tree.links.remove(link)
    mat.node_tree.links.new(tex.outputs["Color"], base)
    return mat


def ensure_materials(vein_count):
    def leaf(name, pal):
        img = bpy.data.images.get(name)
        if img is None or img.get("cr_veins") != int(vein_count) or img.get("cr_rev") != REV:
            img = leaf_image(name, pal, vein_count)
        return img

    sand = bpy.data.images.get("CrSandGrain")
    if sand is None or sand.get("cr_rev") != REV:
        sand = sand_image()
    # Pale rhizome, cream roots, warm pale sand. Sheath paler than the blade.
    return {
        "leaf": _attach(_principled("CrLeaf", LEAF["base"], 0.55), leaf("CrLeafVeins", LEAF)),
        "young": _attach(_principled("CrLeafYoung", YOUNG["base"], 0.55), leaf("CrYoungVeins", YOUNG)),
        "rhizome": _principled("CrRhizome", (0.78, 0.70, 0.50), 0.58),
        "root": _principled("CrRoot", (0.94, 0.90, 0.78), 0.62),
        "stem": _principled("CrStem", (0.50, 0.58, 0.32), 0.55),
        "sheath": _principled("CrSheath", (0.80, 0.82, 0.60), 0.58),
        "scar": _principled("CrScar", (0.34, 0.28, 0.16), 0.50),
        "sand": _attach(_principled("CrSand", (0.90, 0.82, 0.64), 0.92), sand),
    }
