# Phase D results — Cappadocia and Tuz Gölü, scored against the registrations

> **Conventions (project-wide, 2026-08-21):** every paired difference is **Δ = candidate − baseline; negative = candidate better**. Where a table uses "gain", it is defined in that table's header as gain = −Δ. **Inference path:** every number in this document was measured on the **stochastic (dropout-active) path** — pix2pix's evaluated configuration — unless a row explicitly says otherwise; the delivered tool defaults to the deterministic path, whose measured agreement with the stochastic path is |Δ| ≤ 0.05 px at n = 30 resolution (shifts > ~0.15 px excluded, smaller ones not; tool-results.md §A).

**Date:** 2026-08-20 · 130 chips per site, pretrained (regenerated same-environment; disk
cross-check −0.042 ± 0.065) vs C2 epoch 20, KARIOS unchanged. Registrations scored against
their committed texts: [phase-cd-preparation.md](phase-cd-preparation.md) §3 (sites, four-outcome
table, within-site anchoring), [phase-d-ratio-addendum.md](phase-d-ratio-addendum.md) (ratio R),
[phase-d-checks-registration.md](phase-d-checks-registration.md) (verification checks 1–7,
run and reported before this document was written).

## Site table (median residual px / median points)

| site | scene status for C2 | pretrained | C2 | paired C2−pre |
|---|---|---|---|---|
| Cappadocia 36SXJ (2026-05-27) | **clean test** — tile and date absent from fine-tuning | 3.391 / 32 | 2.861 / 39 | **−0.780 ± 0.093** (34/130 worse) |
| Tuz Gölü 36SWJ (2026-04-30) | **not a generalisation test** — itself a fine-tuning tile at the same date (registered caveat, carried inline) | 3.506 / 30 | 3.056 / 33 | −0.587 ± 0.103 (36/126; 4 chips zero-point both arms, excluded) |

Floor sensitivity (check 5): both sites' paired conclusions survive point floors 0/10/20/30 and
strengthen under them — with one exception recorded under "salt" below.

## The transfer ratio R (registered addendum)

R = equal-weight-strata gain(Cappadocia)/gain(Ankara), with gain ≡ −Δ = pretrained − C2 (positive gain = C2 better) = 1.188/1.258 = **0.945**; stratified
bootstrap (10,000 draws) 95% CI **[0.730, 1.184]**, P(R ≥ 0.7) = 0.987. Per the registration's
own instruction for a wide interval, the committed sentence is: **the transfer ratio is above
the registered 0.7 threshold ("mostly real adaptation") with 95% confidence, and is
statistically indistinguishable from full transfer.** The registered confound cuts favourably:
Cappadocia is the *harder* landform, which could only depress R — a near-unity R on the harder
site strengthens, not weakens, the conclusion. C2's Ankara gain is not scene memorisation.

## The geographic penalty, on one baseline (check 1)

All three Turkish sites scored against the same fresh 568-chip European baseline:

| site | pretrained matched gap |
|---|---|
| Ankara | **+0.226 px** (Q4 +0.17, Q5 +0.04 — dense strata ≈ 0) |
| Cappadocia | +0.446 px (flat), +0.436 (badlands) |
| Tuz Gölü | +0.458 px (non-salt), +0.513 (salt) |

A **gradient, not a uniform level** — and Phase B's "no measurable geographic penalty" was
baseline-dependent (corrections-log entry 11; the registered dense-strata criterion T4 remains
untriggered). The quality-selected scene (Ankara) carries the least penalty.

## The landform hypothesis (registered §3, scored with the repaired rule)

The committed composition rule failed as a measurement (5/130 chips at the site defined by the
terrain; near-circular) — corrections-log entry 12; **no verdict was scored against it.**
Repaired rule, registered then computed: Copernicus GLO-30 slope-std, labels committed before
scoring (`c97dbae`): 33 badlands / 65 flat.

- **Pretrained matched gap: badlands +0.436 ± 0.118 vs flat +0.449 ± 0.078 — difference
  −0.013 ± 0.141 (t = −0.09).** No morphological signature, now with power. Within the sparse
  stratum the sign even inverts (badlands +0.07, flat +0.44).
