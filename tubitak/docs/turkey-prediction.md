# Turkey pre-registration — density-only predictions, committed before any Turkish chip exists

**Registered 2026-08-19 08:43:25 UTC.** No Turkish chip has been rendered with a base layer, no Turkish chip has been
generated, and the CLC+ archive has not been opened at registration time. The framing:
**total Turkey−Europe gap = density effect + geography effect**, to be decomposed, not reported as
one number.

## The relationship these predictions come from

44 European chips carry both an OSM-only edge density and an arm-B KARIOS result.
Spearman rho(density, residual) = **−0.655**. Linear fit:

> residual = 3.108 − 2.870 × density   (support: density 0.106–0.863)

**Support warning, stated up front:** Ankara's Q1–Q3 (60 % of chips, density < 0.090) lie entirely
below the sparsest European chip we have. Predictions there are extrapolations; the evidential
weight of the decomposition rests on Q4/Q5, where Europe has genuine support (n = 8 and 36).

## T1 — Ankara median residual, from density alone

> **2.90 ± 1.13 px** (median chip density 0.072; EXTRAPOLATED)

## T2 — per-stratum predictions

| Turkish stratum | median density | predicted residual (px) | ±95 % | support |
|---|---|---|---|---|
| Q1 | 0.006 | **3.09** | 1.15 | extrapolated |
| Q2 | 0.039 | **3.00** | 1.14 | extrapolated |
| Q3 | 0.072 | **2.90** | 1.13 | extrapolated |
| Q4 | 0.116 | **2.77** | 1.12 | interpolated |
| Q5 | 0.326 | **2.17** | 1.10 | interpolated |

European binned reference at the same densities: Q4-band chips 2.995 px (n=8), Q5-band 1.972 px
(n=36).

## T3 — expected gap if geography contributes NOTHING

> Turkey median − Europe median = **+0.85 px** (mean-based: **+0.62 px**), from density alone.
> A naive comparison would report this as "Turkey is ~40 % worse" with zero geographic content.

## T4 — what would mean geography contributes substantially

> **Density-matched gap > +0.5 px on the interpolated strata (Q4/Q5).** That is ~24 % of the
> European baseline, the same materiality yardstick used for the base-layer gates, and safely
> above the per-stratum standard errors (~0.2–0.3 px at n = 26).

## T5 — what would falsify the density explanation entirely

> Either of: (a) the density-matched Q4/Q5 gap is **≈ the raw gap** (density explains < 20 % of
> it), or (b) Turkish per-stratum residuals show **no density trend** (stratum-level Spearman
> |rho| < 0.3 where the European relationship gives −0.655) — the mechanism itself absent in
> Turkey.

## Registered caveats

1. Q1–Q3 predictions extrapolate ~0.1 density units beyond European support; treat them as the
   shape of the expectation, not as tested values.
2. The 44-chip fit's scatter (±1.1 px prediction interval) is dominated by within-density chip
   variance; per-stratum means over 26 chips will be far tighter than the per-chip interval.
3. The 4-month OSM/imagery temporal gap (data-sources.md) acts in the direction of WORSE Turkish
   matching; it is part of the "geography" residual as decomposed here and cannot be separated
   from it with this design.
