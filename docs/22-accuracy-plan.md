# Accuracy plan: imbalance, multiclass, and the 85% line

**IMPLEMENTATION.** This file turns the measured v2 result into a work plan. It is a diagnosis and a proposal, not a promise. Every number here is copied from a recorded artifact, and the file that holds it is named so a reader can check.

Sources: `ml/artifacts/v2/metrics.json` (curated run, `feature_version` v3), `ml/artifacts/inventory.json` (Drive inventory), `docs/09-ml-pipeline.md` (pipeline contract), `docs/11-species.md` (nine species, Thalassia held out), `docs/14-open-questions.md` items 3 and 14.

The question this file answers: *how do we raise the evaluation number while the model still learns honestly, given an imbalanced dataset and a multiclass problem?*

Short answer: the imbalance is mostly handled and is **not** the bottleneck. The bottlenecks are three concrete, measurable defects — an unused ninth class, a scarcity floor on four classes, and a validation protocol too weak to justify the chosen hyperparameters. Fixing those is worth far more than any new feature.

### Implementation status (16 Nov 2026)

| Item | Code | Status |
|---|---|---|
| 1.1 Thalassia audit | `ml/src/audit_thalassia.py` | **Ran on the real copy, verdict `clean`** (16 Nov 2026, local mirror of the 16 Nov Drive listing). 1,037 candidate images in the two nested variants (`all` 791, `research-grade` 246); 996 pass QC; 749 distinct plants; 12 frames (1.2%) near-duplicate a frame in `ovalis` / `uninervis` / `enhalus` / `syringodium`; 258 duplicate pairs inside the class. Written to `ml/artifacts/thalassia_audit.json` + `thalassia_review.csv`. The tool now finds the class where it actually lives (nested inside the trainable folders, three identical `all` mirrors collapsed) — a top-level walk found nothing |
| 1.3 Dedupe + observation grouping | `ml/src/phash.py` | **Done, tested.** iNaturalist observation ids are the primary key (`{observation_id}_{photo_index}_inat`): 3,896 training images carry one, 2,329 distinct observations, so a photoshoot cannot straddle a split. Fallback is capture-time clustering, then `per-file`, and the mode is recorded. 64-bit difference hash (Hamming ≤ 6), union-find merge. Near-duplicate merging is restricted to one class; a cross-class duplicate or a shared observation id is counted (`cross_class_near_duplicates`, `cross_class_observations`) and not merged |
| 2.1 Grouped split | `ml/src/split.py::split_labels_grouped` | **Done, tested.** `StratifiedGroupKFold`, 7 folds → 1 test / 1 val / 5 train, test/val chosen as the fold pair that covers the most classes; refuses to run if a group spans two splits. `split_report.degraded` + `classes_missing_from_val` / `classes_missing_from_test` flag a split that cannot hold out every class, and `train_curated.py` prints the warning instead of quoting a clean macro F1 |
| 2.2 Tune on real rows | `ml/src/train_curated.py` | **Done.** Selection runs on real training frames; augmentation happens only for the final fit, so a copy-heavy candidate cannot win the search |
| 2.3 Grouped CV + 1-SE | `ml/src/tune_svm.py` | **Done, tested.** `search_grouped_cv` reports mean ± SE of macro F1 over `StratifiedGroupKFold`; `best_1se` picks the least flexible candidate within one SE. `--cv-folds 1` keeps the single-split search |
| 2.5 Imbalance knob | `--max-per-class`, `--alpha` | **Done, measured.** Cap and class weights are separate flags so the stack can be ablated instead of assumed. The 2×2 is measured below: no single cell wins on accuracy, baseline lift and top-3 at once. The α sweep adds the finishing result: accuracy falls and balance rises as weighting increases, so **α=1 is the worst default** and α=0.25 / 0.75 are the two defensible operating choices |
| 2.6 Per-class thresholds | `ml/src/thresholds.py` | **Done, tested, measured negative.** One acceptance threshold per *predicted* class, fitted on validation (≥5 photos and above chance, else abstain = "retake"), recorded in `record.json` as `class_thresholds`. It does not beat the global gate at matched coverage — see the measured table below. Keep the code as a recorded diagnostic, not as a shipped rule |
| Confusion audit | `ml/src/audit_confusion.py` | **Done, tested.** Reads a record's `confusion_matrix_test` and prints the largest true → predicted cells plus which classes absorb the wrong photos. No retrain needed |
| Out-of-set audit | `ml/src/audit_negative.py` | **Tool done, tested; no real negatives yet.** Given a folder of non-target photos it reports false-accept rate, confidence distribution, how many a green-mask pre-check catches, **and what that cut costs on real seagrass**. Synthetic dry run: 8/8 named a species, 8/8 cleared the gate, pre-check caught 6/8 (the two green frames survived). The pre-check's cost is now measured on 504 real photos: a 0.05 cut refuses **34%** of genuine seagrass, so the gate is not shippable and the honest answer is a **"none of these" control in the app** plus 100-200 real negatives before any claim |
| Caching | `ml/src/cache.py` | **Done, tested.** QC, dHash, prepared frames, and feature vectors cached by file fingerprint + parameters, outside the repo |
| 2.7 Multiclass metrics | `ml/src/metrics_extra.py` | **Done, tested.** Balanced accuracy, macro recall, top-2/3, per-class table with support gate, coverage/accuracy table, grouped bootstrap CI |
| Wiring | `ml/src/train_curated.py --split grouped --dest-version v3` | **Done.** Default stays image-level so the shipped v2 artifact is untouched; a grouped run must name a new version or it refuses |
| Measured grouped run (9 classes, observations) | `ml/artifacts/runs/20261116T094521023Z-svm/record.md` | **Ran 16 Nov 2026 on the full Drive mirror.** 3,896 `all` images → 3,701 kept → 2,032 capped → 1,452 / 290 / 290. Grouping is `inaturalist` (1,395 observations, 1,050 singletons, 0 group leaks), so **this is the first observation-honest number**. Test acc **0.269**, macro F1 **0.221**, balanced acc **0.269**, top-2 0.555, top-3 0.669, CI **0.213–0.324** (one-vs-one vote, the shipped rule), accepted **0.355 at 53% coverage**, and **nothing exported** (validation macro F1 0.199 < 0.468). CV plateau 0.232–0.241 across all 47 candidates (linear 0.237 inside 1 SE), so tuning does not move it | `ml/artifacts/runs/20261116T094521023Z-svm/record.md` |
| Measured grouped run (8 classes, per-file) | `ml/artifacts/runs/20261116T084646807Z-svm/record.md` | **Ran 16 Nov 2026 on the full Drive mirror** (3,105 `all` images → 2,953 after QC → 1,632 capped → 1,166 / 233 / 233). Test acc **0.438**, macro F1 **0.402**, balanced acc **0.353**, top-2 0.640, top-3 0.790, accuracy CI 0.390-0.515. Validation macro F1 0.432 did not beat the locked 0.468, so **nothing was exported**. Grouping fell back to `per-file` because that run predates the iNaturalist id key, so its scores are optimistic against the nine-class row above |
| 1.2 / 2.8 / 3.x | — | **Not started.** Data collection, paired bootstrap tests, and feature work need the dataset or a decision first. 2.6 is done and moved into row 2.6 above |

