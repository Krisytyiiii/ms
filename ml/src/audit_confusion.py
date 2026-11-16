"""Where do the species collapse? Read a run record's test confusion matrix.

The per-class precision/recall table says *that* a class is weak; the
off-diagonal cells say *which* class absorbed it. Two views, both from the same
matrix:

- **biggest confusions** - the largest true -> predicted cells, with the share
  of that class's test photos they represent.
- **absorbers** - for each predicted class, how many wrong photos it took in,
  which is where a "fix the confusion" data effort should go.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load(path: Path) -> tuple[list[str], list[list[int]]]:
    record = json.loads(Path(path).read_text(encoding="utf-8"))
    labels = list(record.get("classes") or [])
    matrix = record.get("confusion_matrix_test")
    if not labels or not matrix:
        raise SystemExit(f"{path} has no classes/confusion_matrix_test")
    if len(matrix) != len(labels) or any(len(row) != len(labels) for row in matrix):
        raise SystemExit(f"{path}: confusion matrix is not {len(labels)}x{len(labels)}")
    return labels, matrix


def confusions(
    labels: list[str], matrix: list[list[int]], top: int = 20
) -> list[dict]:
    """Off-diagonal cells, largest first, with each one's share of its true class."""
    rows = []
    for true_index, true_name in enumerate(labels):
        support = sum(matrix[true_index])
        for predicted_index, predicted_name in enumerate(labels):
            if true_index == predicted_index:
                continue
            count = int(matrix[true_index][predicted_index])
            if not count:
                continue
            rows.append(
                {
                    "true": true_name,
                    "predicted": predicted_name,
                    "count": count,
                    "support": support,
                    "share": count / support if support else 0.0,
                }
            )
    rows.sort(key=lambda row: (row["count"], row["share"]), reverse=True)
    return rows[:top]


def absorbers(labels: list[str], matrix: list[list[int]]) -> list[dict]:
    """For each predicted class, how many photos it took that were another species."""
    rows = []
    for predicted_index, predicted_name in enumerate(labels):
        wrong = sum(
            matrix[true_index][predicted_index]
            for true_index in range(len(labels))
            if true_index != predicted_index
        )
        correct = matrix[predicted_index][predicted_index]
        rows.append(
            {
                "predicted": predicted_name,
                "wrong": int(wrong),
                "correct": int(correct),
                "precision": correct / (correct + wrong) if correct + wrong else 0.0,
            }
        )
    rows.sort(key=lambda row: row["wrong"], reverse=True)
    return rows


def render(labels: list[str], matrix: list[list[int]], top: int = 12) -> str:
    lines = [
        "| true species | predicted as | count | share of true class |",
        "|---|---|---:|---:|",
    ]
    for row in confusions(labels, matrix, top=top):
        lines.append(
            f"| {row['true']} | {row['predicted']} | {row['count']} | {row['share']:.0%} |"
        )
    lines.extend(
        [
            "",
            "| predicted species | wrong photos absorbed | correct | precision |",
            "|---|---:|---:|---:|",
        ]
    )
    for row in absorbers(labels, matrix):
        lines.append(
            f"| {row['predicted']} | {row['wrong']} | {row['correct']} | {row['precision']:.3f} |"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path, help="run record.json")
    parser.add_argument("--top", type=int, default=12)
    parser.add_argument("--csv", type=Path, default=None, help="write the pairs here")
    args = parser.parse_args(argv)
    labels, matrix = load(args.record)
    print(render(labels, matrix, top=args.top))
    if args.csv:
        rows = confusions(labels, matrix, top=len(labels) ** 2)
        import csv

        with args.csv.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        print("wrote", args.csv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
