"""Train-only copies that move shape and brightness. Validation and test stay real."""

from __future__ import annotations

from collections import Counter

import numpy as np

try:
    from .preprocess import augment_rgb
except ImportError:  # `python test_preprocess.py` from ml/src
    from preprocess import augment_rgb

MAX_COPIES_PER_PHOTO = 3
MAX_PER_CLASS = 200
CURATED_KINDS = (
    "hflip",
    "rot15",
    "rot-15",
    "rot25",
    "rot-25",
    "scale85",
    "scale115",
    "bright-12",
    "bright+12",
)

AUGMENT_SPEC = {
    "splits": "train only",
    "copies_per_photo": MAX_COPIES_PER_PHOTO,
    "max_per_class": MAX_PER_CLASS,
    "kinds": list(CURATED_KINDS),
    "rotation_deg": [15, 25],
    "scale": [0.85, 1.15],
    "brightness": 0.12,
    "hue": "unchanged",
    "stop": "median real-train count of classes above the overall median, capped at 200",
}


def _median(values: list[int]) -> float:
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return float(ordered[mid])
    return (ordered[mid - 1] + ordered[mid]) / 2.0


def augment_stop_count(counts: dict[str, int]) -> int:
    """Class size where extra copies stop.

    The stop is the median real training count among classes above the overall
    median, and it is never past 200. Classes already at that size get no copies.
    """
    values = [int(count) for count in counts.values() if int(count) > 0]
    if not values:
        return 0
    overall = _median(values)
    larger = [count for count in values if count > overall]
    target = _median(larger) if larger else overall
    return min(MAX_PER_CLASS, int(target))


def _copy_counts(n_photos: int, room: int) -> list[int]:
    assigned = [0] * n_photos
    if n_photos == 0 or room <= 0:
        return assigned
    cursor = 0
    made = 0
    while made < room:
        if assigned[cursor] < MAX_COPIES_PER_PHOTO:
            assigned[cursor] += 1
            made += 1
        cursor = (cursor + 1) % n_photos
        if made < room and all(count >= MAX_COPIES_PER_PHOTO for count in assigned):
            break
    return assigned


def augment_train(
    images: list[np.ndarray],
    labels: list[str],
    seed: int = 42,
) -> tuple[list[np.ndarray], list[str]]:
    """Append at most three copies per real training photo. Labels stay aligned."""
    counts = Counter(labels)
    stop = augment_stop_count(dict(counts))
    by_class: dict[str, list[int]] = {}
    for index, label in enumerate(labels):
        by_class.setdefault(label, []).append(index)

    rng = np.random.default_rng(seed)
    out_images = list(images)
    out_labels = list(labels)
    for label in sorted(by_class):
        indexes = by_class[label]
        room = max(0, stop - len(indexes))
        room = min(room, MAX_COPIES_PER_PHOTO * len(indexes))
        if room == 0:
            continue
        for index, n_copies in zip(indexes, _copy_counts(len(indexes), room)):
            if n_copies == 0:
                continue
            picked = sorted(
                int(kind)
                for kind in rng.choice(len(CURATED_KINDS), size=n_copies, replace=False)
            )
            source = images[index]
            for kind_index in picked:
                out_images.append(augment_rgb(source, CURATED_KINDS[kind_index]))
                out_labels.append(label)
    return out_images, out_labels
