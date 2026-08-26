# European held-out results — scored against the registration

> **Conventions (project-wide, 2026-08-21):** every paired difference is **Δ = candidate − baseline; negative = candidate better**. Where a table uses "gain", it is defined in that table's header as gain = −Δ. **Inference path:** every number in this document was measured on the **stochastic (dropout-active) path** — pix2pix's evaluated configuration — unless a row explicitly says otherwise; the delivered tool defaults to the deterministic path, whose measured agreement with the stochastic path is |Δ| ≤ 0.05 px at n = 30 resolution (shifts > ~0.15 px excluded, smaller ones not; tool-results.md §A).

**Date:** 2026-08-20 · 568 chips (577 corpus test − 9 registered train/test-overlap chips),
pretrained vs C2 epoch 20, generated in one environment, KARIOS config unchanged, geometry per
[phase-c-europe-registration.md](phase-c-europe-registration.md) (synthetic origin; registered
before generation, commit `3534a8a`). Zero zero-point chips in either arm.

## Headline, against the registered bands

> Registered bands: > +0.5 px catastrophic forgetting; +0.15…+0.5 modest cost; ±0.15 roughly
> equal; **< −0.15 general improvement, "surprising and needs its own explanation."**

**Paired C2 − pretrained: mean −0.364 ± 0.024 px (t = −15.1), median −0.343; C2 worse on
124/568.** Every stratum improves (Q1 −0.221 ± 0.133 … Q5 −0.373 ± 0.029); points 68 → 90
median (1.36×). **Verdict: the fourth band — general improvement. There is no forgetting to
repair.** The registered expectation (some forgetting, magnitude unknown) was wrong in sign.

Floor sensitivity (check 5): sign and materiality survive minimum-point floors 0/10/20/30
unchanged (−0.364 → −0.374). No flip.

## The explanation, resolved by controls

Three candidates were on the table; two were registered, the third (mechanical blur) was added
and registered before its control ran ([phase-d-checks-registration.md](phase-d-checks-registration.md), check 3).

1. **Corrected georeferencing in the fine-tuning pairs — REFUTED.** The registered prediction
   was improvement concentrated in the systematic (mean-shift) component. Decomposition of all
   568 chips: scatter change **−0.473 ± 0.024** px vs systematic change **+0.079 ± 0.018**
   (systematic slightly *worse* under C2; ~86% of the gain is scatter tightening; same answer
   in the top stratum alone).
2. **Mechanical blur ("KLT prefers smoother inputs") — REFUTED.** Registered bands: ≥ 60%
   of C2's gain recovered by spectrum-matched blurring kills the restraint claim; ≤ 25%
   supports it. Pretrained outputs blurred with the fitted global sigma (0.45; fit quality
   reported below), same georeferencing, same KARIOS (gain ≡ −Δ = pretrained − blurred, per the convention above): recovered fraction **−6.1%** on Europe
   (−7.6% excluding the empty-input stratum) and **+1.7%** at Cappadocia. Blur's per-chip
   effect is a coin flip (295/568 chips worse); its point-count effect is nil (Δn median −1).
   Independently rescored with a second implementation; numbers identical.
3. **Learned restraint — SUPPORTED, for the first time by an active control rather than
   consistency.** Corroborating spectral finding: no single Gaussian sigma matches C2's power
   spectrum (residual crosses zero 3×; a persistent +0.24 log₁₀ low-frequency excess remains)
   — C2 differs from pretrained at low-mid spatial frequencies, i.e. in rendered *content*,
   not in sharpness. The stated caveat travels with the verdict: "spectrum-matched" blurring
   means matched in the mid/high band where blur can act.

## Watch item (checkerboard/periodicity), applied to both arms

Registered metric + the symmetric general-periodicity check (check 6): C2's checkerboard-band
strength correlates with *fewer* points and *worse* residual (rho −0.28/+0.25) — it costs, it
does not inflate. The pretrained quilt band, within-stratum, is weak and inconsistent across
sites (Europe residual rho +0.002); quilt strength is essentially equal in both arms. **The
C2−pretrained gap is not measured against a contaminated reference; no size caveat needed.**

## Consequences

- **C3's rationale changes:** with no forgetting, EU mixing has nothing to repair; C3 (queued
  for the 2026-08-22 quota reset) tests whether mixing buys anything at all, judged per class
  (water / salt-like / urban), and a null is the expected result.
- The Ankara headline's transferability is quantified separately at Cappadocia
  ([phase-d-results.md](phase-d-results.md)): R above the registered 0.7 threshold.

Per-chip data: `eu_per_chip.csv`, `blur_control_per_chip.csv`, `eu_decomposition_per_chip.csv`
(session scratchpad; regenerable end-to-end from committed scripts and registrations).