- Against the registered four-outcome table: neither site "fails" at its registered threshold
  (Tuz salt +0.513 < +0.8; badlands +0.436 < +0.5, and indistinguishable from flat). Nearest
  row: **hold/hold → "the landform explanation is wrong; the badlands chip was an isolated
  anomaly."** The strong-form landform-vocabulary hypothesis is **not supported**; what exists
  is the site-level gradient above, which tracks neither composition nor ruggedness.
- **New observation (not registered; recorded as such):** C2's *gain* concentrates on rugged
  terrain at matched density — Q1 +0.70 (badlands) vs +0.34 (flat); Q2 +2.10 vs +0.70.
  Fine-tuning specifically learned Anatolian rugged-terrain rendering.

## Salt (registered compositional-OOD probe), refined by checks 4 and 5

- **Corpus census (check 4):** 184/5,577 fine-tuning pairs (3.3%) meet the salt chips'
  composite (water+bare ≥ 0.413) threshold — but **water-dominant pairs number 8 (~0.1%)**.
  The claim therefore splits: for composite bare/water terrain, "seen but not learned" stands;
  for the water-dominant salt-lake surface (the all-water-input chips), the honest sentence is
  the registered fallback — **a class absent from training was not learned.**
- **Fragility (check 5):** C2's salt-chip gain is statistically zero at every point floor and
  fails materiality at floor 20 (−0.036 px). Committed sentence: **C2 shows no reliable
  improvement on salt chips; Tuz Gölü's overall gain is carried entirely by non-salt terrain**
  (+0.860 ± 0.121, floor-robust).
- The operational case 36SWJ_12_30 (input class boundaries rendered faithfully; boundaries
  absent in reality; 3.87 → 5.82 px while still emitting points) motivates the registered
  GCP veto rule (see phase-d-checks-registration.md; result reported separately). **Honest
  rendering of a wrong map is still wrong.**

## What the images show ([Cappadocia](figures/cappadocia-visual.png), [Tuz Gölü](figures/tuzgolu-visual.png))

- **36SXJ_6_20 is the single clearest illustration of the density finding and the demo panel:**
  empty input, high-contrast striped-field reality; pretrained invents a plausible parcel
  mosaic; C2 declines to invent; both score ~equally (3.17 vs 3.63 px). Restraint cannot
  manufacture information that the input does not carry.
- **36SXJ_9_1 (badlands):** the motivating "badlands as dark woodland" failure, reproduced in
  the pretrained panel and visibly repaired by C2 (2.53 → 0.58 px, 72 → 152 points) — the
  visual counterpart of the rugged-terrain gain above.
- **Checkerboard wording, corrected:** "cosmetic" is wrong for 36SXJ_10_23 — the lattice is
  visible there and that chip is one where C2 *loses* (2.69 → 3.20 px). The figure illustrates
  the measured cost of the artefact (its strength correlates with fewer points and worse
  residual everywhere it was measured); it does not contradict it.
- **Salt panels (36SWJ_18_24/18_23):** input says water, reality is featureless salt-lake
  surface, pretrained hallucinates a rocky landscape over it, C2 darkens but still textures.
  Neither model knows the class; see the corpus census above for why.

## Periodicity scrutiny, both arms (check 6)

The pretrained quilt/diamond mosaic does not measurably inflate or degrade its own KARIOS
numbers once stratum is controlled (within-stratum rho vs residual: Europe +0.002, Cappadocia
+0.080, Tuz −0.030; Ankara +0.224 driven by one stratum). Quilt strength is ~equal across
arms. The C2−pretrained gap sizes stand without a contamination caveat. The strongest
periodicity–points correlation anywhere is the high-frequency band at Tuz in **both** arms
(−0.43/−0.44): scene-driven, not an arm artefact.

## Standing consequence

C3 (C2 + 1,200 EU pairs = 17.7% of the mix, C2's exact schedule) runs at the 2026-08-22
quota reset. Given the Europe result (no forgetting) it is a "does mixing buy anything" test,
judged per class — water, salt-like, urban — with the corpus census as the interpretive
baseline; a null is the expected outcome and will be reported as one.
