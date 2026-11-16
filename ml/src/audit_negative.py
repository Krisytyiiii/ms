"""What does the model say about photos that are *not* one of the nine species?

The SVM has no "none of the above" option, so every photo becomes a species
call. This audit takes a folder of negatives (sand, rocks, hands, jetty, fish,
seaweed, land plants) and measures the two things a panel will ask:

- **false accept rate** - how often a non-target photo is named a species at all,
  and how often it clears the shipped confidence gate.
- **would a plant-evidence check catch it?** - the green-mask coverage from
  `leaf_focus.plant_fraction`, which is a cheap pre-check rather than a second
  classifier. Its *cost* is reported too: measured on 504 real seagrass photos,
  a 0.05 cut refuses 34% of genuine blades, so the catch rate is only meaningful
  next to the false-reject rate.

Nothing here changes the model. It measures the gap so the claim "it rejects
non-seagrass" can either be earned or dropped.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from identify import default_model_path, identify_path, load_model, sidecar
from leaf_focus import plant_fraction
from preprocess import load_rgb_full

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}

# Measured 16 Nov 2026 on 504 real seagrass photos (60 per class, random sample
# of the `(all)` pools): the share of GENUINE seagrass frames a green-mask cut
# would refuse. Without this number a catch rate on negatives is a half-truth.
REAL_SEAGRASS_FALSE_REJECT = {
    0.01: 0.153,
    0.02: 0.216,
    0.03: 0.290,
    0.05: 0.343,
    0.10: 0.450,
}


def false_reject_rate(plant_min: float) -> float | None:
    """Real seagrass photos a `plant_min` cut would refuse (interpolated)."""
    cuts = np.array(sorted(REAL_SEAGRASS_FALSE_REJECT), dtype=float)
    rates = np.array([REAL_SEAGRASS_FALSE_REJECT[c] for c in cuts], dtype=float)
    if plant_min < cuts[0] or plant_min > cuts[-1]:
        return None
    return float(np.interp(plant_min, cuts, rates))



def image_files(folder: Path) -> list[Path]:
    """Every image under `folder`, sorted, so a run is reproducible."""
    return sorted(
        path
        for path in Path(folder).rglob("*")
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    )


def measure(path: Path, model, threshold: float) -> dict:
    """One negative photo: what the model said, and how much plant was in it."""
    result = identify_path(Path(path), model=model)
    fraction = float(plant_fraction(load_rgb_full(Path(path))))
    return {
        "path": str(path),
        "slug": result["slug"],
        "confidence": float(result["confidence"]),
        "accepted": bool(float(result["confidence"]) >= threshold),
        "plant_fraction": fraction,
        "top": result["top"][:3],
    }


def summarise(rows: list[dict], threshold: float, plant_min: float) -> dict:
    """Counts and rates for a whole negative set."""
    n = len(rows)
    if not n:
        return {"n": 0, "threshold": threshold, "plant_min": plant_min}
    accepted = [row for row in rows if row["accepted"]]
    caught = [row for row in rows if row["plant_fraction"] < plant_min]
    confidence = np.array([row["confidence"] for row in rows], dtype=float)
    fractions = np.array([row["plant_fraction"] for row in rows], dtype=float)
    slugs: dict[str, int] = {}
    for row in rows:
        slugs[row["slug"]] = slugs.get(row["slug"], 0) + 1
    return {
        "n": n,
        "threshold": threshold,
        "plant_min": plant_min,
        "named_a_species": n,
        "accepted": len(accepted),
        "false_accept_rate": len(accepted) / n,
        "accepted_by_plant_check": len(caught),
        "plant_check_catch_rate": len(caught) / n,
        "residual_false_accept_rate": sum(
            1 for row in accepted if row["plant_fraction"] >= plant_min
        )
        / n,
        "confidence_mean": float(confidence.mean()),
        "confidence_p90": float(np.quantile(confidence, 0.9)),
        "plant_fraction_mean": float(fractions.mean()),
        "top_species": sorted(slugs.items(), key=lambda item: item[1], reverse=True)[:5],
    }


def _cost(plant_min: float) -> str:
    rate = false_reject_rate(plant_min)
    if rate is None:
        return "not measured at this cut"
    return f"{rate:.1%}"


def render(summary: dict) -> str:
    if not summary["n"]:
        return "No images found."
    lines = [
        f"Negatives: **{summary['n']}** photos, confidence gate {summary['threshold']:.2f}, "
        f"plant-evidence cut {summary['plant_min']:.2f}",
        "",
        "| measure | value |",
        "|---|---:|",
        f"| named one of the nine species | {summary['named_a_species']} "
        f"({summary['named_a_species'] / summary['n']:.1%}) |",
        f"| cleared the confidence gate (false accept) | {summary['accepted']} "
        f"({summary['false_accept_rate']:.1%}) |",
        f"| would be caught by the plant-evidence check | "
        f"{summary['accepted_by_plant_check']} ({summary['plant_check_catch_rate']:.1%}) |",
        f"| **cost: real seagrass photos that same cut would refuse** | "
        f"{_cost(summary['plant_min'])} |",
        f"| **still falsely accepted after both checks** | "
        f"{summary['residual_false_accept_rate']:.1%} |",
        f"| mean confidence | {summary['confidence_mean']:.3f} |",
        f"| 90th-percentile confidence | {summary['confidence_p90']:.3f} |",
        f"| mean plant fraction | {summary['plant_fraction_mean']:.3f} |",
    ]
    if summary["top_species"]:
        lines.extend(["", "| species named | count |", "|---|---:|"])
        for slug, count in summary["top_species"]:
            lines.append(f"| {slug} | {count} |")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("images", type=Path, help="folder of non-target photos")
    parser.add_argument("--model", type=Path, default=None, help="joblib model")
    parser.add_argument("--threshold", type=float, default=None)
    parser.add_argument("--plant-min", type=float, default=0.02)
    parser.add_argument("--json", type=Path, default=None, help="write the table here")
    args = parser.parse_args(argv)

    model = load_model(args.model) if args.model else load_model()
    model_path = args.model or default_model_path()
    threshold = args.threshold
    if threshold is None:
        threshold = float(sidecar(model_path).get("threshold", 0.44))
    rows = [measure(path, model, threshold) for path in image_files(args.images)]
    summary = summarise(rows, threshold, args.plant_min)
    print(render(summary))
    if args.json:
        args.json.write_text(
            json.dumps({"summary": summary, "rows": rows}, indent=2), encoding="utf-8"
        )
        print("wrote", args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
