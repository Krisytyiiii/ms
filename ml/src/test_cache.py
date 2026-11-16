"""The disk cache must never return a stale value, and must be safe to delete."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.cache import Cache, dhash_value, qc_reason, vector  # noqa: E402
from src.features import feature_spec  # noqa: E402


@pytest.fixture()
def photo(tmp_path: Path) -> Path:
    path = tmp_path / "500_1_inat.jpg"
    rng = np.random.default_rng(3)
    pixels = rng.integers(0, 255, size=(80, 80, 3), dtype=np.uint8)
    Image.fromarray(pixels).save(path)
    return path


def test_array_round_trip_counts_a_hit(tmp_path: Path, photo: Path) -> None:
    cache = Cache(tmp_path / "cache")
    key = cache.key(photo, "demo")
    calls = {"n": 0}

    def loader() -> np.ndarray:
        calls["n"] += 1
        return np.arange(4, dtype=np.float64)

    first = cache.array(key, loader)
    second = cache.array(key, loader)
    assert calls["n"] == 1
    assert np.array_equal(first, second)
    assert cache.summary()["hits"] == 1


def test_edit_invalidates_the_entry(tmp_path: Path, photo: Path) -> None:
    cache = Cache(tmp_path / "cache")
    before = cache.key(photo, "demo")
    photo.write_bytes(photo.read_bytes() + b"\x00")
    after = cache.key(photo, "demo")
    assert before != after


def test_disabled_cache_writes_nothing(tmp_path: Path, photo: Path) -> None:
    root = tmp_path / "cache"
    cache = Cache(root, enabled=False)
    assert qc_reason(cache, photo) is None
    assert not root.exists()
    assert cache.summary()["hits"] == 0


def test_vector_and_qc_are_cached_per_version(tmp_path: Path, photo: Path) -> None:
    cache = Cache(tmp_path / "cache")
    v2 = vector(cache, photo, "v2")
    v3 = vector(cache, photo, "v3")
    assert v2.shape == (feature_spec("v2")["length"],)
    assert v3.shape == (feature_spec("v3")["length"],)
    assert v3.shape[0] > v2.shape[0]
    assert qc_reason(cache, photo) is None
    # Second call is served from disk for both versions.
    assert np.array_equal(vector(cache, photo, "v2"), v2)
    assert dhash_value(cache, photo) == dhash_value(cache, photo)
