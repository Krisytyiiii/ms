"""List, QC, resize, and lightly augment RGB images."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps
from skimage.color import hsv2rgb, rgb2hsv

try:
    from .dataset_contract import (
        IMAGE_SIZE,
        IMAGE_SUFFIXES,
        TRAIN_VARIANT,
        TRAINABLE_SPECIES,
    )
    from .inventory import iter_images, species_folders
    from .leaf_focus import ANALYZE_MAX_SIDE, analyze_and_crop, crop_to_plant
except ImportError:  # `python test_preprocess.py` from ml/src
    from dataset_contract import (
        IMAGE_SIZE,
        IMAGE_SUFFIXES,
        TRAIN_VARIANT,
        TRAINABLE_SPECIES,
    )
    from inventory import iter_images, species_folders
    from leaf_focus import ANALYZE_MAX_SIDE, analyze_and_crop, crop_to_plant

PREPROCESS_SPEC = {
    "version": "v1",
    "resize": IMAGE_SIZE,
    "color": "RGB",
    "exif_transpose": True,
    "leaf_crop": True,
    "min_side_px": 64,
    "min_pixel_std": 8.0,
    "plant_fraction_is_diagnostic": True,
    "variant": TRAIN_VARIANT,
}

MIN_SIDE_PX = 64
MIN_PIXEL_STD = 8.0
# Habitat: sky across the top of the frame and almost no green mask.
# A low green mask by itself stays (brown and pale blades).
HABITAT_SKY_FRACTION = 0.50
HABITAT_MAX_PLANT_FRACTION = 0.02
MIN_KEPT_PER_CLASS = 15
# Features are computed at 256px, so a 1024px working image is enough.
PREPARE_MAX_SIDE = 1024


def cap_per_class(
    pairs: list[tuple[Path, str]],
    max_per_class: int | None,
    seed: int = 42,
) -> list[tuple[Path, str]]:
    """Optional random cap so huge classes (ovalis ~1549) do not dominate runtime."""
    if max_per_class is None:
        return pairs
    by_class: dict[str, list[tuple[Path, str]]] = {}
    for pair in pairs:
        by_class.setdefault(pair[1], []).append(pair)
    rng = np.random.default_rng(seed)
    out: list[tuple[Path, str]] = []
    for items in by_class.values():
        if len(items) > max_per_class:
            pick = rng.choice(len(items), size=max_per_class, replace=False)
            items = [items[int(i)] for i in pick]
        out.extend(items)
    return out


def list_labeled_images(
    root: Path,
    *,
    species: tuple[str, ...] = TRAINABLE_SPECIES,
    variant: str = TRAIN_VARIANT,
) -> list[tuple[Path, str]]:
    """Return (path, slug) for the given species and variant only.

    Reads every study folder `species_folders` finds, including the held-out
    class that only exists nested inside trainable folders. `iter_images`
    prunes a nested different-species folder from its parent, so each image is
    labelled by its innermost species folder exactly once.
    """
    pairs: list[tuple[Path, str]] = []
    for folder, slug, folder_variant in species_folders(root):
        if slug not in species or folder_variant != variant:
            continue
        for path in iter_images(folder):
            if path.suffix.lower() in IMAGE_SUFFIXES:
                pairs.append((path, slug))
    return sorted(pairs, key=lambda pair: (pair[1], str(pair[0]).lower()))


def _pil_to_rgb(image: Image.Image) -> np.ndarray:
    image = ImageOps.exif_transpose(image)
    image = image.convert("RGB")
    return np.array(image, dtype=np.uint8, copy=True)


def load_rgb_full(path: Path) -> np.ndarray:
    with Image.open(path) as image:
        return _pil_to_rgb(image)


def _pixel_std(rgb: np.ndarray) -> float:
    """Std on a short stride so a large frame is not copied to float64."""
    step = max(1, int(max(rgb.shape[0], rgb.shape[1]) / 256))
    return float(rgb[::step, ::step].std())


def load_rgb_from_bytes(data: bytes, size: int = IMAGE_SIZE) -> np.ndarray:
    return resize_rgb(_pil_to_rgb(Image.open(BytesIO(data))), size=size)


def resize_rgb(rgb: np.ndarray, size: int = IMAGE_SIZE) -> np.ndarray:
    image = Image.fromarray(rgb)
    image = image.resize((size, size), Image.Resampling.LANCZOS)
    return np.asarray(image, dtype=np.uint8)


def load_rgb(path: Path, size: int = IMAGE_SIZE) -> np.ndarray:
    return resize_rgb(load_rgb_full(path), size=size)


def prepare_rgb(rgb: np.ndarray, size: int = IMAGE_SIZE) -> np.ndarray:
    """Plant crop when the green mask allows it, then resize.

    Training and identify must both go through this before extract_vector.
    """
    cropped, _ = crop_to_plant(rgb)
    return resize_rgb(cropped, size=size)


def _load_capped_rgb(path: Path, max_side: int) -> tuple[np.ndarray, tuple[int, int]]:
    """Header size plus an RGB array no longer than max_side.

    JPEG draft keeps a multi-megapixel original from being decoded in full.
    """
    source = Image.open(path)
    try:
        orig = source.size
        source.draft("RGB", (max_side, max_side))
        transposed = ImageOps.exif_transpose(source)
        try:
            rgb = transposed.convert("RGB")
            rgb.thumbnail((max_side, max_side), Image.Resampling.BILINEAR)
            return np.array(rgb, dtype=np.uint8, copy=True), orig
        finally:
            if transposed is not source:
                transposed.close()
    finally:
        source.close()


def load_qc_preview(path: Path) -> tuple[np.ndarray, tuple[int, int]]:
    """512px preview and the file's header size. Raises if the file is unreadable."""
    return _load_capped_rgb(path, ANALYZE_MAX_SIDE)


