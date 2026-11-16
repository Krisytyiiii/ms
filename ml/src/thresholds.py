"""Per-class acceptance thresholds (plan row 2.6).

One global retake threshold treats a 23-photo class and a 1,549-photo class the
same, but the SVM's probability scale is not comparable across classes: a class
the model has rarely seen produces smaller margins even when the call is right.
This module fits one acceptance threshold per *predicted* class on validation
rows and lets a hopeless class abstain (return `None`), which the app should
read as "retake" rather than a guess.

The rule is deliberately conservative: a threshold must leave at least
`MIN_CLASS_ACCEPTED` validation photos of that class, and its accepted accuracy
must beat chance. A class that cannot clear both abstains.
"""

from __future__ import annotations

import numpy as np

MIN_CLASS_ACCEPTED = 5


def _best_threshold(
    confidence: np.ndarray, correct: np.ndarray, min_accepted: int
) -> tuple[float, int, float] | None:
    """Highest-accuracy threshold that keeps at least `min_accepted` photos.

    Ties prefer more accepted photos, then the lower threshold.
    """
    best_key: tuple[float, int, float] | None = None
    best: tuple[float, int, float] | None = None
    for threshold in np.unique(confidence):
        mask = confidence >= threshold
        accepted = int(mask.sum())
        if accepted < min_accepted:
            continue
        accuracy = float(correct[mask].mean())
        key = (accuracy, accepted, -float(threshold))
        if best_key is None or key > best_key:
            best_key = key
            best = (float(threshold), accepted, accuracy)
    return best


def choose_class_thresholds(
    probabilities: np.ndarray,
    predicted: np.ndarray,
    truth: np.ndarray,
    classes: list[str],
    min_accepted: int = MIN_CLASS_ACCEPTED,
) -> dict[str, float | None]:
    """One acceptance threshold per class, fitted on validation rows.

    `probabilities` is (n, n_classes), `predicted` and `truth` are integer
    indices into `classes`. A class whose validation rows are too few, or whose
    best accepted accuracy does not beat chance, maps to `None` = never accept.
    """
    probabilities = np.asarray(probabilities, dtype=np.float64)
    predicted = np.asarray(predicted, dtype=int)
    truth = np.asarray(truth, dtype=int)
    if probabilities.ndim != 2:
        raise ValueError("probabilities must be 2-D")
    correct = predicted == truth
    chance = 1.0 / len(classes)
    thresholds: dict[str, float | None] = {}
    for index, slug in enumerate(classes):
        rows = np.flatnonzero(predicted == index)
        if len(rows) < min_accepted:
            thresholds[slug] = None
            continue
        best = _best_threshold(
            probabilities[rows, index], correct[rows], min_accepted
        )
        if best is None or best[2] <= chance:
            thresholds[slug] = None
            continue
        thresholds[slug] = best[0]
    return thresholds


def accept_mask(
    probabilities: np.ndarray,
    predicted: np.ndarray,
    thresholds: dict[str, float | None],
    classes: list[str],
) -> np.ndarray:
    """True where the top class clears its own threshold."""
    probabilities = np.asarray(probabilities, dtype=np.float64)
    predicted = np.asarray(predicted, dtype=int)
    mask = np.zeros(len(predicted), dtype=bool)
    for row, index in enumerate(predicted):
        threshold = thresholds.get(classes[index])
        if threshold is None:
            continue
        mask[row] = probabilities[row, index] >= threshold
    return mask


def summarise(mask: np.ndarray, correct: np.ndarray) -> dict:
    """Accepted count, coverage, and accuracy for an acceptance mask."""
    mask = np.asarray(mask, dtype=bool)
    correct = np.asarray(correct, dtype=bool)
    if len(mask) == 0:
        return {"accepted": 0, "coverage": 0.0, "accuracy": None}
    accepted = int(mask.sum())
    return {
        "accepted": accepted,
        "coverage": float(accepted / len(mask)),
        "accuracy": float(correct[mask].mean()) if accepted else None,
    }


def answering_classes(thresholds: dict[str, float | None]) -> list[str]:
    """Classes the rule is willing to name, in the given order."""
    return [slug for slug, value in thresholds.items() if value is not None]
