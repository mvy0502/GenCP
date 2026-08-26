# Invented structure and its consequences for chip selection

**Status:** measurement only. No pipeline file modified, no chip filter implemented.
**Date:** 2026-08-18
**Companions:** [`geometry-finding.md`](geometry-finding.md) ·
[`train-test-scale-mismatch.md`](train-test-scale-mismatch.md) ·
[`karios-validation.md`](karios-validation.md)

> **UPDATE — confirmed and strengthened by KARIOS.** The proxy metric below gave Spearman
> rho = −0.41 to −0.48. Measured with the real instrument on the geometrically corrected arm
> (n = 116 chips), the relationship is **stronger**: rho = **−0.79** (edge density), −0.71
> (non-dominant fraction) and −0.59 (class count) against residual magnitude, plus **+0.49 to +0.68**
> against surviving key-point count. The proxy was not measuring its own noise. **The site-selection
> guidance in §7 stands and is strengthened**, with edge density now the strongest single predictor.
> KARIOS also shows this lever matters more than the geometry corrections.
>
> **A ceiling control now separates the two possible causes.** Matching each REAL satellite half
> against a shifted copy of itself gives a residual of 0.0010 px with rho = +0.04 to +0.09 against
> the OSM scores — i.e. **generic matchability affects how MANY points a chip yields, but not how
> ACCURATE they are**. The accuracy correlation is therefore GenCP-specific, and survives
> controlling for point count (partial rho −0.61). See
> [`karios-validation.md`](karios-validation.md) §10.

---

## 1. The concern

For chips whose OSM input is nearly featureless — uniform landcover, a couple of faint roads — the
generator still produces a rich field mosaic with dozens of boundaries. It invents structure the
input does not describe.

For visual realism that is a success. For GenCP's purpose it may be a defect. The premise is that a
generated chip inherits known coordinates and is then matched against real imagery; an invented
edge is a **false control point**, and matching can lock onto structure that does not exist on the
ground and return a confident wrong position.

This matters directly for Turkish site selection, so it was measured rather than argued.

---

## 2. Method

40 held-out pairs (corpus test split, the 9 leaked chips excluded), each scored three ways.

**OSM information content** — three scores, because they capture different things:

| score | definition | why |
|---|---|---|
| edge density | fraction of pixels with gradient magnitude > 20 DN | the boundary structure the generator can legitimately place |
| class count | distinct landcover colours covering >= 0.1 % of the chip | semantic richness, independent of geometry |
| non-dominant fraction | 1 − share of the most common colour | a chip 95 % uniform green carries little information however many rare classes it contains |

**Fidelity** — gradient correlation between generated output and the real satellite half. The
question is whether edges land in real places, so gradients rather than colour.

**Chance floor** — measured, not assumed: gradient correlation between each generated chip and a
*different* chip's real half. Result **+0.008 ± 0.032**.

**Local match failure rate** — the fraction of 4x4-grid windows whose generated→real registration
returns more than 2 px. Both images depict the same ground, so a correct match returns ~0; a large
shift means the window locked onto non-corresponding structure. This is much closer to what KARIOS
actually does (local KLT feature matching) than any global correlation.

---

## 3. Invention, measured

| quantity | value |
|---|---|
| mean OSM edge density | 0.3035 |
| mean generated edge density | 0.6508 |
| **generated / OSM input** | **2.1x** |
| **generated / real satellite** | **0.996 mean, 0.988 median** |

**The generator produces 2.1x as much edge structure as its input contains, and lands within 0.4 %
of the real satellite's edge density.** The busyness of the output is set by what satellite imagery
generally looks like, not by how much the input actually specifies — the invention is confirmed and
quantified.

Crucially the ratio is flat against input information (figure, lower-left panel): chips with an
OSM edge density of 0.08 and of 0.85 both produce output as busy as reality. The generator fills in
detail to a learned target regardless of evidence.

---

## 4. Does it degrade matching?

### 4.1 Global fidelity says no — and is the wrong instrument

| info score | Spearman rho with fidelity |
|---|---|
| edge density | +0.066 |
| class count | +0.068 |
| non-dominant fraction | +0.179 |

No relationship. Mean fidelity is 0.248 on low-information chips and 0.260 on high-information
chips — both far above the +0.008 chance floor (33-35 standard errors), and indistinguishable from
each other.

Read alone this would say the invented structure is harmless. That conclusion would be wrong,
because a global correlation averages over the whole chip while a GCP is a *local* match.

### 4.2 The local metric finds the effect

| info score | Spearman rho with **failure rate** |
|---|---|
| edge density | **−0.410** |
| class count | **−0.430** |
| non-dominant fraction | **−0.476** |

| group | n | mean OSM edge density | failure rate | median local shift |
|---|---|---|---|---|
| LOW information | 20 | 0.161 | **0.775** | 5.93 px |
| HIGH information | 20 | 0.446 | **0.634** | 3.86 px |

By quintile of OSM edge density:

