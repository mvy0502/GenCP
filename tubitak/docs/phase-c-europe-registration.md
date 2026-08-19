# Phase C follow-up registration — C2 on European held-out chips

**Registered 2026-08-20, before any European chip has been generated with C2 or re-generated
with the pretrained weights.** Purpose: bound how much of C2's Ankara gain (−1.167 ± 0.074 px
paired) is scene adaptation. C2's fine-tuning tiles share tile 36TVK and the 2026-04-30
acquisition with the Ankara evaluation imagery; chip-level exclusion was proven pixel-wise, but
scene, atmosphere, sun angle and phenology are shared. A model that learned "this April scene"
and one that learned "Anatolian landscape" both produce the Ankara table. Europe separates them.

## Design (fixed before generation)

- **Chips:** all 568 = 577 in `GenCP_HR_DB/image_pairs/test/` minus the **9 registered
  train/test-overlap chips** (geometry-finding.md §12.1). The test split was never used in
  fine-tuning (C1/C2 trained on Turkish tiles only) and is disjoint from the 1200-pair C3
  reserve (drawn from `train/`).
- **Generators:** pretrained `latest_net_G.pth` (54.414 M) and C2 **epoch 20 only** — the same
  checkpoint-discipline rule as the Ankara evaluation. Both generated fresh in the same local
  environment (paired, internally consistent).
- **Inference path:** identical to the Ankara evaluation — `test.py --model test
  --dataset_mode single --norm batch --load_size 256 --crop_size 256`, no `--eval`, CPU.
  Input = the render half (right 257 px) of each pair; `test.py` resizes 257→256 bicubic,
  the corpus-native inference path.
- **Geometry:** the corpus pairs carry **no geotransform**, so each chip receives a synthetic
  origin (E 500000, N 4500000, EPSG:32636, identical for all chips). KARIOS measures
  monitored-vs-reference displacement on a shared pixel grid; the absolute origin cancels.
  Relative geometry is exactly the Ankara evaluation's: reference = satellite half at 10.0 m
  GSD from the origin; generated 256 px at the Option-A corrected GSD (10.0390625 m) from the
  same origin; both warped bilinear to the common 228×228 @ 10 m grid inset 145 m.
- **KARIOS:** `karios_gencp.json` unchanged, `confidence_threshold` 0.8 unchanged. Scoring:
  per-chip median of `hypot(dx,dy)` and point count, as in every prior run.
- **Stratification:** the Ankara Q1–Q5 bins applied as **fixed boundaries** on the same measure
  (fraction of Sobel gradient magnitude > 20 on the grayscale model-input render,
  `ankara_osm_scores.py` definition): cut points **0.09904 / 0.1588 / 0.2241 / 0.33222**.
  EU counts in those bins: Q1 30, Q2 57, Q3 106, Q4 158, Q5 217.
- **Primary estimator:** paired per-chip difference (C2 − pretrained) in median residual;
  mean ± SE and median of the differences; count of chips where C2 is worse; per-stratum table.

## Registered outcome meanings and numeric boundaries

Boundaries use the project's standing ±0.15 px materiality band and the +0.5 px
"substantial" yardstick (both pre-date this registration; turkey-prediction.md T4).

| paired C2 − pretrained on Europe | reading |
|---|---|
| **> +0.5 px** (C2 much worse) | **Catastrophic forgetting.** The Ankara gain is scene-specific and does not represent learning that survives a change of scene. |
| **+0.15 to +0.5 px** | Modest cost; partial forgetting. Ankara gain partially credible; C3's mixing rationale stands. |
| **within ±0.15 px** ("roughly equal") | C2 acquired something that costs little elsewhere; the Ankara gain is more credible as adaptation. C3 has little left to buy on this axis. |
| **< −0.15 px** (C2 better on Europe too) | Surprising general improvement; needs its own explanation. Registered candidate: the fine-tuning pairs carry our **corrected georeferencing**, whereas upstream training used the original (+1/256 scale-error) geometry — fine-tuning may have partially retrained the generator's implicit geometric prior. |

**Registered expectation (honest prior, not a gate):** some forgetting is the default outcome of
a 20-epoch single-region fine-tune; we expect C2 worse on Europe, magnitude unknown. The
question this task answers is which band.

## Checkerboard watch item — metric fixed before generation

C2's outputs show a transpose-convolution checkerboard signature. KLT can lock onto periodic
patterns, which would inflate point counts. For every generated chip (both arms, every site):
artefact strength = fraction of non-DC FFT magnitude within 3×3 windows centred on the
period-2 and period-4 peaks ((±N/2,0),(0,±N/2),(±N/4,0),(0,±N/4) of the grayscale fake).
Report per arm: Spearman rho of strength vs point count and vs residual. A rise in point count
where the artefact is strong is reported, not smoothed away; a null is reported as a null.

## What this task cannot tell

Europe measures **forgetting**, not the Ankara gain's composition directly. A C2 that holds on
Europe could still owe part of its Ankara margin to scene match; the Cappadocia ratio
(phase-d registration addendum, registered separately) addresses that axis. Conversely a C2
that collapses on Europe makes scene-specificity the leading explanation without further tests.
