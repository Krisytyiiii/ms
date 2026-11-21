# Overfitting: what it is here, and what actually fixes it

**IMPLEMENTATION.** This file answers one question: the model memorises (`train accuracy 1.000` vs test `0.494`), so what do we change? It is a work plan with measured support, not a promise. Every number is copied from a recorded artifact and the file that holds it is named.

Sources: `ml/artifacts/v2/metrics.json`, `ml/artifacts/runs/20261106T172238348Z-svm/record.md`, `ml/artifacts/runs/20261116T084646807Z-svm/record.md`, `ml/artifacts/runs/20261116T094521023Z-svm/record.md`, `ml/src/tune_svm.py`, `ml/src/train_curated.py`, `docs/22-accuracy-plan.md`, `docs/23-ml-handover-report.md`.

## 1. The short answer

Most of what looks like overfitting in this model is **not fixable by regularising the SVM**.

About half of the apparent skill is leakage: it disappears when the split stops putting one photoshoot on both sides. The rest is a **scene-variety shortage** that no `C` value can invent. Lowering capacity shrinks the train-to-test gap; it does not raise the floor.

| Lever | Is it real? | Verdict |
|---|---|---|
| Group the split by observation | yes | Mandatory. Lowers the reported number and makes it defensible |
| Grouped CV + one-standard-error rule | yes | Mandatory. Already implemented. Small honest gain |
| Lower `C`, less local `gamma` | yes | Worth doing. Roughly flat on accuracy, shrinks the gap |
| More real photos for the four tail classes | yes | The only lever that moves the number by more than a couple of points |
| Masked colour/texture + skeleton-graph features | yes | Real but bounded, +0.02–0.12 macro F1 |
| Class weights | no | Measured negative at full strength |
| Per-class thresholds | no | Measured negative at matched coverage |
| More augmentation | no | Re-renders the same scenes; cannot add variety |

## 2. What the memorisation actually is

`train_accuracy: 1.0` against `test_accuracy: 0.4939` is memorisation, not a smooth fit. The proof is already measured — same features, same SVM family, three split rules:

| Run | Split rule | Classes | Test acc | Test macro F1 |
|---|---|---:|---:|---:|
| `20261106T172238348Z` | by image | 8 | 0.4939 | 0.406 |
| `20261116T084646807Z` | grouped, `per-file` fallback | 8 | 0.438 | 0.402 |
| `20261116T094521023Z` | grouped by iNaturalist observation | 9 | **0.269** | **0.221** |

When a whole observation can no longer straddle the split, almost half the apparent accuracy goes away. The model was reading **scenes** — substrate tone, lighting, zoom, epiphyte load — not species. That is a split defect before it is a capacity defect.

The selected hyperparameters are also suspect for the same reason. `C=100` won on a single 245-row validation split where some classes hold 4–13 photos. The standard error on a macro F1 built from 4 samples is wider than the gap between the top candidates. **The selection procedure could not tell a real gain from a lucky split.**

## 3. Fix one: selection protocol (cheap, already coded, no new data)

This is the only true anti-overfitting lever available without new photos. `ml/src/tune_svm.py` already implements both halves:

- `search_grouped_cv` — `StratifiedGroupKFold`, mean ± SE of macro F1 per candidate, on real training rows.
- `best_1se` — take the **least flexible** candidate within one standard error of the best.

Measured on the observation-grouped nine-class run: **all 47 candidates landed between 0.232 and 0.241** mean CV macro F1, and the linear kernel (0.237) was inside one SE of the best RBF. The 1-SE rule picked `RBF C=3, gamma=0.003`. There is no peak to find — which is the mechanical proof that "tune harder" is not the fix.

Two supporting rules, both already in the pipeline:

