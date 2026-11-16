from pathlib import Path

import numpy as np
from PIL import Image

from augment import augment_train
from leaf_focus import crop_to_plant, plant_fraction, plant_mask
from preprocess import augment_rgb, list_labeled_images, load_rgb_from_bytes, process_rgb, qc_reason
from select_frames import drop_exact_duplicates, select_leaf_frames
from skimage.color import rgb2hsv


def _green_leaf(size: int = 120) -> np.ndarray:
    frame = np.full((size, size, 3), 220, dtype=np.uint8)
    frame[30:90, 40:80] = (20, 140, 30)
    return frame


def test_nested_species_is_listed_under_its_own_class(tmp_path: Path) -> None:
    """Each image is labelled by its innermost species folder, exactly once."""
    parent = tmp_path / "Enhalus acoroides dataset (all)"
    nested = parent / "Thalassia hemprichii dataset (all)"
    nested.mkdir(parents=True)
    Image.fromarray(_green_leaf()).save(parent / "enhalus.jpg")
    Image.fromarray(_green_leaf()).save(nested / "thalassia.jpg")
    pairs = list_labeled_images(tmp_path)
    assert sorted(slug for _path, slug in pairs) == [
        "enhalus_acoroides",
        "thalassia_hemprichii",
    ]


def test_qc_drops_blank_and_keeps_leaf() -> None:
    blank = np.full((80, 80, 3), 200, dtype=np.uint8)
    sand = np.zeros((80, 80, 3), dtype=np.uint8)
    sand[:, :] = (190, 170, 150)
    sand[::2, ::2] = (200, 180, 155)
    leaf = _green_leaf()
    assert qc_reason(blank) == "low_contrast"
    assert qc_reason(sand) is None
    assert qc_reason(leaf) is None
    assert plant_fraction(leaf) > 0.05
    assert plant_mask(leaf).any()


def test_process_resizes_and_can_crop() -> None:
    leaf = _green_leaf(160)
    out, meta = process_rgb(leaf, size=64)
    assert meta["status"] == "kept"
    assert out.shape == (64, 64, 3)
    cropped, did = crop_to_plant(leaf)
    assert did
    assert cropped.shape[0] < leaf.shape[0]


def test_load_rgb_from_bytes() -> None:
    from io import BytesIO

    from PIL import Image

    buf = BytesIO()
    Image.fromarray(_green_leaf(80)).save(buf, format="JPEG")
    rgb = load_rgb_from_bytes(buf.getvalue(), size=32)
    assert rgb.shape == (32, 32, 3)


def test_too_small() -> None:
    tiny = np.zeros((20, 20, 3), dtype=np.uint8)
    tiny[:, :] = (20, 140, 30)
    assert qc_reason(tiny) == "too_small"


def _sand(size: int = 80) -> np.ndarray:
    sand = np.zeros((size, size, 3), dtype=np.uint8)
    sand[:, :] = (190, 170, 150)
    sand[::2, ::2] = (200, 180, 155)
    return sand


