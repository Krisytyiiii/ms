# svm 20261116T111852655Z

- recorded_at: 2026-11-16T11:18:52Z
- started_at: 2026-11-16T11:15:53Z
- elapsed_seconds: 179.6
- runtime: local
- data_root: C:\Users\Akiro\MarineSeeData\Seagrass
- max_per_class: 400
- split_seed: 42
- fit_seconds: 1.3
- best_params: {'kernel': 'rbf', 'C': 3.0, 'gamma': 0.003}
- best_val_macro_f1: 0.21940745860639296
- n_train: 1974
- n_val: 290
- n_test: 290
- train_accuracy: 0.720871327254306
- val_accuracy: 0.296551724137931
- test_accuracy: 0.3448275862068966
- v2_val_macro_f1: 0.23394128863595806
- v3_val_macro_f1: 0.23127953067494894
- feature_version: v2
- retake_threshold: 0.39
- val_accepted_accuracy: 0.3708609271523179
- val_accepted_coverage: 0.5206896551724138
- test_accepted_accuracy: 0.3916083916083916
- test_accepted_coverage: 0.49310344827586206
- study_line_met: False
- retake_study_line_met: False
- retake_rule: best accepted accuracy with coverage >= 0.50
- duplicates_dropped: 29
- habitat_waived: []
- listed: 3896
- kept: 3701
- skipped: 195

## selection

| slug | kept | dropped |
|---|---:|---:|
| cymodocea_rotundata | 149 | 9 |
| cymodocea_serrulata | 84 | 3 |
| enhalus_acoroides | 634 | 32 |
| halodule_pinifolia | 75 | 10 |
| halodule_uninervis | 347 | 28 |
| halophila_minor | 23 | 1 |
| halophila_ovalis | 1487 | 62 |
| syringodium_isoetifolium | 154 | 7 |
| thalassia_hemprichii | 748 | 43 |

Curated retrain on leaf-visible frames. Habitat drops when the top of the frame is sky-like (sky fraction >= 0.5) and the green mask is under 0.02. Habitat waived for: none. Exact duplicate files dropped: 29. Train-only augment, at most 3 copies per photo. Feature v2. Validation macro F1 0.219 against locked v1 0.468. Held-out test accuracy 0.345 is on this selected set. The locked run on the unfiltered set was test accuracy 0.421. Held-out test accuracy is below the study line of 0.85.

## tuning (top 10 by grouped CV)

| kernel | C | gamma | CV folds | CV macro F1 mean | SD | SE | CV acc |
|---|---:|---:|---:|---:|---:|---:|---:|
| rbf | 30.0 | 0.001 | 5 | 0.241 | 0.022 | 0.010 | 0.332 |
| rbf | 10.0 | 0.003 | 5 | 0.241 | 0.028 | 0.013 | 0.336 |
| rbf | 3.0 | scale | 5 | 0.239 | 0.020 | 0.009 | 0.341 |
| rbf | 100.0 | 0.001 | 5 | 0.238 | 0.038 | 0.017 | 0.326 |
| linear | 0.1 | None | 5 | 0.237 | 0.017 | 0.008 | 0.312 |
| linear | 0.3 | None | 5 | 0.237 | 0.025 | 0.011 | 0.304 |
| rbf | 3.0 | 0.003 | 5 | 0.234 | 0.025 | 0.011 | 0.320 |
| linear | 0.03 | None | 5 | 0.233 | 0.018 | 0.008 | 0.302 |
| linear | 0.01 | None | 5 | 0.233 | 0.028 | 0.013 | 0.296 |
| rbf | 3.0 | 0.01 | 5 | 0.232 | 0.029 | 0.013 | 0.341 |

## train

| slug | precision | recall | f1 | support |
|---|---:|---:|---:|---:|
| cymodocea_rotundata | 0.799 | 0.675 | 0.732 | 200.0 |
| cymodocea_serrulata | 0.875 | 0.770 | 0.819 | 200.0 |
| enhalus_acoroides | 0.706 | 0.713 | 0.710 | 286.0 |
| halodule_pinifolia | 0.899 | 0.845 | 0.871 | 200.0 |
| halodule_uninervis | 0.732 | 0.585 | 0.650 | 248.0 |
| halophila_minor | 0.984 | 0.926 | 0.955 | 68.0 |
| halophila_ovalis | 0.748 | 0.675 | 0.710 | 286.0 |
| syringodium_isoetifolium | 0.743 | 0.750 | 0.746 | 200.0 |
| thalassia_hemprichii | 0.488 | 0.734 | 0.587 | 286.0 |
| macro avg | 0.775 | 0.742 | 0.753 | 1974.0 |
| weighted avg | 0.743 | 0.721 | 0.726 | 1974.0 |

## val

| slug | precision | recall | f1 | support |
|---|---:|---:|---:|---:|
| cymodocea_rotundata | 0.000 | 0.000 | 0.000 | 22.0 |
| cymodocea_serrulata | 0.000 | 0.000 | 0.000 | 12.0 |
| enhalus_acoroides | 0.377 | 0.404 | 0.390 | 57.0 |
| halodule_pinifolia | 0.438 | 0.636 | 0.519 | 11.0 |
| halodule_uninervis | 0.375 | 0.245 | 0.296 | 49.0 |
| halophila_minor | 0.000 | 0.000 | 0.000 | 3.0 |
| halophila_ovalis | 0.273 | 0.316 | 0.293 | 57.0 |
| syringodium_isoetifolium | 0.133 | 0.091 | 0.108 | 22.0 |
| thalassia_hemprichii | 0.329 | 0.421 | 0.369 | 57.0 |
| macro avg | 0.214 | 0.235 | 0.219 | 290.0 |
| weighted avg | 0.282 | 0.297 | 0.285 | 290.0 |

## test

| slug | precision | recall | f1 | support |
|---|---:|---:|---:|---:|
| cymodocea_rotundata | 0.273 | 0.286 | 0.279 | 21.0 |
| cymodocea_serrulata | 0.182 | 0.167 | 0.174 | 12.0 |
| enhalus_acoroides | 0.452 | 0.491 | 0.471 | 57.0 |
| halodule_pinifolia | 0.357 | 0.455 | 0.400 | 11.0 |
| halodule_uninervis | 0.263 | 0.200 | 0.227 | 50.0 |
| halophila_minor | 0.000 | 0.000 | 0.000 | 3.0 |
| halophila_ovalis | 0.375 | 0.368 | 0.372 | 57.0 |
| syringodium_isoetifolium | 0.154 | 0.091 | 0.114 | 22.0 |
| thalassia_hemprichii | 0.351 | 0.456 | 0.397 | 57.0 |
| macro avg | 0.267 | 0.279 | 0.270 | 290.0 |
| weighted avg | 0.329 | 0.345 | 0.334 | 290.0 |
