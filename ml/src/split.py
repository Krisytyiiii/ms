"""Stratified 70 / 15 / 15 split, and a grouped variant that does not leak.

The plain `split_labels` splits by image. Frames from the same photoshoot are
then near-duplicates of each other sitting on both sides of the split, which
inflates the held-out score. `split_labels_grouped` keeps a whole observation
in one split, at 71.4 / 14.3 / 14.3 (7 folds: 1 test, 1 val, 5 train), which is
the closest honest ratio to 70/15/15 that grouped stratification allows.
"""

from __future__ import annotations

from collections import Counter

from sklearn.model_selection import StratifiedGroupKFold, train_test_split

from .dataset_contract import SPLIT_SEED


def split_labels(
    items: list,
    labels: list[str],
    seed: int = SPLIT_SEED,
) -> tuple[list, list, list, list[str], list[str], list[str]]:
    temp_items, test_items, temp_y, test_y = train_test_split(
        items,
        labels,
        test_size=0.15,
        stratify=labels,
        random_state=seed,
    )
    val_ratio = 0.15 / 0.85
    train_items, val_items, train_y, val_y = train_test_split(
        temp_items,
        temp_y,
        test_size=val_ratio,
        stratify=temp_y,
        random_state=seed,
    )
    return train_items, val_items, test_items, train_y, val_y, test_y


def _take(items: list, index: list[int]) -> list:
    return [items[i] for i in index]


def split_labels_grouped(
    items: list,
    labels: list[str],
    groups: list[int],
    seed: int = SPLIT_SEED,
) -> tuple[list, list, list, list[str], list[str], list[str], dict]:
    """Grouped stratified 71.4 / 14.3 / 14.3 split.

    `groups` must be observation ids: an image and its near-duplicates share
    one id. Every item of a group lands in exactly one split.

    Returns the same six lists as `split_labels` plus a report dict that records
    the achieved ratios, the per-class counts, and a leak check (which must be
    zero). The report belongs in `metrics.json` so the split is auditable.

    `degraded` is the flag that matters when reading the resulting score: it is
    true when a class present in the pool is absent from val or test. Grouped
    splitting cannot promise class coverage the groups do not allow, so the
    number is still produced -- but the report says so, and `train_curated.py`
    prints a warning rather than letting the macro F1 read as if every class
    had been tested.
    """
    if len(items) != len(labels) or len(items) != len(groups):
        raise ValueError(
            "items, labels and groups must be the same length "
            f"({len(items)}, {len(labels)}, {len(groups)})"
        )
    if not items:
        raise ValueError("no items to split")

    n_groups = len(set(groups))
    if n_groups < 3:
        raise ValueError(f"need at least 3 observation groups, got {n_groups}")

    n_splits = 7
    if n_groups < n_splits:
        n_splits = max(3, n_groups)

    splitter = StratifiedGroupKFold(
        n_splits=n_splits,
        shuffle=True,
        random_state=seed,
    )
    folds = [test_index for _train, test_index in splitter.split(items, labels, groups)]

    # Which fold is val and which is test is not arbitrary: with coarse groups
    # (or few of them) one choice can leave a split holding a single class.
    # Pick the pair that covers the most classes, then the most even sizes.
    all_classes = set(labels)
    expected = len(items) / n_splits
    best = None
    for test_fold in range(n_splits):
        for val_fold in range(n_splits):
            if test_fold == val_fold:
                continue
            test_index = folds[test_fold]
            val_index = folds[val_fold]
            test_classes = {labels[i] for i in test_index}
            val_classes = {labels[i] for i in val_index}
            balance = -abs(len(test_index) - expected) - abs(len(val_index) - expected)
            score = (
                len((test_classes | val_classes) & all_classes),
                len(test_classes),
                len(val_classes),
                balance,
            )
            if best is None or score > best[0]:
                best = (score, test_fold, val_fold)

    assert best is not None
    _score, test_fold, val_fold = best
    test_index = list(folds[test_fold])
    val_index = list(folds[val_fold])
    held = set(test_index) | set(val_index)
    train_index = [i for i in range(len(items)) if i not in held]

    if not train_index or not val_index or not test_index:
        raise ValueError(
            "grouped split produced an empty part "
            f"(train {len(train_index)}, val {len(val_index)}, test {len(test_index)})"
        )

    train_items, val_items, test_items = (
        _take(items, train_index),
        _take(items, val_index),
        _take(items, test_index),
    )
    train_y = _take(labels, train_index)
    val_y = _take(labels, val_index)
    test_y = _take(labels, test_index)

    def _groups_of(index: list[int]) -> set[int]:
        return {groups[i] for i in index}

    train_groups = _groups_of(train_index)
    val_groups = _groups_of(val_index)
    test_groups = _groups_of(test_index)
    leaks = (
        len(train_groups & val_groups)
        + len(train_groups & test_groups)
        + len(val_groups & test_groups)
    )
    if leaks:
        raise ValueError(f"group leak: {leaks} observation(s) span two splits")

    total = len(items)
    missing_from_test = sorted(set(labels) - set(test_y))
    missing_from_val = sorted(set(labels) - set(val_y))
    seen: dict[str, set[int]] = {}
    for index, label in enumerate(labels):
        seen.setdefault(label, set()).add(groups[index])
    groups_per_class = {label: len(ids) for label, ids in seen.items()}
    report = {
        "mode": "grouped-stratified",
        "n_splits": n_splits,
        "n_items": total,
        "n_groups": n_groups,
        "n_train": len(train_index),
        "n_val": len(val_index),
        "n_test": len(test_index),
        "ratios": {
            "train": round(len(train_index) / total, 4),
            "val": round(len(val_index) / total, 4),
            "test": round(len(test_index) / total, 4),
        },
        "groups": {
            "train": len(train_groups),
            "val": len(val_groups),
            "test": len(test_groups),
        },
        "class_counts": {
            "train": dict(Counter(train_y)),
            "val": dict(Counter(val_y)),
            "test": dict(Counter(test_y)),
        },
        "classes_missing_from_test": missing_from_test,
        "classes_missing_from_val": missing_from_val,
        "degraded": bool(missing_from_test or missing_from_val),
        "classes_with_single_group": sorted(
            label for label, count in groups_per_class.items() if count < 2
        ),
        "folds_used": {"test": test_fold, "val": val_fold},
        "group_leaks": leaks,
        "seed": seed,
    }
    return train_items, val_items, test_items, train_y, val_y, test_y, report
