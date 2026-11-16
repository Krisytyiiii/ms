# svm 20261116T113045148Z

- recorded_at: 2026-11-16T11:30:45Z
- started_at: 2026-11-16T11:24:20Z
- elapsed_seconds: 384.4
- runtime: local
- data_root: C:\Users\Akiro\MarineSeeData\Seagrass
- split_seed: 42
- fit_seconds: 4.1
- best_params: {'kernel': 'rbf', 'C': 3.0, 'gamma': 0.003}
- best_val_macro_f1: 0.26841124323384935
- n_train: 3162
- n_val: 529
- n_test: 529
- train_accuracy: 0.6897533206831119
- val_accuracy: 0.4158790170132325
- test_accuracy: 0.3705103969754253
- v2_val_macro_f1: 0.22462136008862163
- v3_val_macro_f1: 0.2276664061162205
- feature_version: v3
- retake_threshold: 0.47
- val_accepted_accuracy: 0.587360594795539
- val_accepted_coverage: 0.5085066162570888
- test_accepted_accuracy: 0.6212765957446809
- test_accepted_coverage: 0.444234404536862
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

Curated retrain on leaf-visible frames. Habitat drops when the top of the frame is sky-like (sky fraction >= 0.5) and the green mask is under 0.02. Habitat waived for: none. Exact duplicate files dropped: 29. Train-only augment, at most 3 copies per photo. Feature v3. Validation macro F1 0.268 against locked v1 0.468. Held-out test accuracy 0.371 is on this selected set. The locked run on the unfiltered set was test accuracy 0.421. Held-out test accuracy is below the study line of 0.85.

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
| cymodocea_rotundata | 0.630 | 0.860 | 0.727 | 200.0 |
| cymodocea_serrulata | 0.456 | 0.990 | 0.625 | 200.0 |
| enhalus_acoroides | 0.675 | 0.702 | 0.688 | 453.0 |
| halodule_pinifolia | 0.775 | 1.000 | 0.873 | 200.0 |
| halodule_uninervis | 0.720 | 0.548 | 0.622 | 248.0 |
| halophila_minor | 0.889 | 1.000 | 0.941 | 64.0 |
| halophila_ovalis | 0.862 | 0.610 | 0.714 | 1062.0 |
| syringodium_isoetifolium | 0.709 | 0.875 | 0.783 | 200.0 |
| thalassia_hemprichii | 0.579 | 0.505 | 0.539 | 535.0 |
| macro avg | 0.699 | 0.788 | 0.724 | 3162.0 |
| weighted avg | 0.721 | 0.690 | 0.688 | 3162.0 |

## val

| slug | precision | recall | f1 | support |
|---|---:|---:|---:|---:|
| cymodocea_rotundata | 0.044 | 0.091 | 0.060 | 22.0 |
| cymodocea_serrulata | 0.125 | 0.417 | 0.192 | 12.0 |
| enhalus_acoroides | 0.527 | 0.533 | 0.530 | 90.0 |
| halodule_pinifolia | 0.222 | 0.545 | 0.316 | 11.0 |
| halodule_uninervis | 0.207 | 0.122 | 0.154 | 49.0 |
| halophila_minor | 0.000 | 0.000 | 0.000 | 3.0 |
| halophila_ovalis | 0.629 | 0.502 | 0.559 | 213.0 |
| syringodium_isoetifolium | 0.161 | 0.227 | 0.189 | 22.0 |
| thalassia_hemprichii | 0.456 | 0.383 | 0.416 | 107.0 |
| macro avg | 0.264 | 0.314 | 0.268 | 529.0 |
| weighted avg | 0.470 | 0.416 | 0.435 | 529.0 |

## test

| slug | precision | recall | f1 | support |
|---|---:|---:|---:|---:|
| cymodocea_rotundata | 0.054 | 0.095 | 0.069 | 21.0 |
| cymodocea_serrulata | 0.063 | 0.333 | 0.107 | 12.0 |
| enhalus_acoroides | 0.394 | 0.407 | 0.400 | 91.0 |
| halodule_pinifolia | 0.208 | 0.455 | 0.286 | 11.0 |
| halodule_uninervis | 0.289 | 0.260 | 0.274 | 50.0 |
| halophila_minor | 0.000 | 0.000 | 0.000 | 4.0 |
| halophila_ovalis | 0.672 | 0.415 | 0.513 | 212.0 |
| syringodium_isoetifolium | 0.179 | 0.227 | 0.200 | 22.0 |
| thalassia_hemprichii | 0.393 | 0.396 | 0.394 | 106.0 |
| macro avg | 0.250 | 0.288 | 0.249 | 529.0 |
| weighted avg | 0.458 | 0.371 | 0.399 | 529.0 |
