# C3 results — EU mixing, scored against its registered framing

> **Conventions (project-wide, 2026-08-21):** every paired difference is **Δ = candidate − baseline; negative = candidate better**. Where a table uses "gain", it is defined in that table's header as gain = −Δ. **Inference path:** every number in this document was measured on the **stochastic (dropout-active) path** — pix2pix's evaluated configuration — unless a row explicitly says otherwise; the delivered tool defaults to the deterministic path, whose measured agreement with the stochastic path is |Δ| ≤ 0.05 px at n = 30 resolution (shifts > ~0.15 px excluded, smaller ones not; tool-results.md §A).

**Date:** 2026-08-20 · C3 = C2's configuration with 1,200 EU reserve pairs mixed in (17.7% of
6,777 pairs; C2's exact linear 10+10 schedule; seed 42; epoch 20 only, verified latest≡20,
54.414 M params). Training clean: 20/20 epochs, zero spike events, G_L1 29.5→26.7.
Framing registered after the Europe result ([phase-c-europe-results.md](phase-c-europe-results.md)):
**mixing has nothing to repair; this tests whether it buys anything; judged per class; a null
is the expected outcome.** Evaluation: same paths, geometry, KARIOS as every prior arm —
Ankara 130, Europe 568, Cappadocia 130.

## Aggregate: no cost anywhere, one sub-material gain

| site | pre | C2 | C3 | paired C3−C2 |
|---|---|---|---|---|
| Ankara | 2.588 | 0.929 | 0.982 | **+0.014 ± 0.038 — null** |
| Europe | 1.944 | 1.493 | 1.358 | **−0.086 ± 0.018** (t ≈ −4.7; below the ±0.15 materiality band) |
| Cappadocia | 3.391 | 2.861 | 2.853 | **−0.030 ± 0.065 — null** |

All three survive point floors 10/20/30 unchanged. Zero zero-point chips. **Mixing costs the
Anatolian adaptation nothing** (Ankara and Cappadocia are statistical nulls), and buys a
statistically significant but sub-material aggregate improvement on Europe, concentrated in
the mid/dense strata (Q3 −0.157, Q4 −0.129, Q5 −0.080; Q1 +0.235 — sparse Europe got worse).

## Per class — the registered lens, and where the gain actually lives

| class (input composition) | site | n | C2 → C3 | paired |
|---|---|---|---|---|
| water ≥ 0.05 | Europe | 64 | 1.763 → 1.421 | **−0.175 ± 0.065** |
| water ≥ 0.20 | Europe | 27 | 2.752 → 2.598 | −0.233 ± 0.130 |
| salt-like (w+nv ≥ 0.413) | Europe | 16 | 3.092 → 2.809 | −0.356 ± 0.173 |
| urban (gray ≥ 0.05) | Europe | 183 | 0.957 → 0.895 | −0.109 ± 0.020 |
| urban (gray ≥ 0.20) | Europe | 27 | 0.703 → 0.686 | +0.034 ± 0.033 — null |
| urban (gray ≥ 0.05) | Ankara | 20 | 0.552 → 0.585 | +0.040 ± 0.024 — null |
| water / salt-like | Ankara, Cappadocia | 0–3 | — | **untestable: the Turkish evaluation sites contain almost no water/salt-composition chips** |

The class thresholds are descriptive cuts (0.05/0.20 and the pre-fixed salt threshold 0.413),
reported at both levels rather than tuned. The gain concentrates exactly where the corpus
census ([phase-d-results.md](phase-d-results.md), check 4) said C2's training was thin —
water-bearing and salt-like compositions — with the strongest effect on the thinnest class.
Dense urban is a null everywhere: C2 had already saturated it.

**Verdict against the registered framing:** not quite the expected null. Mixing bought a
small, class-concentrated improvement on exactly the under-represented classes, at zero
measured cost to the Turkish adaptation. The registered C3 risk statement (Turkey-only arms
lose water/urban fidelity; the mix recovers it) is scored as: **urban — no loss existed and
none was recovered (null); water — untestable on the Turkish evaluation sites (no water
chips) and confirmed in the recovery direction on the European side.** The one negative:
sparse-Europe chips (Q1) got worse under mixing (+0.235 ± 0.105), an effect to watch if a
European deployment ever matters.

## Watch item

Checkerboard, C3 arm: same profile as C2 at all three sites — strength correlates with fewer
points and worse residual (Ankara −0.52/+0.44; Europe −0.47/+0.40; Cappadocia −0.32/+0.35).
It remains a cost, not an inflation; sparsity confound noted as before.

## Arm selection note (not pre-registered, flagged as such)

No decision rule for "final arm" was registered. On the evidence: C3 weakly dominates C2 —
indistinguishable on both Turkish sites, better on Europe and on the thin classes. The
choice of C3 as the carry-forward arm is therefore a *recommendation*, recorded here with
its basis, not a registered result.
