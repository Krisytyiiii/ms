"""How much of a real seagrass photo does the green mask cover?

This is the number that decides whether a "no leaf detected" pre-check is safe.
The answer, measured on the 16 Nov 2026 mirror, is that it is **not**: a 0.05
cut refuses 34% of genuine seagrass photos, and the classes differ by an order
of magnitude (`halodule_pinifolia` median 0.024 versus `syringodium` 0.294).

Run it against the dataset root to reproduce the table in
`docs/22-accuracy-plan.md`:

    python ml/src/audit_plant_fraction.py C:/Users/Akiro/MarineSeeData/Seagrass

Nothing here trains or changes a model.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

import numpy as np

try:  # imported as `ml.src.audit_plant_fraction` (tests, REPL)
    from .inventory import iter_images, species_folders
    from .leaf_focus import plant_fraction
    from .preprocess import load_rgb_full
except ImportError:  # run as a script from `ml/src`
    from inventory import iter_images, species_folders
    from leaf_focus import plant_fraction
    from preprocess import load_rgb_full

CUTS = (0.01, 0.02, 0.03, 0.05, 0.10)
SEED = 11


def summarise(values: dict[str, list[float]], cuts: tuple[float, ...] = CUTS) -> dict:
    """False-reject table from per-class `plant_fraction` values."""
    everything = np.array([v for vals in values.values() for v in vals], dtype=float)
    if everything.size == 0:
        return {"n": 0, "cuts": []}
    return {
        "n": int(everything.size),
        "cuts": [
            {"cut": float(cut), "false_reject": float((everything < cut).mean())}
            for cut in cuts
        ],
        "per_class": {
            slug: {
                "n": len(vals),
                "median": float(np.median(vals)),
                "under_005": float((np.array(vals) < 0.05).mean()),
            }
            for slug, vals in sorted(values.items())
        },
    }


def measure(root: Path, limit: int = 60, seed: int = SEED) -> dict[str, list[float]]:
    """Sample up to `limit` real photos per class and score the green mask."""
    rng = random.Random(seed)
    values: dict[str, list[float]] = {}
    for folder, slug, variant in species_folders(Path(root)):
        if "all" not in variant:
            continue
        files = list(iter_images(folder))
        if not files:
            continue
        picked = files if len(files) <= limit else rng.sample(files, limit)
        got: list[float] = []
        for path in picked:
            try:
                got.append(float(plant_fraction(load_rgb_full(path))))
            except Exception:  # an unreadable frame must not abort the audit
                continue
        if got:
            values.setdefault(slug, []).extend(got)
    return values


def render(summary: dict) -> str:
    if not summary["n"]:
        return "No images measured."
    lines = [
        f"Real seagrass photos measured: **{summary['n']}**",
        "",
        "| plant_fraction cut | real seagrass photos refused |",
        "|---|---:|",
    ]
    for row in summary["cuts"]:
        lines.append(f"| {row['cut']:.2f} | {row['false_reject']:.1%} |")
    lines.extend(["", "| class | n | median | under 0.05 |", "|---|---:|---:|---:|"])
    for slug, stats in summary["per_class"].items():
        lines.append(
            f"| {slug} | {stats['n']} | {stats['median']:.3f} | {stats['under_005']:.1%} |"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, help="dataset root (folder of species folders)")
    parser.add_argument("--limit", type=int, default=60, help="photos per class")
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--json", type=Path, default=None)
    args = parser.parse_args(argv)

    values = measure(args.root, args.limit, args.seed)
    summary = summarise(values)
    print(render(summary))
    if args.json:
        args.json.write_text(
            json.dumps({"summary": summary, "values": values}, indent=2), encoding="utf-8"
        )
        print("wrote", args.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
