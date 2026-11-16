"""Per-class acceptance thresholds behave conservatively and honestly."""

import numpy as np

from thresholds import (
    MIN_CLASS_ACCEPTED,
    accept_mask,
    answering_classes,
    choose_class_thresholds,
    summarise,
)

CLASSES = ["a", "b", "c"]


def _proba(rows: list[list[float]]) -> np.ndarray:
    return np.asarray(rows, dtype=np.float64)


def test_confident_correct_rows_set_a_high_threshold() -> None:
    # Class "a" is predicted 6 times: 3 confident and correct, 3 unsure and wrong.
    proba = _proba(
        [
            [0.9, 0.05, 0.05],
            [0.8, 0.1, 0.1],
            [0.7, 0.2, 0.1],
            [0.4, 0.3, 0.3],
            [0.35, 0.33, 0.32],
            [0.3, 0.4, 0.3],
        ]
    )
    predicted = np.zeros(6, dtype=int)
    truth = np.array([0, 0, 0, 1, 1, 1])
    thresholds = choose_class_thresholds(proba, predicted, truth, CLASSES, min_accepted=3)
    # With min_accepted=3 the rule can keep just the three correct rows.
    assert thresholds["a"] == 0.7


def test_too_few_rows_abstains() -> None:
    proba = _proba([[0.9, 0.05, 0.05]] * 3)
    predicted = np.zeros(3, dtype=int)
    truth = np.zeros(3, dtype=int)
    thresholds = choose_class_thresholds(proba, predicted, truth, CLASSES)
    assert thresholds["a"] is None
    assert thresholds["b"] is None
    assert answering_classes(thresholds) == []
    assert MIN_CLASS_ACCEPTED > 3


def test_class_that_cannot_beat_chance_abstains() -> None:
    # Six confident predictions of "b", none of them correct: accuracy 0 < 1/3.
    proba = _proba([[0.1, 0.85, 0.05]] * 6)
    predicted = np.ones(6, dtype=int)
    truth = np.zeros(6, dtype=int)
    thresholds = choose_class_thresholds(proba, predicted, truth, CLASSES)
    assert thresholds["b"] is None


def test_accept_mask_uses_the_predicted_class_threshold() -> None:
    proba = _proba(
        [
            [0.62, 0.2, 0.18],
            [0.58, 0.3, 0.12],
            [0.2, 0.65, 0.15],
        ]
    )
    predicted = np.array([0, 0, 1])
    thresholds = {"a": 0.6, "b": None, "c": 0.5}
    mask = accept_mask(proba, predicted, thresholds, CLASSES)
    assert mask.tolist() == [True, False, False]
    correct = predicted == np.array([0, 1, 1])
    stats = summarise(mask, correct)
    assert stats["accepted"] == 1
    assert stats["coverage"] == 1 / 3
    assert stats["accuracy"] == 1.0


def test_summarise_handles_an_empty_mask() -> None:
    stats = summarise(np.zeros(0, dtype=bool), np.zeros(0, dtype=bool))
    assert stats == {"accepted": 0, "coverage": 0.0, "accuracy": None}


if __name__ == "__main__":
    test_confident_correct_rows_set_a_high_threshold()
    test_too_few_rows_abstains()
    test_class_that_cannot_beat_chance_abstains()
    test_accept_mask_uses_the_predicted_class_threshold()
    test_summarise_handles_an_empty_mask()
    print("ok")
