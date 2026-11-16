"""Perceptual hashing and observation grouping.

These guard the two things the grouped split depends on: that "same shot" is
detected, and that frames from one photoshoot land in one group. A silent
failure here would put near-duplicates back on both sides of the split, which
is exactly the leak `docs/22-accuracy-plan.md` is trying to remove.
"""

from __future__ import annotations

import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import phash  # noqa: E402

# Outside the repo: these are scratch images, not fixtures.
HERE = Path(tempfile.mkdtemp(prefix="ms_phash_"))

# Every row differs, so a hash collision cannot come from uniform pixels.
_BASE = np.zeros((64, 64, 3), dtype=np.uint8)
for _y in range(64):
    for _x in range(64):
        _BASE[_y, _x] = ((_x * 3 + _y * 5) % 256, (_x * 7 + _y * 2) % 256, (_x + _y) % 256)


def _setup() -> None:
    HERE.mkdir(parents=True, exist_ok=True)
    Image.fromarray(_BASE).save(HERE / "base.png")
    # Same frame, resized -> should stay very close.
    Image.fromarray(_BASE).resize((128, 128), Image.Resampling.LANCZOS).save(
        HERE / "resized.png"
    )
    Image.fromarray(_BASE).save(HERE / "reencoded.jpg", quality=80)
    # A different frame: rotated means different pixel neighbourhoods.
    other = np.roll(_BASE, 17, axis=1)
    Image.fromarray(other).save(HERE / "other.png")


def setup_module() -> None:
    _setup()


def test_identical_files_hash_to_the_same_value() -> None:
    left = phash.dhash(HERE / "base.png")
    right = phash.dhash(HERE / "base.png")
    assert left == right
    assert phash.hamming(left, right) == 0


def test_resize_and_reencode_stay_within_the_near_duplicate_cutoff() -> None:
    base = phash.dhash(HERE / "base.png")
    resized = phash.dhash(HERE / "resized.png")
    reencoded = phash.dhash(HERE / "reencoded.jpg")
    assert phash.hamming(base, resized) <= phash.NEAR_DUPLICATE_MAX_DISTANCE
    assert phash.hamming(base, reencoded) <= phash.NEAR_DUPLICATE_MAX_DISTANCE


def test_a_different_frame_is_further_than_the_cutoff() -> None:
    base = phash.dhash(HERE / "base.png")
    other = phash.dhash(HERE / "other.png")
    assert phash.hamming(base, other) > phash.NEAR_DUPLICATE_MAX_DISTANCE


def test_near_duplicate_pairs_and_grouping() -> None:
    paths = [
        HERE / "base.png",
        HERE / "resized.png",
        HERE / "other.png",
        HERE / "base.png",
    ]
    hashes = [phash.dhash(path) for path in paths]
    pairs = phash.near_duplicate_pairs(hashes, max_distance=2)
    found = {(i, j) for i, j, _distance in pairs}
    # the three copies of the base frame, all close to each other
    assert (0, 1) in found
    assert (0, 3) in found
    assert (1, 3) in found
    # the rolled frame is its own sample
    assert all(2 not in pair for pair in found)

    labels = phash.group_from_pairs(len(paths), pairs)
    assert labels[0] == labels[1] == labels[3]
    assert labels[2] != labels[0]


def test_observation_groups_cluster_by_capture_time(monkeypatch) -> None:
    paths = [HERE / f"frame{index}.png" for index in range(4)]
    for path in paths:
        path.write_bytes((HERE / "base.png").read_bytes())
    stamps = [
        datetime(2026, 5, 1, 9, 0, 0),
        datetime(2026, 5, 1, 9, 0, 40),
        datetime(2026, 5, 1, 9, 2, 0),
        datetime(2026, 5, 2, 14, 0, 0),
    ]

    def fake_provenance(path: Path) -> dict:
        index = int(path.stem.replace("frame", ""))
        return {
            "path": str(path),
            "model": "TESTCAM",
            "datetime": stamps[index],
            "has_gps": False,
            "body_serial": None,
        }

    monkeypatch.setattr(phash, "exif_provenance", fake_provenance)
    labels, mode = phash.observation_groups(paths, gap_seconds=300)
    assert mode == "time-cluster"
    assert labels[0] == labels[1] == labels[2]
    assert labels[3] != labels[0]


def test_missing_exif_reports_that_it_fell_back(monkeypatch) -> None:
    paths = [HERE / f"bare{index}.png" for index in range(3)]
    for path in paths:
        path.write_bytes((HERE / "base.png").read_bytes())

    def no_exif(path: Path) -> dict:
        return {
            "path": str(path),
            "model": None,
            "datetime": None,
            "has_gps": False,
            "body_serial": None,
        }

    monkeypatch.setattr(phash, "exif_provenance", no_exif)
    labels, mode = phash.observation_groups(paths)
    # One group per file is the old image-level split, and the mode says so.
    assert mode == "per-file"
    assert len(set(labels)) == len(paths)


