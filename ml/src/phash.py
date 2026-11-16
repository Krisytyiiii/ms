"""Perceptual hashing and observation grouping for the dataset.

Two frames of the same plant are not independent samples. If they land on
opposite sides of a split, the test row is effectively a training row and the
reported score is inflated. `docs/22-accuracy-plan.md` calls this out as the
biggest methodological hole in the v2 result.

This module supplies the missing pieces, with no new dependency:

    dhash(path)             64-bit difference hash; survives resize/re-encode
    near_duplicate_pairs    pairs closer than a Hamming distance
    observation_groups      one group per iNaturalist observation when the
                            filenames carry ids, else frames shot within a few
                            minutes, else one group per file
    split_groups            near-duplicate groups merged into observation groups

`split_groups` is what the grouped split should use: a near-duplicate pair and
a same-observation pair are both "one sample" for splitting purposes.

The iNaturalist import names files `{observation_id}_{photo_index}_inat`, and
that id is the strongest grouping key available here: it is the actual
observation the label came from, not a guess from timestamps. The Drive mirror
has no EXIF capture times, so without it the split can only dedupe.

Nothing here reads pixel content for training and nothing writes to the dataset.
"""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np
from PIL import Image

# 8x8 comparisons along one axis -> 64 bits. Enough to separate a blade from a
# sand close-up, cheap enough to hash a few thousand photos in seconds.
HASH_SIDE = 8
HASH_BITS = HASH_SIDE * HASH_SIDE

# Hamming distance under which two frames are treated as the same shot.
# 0-2 is the same file re-encoded; 3-6 is the same frame cropped or resized;
# beyond ~8 unrelated photos of similar seagrass start colliding.
NEAR_DUPLICATE_MAX_DISTANCE = 6

# Frames from one photoshoot are separated by seconds, not hours. A gap larger
# than this starts a new observation group.
OBSERVATION_GAP_SECONDS = 300

# iNaturalist export names: {observation_id}_{photo_index}_inat.jpg
_INAT_FRAME = re.compile(r"^(?P<observation>\d+)_(?P<index>\d+)_inat$", re.IGNORECASE)

_EXIF_MODEL = 272
_EXIF_DATETIME = 306
_EXIF_DATETIME_ORIGINAL = 36867
_EXIF_BODY_SERIAL = 42033
_EXIF_GPS_INFO = 34853


def dhash(path: Path) -> int:
    """64-bit difference hash: one bit per horizontal neighbour comparison."""
    with Image.open(path) as image:
        gray = image.convert("L").resize(
            (HASH_SIDE + 1, HASH_SIDE), Image.Resampling.BILINEAR
        )
        pixels = np.asarray(gray, dtype=np.int16)
    bits = (pixels[:, 1:] > pixels[:, :-1]).flatten()
    value = 0
    for bit in bits:
        value = (value << 1) | int(bit)
    return value


def hamming(left: int, right: int) -> int:
    """Bit distance between two 64-bit hashes."""
    return int((left ^ right).bit_count())


def _popcount_matrix(hashes: np.ndarray) -> np.ndarray:
    """(n, HASH_BITS) uint8 of the bits, so pairwise distances become matmuls."""
    as_bytes = np.ascontiguousarray(hashes, dtype=np.uint64).view(np.uint8)
    as_bytes = as_bytes.reshape(len(hashes), 8)
    return np.unpackbits(as_bytes, axis=1)


def near_duplicate_pairs(
    hashes: list[int] | np.ndarray,
    max_distance: int = NEAR_DUPLICATE_MAX_DISTANCE,
) -> list[tuple[int, int, int]]:
    """Return (i, j, distance) for every i < j closer than `max_distance`.

    Chunked so a few thousand photos do not allocate an n-by-n float matrix at
    once. Returns an empty list for fewer than two hashes.
    """
    values = np.asarray(list(hashes), dtype=np.uint64)
    n = len(values)
    if n < 2:
        return []
    bits = _popcount_matrix(values).astype(np.int32)
    found: list[tuple[int, int, int]] = []
    chunk = 512
    for start in range(0, n, chunk):
        stop = min(start + chunk, n)
        block = bits[start:stop]
        # distance = bits differ, counted over 64 positions
        distances = block.sum(axis=1)[:, None] + bits.sum(axis=1)[None, :]
        distances -= 2 * (block @ bits.T)
        for row in range(stop - start):
            i = start + row
            candidates = np.flatnonzero(distances[row] <= max_distance)
            for j in candidates:
                if j > i:
                    found.append((i, int(j), int(distances[row, j])))
    return found


