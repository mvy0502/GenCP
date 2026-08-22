# T3 — is the reliability layer worth shipping? Result: SHIP AS RECOMMENDATION

> **Conventions:** Δ = candidate − baseline; negative = better. Registration:
> [delivery-registrations.md](delivery-registrations.md) §T3, commit `7e581b2`, before any
> number. Numbers: **Ankara [STOCH single-draw, OVP inputs]**, **Cappadocia [STOCH seed-42
> single-draw, PRE inputs]**.

Tested as what it operationally is — **a ranking under a budget**, not a threshold. The score
is the verbatim `reliability()` formula shipped in `gencp_ref.py` (input-only: Sobel density,
palette class fractions, boundary length, water-edge, with the documented weights), **not
refit and not tuned** for this test.

## The trade-off curves (C2 arm, per-chip KLT median residual over kept chips)

| budget | coverage given up | **Ankara** median | Δ vs 100% | **Cappadocia** median | Δ vs 100% |
|---|---|---|---|---|---|
| 100% | 0% | 0.9744 | — | 2.8038 | — |
| 90% | 10% | 0.9126 | −0.062 | 2.6100 | **−0.194** |
| 75% | 25% | 0.7616 | **−0.213** | 2.3794 | **−0.424** |
| 50% | 50% | 0.5906 | −0.384 | 1.8463 | −0.958 |

Both curves are monotone with no perversity. Spearman(score, residual): Ankara **−0.731**
(p = 5e−23), Cappadocia **−0.722** (p = 3e−22) — nearly identical strength at the two sites.
Kept chips also carry more points at Ankara (median 72 → 118 at the 50% budget), so the
retained set is both more accurate and better-measured.

## Verdict against the registered rule

> **SHIP AS RECOMMENDATION**: at the 75% budget, delivered median residual improves by
> **≥ 0.15 px** versus the 100% budget on **both** sites.

**Both sites clear it** — Ankara −0.213 px, Cappadocia −0.424 px. **The layer ships as a
recommendation.** The registration's explicit counter-case ("a layer that costs 25% of
coverage to buy 0.05 px is not worth shipping") does not apply: at 25% coverage given up the
layer buys 0.21–0.42 px.

**Why this matters beyond the numbers:** the same feature set *failed* as a fixed veto
threshold precisely because a threshold calibrated at Ankara met a different base rate at
Cappadocia (score median 0.201 vs 0.082; the failed rule vetoed 127/130 Cappadocia chips).
Ranking is invariant to that shift — and the near-identical Spearman values at the two sites
show the shift is still present while the ordering still works. The operational lesson,
recorded: **rank, do not threshold, when the base rate moves between sites.**

## Deviation, disclosed

The registered T3 invariance said "same per-chip residuals from the existing archived runs".
Cappadocia's archived C2 residuals **did not survive the scratchpad purge** (searched
exhaustively before concluding: no `pd_36SXJ_per_chip.csv` in any commit; the 130 archived
KARIOS sets at that site are the *pretrained* arm, recomputing to 3.452 px / 31 pts — the
phase-D pretrained row, not C2). They were therefore **regenerated** (C2 checkpoint, seed 42,
same inference and warp path, 130/130 KARIOS, zero zero-point chips) rather than reused. Same
pipeline, same estimator class; regeneration fidelity was previously bounded at −0.042 ± 0.065
px by the phase-D disk-vs-regen cross-check. The first T3 pass, run before this regeneration,
correctly returned SHIP AS INFORMATION ONLY on the unscoreable-validation branch; that
intermediate verdict is superseded by this one, and the reason is recorded rather than
overwritten.

Artifacts: `tool_runs/T3/T3_curve.csv` (Ankara), `T3_curve_cappadocia.csv`,
`T3_per_chip*.csv`, `T3_run.py`, `capp_c2/` (regenerated arm).
