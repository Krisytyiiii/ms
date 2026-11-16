# svm 20261116T112417350Z

- recorded_at: 2026-11-16T11:24:17Z
- started_at: 2026-11-16T11:17:25Z
- elapsed_seconds: 411.7
- runtime: local
- data_root: C:\Users\Akiro\MarineSeeData\Seagrass
- split_seed: 42
- fit_seconds: 4.4
- best_params: {'kernel': 'rbf', 'C': 3.0, 'gamma': 0.003}
- best_val_macro_f1: 0.29233754514777743
- n_train: 3162
- n_val: 529
- n_test: 529
- train_accuracy: 0.7245414294750158
- val_accuracy: 0.4612476370510397
- test_accuracy: 0.42344045368620037
- v2_val_macro_f1: 0.22462136008862163
- v3_val_macro_f1: 0.2276664061162205
- feature_version: v3
- retake_threshold: 0.49
- val_accepted_accuracy: 0.6185185185185185
- val_accepted_coverage: 0.5103969754253308
- test_accepted_accuracy: 0.6008403361344538
- test_accepted_coverage: 0.4499054820415879
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

Curated retrain on leaf-visible frames. Habitat drops when the top of the frame is sky-like (sky fraction >= 0.5) and the green mask is under 0.02. Habitat waived for: none. Exact duplicate files dropped: 29. Train-only augment, at most 3 copies per photo. Feature v3. Validation macro F1 0.292 against locked v1 0.468. Held-out test accuracy 0.423 is on this selected set. The locked run on the unfiltered set was test accuracy 0.421. Held-out test accuracy is below the study line of 0.85.

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
| cymodocea_rotundata | 0.748 | 0.770 | 0.759 | 200.0 |
| cymodocea_serrulata | 0.591 | 0.955 | 0.730 | 200.0 |
| enhalus_acoroides | 0.700 | 0.704 | 0.702 | 453.0 |
| halodule_pinifolia | 0.824 | 0.985 | 0.897 | 200.0 |
| halodule_uninervis | 0.766 | 0.516 | 0.617 | 248.0 |
| halophila_minor | 0.941 | 1.000 | 0.970 | 64.0 |
| halophila_ovalis | 0.803 | 0.718 | 0.758 | 1062.0 |
| syringodium_isoetifolium | 0.785 | 0.785 | 0.785 | 200.0 |
| thalassia_hemprichii | 0.575 | 0.594 | 0.585 | 535.0 |
| macro avg | 0.748 | 0.781 | 0.756 | 3162.0 |
| weighted avg | 0.733 | 0.725 | 0.723 | 3162.0 |

## val

| slug | precision | recall | f1 | support |
|---|---:|---:|---:|---:|
| cymodocea_rotundata | 0.029 | 0.045 | 0.035 | 22.0 |
| cymodocea_serrulata | 0.192 | 0.417 | 0.263 | 12.0 |
| enhalus_acoroides | 0.534 | 0.522 | 0.528 | 90.0 |
| halodule_pinifolia | 0.273 | 0.545 | 0.364 | 11.0 |
| halodule_uninervis | 0.318 | 0.143 | 0.197 | 49.0 |
| halophila_minor | 0.000 | 0.000 | 0.000 | 3.0 |
| halophila_ovalis | 0.618 | 0.592 | 0.604 | 213.0 |
| syringodium_isoetifolium | 0.211 | 0.182 | 0.195 | 22.0 |
| thalassia_hemprichii | 0.440 | 0.449 | 0.444 | 107.0 |
| macro avg | 0.290 | 0.322 | 0.292 | 529.0 |
| weighted avg | 0.478 | 0.461 | 0.464 | 529.0 |

## test

| slug | precision | recall | f1 | support |
|---|---:|---:|---:|---:|
| cymodocea_rotundata | 0.087 | 0.095 | 0.091 | 21.0 |
| cymodocea_serrulata | 0.022 | 0.083 | 0.035 | 12.0 |
| enhalus_acoroides | 0.411 | 0.407 | 0.409 | 91.0 |
| halodule_pinifolia | 0.200 | 0.364 | 0.258 | 11.0 |
| halodule_uninervis | 0.429 | 0.240 | 0.308 | 50.0 |
| halophila_minor | 0.000 | 0.000 | 0.000 | 4.0 |
| halophila_ovalis | 0.629 | 0.528 | 0.574 | 212.0 |
| syringodium_isoetifolium | 0.357 | 0.227 | 0.278 | 22.0 |
| thalassia_hemprichii | 0.389 | 0.481 | 0.430 | 106.0 |
| macro avg | 0.281 | 0.270 | 0.265 | 529.0 |
| weighted avg | 0.464 | 0.423 | 0.437 | 529.0 |
