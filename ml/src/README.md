# `ml/src`

Shared Python for Colab and later inference.

| Module | Job |
|--------|-----|
| `dataset_contract.py` | Nine study slugs, nine trainable (Thalassia un-held after the audit), Drive-title matching |
| `inventory.py` | Count images under a mounted Drive root; `species_folders` finds the nested class once |
| `preprocess.py` | List `all` folders, QC, `prepare_rgb` (plant crop + resize 256, shared by train and identify), augment minority train |
| `leaf_focus.py` | Green-mask diagnostic + optional plant crop |
| `export_processed.py` | Write `data/processed/v1` + `ml/artifacts/preprocess_v1.*` |
| `features.py` | v2 locked: frame + plant HSV histograms, 128px GLCM, blade width (148 numbers) |
| `cache.py` | Content-addressed cache for QC, dHash, prepared frames, and feature vectors (outside the repo) |
| `split.py` | Stratified 70/15/15, plus a grouped variant (one observation per split) with a degraded-coverage report |
| `phash.py` | Difference hash, near-duplicate pairs, iNaturalist observation ids / EXIF time grouping, same-class observation groups |
| `metrics_extra.py` | Balanced accuracy, macro recall, top-2/3, per-class table, coverage/accuracy, grouped bootstrap CI |
| `thresholds.py` | Per-class acceptance thresholds on validation (row 2.6); a class that cannot beat chance abstains, which the app reads as "retake" |
| `audit_confusion.py` | Read a run record's test confusion matrix: biggest true -> predicted cells, and which classes absorb the wrong photos |
| `audit_negative.py` | False-accept audit for photos that are not the nine species: how often the model still names one, how many a green-mask pre-check catches, and what that cut costs on real seagrass (0.05 refuses 34% of genuine blades, measured on 504 photos) |
| `audit_thalassia.py` | Read-only audit of the held-out Thalassia folders (other taxa, habitat shots, duplicates, provenance) |
| `train_svm.py` | Scaler + SVM pipeline, balanced weights (`alpha` exponent), evaluate, export joblib/metrics |
| `tune_svm.py` | Kernel / C / gamma grid on grouped CV, plus the one-standard-error rule |
| `run_log.py` | Timestamped run folder, `run_log.jsonl`, and `run_log.md` |
| `identify.py` | Load v1 joblib, score one photo (same 256 + features as Colab) |
| `serve_identify.py` | LAN `POST /api/v1/identify` for the Flutter app |

Notebooks should import these when the repo is cloned. `01_dataset_inventory.ipynb` also inlines the same rules so a lone Colab upload still runs.
