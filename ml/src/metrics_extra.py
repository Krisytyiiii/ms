"""Multiclass metrics that match the problem, not just accuracy.

Accuracy on a test set where two classes are half the rows is misleading, and a
single accuracy number at n=245 has a 95% interval of roughly +/-6 points. This
module adds the numbers `docs/22-accuracy-plan.md` asks for:

    balanced accuracy   every class counts once
    macro recall        same, named the way the plan names it
    top-k accuracy      "was the right species in the shortlist?"
    coverage/accuracy   the retake tradeoff as a table, not one point
    grouped bootstrap   confidence interval that respects observation groups

Everything is pure Python + NumPy so it can run inside the training script and
in tests without sklearn's reporting objects.
"""

from __future__ import annotations

from collections import Counter

import numpy as np

DEFAULT_THRESHOLDS = (0.30, 0.40, 0.44, 0.50, 0.60, 0.70)


def top_k_accuracy(
    proba: np.ndarray,
    classes: list[str],
    labels: list[str],
    k: int = 2,
) -> float:
    """Share of rows whose truth is among the k highest probabilities."""
    proba = np.asarray(proba, dtype=np.float64)
    if len(labels) == 0:
        return float("nan")
    k = min(k, proba.shape[1])
    order = np.argsort(-proba, axis=1)[:, :k]
    hits = 0
    for row, truth in enumerate(labels):
        if truth in {classes[int(col)] for col in order[row]}:
            hits += 1
    return hits / len(labels)


def balanced_accuracy(labels: list[str], predictions: list[str]) -> float:
    """Mean per-class recall. NaN-free: classes absent from `labels` are skipped."""
    if not labels:
        return float("nan")
    per_class: dict[str, list[int]] = {}
    for truth, pred in zip(labels, predictions):
        hits, total = per_class.get(truth, (0, 0))
        per_class[truth] = (hits + int(truth == pred), total + 1)
    recalls = [hits / total for hits, total in per_class.values() if total]
    return float(np.mean(recalls)) if recalls else float("nan")


def per_class_table(
    labels: list[str],
    predictions: list[str],
    min_support: int = 20,
) -> list[dict]:
    """Per-class recall with support, plus a flag for uninterpretable rows.

    A class with 4 test photos cannot support a recall claim. The table says so
    rather than printing 0.00 and letting a reader treat it as a result.
    """
    truth_counts = Counter(labels)
    pred_counts = Counter(predictions)
    correct = Counter(
        truth for truth, pred in zip(labels, predictions) if truth == pred
    )
    rows = []
    for slug in sorted(truth_counts):
        support = truth_counts[slug]
        hits = correct[slug]
        rows.append(
            {
                "class": slug,
                "support": support,
                "predicted": pred_counts[slug],
                "correct": hits,
                "recall": hits / support if support else None,
                "interpretable": support >= min_support,
            }
        )
    return rows


def coverage_accuracy_table(
    confidence: np.ndarray,
    correct: np.ndarray,
    thresholds: tuple[float, ...] = DEFAULT_THRESHOLDS,
) -> list[dict]:
    """Accuracy among accepted photos and the share accepted, per threshold.

    One (accuracy, coverage) point hides the shape of the tradeoff. The plan
    asks for the table so the rejector can be argued about honestly.
    """
    confidence = np.asarray(confidence, dtype=np.float64)
    correct = np.asarray(correct, dtype=bool)
    if len(confidence) != len(correct):
        raise ValueError("confidence and correct must be the same length")
    rows = []
    for threshold in thresholds:
        accepted = confidence >= threshold
        count = int(accepted.sum())
        rows.append(
            {
                "threshold": float(threshold),
                "accepted": count,
                "coverage": count / len(confidence) if len(confidence) else 0.0,
                "accuracy": (
                    float(correct[accepted].mean()) if count else None
                ),
            }
        )
    return rows


