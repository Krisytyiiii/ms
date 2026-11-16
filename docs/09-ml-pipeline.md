# ML Pipeline (SVM)

**STUDY** — Chapter 2 (algorithm choice), Chapter 3 Model Building, specific objective 4.

The classifier is a **Support Vector Machine** on **extracted features**. It is not a CNN and not YOLO.

## Why SVM (do not reopen casually)

The paper’s Table 1 argument:

| Model | Why the study rejected or kept it |
|-------|-----------------------------------|
| SVM | Works on small/medium sets; low compute; no GPU required; selected |
| ANN | Needs more labeled data; heavier |
| CNN | Highest published accuracy only with large data + GPU; overfitting risk on this set |

MarineSee’s dataset is **localized and self-collected**. That is the reason for SVM. Colab having a GPU does **not** change the study choice. Use the GPU for resize/augment if useful; still train SVM.

## Dataset

**STUDY:**

- Collected at Lawigan, Taitaidaga, Manguihay, and Pujada Bay
- Leaf and canopy images
- Nine species folders as ground truth
- Split **70% / 15% / 15%** train / validation / test
- Imbalance expected; augment under-represented classes
- Augment: random flip, rotation, zoom
- Total image count in the paper is still `[INSERT NUMBER]`

**IMPLEMENTATION:** images live on **Google Drive**, not in git. Counts: `ml/artifacts/inventory.md`. Training uses **eight** classes (`TRAINABLE_SPECIES`) from the **`all`** folders. *Thalassia hemprichii* stays held out. Resize **256×256**. Split seed **42**.

The curated local run (`python ml/src/train_curated.py`, 6 Nov 2026) listed **2,175** photos, kept **2,058** after the habitat rule and **11** exact-duplicate drops, then capped Enhalus and *H. ovalis* at 400. Held-out test accuracy on that selected set is **49.4%** (245 photos). The study line is **85%**. The earlier locked run on the unfiltered local set was **42.1%** test accuracy. Record: `ml/artifacts/runs/20261106T172238348Z-svm/record.md`. Local *H. pinifolia* is 85 photos, so this is the laptop score, not a Drive-full score.

**Grouped split, measured (16 Nov 2026).** The same script on the full 16 Nov Drive mirror (7,254 image files; `all` pools 3,896, because Thalassia is now trainable) with `--split grouped --dest-version v3`: 3,701 kept after QC → 2,032 after the 400-per-class cap, grouped by iNaturalist observation id into 1,395 observations (1,050 singletons, 0 group leaks), split **1,452 train / 290 validation / 290 test**. Tuning used 5-fold `StratifiedGroupKFold` on real photos only. Held-out **test accuracy 26.9%, macro F1 0.221, balanced accuracy 0.269, top-2 0.555, top-3 0.669**, 95% CI on accuracy **0.213–0.324**; accepted accuracy **35.5% at 53.4% coverage** (threshold 0.38, frozen on validation). All of these use the one-vs-one vote the app ships — see the decision-rule note below; the same record's probability-argmax view is 34.5% accuracy, and quoting one rule's accuracy beside the other's interval is the error that note exists to prevent. **Nothing was exported:** validation macro F1 0.199 is far below the locked 0.468, so `v2` remains the shipped model. Record: `ml/artifacts/runs/20261116T094521023Z-svm/record.md`.

**Why this is lower than the 6 Nov 49.4% and the 16 Nov 8-class 43.8%.** Both earlier runs let frames from one photoshoot land on both sides of the split; grouping by observation id removes that leak, and a colour/texture SVM that has seen a photoshoot's sand, water and white balance recognises the photoshoot rather than the plant. The 26.9% is therefore the first observation-honest estimate, not a regression. It also shows the 8-class `per-file` run was optimistic even though it was already grouped by dedupe. The CV sweep in the same run is the mechanism behind the ceiling: all 47 kernel/C/gamma candidates scored between **0.232 and 0.241** mean macro F1, the linear kernel (0.237) was within one standard error of the best RBF, and the 1-SE rule chose `rbf C=3, gamma=0.003` (0.234). No setting on these features lifts the result.

**Per-class, same run (test).** Thalassia 0.343 (support 57) is third-best; the losses sit with syringodium 0.098 (22), uninervis 0.182 (50), serrulata 0.185 (12), rotundata 0.215 (21), pinifolia 0.267 (11), ovalis 0.316 (57), enhalus 0.380 (57), minor 0.000 (3). The ninth class did not cause the drop.

