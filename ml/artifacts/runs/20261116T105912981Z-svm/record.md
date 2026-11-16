# svm 20261116T105912981Z

- recorded_at: 2026-11-16T10:59:12Z
- started_at: 2026-11-16T10:56:35Z
- elapsed_seconds: 157.4
- runtime: local
- data_root: C:\Users\Akiro\MarineSeeData\Seagrass
- max_per_class: 400
- split_seed: 42
- fit_seconds: 1.8
- best_params: {'kernel': 'rbf', 'C': 3.0, 'gamma': 0.003}
- best_val_macro_f1: 0.19903821551991022
- n_train: 1974
- n_val: 290
- n_test: 290
- train_accuracy: 0.6702127659574468
- val_accuracy: 0.24482758620689654
- test_accuracy: 0.2689655172413793
- v2_val_macro_f1: 0.23394128863595806
- v3_val_macro_f1: 0.23127953067494894
- feature_version: v2
- retake_threshold: 0.38
- val_accepted_accuracy: 0.3064516129032258
- val_accepted_coverage: 0.6413793103448275
- test_accepted_accuracy: 0.37777777777777777
- test_accepted_coverage: 0.6206896551724138
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

Curated retrain on leaf-visible frames. Habitat drops when the top of the frame is sky-like (sky fraction >= 0.5) and the green mask is under 0.02. Habitat waived for: none. Exact duplicate files dropped: 29. Train-only augment, at most 3 copies per photo. Feature v2. Validation macro F1 0.199 against locked v1 0.468. Held-out test accuracy 0.269 is on this selected set. The locked run on the unfiltered set was test accuracy 0.421. Held-out test accuracy is below the study line of 0.85.

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
| cymodocea_rotundata | 0.607 | 0.825 | 0.699 | 200.0 |
| cymodocea_serrulata | 0.517 | 1.000 | 0.681 | 200.0 |
| enhalus_acoroides | 0.722 | 0.563 | 0.633 | 286.0 |
| halodule_pinifolia | 0.689 | 0.985 | 0.811 | 200.0 |
| halodule_uninervis | 0.859 | 0.444 | 0.585 | 248.0 |
| halophila_minor | 0.872 | 1.000 | 0.932 | 68.0 |
| halophila_ovalis | 0.774 | 0.514 | 0.618 | 286.0 |
| syringodium_isoetifolium | 0.680 | 0.850 | 0.756 | 200.0 |
| thalassia_hemprichii | 0.656 | 0.367 | 0.471 | 286.0 |
| macro avg | 0.708 | 0.728 | 0.687 | 1974.0 |
| weighted avg | 0.702 | 0.670 | 0.654 | 1974.0 |

## val

| slug | precision | recall | f1 | support |
|---|---:|---:|---:|---:|
| cymodocea_rotundata | 0.088 | 0.136 | 0.107 | 22.0 |
| cymodocea_serrulata | 0.050 | 0.167 | 0.077 | 12.0 |
| enhalus_acoroides | 0.370 | 0.351 | 0.360 | 57.0 |
| halodule_pinifolia | 0.216 | 0.727 | 0.333 | 11.0 |
| halodule_uninervis | 0.423 | 0.224 | 0.293 | 49.0 |
| halophila_minor | 0.000 | 0.000 | 0.000 | 3.0 |
| halophila_ovalis | 0.318 | 0.246 | 0.277 | 57.0 |
| syringodium_isoetifolium | 0.095 | 0.091 | 0.093 | 22.0 |
| thalassia_hemprichii | 0.355 | 0.193 | 0.250 | 57.0 |
| macro avg | 0.213 | 0.237 | 0.199 | 290.0 |
| weighted avg | 0.301 | 0.245 | 0.255 | 290.0 |

## test

| slug | precision | recall | f1 | support |
|---|---:|---:|---:|---:|
| cymodocea_rotundata | 0.159 | 0.333 | 0.215 | 21.0 |
| cymodocea_serrulata | 0.119 | 0.417 | 0.185 | 12.0 |
| enhalus_acoroides | 0.442 | 0.333 | 0.380 | 57.0 |
| halodule_pinifolia | 0.176 | 0.545 | 0.267 | 11.0 |
| halodule_uninervis | 0.259 | 0.140 | 0.182 | 50.0 |
| halophila_minor | 0.000 | 0.000 | 0.000 | 3.0 |
| halophila_ovalis | 0.395 | 0.263 | 0.316 | 57.0 |
| syringodium_isoetifolium | 0.105 | 0.091 | 0.098 | 22.0 |
| thalassia_hemprichii | 0.405 | 0.298 | 0.343 | 57.0 |
| macro avg | 0.229 | 0.269 | 0.221 | 290.0 |
| weighted avg | 0.320 | 0.269 | 0.276 | 290.0 |
