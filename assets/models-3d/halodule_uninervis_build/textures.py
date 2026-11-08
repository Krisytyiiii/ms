"""Packed images and materials. Veins and sand grain live in images so they survive glTF export."""

import bpy
import numpy as np

from .util import sock, srgb

LEAF = {"base": (0.24, 0.50, 0.22), "vein": (0.12, 0.31, 0.12), "tip": (0.40, 0.60, 0.28), "pale": (0.68, 0.72, 0.46)}
YOUNG = {"base": (0.46, 0.70, 0.34), "vein": (0.29, 0.50, 0.23), "tip": (0.58, 0.77, 0.41), "pale": (0.78, 0.82, 0.56)}


def vein_xs(vein_count):
    """Vein lane positions across the strap, -1..1 is edge to edge."""
    if vein_count <= 1:
        return [0.0]
    return [-0.9 + 1.8 * k / (vein_count - 1) for k in range(vein_count)]


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


def leaf_image(name, pal, vein_count, w=256, h=512, seed=3):
    rng = np.random.default_rng(seed)
    u = np.linspace(0.0, 1.0, w)[None, :]
    v = np.linspace(0.0, 1.0, h)[:, None]
    one = vein_count <= 1
    if one:
        stripe = np.exp(-((u - 0.5) ** 2) / (2 * 0.040 ** 2))
    else:
        lanes = 0.5 + 0.5 * np.array(vein_xs(vein_count))
        stripe = np.max(np.exp(-((u[..., None] - lanes) ** 2) / (2 * 0.007 ** 2)), axis=-1)
    base, vein, tip, pale = (np.array(pal[k]) for k in ("base", "vein", "tip", "pale"))
    t = np.clip(v / 0.16, 0.0, 1.0)
    s = (t * t * (3 - 2 * t))[..., None]
    col = pale * (1 - s) + base * s
    from .config import CONFIG

    lesson = CONFIG.get("variant") == "lesson"
    # One dark midrib, and the trident stays green. The vein does not split.
    tip_mix = 0.0 if one else (0.18 if lesson else 0.6)
    vein_mix = 0.86 if one else (0.16 if lesson else 0.24)
    tt = np.clip((v - 0.78) / 0.22, 0.0, 1.0)[..., None] * tip_mix
    col = col * (1 - tt) + tip * tt
    col = np.broadcast_to(col, (h, w, 3)).copy()
    k = stripe[..., None] * vein_mix
    col = col * (1 - k) + vein * k
    edge = np.clip((np.abs(u - 0.5) * 2 - 0.9) / 0.1, 0.0, 1.0)
    col *= (1 - 0.06 * edge)[..., None]
    streak = np.convolve(rng.normal(0, 1, w), np.ones(5) / 5, mode="same") * 0.018
    col *= (1 + streak)[None, :, None]
    img = _image(name, w, h)
    _fill(img, col)
    img["cr_veins"] = vein_count
    return img


def _soft_grain(rng, n, cells):
    """Low-frequency grain. No salt-and-pepper specks."""
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


