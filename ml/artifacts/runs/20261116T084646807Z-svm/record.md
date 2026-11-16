# svm 20261116T084646807Z

- recorded_at: 2026-11-16T08:46:46Z
- started_at: 2026-11-16T08:03:32Z
- elapsed_seconds: 2594.5
- runtime: local
- data_root: C:\Users\Akiro\MarineSeeData\Seagrass
- max_per_class: 400
- split_seed: 42
- fit_seconds: 3.0
- best_params: {'kernel': 'rbf', 'C': 10.0, 'gamma': 0.003}
- best_val_macro_f1: 0.4323226139263875
- n_train: 1683
- n_val: 233
- n_test: 233
- train_accuracy: 0.8936423054070113
- val_accuracy: 0.4678111587982833
- test_accuracy: 0.43776824034334766
- v2_val_macro_f1: 0.4204702868419683
- v3_val_macro_f1: 0.4323226139263875
- feature_version: v3
- retake_threshold: 0.46
- val_accepted_accuracy: 0.6141732283464567
- val_accepted_coverage: 0.5450643776824035
- test_accepted_accuracy: 0.55
- test_accepted_coverage: 0.5150214592274678
- study_line_met: False
- retake_study_line_met: False
- retake_rule: best accepted accuracy with coverage >= 0.50
- duplicates_dropped: 16
- habitat_waived: []
- listed: 3105
- kept: 2953
- skipped: 152

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

Curated retrain on leaf-visible frames. Habitat drops when the top of the frame is sky-like (sky fraction >= 0.5) and the green mask is under 0.02. Habitat waived for: none. Exact duplicate files dropped: 16. Train-only augment, at most 3 copies per photo. Feature v3. Validation macro F1 0.432 against locked v1 0.468. Held-out test accuracy 0.438 is on this selected set. The locked run on the unfiltered set was test accuracy 0.421. Held-out test accuracy is below the study line of 0.85.

## tuning (top 10 by validation macro F1)

| kernel | C | gamma | train macro F1 | val macro F1 | val acc | gap |
|---|---:|---:|---:|---:|---:|---:|
| rbf | 10.0 | 0.003 | 0.906 | 0.432 | 0.468 | 0.473 |
| rbf | 3.0 | scale | 0.921 | 0.428 | 0.476 | 0.493 |
| rbf | 10.0 | scale | 0.980 | 0.424 | 0.515 | 0.555 |
| rbf | 10.0 | 0.01 | 0.997 | 0.421 | 0.511 | 0.576 |
| rbf | 3.0 | 0.01 | 0.949 | 0.414 | 0.511 | 0.535 |
| rbf | 30.0 | scale | 0.998 | 0.413 | 0.506 | 0.585 |
| rbf | 100.0 | scale | 1.000 | 0.411 | 0.502 | 0.589 |
| rbf | 1.0 | 0.01 | 0.851 | 0.411 | 0.442 | 0.440 |
| rbf | 1.0 | scale | 0.788 | 0.406 | 0.446 | 0.382 |
| rbf | 30.0 | 0.01 | 1.000 | 0.399 | 0.502 | 0.601 |

## train

| slug | precision | recall | f1 | support |
|---|---:|---:|---:|---:|
| cymodocea_rotundata | 0.836 | 0.890 | 0.862 | 200.0 |
| cymodocea_serrulata | 0.882 | 0.970 | 0.924 | 200.0 |
| enhalus_acoroides | 0.849 | 0.829 | 0.839 | 286.0 |
| halodule_pinifolia | 0.942 | 0.980 | 0.961 | 200.0 |
| halodule_uninervis | 0.903 | 0.827 | 0.863 | 248.0 |
| halophila_minor | 0.985 | 1.000 | 0.992 | 64.0 |
| halophila_ovalis | 0.920 | 0.849 | 0.883 | 285.0 |
| syringodium_isoetifolium | 0.904 | 0.940 | 0.922 | 200.0 |
| macro avg | 0.903 | 0.911 | 0.906 | 1683.0 |
| weighted avg | 0.894 | 0.894 | 0.893 | 1683.0 |

## val

| slug | precision | recall | f1 | support |
|---|---:|---:|---:|---:|
| cymodocea_rotundata | 0.364 | 0.571 | 0.444 | 21.0 |
| cymodocea_serrulata | 0.357 | 0.417 | 0.385 | 12.0 |
| enhalus_acoroides | 0.529 | 0.474 | 0.500 | 57.0 |
| halodule_pinifolia | 0.538 | 0.636 | 0.583 | 11.0 |
| halodule_uninervis | 0.455 | 0.510 | 0.481 | 49.0 |
| halophila_minor | 0.333 | 0.250 | 0.286 | 4.0 |
| halophila_ovalis | 0.551 | 0.474 | 0.509 | 57.0 |
| syringodium_isoetifolium | 0.333 | 0.227 | 0.270 | 22.0 |
| macro avg | 0.433 | 0.445 | 0.432 | 233.0 |
| weighted avg | 0.474 | 0.468 | 0.466 | 233.0 |

## test

| slug | precision | recall | f1 | support |
|---|---:|---:|---:|---:|
| cymodocea_rotundata | 0.250 | 0.333 | 0.286 | 21.0 |
| cymodocea_serrulata | 0.333 | 0.500 | 0.400 | 12.0 |
| enhalus_acoroides | 0.567 | 0.596 | 0.581 | 57.0 |
| halodule_pinifolia | 0.364 | 0.400 | 0.381 | 10.0 |
| halodule_uninervis | 0.489 | 0.440 | 0.463 | 50.0 |
| halophila_minor | 0.333 | 0.333 | 0.333 | 3.0 |
| halophila_ovalis | 0.422 | 0.328 | 0.369 | 58.0 |
| syringodium_isoetifolium | 0.391 | 0.409 | 0.400 | 22.0 |
| macro avg | 0.394 | 0.417 | 0.402 | 233.0 |
| weighted avg | 0.445 | 0.438 | 0.438 | 233.0 |
