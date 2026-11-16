# svm 20261116T105309274Z

- recorded_at: 2026-11-16T10:53:09Z
- started_at: 2026-11-16T10:44:16Z
- elapsed_seconds: 532.5
- runtime: local
- data_root: C:\Users\Akiro\MarineSeeData\Seagrass
- split_seed: 42
- fit_seconds: 5.3
- best_params: {'kernel': 'rbf', 'C': 3.0, 'gamma': 0.003}
- best_val_macro_f1: 0.25657263476143605
- n_train: 3162
- n_val: 529
- n_test: 529
- train_accuracy: 0.6394686907020873
- val_accuracy: 0.3705103969754253
- test_accuracy: 0.3270321361058601
- v2_val_macro_f1: 0.22462136008862163
- v3_val_macro_f1: 0.2276664061162205
- feature_version: v3
- retake_threshold: 0.49
- val_accepted_accuracy: 0.569811320754717
- val_accepted_coverage: 0.500945179584121
- test_accepted_accuracy: 0.630901287553648
- test_accepted_coverage: 0.44045368620037806
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

Curated retrain on leaf-visible frames. Habitat drops when the top of the frame is sky-like (sky fraction >= 0.5) and the green mask is under 0.02. Habitat waived for: none. Exact duplicate files dropped: 29. Train-only augment, at most 3 copies per photo. Feature v3. Validation macro F1 0.257 against locked v1 0.468. Held-out test accuracy 0.327 is on this selected set. The locked run on the unfiltered set was test accuracy 0.421. Held-out test accuracy is below the study line of 0.85.

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
| cymodocea_rotundata | 0.499 | 0.950 | 0.654 | 200.0 |
| cymodocea_serrulata | 0.403 | 1.000 | 0.575 | 200.0 |
| enhalus_acoroides | 0.635 | 0.673 | 0.654 | 453.0 |
| halodule_pinifolia | 0.755 | 1.000 | 0.860 | 200.0 |
| halodule_uninervis | 0.637 | 0.601 | 0.618 | 248.0 |
| halophila_minor | 0.877 | 1.000 | 0.934 | 64.0 |
| halophila_ovalis | 0.900 | 0.481 | 0.627 | 1062.0 |
| syringodium_isoetifolium | 0.613 | 0.925 | 0.737 | 200.0 |
| thalassia_hemprichii | 0.601 | 0.407 | 0.486 | 535.0 |
| macro avg | 0.658 | 0.782 | 0.683 | 3162.0 |
| weighted avg | 0.706 | 0.639 | 0.633 | 3162.0 |

## val

| slug | precision | recall | f1 | support |
|---|---:|---:|---:|---:|
| cymodocea_rotundata | 0.061 | 0.182 | 0.091 | 22.0 |
| cymodocea_serrulata | 0.104 | 0.417 | 0.167 | 12.0 |
| enhalus_acoroides | 0.500 | 0.522 | 0.511 | 90.0 |
| halodule_pinifolia | 0.188 | 0.545 | 0.279 | 11.0 |
| halodule_uninervis | 0.238 | 0.204 | 0.220 | 49.0 |
| halophila_minor | 0.000 | 0.000 | 0.000 | 3.0 |
| halophila_ovalis | 0.667 | 0.404 | 0.503 | 213.0 |
| syringodium_isoetifolium | 0.128 | 0.227 | 0.164 | 22.0 |
| thalassia_hemprichii | 0.478 | 0.308 | 0.375 | 107.0 |
| macro avg | 0.263 | 0.312 | 0.257 | 529.0 |
| weighted avg | 0.486 | 0.371 | 0.406 | 529.0 |

## test

| slug | precision | recall | f1 | support |
|---|---:|---:|---:|---:|
| cymodocea_rotundata | 0.052 | 0.143 | 0.076 | 21.0 |
| cymodocea_serrulata | 0.043 | 0.250 | 0.073 | 12.0 |
| enhalus_acoroides | 0.396 | 0.440 | 0.417 | 91.0 |
| halodule_pinifolia | 0.200 | 0.455 | 0.278 | 11.0 |
| halodule_uninervis | 0.263 | 0.300 | 0.280 | 50.0 |
| halophila_minor | 0.000 | 0.000 | 0.000 | 4.0 |
| halophila_ovalis | 0.683 | 0.325 | 0.441 | 212.0 |
| syringodium_isoetifolium | 0.103 | 0.182 | 0.131 | 22.0 |
| thalassia_hemprichii | 0.436 | 0.321 | 0.370 | 106.0 |
| macro avg | 0.242 | 0.268 | 0.230 | 529.0 |
| weighted avg | 0.466 | 0.327 | 0.365 | 529.0 |
