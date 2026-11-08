# svm 20261106T172238348Z

- recorded_at: 2026-11-06T17:22:38Z
- started_at: 2026-11-06T17:03:00Z
- elapsed_seconds: 1178.2
- runtime: local
- data_root: D:\pepot\marinesee\assets\species\Seagrass
- max_per_class: 400
- split_seed: 42
- fit_seconds: 1.5
- best_params: {'kernel': 'rbf', 'C': 100.0, 'gamma': 0.01}
- best_val_macro_f1: 0.47443749645258915
- n_train: 1667
- n_val: 245
- n_test: 245
- train_accuracy: 1.0
- val_accuracy: 0.5387755102040817
- test_accuracy: 0.49387755102040815
- v2_val_macro_f1: 0.44821870335225666
- v3_val_macro_f1: 0.47443749645258915
- feature_version: v3
- retake_threshold: 0.44
- val_accepted_accuracy: 0.6549295774647887
- val_accepted_coverage: 0.5795918367346938
- test_accepted_accuracy: 0.6
- test_accepted_coverage: 0.5918367346938775
- study_line_met: False
- retake_study_line_met: False
- retake_rule: best accepted accuracy with coverage >= 0.50
- duplicates_dropped: 11
- habitat_waived: []
- listed: 2175
- kept: 2058
- skipped: 117

## selection

| slug | kept | dropped |
|---|---:|---:|
| cymodocea_rotundata | 149 | 9 |
| cymodocea_serrulata | 84 | 3 |
| enhalus_acoroides | 634 | 32 |
| halodule_pinifolia | 75 | 10 |
| halodule_uninervis | 347 | 28 |
| halophila_minor | 23 | 1 |
| halophila_ovalis | 592 | 27 |
| syringodium_isoetifolium | 154 | 7 |

Curated retrain on leaf-visible frames. Habitat drops when the top of the frame is sky-like (sky fraction >= 0.5) and the green mask is under 0.02. Habitat waived for: none. Exact duplicate files dropped: 11. Train-only augment, at most 3 copies per photo. Feature v3. Validation macro F1 0.474 against locked v1 0.468. Held-out test accuracy 0.494 is on this selected set. The locked run on the unfiltered set was test accuracy 0.421. Held-out test accuracy is below the study line of 0.85.

## tuning (top 10 by validation macro F1)

| kernel | C | gamma | train macro F1 | val macro F1 | val acc | gap |
|---|---:|---:|---:|---:|---:|---:|
| rbf | 100.0 | 0.01 | 1.000 | 0.474 | 0.539 | 0.526 |
| rbf | 10.0 | 0.01 | 0.995 | 0.473 | 0.522 | 0.522 |
| rbf | 30.0 | 0.01 | 1.000 | 0.472 | 0.535 | 0.528 |
| rbf | 3.0 | 0.01 | 0.961 | 0.449 | 0.502 | 0.513 |
| rbf | 100.0 | 0.003 | 0.997 | 0.436 | 0.486 | 0.561 |
| rbf | 100.0 | scale | 1.000 | 0.432 | 0.506 | 0.568 |
| rbf | 30.0 | 0.003 | 0.972 | 0.430 | 0.494 | 0.542 |
| rbf | 30.0 | scale | 0.998 | 0.429 | 0.498 | 0.569 |
| rbf | 3.0 | scale | 0.922 | 0.427 | 0.494 | 0.495 |
| rbf | 10.0 | scale | 0.986 | 0.422 | 0.490 | 0.563 |

## train

| slug | precision | recall | f1 | support |
|---|---:|---:|---:|---:|
| cymodocea_rotundata | 1.000 | 1.000 | 1.000 | 200.0 |
| cymodocea_serrulata | 1.000 | 1.000 | 1.000 | 200.0 |
| enhalus_acoroides | 1.000 | 1.000 | 1.000 | 280.0 |
| halodule_pinifolia | 1.000 | 1.000 | 1.000 | 200.0 |
| halodule_uninervis | 1.000 | 1.000 | 1.000 | 243.0 |
| halophila_minor | 1.000 | 1.000 | 1.000 | 64.0 |
| halophila_ovalis | 1.000 | 1.000 | 1.000 | 280.0 |
| syringodium_isoetifolium | 1.000 | 1.000 | 1.000 | 200.0 |
| macro avg | 1.000 | 1.000 | 1.000 | 1667.0 |
| weighted avg | 1.000 | 1.000 | 1.000 | 1667.0 |

## val

| slug | precision | recall | f1 | support |
|---|---:|---:|---:|---:|
| cymodocea_rotundata | 0.417 | 0.217 | 0.286 | 23.0 |
| cymodocea_serrulata | 0.462 | 0.462 | 0.462 | 13.0 |
| enhalus_acoroides | 0.672 | 0.750 | 0.709 | 60.0 |
| halodule_pinifolia | 0.333 | 0.182 | 0.235 | 11.0 |
| halodule_uninervis | 0.400 | 0.500 | 0.444 | 52.0 |
| halophila_minor | 1.000 | 0.333 | 0.500 | 3.0 |
| halophila_ovalis | 0.579 | 0.550 | 0.564 | 60.0 |
| syringodium_isoetifolium | 0.583 | 0.609 | 0.596 | 23.0 |
| macro avg | 0.556 | 0.450 | 0.474 | 245.0 |
| weighted avg | 0.537 | 0.539 | 0.530 | 245.0 |

## test

| slug | precision | recall | f1 | support |
|---|---:|---:|---:|---:|
| cymodocea_rotundata | 0.364 | 0.364 | 0.364 | 22.0 |
| cymodocea_serrulata | 0.545 | 0.462 | 0.500 | 13.0 |
| enhalus_acoroides | 0.636 | 0.583 | 0.609 | 60.0 |
| halodule_pinifolia | 0.417 | 0.455 | 0.435 | 11.0 |
| halodule_uninervis | 0.441 | 0.577 | 0.500 | 52.0 |
| halophila_minor | 0.000 | 0.000 | 0.000 | 4.0 |
| halophila_ovalis | 0.526 | 0.500 | 0.513 | 60.0 |
| syringodium_isoetifolium | 0.350 | 0.304 | 0.326 | 23.0 |
| macro avg | 0.410 | 0.406 | 0.406 | 245.0 |
| weighted avg | 0.492 | 0.494 | 0.490 | 245.0 |