def grouped_bootstrap_ci(
    correct: np.ndarray,
    groups: list[int],
    n_boot: int = 2000,
    alpha: float = 0.05,
    seed: int = 42,
) -> dict:
    """Percentile interval for accuracy, resampling observation groups.

    Images from one observation are not independent, so resampling images
    understates the interval. Resampling groups is the honest version.
    """
    correct = np.asarray(correct, dtype=float)
    if len(correct) != len(groups):
        raise ValueError("correct and groups must be the same length")
    if len(correct) == 0:
        return {"point": None, "low": None, "high": None, "n_boot": 0}

    by_group: dict[int, list[float]] = {}
    for value, group in zip(correct, groups):
        by_group.setdefault(group, []).append(float(value))
    keys = list(by_group)
    sums = np.array([sum(by_group[key]) for key in keys], dtype=float)
    sizes = np.array([len(by_group[key]) for key in keys], dtype=float)

    rng = np.random.default_rng(seed)
    draws = rng.integers(0, len(keys), size=(n_boot, len(keys)))
    totals = sums[draws].sum(axis=1)
    counts = sizes[draws].sum(axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        samples = np.where(counts > 0, totals / counts, np.nan)
    samples = samples[~np.isnan(samples)]
    if len(samples) == 0:
        return {"point": float(correct.mean()), "low": None, "high": None, "n_boot": 0}

    return {
        "point": float(correct.mean()),
        "low": float(np.quantile(samples, alpha / 2)),
        "high": float(np.quantile(samples, 1 - alpha / 2)),
        "n_boot": int(len(samples)),
        "groups": len(keys),
    }


def build_summary(
    probabilities: np.ndarray,
    classes: list[str],
    labels: list[str],
    groups: list[int] | None = None,
    thresholds: tuple[float, ...] = DEFAULT_THRESHOLDS,
    predictions: list[str] | None = None,
) -> dict:
    """Assemble the multiclass report from a probability matrix.

    `predictions` is the decision the caller actually ships. Pass it: the
    one-vs-one vote and the argmax of the Platt-coupled probabilities are two
    different rules, and mixing them put a 0.269 accuracy next to a 0.345
    confidence interval in the same record. Without it the summary falls back
    to the probability argmax and says so in `decision_rule`.
    """
    probabilities = np.asarray(probabilities, dtype=np.float64)
    classes = [str(name) for name in classes]
    top = probabilities.argmax(axis=1)
    if predictions is None:
        predictions = [classes[int(col)] for col in top]
        decision_rule = "probability_argmax"
    else:
        predictions = [str(name) for name in predictions]
        judgement = {slug: index for index, slug in enumerate(classes)}
        # The confidence of a voted call is the probability of that call, not
        # the top probability, or the retake threshold would gate a different
        # class than the one it returns.
        top = np.array(
            [judgement.get(slug, int(np.argmax(probabilities[row])))
             for row, slug in enumerate(predictions)],
            dtype=int,
        )
        decision_rule = "one_vs_one_vote"
    confidence = probabilities[np.arange(len(probabilities)), top]
    correct = np.array([pred == truth for pred, truth in zip(predictions, labels)])

    out = {
        "decision_rule": decision_rule,
        "accuracy": float(correct.mean()) if len(correct) else None,
        "balanced_accuracy": balanced_accuracy(labels, predictions),
        "macro_recall": balanced_accuracy(labels, predictions),
        "top2_accuracy": top_k_accuracy(probabilities, classes, labels, k=2),
        "top3_accuracy": top_k_accuracy(probabilities, classes, labels, k=3),
        "per_class": per_class_table(labels, predictions),
        "coverage_accuracy": coverage_accuracy_table(
            confidence, correct, thresholds
        ),
        "n": len(labels),
    }
    if groups is not None:
        out["accuracy_ci"] = grouped_bootstrap_ci(correct, groups)
    return out


def voted_calls(model, features: np.ndarray, labels: list[str]) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """Confidence, correctness, and slug for the rule that actually ships.

    `sklearn`'s `predict` is the one-vs-one vote; the app and `identify.py` both
    return that slug and take its probability as the confidence. Evaluating the
    argmax of the probabilities instead measures a different classifier.
    """
    probabilities = np.asarray(model.predict_proba(features), dtype=np.float64)
    classes = [str(name) for name in model.classes_]
    judgement = {slug: index for index, slug in enumerate(classes)}
    predictions = [str(name) for name in model.predict(features)]
    top = np.array([judgement[slug] for slug in predictions], dtype=int)
    confidence = probabilities[np.arange(len(probabilities)), top]
    correct = np.array([pred == truth for pred, truth in zip(predictions, labels)])
    return confidence, correct, predictions
