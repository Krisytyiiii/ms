"""Curated eight-class SVM. Tune on validation, then score the test split once.

Leaf-visible selection and exact-duplicate removal happen before the split.
Augmentation is train-only. Artifacts land in ml/artifacts/v2 only when
validation macro F1 beats the locked v1 score of 0.468. v1 is left in place.

    python ml/src/train_curated.py
    python ml/src/train_curated.py --root D:\\path\\to\\Seagrass
"""

from __future__ import annotations

import argparse
import gc
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from tqdm import tqdm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.augment import AUGMENT_SPEC, augment_train  # noqa: E402
from src.dataset_contract import (  # noqa: E402
    HELD_OUT_SPECIES,
    IMAGE_SIZE,
    SPLIT_SEED,
    TRAIN_VARIANT,
    TRAINABLE_SPECIES,
)
from src.features import extract_vector, feature_spec  # noqa: E402
from src.identify import acceptance, choose_retake_threshold  # noqa: E402
from src.preprocess import cap_per_class, list_labeled_images, load_prepared  # noqa: E402
from src.run_log import append_run  # noqa: E402
from src.select_frames import select_leaf_frames  # noqa: E402
from src.split import split_labels  # noqa: E402
from src.train_svm import evaluate, export_artifacts, make_pipeline  # noqa: E402
from src.tune_svm import best, best_params, search  # noqa: E402

V1_VAL_MACRO_F1 = 0.468
SHAPE_GATE = 0.55
STUDY_TEST_ACCURACY = 0.85
MAX_PER_CLASS = 400
DATA_ROOT = ROOT.parent / "assets" / "species" / "Seagrass"


def featurize(images: list[np.ndarray], tag: str, version: str) -> np.ndarray:
    rows = [
        extract_vector(image, version=version)
        for image in tqdm(images, desc=f"Features {tag} {version}", unit="img")
    ]
    return np.stack(rows, axis=0)


def load_many(paths, labels, tag: str) -> tuple[list[np.ndarray], list[str], int]:
    images: list[np.ndarray] = []
    keep: list[str] = []
    failed = 0
    for path, label in tqdm(list(zip(paths, labels)), desc=f"Load {tag}", unit="img"):
        try:
            images.append(load_prepared(path, size=IMAGE_SIZE))
        except (OSError, ValueError):
            failed += 1
            continue
        keep.append(label)
    return images, keep, failed


def tune(x_train, y_train, x_val, y_val, version: str) -> list[dict]:
    return search(
        x_train,
        y_train,
        x_val,
        y_val,
        seed=SPLIT_SEED,
        progress=lambda params: tqdm(list(params), desc=f"Tune {version}", unit="model"),
    )


def top_calls(model, features: np.ndarray, labels: list[str]) -> tuple[np.ndarray, np.ndarray]:
    proba = model.predict_proba(features)
    classes = [str(name) for name in model.classes_]
    top = proba.argmax(axis=1)
    confidence = proba[np.arange(len(features)), top]
    correct = np.array([classes[int(col)] == truth for col, truth in zip(top, labels)])
    return confidence, correct