- **Tune on real rows, then augment for the final fit.** Augmented copies in the tuning split inflate high-`C` candidates, because the copies are near-duplicates of training scenes.
- **Do not select on `probability=True` scores.** `SVC(probability=True)` runs an internal 5-fold CV that ignores group keys — a second, quieter leak, and it makes results seed-dependent. Use `decision_function` margins for selection; keep Platt probabilities only for the UI.

## 4. Fix two: lower the capacity, and accept that it is mostly cosmetic

`C=100` on 156 dimensions is a large allowance for an RBF kernel: it permits tiny closed regions around individual photos. Sweep down. The grid already covers `RBF_C = 0.1 … 100`.

Neighbours of the selected point, from `ml/artifacts/v2/metrics.json` (`tuning_rows`, gamma fixed at 0.01):

| C | Validation macro F1 | Train accuracy |
|---:|---:|---:|
| 3 | 0.4487 | 0.954 |
| 10 | 0.4732 | 0.994 |
| 30 | 0.4718 | 0.9995 |
| **100 (selected)** | **0.4744** | **1.000** |

The spread between `C=10` and `C=100` is **0.0012**. On 245 rows that is noise, and `C=10` memorises visibly less. Any defensible rewrite should prefer the least flexible point inside one SE, not the maximum.

On `gamma`: with standardized features, `gamma='scale'` is approximately `1/156 ≈ 0.0064`, so the selected `0.01` sits on the **more local** side of the default. That is the overfitting direction. `0.003` is the measured 1-SE pick on the grouped run.

**Expectation:** lower `C` shrinks the gap and costs nothing measurable. It will not lift test accuracy into a new band.

## 5. Fix three: data variety, the only lever that moves the number

Recall is set by scene variety, not by weight. `halophila_minor` has **23 real images**, augmented three ways, and scores **0.00** test recall. Those are still 23 scenes. A model can memorise 23 scenes perfectly and learn nothing about the species.

Real kept images per class, before the 400 cap and before augmentation:

```text
enhalus 634 | ovalis 592 | uninervis 347 | syringodium 154
rotundata 149 | serrulata 84 | pinifolia 75 | halophila_minor 23
```

The measured imbalance ablation proves the point — four cells over `{cap, weights}`, same protocol, observation-grouped, test scored once:

| Cap / weights | Accuracy | Majority baseline | Macro F1 | Balanced acc | Top-3 |
|---|---:|---:|---:|---:|---:|
| 400 / α=1 | 0.269 | 0.197 | 0.221 | 0.269 | 0.669 |
| 400 / α=0 | 0.345 | 0.197 | **0.270** | **0.279** | 0.679 |
| none / α=1 | 0.327 | 0.401 | 0.230 | 0.268 | 0.792 |
| none / α=0 | **0.471** | 0.401 | 0.243 | 0.233 | **0.802** |

**No cell gets balanced accuracy above 0.28.** The imbalance stack reshuffles which classes win; it does not raise the floor. That is why "just fix the imbalance" is not the lever.

The class-weight sweep on all data (`α`, no cap) gives a clean trade-off rather than a spike:

| α | Accuracy | Balanced | Accepted @ 0.44 |
|---:|---:|---:|---|
| 0 | **0.471** | 0.233 | 0.580 @ 57% |
| 0.25 | 0.454 | 0.257 | 0.588 @ 56% |
| 0.5 | 0.423 | 0.270 | 0.579 @ 55% |
| 0.75 | 0.371 | **0.288** | 0.588 @ 49% |
| 1.0 | 0.327 | 0.268 | 0.588 @ 42% |

Full weighting (`α=1`, the current default) is the worst of the five on accuracy, coverage **and** baseline lift.

## 6. Fix four: remove the nuisance axes the model memorises

Colour is 102 of 156 dimensions (~65%). Colour is exactly the axis that moves with depth, sun angle, turbidity, white balance, and **sand tone**. A colour-heavy vector can learn "substrate + lighting" as a class cue, which is memorisation of context rather than species.

Two changes, both hand-crafted and inside the study's SVM rules:

