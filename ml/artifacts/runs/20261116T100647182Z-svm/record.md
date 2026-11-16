# svm 20261116T100647182Z

- recorded_at: 2026-11-16T10:06:47Z
- started_at: 2026-11-16T09:52:12Z
- elapsed_seconds: 875.1
- runtime: local
- data_root: C:\Users\Akiro\MarineSeeData\Seagrass
- split_seed: 42
- fit_seconds: 3.7
- best_params: {'kernel': 'rbf', 'C': 3.0, 'gamma': 0.003}
- best_val_macro_f1: 0.2751250568279554
- n_train: 3162
- n_val: 529
- n_test: 529
- train_accuracy: 0.711258697027198
- val_accuracy: 0.497164461247637
- test_accuracy: 0.4706994328922495
- v2_val_macro_f1: 0.22462136008862163
- v3_val_macro_f1: 0.2276664061162205
- feature_version: v3
- retake_threshold: 0.45
- val_accepted_accuracy: 0.6078431372549019
- val_accepted_coverage: 0.5784499054820416
- test_accepted_accuracy: 0.5833333333333334
- test_accepted_coverage: 0.5444234404536862
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

Curated retrain on leaf-visible frames. Habitat drops when the top of the frame is sky-like (sky fraction >= 0.5) and the green mask is under 0.02. Habitat waived for: none. Exact duplicate files dropped: 29. Train-only augment, at most 3 copies per photo. Feature v3. Validation macro F1 0.275 against locked v1 0.468. Held-out test accuracy 0.471 is on this selected set. The locked run on the unfiltered set was test accuracy 0.421. Held-out test accuracy is below the study line of 0.85.

## tuning (top 10 by grouped CV)

| kernel | C | gamma | CV folds | CV macro F1 mean | SD | SE | CV acc |
|---|---:|---:|---:|---:|---:|---:|---:|
| rbf | 100.0 | 0.001 | 5 | 0.234 | 0.024 | 0.011 | 0.398 |
| rbf | 10.0 | 0.003 | 5 | 0.233 | 0.025 | 0.011 | 0.405 |
| rbf | 30.0 | 0.001 | 5 | 0.229 | 0.022 | 0.010 | 0.379 |
| rbf | 3.0 | 0.003 | 5 | 0.228 | 0.034 | 0.015 | 0.367 |
| rbf | 3.0 | scale | 5 | 0.224 | 0.032 | 0.014 | 0.407 |
| rbf | 10.0 | 0.001 | 5 | 0.223 | 0.020 | 0.009 | 0.344 |
| rbf | 1.0 | scale | 5 | 0.222 | 0.030 | 0.013 | 0.362 |
| linear | 0.3 | None | 5 | 0.219 | 0.025 | 0.011 | 0.341 |
| rbf | 30.0 | 0.003 | 5 | 0.218 | 0.025 | 0.011 | 0.410 |
| linear | 0.1 | None | 5 | 0.218 | 0.025 | 0.011 | 0.330 |

## train

| slug | precision | recall | f1 | support |
|---|---:|---:|---:|---:|
| cymodocea_rotundata | 0.852 | 0.575 | 0.687 | 200.0 |
| cymodocea_serrulata | 0.938 | 0.600 | 0.732 | 200.0 |
| enhalus_acoroides | 0.728 | 0.656 | 0.690 | 453.0 |
| halodule_pinifolia | 0.935 | 0.865 | 0.899 | 200.0 |
| halodule_uninervis | 0.841 | 0.468 | 0.601 | 248.0 |
| halophila_minor | 1.000 | 0.750 | 0.857 | 64.0 |
| halophila_ovalis | 0.642 | 0.908 | 0.752 | 1062.0 |
| syringodium_isoetifolium | 0.928 | 0.580 | 0.714 | 200.0 |
| thalassia_hemprichii | 0.609 | 0.561 | 0.584 | 535.0 |
| macro avg | 0.830 | 0.662 | 0.724 | 3162.0 |
| weighted avg | 0.740 | 0.711 | 0.706 | 3162.0 |

## val

| slug | precision | recall | f1 | support |
|---|---:|---:|---:|---:|
| cymodocea_rotundata | 0.000 | 0.000 | 0.000 | 22.0 |
| cymodocea_serrulata | 0.000 | 0.000 | 0.000 | 12.0 |
| enhalus_acoroides | 0.600 | 0.500 | 0.545 | 90.0 |
| halodule_pinifolia | 0.600 | 0.545 | 0.571 | 11.0 |
| halodule_uninervis | 0.267 | 0.082 | 0.125 | 49.0 |
| halophila_minor | 0.000 | 0.000 | 0.000 | 3.0 |
| halophila_ovalis | 0.528 | 0.756 | 0.622 | 213.0 |
| syringodium_isoetifolium | 0.300 | 0.136 | 0.188 | 22.0 |
| thalassia_hemprichii | 0.440 | 0.411 | 0.425 | 107.0 |
| macro avg | 0.304 | 0.270 | 0.275 | 529.0 |
| weighted avg | 0.453 | 0.497 | 0.460 | 529.0 |

## test

| slug | precision | recall | f1 | support |
|---|---:|---:|---:|---:|
| cymodocea_rotundata | 0.111 | 0.048 | 0.067 | 21.0 |
| cymodocea_serrulata | 0.333 | 0.083 | 0.133 | 12.0 |
| enhalus_acoroides | 0.410 | 0.352 | 0.379 | 91.0 |
| halodule_pinifolia | 0.375 | 0.273 | 0.316 | 11.0 |
| halodule_uninervis | 0.400 | 0.120 | 0.185 | 50.0 |
| halophila_minor | 0.000 | 0.000 | 0.000 | 4.0 |
| halophila_ovalis | 0.549 | 0.759 | 0.638 | 212.0 |
| syringodium_isoetifolium | 0.111 | 0.045 | 0.065 | 22.0 |
| thalassia_hemprichii | 0.389 | 0.415 | 0.402 | 106.0 |
| macro avg | 0.298 | 0.233 | 0.243 | 529.0 |
| weighted avg | 0.431 | 0.471 | 0.434 | 529.0 |