class _UnionFind:
    def __init__(self, n: int) -> None:
        self.parent = list(range(n))

    def find(self, a: int) -> int:
        while self.parent[a] != a:
            self.parent[a] = self.parent[self.parent[a]]
            a = self.parent[a]
        return a

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[rb] = ra

    def labels(self) -> list[int]:
        """Dense group ids in first-appearance order, so output is stable."""
        seen: dict[int, int] = {}
        out: list[int] = []
        for index in range(len(self.parent)):
            root = self.find(index)
            if root not in seen:
                seen[root] = len(seen)
            out.append(seen[root])
        return out


def group_from_pairs(n: int, pairs: list[tuple[int, int, int]]) -> list[int]:
    """Union-find over near-duplicate pairs; returns one group id per item."""
    union = _UnionFind(n)
    for i, j, _distance in pairs:
        union.union(i, j)
    return union.labels()


def _parse_exif_datetime(raw: object) -> datetime | None:
    if not isinstance(raw, str):
        return None
    text = raw.strip().replace("\x00", "")
    for fmt in ("%Y:%m:%d %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text[:19], fmt)
        except ValueError:
            continue
    return None


def exif_provenance(path: Path) -> dict:
    """Camera model, capture time, and GPS presence. Never raises.

    Used by the audit for a data-card style provenance table; the split only
    needs the capture time.
    """
    info = {
        "path": str(path),
        "model": None,
        "datetime": None,
        "has_gps": False,
        "body_serial": None,
    }
    try:
        with Image.open(path) as image:
            exif = image.getexif()
    except (OSError, ValueError):
        return info

    def _text(tag: int) -> str | None:
        value = exif.get(tag)
        if isinstance(value, bytes):
            value = value.decode("ascii", "ignore")
        if not isinstance(value, str):
            return None
        cleaned = value.strip().replace("\x00", "")
        return cleaned or None

    info["model"] = _text(_EXIF_MODEL)
    info["body_serial"] = _text(_EXIF_BODY_SERIAL)
    info["datetime"] = _parse_exif_datetime(
        exif.get(_EXIF_DATETIME_ORIGINAL) or exif.get(_EXIF_DATETIME)
    )
    try:
        info["has_gps"] = bool(exif.get_ifd(_EXIF_GPS_INFO))
    except (KeyError, OSError, AttributeError):
        info["has_gps"] = False
    return info


def inaturalist_observation(path: Path) -> str | None:
    """Observation id from an iNaturalist export name, or None.

    `102223851_3_inat.jpg` is frame 3 of observation 102223851. The id is the
    label's provenance, so it groups a photoset even when the frames were
    re-encoded, cropped, or copied between folders.
    """
    match = _INAT_FRAME.match(path.stem)
    return match.group("observation") if match else None


def observation_groups(
    paths: list[Path],
    gap_seconds: int = OBSERVATION_GAP_SECONDS,
) -> tuple[list[int], str]:
    """Group frames into observation events.

    Order of preference:

    1. iNaturalist observation id in the filename -- the exact observation the
       label came from, so it survives re-encoding and folder copies;
    2. body serial + capture time -- the strongest key a JPEG carries;
    3. capture time clustered per folder: consecutive frames less than
       `gap_seconds` apart belong to the same shoot;
    4. no EXIF at all -- fall back to one group per file, which is exactly the
       image-level split the project is trying to move away from, so the
       caller is told the mode that was used.

    Returns (group_id_per_path, mode) where mode is "inaturalist",
    "inaturalist-partial", "exif", "time-cluster", or "per-file". "per-file" is
    a warning, not a success.
    """
    ids = [inaturalist_observation(path) for path in paths]
    if any(ids):
        ordered: dict[str, int] = {}
        labels: list[int] = []
        for index, observation in enumerate(ids):
            key = observation if observation is not None else f"file:{paths[index]}"
            if key not in ordered:
                ordered[key] = len(ordered)
            labels.append(ordered[key])
        mode = "inaturalist" if all(ids) else "inaturalist-partial"
        return labels, mode

    rows = [exif_provenance(path) for path in paths]
    dated = [row for row in rows if row["datetime"] is not None]
    serials = [row for row in rows if row["body_serial"]]

    if serials and len(serials) == len(rows):
        # Same camera body: cluster its frames by capture-time gap. This is
        # stronger than the folder-scoped cluster because one shoot can be
        # split across subfolders.
        order = sorted(range(len(rows)), key=lambda index: rows[index]["datetime"])
        labels = [0] * len(rows)
        group = 0
        previous: datetime | None = None
        for index in order:
            stamp = rows[index]["datetime"]
            if previous is not None:
                gap = (stamp - previous).total_seconds()
                if gap < 0 or gap > gap_seconds:
                    group += 1
            labels[index] = group
            previous = stamp
        return labels, "exif"

    if len(dated) < len(rows):
        return list(range(len(rows))), "per-file"

    by_folder: dict[str, list[int]] = defaultdict(list)
    for index, row in enumerate(rows):
        by_folder[str(paths[index].parent)].append(index)

    labels = [0] * len(rows)
    group = 0
    for _folder, members in sorted(by_folder.items()):
        members.sort(key=lambda index: rows[index]["datetime"])
        previous: datetime | None = None
        for position, index in enumerate(members):
            stamp = rows[index]["datetime"]
            if previous is not None:
                gap = (stamp - previous).total_seconds()
                if gap < 0 or gap > gap_seconds:
                    group += 1
            elif position > 0:
                group += 1
            labels[index] = group
            previous = stamp
        group += 1
    return labels, "time-cluster"


def split_groups(
    paths: list[Path],
    labels: list[str] | None = None,
    max_distance: int = NEAR_DUPLICATE_MAX_DISTANCE,
    gap_seconds: int = OBSERVATION_GAP_SECONDS,
    hashes: list[int] | None = None,
) -> tuple[list[int], dict]:
    """Observation groups with near-duplicate groups merged in.

    A pair of near-identical frames is one sample even if their EXIF is missing,
    so the two groupings are combined. Returns (group_id_per_path, report).

    `labels` must be passed when known. Near-duplicate merging is then limited
    to frames of the same class, because a cross-class near-duplicate is a
    *label* problem, not a grouping problem: merging two species into one group
    would break stratification and could empty a validation split. Cross-class
    pairs are still counted, as `cross_class_near_duplicates`.

    Transitive chaining is real: A close to B and B close to C can merge a long
    run of frames. Restricting merges to one class bounds the damage, and the
    report exposes `largest_group` so a degenerate pool is visible.
    """
    n = len(paths)
    if labels is not None and len(labels) != n:
        raise ValueError(
            f"labels must match paths ({len(labels)} != {n})"
        )
    if hashes is None:
        hashes = [dhash(path) for path in paths]
    duplicate_pairs = near_duplicate_pairs(hashes, max_distance)
    time_labels, time_mode = observation_groups(paths, gap_seconds)

    same_class: list[tuple[int, int, int]] = []
    cross_class = 0
    for i, j, distance in duplicate_pairs:
        if labels is not None and labels[i] != labels[j]:
            cross_class += 1
            continue
        same_class.append((i, j, distance))

    union = _UnionFind(n)
    for i, j, _distance in same_class:
        union.union(i, j)
    first_with_label: dict[int, int] = {}
    cross_class_observations = 0
    for index, label in enumerate(time_labels):
        if label in first_with_label:
            anchor = first_with_label[label]
            if labels is not None and labels[anchor] != labels[index]:
                # The same observation id is filed under two species. That is
                # a label problem; merging it would put two classes in one
                # group and break stratification, so report and skip.
                cross_class_observations += 1
                continue
            union.union(anchor, index)
        else:
            first_with_label[label] = index

    labels_out = union.labels()
    sizes = defaultdict(int)
    for label in labels_out:
        sizes[label] += 1
    report = {
        "mode": time_mode,
        "n_images": n,
        "n_groups": len(sizes),
        "largest_group": max(sizes.values()) if sizes else 0,
        "singleton_groups": sum(1 for size in sizes.values() if size == 1),
        "near_duplicate_pairs": len(same_class),
        "cross_class_near_duplicates": cross_class,
        "cross_class_observations": cross_class_observations,
        "near_duplicate_max_distance": max_distance,
        "observation_gap_seconds": gap_seconds,
    }
    if labels is not None:
        report["n_classes"] = len(set(labels))
        report["groups_per_class"] = round(len(sizes) / max(len(set(labels)), 1), 2)
    return labels_out, report
