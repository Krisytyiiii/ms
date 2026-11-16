"""Keep leaf-visible frames and drop exact duplicate files before the split."""

from __future__ import annotations

import hashlib
from collections import Counter
from pathlib import Path

try:
    from .preprocess import (
        HABITAT_MAX_PLANT_FRACTION,
        HABITAT_SKY_FRACTION,
        MIN_KEPT_PER_CLASS,
        qc_path,
    )
except ImportError:  # `python test_preprocess.py` from ml/src
    from preprocess import (
        HABITAT_MAX_PLANT_FRACTION,
        HABITAT_SKY_FRACTION,
        MIN_KEPT_PER_CLASS,
        qc_path,
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def drop_exact_duplicates(
    pairs: list[tuple[Path, str]],
) -> tuple[list[tuple[Path, str]], int]:
    """Keep one file per byte digest so the same JPEG cannot sit in train and test."""
    ordered = sorted(pairs, key=lambda item: (item[1], str(item[0]).lower()))
    seen: set[str] = set()
    kept: list[tuple[Path, str]] = []
    dropped = 0
    for path, slug in ordered:
        digest = _sha256(path)
        if digest in seen:
            dropped += 1
            continue
        seen.add(digest)
        kept.append((path, slug))
    return kept, dropped


def _frame_reason(path: Path) -> str | None:
    return qc_path(path)


def select_leaf_frames(
    pairs: list[tuple[Path, str]],
    reason_fn=None,
) -> tuple[list[tuple[Path, str]], dict]:
    """QC the pool, waive habitat for tiny classes, then drop exact duplicates.

    `too_small` and `low_contrast` always drop. Habitat drops unless applying it
    would leave that class under 15 photos.

    `reason_fn(path)` replaces `qc_path` when the caller has a cache; the rules
    are unchanged.
    """
    reason_for = reason_fn or _frame_reason
    scored: list[dict] = []
    total = len(pairs)
    for index, (path, slug) in enumerate(pairs, start=1):
        scored.append(
            {
                "path": path,
                "slug": slug,
                "reason": reason_for(path),
                "waived": False,
            }
        )
        if index % 250 == 0 or index == total:
            print(f"qc {index}/{total}", flush=True)

    by_slug: dict[str, list[dict]] = {}
    for row in scored:
        by_slug.setdefault(row["slug"], []).append(row)

    waived: list[str] = []
    waived_frames = 0
    for slug in sorted(by_slug):
        rows = by_slug[slug]
        kept_n = sum(1 for row in rows if row["reason"] is None)
        if kept_n >= MIN_KEPT_PER_CLASS:
            continue
        habitat_rows = [row for row in rows if row["reason"] == "habitat"]
        if not habitat_rows:
            continue
        for row in habitat_rows:
            row["reason"] = None
            row["waived"] = True
        waived.append(slug)
        waived_frames += len(habitat_rows)

    passing = [(row["path"], row["slug"]) for row in scored if row["reason"] is None]
    kept, duplicates_dropped = drop_exact_duplicates(passing)
    kept_keys = {str(path.resolve()) for path, _ in kept}

    skip_reasons: dict[str, int] = {}
    for row in scored:
        if str(row["path"].resolve()) in kept_keys:
            continue
        reason = "duplicate" if row["reason"] is None else str(row["reason"])
        skip_reasons[reason] = skip_reasons.get(reason, 0) + 1

    listed = Counter(slug for _, slug in pairs)
    kept_counts = Counter(slug for _, slug in kept)
    slugs = sorted(set(listed) | set(kept_counts))
    below = [slug for slug in slugs if kept_counts[slug] < MIN_KEPT_PER_CLASS]
    return kept, {
        "listed": len(pairs),
        "kept": len(kept),
        "dropped": len(pairs) - len(kept),
        "duplicates_dropped": duplicates_dropped,
        "habitat_waived": waived,
        "habitat_frames_kept_by_waiver": waived_frames,
        "classes_below_minimum": below,
        "min_kept_per_class": MIN_KEPT_PER_CLASS,
        "habitat_sky_fraction": HABITAT_SKY_FRACTION,
        "habitat_max_plant_fraction": HABITAT_MAX_PLANT_FRACTION,
        "by_slug_listed": {slug: int(listed[slug]) for slug in slugs},
        "by_slug_kept": {slug: int(kept_counts[slug]) for slug in slugs},
        "by_slug_dropped": {slug: int(listed[slug] - kept_counts[slug]) for slug in slugs},
        "skip_reasons": skip_reasons,
    }