Nothing above changed the feature vector, so the on-device contract in `09-ml-pipeline.md` is unaffected and the app is untouched.

---

## 1. What the model does today

| Measure | Value |
|---|---|
| Classes trained | 8 (Thalassia held out) |
| Feature vector | 148 dims, v3 (color 0–101, GLCM 102–137, shape 138–147) |
| Kernel / params | RBF, `C=100`, `gamma=0.01`, `class_weight="balanced"` |
| Rows | train 1667 (1,142 real + 525 augmented copies), val 245 (real), test 245 (real). Accounting in §6 |
| **train accuracy** | **1.000** |
| val accuracy / macro F1 | 0.539 / 0.474 |
| **test accuracy** | **0.494** |
| **test macro F1 / macro recall** | **0.406 / 0.406** |
| Accepted (conf ≥ 0.44) | test 60% accuracy at 59% coverage; val 65.5% at 58% |
| Study target | ≥ 85% test accuracy |

Chance for eight classes is 0.125, so the model is learning — 0.49 is roughly four times chance. The problem is that 0.49 and 0.85 are not the same conversation.

### Why 0.494 is the wrong headline number

The test set is not balanced. Two classes are ~half of it:

| class | test n | recall |
|---|---|---|
| enhalus_acoroides | 60 | 0.58 |
| halophila_ovalis | 60 | 0.50 |
| halodule_uninervis | 52 | 0.58 |
| syringodium_isoetifolium | 23 | 0.30 |
| cymodocea_rotundata | 22 | 0.36 |
| cymodocea_serrulata | 13 | 0.46 |
| halodule_pinifolia | 11 | 0.45 |
| halophila_minor | 4 | **0.00** |

A model that only ever answered "enhalus" would already score about 0.245 on this test set. Accuracy rewards that. Macro F1 (0.406) treats every species equally, which is what a nine-species identification tool actually promises the user. **Report macro F1 first, accuracy second.** Both are already in `metrics.json`; only the ordering of the claim needs to change.

### Where the errors are

Confusion matrix, rows true / columns predicted, 245 photos:

```text
                    rotu serr enha pini univ mino oval syri
cymodocea_rotundata    8    0    0    0    6    0    5    3
cymodocea_serrulata    2    6    1    0    0    0    3    1
enhalus_acoroides      3    0   35    1    9    0   10    2
halodule_pinifolia     0    0    2    5    3    0    1    0
halodule_uninervis     3    1    5    2   30    0    6    5
halophila_minor        1    0    1    0    1    0    1    0
halophila_ovalis       2    1    8    3   14    0   30    2
syringodium_isoeti     3    3    3    1    5    0    1    7
```

Three structures, not one:

1. **The two *Halophila*/*Halodule* grass-like pairings.** `ovalis → uninervis` (14) is the single largest error cell in the matrix, and `uninervis → ovalis` (6) is the mirror. These two share a leaf shape: oval blades versus narrow blades is a *shape* distinction the current 10 shape features resolve poorly.
2. **`enhalus` absorbing everything.** `enhalus` is the predicted class for 8 of `ovalis`, 9 of `uninervis`, 3 of `rotundata`. `enhalus` is also the largest class (634 real images), so both weight and prior point at it.
3. **`rotundata` has no home.** Its 22 test photos scatter across four classes with a maximum of 8. A class whose recall is 0.36 and whose errors are spread evenly is a class the features do not describe, not a class with a rival.

`halophila_minor` at 0.00 recall is a sample-size artifact on top of a scarcity problem: 4 test images, 23 real images total. Nothing about that row can be read as a modelling result.

---

## 2. Diagnosis

Findings are ordered by how much accuracy they cost.

### 2.1 The ninth class is missing, and it is a guaranteed error

`TRAINABLE_SPECIES` in `ml/src/dataset_contract.py` lists eight slugs. The inventory shows **743 Thalassia hemprichii images** sitting in `Thalassia hemprichii dataset (all)` (and its research-grade subset) that no model has ever seen. They are held out because a 19 Sep 2026 local dump had Thalassia photos nested inside Enhalus and Halodule folders, so the folder needs an audit for mixed-in frames before it can be trusted — `docs/11-species.md` and `docs/14-open-questions.md` item 3 both say so.

The cost is visible and not subtle. A real Thalassia photo goes through the app as:

```text
thalassia_hemprichii.jpg -> enhalus_acoroides 59.9%
```

Every Thalassia photo is a guaranteed wrong answer, and it is wrong *toward* `enhalus`, the class that already absorbs the most errors. On an evaluation that includes Thalassia quadrats this is a hard ceiling no tuning touches. This is the largest single term in the gap.

### 2.2 Four classes have a scarcity floor, not a modelling problem

Real kept images per class, before the 400-per-class cap and before augmentation:

```text
enhalus 634 | ovalis 592 | uninervis 347 | syringodium 154
rotundata 149 | serrulata 84 | pinifolia 75 | halophila_minor 23
```

The 400 cap, the balanced weights and the augmentation-to-200 target already equalise *influence*. What none of them can equalise is *variety*. 23 real minor photos, augmented three ways, are still 23 scenes. A model can memorise 23 scenes perfectly and has learned nothing about the species. That is why `halophila_minor` recall is 0.00 and why `syringodium` (154 real, recall 0.30) and `rotundata` (149, recall 0.36) sit near the floor too.

So the honest statement is: **imbalance is handled; scarcity is not.** Weighting cannot manufacture variety, and augmentation cannot either — it is a geometric re-rendering of the same scene.

One caveat on the word "handled": three corrections (cap, weights, augmentation) are stacked on the same problem and have never been ablated. One of them may be double-counting. See action 2.5.

### 2.3 The model memorises, and the selected hyperparameters may be noise

`train accuracy 1.000` against `test accuracy 0.494` is memorisation, not a smooth fit. `C=100` on 148 attributes is a very high penalty allowance for an RBF kernel; the model is permitted to draw tiny closed regions around individual training points.

That choice was made by `ml/src/tune_svm.py` scoring one 245-row validation split and taking the highest `val_macro_f1`. With 245 rows spread over 8 classes, some classes have 4–13 validation photos. The standard error on a macro F1 computed from ~4 samples in a class is large enough that the gap between `C=10` and `C=100` is plausibly inside the noise. **The selection procedure cannot currently distinguish a real improvement from a lucky split.**

This is the cheapest fixable defect in the list, and it does not require new data.

### 2.4 The split is by image, not by observation

`ml/src/split.py` uses stratified `train_test_split` over images. The dataset came from field photoshoots and iNaturalist: one observation often yields several near-duplicate frames of the same blade. If two frames of the same plant land on opposite sides of the split, the test set contains a photo the model has effectively already seen.

Direction of the bias: **the reported 0.494 is likely optimistic, not pessimistic.** Fixing this correctly will probably make the number go *down*. That is the point — a number you can defend is worth more than a number that is high.

### 2.5 The features are doing a hard job with blunt tools

148 hand-crafted dimensions for eight fine-grained seagrass species, where the discriminating traits are blade width (millimetres), vein count, leaf-tip shape, and rhizome/root structure. Current composition: 102 color-histogram values, 36 GLCM texture values, 10 shape values.

Two structural weaknesses fall out of the confusion matrix:

- **Color is over-represented (69% of the vector).** Color is exactly the axis that moves with depth, sun angle, turbidity, epiphyte load and white balance. Two of the three big confusion pairs are species that differ mainly in *shape*, so the vector is mostly measuring the axis that cannot separate them.
- **Shape is under-represented (7%) and the model is likely reading substrate.** Every photo contains sand. A sand background has a characteristic brightness and texture, and a color/texture-heavy vector will happily learn "sand tone" as a class cue. `ovalis → uninervis` at 14 confusions is consistent with both species sitting on the same substrate.

---

## 3. Plan

Ordered by expected effect per unit of effort. Effect sizes are estimates, marked as such, not measurements.

### Tier 1 — data (the only tier that can move the number by more than a few points)

| # | Action | Why it dominates | Est. |
|---|---|---|---|
| 1.1 | **Audit the two Thalassia folders and add class 9.** Read-only scan for other taxa, habitat-only shots, duplicates, and the mix-in history. Then retrain with nine classes. | Removes a guaranteed 0% class that currently also pollutes `enhalus`. On any evaluation that includes Thalassia this is the largest single gain available | Largest available; on a Thalassia-inclusive eval, potentially +0.10–0.20 macro F1 |
| 1.2 | **Collect more real photos of minor / pinifolia / serrulata / rotundata.** | Recall is set by scene variety, not by weight. 23 → 100 real minor photos is a different problem from 23 | +0.05–0.15 macro F1, the only route to a real floor |
| 1.3 | **Perceptual-hash dedupe across the whole pool, then group the split by source observation** (photoset / iNaturalist observation ID / EXIF capture-time cluster), not by image. | Removes near-duplicate leakage; makes the reported number defensible to a panel | Honesty, not points — expect the number to *drop*, possibly by 5–15 points |

The order matters: **audit before retuning.** Retuning on eight classes and then adding a ninth invalidates the tuning, because class weights, the confusion structure, and the optimal `C`/`gamma` all move. The audit is read-only and independent of the split work, so those two can run in parallel.

If the audit cannot finish in the time available, there is a cheaper fallback that is still defensible: ship an explicit **out-of-set abstention** so a Thalassia photo returns "not one of the nine species", not `enhalus_acoroides` at 60%. An abstention is honest; a confident wrong answer to a panel member holding a Thalassia photo is not. Doing both is better.

### Tier 2 — protocol (cheap, immediate, and it protects the claim)

| # | Action | Why |
|---|---|---|
| 2.1 | **Repeated grouped stratified k-fold CV on the real training data** instead of one 245-row validation split. Report mean ± SD of macro F1 and macro recall per candidate. | Makes `C=100` either defensible or visibly overfit. 5×5 folds is cheap on ~1,100 rows. `StratifiedGroupKFold` keeps a photoshoot inside one fold |
| 2.2 | **Tune on real-only rows, then augment for the final fit.** | Augmented copies in the tuning split inflate the apparent gain of high `C`, because the copies are near-duplicates of the training scenes |
| 2.3 | **Sweep `C` downward, and use the one-standard-error rule.** The current grid's chosen point is at the top of the range with train accuracy 1.000. Note `gamma='scale'` here is `1/(148·1) ≈ 0.0068`, so the selected `0.01` sits on the *more local* side of the default. | Directly addresses the memorisation in 2.3. Pick the least flexible setting within 1 SE of the best CV score |
| 2.4 | **Run a linear-kernel SVM as the reference point, and report pairwise (two-class) accuracy for the confusable pairs** (`ovalis` vs `uninervis`, `enhalus` vs `ovalis`). | `SVC` is one-vs-one internally: 28 binary models for 8 classes. If the `ovalis`/`uninervis` specialist scores ~0.70 while the multiclass decision scores ~0.50, the loss is in the aggregation and calibration, not the features — and per-class thresholds or `decision_function_shape='ovr'` may claw back points for almost no work. **Do this before any feature work** |
| 2.5 | **Ablate the imbalance stack instead of running all three.** Table over {none, `class_weight`, 400 cap, cap + weights, aug ×1, aug ×3} and pick on grouped CV. Also try `class_weight` as `balanced` raised to α ∈ {0.5, 0.75, 1.0}. | The current run caps at 400 *and* weights balanced *and* augments. These are three corrections to the same problem and they may be double-counting. α is the knob that trades macro recall against plain accuracy |
| 2.6 | **Per-class decision thresholds / bias offsets** tuned on CV to equalise per-class recall. | Multiclass one-vs-one still biases toward dense classes after weighting. Targets macro recall directly rather than proxying through weights |
| 2.7 | **Report the multiclass set properly:** macro F1, macro recall, balanced accuracy, per-class recall **with n per class**, top-2 / top-3 accuracy, and a coverage–accuracy *table* (not one point) at thresholds 0.40 / 0.50 / 0.60 / 0.70. Put macro F1 first. | Matches what a nine-species tool promises. Top-2 is meaningful here because the top confusions are two-species pairs. A single (accuracy, coverage) point hides that the rejector is weak |
| 2.8 | **Grouped bootstrap confidence intervals** (resample groups, not images), and paired bootstrap or McNemar when comparing two models. | At n = 245 the 95% CI on accuracy is roughly ±6 points. **The val 65.5% vs test 60% gap is inside that interval — it is not a finding.** Do not claim a model win from a validation-only difference |
| 2.9 | **Score test exactly once**, after the protocol is frozen, and record the split file hash with the metrics | The panel will ask how many times test was read |
| 2.10 | **Measure calibration** (reliability diagram, ECE, Brier) and consider a margin-based rejector (`decision_function` gap) instead of the probability threshold. | With 4–23 photos in the tail classes, the Platt-scaled one-vs-one probabilities are compressed and poorly calibrated — which is exactly why the threshold landed on an odd 0.44. A margin gap may separate "confident" from "guessing" better |
| 2.11 | **Set `random_state` everywhere and log it.** Note that `SVC(probability=True)` refits with an internal 5-fold CV that **ignores group keys** — a second, quieter leak that also makes results seed-dependent. | For evaluation, use margins. Keep probabilities only for the UI |


### Tier 3 — features (real but bounded; `ml/src` changes first, then the app)

Feature v3 already bought +0.026 validation macro F1 over v2, so this axis is not dead — it is just no longer the big lever. Ranked by remaining signal: **shape has the most, texture is contaminated, color has the least.**

| # | Action | Rationale |
|---|---|---|
| 3.1 | **Replace the single global skeleton with a skeleton *graph*.** Nodes = branch points; edges = blade segments carrying length, mean and max width, width:length ratio, orientation, tip angle, and per-shoot blade count. | This is where a taxonomist's discrimination actually lives, and one blob statistic throws it away. Still hand-crafted, still inside the study's rules. **The highest-value modelling investment available** |
| 3.2 | **Compute color and GLCM on blade pixels only**, after the plant mask. Drop absolute luminance; keep chromaticity / hue-saturation. Add multi-scale GLCM (64 px and 128 px). | Absolute RGB histograms encode water tint, white balance and sand coverage more than species. `enhalus↔ovalis` may be substantially a background statistic. GLCM on an unmasked crop measures epiphyte load and zoom, not species |
| 3.3 | **Per-blade voting:** classify each blade, average the scores, then decide per photo. | Cheap variance reduction, and it matches how a field user photographs a shoot (several blades per frame) |
| 3.4 | **Per-class decision thresholds** on the calibrated probabilities, tuned on validation to equalise per-class recall | Cheap, and it fits the existing coverage/accuracy story. **Measured 16 Nov 2026: it does not beat the global gate** (see §4) — retry only as a margin-based rejector or fitted inside the CV folds |

Expected: **+0.05 to +0.12** macro F1 from 3.1 + 3.3 if done well; +0.02 to +0.06 from 3.2. Not +35 points.

The epiphyte and macroalgae problem is a **documented limitation, not a feature-engineering target**. Do not try to engineer it away. Measure it — "recall on heavy-epiphyte frames is X" — and put it in Limitations.

---

## 4. Honest ceiling

With roughly 2,000 real photos across eight (soon nine) fine-grained classes, separated by millimetre-scale blade traits, described by 148 hand-crafted features, and classified by an SVM:

**85% test accuracy is not reachable.** Planning bands, in order of how much work is done:

| State | Balanced acc. | Full-coverage acc. | Top-3 | Accepted acc. |
|---|---|---|---|---|
| As-is, but honestly evaluated (grouped split, 9 classes) | 0.30–0.40 | 0.40–0.50 | 0.65–0.75 | — |
| Tier 1 + Tier 2 done, no new data | 0.42–0.55 | 0.50–0.58 | 0.78–0.85 | 0.68–0.78 at 40–55% coverage |
| Blade-graph features + real data for the three tail classes | 0.60–0.72 | 0.65–0.75 | — | — |

Uncertainty on these bands is roughly ±0.05–0.07. They are planning figures, not predictions. Note that the first row is *lower* than the current 49.4% headline — grouping the split will bite, and that is correct.

**Measured, first data point for row 1 (16 Nov 2026):** eight classes, grouped (dedupe) split → balanced accuracy **0.353**, full-coverage accuracy **0.438**, top-3 **0.790**, accepted accuracy 0.550 at 51.5% coverage. All three land inside the "as-is, honestly evaluated" band. Grouping cost about 5.6 points of full-coverage accuracy against the 49.4% image-split headline, which is the honesty discount this section predicted. The band row says "9 classes": that run trained eight, so class 9 would add a ninth zero-recall column on top of these numbers rather than lift them. Its grouping was `per-file`, though, so the paragraph below supersedes it.

**Measured, nine classes and true observation grouping (16 Nov 2026):** `ml/artifacts/runs/20261116T094521023Z-svm/record.md`. 3,896 `all` images → 3,701 kept → 2,032 after the 400-per-class cap, grouped by the **iNaturalist observation id** (`inaturalist` mode: 1,395 observations, 1,050 singletons, zero group leaks), then 1,452 / 290 / 290 by image. Test accuracy **0.269**, macro F1 **0.221**, balanced accuracy **0.269**, top-2 0.555, top-3 0.669, accuracy CI **0.213–0.324**, accepted accuracy 0.355 at 53% coverage — all under the one-vs-one vote the app ships. Macro F1 fell from 0.402 to 0.221. That is not a regression: the earlier numbers let frames from one photoshoot sit on both sides of the split, and a 148-feature texture/colour SVM memorises a photoshoot. Grouped by observation, the honest number is ~0.27 accuracy, not ~0.44. This is a **measurement correction**, and it lands **below** the "as-is, honestly evaluated" band on both metrics (band 0.30–0.40 balanced, 0.40–0.50 full-coverage; measured 0.269 and 0.269). The band was already labelled optimistic, and it was: with ~2,000 real photos, nine fine-grained classes and 148 hand-crafted features, observation-honest accuracy is about a quarter, and the band's lower bound is roughly what the model reaches only after the Tier 1/Tier 2 work is done.

Two supporting observations from the same run, both worth stating in the paper:

- **Tuning is flat.** All 47 candidates sat between 0.232 and 0.241 mean CV macro F1, and the linear kernel (0.237) was inside one standard error of the best RBF. The 1-SE rule picked `rbf C=3, gamma=0.003` at 0.234, three points below the top of a plateau that has no real peak. No hyperparameter choice on these features moves the result; that is the mechanical evidence behind "more tuning does not close the gap".
- **Class 9 is not the culprit.** Thalassia scored F1 0.343, the third-best class in the run. The losses are spread across rotundata (0.215), serrulata (0.185), uninervis (0.182), syringodium (0.098) and minor (0.000, n=3). Adding the ninth class did not create the drop; observation-level evaluation exposed a weakness that was always there.

### Measured: the imbalance ablation (16 Nov 2026)

Four cells, same protocol (9 classes, grouped by iNaturalist observation, 5-fold `StratifiedGroupKFold` on real rows, 1-SE rule, test scored once, nothing exported). **Every number below is the one-vs-one vote — the rule the phone and `identify.py` ship.** Records: `ml/artifacts/runs/20261116T105912981Z-svm` (cap + weights), `.../20261116T105632306Z-svm` (cap only), `.../20261116T105309274Z-svm` (weights only), `.../20261116T100647182Z-svm` (neither), re-measured under the corrected rule.

| Cap / weights | n test | Accuracy | Majority baseline | Macro F1 | Balanced acc | Top-3 | Accepted @ 0.44 |
|---|---|---|---|---|---|---|---|
| 400 / α=1 | 290 | 0.269 | 0.197 | 0.221 | 0.269 | 0.669 | 0.350 @ 40% |
| 400 / α=0 | 290 | 0.345 | 0.197 | **0.270** | **0.279** | 0.679 | 0.429 @ 39% |
| none / α=1 | 529 | 0.327 | 0.401 | 0.230 | 0.268 | 0.792 | **0.588 @ 42%** |
| none / α=0 | 529 | **0.471** | 0.401 | 0.243 | 0.233 | **0.802** | 0.580 @ 57% |

**Two different questions, two different winners.** Accuracy prefers *no cap, no weights*; lift over the majority baseline prefers *cap, no weights* (+0.148 versus +0.070); the user-facing pair of top-3 plus accepted accuracy prefers *no cap* (0.79–0.80 and ~0.58). Anyone who quotes one column and calls it "the" result is choosing a story, not measuring one.

Read by the baseline column, not the accuracy column: the uncapped cells hold out 529 images instead of 290, and 40% of that split is `halophila_ovalis`, so their majority-class baseline is 0.401 rather than 0.197. The 0.471 is **+0.07** above "always say ovalis". The uncapped **weighted** cell is the only one that lands **below** its own baseline (−0.07): full-strength class weights give away more accuracy than they buy in recall.

Three findings worth carrying into the paper:

1. **The 400-per-class cap is not costing 20 points.** That reading came from comparing the capped 0.269 (290 test rows) with the uncapped 0.471 (529 test rows) — two different splits, and the earlier pair also mixed the vote with the probability argmax. On the identical 290-row split the only fair pair is cap+weights 0.269 versus cap-only 0.345: **dropping the class weights** is worth +7.6 points of accuracy and +4.9 of macro F1, for −0.001 of balanced accuracy.
2. **No cell gets balanced accuracy above 0.28.** The imbalance stack (cap, weights, augmentation) reshuffles which classes win; it does not raise the floor. One more mechanical reason "just fix the imbalance" is not the lever.
3. **Top-3 rises to ~0.80 with all the data** (0.669 → 0.792). The right species is in the shortlist even when the call is wrong, which is what makes an abstain-and-retake UI more defensible than a single hard label — and it is the number that should carry the product claim.

**Decision-rule correction (same day).** The first version of this table mixed two classifiers: `test_report` and the confusion matrix come from the one-vs-one vote, while balanced accuracy, top-k, the CI and acceptance came from the argmax of the probabilities. On the same 290 photos those two rules are correct on 78 versus 100 photos, so "accuracy 0.269, balanced 0.283, CI 0.281–0.414" quoted three numbers from two different classifiers. `metrics_extra.voted_calls` now feeds every number from the vote, `test_metrics_proba_argmax` is recorded separately, and `docs/09` fixes the rule for all future runs.

### Measured: per-class thresholds do not beat one global gate (16 Nov 2026)

`ml/src/thresholds.py` fits one acceptance threshold per predicted class on validation (≥5 photos, accepted accuracy above chance, otherwise `null` = never answer). Judge a rejector at **matched coverage**, because lowering a threshold always buys coverage with accuracy. Numbers are the shipped vote rule:

| Cell | Global gate at 0.44 | Global gate at matched coverage | Per-class thresholds |
|---|---|---|---|
| 400 / α=1 | 0.350 @ 40% | 0.375 @ 25% (t=0.50) | 0.364 @ 19% |
| 400 / α=0 | 0.429 @ 39% | 0.443 @ 21% (t=0.50) | 0.475 @ 14% |
| none / α=1 | 0.588 @ 42% | 0.624 @ 34% (t=0.50) | 0.531 @ 15% |

**The lever fails, honestly reported.** At comparable coverage the single global gate is never worse and is clearly better in the uncapped run (0.62 at 34% versus 0.53 at 15%). The cause is visible in the fitted values: with only ~290 validation rows and a minimum of 5 accepted photos per class, the rule abstains on `rotundata`, `serrulata` and `minor` — the three classes with the fewest validation rows — and in the uncapped cell it sets a 0.88 threshold on `ovalis` from that one split's confidence distribution. The per-class probability scale is not stable across observation groups, so a threshold fitted on one split does not transfer.

What to try instead, in order: (a) the **margin-based rejector** (row 2.10) — a `decision_function` gap is not Platt-compressed and does not need per-class calibration; (b) fit thresholds **inside the grouped CV folds** and average, so they see 5× the rows and the group structure; (c) per-blade voting (3.3), which changes the score distribution rather than the cut on it. Do not re-run this same rule on a different seed and call it new evidence.

### Measured: the class-weight sweep (16 Nov 2026)

The weights had only ever been set to "full" or "off". Sweeping the exponent on all the data (no cap, 5-fold grouped CV, same protocol, test scored once):

| Weights α | Accuracy | vs baseline (0.401) | Balanced | Top-3 | Accepted @ 0.44 | CI on accuracy |
|---|---|---|---|---|---|---|
| 0 | **0.471** | +0.070 | 0.233 | 0.802 | 0.580 @ 57% | 0.417–0.528 |
| 0.25 | 0.454 | +0.053 | 0.257 | 0.798 | 0.588 @ 56% | 0.401–0.509 |
| 0.5 | 0.423 | +0.022 | 0.270 | 0.792 | 0.579 @ 55% | 0.371–0.475 |
| 0.75 | 0.371 | −0.030 | **0.288** | 0.794 | 0.588 @ 49% | 0.321–0.420 |
| 1.0 | 0.327 | −0.074 | 0.268 | 0.792 | 0.588 @ 42% | 0.280–0.376 |

**This is the one tuning knob that was worth turning, and it produces a clean trade-off curve rather than a spike.** Accuracy falls monotonically as the rare-species weighting rises; balanced accuracy peaks at α=0.75; the accepted accuracy at the 0.44 gate is almost flat (~0.58) while coverage shrinks from 57% to 42%. Full weighting (the current default) is the worst of the five on accuracy, coverage *and* baseline lift, so there is no reason to keep α=1 as a default.

**Recommendation, stated as a decision rather than a setting:** ship **α=0.25** if the app promises "we will usually give you an answer", or **α=0.75** if it promises "we only answer when we are likely right". Do not quote a single figure without the promise it belongs to.

### The operating point to report

This is the table the evaluation chapter should carry, because it is the only honest way to present a model that abstains. All-data, α=0.25 on the left and α=0.75 on the right; a user sees one row, chosen by the confidence gate.

| Confidence gate | α=0.25: right when answering | …and how often it answers | α=0.75: right when answering | …and how often it answers |
|---|---|---|---|---|
| 0.30 | 48.1% | 90.4% | 48.5% | 71.3% |
| 0.40 | 56.3% | 67.9% | 56.5% | 53.5% |
| **0.44 (currently shipped)** | **58.8%** | **56.0%** | **58.8%** | **48.6%** |
| 0.50 | 62.9% | 42.3% | 64.6% | 39.5% |
| 0.60 | 69.2% | 25.1% | 65.6% | 23.1% |
| 0.70 | 70.6% | 12.9% | 71.6% | 12.7% |

Read it as: *"at the shipped gate, when the tool answers it is right about six times in ten, and it answers about half the time; ask for a retake otherwise."* That is a defensible product claim, and it is a better description of the system than 26.9% overall accuracy. Pair it with top-3 = 0.79–0.80 and the per-class table, and always name the baseline (0.401 on this split — the split is ovalis-heavy).

**Two things this table also settles:** per-class thresholds are dropped (they lose at matched coverage), and the "improve the imbalance" line of work is finished — five settings, all within 0.23–0.29 balanced accuracy.

### Where the errors actually go (confusion audit, `ml/src/audit_confusion.py`)

From the honest 290-row run (`20261116T094521023Z`), the largest off-diagonal cells and the classes that absorb them:

| true species | predicted as | count | share of the true class |
|---|---|---:|---:|
| halodule_uninervis | halodule_pinifolia | 10 | 20% |
| halophila_ovalis | thalassia_hemprichii | 11 | 19% |
| enhalus_acoroides | cymodocea_rotundata | 10 | 18% |
| thalassia_hemprichii | cymodocea_serrulata | 10 | 18% |
| halophila_ovalis | cymodocea_serrulata | 9 | 16% |

| predicted species | wrong photos absorbed | correct | precision |
|---|---:|---:|---:|
| cymodocea_rotundata | 37 | 7 | 0.159 |
| cymodocea_serrulata | 37 | 5 | 0.119 |
| halodule_pinifolia | 28 | 6 | 0.176 |
| thalassia_hemprichii | 25 | 17 | 0.405 |

Two classes, `rotundata` and `serrulata`, together absorb **74 wrong photos for 12 correct ones**. That is the mechanism behind the threshold result: raising a cut on a class cannot help a class that answers almost everything. The fix is aimed data and pair-specific work (row 2.4's specialists, 3.1's blade graph, 3.3's per-blade vote), not more threshold tuning.

### Out-of-set photos: the tool exists, the number does not yet (16 Nov 2026)

The SVM has **no "none of the nine" outcome**, so every photo becomes a species call — sand, a hand, a fish, a different seaweed. `ml/src/audit_negative.py` measures the gap: give it a folder of non-target photos and it reports the **false-accept rate** (named a species, and named one above the shipped confidence gate), the confidence distribution, and how many a green-mask pre-check (`leaf_focus.plant_fraction`) would have caught.

Dry run on **8 synthetic solid-colour frames** (placeholders, *not* evidence — they exist to prove the mechanism, not to produce a number): all 8 were named a species, all 8 cleared the gate, and the plant-evidence check caught 6 of 8. The two survivors were the **green** placeholders (lawn, seaweed). That is the shape of the problem in one line:

- **confidence cannot reject.** SVM probabilities are overconfident off-distribution, so a low-evidence photo still looks "confident" — the same defect that makes the retake gate weak on real seagrass.
- **a green check cannot reject other green things.** It separates sand/sky/skin/rock from plants, not seagrass from lawn.

#### The leaf-evidence pre-check was measured on real seagrass and it fails (16 Nov 2026)

Before shipping "too little blade material → refuse", the pre-check was scored on **504 real seagrass photos** (60 per class, sampled at random from `C:\Users\Akiro\MarineSeeData\Seagrass`, the same `(all)` pools training uses). It would refuse genuine blades:

| `plant_fraction` cut | Real seagrass photos refused |
|---|---|
| 0.01 | 15.3% |
| 0.02 | 21.6% |
| 0.03 | 29.0% |
| **0.05** (the value in the audit script's first draft) | **34.3%** |
| 0.10 | 45.0% |

The failure is structural, not a tuning problem. The mask is a hue + excess-green cut, so it counts *green pixels*, and the classes differ in how green a real photo is: `halodule_pinifolia` has a median `plant_fraction` of **0.024** (brown, hair-thin blades against sand) and 67% of its photos fall under 0.05, while `syringodium_isoetifolium` sits at 0.294. A single global cut therefore has to either refuse a third of the dataset or catch almost nothing.

**Consequence for the plan: drop the plant-evidence gate as a rejection mechanism.** It is safe only as the *conjunction* `preprocess.qc_reason` already uses (sky-like top third **and** almost no green), which is why that rule survives dataset QC while a standalone cut would not. Any future "not a seagrass" decision needs evidence the features can actually supply — a margin/`decision_function` gap measured on real negatives, or a trained non-target class.

**To make any claim, collect 100–200 real negatives** (sand, rock, hand, jetty, boat, fish, seaweed, land plants) and run `audit_negative.py`; report false-accept rate and false-reject rate together. Until then the honest sentence is "rejection is not implemented and not measured", not "it rejects non-seagrass".

Two ways forward, and they are not equal: an explicit **"none of these" control in the app** is cheap, safe and costs nothing in accuracy — it puts the correction in the user's hands; a **tenth "non-target" class** is the only reliable fix for other plants but changes the label set in `docs/11` and the study's scope, so it needs an adviser decision before any code.

**The control shipped (16 Nov 2026), the measurement did not.** `app/lib/screens/result_screen.dart` now shows "None of these" under every named result. Tapping it swaps the species panel for "Not one of the nine species", states that the model cannot refuse a photo by itself, and offers Take another photo or a way back to the result. `app/test/widget_test.dart` covers the swap and the return. This is user correction, not a rejector: false-accept rate is still unmeasured, and no accuracy number moves because of it. The tenth class stays undecided.

This needs a decision, not more code. Three things to do in the paper:

1. **Restate the success criterion up front and get it agreed with the adviser** before the final run. A defensible, achievable target reads like: macro recall ≥ 2× chance (0.25) with a 95% CI excluding chance; accepted-photo accuracy ≥ 75% at ≥ 40% coverage; per-class recall reported with n and CIs; all nine species represented; evaluation grouped by observation with a single test scoring.
2. **Report the 85% target and the measured shortfall explicitly**, with the mechanical explanation (feature expressiveness ceiling, a 23-image smallest class, in-situ nuisance factors) and the ablation evidence that more tuning of the same features does not close it. A panel respects "we measured the ceiling and here is the evidence" far more than a suspiciously round number.
3. **Name the single scope change that would reach 85%** — a learned feature representation (CNN embedding) and/or an order of magnitude more data — and state that it is out of scope by design. That answers "why didn't you just use a CNN?" while keeping the SVM-only contribution intact.

`docs/14-open-questions.md` items 3 and 14 and the accuracy paragraph in `docs/09-ml-pipeline.md` are where the current claim lives. Whichever option is chosen, those must change in the same edit as the claim.

---

## 5. What not to do

| Temptation | Why not |
|---|---|
| Add a CNN / YOLO / second classifier to reach 85% | Banned by `AGENTS.md` unless `docs/09-ml-pipeline.md` and the paper change first. It would also be a different study, and the paper chose SVM for the small localized dataset and mobile constraints |
| SMOTE (or any interpolation) on the 148-d feature vector | Interpolating blade-width and vein-count attributes invents blade shapes that do not exist. That is the "do not invent science" line |
| More augmentation copies | Train accuracy is already 1.000. More synthetic rows deepen the memorisation and raise the tuning-selected `C` further |
| Quoting 49.4% as the headline accuracy | The test set is half two classes; the number flatters. Quote macro F1 |
| Quoting 60% / 59% coverage as the v1 result | Those come from the curated run at threshold 0.44 and describe a different model. `docs/14-open-questions.md` item 14 already records this |
| Lowering the 0.44 threshold to make coverage look better | Coverage rises, accuracy falls. The pair moves together; quoting one without the other is the error |
| Chasing parity residuals instead of accuracy | The on-device port is at decision parity with sklearn. That work is finished; it is not where the points are |
| Keeping `C=100` because it won one 245-row split | See 2.3. The selection noise is larger than the margin |
| Reporting 8-class accuracy while the paper claims nine species | One panel question dismantles it. Fix the class list or state the abstention |
| Adding a CNN "just for the features" | If a learned representation is needed, write it as future work with a one-paragraph justification. Violating the study's own scope rule mid-thesis is worse than a lower number |
| Hand-tuning on the nine bundled sample photos | n = 9. It is a smoke test, not a benchmark |

---

## 6. Split accounting (answer this before a panel asks)

A panel will do these divisions. They should already be on the page.

```text
kept real images                         2058
  enhalus 634, ovalis 592, uninervis 347, syringodium 154,
  rotundata 149, serrulata 84, pinifolia 75, minor 23
dropped by the 400-per-class cap         -426   (enhalus -234, ovalis -192)
                                         -----
after cap                                1632
  train 1142 | val 245 | test 245        (70 / 15 / 15)
augmented copies added to train          +525
                                         -----
n_train                                  1667   = train_class_counts sum
```

The 525 extra rows land only where a class was below the augmentation stop target of 200: `rotundata` 104 → 200, `syringodium` 108 → 200, `serrulata` 58 → 200, `pinifolia` 53 → 200, `minor` 16 → 64 (16 real + 3 copies each). `enhalus` (280), `ovalis` (280) and `uninervis` (243) are already above the target and receive **no** copies. Two separate constants, often confused: `train_curated.MAX_PER_CLASS = 400` is the pre-split real cap; `augment.MAX_PER_CLASS = 200` is the size at which augmentation stops.

The 426 dropped images are real data thrown away, and that is one reason the imbalance stack deserves the ablation in 2.5.

Publish a versioned label manifest alongside the metrics — `path, class, group_id, phash` — so the split can be regenerated exactly. Half a day of work, and it answers the most common methodological challenge in one file.

---

## 7. Independent review (16 Nov 2026)

A second-opinion review was run against the measured numbers, the confusion matrix, the class counts, and the SVM-only constraint, with no access to this repo. Its recommendations were merged above. The material it added that this plan did not already contain:

- **Grouped bootstrap CIs.** At n = 245 the interval is ±6 points, so the val-vs-test gap is noise. This is the cheapest credibility win in the whole document and it was missing.
- **Ablate the imbalance stack.** Running a 400 cap *and* balanced weights *and* 3× augmentation is three corrections for one problem. Un-tested; plausibly double-counting; cheap to settle.
- **Pairwise specialist diagnostic.** Because `SVC` is one-vs-one internally, a two-class `ovalis`-vs-`uninervis` score isolates whether the loss is in features or in aggregation. Run before any feature work.
- **The `probability=True` leak.** Its internal 5-fold CV ignores group keys, so it is a second, quieter leakage path and makes results seed-dependent. Use margins for evaluation.
- **One-standard-error rule and linear-SVM reference.** Choose the least flexible model within 1 SE; if linear is competitive with RBF on grouped CV, prefer linear — fewer parameters, easier to defend.
- **Ablation-style honesty about calibration**, and a margin-gap rejector as an alternative to the probability threshold.
- **Provenance/data card.** Collection dates, camera models, locations, permission, licence. `"images on Google Drive"` is not a dataset statement.

Two things in the review were checked and **not** adopted:

- Its accounting concern (about 483 unaccounted images) came from assuming a 200-image pre-split cap. The actual constants are 400 and 200 with different meanings, and the numbers reconcile exactly — see §6.
- Its suggestion to add a Python↔Dart golden-vector parity test. That already exists and passes: `app/test/local_parity_test.dart` (features, decisions, and the raw-bytes path) and `app/test/resample_test.dart` (resampler pinned to `PIL.Image.resize`). Parity is not an open risk.

Its top-2 figure (~0.69) is an **estimate** derived from the confusion matrix by assuming each row's largest off-diagonal is the runner-up. It is not a measurement — the real number needs the probability matrix. Treat it as a reason to measure, not as a result.

---

## 8. Open decisions

1. **Is the 85% target renegotiable?** Owner: adviser. Blocking for how the paper's results chapter is written.
2. **Is the Thalassia folder auditable within the remaining time?** Owner: team. Read-only scan first; the decision to include class 9 follows the scan, not before.
3. **Can more minority-class photos be collected?** Owner: team. Highest-value data, lowest technical risk.
4. **Grouping key for an observation-level split** — what field identifies a photoset? Owner: team. If no key exists, the split cannot be de-duplicated and that limitation must be stated rather than glossed.
