"""Curated nine-class SVM. Tune on real rows, then score the test split once.

Leaf-visible selection, exact-duplicate removal, and observation grouping happen
before the split. Augmentation is train-only and is applied after selection, so
the tuning rows are real photos. Artifacts land in the version named by
`--dest-version`; the fixed validation split still gates the export, so a new
run cannot silently replace a better-validated model.

    python ml/src/train_curated.py --split grouped --dest-version v3 --cv-folds 5
    python ml/src/train_curated.py --root D:\\path\\to\\Seagrass --no-cap
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
from src.cache import Cache  # noqa: E402
from src.cache import dhash_value, qc_reason, prepared as cached_prepared  # noqa: E402
from src.cache import vector as cached_vector  # noqa: E402
from src.dataset_contract import (  # noqa: E402
    HELD_OUT_SPECIES,
    IMAGE_SIZE,
    SPLIT_SEED,
    TRAIN_VARIANT,
    TRAINABLE_SPECIES,
)
from src.features import extract_vector, feature_spec  # noqa: E402
from src.identify import acceptance, choose_retake_threshold  # noqa: E402
from src.metrics_extra import build_summary, voted_calls  # noqa: E402
from src.phash import split_groups  # noqa: E402
from src.preprocess import cap_per_class, list_labeled_images  # noqa: E402
from src.run_log import append_run  # noqa: E402
from src.select_frames import select_leaf_frames  # noqa: E402
from src.split import split_labels, split_labels_grouped  # noqa: E402
from src.thresholds import accept_mask, answering_classes, choose_class_thresholds  # noqa: E402
from src.thresholds import summarise as summarise_acceptance  # noqa: E402
from src.train_svm import balanced_weights, evaluate, export_artifacts, make_pipeline  # noqa: E402
from src.tune_svm import best, best_1se, params_of, search, search_grouped_cv  # noqa: E402

V1_VAL_MACRO_F1 = 0.468
SHAPE_GATE = 0.55
STUDY_TEST_ACCURACY = 0.85
MAX_PER_CLASS = 400
DATA_ROOT = ROOT.parent / "assets" / "species" / "Seagrass"


def featurize(
    images: list[np.ndarray],
    tag: str,
    version: str,
    paths: list[Path] | None = None,
    cache: Cache | None = None,
) -> np.ndarray:
    """Feature matrix for prepared frames.

    When `paths` names the source file of a row, the vector is cached per file
    and feature version, so a retrain that only changes SVM parameters does not
    re-extract it. Augmented rows pass `paths[i] = None` and are always computed.
    """
    rows = []
    for index, image in enumerate(tqdm(images, desc=f"Features {tag} {version}", unit="img")):
        path = paths[index] if paths is not None else None
        if cache is not None and path is not None:
            rows.append(cached_vector(cache, Path(path), version, image=image))
        else:
            rows.append(extract_vector(image, version=version))
    return np.stack(rows, axis=0)


def load_many_grouped(paths, labels, groups, tag: str, cache: Cache | None = None):
    """Load prepared frames, keeping each row's observation group aligned.

    Unreadable files are dropped together with the group id they belong to, so
    the group list cannot drift out of step with the labels.
    """
    images: list[np.ndarray] = []
    keep: list[str] = []
    keep_groups: list[int] = []
    keep_paths: list[Path] = []
    failed = 0
    for path, label, group in tqdm(
        list(zip(paths, labels, groups)), desc=f"Load {tag}", unit="img"
    ):
        try:
            if cache is not None:
                images.append(cached_prepared(cache, Path(path), IMAGE_SIZE))
            else:
                from src.preprocess import load_prepared

                images.append(load_prepared(path, size=IMAGE_SIZE))
        except (OSError, ValueError):
            failed += 1
            continue
        keep.append(label)
        keep_groups.append(int(group))
        keep_paths.append(Path(path))
    return images, keep, keep_groups, keep_paths, failed


def main() -> None:
    parser = argparse.ArgumentParser(description="Curated MarineSee SVM retrain.")
    parser.add_argument("--root", type=Path, default=DATA_ROOT)
    parser.add_argument(
        "--split",
        choices=("image", "grouped"),
        default="image",
        help=(
            "image = v2 behaviour (frames from one photoshoot may straddle the "
            "split); grouped = one observation per split, no near-duplicate leaks"
        ),
    )
    parser.add_argument(
        "--dest-version",
        default="v2",
        help="artifact folder to write, e.g. v3. Grouped runs must name a new one.",
    )
    parser.add_argument(
        "--cv-folds",
        type=int,
        default=5,
        help=(
            "grouped cross-validation folds for hyperparameter selection. "
            "1 keeps the old single validation split; 0 disables CV too"
        ),
    )
    parser.add_argument(
        "--max-per-class",
        type=int,
        default=MAX_PER_CLASS,
        help="random real-photo cap per class before the split; 0 keeps every photo",
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=1.0,
        help=(
            "exponent on inverse-frequency class weights: 0 = none, "
            "1 = sklearn 'balanced', >1 = extra weight for small classes"
        ),
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="ignore the on-disk QC / hash / feature cache",
    )
    args = parser.parse_args()
    if args.split == "grouped" and args.dest_version == "v2":
        raise SystemExit(
            "a grouped split changes the model. Pass --dest-version v3 "
            "(or another new name) so the shipped v2 artifact is not overwritten. "
            "Nothing was written."
        )
    data_root = args.root
    if not data_root.is_dir():
        raise FileNotFoundError(data_root)
    cache = Cache(enabled=not args.no_cache)
    max_per_class = args.max_per_class or None

    started = datetime.now(timezone.utc)
    listed = list_labeled_images(data_root)
    print("listed", len(listed), dict(Counter(slug for _, slug in listed)))
    kept, selection = select_leaf_frames(
        listed, reason_fn=lambda path: qc_reason(cache, path)
    )
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
    pairs = cap_per_class(kept, max_per_class, seed=SPLIT_SEED)
    print("after cap", len(pairs), dict(Counter(slug for _, slug in pairs)))

    # Observation groups are always computed, even for an image-level split:
    # the straddle count is what shows how much the ungrouped number flatters.
    pair_paths = [path for path, _ in pairs]
    pair_labels = [slug for _, slug in pairs]
    pair_hashes = [dhash_value(cache, path) for path in pair_paths]
    group_ids, group_report = split_groups(
        pair_paths, labels=pair_labels, hashes=pair_hashes
    )
    group_of = {str(path): gid for path, gid in zip(pair_paths, group_ids)}
    print(
        "groups",
        group_report["n_groups"],
        "mode",
        group_report["mode"],
        "near-dup pairs",
        group_report["near_duplicate_pairs"],
        "largest",
        group_report["largest_group"],
    )
    if group_report["cross_class_near_duplicates"]:
        print(
            f"WARNING {group_report['cross_class_near_duplicates']} near-duplicate "
            "pair(s) span two classes. Those files are either mislabelled or the "
            "same plant filed twice; they are not merged into one group, but they "
            "are a label problem and belong in the audit."
        )
    if group_report.get("cross_class_observations"):
        print(
            f"WARNING {group_report['cross_class_observations']} iNaturalist "
            "observation id(s) appear under two species. Same photo filed twice; "
            "kept out of one group so stratification survives."
        )
    if group_report["largest_group"] > max(len(pair_paths) // 4, 25):
        print(
            f"WARNING largest observation group holds {group_report['largest_group']} "
            "of "
            f"{len(pair_paths)} images. Near-duplicate chaining is collapsing the "
            "pool; the grouped split will be coarse."
        )

    pair_groups = [group_of[str(path)] for path in pair_paths]

    if args.split == "grouped":
        (
            train_p,
            val_p,
            test_p,
            split_train_y,
            split_val_y,
            test_y,
            split_report,
        ) = split_labels_grouped(
            pair_paths, pair_labels, pair_groups, seed=SPLIT_SEED
        )
    else:
        train_p, val_p, test_p, split_train_y, split_val_y, test_y = split_labels(
            pair_paths, pair_labels, seed=SPLIT_SEED
        )
        split_groups_seen = {
            "train": {group_of[str(path)] for path in train_p},
            "val": {group_of[str(path)] for path in val_p},
            "test": {group_of[str(path)] for path in test_p},
        }
        straddle = (
            (split_groups_seen["train"] & split_groups_seen["val"])
            | (split_groups_seen["train"] & split_groups_seen["test"])
            | (split_groups_seen["val"] & split_groups_seen["test"])
        )
        split_report = {
            "mode": "image-stratified",
            "n_train": len(train_p),
            "n_val": len(val_p),
            "n_test": len(test_p),
            "class_counts": {
                "train": dict(Counter(split_train_y)),
                "val": dict(Counter(split_val_y)),
                "test": dict(Counter(test_y)),
            },
            "groups_in_more_than_one_split": len(straddle),
            "note": (
                "Image-level split: observation groups can straddle, so the "
                "held-out score is optimistic. Use --split grouped for the "
                "defensible number."
            ),
        }
        if straddle:
            print(
                f"WARNING {len(straddle)} observation group(s) span two splits; "
                "the held-out score is inflated. See --split grouped."
            )
    print(
        "split",
        split_report["mode"],
        "train",
        split_report["n_train"],
        "val",
        split_report["n_val"],
        "test",
        split_report["n_test"],
    )
    if args.split == "grouped":
        if split_report["classes_missing_from_val"]:
            print(
                "WARNING classes absent from validation:",
                ", ".join(split_report["classes_missing_from_val"]),
            )
        if split_report["classes_missing_from_test"]:
            print(
                "WARNING classes absent from test:",
                ", ".join(split_report["classes_missing_from_test"]),
            )
        if split_report["degraded"]:
            print(
                "WARNING grouped split is degraded: the macro F1 below is a mean "
                "over the classes that were actually held out, not over all "
                f"{len(set(pair_labels))}. Report it with this list attached."
            )

    train_img, train_y, train_groups, train_paths, train_failed = load_many_grouped(
        train_p,
        split_train_y,
        [group_of[str(path)] for path in train_p],
        "train",
        cache=cache,
    )
    val_img, val_y, val_groups, val_paths, val_failed = load_many_grouped(
        val_p,
        split_val_y,
        [group_of[str(path)] for path in val_p],
        "val",
        cache=cache,
    )
    real_train_counts = dict(Counter(train_y))
    class_weight = balanced_weights(train_y, alpha=args.alpha) if args.alpha > 0 else None

    def select_for(version: str):
        """Tune on real rows only; augmented copies would flatter high C (plan 2.2)."""
        x_real = featurize(train_img, "train", version, paths=train_paths, cache=cache)
        x_val_version = featurize(val_img, "val", version, paths=val_paths, cache=cache)
        if args.cv_folds >= 2:
            rows = search_grouped_cv(
                x_real,
                train_y,
                train_groups,
                n_splits=args.cv_folds,
                seed=SPLIT_SEED,
                progress=lambda grid: tqdm(
                    list(grid), desc=f"CV {version}", unit="model"
                ),
            )
            champion = best_1se(rows)
            score = float(champion["cv_macro_f1_mean"])
            print(
                f"{version} grouped CV macro F1 {score:.4f} "
                f"+/- {float(champion['cv_macro_f1_se']):.4f}"
            )
        else:
            rows = search(
                x_real,
                train_y,
                x_val_version,
                val_y,
                seed=SPLIT_SEED,
                progress=lambda grid: tqdm(
                    list(grid), desc=f"Tune {version}", unit="model"
                ),
            )
            champion = best(rows)
            score = float(champion["val_macro_f1"])
            print(f"{version} val macro F1 {score:.4f}")
        print(f"  chosen {version} {params_of(champion)}")
        return rows, champion, score, x_real, x_val_version

    tuning_rows, winner, v2_f1, x_train_real, x_val = select_for("v2")
    v3_f1 = None
    version = "v2"

    if v2_f1 < SHAPE_GATE:
        print("selection score under 0.55; adding blade and tip features")
        rows_v3, challenger, v3_f1, x_train_real_v3, x_val_v3 = select_for("v3")
        if v3_f1 > v2_f1:
            version = "v3"
            tuning_rows, winner = rows_v3, challenger
            x_train_real, x_val = x_train_real_v3, x_val_v3
        else:
            print("v2 remains the winner")

    params = params_of(winner)
    print("winner", version, params)
    del x_train_real

    # Augmented copies are built only for the final fit, after selection.
    aug_img, aug_y = augment_train(train_img, train_y, seed=SPLIT_SEED)
    print("train after augment", dict(Counter(aug_y)))
    aug_paths = list(train_paths) + [None] * (len(aug_img) - len(train_paths))
    x_train = featurize(aug_img, "train", version, paths=aug_paths, cache=cache)
    del aug_img, train_img, val_img
    gc.collect()
    train_y = aug_y

    model = make_pipeline(
        SPLIT_SEED, probability=True, class_weight=class_weight, **params
    )
    t0 = time.perf_counter()
    model.fit(x_train, train_y)
    fit_seconds = time.perf_counter() - t0

    val_conf, val_correct, val_pred = voted_calls(model, x_val, val_y)
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

    # Per-class acceptance thresholds (plan row 2.6). A class either earns its
    # own threshold on validation or abstains, which the app reads as "retake".
    class_names = [str(name) for name in model.classes_]
    index_of = {slug: index for index, slug in enumerate(class_names)}
    val_proba = model.predict_proba(x_val)
    val_pred_idx = np.asarray([index_of[slug] for slug in val_pred], dtype=int)
    val_true_idx = np.asarray([index_of[slug] for slug in val_y], dtype=int)
    class_thresholds = choose_class_thresholds(
        val_proba, val_pred_idx, val_true_idx, class_names
    )
    val_class_mask = accept_mask(val_proba, val_pred_idx, class_thresholds, class_names)
    val_class_accepted = summarise_acceptance(val_class_mask, val_pred_idx == val_true_idx)
    print(
        "per-class thresholds",
        f"{len(answering_classes(class_thresholds))}/{len(class_names)} classes answer",
        "val accepted acc",
        val_class_accepted["accuracy"],
        "coverage",
        f"{val_class_accepted['coverage']:.3f}",
    )

    test_img, test_y, test_groups, test_paths, test_failed = load_many_grouped(
        test_p,
        test_y,
        [group_of[str(path)] for path in test_p],
        "test",
        cache=cache,
    )
    x_test = featurize(test_img, "test", version, paths=test_paths, cache=cache)
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
    test_conf, test_correct, test_pred = voted_calls(model, x_test, test_y)
    test_accepted = acceptance(test_conf, test_correct, threshold)
    test_proba = model.predict_proba(x_test)
    test_pred_idx = np.asarray([index_of[slug] for slug in test_pred], dtype=int)
    test_true_idx = np.asarray([index_of[slug] for slug in test_y], dtype=int)
    test_class_mask = accept_mask(test_proba, test_pred_idx, class_thresholds, class_names)
    test_class_accepted = summarise_acceptance(
        test_class_mask, test_pred_idx == test_true_idx
    )
    for name in ("train", "val", "test"):
        macro = results[name]["report"]["macro avg"]["f1-score"]
        print(f"{name} acc {results[name]['accuracy']:.4f}  macro F1 {macro:.4f}")
    print(
        "test accepted acc",
        test_accepted["accuracy"],
        "coverage",
        f"{test_accepted['coverage']:.3f}",
    )
    print(
        "test accepted acc per-class",
        test_class_accepted["accuracy"],
        "coverage",
        f"{test_class_accepted['coverage']:.3f}",
    )

    # The multiclass numbers the plan asks for, with a grouped bootstrap CI.
    # `predictions` is the one-vs-one vote -- the rule the app and `identify.py`
    # both use -- so accuracy, balanced accuracy, per-class recall and the CI all
    # describe the same classifier as `test_report`. The probability-argmax view
    # is kept beside it, clearly named, because it is a different rule.
    test_metrics = build_summary(
        model.predict_proba(x_test),
        list(model.classes_),
        test_y,
        groups=test_groups,
        predictions=test_pred,
    )
    test_metrics_proba_argmax = build_summary(
        model.predict_proba(x_test), list(model.classes_), test_y, groups=test_groups
    )
    val_metrics = build_summary(
        model.predict_proba(x_val),
        list(model.classes_),
        val_y,
        groups=val_groups,
        predictions=val_pred,
    )
    print(
        "test acc rule",
        "vote",
        f"{test_metrics['accuracy']:.4f}",
        "proba-argmax",
        f"{test_metrics_proba_argmax['accuracy']:.4f}",
        "(the app ships the vote)",
    )
    print(
        "test balanced acc",
        f"{test_metrics['balanced_accuracy']:.4f}",
        "top-2",
        f"{test_metrics['top2_accuracy']:.4f}",
        "top-3",
        f"{test_metrics['top3_accuracy']:.4f}",
        "acc CI",
        f"[{test_metrics['accuracy_ci']['low']:.3f}, "
        f"{test_metrics['accuracy_ci']['high']:.3f}]",
    )
    for row in test_metrics["coverage_accuracy"]:
        acc = row["accuracy"]
        print(
            f"  coverage {row['coverage']:.3f} at threshold {row['threshold']:.2f} "
            f"-> accuracy {'n/a' if acc is None else f'{acc:.3f}'}"
        )

    test_accuracy = float(results["test"]["accuracy"])
    val_macro = float(results["val"]["report"]["macro avg"]["f1-score"])
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
        "max_per_class": max_per_class,
        "split_seed": SPLIT_SEED,
        "image_size": IMAGE_SIZE,
        "variant": TRAIN_VARIANT,
        "feature_version": version,
        "feature_spec": feature_spec(version),
        "augment": AUGMENT_SPEC,
        "protocol": {
            "selection": (
                f"grouped {args.cv_folds}-fold CV, one-standard-error rule"
                if args.cv_folds >= 2
                else "single fixed validation split"
            ),
            "cv_folds": args.cv_folds,
            "tuning_rows": "real photos only",
            "class_weight_alpha": args.alpha,
            "cache": cache.summary(),
        },
        "observation_grouping": group_report,
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
        "split_mode": args.split,
        "split_report": split_report,
        "group_report": group_report,
        "train_real_counts": real_train_counts,
        "train_class_counts": dict(Counter(train_y)),
        "v2_val_macro_f1": v2_f1,
        "v3_val_macro_f1": v3_f1,
        "shape_gate": SHAPE_GATE,
        "best_val_macro_f1": val_macro,
        "selection_scores": {"v2": v2_f1, "v3": v3_f1},
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
        "class_thresholds": class_thresholds,
        "class_threshold_rule": (
            "per predicted class on validation; >=5 photos and above chance, else abstain"
        ),
        "val_accepted_class_thresholds": val_class_accepted,
        "test_accepted_class_thresholds": test_class_accepted,
        "val_metrics": val_metrics,
        "test_metrics": test_metrics,
        "test_metrics_proba_argmax": test_metrics_proba_argmax,
        "decision_rule": (
            "one_vs_one_vote for report/accuracy/balanced/per-class/acceptance; "
            "top-2/3 are the probability ranking; probability-argmax view is recorded "
            "separately as test_metrics_proba_argmax"
        ),
        "study_target_accuracy": STUDY_TEST_ACCURACY,
        "study_line_met": study_met,
        "prior_locked_test_accuracy": 0.421,
        "loss_note": loss_note,
    }
    append_run(ROOT.parent, record)

    if val_macro > V1_VAL_MACRO_F1:
        dest = ROOT / "artifacts" / args.dest_version
        export_artifacts(
            model,
            record,
            dest,
            filename=f"svm_seagrass_{args.dest_version}.joblib",
            feature_spec=feature_spec(version),
        )
        print("wrote", dest)
    else:
        print(
            "validation macro F1 did not beat 0.468; nothing exported. "
            f"v1 and {args.dest_version} are untouched."
        )


if __name__ == "__main__":
    main()
