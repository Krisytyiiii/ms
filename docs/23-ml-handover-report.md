# ML handover report: what the artifacts support

**IMPLEMENTATION.** This is a review of the received AI/ML handover against the files actually in this repo. It is not a new result and not a claim of accuracy. Each assertion below is either traced to a recorded artifact (file named) or marked `OPEN` because nothing in the repo holds it.

Sources checked on 19 Nov 2026:

- `ml/artifacts/v2/metrics.json` — the curated run, `feature_version` v3
- `ml/artifacts/v2/feature_spec.json`, `ml/artifacts/v2/label_map.json`
- `ml/artifacts/runs/20261106T172238348Z-svm/record.md` (same run, human-readable)
- `ml/artifacts/runs/20261116T084646807Z-svm/record.md` (grouped, 8 classes)
- `ml/artifacts/runs/20261116T094521023Z-svm/record.md` (grouped, 9 classes)
- `ml/artifacts/run_log.md`, `ml/artifacts/inventory.json`
- `docs/09-ml-pipeline.md`, `docs/22-accuracy-plan.md`, `.gitignore`

## 1. Verdict in one paragraph

The **experiment** in the handover is real and traceable. Every dataset count, augmentation setting, feature dimension, hyperparameter, and evaluation score matches `ml/artifacts/v2/metrics.json` to the digit. The **packaging and integration** part is not traceable: there is no `ml/artifacts/v3/`, no joblib for v2 or v3, no integration-check record, and no `REVIEW_REQUIRED` marker anywhere in the repo. Treat the seven-phase narrative as a description of work done outside this repo until a record is committed.

## 2. Dataset preparation — verified

| Claim | Handover | Recorded | Match |
|---|---:|---:|---|
| Initially listed | 2,175 | `listed: 2175` | yes |
| Kept after filtering | 2,058 | `kept: 2058` | yes |
| Skipped | 117 | `skipped: 117` | yes |
| Habitat exclusions | 106 | `skip_reasons.habitat: 106` | yes |
| Exact duplicates removed | 11 | `skip_reasons.duplicate: 11` | yes |
| Final selected after per-class cap | 1,632 | `images_this_run: 1632` | yes |
| Per-class cap | 400 | `max_per_class: 400` | yes |
| Seed | 42 | `split_seed: 42` | yes |
| Train (real) | 1,142 | sum of `train_real_counts` = 1,142 | yes |
| Validation | 245 | `n_val: 245` | yes |
| Test | 245 | `n_test: 245` | yes |

The 70/15/15 label is coherent with 1,142 / 245 / 245 (70.0 / 15.0 / 15.0 of 1,632).

Per-class kept counts, for the record: `ovalis 592`, `enhalus 634`, `uninervis 347`, `syringodium 154`, `rotundata 149`, `serrulata 84`, `pinifolia 75`, `minor 23`.

**Class count.** Eight classes, with `thalassia_hemprichii` in `held_out`. The handover is correct that the trainable system is eight-class, not nine.

**Split mode.** The handover does not say this run is split by image. It is. `docs/09-ml-pipeline.md` records that image-level splitting lets frames from one photoshoot straddle train and test, so the held-out score is optimistic. This is not a stated limitation in the handover and should be added (see §5).

**Near-duplicate leakage.** Confirmed as a real, unresolved limitation. `docs/22-accuracy-plan.md` records 12 Thalassia frames near-duplicate a frame in another class, plus 258 duplicate pairs inside Thalassia. The handover's "unresolved groups" phrasing is accurate but understated.

## 3. Augmentation and features — verified

| Claim | Handover | `metrics.json` / `feature_spec.json` |
|---|---|---|
| Train-only augmentation | yes | `augment.splits: "train only"` |
| H-flip, rot ±15°, ±25°, scale 0.85/1.15, bright ±12%, hue unchanged | yes | `augment.kinds`, `rotation_deg`, `scale`, `brightness`, `hue` |
| Max 3 copies per photo | yes | `copies_per_photo: 3` |
| Class target = median of above-median classes, cap 200 | yes | `augment.stop`, `max_per_class: 200` |
| Real train → augmented train | 1,142 → 1,667 (+525) | `n_train: 1667`, delta 525 |
| Feature version | v3, 156 dims | `feature_version: "v3"`, `feature_spec.length: 156` |
| HSV histograms + mean/std | yes | `color` spec |
| GLCM 128 px, 32 levels, d1/d2/d4, 4 angles, 6 props, mean+range | yes | `texture` spec |
| Morphology: mask blobs, blade width, plus v3 extras | yes | `shape` spec |

