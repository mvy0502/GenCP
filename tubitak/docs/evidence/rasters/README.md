# Rasters — the seed-independent inputs to the edge-ratio measurement

**Committed 2026-08-26 as insurance**, per standing practice 10 and because the Phase D
regeneration had just been stopped by discovering that its input imagery was gone
([phase-d-regeneration-STOP.md](../../phase-d-regeneration-STOP.md)).

**These two sets are all that is needed, besides the per-seed arm warps, to recompute the
edge-ratio measurement on either mask.** With them committed, the informative-mask test can be
run in any later session even if this disk does not survive.

| set | files | source | seed-dependent? |
|---|---|---|---|
| `input_render_warped/` | 130 | `C45_s{seed}_modal/warp/input/` | **NO** — verified byte-identical across all six Modal seeds (130 files × 5 comparisons, zero differences). There is one set of 130, not 3,120 |
| `real_chip_bt601/` | 130 | `pkgA/gray/ref_ank/bt601/` | **NO** — the real Sentinel-2 reference, common to every arm and seed |

`c45_edge_ratio.py` reads exactly these two plus the per-arm warp: the mask comes from
`warp/input/{stem}.tif` (BT.601 gray, Sobel), the denominator from
`ref_ank/bt601/{stem}.tif`. **The per-seed arm warps are NOT committed here** — they are
650 files × 6 seeds and remain in `tool_runs/`; if they are lost the arm outputs must be
re-inferred, and that is a stochastic path, so it would be a replication rather than a
reproduction.

Total 26.4 MB. sha256 for all 260 files is in [../MANIFEST.md](../MANIFEST.md).