The earlier 8-class grouped run is **dedupe-grouped, not observation-grouped**: the mirror carries no EXIF capture times, so `split_groups` fell back to `mode: per-file` with 8 near-duplicate pairs. It keeps duplicate frames apart but cannot keep a whole photoshoot on one side, which is why its 43.8% is optimistic. The inaturalist key added on 16 Nov fixes this for every later run.


**OPEN:** *Thalassia* source; final image size.

## Preprocess

Order from Figure 9 / Chapter 3:

1. Select images that actually show leaf shape, blade width, color
2. Resize to one fixed size (**IMPLEMENTATION:** 256×256)
3. Check class counts; augment minority classes
4. Label via species folders

**IMPLEMENTATION:** `qc_reason` drops a habitat frame when the top third is sky-like (sky fraction ≥ 0.50) and the green mask covers under 2% of the frame. Brown and pale blades stay. A class that would fall under 15 kept photos skips that habitat rule; on this local run no class needed the waiver (*H. minor* kept 23 of 24). Exact duplicate file bytes are removed before the split. Train copies are at most three per real photo: horizontal flip, rotations of ±15° and ±25°, scale 0.85–1.15, and brightness ±12% with hue left unchanged. A class stops at the median count of the larger classes, and never past 200 added up to that cap. Validation, test, and user photos are not augmented. `prepare_rgb` still crops a mid-size plant and then resizes. Identify uses that same path.

At inference, apply the **same resize and color assumptions**. Do not augment user photos.

## Feature extraction

**STUDY** names:

| Family | Paper wording | Typical implementation (IMPLEMENTATION until locked) |
|--------|---------------|------------------------------------------------------|
| Color | Color histograms | HSV histogram of the frame and of plant-mask pixels, plus plant HSV mean / spread |
| Texture | GLCM | 128px gray, distances 1/2/4, six properties averaged over four angles plus their spread |
| Shape | Contour and blade characteristics | v2: plant-mask blobs plus skeleton blade width. v3 adds max, base, and tip width, taper, endpoint count, circularity, and axis lengths |

The SVM sees a **feature vector**, not raw pixels. **IMPLEMENTATION:** `extract_vector` defaults to v2 (148 numbers). The curated export uses v3 (156 numbers) because v2 validation macro F1 was 0.448, under the 0.55 gate. `identify.py` reads `feature_spec.json` beside the joblib and calls the same `prepare_rgb` path. The 13 Oct 2026 lock remains RBF `C=3`, `gamma=0.01` on v2, in `ml/artifacts/v1`. The curated winner, chosen on validation macro F1, is RBF `C=100`, `gamma=0.01` on v3, in `ml/artifacts/v2`. The paper’s exact list stays **OPEN**.

## Train and evaluate