def _habitat_frame(size: int = 96) -> np.ndarray:
    frame = np.zeros((size, size, 3), dtype=np.uint8)
    frame[:, :] = (180, 160, 140)
    frame[: size // 3, :] = (40, 90, 220)
    return frame


def _brown_blade(size: int = 96) -> np.ndarray:
    frame = _sand(size)
    frame[20 : size - 16, size // 2 - 3 : size // 2 + 3] = (110, 60, 30)
    return frame


def test_habitat_dropped_brown_blade_and_sand_kept() -> None:
    habitat = _habitat_frame()
    assert qc_reason(habitat) == "habitat"
    skipped, meta = process_rgb(habitat, size=64)
    assert meta["status"] == "skipped"
    assert meta["reason"] == "habitat"
    assert skipped.shape == habitat.shape
    assert qc_reason(_brown_blade()) is None
    assert qc_reason(_sand()) is None


def test_augment_changes_pixels_and_keeps_hue() -> None:
    source = _green_leaf(80)
    for kind in (
        "hflip",
        "rot15",
        "rot-15",
        "rot25",
        "rot-25",
        "scale85",
        "scale115",
        "bright-12",
        "bright+12",
    ):
        out = augment_rgb(source, kind)
        assert out.shape == source.shape, kind
        assert out.dtype == np.uint8, kind
        assert not np.array_equal(out, source), kind
    before = rgb2hsv(source.astype(np.float64) / 255.0)
    after = rgb2hsv(augment_rgb(source, "bright+12").astype(np.float64) / 255.0)
    stable = (before[:, :, 2] > 0.05) & (before[:, :, 2] < 0.85)
    hue_shift = np.abs(before[:, :, 0][stable] - after[:, :, 0][stable])
    assert float(hue_shift.max()) < 0.002
    assert float(after[:, :, 2][stable].mean()) > float(before[:, :, 2][stable].mean())


def test_augment_train_keeps_labels_and_caps_copies() -> None:
    leaf = _green_leaf(64)
    sand = _sand(64)
    images = [leaf] * 4 + [sand] * 12
    labels = ["halophila_minor"] * 4 + ["halophila_ovalis"] * 12
    out_images, out_labels = augment_train(images, labels, seed=42)
    assert len(out_images) == len(out_labels)
    assert out_labels[: len(labels)] == labels
    assert np.array_equal(out_images[0], leaf)
    extras = out_labels[len(labels) :]
    assert extras.count("halophila_ovalis") == 0
    assert extras.count("halophila_minor") == 8
    assert all(image.shape == leaf.shape for image in out_images)


def _tagged(frame: np.ndarray, index: int) -> np.ndarray:
    """One corner pixel keeps each file's bytes unique without changing the QC class."""
    out = frame.copy()
    out[-1, -1] = (index % 220, 8, 12)
    return out


def test_habitat_waived_for_a_tiny_class(tmp_path: Path) -> None:
    habitat = _habitat_frame()
    leaf = _green_leaf(96)
    pairs: list[tuple[Path, str]] = []
    for index in range(14):
        path = tmp_path / f"minor_sky_{index}.png"
        Image.fromarray(_tagged(habitat, index)).save(path)
        pairs.append((path, "halophila_minor"))
    leaf_path = tmp_path / "minor_leaf.png"
    Image.fromarray(_tagged(leaf, 100)).save(leaf_path)
    pairs.append((leaf_path, "halophila_minor"))
    for index in range(16):
        path = tmp_path / f"enhalus_{index}.png"
        Image.fromarray(_tagged(leaf, 200 + index)).save(path)
        pairs.append((path, "enhalus_acoroides"))
    sky_path = tmp_path / "enhalus_sky.png"
    Image.fromarray(_tagged(habitat, 250)).save(sky_path)
    pairs.append((sky_path, "enhalus_acoroides"))

    kept, record = select_leaf_frames(pairs)
    counts: dict[str, int] = {}
    for _, slug in kept:
        counts[slug] = counts.get(slug, 0) + 1
    assert counts["halophila_minor"] == 15
    assert counts["enhalus_acoroides"] == 16
    assert record["habitat_waived"] == ["halophila_minor"]
    assert record["skip_reasons"].get("habitat") == 1


def test_exact_duplicate_dropped(tmp_path: Path) -> None:
    leaf = _green_leaf(80)
    first = tmp_path / "a.png"
    second = tmp_path / "b.png"
    Image.fromarray(leaf).save(first)
    second.write_bytes(first.read_bytes())
    kept, dropped = drop_exact_duplicates([(second, "halophila_ovalis"), (first, "halophila_ovalis")])
    assert dropped == 1
    assert len(kept) == 1
    selected, record = select_leaf_frames([(first, "enhalus_acoroides"), (second, "enhalus_acoroides")])
    assert len(selected) == 1
    assert record["duplicates_dropped"] == 1
    assert record["skip_reasons"].get("duplicate") == 1


if __name__ == "__main__":
    import tempfile

    test_qc_drops_blank_and_keeps_leaf()
    test_process_resizes_and_can_crop()
    test_load_rgb_from_bytes()
    test_too_small()
    test_habitat_dropped_brown_blade_and_sand_kept()
    test_augment_changes_pixels_and_keeps_hue()
    test_augment_train_keeps_labels_and_caps_copies()
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        waive = root / "waive"
        dup = root / "dup"
        waive.mkdir()
        dup.mkdir()
        test_habitat_waived_for_a_tiny_class(waive)
        test_exact_duplicate_dropped(dup)
    with tempfile.TemporaryDirectory() as raw:
        test_nested_other_species_is_not_listed(Path(raw))
    print("ok")
