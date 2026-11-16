# svm 20261116T113637282Z

- recorded_at: 2026-11-16T11:36:37Z
- started_at: 2026-11-16T11:30:48Z
- elapsed_seconds: 349.1
- runtime: local
- data_root: C:\Users\Akiro\MarineSeeData\Seagrass
- split_seed: 42
- fit_seconds: 3.4
- best_params: {'kernel': 'rbf', 'C': 3.0, 'gamma': 0.003}
- best_val_macro_f1: 0.28738282044018654
- n_train: 3162
- n_val: 529
- n_test: 529
- train_accuracy: 0.7305502846299811
- val_accuracy: 0.4820415879017013
- test_accuracy: 0.45368620037807184
- v2_val_macro_f1: 0.22462136008862163
- v3_val_macro_f1: 0.2276664061162205
- feature_version: v3
- retake_threshold: 0.49
- val_accepted_accuracy: 0.6259259259259259
- val_accepted_coverage: 0.5103969754253308
- test_accepted_accuracy: 0.6333333333333333
- test_accepted_coverage: 0.45368620037807184
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

Curated retrain on leaf-visible frames. Habitat drops when the top of the frame is sky-like (sky fraction >= 0.5) and the green mask is under 0.02. Habitat waived for: none. Exact duplicate files dropped: 29. Train-only augment, at most 3 copies per photo. Feature v3. Validation macro F1 0.287 against locked v1 0.468. Held-out test accuracy 0.454 is on this selected set. The locked run on the unfiltered set was test accuracy 0.421. Held-out test accuracy is below the study line of 0.85.

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
| cymodocea_rotundata | 0.815 | 0.640 | 0.717 | 200.0 |
| cymodocea_serrulata | 0.834 | 0.805 | 0.819 | 200.0 |
| enhalus_acoroides | 0.695 | 0.684 | 0.690 | 453.0 |
| halodule_pinifolia | 0.878 | 0.935 | 0.906 | 200.0 |
| halodule_uninervis | 0.826 | 0.516 | 0.635 | 248.0 |
| halophila_minor | 0.984 | 0.969 | 0.976 | 64.0 |
| halophila_ovalis | 0.728 | 0.822 | 0.772 | 1062.0 |
| syringodium_isoetifolium | 0.844 | 0.675 | 0.750 | 200.0 |
| thalassia_hemprichii | 0.567 | 0.609 | 0.587 | 535.0 |
| macro avg | 0.797 | 0.740 | 0.761 | 3162.0 |
| weighted avg | 0.738 | 0.731 | 0.729 | 3162.0 |

## val

| slug | precision | recall | f1 | support |
|---|---:|---:|---:|---:|
| cymodocea_rotundata | 0.000 | 0.000 | 0.000 | 22.0 |
| cymodocea_serrulata | 0.250 | 0.167 | 0.200 | 12.0 |
| enhalus_acoroides | 0.538 | 0.544 | 0.541 | 90.0 |
| halodule_pinifolia | 0.400 | 0.545 | 0.462 | 11.0 |
| halodule_uninervis | 0.235 | 0.082 | 0.121 | 49.0 |
| halophila_minor | 0.000 | 0.000 | 0.000 | 3.0 |
| halophila_ovalis | 0.565 | 0.671 | 0.614 | 213.0 |
| syringodium_isoetifolium | 0.235 | 0.182 | 0.205 | 22.0 |
| thalassia_hemprichii | 0.448 | 0.439 | 0.443 | 107.0 |
| macro avg | 0.297 | 0.292 | 0.287 | 529.0 |
| weighted avg | 0.455 | 0.482 | 0.463 | 529.0 |

## test

| slug | precision | recall | f1 | support |
|---|---:|---:|---:|---:|
| cymodocea_rotundata | 0.067 | 0.048 | 0.056 | 21.0 |
| cymodocea_serrulata | 0.053 | 0.083 | 0.065 | 12.0 |
| enhalus_acoroides | 0.435 | 0.407 | 0.420 | 91.0 |
| halodule_pinifolia | 0.267 | 0.364 | 0.308 | 11.0 |
| halodule_uninervis | 0.444 | 0.160 | 0.235 | 50.0 |
| halophila_minor | 0.000 | 0.000 | 0.000 | 4.0 |
| halophila_ovalis | 0.572 | 0.637 | 0.603 | 212.0 |
| syringodium_isoetifolium | 0.273 | 0.136 | 0.182 | 22.0 |
| thalassia_hemprichii | 0.395 | 0.481 | 0.434 | 106.0 |
| macro avg | 0.278 | 0.257 | 0.256 | 529.0 |
| weighted avg | 0.446 | 0.454 | 0.441 | 529.0 |
