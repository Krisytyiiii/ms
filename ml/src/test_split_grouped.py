"""Grouped split: no observation may appear on two sides.

If this test passes, `train_curated.py --split grouped` is safe to run. If it
fails, the "honest" number would still contain near-duplicate leakage.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.split import split_labels_grouped  # noqa: E402


def _synthetic(per_class: int = 10, classes: int = 8, per_group: int = 4):
    items = []
    labels = []
    groups = []
    group = 0
    for class_index in range(classes):
        slug = f"species_{class_index}"
        for index in range(per_class):
            items.append(f"{slug}/img{index}.jpg")
            labels.append(slug)
            groups.append(group)
            if (index + 1) % per_group == 0:
                group += 1
    return items, labels, groups


def test_no_group_spans_two_splits() -> None:
    items, labels, groups = _synthetic()
    train, val, test, train_y, val_y, test_y, report = split_labels_grouped(
        items, labels, groups, seed=42
    )

    train_groups = {groups[items.index(item)] for item in train}
    val_groups = {groups[items.index(item)] for item in val}
    test_groups = {groups[items.index(item)] for item in test}

    assert not (train_groups & val_groups)
    assert not (train_groups & test_groups)
    assert not (val_groups & test_groups)
    assert report["group_leaks"] == 0


def test_every_item_lands_exactly_once() -> None:
    items, labels, groups = _synthetic()
    train, val, test, *_rest = split_labels_grouped(items, labels, groups, seed=42)
    assert len(train) + len(val) + len(test) == len(items)
    assert sorted(train + val + test) == sorted(items)


def test_ratios_are_near_seventy_fifteen_fifteen() -> None:
    items, labels, groups = _synthetic(per_class=20, classes=8, per_group=2)
    _train, _val, _test, _ty, _vy, _sy, report = split_labels_grouped(
        items, labels, groups, seed=42
    )
    ratios = report["ratios"]
    assert 0.60 <= ratios["train"] <= 0.80
    assert 0.10 <= ratios["val"] <= 0.20
    assert 0.10 <= ratios["test"] <= 0.20
    assert report["mode"] == "grouped-stratified"


def test_labels_stay_aligned_with_items() -> None:
    items, labels, groups = _synthetic()
    train, val, test, train_y, val_y, test_y, _report = split_labels_grouped(
        items, labels, groups, seed=42
    )
    for item, label in zip(train, train_y):
        assert item.split("/")[0] == label
    for item, label in zip(val, val_y):
        assert item.split("/")[0] == label
    for item, label in zip(test, test_y):
        assert item.split("/")[0] == label


def test_few_groups_reduce_the_fold_count_instead_of_crashing() -> None:
    items = [f"a/img{index}.jpg" for index in range(6)]
    labels = ["a"] * 6
    groups = [0, 0, 1, 1, 2, 2]
    train, val, test, *_rest = split_labels_grouped(items, labels, groups, seed=42)
    assert train and val and test


def test_two_groups_is_an_error() -> None:
    with pytest.raises(ValueError):
        split_labels_grouped(["a", "b"], ["x", "x"], [0, 1], seed=42)


def test_mismatched_lengths_are_an_error() -> None:
    with pytest.raises(ValueError):
        split_labels_grouped(["a", "b"], ["x"], [0, 1], seed=42)


def test_a_class_with_one_group_marks_the_split_degraded() -> None:
    """Coverage the groups do not allow is reported, not hidden.

    Class `b` exists as a single observation, so it can land in val or test but
    never both. The split must still be produced, with `degraded` set and the
    class named, so nobody quotes the macro F1 as if every class were held out.
    """
    items = [f"a{i}.jpg" for i in range(4)] + ["b0.jpg", "b1.jpg"]
    labels = ["a"] * 4 + ["b"] * 2
    groups = [0, 0, 1, 1, 2, 2]
    report = split_labels_grouped(items, labels, groups, seed=42)[-1]
    assert report["degraded"] is True
    assert "b" in report["classes_with_single_group"]
    assert (
        "b" in report["classes_missing_from_val"]
        or "b" in report["classes_missing_from_test"]
    )


def test_a_split_that_covers_every_class_is_not_degraded() -> None:
    items, labels, groups = _synthetic(per_class=20, classes=8, per_group=2)
    report = split_labels_grouped(items, labels, groups, seed=42)[-1]
    assert report["degraded"] is False
    assert report["classes_with_single_group"] == []
    assert set(report["folds_used"]) == {"test", "val"}

