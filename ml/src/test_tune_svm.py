"""Tuning picks on validation only and never needs the test split."""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.tune_svm import (  # noqa: E402
    best,
    best_1se,
    best_params,
    candidate_params,
    flexibility,
    grouped_folds,
    search,
    search_grouped_cv,
)


def _blobs(seed: int, n: int) -> tuple[np.ndarray, list[str]]:
    rng = np.random.default_rng(seed)
    centers = {"a": (0.0, 0.0), "b": (4.0, 4.0), "c": (0.0, 4.0)}
    rows, labels = [], []
    for label, center in centers.items():
        rows.append(rng.normal(center, 1.0, size=(n, 2)))
        labels += [label] * n
    return np.vstack(rows), labels


def test_grid_has_rbf_and_linear() -> None:
    kernels = {row["kernel"] for row in candidate_params()}
    assert kernels == {"rbf", "linear"}


def test_search_scores_val_and_picks_best() -> None:
    x_train, y_train = _blobs(1, 30)
    x_val, y_val = _blobs(2, 10)
    grid = [
        {"kernel": "rbf", "C": 0.1, "gamma": 0.001},
        {"kernel": "rbf", "C": 10.0, "gamma": "scale"},
    ]
    rows = search(x_train, y_train, x_val, y_val, grid=grid)
    assert len(rows) == 2
    assert all(0.0 <= row["val_macro_f1"] <= 1.0 for row in rows)
    chosen = best(rows)
    assert chosen["val_macro_f1"] == max(row["val_macro_f1"] for row in rows)
    assert set(best_params(rows)) == {"kernel", "C", "gamma"}


def test_grouped_folds_keep_an_observation_in_one_fold() -> None:
    _x, labels = _blobs(4, 12)
    groups = [index // 4 for index in range(len(labels))]  # 3 frames per shoot
    folds = grouped_folds(labels, groups, n_splits=3, seed=1)
    assert len(folds) == 3
    for train_index, val_index in folds:
        train_groups = {groups[int(i)] for i in train_index}
        val_groups = {groups[int(i)] for i in val_index}
        assert not (train_groups & val_groups)


def test_grouped_cv_reports_mean_and_spread() -> None:
    x, labels = _blobs(5, 12)
    groups = [index // 3 for index in range(len(labels))]
    grid = [
        {"kernel": "rbf", "C": 0.1, "gamma": 0.001},
        {"kernel": "linear", "C": 0.1, "gamma": None},
    ]
    rows = search_grouped_cv(x, labels, groups, grid=grid, n_splits=3, seed=2)
    assert len(rows) == 2
    for row in rows:
        assert row["cv_folds"] == 3
        assert row["cv_macro_f1_se"] >= 0.0
        assert len(row["cv_macro_f1_folds"]) == 3


def test_one_se_rule_prefers_the_simpler_candidate() -> None:
    rows = [
        {"kernel": "rbf", "C": 100.0, "gamma": 0.1,
         "cv_macro_f1_mean": 0.60, "cv_macro_f1_se": 0.05, "cv_accuracy_mean": 0.6},
        {"kernel": "linear", "C": 0.1, "gamma": None,
         "cv_macro_f1_mean": 0.56, "cv_macro_f1_se": 0.05, "cv_accuracy_mean": 0.55},
    ]
    chosen = best_1se(rows)
    assert chosen["kernel"] == "linear"
    assert flexibility(chosen) < flexibility(rows[0])
