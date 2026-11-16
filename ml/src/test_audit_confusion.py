"""The confusion audit reads a record and reports the largest off-diagonal cells."""

import json

import pytest

from audit_confusion import absorbers, confusions, load, render


def _record(tmp_path, labels, matrix):
    path = tmp_path / "record.json"
    path.write_text(
        json.dumps({"classes": labels, "confusion_matrix_test": matrix}),
        encoding="utf-8",
    )
    return path


def test_confusions_sorts_by_count_and_carries_the_share(tmp_path) -> None:
    labels = ["a", "b", "c"]
    matrix = [
        [5, 3, 2],
        [1, 6, 3],
        [0, 1, 9],
    ]
    rows = confusions(labels, matrix, top=3)
    assert rows[0] == {
        "true": "a",
        "predicted": "b",
        "count": 3,
        "support": 10,
        "share": 0.3,
    }
    assert [row["count"] for row in rows] == [3, 3, 2]
    # The diagonal never appears.
    assert all(row["true"] != row["predicted"] for row in rows)


def test_absorbers_counts_wrong_photos_taken_in() -> None:
    labels = ["a", "b", "c"]
    matrix = [
        [5, 3, 2],
        [1, 6, 3],
        [0, 1, 9],
    ]
    rows = absorbers(labels, matrix)
    assert rows[0]["predicted"] == "c"
    assert rows[0]["wrong"] == 5
    assert rows[0]["correct"] == 9
    assert rows[0]["precision"] == pytest.approx(9 / 14)


def test_load_rejects_a_matrix_that_does_not_match_the_labels(tmp_path) -> None:
    path = _record(tmp_path, ["a", "b"], [[1, 0, 0], [0, 1, 0]])
    with pytest.raises(SystemExit):
        load(path)


def test_load_rejects_a_record_without_a_matrix(tmp_path) -> None:
    path = tmp_path / "record.json"
    path.write_text(json.dumps({"classes": ["a"]}), encoding="utf-8")
    with pytest.raises(SystemExit):
        load(path)


def test_render_prints_markdown_tables(tmp_path) -> None:
    path = _record(tmp_path, ["a", "b"], [[3, 1], [2, 4]])
    labels, matrix = load(path)
    text = render(labels, matrix)
    assert "| true species | predicted as |" in text
    assert "| predicted species | wrong photos absorbed |" in text
    assert "| a | b | 1 | 25% |" in text


if __name__ == "__main__":
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as folder:
        tmp = Path(folder)
        test_confusions_sorts_by_count_and_carries_the_share(tmp)
        test_absorbers_counts_wrong_photos_taken_in()
        test_load_rejects_a_matrix_that_does_not_match_the_labels(tmp)
        test_load_rejects_a_record_without_a_matrix(tmp)
        test_render_prints_markdown_tables(tmp)
    print("ok")
