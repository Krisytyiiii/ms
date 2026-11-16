# Open Questions

Do not silently answer these in code. When the team (or adviser) decides, write the answer here and update the related doc.

## Must confirm before we write much app code

### Product / paper

1. **Authors and official short title** for the cover page and README?
2. Keep the limitation sentence that forbids “automated species recognition,” or strike it in the next paper revision? (Repo default: SVM stays.)
3. Dataset counts: Drive inventory (30 Aug 2026) still says *Thalassia* = 0 at the Drive root. A **local** dump (19 Sep 2026) had Thalassia nested under other taxa; those folders were relocated to a top-level class. Paper still needs `[INSERT NUMBER]` updated. **No longer a zero-image blocker locally** — still held out of v1 until a mix-in audit. **Audit ran 16 Nov 2026 and returned `clean`**: 1,037 nested images, 996 usable, 749 distinct plants, 12 frames (1.2%) near-duplicating another class (`ml/artifacts/thalassia_audit.json`). **Decision (16 Nov 2026): train class 9.** `HELD_OUT_SPECIES` is now empty, so the curated pipeline reads all nine `all` pools (3,896 images); the locked `v1`/`v2` artifacts stay eight-class until a nine-class run beats validation macro F1 0.468.

4. Drive folder confirmed at `/content/drive/MyDrive/Seagrass`. **Decision (30 Aug 2026):** v1 trains **eight** classes on **`all`** folders (no research-grade, no ovalis `- Copy`). *Thalassia* remains a paper class and is **held out** of training until the relocated folder is audited. Tell the adviser this was a folder-layout gap, not a scope change.

### Mobile stack

5. **Flutter** (locked 30 Aug 2026). Android 8+ APK, physical phone, no emulator. Paper’s “Android Studio” = SDK toolchain, not daily IDE. See `16-flutter-audit-and-scaffold.md`.
6. Visitor **login** or guest-first?
7. **3D:** App **integrates** only. We do not build Blender files. Viewer plays `app/assets/models-3d/<slug>_growth.mp4` when present, else a species still, else the placeholder. **OPEN:** who delivers the remaining eight clips / `.glb` files and when.
8. Identification **on-device** or **API**? **Decision (16 Nov 2026): on-device.** The phone must scan and return a result with no internet. Export contract: `ml/src/export_mobile.py` writes `ml/artifacts/<version>/svm_mobile.bin` + `svm_mobile.json`; `ml/src/test_export_mobile.py` proves the portable math matches sklearn (max probability difference 1.6e-14, 0 label mismatches on 128 vectors). The earlier 20 Sep 2026 laptop-API decision (`ml/src/serve_identify.py`) is retained only as a LAN fallback and parity reference. Remaining work: port `preprocess.py` + `features.py` + `leaf_focus.py` to Dart behind a parity test, then switch `app/lib/classify/`. This closes evaluation rows FS-3, FS-4, and FS-5.

### Content store

9. **Firebase**, **MySQL + API**, or **bundled JSON** in the APK for v1 profiles?
10. Do admins edit content in a web console, in Firebase console, or only via a JSON PR?

### Model

11. Fixed **resize** (width × height)?
12. Exact **feature vector** (histogram bins, GLCM distances/angles, which shape metrics)?
13. SVM **kernel**, `C`, gamma, class weights?
14. **Confidence threshold** for "please retake"? Frozen at **0.44** on the curated validation pass (`retake_threshold` in `ml/artifacts/v2/metrics.json`). Accepted validation accuracy at 0.44 is 65.5%, with 58% of validation photos kept. The study line for that claim is 85%. `identify.py` reads the value from the exported metrics. The 0.20 fallback remains only when that file has no threshold. **On-device note (16 Nov 2026):** v1's `metrics.json` has no `retake_threshold`, so the mobile export is run with an explicit `--threshold 0.44` and records `retake_threshold_source` in `svm_mobile.json`. The 0.44 was frozen on the curated model, not re-fitted on v1 — the 65.5% / 58% accepted-coverage figures therefore describe the curated run and must not be quoted for the shipping v1 model. `app/test/local_parity_test.dart` locks the shipped threshold at 0.44.
15. Split **random seed** and stratification by class?

### Evaluation