def qc_path(path: Path) -> str | None:
    """Same rules as `qc_reason`, read from a preview so the full frame stays on disk."""
    try:
        preview, (width, height) = load_qc_preview(path)
    except (OSError, ValueError, MemoryError):
        return "unreadable"
    if min(width, height) < MIN_SIDE_PX:
        return "too_small"
    if _pixel_std(preview) < MIN_PIXEL_STD:
        return "low_contrast"
    _cropped, plant, sky, _did_crop = analyze_and_crop(preview)
    if sky >= HABITAT_SKY_FRACTION and plant < HABITAT_MAX_PLANT_FRACTION:
        return "habitat"
    return None


def load_prepared(path: Path, size: int = IMAGE_SIZE) -> np.ndarray:
    rgb, _orig = _load_capped_rgb(path, PREPARE_MAX_SIDE)
    return prepare_rgb(rgb, size=size)


def prepared_from_bytes(data: bytes, size: int = IMAGE_SIZE) -> np.ndarray:
    return prepare_rgb(_pil_to_rgb(Image.open(BytesIO(data))), size=size)


def qc_reason(rgb: np.ndarray) -> str | None:
    """Return a skip reason, or None if the frame may be used.

    Habitat frames are rejected: the top of the frame is sky-like and the green
    plant mask covers under 2%. A low green mask alone is kept, so brown and
    pale blades stay. The per-class guard that can waive this reject lives in
    `select_frames.select_leaf_frames`.
    """
    height, width = rgb.shape[:2]
    if min(height, width) < MIN_SIDE_PX:
        return "too_small"
    if _pixel_std(rgb) < MIN_PIXEL_STD:
        return "low_contrast"
    _cropped, plant, sky, _did_crop = analyze_and_crop(rgb)
    if sky >= HABITAT_SKY_FRACTION and plant < HABITAT_MAX_PLANT_FRACTION:
        return "habitat"
    return None


def process_rgb(rgb: np.ndarray, size: int = IMAGE_SIZE) -> tuple[np.ndarray, dict]:
    """QC â†’ optional plant crop â†’ resize. Does not augment."""
    reason = qc_reason(rgb)
    cropped, frac, sky, did_crop = analyze_and_crop(rgb)
    base = {
        "plant_fraction": frac,
        "sky_fraction": sky,
        "cropped": False,
        "src_size": [int(rgb.shape[1]), int(rgb.shape[0])],
    }
    if reason is not None:
        return rgb, {"status": "skipped", "reason": reason, **base}
    out = resize_rgb(cropped, size=size)
    return out, {"status": "kept", "reason": None, **base, "cropped": did_crop}


