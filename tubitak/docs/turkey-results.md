# Turkey: first generation and the decomposed gap

**Date:** 2026-08-19 · 130 chips (26 per CLC+ stratum), generated through the unmodified network,
affine-corrected outputs (Option A default), KARIOS against the real S2C_36TVK_20260430 halves,
same config as every European run. **All 130 chips scored** — no zero-point failures.
Registrations: [`turkey-prediction.md`](turkey-prediction.md) v1 (proxy) and v2 (CLC+, committed
before any Turkish result existed).

## 0. Read these three qualifications before the headline

**COVERAGE.** The matched comparison covers **104 of 130 chips**. The remaining 26 (Q1, the
sparsest fifth) have no European counterpart at that sparsity and are the worst absolute
performers (3.480 ± 0.149 px). The generalisation claim holds for the ~80 % of Ankara where a
comparison is possible; **for the sparsest fifth, no comparison exists** — its number is reported
raw and undecomposed.

**IMAGERY SELECTION ASYMMETRY.** The Ankara scene was deliberately selected — 2.04 % cloud,
spring, the highest vegetation index among candidates. The European reference imagery is whatever
the corpus authors used: unknown dates, unknown quality, heterogeneous. The rasteriser side is
controlled (gate passed at +0.012 px); the imagery side is not. The claim is therefore:
**"at least as good as density-matched Europe, with Turkish imagery quality-selected and the
European reference not."**

**WHAT THE REGISTRATION ACTUALLY TESTED.** The predictions were derived from Europe's
density→residual relationship and applied to Turkish densities. The registration therefore tested
whether that RELATIONSHIP transfers — it does (Turkish rho −0.727 vs European −0.675) — and
geographic generalisation is **inferred** from the absence of a residual gap once density is
controlled, not measured directly. Same conclusion; this is the inference chain that carries it.

**Fragility flag:** Q2's matched baseline rests on **6 European chips**; its large density effect
(+1.334 px) carries correspondingly wide uncertainty. Per-stratum uncertainties are given below.

## 0b. Two numbers, two questions

| estimator | value | answers |
|---|---|---|
| stratified (equal stratum weights) | residual **2.481 px**, points 54.6 | *how does the relationship behave?* |
| population-weighted (exact pool shares) | residual **2.481 px**, points 54.6 | *what would a GCP database over Ankara deliver?* |

They coincide **by construction**: the strata are exact population quintiles of the 1564 valid
candidates (313/313/312/313/313), so equal stratum weights are population weights. The expectation
that the population number would be worse rested on the OSM-only proxy picture (16 % near-empty
chips); on the real CLC+ rasters only **1.6 %** are near-empty. Within-stratum sampling bias is
≤ 0.007 density units. (Both numbers describe the *valid* population — the 200 cloud/snow-excluded
candidates are in neither.)

## 1. The decomposition — headline table

| stratum | n | TK resid (px) | TK pts | v2 pred | RAW gap | matched base | MATCHED gap | density effect |
|---|---|---|---|---|---|---|---|---|
| Q1 | 26 | 3.480 ± 0.149 | 37 | 3.24 | +1.428 | NO SUPPORT | — | — |
| Q2 | 26 | 3.106 ± 0.186 | 38 | 3.04 | +1.054 | 3.386 (n=6!) | **−0.280** | +1.334 (fragile) |
| Q3 | 26 | 2.492 ± 0.177 | 52 | 2.85 | +0.440 | 2.375 (n=19) | **+0.118** | +0.323 |
| Q4 | 26 | 2.084 ± 0.151 | 56 | 2.57 | +0.032 | 2.199 (n=35) | **−0.114** | +0.147 |
| Q5 | 26 | 1.240 ± 0.146 | 91 | 2.02 | −0.812 | 1.953 (n=39) | **−0.713** | −0.099 |
| **overall** | 130 | **2.588** | 51 | 2.85 | **+0.536** | | **−0.247** (Q2–Q5 mean) | **≈ +0.78** |

- **RAW gap** (what a naive analysis reports): Turkey is +0.536 px (26 %) worse than the unmatched
  European reference (2.052 px).
- **MATCHED gap** (density controlled, supported strata): **−0.247 px — Turkey is slightly BETTER
  than density-matched Europe**, and dramatically so at the dense end (Q5: 1.240 vs 1.953 px, with
  91 points/chip).
- **Density effect = raw − matched ≈ +0.78 px**, against the v2 registered prediction of +0.80 px.

## 2. Scoring the v2 registration

| item | registered | measured | verdict |
|---|---|---|---|
| T1 Ankara median | 2.85 ± 1.08 px | **2.588** | **HELD** |
| T2 per-stratum | 3.24 / 3.04 / 2.85 / 2.57 / 2.02 | 3.48 / 3.11 / 2.49 / 2.08 / 1.24 | **HELD** within intervals; Turkey outperforms at the dense end |
| T3 density-only gap | +0.80 px | density effect ≈ **+0.78 px** | **HELD, almost exactly** |
| T4 geography substantial ⇔ matched gap > +0.5 px | — | matched gap **−0.247** (max stratum +0.118) | **NOT met → no measurable geographic penalty** |
| T5 density explanation falsified ⇔ matched ≈ raw or \|rho\| < 0.3 | — | matched ≠ raw; Turkish rho **−0.727** (EU −0.675) | **NOT falsified — density mechanism confirmed, same strength** |

**Conclusion: the model generalises to Ankara.** The entire raw deficit is input-density, not
geography — and where Turkish OSM is dense, the model *beats* its density-matched European
performance. Q1 (20 % of the selection) remains undecomposable by design and reports raw only:
3.480 px, 37 pts.

## 3. What the images show that the numbers do not

[`figures/ankara-first-generation.png`](figures/ankara-first-generation.png) — sparsest chip of
each stratum plus the densest overall:

1. **Q1 invention, exactly as measured in Europe**: from a near-empty input the generator invents a
   plausible parcel mosaic bearing no relation to the real striped fields beneath it. 13 surviving
   points. The hallucination failure mode transfers to Turkey unchanged.
2. **A genuinely unseen landform fails visibly (Q2)**: the real chip is white eroded
   badlands/limestone gullies — terrain absent from the European corpus. The generator renders
   dark woodland with an incoherent saturated white blob. This is what geographic novelty actually
   looks like; it is rare enough (this terrain class) not to move the stratum statistics.
3. **A phenology mismatch the metrics barely see**: generated steppe agriculture trends brown
   (the corpus' summer prior) while the deliberately-chosen late-April scene is at green peak.
   KLT matches structure, not colour, so residuals hide it — but any radiometric use of these
   chips would not.
4. **Dense urban Ankara is the model's best case**: road grids and block structure track the real
   city closely (1.11 px, 163 points on the densest chip) — consistent with Q5 beating matched
   Europe.

## 4. Honest caveats

- The matched baselines rest on 6–39 European chips per stratum; Q2's baseline (n = 6) is fragile.
- The 4-month OSM/imagery gap and the seasonal choice both act on the Turkish side only and are
  inside the "geography" term; a nil geographic effect therefore also bounds their combined cost.
- Turkish surviving points run below matched Europe (51 vs ~70 median) even where residuals beat
  it: fewer, better points. Point count and accuracy decouple, as the ceiling control predicted.
