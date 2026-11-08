from io import BytesIO

import numpy as np
from PIL import Image

from dataset_contract import TRAINABLE_SPECIES
from identify import choose_retake_threshold
from serve_identify import identify_payload


def _jpeg() -> bytes:
    frame = np.full((256, 256, 3), (190, 170, 150), dtype=np.uint8)
    frame[30:230, 118:138] = (30, 150, 40)
    buf = BytesIO()
    Image.fromarray(frame).save(buf, format="JPEG")
    return buf.getvalue()


def test_empty_body() -> None:
    status, payload = identify_payload(b"")
    assert status == 400
    assert payload["success"] is False


def test_too_large() -> None:
    status, payload = identify_payload(b"x" * (8 * 1024 * 1024 + 1))
    assert status == 413
    assert payload["success"] is False


def test_unreadable_bytes_stay_an_error() -> None:
    status, payload = identify_payload(b"not-an-image")
    assert status == 400
    assert payload["success"] is False
    assert "slug" not in payload.get("data", {})


def test_photo_returns_a_trainable_species_and_a_percent() -> None:
    status, payload = identify_payload(_jpeg())
    assert status == 200
    assert payload["success"] is True
    data = payload["data"]
    assert data["slug"] in TRAINABLE_SPECIES
    assert 0.0 <= data["confidence"] <= 1.0
    assert isinstance(data["low_confidence"], bool)
    again, _ = identify_payload(_jpeg())
    assert again == 200


def test_lowest_threshold_meets_accuracy_and_coverage() -> None:
    confidence = np.array([0.9] * 40 + [0.4] * 60)
    correct = np.array([True] * 70 + [False] * 30)
    chosen = choose_retake_threshold(confidence, correct)
    assert chosen["study_line_met"] is True
    assert chosen["threshold"] == 0.41
    assert chosen["accuracy"] == 1.0
    assert chosen["coverage"] == 0.4


def test_fallback_threshold_keeps_half_when_the_line_is_missed() -> None:
    confidence = np.array([0.95] * 50 + [0.2] * 50)
    correct = np.array([True] * 40 + [False] * 60)
    chosen = choose_retake_threshold(confidence, correct)
    assert chosen["study_line_met"] is False
    assert chosen["threshold"] == 0.21
    assert chosen["accuracy"] == 0.8
    assert chosen["coverage"] == 0.5


if __name__ == "__main__":
    test_empty_body()
    test_too_large()
    test_unreadable_bytes_stay_an_error()
    test_photo_returns_a_trainable_species_and_a_percent()
    test_lowest_threshold_meets_accuracy_and_coverage()
    test_fallback_threshold_keeps_half_when_the_line_is_missed()
    print("ok")