- Train on the 70% split.
- **Split mode matters.** `train_curated.py --split image` (default, the shipped v2 behaviour) splits by image, so frames from one photoshoot can straddle train and test and the held-out score is optimistic. `--split grouped` keeps a whole observation in one split and is the defensible mode. A grouped run must name a new `--dest-version` (e.g. `v3`) and is refused for `v2`, so the shipped artifact cannot be silently replaced. The observed straddle count is written to `metrics.json` (`split_report.groups_in_more_than_one_split`) either way.
- Observation grouping is `ml/src/phash.py`. **iNaturalist ids come first:** the Drive export names files `{observation_id}_{photo_index}_inat`, so the split can group by the real observation that produced the label (2,329 observations across the 3,896 training images). Only when names carry no id does it fall back to capture-time clustering per camera/folder (5-minute gap) and then to `per-file`, which is exactly the old image-level split — recorded as the mode, not hidden. A 64-bit difference hash (Hamming ≤ 6) is merged into the same groups so re-encoded copies also stay together.
- **Near-duplicate merging never crosses a class.** Two identical frames filed under two species are a label problem, not one observation: merging them would put two classes in one group, break stratification, and can empty a split. `split_groups(..., labels=...)` keeps them apart and reports the count as `group_report.cross_class_near_duplicates`; `train_curated.py` prints a warning when it is non-zero.
- **A grouped split can be degraded, and says so.** `split_report.degraded` is true when a class in the pool is absent from validation or test, with `classes_missing_from_val` / `classes_missing_from_test` naming them and `classes_with_single_group` naming classes that have only one observation (so they cannot be on both sides by construction). `degraded` does not stop the run, but the macro F1 is then a mean over the classes actually held out and must be quoted with that list. `folds_used` records which k-fold pair became test and validation.
- Tune on 15% validation, or grouped CV. **IMPLEMENTATION:** `ml/src/tune_svm.py` fits RBF (C × gamma) and linear (C) settings and never reads the test split. `train_curated.py --cv-folds 5` (default) scores every candidate on `StratifiedGroupKFold` over the real training rows and applies the **one-standard-error rule** (`best_1se`): among candidates within 1 SE of the best mean macro F1 it takes the simplest boundary, which is the plan's answer to a `C=100` chosen at the top of the grid. `--cv-folds 1` keeps the single-split search as a reference. Tuning uses **real photos only** — augmented copies are near-duplicates of the same scenes and would flatter high `C`. Notebook 02 plots train against validation macro F1 across C in place of a loss curve (an SVM has no epochs). `train_curated.py` scores the test split once, after that choice.
- **Imbalance is one knob, not three.** The final fit uses `class_weight` computed as inverse frequency raised to `--alpha` (1.0 = sklearn `balanced`, 0 = none). The 400-per-class cap is `--max-per-class` (0 keeps every photo), so an ablation can separate the cap from the weights instead of assuming both are needed.
- **Caching.** QC, dHash, prepared frames, and feature vectors are cached per file fingerprint under `~/.cache/marinesee` (`MARINESEE_CACHE` overrides; `--no-cache` bypasses). A retrain that only moves SVM parameters reuses them; deleting the folder is always safe because every entry is derived data.
- Report accuracy (and preferably per-class precision/recall) on 15% test.
- Success line for the study: **≥ 85%** test accuracy. The curated held-out result is **49.4%**. Validation macro F1 is **0.474**. Among test photos whose top-class probability is at least **0.44**, accuracy is **60%** and coverage is **59%**. That threshold was frozen on validation. Accepted validation accuracy there is **65.5%** with **58%** of validation photos kept. The 85% line is the study target for both the raw test score and the accepted-photo claim.

The test set is half two classes (enhalus 60 + ovalis 60 of 245), so 49.4% accuracy flatters the model. **The honest headline is macro F1 0.406 / macro recall 0.406.** Training accuracy is 1.000, the selected `C=100` came from one 245-row validation split, and Thalassia's 743 photos are not trainable yet. Diagnosis, ranked plan, and the honest ceiling are in `22-accuracy-plan.md`; the 85% decision is `14-open-questions.md` item 3.

Also log: confusion matrix, support per class, seed, library versions. The panel will ask.

### Reported numbers (multiclass-aware)

`ml/src/metrics_extra.py` computes the set that matches a nine-class problem, and `train_curated.py` writes it to `metrics.json` as `val_metrics` / `test_metrics`:

- `accuracy`, `balanced_accuracy`, `macro_recall`
- `top2_accuracy`, `top3_accuracy` — the honest framing for a tool that shows a shortlist
- `per_class` — support, correct, recall, and an `interpretable` flag (false under 20 test photos)
- `coverage_accuracy` — a table across thresholds 0.30 / 0.40 / 0.44 / 0.50 / 0.60 / 0.70, not one point
- `accuracy_ci` — grouped bootstrap (resamples observations, not images), because n = 245 has a roughly ±6-point interval

`accuracy` alone is not the headline: the test set is half two classes. Quote `balanced_accuracy` and `macro_recall` first.

### Thalassia audit (before class 9 can exist)

`ml/src/audit_thalassia.py` is read-only and writes `ml/artifacts/thalassia_audit.json` plus `thalassia_review.csv`:

```bat
.venv\Scripts\python.exe ml\src\audit_thalassia.py --root D:\path\to\Seagrass
```

It reports per-variant counts, how many frames survive the same `qc_path` filter the training pool gets, cross-class near-duplicates (a Thalassia frame matching an Enhalus/Halodule frame, i.e. a label problem in one direction or the other), the number of distinct plants behind the file count, and EXIF provenance for the data card. The verdict is `clean` / `review` and is a decision aid, not a decision. **It detects duplicate frames, not taxa** — a misfiled Thalassia photo is only caught when a near-identical file also exists in a Thalassia folder, so the sampled human pass still has to happen.

## Export

Save, next to the model:

- label map (`0` … `8` → scientific name)
- feature-vector schema / extractor version
- metrics JSON
- git commit hash of `ml/` if cloned in Colab

Suggested filenames under `ml/artifacts/` (no images):

```text
svm_seagrass.joblib
label_map.json
feature_spec.json
metrics.json
```

## What Colab is for

See `12-colab-and-training.md`. Short version: Colab runs this pipeline against Drive. This repo stores the code.

## Mobile export (on-device inference)

The APK identifies with no network, so the locked SVM is exported to a phone-portable form:

```text
ml/artifacts/v1/svm_mobile.bin    float32: scaler, support vectors, dual coefs, intercept, Platt A/B
ml/artifacts/v1/svm_mobile.json   classes, gamma, layout, feature spec, retake threshold
```

`ml/src/export_mobile.py` writes both and refuses to export unless its NumPy re-implementation of scaler → RBF → one-vs-one → Platt → Wu-Lin-Weng coupling matches `sklearn` (`max_proba_abs_diff` ~1e-14, zero label mismatches). `ml/src/test_export_mobile.py` locks that. `ml/src/mobile_fixtures.py` writes the Dart grading fixtures.

Dart runs the same math from `app/assets/ml/` (`app/lib/classify/local/`). The gate is `app/test/local_parity_test.dart`:

- **Features.** 148-value vector, blocks 0–101 color, 102–137 GLCM, 138–147 shape. Measured worst case across the nine bundled photos: color 0.003, GLCM 0.014, shape 0.040.
- **Decisions.** Every fixture reproduces `sklearn`'s slug, with confidence within 0.02. This is the check that matters.
- **Raw bytes.** The originals go through decode → EXIF → plant crop → 256px → features → SVM, which is the path the phone runs. `app/test/resample_test.dart` pins the resampler to `PIL.Image.resize`.

Two known, documented residuals, not bugs to chase blind:

- The 128px GLCM plane resamples with a slightly different kernel than `skimage.transform.resize`, which moves ~63 of 16384 quantized levels by one step.
- `skimage.morphology.skeletonize` uses a compiled lookup table that ships without source, so the thinning is a documented reimplementation and the shape block carries ~0.04 absolute drift.

Retake threshold: `identify.py` and the app both gate on `retake_threshold`, falling back to 0.20 only when the metrics file has no key. v1's `metrics.json` has none, so the export is run as

```bat
.venv\Scripts\python.exe ml\src\export_mobile.py --version v1 --threshold 0.44
```

with the 0.44 decision from `14-open-questions.md` item 14 written into the JSON as `retake_threshold_source`. Without the explicit flag the phone would silently ship the 0.20 fallback and never ask for a retake.

Per-class acceptance: `ml/src/thresholds.py` also fits one acceptance threshold per *predicted* class on validation (plan row 2.6) and `train_curated.py` records it as `class_thresholds` plus `val_accepted_class_thresholds` / `test_accepted_class_thresholds`. A class that cannot keep 5 validation photos above chance maps to `null` = never accept, which reads as "retake". This is **recorded, not yet exported**: the on-device gate is still the single `retake_threshold`, so the app contract above is unchanged until the export writes a per-class table.

**Decision rule (one rule, everywhere).** `sklearn`'s `predict` is a one-vs-one **vote**; the argmax of the Platt-coupled probabilities is a different classifier, and on the same 290 test photos of the 16 Nov nine-class run it is correct on 78 versus 100 of them (0.269 vs 0.345 accuracy). The phone (`app/lib/classify/local/svm_model.dart` counts votes) and `identify.py` (`model.predict`) both return the **vote** and take *that class's* probability as the confidence, so the label and the retake gate describe the same class. Training reports now do the same: `metrics_extra.voted_calls` feeds accuracy, balanced accuracy, per-class recall and acceptance, and the probability-argmax view is kept separately as `test_metrics_proba_argmax`. Never quote a balanced accuracy or CI from one rule next to an accuracy from the other.

Frame-size note: training caps the long side at 1024 px (`load_prepared`) while `prepared_from_bytes` and the Dart app crop the frame at full resolution. Measured on 4096 px upscales of three bundled photos, the feature vectors differ by at most 0.26 on a single slot (mean under 0.007) and the predicted slug never changed, with confidence moving at most 0.03. Left as is, deliberately: the difference is below the decision-parity tolerance, and changing either side would invalidate the fixtures for no measurable gain.

