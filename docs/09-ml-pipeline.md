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
- Tune on 15% validation. **IMPLEMENTATION:** `ml/src/tune_svm.py` fits RBF (C × gamma) and linear (C) settings with `class_weight="balanced"` on train, picks the highest validation macro F1, and never reads the test split. Notebook 02 plots train against validation macro F1 across C in place of a loss curve (an SVM has no epochs). `train_curated.py` scores the test split once, after that choice. Final grid values stay **OPEN** for the paper.
- Report accuracy (and preferably per-class precision/recall) on 15% test.
- Success line for the study: **≥ 85%** test accuracy. The curated held-out result is **49.4%**. Validation macro F1 is **0.474**. Among test photos whose top-class probability is at least **0.44**, accuracy is **60%** and coverage is **59%**. That threshold was frozen on validation. Accepted validation accuracy there is **65.5%** with **58%** of validation photos kept. The 85% line is the study target for both the raw test score and the accepted-photo claim.

Also log: confusion matrix, support per class, seed, library versions. The panel will ask.

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