def main() -> None:
    parser = argparse.ArgumentParser(description="Curated MarineSee SVM retrain.")
    parser.add_argument("--root", type=Path, default=DATA_ROOT)
    args = parser.parse_args()
    data_root = args.root
    if not data_root.is_dir():
        raise FileNotFoundError(data_root)

    started = datetime.now(timezone.utc)
    listed = list_labeled_images(data_root)
    print("listed", len(listed), dict(Counter(slug for _, slug in listed)))
    kept, selection = select_leaf_frames(listed)
    print(
        "kept",
        selection["kept"],
        "dropped",
        selection["dropped"],
        "habitat waived",
        selection["habitat_waived"] or "none",
        "duplicates",
        selection["duplicates_dropped"],
    )
    print("kept by species", selection["by_slug_kept"])
    pairs = cap_per_class(kept, MAX_PER_CLASS, seed=SPLIT_SEED)
    print("after cap", len(pairs), dict(Counter(slug for _, slug in pairs)))

    train_p, val_p, test_p, split_train_y, split_val_y, test_y = split_labels(
        [path for path, _ in pairs],
        [slug for _, slug in pairs],
        seed=SPLIT_SEED,
    )
    train_img, train_y, train_failed = load_many(train_p, split_train_y, "train")
    val_img, val_y, val_failed = load_many(val_p, split_val_y, "val")
    real_train_counts = dict(Counter(train_y))
    train_img, train_y = augment_train(train_img, train_y, seed=SPLIT_SEED)
    print("train after augment", dict(Counter(train_y)))

    version = "v2"
    x_train = featurize(train_img, "train", version)
    x_val = featurize(val_img, "val", version)
    del train_img, val_img
    gc.collect()
    tuning_rows = tune(x_train, train_y, x_val, val_y, version)
    winner = best(tuning_rows)
    v2_f1 = float(winner["val_macro_f1"])
    v3_f1 = None
    print(f"v2 val macro F1 {v2_f1:.4f}")

    if v2_f1 < SHAPE_GATE:
        print("validation macro F1 under 0.55; adding blade and tip features")
        held_train_y, held_val_y = list(train_y), list(val_y)
        train_img, v3_train_y, _ = load_many(train_p, split_train_y, "train")
        val_img, v3_val_y, _ = load_many(val_p, split_val_y, "val")
        train_img, v3_train_y = augment_train(train_img, v3_train_y, seed=SPLIT_SEED)
        x_train_v3 = featurize(train_img, "train", "v3")
        x_val_v3 = featurize(val_img, "val", "v3")
        del train_img, val_img
        gc.collect()
        rows_v3 = tune(x_train_v3, v3_train_y, x_val_v3, v3_val_y, "v3")
        challenger = best(rows_v3)
        v3_f1 = float(challenger["val_macro_f1"])
        print(f"v3 val macro F1 {v3_f1:.4f}")
        if v3_f1 > v2_f1:
            version = "v3"
            del x_train, x_val
            x_train, x_val = x_train_v3, x_val_v3
            train_y, val_y = v3_train_y, v3_val_y
            tuning_rows = rows_v3
            winner = challenger
        else:
            del x_train_v3, x_val_v3
            train_y, val_y = held_train_y, held_val_y
            print("v2 remains the validation winner")
        gc.collect()

    params = best_params(tuning_rows)
    print("winner", version, params, "val macro F1", f"{float(winner['val_macro_f1']):.4f}")

    model = make_pipeline(SPLIT_SEED, probability=True, **params)
    t0 = time.perf_counter()
    model.fit(x_train, train_y)
    fit_seconds = time.perf_counter() - t0

    val_conf, val_correct = top_calls(model, x_val, val_y)
    retake = choose_retake_threshold(val_conf, val_correct)
    threshold = float(retake["threshold"])
    print(
        "retake threshold",
        f"{threshold:.2f}",
        "val accepted acc",
        retake["accuracy"],
        "coverage",
        f"{float(retake['coverage']):.3f}",
        "line",
        retake["study_line_met"],
    )

    test_img, test_y, test_failed = load_many(test_p, test_y, "test")
    x_test = featurize(test_img, "test", version)
    del test_img
    gc.collect()
    results = {
        name: evaluate(model, features, labels)
        for name, features, labels in (
            ("train", x_train, train_y),
            ("val", x_val, val_y),
            ("test", x_test, test_y),
        )
    }
    test_conf, test_correct = top_calls(model, x_test, test_y)
    test_accepted = acceptance(test_conf, test_correct, threshold)
    for name in ("train", "val", "test"):
        macro = results[name]["report"]["macro avg"]["f1-score"]
        print(f"{name} acc {results[name]['accuracy']:.4f}  macro F1 {macro:.4f}")
    print(
        "test accepted acc",
        test_accepted["accuracy"],
        "coverage",
        f"{test_accepted['coverage']:.3f}",
    )

    test_accuracy = float(results["test"]["accuracy"])
    val_macro = float(winner["val_macro_f1"])
    study_met = test_accuracy >= STUDY_TEST_ACCURACY
    waived = selection["habitat_waived"]
    loss_note = (
        "Curated retrain on leaf-visible frames. Habitat drops when the top of the frame "
        f"is sky-like (sky fraction >= {selection['habitat_sky_fraction']}) and the green "
        f"mask is under {selection['habitat_max_plant_fraction']}. "
        f"Habitat waived for: {', '.join(waived) if waived else 'none'}. "
        f"Exact duplicate files dropped: {selection['duplicates_dropped']}. "
        f"Train-only augment, at most {AUGMENT_SPEC['copies_per_photo']} copies per photo. "
        f"Feature {version}. Validation macro F1 {val_macro:.3f} against locked v1 "
        f"{V1_VAL_MACRO_F1:.3f}. Held-out test accuracy {test_accuracy:.3f} is on this "
        "selected set. The locked run on the unfiltered set was test accuracy 0.421. "
        + (
            "Held-out test accuracy meets the study line of 0.85."
            if study_met
            else "Held-out test accuracy is below the study line of 0.85."
        )
    )

    finished = datetime.now(timezone.utc)
    record = {
        "kind": "svm",
        "runtime": "local",
        "started_at": started.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "elapsed_seconds": round((finished - started).total_seconds(), 1),
        "data_root": str(data_root),
        "max_per_class": MAX_PER_CLASS,
        "split_seed": SPLIT_SEED,
        "image_size": IMAGE_SIZE,
        "variant": TRAIN_VARIANT,
        "feature_version": version,
        "feature_spec": feature_spec(version),
        "augment": AUGMENT_SPEC,
        "selection": {
            "habitat_sky_fraction": selection["habitat_sky_fraction"],
            "habitat_max_plant_fraction": selection["habitat_max_plant_fraction"],
            "min_kept_per_class": selection["min_kept_per_class"],
            "classes_below_minimum": selection["classes_below_minimum"],
            "habitat_frames_kept_by_waiver": selection["habitat_frames_kept_by_waiver"],
            "skip_reasons": selection["skip_reasons"],
            "by_slug_listed": selection["by_slug_listed"],
        },
        "classes": list(TRAINABLE_SPECIES),
        "held_out": list(HELD_OUT_SPECIES),
        "listed": selection["listed"],
        "kept": selection["kept"],
        "skipped": selection["dropped"],
        "duplicates_dropped": selection["duplicates_dropped"],
        "habitat_waived": waived,
        "by_slug_kept": selection["by_slug_kept"],
        "by_slug_dropped": selection["by_slug_dropped"],
        "images_this_run": len(pairs),
        "load_failed": {
            "train": train_failed,
            "val": val_failed,
            "test": test_failed,
        },
        "n_train": len(train_y),
        "n_val": len(val_y),
        "n_test": len(test_y),
        "train_real_counts": real_train_counts,
        "train_class_counts": dict(Counter(train_y)),
        "v2_val_macro_f1": v2_f1,
        "v3_val_macro_f1": v3_f1,
        "shape_gate": SHAPE_GATE,
        "best_val_macro_f1": val_macro,
        "v1_val_macro_f1": V1_VAL_MACRO_F1,
        "best_params": params,
        "tuning_rows": tuning_rows,
        "fit_seconds": round(fit_seconds, 1),
        "train_accuracy": results["train"]["accuracy"],
        "val_accuracy": results["val"]["accuracy"],
        "test_accuracy": test_accuracy,
        "train_report": results["train"]["report"],
        "val_report": results["val"]["report"],
        "test_report": results["test"]["report"],
        "confusion_matrix_test": results["test"]["confusion_matrix"],
        "retake_threshold": threshold,
        "retake_rule": retake["rule"],
        "retake_study_line_met": bool(retake["study_line_met"]),
        "val_accepted_accuracy": retake["accuracy"],
        "val_accepted_coverage": float(retake["coverage"]),
        "test_accepted_accuracy": test_accepted["accuracy"],
        "test_accepted_coverage": float(test_accepted["coverage"]),
        "study_target_accuracy": STUDY_TEST_ACCURACY,
        "study_line_met": study_met,
        "prior_locked_test_accuracy": 0.421,
        "loss_note": loss_note,
    }
    append_run(ROOT.parent, record)

    if val_macro > V1_VAL_MACRO_F1:
        dest = ROOT / "artifacts" / "v2"
        export_artifacts(
            model,
            record,
            dest,
            filename="svm_seagrass_v2.joblib",
            feature_spec=feature_spec(version),
        )
        print("wrote", dest)
    else:
        print("validation macro F1 did not beat 0.468; left ml/artifacts/v1 in place")


if __name__ == "__main__":
    main()
