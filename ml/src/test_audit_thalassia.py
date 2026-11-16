"""The Thalassia audit's decision aid.

`_verdict` is the only part that decides anything, so it is the part worth
testing. The scan itself is read-only and takes a real dataset to run.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.audit_thalassia import _folder_pairs, _verdict  # noqa: E402


def test_clean_class_is_clean() -> None:
    verdict, reasons = _verdict(
        usable=700, mixin_share=0.0, distinct_plants=500, failed=0
    )
    assert verdict == "clean"
    assert reasons


def test_large_mixin_share_asks_for_review() -> None:
    verdict, reasons = _verdict(
        usable=700, mixin_share=0.25, distinct_plants=500, failed=0
    )
    assert verdict == "review"
    assert any("review CSV" in reason for reason in reasons)


def test_small_class_asks_for_review_even_when_clean() -> None:
    verdict, reasons = _verdict(
        usable=40, mixin_share=0.0, distinct_plants=35, failed=0
    )
    assert verdict == "review"
    assert any("under 100" in reason for reason in reasons)


def test_heavy_duplication_asks_for_review() -> None:
    verdict, reasons = _verdict(
        usable=200, mixin_share=0.0, distinct_plants=40, failed=0
    )
    assert verdict == "review"
    assert any("distinct plants" in reason for reason in reasons)


def test_unreadable_files_are_reported_but_do_not_block() -> None:
    verdict, reasons = _verdict(
        usable=700, mixin_share=0.0, distinct_plants=600, failed=3
    )
    assert verdict == "clean"
    assert any("could not be hashed" in reason for reason in reasons)


def _touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\xff\xd8\xff\xd9")


def test_nested_candidate_class_is_found_once(tmp_path: Path) -> None:
    """The Drive keeps Thalassia inside the trainable folders, in 3 copies."""
    pinifolia = tmp_path / "Halodule pinifolia dataset (all)"
    uninervis = tmp_path / "Halodule uninervis dataset (all)"
    _touch(pinifolia / "inaturalist" / "p1.jpg")
    _touch(pinifolia / "inaturalist" / "p2.jpg")
    for parent in (pinifolia, uninervis):
        nested = parent / "Thalassia hemprichii dataset (all)"
        _touch(nested / "inaturalist" / "t1.jpg")
        _touch(nested / "inaturalist" / "t2.jpg")

    rows = _folder_pairs(tmp_path)
    by_slug: dict[str, int] = {}
    for _path, slug, _variant in rows:
        by_slug[slug] = by_slug.get(slug, 0) + 1

    assert by_slug == {"halodule_pinifolia": 2, "thalassia_hemprichii": 2}