def sand_image(name="HuSandGrain", n=512, seed=5):
    """Warm pale sand. The top band is the bed; the lower band is the same sand in the cut."""
    rng = np.random.default_rng(seed)
    u = np.linspace(0.0, 1.0, n, endpoint=False)[None, :]
    v = np.linspace(0.0, 1.0, n, endpoint=False)[:, None]
    tau = 2 * np.pi
    waves = 0.5 + 0.5 * (0.5 * np.sin(tau * (7 * u + 2 * v)) + 0.5 * np.sin(tau * (3 * u - 5 * v) + 1.7))
    grain = _soft_grain(rng, n, n // 24)
    broad = _soft_grain(rng, n, n // 48)

    base = np.array((0.86, 0.76, 0.58))
    top_col = base * (0.94 + 0.08 * waves[..., None])
    top_col = top_col * (0.97 + 0.04 * grain[..., None])
    top_col = top_col + broad[..., None] * np.array((0.018, 0.012, 0.006))

    depth = np.clip(v / 0.50, 0.0, 1.0)
    strata = 0.5 + 0.5 * np.sin(tau * (3.0 * depth + 0.03 * np.sin(tau * 2 * u)))
    cut = np.array((0.74, 0.64, 0.48))
    deep = np.array((0.62, 0.52, 0.38))
    cut_col = deep * (1.0 - depth[..., None]) + cut * depth[..., None]
    cut_col = cut_col * (0.94 + 0.08 * strata[..., None])
    cut_col = cut_col * (0.98 + 0.03 * broad[..., None])

    col = np.where((v >= 0.52)[..., None], top_col, cut_col)
    img = _image(name, n, n)
    _fill(img, col)
    img["cr_cutaway"] = 1
    img["cr_grain"] = 3
    return img


def water_image(name="HuWater", w=128, h=512):
    """Aquarium water. The time-lapse uses a light shallow tank; the other set stays deep."""
    from .config import CONFIG

    u = np.linspace(0.0, 1.0, w)[None, :, None]
    v = np.linspace(0.0, 1.0, h)[:, None, None]
    if CONFIG.get("variant") in ("realistic", "lesson"):
        # MarineSee sea: water, primary, primaryDark from app/lib/theme/tokens.dart
        bottom = np.array((0.055, 0.494, 0.671))
        mid = np.array((0.078, 0.588, 0.769))
        top = np.array((0.243, 0.784, 0.918))
    else:
        bottom = np.array((0.02, 0.07, 0.10))
        mid = np.array((0.04, 0.16, 0.22))
        top = np.array((0.10, 0.34, 0.42))
    a = np.clip(v / 0.45, 0.0, 1.0)
    a = a * a * (3.0 - 2.0 * a)
    b = np.clip((v - 0.45) / 0.55, 0.0, 1.0)
    b = b * b * (3.0 - 2.0 * b)
    col = bottom * (1.0 - a) + mid * a
    col = col * (1.0 - b) + top * b
    col = np.broadcast_to(col, (h, w, 3)).copy()
    # Soft vertical sun shafts strongest near the top of the aquarium
    rays = (
        0.5 + 0.5 * np.sin((u * 5.0 + v * 0.7) * 2.0 * np.pi)
    ) * (0.5 + 0.5 * np.cos((u * 11.0 - v * 0.4) * 2.0 * np.pi + 0.8))
    shaft = (rays ** 2) * (v ** 1.4) * 0.10
    col += shaft * np.array((0.35, 0.75, 0.85))
    img = _image(name, w, h)
    _fill(img, col)
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
    sock(bsdf, "Specular IOR Level").default_value = spec
    return mat


def _attach(mat, img):
    nodes = mat.node_tree.nodes
    bsdf = next(node for node in nodes if node.type == "BSDF_PRINCIPLED")
    tex = next((node for node in nodes if node.type == "TEX_IMAGE"), None) or nodes.new("ShaderNodeTexImage")
    tex.image = img
    mat.node_tree.links.new(tex.outputs["Color"], sock(bsdf, "Base Color"))
    return mat


def ensure_materials(vein_count):
    from .config import CONFIG

    def leaf_img(name, pal):
        style = "lesson" if CONFIG.get("variant") == "lesson" else "aquarium"
        img = bpy.data.images.get(name)
        if img is None or img.get("cr_veins") != vein_count or img.get("cr_style") != style:
            img = leaf_image(name, pal, vein_count)
            img["cr_style"] = style
        return img

    sand = bpy.data.images.get("HuSandGrain")
    if sand is None or sand.get("cr_grain") != 3:
        sand = sand_image()
    return {
        "leaf": _attach(_principled("HuLeaf", LEAF["base"], 0.48, 0.22), leaf_img("HuLeafVeins", LEAF)),
        "young": _attach(_principled("HuLeafYoung", YOUNG["base"], 0.50, 0.20), leaf_img("HuYoungVeins", YOUNG)),
        "rhizome": _principled("HuRhizome", (0.95, 0.90, 0.78), 0.46, 0.08),
        "root": _principled("HuRoot", (0.90, 0.84, 0.68), 0.62, 0.10),
        "stem": _principled("HuStem", (0.52, 0.60, 0.34), 0.55, 0.14),
        "sheath": _principled("HuSheath", (0.70, 0.74, 0.46), 0.58, 0.12),
        "scar": _principled("HuScar", (0.012, 0.012, 0.014), 0.40, 0.03),
        "sand": _attach(_principled("HuSand", (0.86, 0.76, 0.58), 0.94, 0.05), sand),
    }