`docs/22-accuracy-plan.md` lists the 156-dim split as color 0–101, GLCM 102–137, shape 138–147, but `ml/artifacts/v2/feature_spec.json` puts `blade_width_index` at 144 and `tip_index` at 148, so the doc's shape block does not cover the whole v3 tail. The authoritative split is `OPEN` in `docs/09-ml-pipeline.md`; do not quote docs/22's indices as the contract.

## 4. Model and results — verified

| Claim | Handover | Recorded |
|---|---|---|
| StandardScaler + RBF SVM | yes | `train_curated.py` pipeline; `best_params` |
| C = 100 | 100 | `C: 100.0` |
| gamma = 0.01 | 0.01 | `gamma: 0.01` |
| Probability on | yes | `probability=True` in the tuned estimator |
| Candidates tuned | 65 | 65 rows in `tuning_rows` |
| Validation accuracy | 53.88% | `0.5387755102040817` |
| Validation macro F1 | 47.44% | `0.47443749645258915` |
| Test accuracy | 49.39% | `0.49387755102040815` |
| Test macro F1 | 40.57% | `0.40568956658440986` |
| Test weighted F1 | 49.00% | `0.4900487783197591` |
| Train accuracy | (implied overfit) | `1.0` |
| Retake threshold | 0.44 | `retake_threshold: 0.44` |
| Threshold rule | max accepted acc, coverage ≥ 50% | `retake_rule` |
| Accepted accuracy / coverage (test) | 60.00% / 59.18% | `0.6` / `0.5918367346938775` |
| Accepted accuracy / coverage (val) | — | `0.6549` / `0.5796` |

Train accuracy 1.000 against validation macro F1 0.474 and `f1_gap` 0.5256 confirms the overfitting concern. It is the single clearest number in the set.

**`class_weight` is `OPEN`.** The handover says `None`. `metrics.json` records no `class_weight` field, while `docs/22-accuracy-plan.md` states `class_weight="balanced"` for the shipped row. Two repo documents and the handover disagree, and no artifact settles it. Do not assert `None` in the paper until the training call is read or re-run.

### The two accuracy figures, side by side

The handover quotes one test number. The repo holds two defensible readings of the same pipeline, and quoting either alone misleads.

| Run | Split mode | Classes | Test acc | Test macro F1 | Status |
|---|---|---:|---:|---:|---|
| `20261106T172238348Z` (curated v2) | image-level, seed 42 | 8 | **49.39%** | 0.406 | Selected. Optimistic: photoshoots straddle splits |
| `20261116T084646807Z` | grouped fallback `per-file` | 8 | **43.8%** | 0.402 | Not exported. Also optimistic, but less so |
| `20261116T094521023Z` | grouped by iNaturalist observation | 9 | **26.9%** | 0.221 | Not exported (val F1 0.199 < 0.468). The observation-honest number |

Read it this way: 49.39% is the best case, 26.9% is the honest case, and the 85% target is not met under either. The 49.39% figure is what the selected artifact scored; it is not the model's expected field accuracy. `docs/09-ml-pipeline.md` makes the same point and adds a rule worth keeping: do not quote one decision rule's accuracy beside another rule's confidence interval.

## 5. Claims this repo cannot verify — `OPEN`

