# Package A results — the arm ordering survives every change of measurement condition

> **Conventions:** Δ = candidate − baseline; negative = candidate better. **Inference path:**
> every scored image was generated on the stochastic (dropout-active) path and used as-is
> (registered; path bounded by tool-results.md §A). Registration:
> [packageA-registration.md](packageA-registration.md), commit `18904f0`, committed with the
> urban chip lists before any number existed.

**Question registered:** does the arm ordering survive a change of matcher, band, and
subset? **Answer: yes — one answer fills the decision table.** ~~48 of 49 condition cells rank
C2 first or tie it with C3 within noise; no flip anywhere reaches the registered 2 SE
threshold for a claimed ordering change.~~

**CORRECTED 2026-08-26.** Struck, not deleted. The count "48 of 49" **is not reproducible
from the artifact under any counting scheme** — the harness emits no cell total, and
enumeration gives 56, 42 or 24 depending on the convention; the only scheme yielding a
denominator of 49 gives a numerator of **47**. Separately, the artifact contains **two** cells
in which C1 ranks ahead of C2, not one: **EU-150 urban `bt601|phase`** (C1 by 0.0246 ± 0.2080,
reported at the time as "−0.03 ± 0.21") and **EU-150 urban `mean|phase`** (C1 by
0.0092 ± 0.2168, **not reported at the time**). Both sit far below the registered 2 SE
threshold. **The corrected statement, which needs no denominator:**

> **C2 ranks first, or ties C3 within noise, in every condition cell except two — both at
> EU-150 urban under phase correlation, one in each band conversion, and both far below the
> registered 2 SE threshold. No flip anywhere reaches that threshold, so no ordering change is
> claimed.**

Full derivation in [packageA-audit.md](packageA-audit.md) §C-2 and §C-3; corrections-log
entry **30** is drafted for this. Every other number in this document reproduces from raw to
within 0.0008 px.

## Cache verification before any reuse

regC single-draw warps and task3 warps reproduce pixel-exactly from the archived fakes under
the registered affine recipe (task3: 7/155,952 px differ by 1 DN — float32-vs-float64
rounding path, not different data); every reused RGB-KLT per-chip median re-derives exactly
from the KARIOS CSVs on disk. 1,860 fresh gray-pair KARIOS runs, 26 NCC/phase cells, zero
failures, checkpointed throughout.

## Rank stability

| set (n, arms) | conditions | ordering |
|---|---|---|
| Ankara-130 (130; pre/C1/C2) | all 7 | **C2 > C1 > pretrained — preserved everywhere** |
| EU-150 (150; C1/C2) | all 7 | **C2 > C1 — preserved everywhere** |
| Ankara-30 production (30; 4 arms) | 7 | RGB-KLT rank C3>C2>C1>pre with C3−C2 = −0.02 ± 0.09 (statistical tie); every flip across conditions is C2↔C3 (or C1↔pre under phase) at well under 2 SE — **rank unstable within noise, never a claimed change**; BT.601 KLT preserves the rank exactly |
| Ankara-30 Overpass (30; 4 arms) | 7 | C2>C3>C1>pre preserved in 5/6 non-baseline conditions; the one flip (BT.601 phase, −2.20 ± 1.43) is under 2 SE — noise |

Top-two margins, Δ(C2 − C1): Ankara-130 −0.70 ± 0.06 (RGB and BT.601 KLT), **−1.01 ± 0.17
(BT.601 NCC)**; EU-150 −0.47 ± 0.05 (RGB KLT) → **−1.15 ± 0.15 (BT.601 NCC)**. Phase
correlation (its own quantity, own column): −5.27 ± 1.00 and −2.95 ± 1.04 global-shift px.

## The registered prediction failed — in the direction that strengthens the result

> Registered: NCC rewards sharpness, so C2's blur should cost it more than under KLT; C1
> closes (≤ 50% of the KLT gap) or overtakes (Δ(C1−C2) ≤ −0.10 px at ≥ 1 SE); C2 holding
> ≥ 75% of its margin materially strengthens the restraint claim.

**Outcome:** on every set and both conversions, NCC *grew* C2's margin instead of shrinking
it (Ankara-130: +0.70 → +1.01; EU-150: +0.43 → +1.15). C2 holds > 100% of its KLT margin.
**Per the registered band: the restraint result is materially strengthened — C2's win is not
conditioned on the KLT matcher.** The sharpness-helps-NCC intuition was wrong: honest smooth
structure correlates better than sharp invented structure under template matching too.

## Urban headline (lists committed at `18904f0` before scoring)

Ankara-130 urban (n = 20), BT.601 KLT: **C2 0.591 px vs C1 0.764 vs pretrained 1.349**
[STOCH single-draw, OVP inputs] — **superseded for quotation by the production-path
re-measurement: 0.593 ± 0.041 px (POST inputs, K = 8; headline-results.md B2), which is the
institution-facing figure** —
C2 first under RGB and BT.601, KLT and NCC; same at EU-150 urban (n = 26) except one phase
cell (−0.03 ± 0.21 — pure noise). Ankara-30 urban n = 2: values reported, no verdict, as
pre-declared. Quoted beside the production-path restatement: paired C2 − pretrained on
Ankara-30 production inputs, RGB KLT = **−0.84 px** (the phase-c-results restatement quotes
≈ −0.97 on the same design's Task-3 sample; both are the production-path figures, and both
are the numbers the institution should be shown — not −1.167).

## Decision table

| condition (matcher × band × subset) | arm |
|---|---|
| every cell with a permitted verdict ~~(48/49)~~ **except the two below** | **C2** (or C2≈C3 within noise at n = 30) |
| ~~the single exception (EU-150 urban, phase corr.) | C1 by −0.03 ± 0.21 — noise, no verdict~~ | |
| **exception 1 — EU-150 urban, BT.601, phase corr.** | C1 by 0.0246 ± 0.2080 — noise, no verdict |
| **exception 2 — EU-150 urban, unweighted mean, phase corr.** | C1 by 0.0092 ± 0.2168 — noise, no verdict. **Added 2026-08-26; not reported in the original document** |

**One answer fills the table: recommend C2; supply C1 as the second arm.** C3 — available
only at n = 30 — is statistically indistinguishable from C2 wherever both exist and never
separates at ≥ 2 SE; it remains the recommended *training* configuration going forward
(phase-c3-results) but adds nothing measurable to the hand-over choice here.

## The limitation we cannot remove

Georef is unmeasurable from here: they run it, we never see it. Every number above is a
proxy. What this table establishes is that **the choice of proxy does not matter to the arm
choice** — across two matchers of different families, a third global-shift method, two band
conversions, and the urban operational subset, the ordering never changes outside noise.
That is the strongest defensibility statement available without their matcher.
