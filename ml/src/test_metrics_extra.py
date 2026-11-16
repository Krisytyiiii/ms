"""Multiclass metrics: the numbers the result chapter should quote.

Hand-computed expectations, so a change in the reporting code cannot quietly
inflate a score.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.metrics_extra import (  # noqa: E402
    balanced_accuracy,
    build_summary,
    coverage_accuracy_table,
    grouped_bootstrap_ci,
    per_class_table,
    top_k_accuracy,
)


def test_top_k_uses_the_shortlist() -> None:
    classes = ["a", "b", "c"]
    probabilities = np.array(
        [
            [0.6, 0.3, 0.1],  # truth a -> top1
            [0.6, 0.3, 0.1],  # truth b -> top2 only
            [0.6, 0.3, 0.1],  # truth c -> neither
        ]
    )
    labels = ["a", "b", "c"]
    assert top_k_accuracy(probabilities, classes, labels, k=1) == pytest.approx(1 / 3)
    assert top_k_accuracy(probabilities, classes, labels, k=2) == pytest.approx(2 / 3)
    assert top_k_accuracy(probabilities, classes, labels, k=3) == pytest.approx(1.0)


def test_balanced_accuracy_ignores_class_size() -> None:
    # "big" is right 3/4, "small" is right 0/1 -> (0.75 + 0.0) / 2
    labels = ["big", "big", "big", "big", "small"]
    predictions = ["big", "big", "big", "other", "other"]
    assert balanced_accuracy(labels, predictions) == pytest.approx(0.375)


def test_balanced_accuracy_differs_from_accuracy_when_classes_are_lopsided() -> None:
    labels = ["big"] * 10 + ["small"]
    predictions = ["big"] * 10 + ["big"]
    accuracy = 10 / 11
    assert balanced_accuracy(labels, predictions) == pytest.approx(0.5)
    assert accuracy > 0.9  # the flattering number


def test_per_class_table_flags_uninterpretable_support() -> None:
    labels = ["a"] * 25 + ["b"] * 4
    predictions = ["a"] * 25 + ["a"] * 4
    rows = {row["class"]: row for row in per_class_table(labels, predictions)}
    assert rows["a"]["recall"] == pytest.approx(1.0)
    assert rows["a"]["interpretable"] is True
    assert rows["b"]["recall"] == pytest.approx(0.0)
    assert rows["b"]["interpretable"] is False
    assert rows["b"]["support"] == 4


def test_coverage_shrinks_as_the_threshold_rises() -> None:
    confidence = np.array([0.9, 0.8, 0.5, 0.3])
    correct = np.array([True, False, True, False])
    table = coverage_accuracy_table(confidence, correct, thresholds=(0.4, 0.6, 0.95))
    coverages = [row["coverage"] for row in table]
    assert coverages[0] == pytest.approx(0.75)
    assert coverages[1] == pytest.approx(0.5)
    assert coverages[2] == pytest.approx(0.0)
    assert table[0]["accuracy"] == pytest.approx(2 / 3)
    assert table[1]["accuracy"] == pytest.approx(0.5)
    assert table[2]["accuracy"] is None


def test_grouped_bootstrap_point_is_the_plain_accuracy() -> None:
    correct = np.array([1, 0, 1, 1, 0, 1], dtype=float)
    groups = [0, 0, 1, 1, 2, 2]
    ci = grouped_bootstrap_ci(correct, groups, n_boot=500, seed=7)
    assert ci["point"] == pytest.approx(correct.mean())
    assert ci["groups"] == 3
    assert ci["low"] <= ci["point"] <= ci["high"]


def test_grouped_bootstrap_widens_when_groups_are_coherent() -> None:
    # Two coherent groups of 10: every resample is 0.5 or 1.0, so the interval
    # must be wide even though n = 20 looks comfortable.
    correct = np.array([1] * 10 + [0] * 10, dtype=float)
    coherent = [0] * 10 + [1] * 10
    independent = list(range(20))
    wide = grouped_bootstrap_ci(correct, coherent, n_boot=500, seed=7)
    narrow = grouped_bootstrap_ci(correct, independent, n_boot=500, seed=7)
    assert (wide["high"] - wide["low"]) > (narrow["high"] - narrow["low"])


def test_build_summary_reports_the_whole_set() -> None:
    classes = ["a", "b", "c", "d"]
    probabilities = np.array(
        [
            [0.70, 0.20, 0.05, 0.05],
            [0.10, 0.60, 0.20, 0.10],
            [0.10, 0.20, 0.60, 0.10],
            [0.05, 0.05, 0.20, 0.70],
        ]
    )
    labels = ["a", "b", "c", "a"]
    groups = [0, 1, 2, 2]
    summary = build_summary(probabilities, classes, labels, groups=groups)
    assert summary["accuracy"] == pytest.approx(0.75)
    # recall: a 1/2, b 1/1, c 1/1 -> mean 0.8333
    assert summary["balanced_accuracy"] == pytest.approx((0.5 + 1.0 + 1.0) / 3)
    # the last row is a confident "d" for an "a" photo, so only 3 of 4 rows
    # have the truth in the top 2 or top 3
    assert summary["top2_accuracy"] == pytest.approx(0.75)
    assert summary["top3_accuracy"] == pytest.approx(0.75)
    assert summary["n"] == 4
    assert "accuracy_ci" in summary
    assert len(summary["coverage_accuracy"]) == len(
        build_summary(probabilities, classes, labels)["coverage_accuracy"]
    )
    assert {row["class"] for row in summary["per_class"]} == {"a", "b", "c"}


def test_build_summary_without_groups_has_no_interval() -> None:
    probabilities = np.array([[0.9, 0.1], [0.2, 0.8]])
    summary = build_summary(probabilities, ["a", "b"], ["a", "b"])
    assert "accuracy_ci" not in summary
    assert summary["accuracy"] == pytest.approx(1.0)


def test_summary_uses_the_shipped_predictions_not_the_argmax() -> None:
    # Row 0: the vote says "b", the probability argmax says "a". The shipped
    # rule is the vote, so this row must count as wrong.
    probabilities = np.array([[0.45, 0.40], [0.2, 0.8]])
    summary = build_summary(
        probabilities, ["a", "b"], ["a", "b"], predictions=["b", "b"]
    )
    assert summary["decision_rule"] == "one_vs_one_vote"
    assert summary["accuracy"] == pytest.approx(0.5)
    # A single row is its own class here, so balanced accuracy is 0.5 as well.
    assert summary["balanced_accuracy"] == pytest.approx(0.5)
    # The confidence gate must read the voted class's probability, not the top
    # one: row 0's vote "b" carries 0.40, so a 0.44 gate rejects that row.
    at_44 = [row for row in summary["coverage_accuracy"] if row["threshold"] == 0.44]
    assert at_44 and at_44[0]["coverage"] == pytest.approx(0.5)
    assert at_44[0]["accuracy"] == pytest.approx(1.0)
    at_40 = [row for row in summary["coverage_accuracy"] if row["threshold"] == 0.40]
    assert at_40 and at_40[0]["coverage"] == pytest.approx(1.0)


def test_summary_says_when_it_fell_back_to_the_argmax() -> None:
    probabilities = np.array([[0.9, 0.1], [0.2, 0.8]])
    summary = build_summary(probabilities, ["a", "b"], ["a", "b"])
    assert summary["decision_rule"] == "probability_argmax"
