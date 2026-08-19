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

---

# v2 registration — CLC+ densities on both sides (registered 2026-08-19 09:05:09 UTC)

**Why a v2 exists and is legitimate:** v1 was computed on the OSM-only proxy because the base layer
did not exist yet. The proxy mismeasured Ankara badly (median density 0.072 where the real rendered
input is 0.189). No Turkish KARIOS result exists at v2 registration time — this revises the INPUT
measurement, not the story. v1 stands above, unedited.

**Instrument note:** both sides now use the same measure — edge density of OUR CLC+ renders (EU:
the 44 arm-B chips re-rendered on CLC+; Ankara: the 1564 candidate renders).

## The v2 relationship

44 EU chips, Spearman rho(CLC+ density, arm-B residual) = **−0.675** (v1: −0.655 on the proxy).
Fit: residual = 3.459 − 3.223 × density (support 0.111–0.883).

## T1–T3 v2 (v1 in parentheses)

| | v2 | v1 |
|---|---|---|
| T1 Ankara median residual, density alone | **2.85 ± 1.08 px** | (2.90 ± 1.13) |
| T3 density-only Turkey−Europe gap | **+0.80 px median / +0.58 mean** | (+0.85 / +0.62) |

Per-stratum (final CLC+ strata): Q1 **3.24** (extrapolated) · Q2 **3.04** · Q3 **2.85** ·
Q4 **2.57** · Q5 **2.02** px — Q2–Q5 all interpolated now.

## T4/T5 v2 (thresholds unchanged, scope widened)

T4: geography substantial ⇔ matched gap > **+0.5 px** on the interpolated strata — now **Q2–Q5**,
not just Q4/Q5. T5: density explanation falsified ⇔ matched ≈ raw gap, or Turkish stratum-level
density trend |rho| < 0.3 against the EU −0.675.

## The v1 → v2 movement — itself a result

**Predictions moved almost nothing** (T1 −0.05 px, T3 −0.05 px): the proxy preserved rank order
well enough that the fitted relationship survives the variable change. **Support moved
enormously**: the fraction of the 130-chip selection with no density-matched European counterpart
falls **40 % → 20 %** (only Q1 remains unsupported), because Ankara's real rendered densities are
2.6× its OSM-only ones. An OSM-only view of "how much map data does this place have" overstated
Ankara's sparsity by that factor — the base layer supplies most of the input structure precisely
where OSM is thin.

## Matched baseline v2 (CLC+ density both sides, band = within 2× of stratum median)

| stratum | med CLC+ dens | EU chips | baseline resid | baseline pts |
|---|---|---|---|---|
| Q1 | 0.060 | 1 | **NO SUPPORT** | — |
| Q2 | 0.130 | 6 | 3.386 px | 38 |
| Q3 | 0.193 | 19 | 2.375 px | 52 |
| Q4 | 0.273 | 35 | 2.199 px | 70 |
| Q5 | 0.451 | 39 | 1.953 px | 72 |

(supersedes the v1 table in ankara-acquisition.md §7, whose Q3/Q4 medians of 0.083/0.084 betrayed
the variable mismatch — strata formed on CLC+ scores but matched on OSM-only density)
