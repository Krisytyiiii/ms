"""The negative-set audit counts false accepts honestly."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.audit_negative import image_files, render, summarise  # noqa: E402


def _row(slug="enhalus_acoroides", confidence=0.9, accepted=True, fraction=0.01) -> dict:
    return {
        "path": "x.jpg",
        "slug": slug,
        "confidence": confidence,
        "accepted": accepted,
        "plant_fraction": fraction,
        "top": [],
    }


def test_every_negative_is_given_a_species() -> None:
    rows = [_row(), _row(), _row()]
    summary = summarise(rows, threshold=0.44, plant_min=0.05)
    assert summary["n"] == 3
    # The SVM has no "none of the above"; all three are named.
    assert summary["named_a_species"] == 3


def test_false_accept_rate_counts_only_gate_clearing_photos() -> None:
    rows = [
        _row(confidence=0.9, accepted=True),
        _row(confidence=0.6, accepted=True),
        _row(confidence=0.2, accepted=False),
        _row(confidence=0.1, accepted=False),
    ]
    summary = summarise(rows, threshold=0.44, plant_min=0.05)
    assert summary["false_accept_rate"] == 0.5


def test_plant_evidence_check_catches_bare_backgrounds() -> None:
    rows = [
        _row(fraction=0.01),  # sand: almost no blade material
        _row(fraction=0.02),
        _row(fraction=0.40),  # a genuinely green photo survives the check
        _row(fraction=0.9),
    ]
    summary = summarise(rows, threshold=0.44, plant_min=0.05)
    assert summary["plant_check_catch_rate"] == 0.5
    # Both caught photos were also falsely accepted by the confidence gate,
    # so the residual after both checks is half the set.
    assert summary["residual_false_accept_rate"] == 0.5


def test_summary_of_an_empty_folder_does_not_divide_by_zero() -> None:
    summary = summarise([], threshold=0.44, plant_min=0.05)
    assert summary["n"] == 0
    assert "No images found" in render(summary)


def test_render_names_the_false_accept_rate() -> None:
    text = render(summarise([_row(), _row(accepted=False, confidence=0.1)], 0.44, 0.05))
    assert "false accept" in text
    assert "named one of the nine species | 2 (100.0%)" in text


def test_false_reject_rate_is_interpolated_between_measured_cuts() -> None:
    from src.audit_negative import false_reject_rate

    assert false_reject_rate(0.05) == 0.343
    # Between the measured 0.02 (21.6%) and 0.03 (29.0%) points.
    assert 0.216 < false_reject_rate(0.025) < 0.290
    # Outside the measured range we do not invent a number.
    assert false_reject_rate(0.5) is None


def test_render_reports_what_the_plant_cut_costs_on_real_seagrass() -> None:
    text = render(summarise([_row()], 0.44, 0.05))
    assert "cost: real seagrass photos that same cut would refuse** | 34.3%" in text


def test_image_files_finds_nested_images_only(tmp_path: Path) -> None:
    (tmp_path / "sub").mkdir()
    (tmp_path / "a.JPG").write_bytes(b"x")
    (tmp_path / "sub" / "b.png").write_bytes(b"x")
    (tmp_path / "notes.txt").write_bytes(b"x")
    found = image_files(tmp_path)
    assert [path.name for path in found] == ["a.JPG", "b.png"]


if __name__ == "__main__":
    test_every_negative_is_given_a_species()
    test_false_accept_rate_counts_only_gate_clearing_photos()
    test_plant_evidence_check_catches_bare_backgrounds()
    test_summary_of_an_empty_folder_does_not_divide_by_zero()
    test_image_files_finds_nested_images_only(Path("."))
    print("ok")