def test_split_groups_merges_duplicates_into_one_observation(monkeypatch) -> None:
    paths = [HERE / f"g{index}.png" for index in range(3)]
    for path in paths:
        path.write_bytes((HERE / "base.png").read_bytes())
    stamps = {
        "g0": datetime(2026, 5, 1, 9, 0, 0),
        "g1": datetime(2026, 6, 1, 9, 0, 0),
        "g2": datetime(2026, 7, 1, 9, 0, 0),
    }

    def fake_provenance(path: Path) -> dict:
        return {
            "path": str(path),
            "model": "TESTCAM",
            "datetime": stamps[path.stem],
            "has_gps": False,
            "body_serial": None,
        }

    monkeypatch.setattr(phash, "exif_provenance", fake_provenance)
    # Three different dates would be three observations, but all three frames
    # are the same file, so the duplicate merge must collapse them to one.
    labels, report = phash.split_groups(paths, max_distance=2)
    assert len(set(labels)) == 1
    assert report["near_duplicate_pairs"] >= 2
    assert report["largest_group"] == 3
    assert report["mode"] == "time-cluster"


def test_gap_boundary_starts_a_new_group(monkeypatch) -> None:
    paths = [HERE / f"b{index}.png" for index in range(2)]
    for path in paths:
        path.write_bytes((HERE / "base.png").read_bytes())
    base = datetime(2026, 5, 1, 9, 0, 0)
    offsets = [timedelta(0), timedelta(seconds=301)]

    def fake_provenance(path: Path) -> dict:
        index = int(path.stem.replace("b", ""))
        return {
            "path": str(path),
            "model": "TESTCAM",
            "datetime": base + offsets[index],
            "has_gps": False,
            "body_serial": None,
        }

    monkeypatch.setattr(phash, "exif_provenance", fake_provenance)
    labels, _mode = phash.observation_groups(paths, gap_seconds=300)
    assert labels[0] != labels[1]


def test_cross_class_near_duplicates_are_reported_not_merged(monkeypatch) -> None:
    """A duplicate filed under two species is a label bug, not one observation.

    Merging the two would put two classes in one group, break stratification,
    and (as a smoke run on the real pipeline showed) collapse a whole split.
    """
    paths = [HERE / f"x{index}.png" for index in range(2)]
    for path in paths:
        path.write_bytes((HERE / "base.png").read_bytes())

    def fake_provenance(path: Path) -> dict:
        index = int(path.stem.replace("x", ""))
        return {
            "path": str(path),
            "model": "TESTCAM",
            "datetime": datetime(2026, 5, 1 + index, 9, 0, 0),
            "has_gps": False,
            "body_serial": None,
        }

    monkeypatch.setattr(phash, "exif_provenance", fake_provenance)
    labels, report = phash.split_groups(
        paths,
        labels=["enhalus", "thalassia"],
        max_distance=2,
    )
    assert report["cross_class_near_duplicates"] == 1
    assert report["near_duplicate_pairs"] == 0
    # Different classes must stay in different groups even though the pixels match.
    assert len(set(labels)) == 2


def _inat_frame(name: str) -> Path:
    path = HERE / name
    path.write_bytes((HERE / "base.png").read_bytes())
    return path


def test_inaturalist_ids_group_a_photoshoot_without_exif() -> None:
    """The Drive mirror has no capture times; the filename id is the grouping."""
    paths = [
        _inat_frame("102223851_1_inat.jpg"),
        _inat_frame("102223851_2_inat.jpg"),
        _inat_frame("102223851_7_inat.jpg"),
        _inat_frame("999_1_inat.jpg"),
    ]
    labels, mode = phash.observation_groups(paths)
    assert mode == "inaturalist"
    assert labels[0] == labels[1] == labels[2]
    assert labels[3] != labels[0]
    assert phash.inaturalist_observation(paths[0]) == "102223851"
    assert phash.inaturalist_observation(HERE / "frame0.png") is None


def test_partial_inaturalist_names_still_group_what_they_can() -> None:
    paths = [
        _inat_frame("500_1_inat.jpg"),
        _inat_frame("500_2_inat.jpg"),
        _inat_frame("plain_frame.jpg"),
    ]
    labels, mode = phash.observation_groups(paths)
    assert mode == "inaturalist-partial"
    assert labels[0] == labels[1]
    assert labels[2] not in {labels[0], labels[1]}


def test_one_observation_id_under_two_species_is_reported_not_merged() -> None:
    paths = [
        _inat_frame("700_1_inat.jpg"),
        _inat_frame("700_2_inat.jpg"),
    ]
    labels, report = phash.split_groups(
        paths, labels=["enhalus_acoroides", "thalassia_hemprichii"], max_distance=6
    )
    assert report["mode"] == "inaturalist"
    assert report["cross_class_observations"] == 1
    assert len(set(labels)) == 2
