"""Pick SVM kernel, C, and gamma on grouped cross-validation.

Two modes:

* `search` fits each candidate on one train split and scores the untouched
  validation split. That is the original behaviour and stays as the reference.
* `search_grouped_cv` repeats `StratifiedGroupKFold` on the real training rows,
  so a candidate is scored on several held-out observations instead of one
  233-row split, and reports mean +/- SE. `best_1se` then takes the **least
  flexible** candidate within one standard error of the best, which is the
  one-standard-error rule `docs/22-accuracy-plan.md` action 2.3 asks for.

The test split is never read here. Selection metric is macro F1 so small
species count as much as large ones.
"""

from __future__ import annotations

import math
import time
from collections.abc import Callable, Iterable

import numpy as np
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import StratifiedGroupKFold

from .dataset_contract import SPLIT_SEED
from .train_svm import make_pipeline

RBF_C = (0.1, 0.3, 1.0, 3.0, 10.0, 30.0, 100.0)
RBF_GAMMA: tuple[str | float, ...] = ("scale", 0.001, 0.003, 0.01, 0.03, 0.1)
LINEAR_C = (0.01, 0.03, 0.1, 0.3, 1.0)
SELECTION_METRIC = "val_macro_f1"
CV_METRIC = "cv_macro_f1_mean"

TUNING_SPEC = {
    "split": "fixed 15% validation, or grouped k-fold",
    "metric": SELECTION_METRIC,
    "class_weight": "balanced",
    "rbf_C": list(RBF_C),
    "rbf_gamma": list(RBF_GAMMA),
    "linear_C": list(LINEAR_C),
}


def candidate_params() -> list[dict]:
    grid = [{"kernel": "rbf", "C": c, "gamma": g} for c in RBF_C for g in RBF_GAMMA]
    grid += [{"kernel": "linear", "C": c, "gamma": None} for c in LINEAR_C]
    return grid


def _rows_for(
    params_list: Iterable[dict],
    train_pairs,
    val_pairs,
    seed: int,
) -> list[dict]:
    rows: list[dict] = []
    for params in params_list:
        model = make_pipeline(seed, probability=False, **params)
        start = time.perf_counter()
        x_train, y_train = train_pairs
        model.fit(x_train, y_train)
        fit_seconds = time.perf_counter() - start
        train_pred = model.predict(x_train)
        val_pred = model.predict(val_pairs[0])
        train_f1 = float(f1_score(y_train, train_pred, average="macro", zero_division=0))
        val_f1 = float(
            f1_score(val_pairs[1], val_pred, average="macro", zero_division=0)
        )
        rows.append(
            {
                **params,
                "train_accuracy": float(accuracy_score(y_train, train_pred)),
                "val_accuracy": float(accuracy_score(val_pairs[1], val_pred)),
                "train_macro_f1": train_f1,
                "val_macro_f1": val_f1,
                "f1_gap": train_f1 - val_f1,
                "fit_seconds": round(fit_seconds, 3),
            }
        )
    return rows


def search(
    x_train: np.ndarray,
    y_train: list[str],
    x_val: np.ndarray,
    y_val: list[str],
    grid: Iterable[dict] | None = None,
    seed: int = SPLIT_SEED,
    progress: Callable[[Iterable[dict]], Iterable[dict]] | None = None,
) -> list[dict]:
    params_list = list(grid if grid is not None else candidate_params())
    iterator = progress(params_list) if progress else params_list
    return _rows_for(iterator, (x_train, y_train), (x_val, y_val), seed)


def grouped_folds(
    labels: list[str],
    groups: list[int],
    n_splits: int = 5,
    seed: int = SPLIT_SEED,
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Grouped stratified folds; every observation stays inside one fold."""
    n_groups = len(set(groups))
    if n_groups < 2:
        raise ValueError(f"need at least 2 observation groups, got {n_groups}")
    folds = min(n_splits, n_groups)
    splitter = StratifiedGroupKFold(n_splits=folds, shuffle=True, random_state=seed)
    return list(
        splitter.split(np.zeros(len(labels)), labels, groups)
    )


def search_grouped_cv(
    x: np.ndarray,
    y: list[str],
    groups: list[int],
    grid: Iterable[dict] | None = None,
    n_splits: int = 5,
    seed: int = SPLIT_SEED,
    progress: Callable[[Iterable[dict]], Iterable[dict]] | None = None,
) -> list[dict]:
    """Mean +/- SE of grouped-CV macro F1 for every candidate.

    The spread is what makes a one-standard-error rule possible; a single split
    cannot tell a real gain from selection noise.
    """
    params_list = list(grid if grid is not None else candidate_params())
    iterator = progress(params_list) if progress else params_list
    folds = grouped_folds(y, groups, n_splits=n_splits, seed=seed)
    rows: list[dict] = []
    for params in iterator:
        scores: list[float] = []
        accuracies: list[float] = []
        for train_index, val_index in folds:
            model = make_pipeline(seed, probability=False, **params)
            model.fit(x[train_index], [y[i] for i in train_index])
            pred = model.predict(x[val_index])
            truth = [y[i] for i in val_index]
            scores.append(
                float(f1_score(truth, pred, average="macro", zero_division=0))
            )
            accuracies.append(float(accuracy_score(truth, pred)))
        spread = float(np.std(scores, ddof=1)) if len(scores) > 1 else 0.0
        rows.append(
            {
                **params,
                "cv_folds": len(folds),
                "cv_macro_f1_mean": float(np.mean(scores)),
                "cv_macro_f1_sd": spread,
                "cv_macro_f1_se": spread / math.sqrt(len(scores)) if scores else 0.0,
                "cv_accuracy_mean": float(np.mean(accuracies)),
                "cv_macro_f1_folds": [round(score, 4) for score in scores],
            }
        )
    return rows


def flexibility(row: dict) -> float:
    """Lower is a simpler decision boundary: linear < RBF, smaller C, smoother gamma."""
    c = float(row["C"])
    if row["kernel"] == "linear":
        return math.log10(c)
    gamma = row.get("gamma")
    value = 1.0 / 148.0 if gamma in (None, "scale") else float(gamma)
    return math.log10(c) + math.log10(value)


def best_1se(rows: list[dict], metric: str = CV_METRIC) -> dict:
    """Least flexible candidate within one SE of the best cross-validated score."""
    if not rows:
        raise ValueError("no tuning rows")
    top = max(rows, key=lambda row: row[metric])
    cutoff = top[metric] - float(top.get("cv_macro_f1_se", 0.0))
    within = [row for row in rows if row[metric] >= cutoff]
    return min(within, key=lambda row: (flexibility(row), -row[metric]))


def best(rows: list[dict]) -> dict:
    """Highest validation macro F1; ties go to higher accuracy, then smaller C."""
    if not rows:
        raise ValueError("no tuning rows")
    return max(rows, key=lambda r: (r[SELECTION_METRIC], r["val_accuracy"], -float(r["C"])))


def best_params(rows: list[dict]) -> dict:
    row = best(rows)
    return {"kernel": row["kernel"], "C": row["C"], "gamma": row["gamma"]}


def params_of(row: dict) -> dict:
    return {"kernel": row["kernel"], "C": row["C"], "gamma": row["gamma"]}