16. How many respondents per user group?
17. Final questionnaire items (Likert text)?

## Nice to confirm early, not blockers for docs

18. Common names in English only, or also local names once approved?
19. May we store anonymous identify metrics (predicted class + confidence, no photo)?
20. Git remote: GitHub, Cursor-hosted, or local-only for now?

## Decisions already made in this repo

| Item | Decision | Where |
|------|----------|--------|
| One repo for app + training + docs | Yes | `06-architecture.md` |
| Images in git | No | `data/README.md` |
| Train in Colab on Drive-mounted data | Yes | `12-colab-and-training.md` |
| Classifier | SVM only | `09-ml-pipeline.md` |
| Species list | Nine names locked; Drive *Halophila spinulosa* excluded | `11-species.md` |
| Drive folder | Shared Seagrass id `1MU31a5BG3MKn1fEYV-ljhc2zS4CoE79F` | `data/README.md` |
| Inventory | Drive 30 Aug 2026: 8/9, *Thalassia* missing at Drive root. Local 19 Sep 2026: *Thalassia* relocated to its own folders; still held out of v1 | `ml/artifacts/inventory.md` |
| v1 classes | Eight Drive classes; *Thalassia* held out | `ml/src/dataset_contract.py` |
| v1 smoke test | 22.4% test acc on 100/class — baseline only | `ml/artifacts/v1_smoke_metrics.md` |
| Client toolkit | Flutter; phone only | `16-flutter-audit-and-scaffold.md` |
| v1 inference | **On-device** (16 Nov 2026); laptop API kept as fallback + parity reference | `ml/src/export_mobile.py`, `ml/src/serve_identify.py` |
| Mobile model export | `svm_mobile.bin` + `svm_mobile.json`; 5 tests prove parity with sklearn | `ml/src/test_export_mobile.py` |
| Colab v1 (full `all`) | Test acc **35.0%** (not 85%) | `ml/artifacts/v1/metrics.json` |
| Locked local v1 | Test acc **42.1%**, validation macro F1 **0.468**, RBF `C=3`, `gamma=0.01` on feature v2 | `ml/artifacts/v1/metrics.json` |
| Curated local SVM (6 Nov 2026) | Test acc **49.4%** on the leaf-visible set. The study line is 85%. Validation macro F1 **0.474**. RBF `C=100`, `gamma=0.01`, feature v3. Retake threshold **0.44** | `ml/artifacts/runs/20261106T172238348Z-svm/record.md` |
| Grouped split (16 Nov 2026, 8 classes) | Test acc **43.8%**, macro F1 **0.402**, balanced acc 0.353, top-3 0.790 on the full Drive mirror. RBF `C=10`, `gamma=0.003`, feature v3. Not exported: validation macro F1 0.432 lost to the locked 0.468. Grouping is `per-file` (no EXIF times), so these figures are optimistic | `ml/artifacts/runs/20261116T084646807Z-svm/record.md` |
| Observation-grouped, nine classes (16 Nov 2026) | **The honest number:** test acc **26.9%**, macro F1 **0.221**, balanced acc 0.269, top-3 0.669, grouped by iNaturalist observation (1,395 observations, 0 leaks) on 2,032 capped images. RBF `C=3`, `gamma=0.003`, feature v2. Not exported: validation macro F1 0.199 < 0.468. CV macro F1 plateaus at 0.232–0.241 across all 47 candidates, linear within 1 SE, so tuning cannot close it. These are one-vs-one vote numbers; the same record's probability-argmax accuracy is 34.5% | `ml/artifacts/runs/20261116T094521023Z-svm/record.md` |
| Decision rule | **One-vs-one vote** (`sklearn` `predict`), confidence = that class's coupled probability. The phone and `identify.py` both do this; the win-by-votes rule disagrees with probability-argmax by up to 13 points on the same test split | `docs/09-ml-pipeline.md` |
| Thalassia audit (16 Nov 2026) | Nested class verified **`clean`**: 996 usable frames, 749 distinct plants, 12 frames (1.2%) duplicate another class. Class 9 now trained and scoring F1 0.343 (third best) | `ml/artifacts/thalassia_audit.json` |
| SVM-vs-limitation sentence | Identification is in scope | `00-study-review.md` |
