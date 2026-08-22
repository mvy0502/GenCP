# Registration D — variance map at K = 32: same bar, better estimator
**Registered 2026-08-21, branch `tubitak-tool`, before any number exists. Convention:
Δ = candidate − baseline, negative = candidate better. Inference path: stochastic
(dropout-active) — the quantity under study IS the dropout ensemble.**

**What this is, explicitly:** the K = 8 variance map measured rho = +0.11…+0.14 against a
registered usability bar of +0.15 — bar not met, result standing
([tool-results.md](tool-results.md) §C). **We are not moving a bar we failed to clear; we
are fixing a measurement instrument** — the per-pixel variance estimated from 8 draws is
itself noisy, and estimator noise attenuates measured predictive power — exactly as the
composition-based badlands rule was replaced by DEM ruggedness. **The bar stays +0.15
(p < 0.01, both fine-tuned arms at one site). The K = 8 result remains on the record as the
first measurement.**

**Registered attenuation prediction:** if estimator noise is the explanation, the measured
rho should **rise with K** (K = 8 → 32). If it does not rise, the attenuation story is
wrong and the effect really is sub-bar — the more informative outcome, reported plainly.

**Invariances — identical across all draws and to the K = 8 run:** inputs (same files),
render path (none re-run), checkpoints, KARIOS config, references, warp geometry, the
KLT point sets (points come from each cell's mean-image run), analysis code path. The only
changes: number of draws (8 → 32, seeds 42…73) and the resulting variance/mean estimators.

**Design:** same 8 cells as K = 8 (Ankara-Overpass ×{pretrained, C1, C2}; Ankara-production
×{pretrained, C1, C2}; EU-150 ×{C1, C2}); 24 additional seeds per cell (draws 42…49 reused
from `tool_runs/regC/draws/`); mean-of-32 and std-of-32 composed per chip; KARIOS on the
mean-of-32 (780 runs); per-point local variance (5×5 window) vs |residual|, within-stratum
combined Spearman exactly as in registration C. Secondary read-out: Δ(mean-of-32 −
single-draw) per cell, for the worth-it clause at the registered C bands.

**Checkpointing (standing practice 7):** every draw, composition, and KARIOS result is a
file; the runner skips existing files, so a respawn resumes rather than restarts. Counted
liveness on every stage.

**Adoption discipline:** if K = 32 clears the bar, the reliability sidecar becomes eligible
to change from input-heuristic to model-derived — **reported first; not changed in the tool
in the same step.**
