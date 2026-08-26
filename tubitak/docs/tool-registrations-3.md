# Registrations: determinism measurement, acceptance-gate re-run, K-draw experiment
**Registered 2026-08-21, branch `tubitak-tool`, before any number below exists.**

Process rule now in force (from the three ill-posed gate elements — same failure shape each
time, an unstated invariance assumption): **every gate registration carries a mandatory
section listing what it assumes identical on both sides** — data source, render path, code
path, determinism.

## A — determinism measurement (`--deterministic` vs the seeded evaluated path)

**Question:** does disabling generator dropout at inference (dropout-only; NOT `--eval`)
change the KARIOS score distribution relative to the seeded stochastic path?

**Invariances — this comparison assumes identical on both sides:** OSM data source (one
extract, shared), render path (same renders reused), code path (same `test.py` command
except the single `--no_dropout` flag), checkpoints (same files), KARIOS config, references.
Determinism: side 1 is seeded-stochastic (seed 42), side 2 is architecture-deterministic.
The ONLY degree of freedom is dropout.

**Design:** the Task-3 30-chip Ankara set, production (Geofabrik post-fix) inputs already on
disk under `tool_runs/task3/inputs/`; all four arms; per-chip median residual and points,
paired dropout-off − seeded.

**Registered bands:** |paired mean Δ| ≤ **0.05 px** per arm → *indistinguishable*; note that
`--deterministic` could become the default later, but no default change without reporting
back. Δ > **0.15 px** (materiality band) in any arm → *materially different*; the seeded
evaluated path stays default and the divergence is documented. Between → *documented
difference, seeded path stays default*. Point counts reported alongside.

## B — rasteriser acceptance gate re-run (re-measurement, not a new claim)

**This is a re-measurement of the same claim under a corrected input path, not a new
claim:** the claim is renderer-tolerance §6.2's — that substituting our rasteriser's renders
for the corpus's own reference rasters moves the held-out KARIOS residual by less than the
**unchanged acceptance bound 0.15 px**. The original PASS (+0.012 ± 0.132) was scored on a
corpus of which 17/25 inputs are now known to be stale pre-fix renders (corrections-log
entry 15) and is flagged PENDING everywhere it appears.

**Invariances — this gate assumes identical on both sides:** OSM data source (the dated
Geofabrik snapshots on disk; German chips carry a recorded snapshot-drift caveat from the
14:42 `germany-latest` re-download — reported per-chip, not hidden), render path (the
current `osm_to_raster.make_chip`, CLC+ base, post-fix `-s smart` per-chip extracts in
`geofabrik/chips/`), code path (same `test.py` inference, same KARIOS config), references
(`karios` reference set unchanged). Determinism: **inference is stochastic by design**, so
per the K-draw standing rule (n = 25 < 60) **both sides are scored on the mean of K = 8
seeded draws** (seeds 42…49); the original single-draw PASS is quoted beside the re-run with
that estimator difference stated.

**Sides:** (1) our-render fakes from the regenerated post-fix inputs; (2) corpus-reference
fakes from the same reference rasters the original gate used. Held-out 25 chips
(`acc_clcheld` stems). Verdict against the unchanged 0.15 px bound; a failed re-run of a
previously passing gate is an important result and is not smoothed.

## C — K-draw averaging: better reference + free confidence map

**Idea (from the dropout finding):** structure stable across dropout draws is model-confident;
structure that washes out is invention. Mean-of-K = reference with invention suppressed;
across-draw variance = per-pixel confidence map — the institution's mask request at pixel
resolution, derived from the model rather than input heuristics.

**Invariances — assumes identical across all draws:** inputs, render path, checkpoint,
KARIOS config; the only varying element is the dropout RNG (seeds 42…49).

**Design:** K = **8** draws (cost reported; ~8× inference, no extra rendering; if a site
proves too expensive a smaller K is justified in the report, not silently used). Arms: C2
and C1, plus pretrained on Ankara (cheap). Sites: **Ankara 130** (production-provenance
inputs where available: the Task-3 renders cover 30; the remaining 100 use the archived
Overpass inputs, split reported) and **Europe held-out, 150-chip stratified subsample**
(seeded, cost-bounded; full 568 × 8 × 2 arms ≈ 9k inferences is not justified before the
concept is proven). Comparison: mean-of-K image vs single draw (seed 42), same KARIOS
config, paired per chip. Separately: per-point |residual| vs local across-draw variance
(mean over a 5-px window at each KLT point), Spearman, within information-density stratum.

**Registered predictions and bands:**
- Mean-of-K vs single draw: predicted improvement ≥ 0 (averaging suppresses invention).
  **Worth its cost if paired improvement ≥ 0.10 px** on either site **or** the variance map
  passes its test below (either justifies the 8× compute); **not worth it if** improvement
  < 0.05 px **and** the variance test fails.
- Variance map is *real and usable* if within-stratum Spearman rho(point residual, local
  variance) ≥ **+0.15 with p < 0.01** on both arms at either site; *not usable* below +0.05.
- **Registered risk, stated in advance:** averaging blurs, and the institution's matcher is
  not KLT — a gain under KLT is conditional evidence only, reported as such like every
  KLT-based number. Blur is also confounded with the check-3 result (blur alone recovered
  ~0% of C2's gain), which cuts in favour of attributing any mean-of-K gain to invention
  suppression rather than smoothing; that argument is stated, not assumed.

If the variance map works, the reliability sidecar changes from an input-heuristic to a
model-derived quantity, and the results document says so explicitly.
