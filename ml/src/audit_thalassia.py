"""Read-only audit of the held-out Thalassia folders before they may be trained.

`docs/22-accuracy-plan.md` action 1.1. The class is held out because an older
local dump had Thalassia photos nested inside Enhalus and Halodule folders, so
the risk runs both ways: the candidate class may contain other taxa, and the
*trainable* classes may already contain Thalassia. This script only reads.

It answers four questions:

1. How many Thalassia images exist, and per folder variant?
2. How many would survive the same QC the training pool gets (`qc_path`)?
3. Do any Thalassia frames near-duplicate a frame in another species folder?
   Each hit is a label problem in one direction or the other.
4. What does provenance look like (camera models, capture span, GPS coverage)?

Writes two files and retrains nothing:

    ml/artifacts/thalassia_audit.json     machine-readable summary
    ml/artifacts/thalassia_review.csv     human review queue, worst match first

    python ml/src/audit_thalassia.py
    python ml/src/audit_thalassia.py --root D:\\path\\to\\Seagrass --max-distance 6
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.dataset_contract import (  # noqa: E402
    IMAGE_SUFFIXES,
    TRAINABLE_SPECIES,
    classify_folder,
)
from src.inventory import iter_images, nested_other_species_dirs  # noqa: E402
from src.phash import (  # noqa: E402
    NEAR_DUPLICATE_MAX_DISTANCE,
    dhash,
    exif_provenance,
    group_from_pairs,
    near_duplicate_pairs,
)
from src.preprocess import qc_path  # noqa: E402

CANDIDATE = "thalassia_hemprichii"
DATA_ROOT = ROOT.parent / "assets" / "species" / "Seagrass"
ARTIFACTS = ROOT / "artifacts"


def _folder_pairs(root: Path) -> list[tuple[Path, str, str]]:
    """(path, slug, folder_variant) for every study folder, any variant.

    The held-out class only exists *inside* the trainable folders on the Drive
    layout, so a top-level walk would find zero candidates. `iter_images`
    prunes a nested different-species folder from its parent, so the nested
    folder itself is collected here and every image is still counted once.

    Nested mirrors of the same class+variant (the Drive has three identical
    Thalassia `(all)` copies) are collapsed to the largest one: hashing the
    same frames three times would read as tripled duplication and downgrade
    the verdict for no reason.
    """
    rows: list[tuple[Path, str, str]] = []
    nested_best: dict[tuple[str, str], tuple[Path, list[Path]]] = {}
    mirrors: list[tuple[Path, Path]] = []

    for child in sorted(root.iterdir(), key=lambda p: p.name.lower()):
        if not child.is_dir() or child.name.startswith("."):
            continue
        slug, scope, variant = classify_folder(child.name)
        if scope != "study" or slug is None:
            continue
        for path in iter_images(child):
            if path.suffix.lower() in IMAGE_SUFFIXES:
                rows.append((path, slug, variant))

        for nested in nested_other_species_dirs(child):
            nslug, nscope, nvariant = classify_folder(nested.name)
            if nscope != "study" or nslug is None:
                continue
            key = (nslug, nvariant)
            images = [
                path
                for path in iter_images(nested)
                if path.suffix.lower() in IMAGE_SUFFIXES
            ]
            kept = nested_best.get(key)
            if kept is None or len(images) > len(kept[1]):
                if kept is not None:
                    mirrors.append((kept[0], nested))
                nested_best[key] = (nested, images)
            else:
                mirrors.append((kept[0], nested))

    for nested, images in nested_best.values():
        nslug, _scope, nvariant = classify_folder(nested.name)
        rows.extend((path, nslug, nvariant) for path in images)
    for kept, dropped in mirrors:
        print(
            f"note: {dropped} is a repeat of the same class+variant as {kept}; "
            "not hashed twice",
            file=sys.stderr,
        )
    return rows



def _median(values: list[float]) -> float | None:
    return float(np.median(values)) if values else None


def _rel(path: Path, root: Path) -> str:
    """Root-relative for the committed review CSV: no local mirror paths."""
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Read-only Thalassia mix-in audit."
    )
    parser.add_argument("--root", type=Path, default=DATA_ROOT)
    parser.add_argument("--out", type=Path, default=ARTIFACTS)
    parser.add_argument(
        "--max-distance",
        type=int,
        default=NEAR_DUPLICATE_MAX_DISTANCE,
        help="Hamming distance under which two frames are the same shot",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="cap images per species for a quick pass (0 = no cap)",
    )
    parser.add_argument(
        "--review-limit",
        type=int,
        default=300,
        help="rows in the human review CSV",
    )
    args = parser.parse_args()

    if not args.root.is_dir():
        raise SystemExit(
            f"dataset root not found: {args.root}\n"
            "Point --root at the Seagrass folder (Drive or a local copy). "
            "Nothing was written."
        )

    print(f"scanning {args.root}")
    rows = _folder_pairs(args.root)
    if not rows:
        raise SystemExit("no study folders matched; check --root and dataset_contract.py")

    by_slug: dict[str, list[tuple[Path, str, str]]] = defaultdict(list)
    for path, slug, variant in rows:
        by_slug[slug].append((path, slug, variant))

    candidates = by_slug.get(CANDIDATE, [])
    if not candidates:
        raise SystemExit(
            f"no {CANDIDATE} folder found under {args.root}. "
            "If Thalassia moved, update SPECIES_PHRASES in dataset_contract.py."
        )

    if args.limit:
        candidates = candidates[: args.limit]

    print(
        f"{CANDIDATE}: {len(candidates)} images in "
        f"{len({variant for _p, _s, variant in candidates})} variant(s)"
    )
    variant_counts = Counter(variant for _p, _s, variant in candidates)
    for variant, count in sorted(variant_counts.items()):
        print(f"  variant {variant:16s} {count:5d}")

    # 1. QC, same filter the training pool gets.
    qc_reasons: Counter[str] = Counter()
    qc_pass: list[tuple[Path, str, str]] = []
    for path, slug, variant in candidates:
        reason = qc_path(path)
        qc_reasons[reason or "pass"] += 1
        if reason is None:
            qc_pass.append((path, slug, variant))
    usable = len(qc_pass)
    print(f"  QC pass {usable} / {len(candidates)}  {dict(qc_reasons)}")

    # 2. Hashes for the candidate class and every trainable class it could
    # already be hiding inside.
    references = [
        (path, slug, variant)
        for slug in TRAINABLE_SPECIES
        for path, _s, variant in by_slug.get(slug, [])
    ]
    if args.limit:
        capped: dict[str, list[tuple[Path, str, str]]] = defaultdict(list)
        for row in references:
            if len(capped[row[1]]) < args.limit:
                capped[row[1]].append(row)
        references = [row for slug_rows in capped.values() for row in slug_rows]

    pool = qc_pass + references
    print(f"hashing {len(pool)} images ({usable} candidate + {len(references)} reference)")
    hashes: list[int] = []
    failed = 0
    for path, _slug, _variant in pool:
        try:
            hashes.append(dhash(path))
        except (OSError, ValueError):
            hashes.append(0)
            failed += 1

    n_candidate = len(qc_pass)
    pairs = near_duplicate_pairs(hashes, args.max_distance)
    cross_class = [
        (i, j, distance)
        for i, j, distance in pairs
        if (i < n_candidate) != (j < n_candidate)
    ]
    within_candidate = [
        (i, j, distance)
        for i, j, distance in pairs
        if i < n_candidate and j < n_candidate
    ]

    # 3. Which reference classes absorb the candidate frames, and how badly.
    absorbed: Counter[str] = Counter()
    suspicious_candidate: dict[int, tuple[str, int]] = {}
    review_rows: list[dict] = []
    for i, j, distance in cross_class:
        candidate_index, other_index = (i, j) if i < n_candidate else (j, i)
        candidate_path = qc_pass[candidate_index][0]
        other_path, other_slug, _variant = pool[other_index]
        absorbed[other_slug] += 1
        current = suspicious_candidate.get(candidate_index)
        if current is None or distance < current[1]:
            suspicious_candidate[candidate_index] = (other_slug, distance)
        review_rows.append(
            {
                "distance": distance,
                "candidate": _rel(candidate_path, args.root),
                "candidate_folder": candidate_path.parent.name,
                "closest_class": other_slug,
                "closest_path": _rel(other_path, args.root),
                "closest_folder": other_path.parent.name,
            }
        )
    review_rows.sort(key=lambda row: (row["distance"], row["candidate"]))

    # 4. Near-duplicate clusters inside the candidate class: how much of it is
    # really distinct plants.
    within_groups = group_from_pairs(n_candidate, within_candidate)
    group_sizes = Counter(within_groups)
    distinct_plants = len(group_sizes)

    # 5. Provenance for the data card.
    provenance = [exif_provenance(path) for path, _slug, _variant in qc_pass]
    models = Counter(row["model"] for row in provenance if row["model"])
    dated = [row["datetime"] for row in provenance if row["datetime"]]
    gps_share = (
        sum(1 for row in provenance if row["has_gps"]) / len(provenance)
        if provenance
        else 0.0
    )

    mixin_share = len({i for i, _j, _d in cross_class if i < n_candidate}) / max(
        usable, 1
    )
    verdict, reasons = _verdict(
        usable=usable,
        mixin_share=mixin_share,
        distinct_plants=distinct_plants,
        failed=failed,
    )

    audit = {
        "kind": "thalassia-audit",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "root": str(args.root),
        "candidate": CANDIDATE,
        "max_distance": args.max_distance,
        "candidate_images": len(candidates),
        "candidate_by_variant": dict(variant_counts),
        "qc_pass": usable,
        "qc_reasons": dict(qc_reasons),
        "hash_failures": failed,
        "reference_images": len(references),
        "near_duplicate_pairs_with_other_classes": len(cross_class),
        "candidate_frames_matching_another_class": len(suspicious_candidate),
        "mixin_share": round(mixin_share, 4),
        "absorbed_by": dict(absorbed.most_common()),
        "candidate_internal_duplicate_pairs": len(within_candidate),
        "distinct_candidate_plants": distinct_plants,
        "median_group_size": _median(
            [float(size) for size in group_sizes.values()]
        ),
        "provenance": {
            "camera_models": dict(models.most_common(10)),
            "dated_frames": len(dated),
            "earliest": min(dated).isoformat() if dated else None,
            "latest": max(dated).isoformat() if dated else None,
            "gps_share": round(gps_share, 3),
        },
        "verdict": verdict,
        "verdict_reasons": reasons,
        "note": (
            "Read-only. A 'review' verdict means the frames below the distance "
            "cutoff need a human pass before the class is trained; it is not a "
            "rejection of the class. This scan detects duplicate frames, not "
            "taxa: a Thalassia photo misfiled under Enhalus is only caught when "
            "a near-identical file also exists in a Thalassia folder. The "
            "sampled human pass is what covers the rest."
        ),
    }

    args.out.mkdir(parents=True, exist_ok=True)
    json_path = args.out / "thalassia_audit.json"
    csv_path = args.out / "thalassia_review.csv"
    json_path.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "distance",
                "candidate",
                "candidate_folder",
                "closest_class",
                "closest_path",
                "closest_folder",
            ],
        )
        writer.writeheader()
        for row in review_rows[: args.review_limit]:
            writer.writerow(row)

    print()
    print(f"usable frames            {usable}")
    print(f"distinct plants (pHash)  {distinct_plants}")
    print(f"cross-class near-dup pairs {len(cross_class)}")
    print(f"candidate frames flagged {len(suspicious_candidate)} ({mixin_share:.1%})")
    if absorbed:
        print("absorbed by:")
        for slug, count in absorbed.most_common():
            print(f"  {slug:26s} {count:4d}")
    print(f"camera models            {dict(models.most_common(5)) or 'none in EXIF'}")
    print()
    print(f"VERDICT: {verdict}")
    for reason in reasons:
        print(f"  - {reason}")
    print()
    print(f"wrote {json_path}")
    print(f"wrote {csv_path}")


def _verdict(
    *,
    usable: int,
    mixin_share: float,
    distinct_plants: int,
    failed: int,
) -> tuple[str, list[str]]:
    """Decision aid only. The team decides; this states what the numbers say."""
    reasons: list[str] = []
    if failed:
        reasons.append(f"{failed} files could not be hashed (corrupt or unreadable)")

    if usable < 100:
        reasons.append(
            f"only {usable} usable frames; under 100 the class will be a scarcity "
            "problem even after the audit"
        )
    if mixin_share >= 0.10:
        reasons.append(
            f"{mixin_share:.1%} of candidate frames near-duplicate another species "
            "folder; inspect the review CSV before training"
        )
    elif mixin_share > 0.02:
        reasons.append(
            f"{mixin_share:.1%} of candidate frames match another class; a sample "
            "review is enough, do not skip it"
        )
    if distinct_plants < 0.5 * usable:
        reasons.append(
            f"{distinct_plants} distinct plants for {usable} frames; the effective "
            "sample size is well below the file count"
        )

    if mixin_share >= 0.10 or usable < 100:
        return "review", reasons or ["insufficient evidence to admit the class"]
    if mixin_share > 0.02 or distinct_plants < 0.5 * usable:
        return "review", reasons
    return "clean", reasons or ["no cross-class near-duplicates above the cutoff"]


if __name__ == "__main__":
    main()