| # | Handover claim | Repo evidence | Status |
|---|---|---|---|
| 1 | A `v3` package exists as a byte-for-byte copy of the frozen model | `ml/artifacts/` has `v1/` and `v2/` only | `OPEN` — no `v3/` directory |
| 2 | 27 of 27 integration checks passed | `git grep` finds no check record, no count, no log | `OPEN` — no evidence |
| 3 | Phase 7 is `REVIEW_REQUIRED` | String does not appear anywhere in the repo | `OPEN` |
| 4 | v2 and v3 joblib files exist locally, ignored by Git | `v2/` has only `feature_spec.json`, `label_map.json`, `metrics.json`. No joblib. `v1/svm_seagrass_v1.joblib` exists and is explicitly un-ignored | `CONFLICT` — v1 is the only tracked model |
| 5 | Seven phases ran in order, with an experiment per phase | No phase records, logs, or run ids for phases 1–7 as named | `OPEN` |
| 6 | Test accessed once after selection, no post-test tuning | Cannot be checked from artifacts; the 16 Nov runs post-date the 6 Nov test score | `OPEN` — worth an explicit statement of what was and was not re-tuned |

## 6. Conflicts with existing docs

1. **The name `v3` is taken.** `docs/09-ml-pipeline.md` and `docs/22-accuracy-plan.md` use `v3` as the `--dest-version` for grouped-split runs, and `train_curated.py` refuses `--dest-version v2` but allows `v3`. If a packaging artifact is also called `v3`, the pipeline flag and the package name collide. Pick a distinct name (`v3-package`, or a hash) before committing anything.
2. **`class_weight`** — see §4. Handover `None`, `docs/22` `balanced`, artifact silent.
3. **Headline accuracy** — handover implies 49.39% is the official test result. `docs/09` treats the observation-grouped 26.9% as the defensible one and calls the image-level split optimistic.
4. **Run inventory** — the handover lists no run ids, so none of its seven phases can be cross-checked against `ml/artifacts/run_log.md`. Every other result in the repo names a run id.

## 7. What the handover gets right and should be kept

- The 85% target was not met. Stated plainly, repeatedly, and correctly.
- The result is framed as a completed experimental workflow with measurable limitations, not as a success. That framing is the honest one and should survive into the paper.
- It refuses to call the retained configuration "the best possible SVM". Correct — it is the best among the documented candidates.
- It separates "integration checks passed" from "the model is accurate" and from "the physical-device workflow is validated". Correct on all three.
- The dataset limitation about near-duplicates is acknowledged rather than hidden.

## 8. Limitations to carry into the paper

1. 85% target not achieved; best honest test accuracy 26.9%, selected artifact 49.39% on an optimistic split.
2. Eight trainable species, not the nine in the study.
3. Near-duplicate leakage unresolved across splits.
4. Four classes have very small support (`minor` 23 kept / 16 real train, `pinifolia` 75, `serrulata` 84, `rotundata` 149).
5. Train accuracy 1.000 vs validation macro F1 0.474 — a large generalization gap.
6. Local dataset inventory differs from Drive inventory records.
7. Model artifact distribution unresolved: only `v1` is tracked; `v2` has no joblib in the repo.
8. No committed record of the Phase 1–7 work or the 27 integration checks.
9. Device-level validation is not established by contract tests alone.

## 9. Recommended wording for the paper

> The classifier was trained with a 156-dimension handcrafted feature vector (HSV colour, GLCM texture, plant-mask morphology) and an RBF support vector machine (`C=100`, `gamma=0.01`). On the selected artifact it reached 49.39% test accuracy (macro F1 0.406) under an image-level split. Under observation-grouped evaluation, which prevents photographs from the same collection appearing in both training and test sets, accuracy fell to 26.9% (macro F1 0.221). Both figures are below the 85% study target. Systematic experiments across class weighting, augmentation, feature configuration, and 65 SVM hyperparameter candidates did not produce a validated improvement over the retained configuration, which is therefore the best of the documented candidates rather than a solution to the accuracy problem.

## 10. What to do next, in order

1. **Decide the headline number.** Recommend reporting the grouped 26.9% with the 49.39% as the selected-artifact score and the difference explained.
2. **Resolve `class_weight`.** Read the call that produced `v2/metrics.json` or re-run with the flag recorded. One line in the record closes it.
3. **Commit an artifact record.** Either a run record for the packaging phase or a note that no packaging phase was performed. An unverifiable 27/27 check should not appear in the paper.
4. **Name the package something other than `v3`** if it is ever committed.
5. **Add the split-mode limitation** to the handover's limitation list. It is the largest unstated caveat.