1. **Compute HSV and GLCM on blade pixels only**, after the plant mask. Drop absolute luminance; keep chromaticity. Add GLCM at 64 px and 128 px.
2. **Replace the single global skeleton with a skeleton graph.** Nodes at branch points; edges carrying blade length, mean and max width, width:length ratio, orientation, tip angle, and per-shoot blade count.

The confusion matrix justifies the second point: `ovalis → uninervis` is the single largest error cell (14 of 245), and `uninervis → ovalis` is the mirror (6). Those two differ by blade shape, and the current 10 shape dimensions resolve that distinction poorly. `enhalus` absorbing 8 `ovalis`, 9 `uninervis` and 3 `rotundata` is consistent with a background statistic — `enhalus` is also the largest class.

## 7. What to run

```bat
python -m ml.src.train_curated --split grouped --dest-version v4 --cv-folds 5 --alpha 0.25 --max-per-class 0
```

| Flag | Why |
|---|---|
| `--split grouped` | removes the scene leak that accounts for roughly half the headline accuracy |
| `--cv-folds 5` | grouped CV plus the 1-SE rule; no single-split winner |
| `--alpha 0.25` | measured "usually give an answer" point. Use `0.75` for "only answer when likely right" |
| `--max-per-class 0` | keeps every real photo; the cap is not the bottleneck |
| `--dest-version v4` | `v3` is already the grouped-run destination name in `docs/09` and `docs/22`. Do not reuse it |

Everything else in `docs/22-accuracy-plan.md` §2 stays subordinate to the data work: no amount of protocol repair takes this model to 85%.

## 8. Expected effect, stated as planning bands

| Fix | Train-to-test gap | Test accuracy |
|---|---|---|
| Group by observation | exposed, then honest | **drops** 0.49 → ~0.27 |
| 1-SE + lower `C` | shrinks | ~flat, maybe +0.01 to +0.02 |
| More real photos for `minor` / `pinifolia` / `serrulata` / `rotundata` | shrinks a lot | **+0.05 to +0.15** macro F1 |
| Blade-masked colour/texture + skeleton graph | shrinks | +0.02 to +0.12 macro F1 |
| Class weights, per-class thresholds, more augmentation | **no effect** (measured negative) | no gain |

**85% remains unreachable** with ~2,000 real photos, nine fine-grained classes, and handcrafted features. `docs/22` puts the ceiling near 0.65–0.75 full-coverage accuracy after the data and protocol tiers are done. Reducing overfitting is about making 0.27–0.40 honest and repeatable, not about reaching the target.

## 9. Do not do these

Recorded as negative so they are not re-run as "new evidence":

1. **Raise `C` or widen the grid.** The tuned plateau is flat; a higher maximum only memorises more.
2. **Re-fit per-class thresholds on one split.** At matched coverage the global 0.44 gate is never worse. The per-class scale does not transfer across observation groups.
3. **Increase augmentation copies.** It re-renders existing scenes. Variety, not volume, is the constraint.
4. **Add class weight to fix the gap.** `α=1` is the worst setting measured on accuracy, coverage, and baseline lift.
5. **Quote a validation-only difference as a win.** At n = 245 the 95% CI on accuracy is roughly ±6 points; the 65.5% vs 60% gap is inside it.

## 10. Sentence for the paper

> The classifier reached 1.000 training accuracy against 49.39% test accuracy on an image-level split, which indicates memorisation of photographic context rather than species. Re-evaluating with observation-grouped splits reduced test accuracy to 26.9% (macro F1 0.221), confirming that roughly half of the initial estimate reflected leakage between photographs of the same plant. Grouped cross-validation with a one-standard-error selection rule found no hyperparameter peak across 47 candidates, so the retained configuration is a robust choice within a flat plateau rather than an optimum. Closing the remaining gap requires additional distinct field photographs for the underrepresented species and additional shape-based features; it is not achievable through further regularisation or class rebalancing.