_SMALL_ROTATIONS = {
    "rot15": 15.0,
    "rot-15": -15.0,
    "rot25": 25.0,
    "rot-25": -25.0,
}
_SCALES = {"scale85": 0.85, "scale115": 1.15}
_BRIGHTNESS = {"bright-12": 0.88, "bright+12": 1.12}


def _border_fill(image: Image.Image) -> tuple[int, int, int]:
    arr = np.asarray(image)
    border = np.concatenate([arr[0], arr[-1], arr[:, 0], arr[:, -1]], axis=0)
    median = np.median(border, axis=0)
    return tuple(int(channel) for channel in median)


def _rotated(image: Image.Image, degrees: float) -> Image.Image:
    return image.rotate(
        degrees,
        resample=Image.Resampling.BICUBIC,
        expand=False,
        fillcolor=_border_fill(image),
    )


def _scaled(image: Image.Image, factor: float) -> Image.Image:
    width, height = image.size
    scaled_w = max(1, int(round(width * factor)))
    scaled_h = max(1, int(round(height * factor)))
    resized = image.resize((scaled_w, scaled_h), Image.Resampling.LANCZOS)
    if factor >= 1.0:
        left = max(0, (scaled_w - width) // 2)
        top = max(0, (scaled_h - height) // 2)
        return resized.crop((left, top, left + width, top + height))
    canvas = Image.new("RGB", (width, height), _border_fill(image))
    canvas.paste(resized, ((width - scaled_w) // 2, (height - scaled_h) // 2))
    return canvas


def _brightness(rgb: np.ndarray, factor: float) -> np.ndarray:
    """Scale HSV value. Hue is left unchanged."""
    hsv = np.array(rgb2hsv(rgb.astype(np.float64) / 255.0), copy=True)
    hsv[:, :, 2] = np.clip(hsv[:, :, 2] * factor, 0.0, 1.0)
    out = hsv2rgb(hsv)
    return np.clip(np.round(out * 255.0), 0, 255).astype(np.uint8)


def augment_rgb(rgb: np.ndarray, kind: str) -> np.ndarray:
    if kind in _BRIGHTNESS:
        return _brightness(rgb, _BRIGHTNESS[kind])
    image = Image.fromarray(rgb)
    if kind == "hflip":
        image = ImageOps.mirror(image)
    elif kind == "rot90":
        image = image.rotate(90, expand=False)
    elif kind == "rot270":
        image = image.rotate(270, expand=False)
    elif kind in _SMALL_ROTATIONS:
        image = _rotated(image, _SMALL_ROTATIONS[kind])
    elif kind in _SCALES:
        image = _scaled(image, _SCALES[kind])
    elif kind == "zoom":
        width, height = image.size
        inset = int(min(width, height) * 0.1)
        image = image.crop((inset, inset, width - inset, height - inset)).resize(
            (width, height), Image.Resampling.LANCZOS
        )
    else:
        raise ValueError(kind)
    return np.asarray(image, dtype=np.uint8)


def expand_minority_train(
    images: list[np.ndarray],
    labels: list[str],
    min_per_class: int = 80,
) -> tuple[list[np.ndarray], list[str]]:
    """Add flip/rotate/zoom copies for classes below min_per_class. Train only."""
    kinds = ("hflip", "rot90", "rot270", "zoom")
    out_images = list(images)
    out_labels = list(labels)
    by_class: dict[str, list[np.ndarray]] = {}
    for img, lab in zip(images, labels):
        by_class.setdefault(lab, []).append(img)

    for lab, items in by_class.items():
        extra_needed = max(0, min_per_class - len(items))
        if extra_needed == 0:
            continue
        made = 0
        idx = 0
        while made < extra_needed:
            src = items[idx % len(items)]
            kind = kinds[idx % len(kinds)]
            out_images.append(augment_rgb(src, kind))
            out_labels.append(lab)
            made += 1
            idx += 1
    return out_images, out_labels