| quintile | n | mean fidelity | busy ratio | **failure rate** |
|---|---|---|---|---|
| Q1 0.000-0.144 | 8 | 0.235 | 1.085 | **0.836** |
| Q2 0.144-0.201 | 8 | 0.268 | 0.965 | **0.758** |
| Q3 0.201-0.298 | 8 | 0.215 | 1.003 | **0.695** |
| Q4 0.298-0.445 | 8 | 0.323 | 0.985 | **0.562** |
| Q5 0.445-0.852 | 8 | 0.229 | 0.942 | **0.672** |

The relationship is real and in the predicted direction: sparser OSM input produces more local
match failures. It is also **monotonic only up to Q4** — Q5 rises again, so the trend is not clean.

Figure: [`figures/hallucination-analysis.png`](figures/hallucination-analysis.png). Top row is the
global metric finding nothing; bottom row is invention and the local metric finding the trend.

---

## 5. Is there a usable threshold?

**No. The data does not support one, and it would not help if it did.**

* The relationship is a **gradual trend, not a cliff**. Failure rate slides from 0.84 to 0.56
  across quintiles with no discontinuity, and reverses in Q5. There is no value of OSM edge density
  at which behaviour changes qualitatively.
* **Even the best chips fail most windows.** The lowest failure rate of any quintile is 0.562. A
  threshold that admitted only the top quintile would still admit chips where more than half the
  local windows mismatch. Filtering by input information cannot make chips safe; it can only make
  them *less bad*.
* **40 chips, 8 per quintile.** That is enough to establish the direction and significance of the
  trend, not to place a cut point with any confidence.

What the data *does* support is **ranking rather than filtering**: OSM non-dominant fraction is the
strongest single predictor (rho = −0.476) and could order candidate sites by expected match
reliability. If a cut is wanted anyway, the bottom quintile (OSM edge density < 0.144, failure rate
0.836) is the defensible one to drop — but that is a pragmatic choice, not a threshold the data
identifies.

### Important caveat on the absolute numbers

A 56-84 % window failure rate sounds catastrophic and should not be read that way. KARIOS runs with
`outliers_filtering: true`, so failed matches are detected and discarded downstream; a high raw
failure rate means fewer surviving control points, not wrong ones — provided the filter catches
them. The measurement here says the *raw* local match rate is poor and degrades with sparse input,
not that the final GCPs are wrong at that rate. It is also sensitive to the 2 px tolerance and to
the estimator's own ~1 px noise on 64 px cross-modal windows.

---

## 6. Does upstream filter chips at all?

**No.** Searching the whole repository — `.py`, `.md`, notebook source cells — finds no selection
criterion, quality filter, scoring step, or exclusion rule applied to chips before they enter the
GCP database. The only quality mechanism is **post-hoc**: KARIOS evaluation after generation, with
`outliers_filtering: true` and `quality_level: 0.1` in the KLT matcher. Chips are generated for
whatever OSM input exists and assessed afterwards.

**Upstream saw the symptom.** The README reports KARIOS results of *"mean error around 0.7 pixel
(7m) and a RMSE around 2.5 pixels (24m) due to outliers, mostly in rural areas."*

"Mostly in rural areas" is this effect, observed and attributed to terrain type, but not diagnosed
as invented structure and not acted on with any input-side filter. The measurements above give that
observation a mechanism and a predictor.

---

## 7. What this means for Turkish site selection

1. **Prefer sites with dense, varied OSM coverage.** Match reliability tracks OSM information
   content (rho ≈ −0.48). Urban and peri-urban areas with high non-dominant fraction are the
   strongest candidates.
2. **Expect rural and uniform-landcover sites to perform worst**, consistent with both this
   measurement and upstream's own reported outlier pattern.
3. **Rank, do not threshold.** Compute the three scores over candidate AOIs and order them; the
   data does not support a defensible cut point.
4. **The generator will produce convincing detail everywhere**, including where the input specifies
   nothing. Visual plausibility of a generated chip is *not* evidence that it will match — the busy
   ratio is ~1.0 regardless of input information, while failure rate varies by 28 points.

---

## 8. Limitations

1. **40 chips, 8 per quintile.** Establishes direction and significance; too few to place a cut point.
2. **The failure criterion is a proxy.** A 2 px tolerance with bounded-search NCC on 64 px gradient
   windows is not KLT. It is closer to KARIOS than a global correlation, but only KARIOS itself
   settles the question — which is the planned run.
3. **No land-cover stratification.** "Rural" was approximated by OSM information content, not by
   actual class labels. A stratified analysis would test the upstream observation directly.
4. **Chip-level, not point-level.** GCP quality is ultimately per control point; everything here is
   aggregated per chip.
5. **The three information scores are correlated with each other** and were not orthogonalised, so
   their rho values should not be added or treated as independent evidence.

---

## 9. Reproducing

```bash
conda activate gencp
python tubitak/scripts/hallucination_analysis.py \
    --figure tubitak/docs/figures/hallucination-analysis.png --per-chip
```

Requires the generated chips under `tubitak/data/scale_test/` (gitignored); see
[`train-test-scale-mismatch.md`](train-test-scale-mismatch.md) §4.1 for how they were produced.
