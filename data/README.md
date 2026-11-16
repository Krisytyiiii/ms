# Dataset (Google Drive, not git)

**STUDY:** leaf and canopy photos of the nine Mati species, from Lawigan, Taitaidaga, Manguihay, and Pujada Bay. Split 70/15/15 after we lock the files.

**IMPLEMENTATION:** the images are already on Google Drive. This folder is only a pointer.

## Do not put images here

Git will ignore common image types. If you need a local copy for debugging, keep it outside the repo or in an ignored path.

## Expected class folders

Names must match `docs/11-species.md`:

```text
cymodocea_rotundata/
cymodocea_serrulata/
enhalus_acoroides/
halodule_pinifolia/
halodule_uninervis/
halophila_minor/
halophila_ovalis/
syringodium_isoetifolium/
thalassia_hemprichii/
```

## Drive location (locked)

| Item | Value |
|------|--------|
| Folder | [Seagrass (Shared with me)](https://drive.google.com/drive/folders/1MU31a5BG3MKn1fEYV-ljhc2zS4CoE79F) |
| Folder id | `1MU31a5BG3MKn1fEYV-ljhc2zS4CoE79F` |
| Owner (as of Aug 2026) | akeroshii |
| Colab path after shortcut | `/content/drive/MyDrive/Seagrass` |
| Listing read | **16 Nov 2026** from the shared link: 7,254 image files in 7,329 entries, ≈3.9 GB |
| Local mirror (dev only, if you pull it) | `C:\Users\Akiro\MarineSeeData\Seagrass` — outside the repo, never in git |
| Split | not on Drive; the trainer splits after QC (`--split grouped`) |

Drive titles are **not** our slugs. They look like `Enhalus acoroides dataset (all)` and `… (research-grade)`. Matching lives in `ml/src/dataset_contract.py`.

## Counts from the 16 Nov 2026 listing

`(all)` is what v1 trains on. These counts are **after pruning the Thalassia folders that sit inside five of the class folders** — the same prune `ml/src/inventory.py::iter_images` applies before training. Without it, `Halodule pinifolia (all)` reads as 876 instead of 85.

| Slug | `(all)` | `(research-grade)` |
|---|---|---|
| cymodocea_rotundata | 158 | 57 |
| cymodocea_serrulata | 87 | 15 |
| enhalus_acoroides | 666 | 362 |
| halodule_pinifolia | 85 | 19 |
| halodule_uninervis | 375 | 148 |
| halophila_minor | 24 | 3 |
| halophila_ovalis | 1549 | 378 |
| syringodium_isoetifolium | 161 | 48 |
| **trainable `(all)` total** | **3,105** | 1,030 |
| thalassia_hemprichii | **0 at root** | **0 at root** — the class is nested, see below |

These are file counts, not usable photos: QC drops blur, non-leaf and near-duplicate frames. The last counted training pool (30 Aug 2026 Drive, 19 Sep 2026 recount) was 2,058 kept real images — that recount is in `ml/artifacts/inventory.md` and is stale relative to this listing.

## Thalassia is on the Drive, but it is nested

There is still **no top-level `Thalassia hemprichii` folder**. The class exists as six nested copies, and three of them are the same 791-file `(all)` copy:

| Parent folder | Nested folder | Images |
|---|---|---|
| `Halodule pinifolia dataset (all)` | `Thalassia hemprichii dataset (all)` | 791 |
| `Halodule uninervis dataset (all)` | `Thalassia hemprichii dataset (all)` | 791 |
| `Halophila ovalis dataset (research-grade)` | `Thalassia hemprichii dataset (all)` | 791 |
| `Halodule uninervis dataset (all)` | `Thalassia hemprichii dataset (research-grade)` | 246 |
| `Enhalus acoroides dataset (research-grade)` | `Thalassia hemprichii dataset (research-grade)` | 246 |
| `Halophila ovalis dataset (research-grade)` | `Thalassia hemprichii dataset (research-grade)` | 254 |

Because `iter_images` prunes a nested different-species folder, **none of these files are trained as their parent class** — that is why `pinifolia (all)` is 85 and not 876. The nesting is also why the folder needed the audit before class 9 could be trained: the same problem may have run the other way.

- *H. minor* research-grade is **3** images, *C. serrulata* 15, *H. pinifolia* 19 — research-grade alone cannot train those classes.
- The August inventory's 378-file ovalis `(research-grade) - Copy` is no longer present; the ovalis `(research-grade)` folder now holds 378 files.
- *Halophila spinulosa* is still **not** in this mount.

**v1 (30 Aug 2026):** train the **eight** present classes from **`all`**. Notebook: `ml/notebooks/02_svm_v1_eight_class.ipynb`. Full table: `ml/artifacts/inventory.md` (stale, predates this listing).

**Audit done, verdict `clean` (16 Nov 2026).** `python ml/src/audit_thalassia.py --root <mirror>` read the two nested variants — **1,037 images** (`all` 791, `research-grade` 246), **996 pass QC**, **749 distinct plants**, 258 near-duplicate pairs inside the class, and **12 frames (1.2%)** that near-duplicate a frame in `ovalis` (9), `uninervis` (8), `enhalus` (6), `syringodium` (6) or `rotundata` (2). Some of those are distance-0 matches between consecutive iNaturalist observation ids (`…11418352` vs `…11418353`), i.e. the same photo filed under two species — worth a human pass on the 31-row queue. The tool now finds the class where it actually lives: a top-level walk saw nothing because Thalassia exists only nested, and the three identical `all` mirrors are collapsed instead of hashed three times. Result: `ml/artifacts/thalassia_audit.json`; queue: `ml/artifacts/thalassia_review.csv`.

**Nine classes are now trainable (16 Nov 2026).** `HELD_OUT_SPECIES` is empty, so `list_labeled_images` returns all nine `all` pools — **3,896 images**, Thalassia `(all)` 791 included — and `species_folders` finds the nested folder once instead of zero times. The locked `v1`/`v2` artifacts are still eight-class and are not rebuilt: a new export only replaces them if its fixed-validation macro F1 beats 0.468.

Colab steps: `docs/12-colab-and-training.md` and `ml/notebooks/README.md`.
