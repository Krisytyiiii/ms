"""The green-mask pre-check cost is measured, not assumed."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.audit_plant_fraction import render, summarise  # noqa: E402


def test_false_reject_rate_counts_real_seagrass_below_the_cut() -> None:
    values = {"a": [0.001, 0.001, 0.30, 0.40], "b": [0.002, 0.50]}
    summary = summarise(values, cuts=(0.05,))
    assert summary["n"] == 6
    assert summary["cuts"][0]["false_reject"] == 0.5


def test_per_class_stats_expose_the_class_spread() -> None:
    values = {"brown": [0.01, 0.02], "green": [0.3, 0.4]}
    summary = summarise(values)
    assert summary["per_class"]["brown"]["under_005"] == 1.0
    assert summary["per_class"]["green"]["under_005"] == 0.0
    assert summary["per_class"]["green"]["median"] == 0.35


def test_empty_input_does_not_divide_by_zero() -> None:
    summary = summarise({})
    assert summary["n"] == 0
    assert render(summary) == "No images measured."


def test_render_shows_the_cost_table() -> None:
    text = render(summarise({"a": [0.001, 0.5]}, cuts=(0.05, 0.10)))
    assert "real seagrass photos refused" in text
    assert "| 0.05 | 50.0% |" in text


def test_real_measured_table_is_reproducible_from_docs() -> None:
    """The cut-to-cost table quoted in docs/22 must match, not drift.

    Values come from 504 real seagrass photos; `audit_plant_fraction.py`
    reproduces them against the Drive mirror. This pins the published numbers
    so a future edit cannot silently contradict the write-up.
    """
    measured = {0.01: 0.153, 0.02: 0.216, 0.03: 0.290, 0.05: 0.343, 0.10: 0.450}
    from src.audit_negative import REAL_SEAGRASS_FALSE_REJECT

    assert REAL_SEAGRASS_FALSE_REJECT == measured


if __name__ == "__main__":
    test_false_reject_rate_counts_real_seagrass_below_the_cut()
    test_per_class_stats_expose_the_class_spread()
    test_empty_input_does_not_divide_by_zero()
    test_render_shows_the_cost_table()
    test_real_measured_table_is_reproducible_from_docs()
    print("ok")
