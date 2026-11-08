"""Packed images and materials. Veins and sand grain live in images so they survive glTF export."""

import bpy
import numpy as np

from .util import sock, srgb

# Pale yellow-green blades. The vein is a dark line, not a second shade of ribbon.
LEAF = {"base": (0.66, 0.78, 0.48), "vein": (0.03, 0.08, 0.03), "tip": (0.74, 0.84, 0.54), "pale": (0.82, 0.88, 0.62)}
YOUNG = {"base": (0.76, 0.86, 0.58), "vein": (0.06, 0.14, 0.05), "tip": (0.84, 0.90, 0.66), "pale": (0.90, 0.93, 0.74)}


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
    if vein_count <= 1:
        # One dark midvein. At the rounded tip it becomes two lines. The outline stays one end.
        split = 0.84
        ramp = np.clip((v - split) / 0.08, 0.0, 1.0)
        ramp = ramp * ramp * (3.0 - 2.0 * ramp)
        du = 0.26 * ramp
        sig = 0.020
        denom = 2.0 * sig * sig
        single = np.exp(-((u - 0.5) ** 2) / denom)
        left = np.exp(-((u - (0.5 - du)) ** 2) / (denom * 0.85))
        right = np.exp(-((u - (0.5 + du)) ** 2) / (denom * 0.85))
        stripe = single * (1.0 - ramp) + np.maximum(left, right) * ramp
    else:
        lanes = 0.5 + 0.5 * np.array(vein_xs(vein_count))
        stripe = np.max(np.exp(-((u[..., None] - lanes) ** 2) / (2 * 0.007 ** 2)), axis=-1)
    base, vein, tip, pale = (np.array(pal[k]) for k in ("base", "vein", "tip", "pale"))
    t = np.clip(v / 0.16, 0.0, 1.0)
    s = (t * t * (3 - 2 * t))[..., None]
    col = pale * (1 - s) + base * s
    from .config import CONFIG

    lesson = CONFIG.get("variant") in ("lesson", "phone")
    # The tip stays green so the split vein stays visible. A brown tip is not this leaf.
    tip_mix = 0.05 if vein_count <= 1 else (0.18 if lesson else 0.6)
    vein_mix = 1.0 if vein_count <= 1 else (0.16 if lesson else 0.24)
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


def sand_image(name="HpSandGrain", n=512, seed=5):
    """Dual-zone atlas:
    - v in [0.55, 1.00]: warm reef-sand surface
    - v in [0.46, 0.55]: reef-pebble stone band
    - v in [0.00, 0.46]: stratified cutaway sediment
    Grain is soft. Hard black-and-white specks read as a field of dots.
    """
    rng = np.random.default_rng(seed)
    u = np.linspace(0.0, 1.0, n, endpoint=False)[None, :]
    v = np.linspace(0.0, 1.0, n, endpoint=False)[:, None]
    tau = 2 * np.pi
    waves = 0.5 + 0.5 * (0.5 * np.sin(tau * (7 * u + 2 * v)) + 0.5 * np.sin(tau * (3 * u - 5 * v) + 1.7))
    grain = _soft_grain(rng, n, n // 24)
    broad = _soft_grain(rng, n, n // 48)

    base = np.array((0.91, 0.83, 0.68))
    top_col = base * (0.93 + 0.07 * waves[..., None])
    top_col = top_col * (0.97 + 0.045 * grain[..., None])
    top_col = top_col + broad[..., None] * np.array((0.02, 0.015, 0.008))

    peb_base = np.array((0.48, 0.46, 0.42))
    peb_mottle = 0.90 + 0.16 * (0.5 + 0.5 * np.sin(tau * (9 * u + 11 * v)))
    peb_col = peb_base * peb_mottle[..., None] * (0.96 + 0.06 * grain[..., None])

    depth = np.clip(v / 0.45, 0.0, 1.0)
    strata = 0.5 + 0.5 * np.sin(tau * (4.0 * depth + 0.04 * np.sin(tau * 2 * u)))
    crust = np.clip((depth - 0.86) / 0.14, 0.0, 1.0)[..., None]
    upper_sed = np.array((0.74, 0.64, 0.48))
    deep_sed = np.array((0.58, 0.48, 0.34))
    rim_sand = np.array((0.88, 0.78, 0.62))
    sed_col = deep_sed * (1.0 - depth[..., None]) + upper_sed * depth[..., None]
    sed_col = sed_col * (0.92 + 0.12 * strata[..., None])
    sed_col = sed_col * (0.98 + 0.03 * broad[..., None])
    sed_col = sed_col * (1.0 - crust) + rim_sand * crust

    col = np.where((v >= 0.55)[..., None], top_col, np.where((v >= 0.46)[..., None], peb_col, sed_col))
    img = _image(name, n, n)
    _fill(img, col)
    img["cr_cutaway"] = 1
    img["cr_grain"] = 2
    return img


def water_image(name="HpWater", w=128, h=512):
    """Aquarium water. The time-lapse uses a light shallow tank; the other set stays deep."""
    from .config import CONFIG

    v = np.linspace(0.0, 1.0, h)[:, None, None]
    if CONFIG.get("variant") in ("realistic", "lesson", "phone"):
        # MarineSee sea: water, primary, primaryDark from app/lib/theme/tokens.dart
        bottom = np.array((0.055, 0.494, 0.671))
        top = np.array((0.243, 0.784, 0.918))
    else:
        bottom = np.array((0.02, 0.07, 0.10))
        top = np.array((0.10, 0.34, 0.42))
    t = v * v * (3.0 - 2.0 * v)
    col = bottom * (1.0 - t) + top * t
    col = np.broadcast_to(col, (h, w, 3)).copy()
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
        style = "fork" if vein_count <= 1 else ("lesson" if CONFIG.get("variant") == "lesson" else "aquarium")
        img = bpy.data.images.get(name)
        if img is None or img.get("cr_veins") != vein_count or img.get("cr_style") != style:
            img = leaf_image(name, pal, vein_count)
            img["cr_style"] = style
        return img

    sand = bpy.data.images.get("HpSandGrain")
    if sand is None or sand.get("cr_grain") != 2:
        sand = sand_image()
    return {
        "leaf": _attach(_principled("HpLeaf", LEAF["base"], 0.48, 0.22), leaf_img("HpLeafVeins", LEAF)),
        "young": _attach(_principled("HpLeafYoung", YOUNG["base"], 0.50, 0.20), leaf_img("HpYoungVeins", YOUNG)),
        "rhizome": _principled("HpRhizome", (0.93, 0.89, 0.76), 0.46, 0.12),
        "root": _principled("HpRoot", (0.76, 0.68, 0.52), 0.62, 0.08),
        "stem": _principled("HpStem", (0.70, 0.78, 0.50), 0.52, 0.12),
        "sheath": _principled("HpSheath", (0.78, 0.84, 0.58), 0.56, 0.10),
        "scar": _principled("HpScar", (0.012, 0.012, 0.014), 0.40, 0.06),
        "sand": _attach(_principled("HpSand", (0.91, 0.83, 0.68), 0.90, 0.08), sand),
    }
