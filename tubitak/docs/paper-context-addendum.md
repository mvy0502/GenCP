# Paper Context — Handoff Document

**Purpose.** Everything an agent needs to work on the paper without reading the project's full
history. The paper matters as much as the internship deliverable and is tracked separately
from it.

**Read this first, then `tubitak/docs/` for the primary records.** Every number here is
traceable to a committed document; where a number is uncertain or contested, it says so.

**Repository:** `github.com/mvy0502/GenCP`, branch `tubitak-tr`, directory `tubitak/`

**Repository identity.** This document is the text the repository carries as
`tubitak/docs/paper-context-addendum.md` — the settled name, used by every document that
links here. It was **untracked until commit `84414d7`** (24 August 2026); corrections-log
entry 23 records why that mattered, namely that §22's non-monotonicity caveat and §16's
prior-art record had no commit timestamp and so could not be cited as predating anything.

**Provenance.** Sections 14–23 were appended **2026-08-23** as an addendum to sections 1–13,
which existed as a separate file; the two were merged into this single 1–23 text on
**2026-08-24** and committed in `84414d7`. This note replaces the addendum header
("ADDENDUM — sections 14-22 / Appended 2026-08-23") that the merge obsoleted and that was
the only record of the append date. **The 2026-08-23 date is carried forward from that
header and is not verifiable by commit timestamp** — the file was untracked at the time, so
nothing in the repository proves it. Treat it as a statement of recollection, not as a dated
claim this repository can evidence.

**Revision 2026-08-24.** Updated after the B2/B3 registration audit and the first related-work
pass. Changed since the previous version: §4 (pretrained edge ratio added; the point-count
argument bound to its panel), §5 (**the mediation result is withdrawn**), §6 and §8 (the RGB
band conversion), §9 (four new limitations), §12 (scope decided; related work done), §16
(three must-cites, the gap qualified), §19 (figure-citation rule; the objective confirmed
three ways), §21 (B2 and B3 audit outcomes, corrections-log entries 19–22, the audit base
rate), §22 (pretrained's edge ratio was measured after all). Sections not listed are unchanged.

---

## 1. The claim

> **Plausibility pressure degrades generated reference imagery for geometric matching.
> The adversarial term and a perceptual (LPIPS) reconstruction loss are each such a
> pressure, established separately.**

**REWRITTEN 2026-08-26 — this is the live claim statement, so it is rewritten rather than
struck.** The previous wording is preserved here:

> ~~Plausibility pressure degrades generated reference imagery for geometric matching. The
> adversarial term and a perceptual (LPIPS) reconstruction loss are both such pressures, and
> they act on the same lever.~~

The final clause is dropped. "The same lever" was the interaction claim, and the registered
seed-level interaction reading failed at 5/6 across six confirmatory seeds on all three
registered scales — see [seed-block-results.md](seed-block-results.md) §4, where the
pre-committed consequence fires. The claim now stops at what the six-seed block establishes:
each pressure is separately established, and nothing is asserted about how they combine.
**The word "separately" is doing deliberate work — it marks the absence of a joint claim,
rather than leaving the reader to assume one.**

Mechanism: where the conditioning input carries no information, a loss that rewards
plausibility causes the generator to invent structure. An invented edge is a false control
point. For georeferencing, a false control point is worse than no control point, because it
displaces the solution silently.

This began as a narrower claim about the adversarial term. The 2×2 factorial (§3) widened it.

---

## 2. What GenCP is, and what we did to it

**Upstream.** Guasch, Yalcin, Saunier, de Laurentiis, Goryl, Kocaman, *GENCP: GAN-Based
Ground Control Point Generation for Satellite Image Georeferencing*, Remote Sensing 18(14):2356,
DOI `10.3390/rs18142356`. ESA-funded, Telespazio. A conditional GAN (pix2pix, U-Net-256
generator, 54.414 M parameters, PatchGAN discriminator, `--direction BtoA`) renders a synthetic
Sentinel-2-like image from OpenStreetMap + land-cover input, so that copyright-restricted
reference imagery need not be shared.

**Published objective (verified from the paper's text and the upstream code, not assumed):**
adversarial + λ·LPIPS, λ = 100, BCE discriminator (`gan_mode: vanilla`). The paper does not
name the LPIPS backbone; the upstream code uses VGG. Our C4/C5 therefore reproduce *the
repository's executable definition* of the published objective, and the paper must say so in
those words.

**The discriminator is not published.** Only `latest_net_G.pth` is on Zenodo (record 15044428).
Every fine-tuning arm with an adversarial term therefore starts from a randomly initialised
discriminator, seeded and recorded in a provenance file. §5 shows this is not what causes the
adversarial arms to lose, but the paper must disclose it.

**Our work.** Fine-tuned on 5,577 Turkish pairs (Kaggle T4, 20 epochs, seed 42, linear 10+10
schedule), evaluated with KARIOS (KLT feature matching, `confidence_threshold: 0.8`) against
real Sentinel-2.

---

## 3. The core experiment — 2×2 factorial

|                     | reconstruction = L1 | reconstruction = LPIPS |
|---------------------|---------------------|------------------------|
| **adversarial ON**  | C1                  | C4                     |
| **adversarial OFF** | C2                  | C5                     |

Everything else held fixed: same training data, schedule, seed, initialisation, evaluation
chips, matcher, KARIOS configuration. The pretrained weights already occupy the C4 cell,
trained on European data rather than fine-tuned on ours — state this rather than presenting
C4 as an empty cell.

### Primary panel — Ankara, n = 130 [label: STOCH seed42, OVP]

| arm | mean (px) | median (px) | points (median) |
|---|---|---|---|
| pretrained | 2.563 | 2.588 | 51 |
| C1 (GAN + L1) | 2.075 | 1.794 | 59 |
| **C2 (L1 only)** | **1.376** | **0.974** | 72 |
| C4 (GAN + LPIPS) | 1.965 | 1.918 | 62 |
| C5 (LPIPS only) | 1.478 | 1.134 | **88** |

**Primary result (registered, fired).** C5 − C4 = **−0.487 ± 0.053 px** (t = −9.2, better on
113/130 chips; registered band was ≥ 2 SE). Adversarial OFF beats ON under *both*
reconstruction terms. The main effect is replicated, not observed once.

~~**Interaction — substitutes.** Adversarial penalty under L1 = +0.700 ± 0.059; under LPIPS =
+0.487 ± 0.053. Interaction I = −0.212 ± 0.069 (t = −3.07). LPIPS already supplies part of the
plausibility pressure, so the discriminator adds less on top of it. Consistent with this:
C4 − C1 = −0.110 (1.9 SE) — **not significant at the registered threshold**; do not write
"null".~~

**SUPERSEDED 2026-08-26.** Struck, not deleted — the original wording stands above as the
record of what was claimed on single-seed data. The registered seed-level interaction
reading failed at 5/6 across the six confirmatory seeds, on the raw, log and rank scales
alike, and the pre-committed consequence removed "substitutes" and the interaction claim
from the paper. See [seed-block-results.md](seed-block-results.md) §4. The number above is
seed 42's, with a chip-level error bar; §5(c) of the same document records that it falls
outside the range spanned by the six replicates on two of the three scales. **The paper
makes no interaction claim; it carries the disclosure at §24 below instead.**

**Secondary (fired, own finding).** C5 − C2 = +0.103 ± 0.042 (t = 2.5): perceptual
reconstruction carries its own positional penalty even with no discriminator present.

**Dose-response replicates under LPIPS.** Penalty by epoch: 0.334 → 0.254 → 0.441 → 0.496 →
0.487, all ≥ 6 SE. Same dip-then-grow-then-plateau shape as the L1 family. Training longer with
a discriminator widens the gap under both reconstruction terms.

**Production-path secondary (20 chips, K = 8 draws).** C5 − C4 = −0.182 ± 0.054 (t = −3.4),
the same magnitude as the L1 pair's on-path −0.171 ± 0.042. Existing arms reproduced to the
fourth digit, which validates the harness.

---

## 4. The mechanism, measured directly

Edge density in **input-silent regions**, relative to the real image. A ratio near 1.0 means
the model fills terrain it has no information about to exactly the busyness of reality — which
is the operational definition of invention.

| arm | ratio |
|---|---|
| pretrained | 1.02 |
| C1 (GAN + L1) | 1.10 |
| C4 (GAN + LPIPS) | 1.12 |
| **C5 (LPIPS only)** | **1.16** — highest of all five arms |
| **C2 (L1 only)** | **0.28** |

**With no discriminator anywhere, LPIPS alone invents more than the adversarial arms do.**
This was the registered primary prediction for C5 and it is the single result that widens the
claim from "adversarial" to "plausibility pressure".

### The point-count argument — include this, it closes a reviewer objection

A reviewer can object: *"L1-only simply produces fewer features; fewer-but-better is a trivial
trade-off, not a mechanism."*

C5 refutes it **on the Ankara-130 primary panel, and the panel must be named in the sentence**:
C5 produces more surviving matches than C2 (median 88 vs 72) and still scores worse
(1.478 vs 1.376 px). The harm is therefore not about feature count. It is about features that
have no grounding in the input.

**Do not extend this to the production panel; it reverses there.** On the 20-chip production
subset C2 has both more points *and* the better score (235 pts / 0.593 px against C5's
224 / 0.663), which is exactly the configuration the objection describes. The refutation rests
on Ankara-130 alone. A reviewer reading both tables will find the reversal, and finding it
unremarked is worse than the reversal itself.

There is also a mechanistic distinction worth stating: the two pressures invent *differently*.
The discriminator produces texture that is largely **unmatchable** (high edge ratio, low point
count). LPIPS produces structure that is **matchable but misplaced** (high edge ratio, highest
point count). Both hurt, by different routes.

---

## 5. Alternative explanations ruled out

Each was registered before it was tested. Report them; they are what makes the claim survive
review.

**Blur, not restraint.** Low-pass filtering the adversarial arm's output to match the L1-only
arm's spectral profile (fitted σ = 0.45) recovers only −6.1% (Europe) / +1.7% (Cappadocia) of
the gain; registered support band was ≤ 25%. The spectral fit was itself informative: a
persistent low-frequency excess that no blur reproduces — the arms differ in content, not
sharpness.

**Corrected georeferencing in the fine-tuning pairs.** Decomposition of the European gain:
~86% is scatter reduction, and the systematic component slightly worsened. Candidate refuted.

**Cold-started discriminator damage.** Checkpoint sweep at epochs 1, 2, 5, 10, 20. C1 at epoch 1
is *already better* than pretrained (−0.399 ± 0.064, 6.3 SE) — the wrong sign for startup
damage — and the C1−C2 deficit exists from epoch 1 and *grows* with continued adversarial
training (+0.55 → +0.70). Dose-response, not transient.
*Honesty note the paper must carry:* the registered reading bands did not anticipate this
curve shape. The conclusion is read off the curve, post hoc, its strength resting on the sign
and the monotone growth rather than on a pre-committed rule.

**Optimising the evaluation metric.** The result holds under matchers from different families:
ORB (Δ(C2−C1) = −0.613 ± 0.135, ~4.5 SE, computed on the **29-chip intersection** where both
arms matched, *not* on the 53/34 matched counts quoted beside it), AKAZE, and mutual information
(−1.260 ± 0.261, a **lower bound**: the ±8 px search grid censors 15.8% of measurements at the
bound and does so more heavily for the worse arms, so the true margin is at least this large;
corrections-log entry 21).

**The mediation leg was withdrawn by the B2/B3 audit (entry 20). Do not quote it in its old
form.** The registered test reported the conditional gap as the OLS fitted value at the
covariate means, which is algebraically identical to the raw mean for any covariates whatsoever.
"Mediates 0%" could not have returned any other number, and the test as run cannot detect
mediation of any size. The mediation-capable statistic from the same fit, the gap at
Δsimilarity = 0, gives **ank130 −0.395 ± 0.124 (43.8% of the magnitude lost, still
significant)** and **eu150 −0.106 ± 0.088 (75.6% lost, significance lost, t = −1.20)**.
Gradient similarity carries the attenuation; photometric similarity is inert.

The registered "fully mediated" threshold (≥ 80% of magnitude **and** loss of significance,
jointly) is not met on either set, so "matcher-independent" is not withdrawn. Two things travel
with that sentence. First, the threshold is pre-registered but **the statistic it is applied to
was chosen during the audit**, so this is a pre-committed rule applied to a post-hoc quantity,
and the paper says so. Second, **eu150 sits 4.4 points under the bar with significance already
lost** — it must not be presented as a clean pass.

**How to read the attenuation, offered as interpretation and labelled as such.** Conditioning
on gradient similarity removes much of the gap, but gradient similarity to the real image is
plausibly *on the causal path* from restraint to positional accuracy rather than a confound
beside it: a reference whose gradients resemble reality is what an accurate reference is.
Conditioning on a mediator removes part of the effect being estimated. The attenuation therefore
does not separate the "trained-on-the-metric" explanation from the mechanism we propose.
**The evidence that does separate them is the cross-family replication** — descriptor and
statistical matchers, trained on nothing resembling pixel L1, still rank C2 first — and this
alternative-explanation row should rest on that leg alone.

**Matcher independence, quantified.** 6,510 scored comparisons across three matcher families,
two band conversions and an urban subset: ~~**the arm ordering is preserved in 48 of 49 cells**
(the exception, EU urban under phase correlation at −0.03 ± 0.21, was pre-classified as noise).~~
**CORRECTED 2026-08-26** — the count is not reproducible and there are **two** exceptions, not
one ([packageA-audit.md](packageA-audit.md) §C-2/§C-3). Read instead: **the arm ordering is
preserved in every condition cell except two, both at EU-150 urban under phase correlation,
one per band conversion (C1 ahead by 0.0246 ± 0.2080 and 0.0092 ± 0.2168), both far below the
registered 2 SE threshold and pre-classified as noise.**
NCC *grows* C2's margin over C1 rather than shrinking it (Ankara −0.70 → −1.01; Europe −0.47 →
−1.15) — the opposite of the registered prediction, which had expected blur to be punished.

Mechanistic reading for that surprise, worth stating: a blurred template gives a *broad*
correlation peak; invented structure gives a *sharp peak in the wrong place*. A broad peak in
the right place localises better than a sharp peak in the wrong one. That is why the result
does not depend on the matcher family.

---

## 6. Supporting results the paper can draw on

**Geometric error found in the published pipeline.** Input rasters of 257×257 at 10 m are
resampled to 256×256 with the geographic transform copied unchanged, giving a true GSD of
10.0390625 m against a declared 10.0 — an error of exactly 1/256 (+0.39%), up to 14.1 m at the
chip corner. Confirmed four independent ways: code-path inspection, reconstruction to ≤ 1 DN,
phase correlation, and a statistical test against KARIOS at 9.9σ. Corrected; the correction is
mandatory in our production path.

**Determinants of accuracy.** Input information density dominates (ρ = −0.61 controlled;
an early uncontrolled local metric gave −0.79 and that number is retracted). Shown specific to
generated imagery via a ceiling control (real-vs-shifted-real gives ρ ≈ +0.04…+0.09, null).

**Geographic transfer.** Against a density-matched European baseline the Turkish penalty is
+0.226 px, and it dissolves with input density: +0.375 px mid-stratum, +0.038 px in the densest.
Fine-tuning transfers to an unseen tile *and* date: transfer ratio R = 0.945, bootstrap 95% CI
[0.730, 1.184], P(R ≥ 0.7) = 0.987 against a pre-registered threshold of 0.70.

**Landform-vocabulary hypothesis: not supported**, on a powered test. DEM-derived (Copernicus
GLO-30 slope-std) ruggedness labels committed before scoring; badlands − flat = −0.013 ± 0.141,
n = 33/65. An earlier composition-based rule selected 5 of 130 chips and was discarded as a
measurement failure, not scored as a result.

**Operational figure.** On urban chips in the panchromatic-equivalent single band — the
condition an operational georeferencing pipeline would use — C2 = **0.593 ± 0.041 px**
(production path, K = 8, n = 20, BT.601), better than pretrained on 20/20 chips.

The RGB counterpart, unreported until the B2 audit (entry 19) and now published, runs the same
way and every margin is *wider*: C2 = **0.6030 ± 0.0376 px** against pretrained 1.6314 /
C1 0.8610 / C3 0.6372; paired C2 − pretrained −1.0284 ± 0.1876 (20/20), C2 − C1
−0.2580 ± 0.0901 (18/20). The registered restatement check passes on RGB too (0.012 px).

---

## 7. The comparison against real imagery — the negative result

This may belong in the paper, or in a second paper, or as a limitations section. It is
measured, registered, and unfavourable to the method.

**Design.** Known-displacement recovery: apply a known geometric distortion to a real target
scene, then ask each candidate reference to register it. Ground truth is exact by construction.
This design also legitimises sources whose own georeferencing is unverified — their error shows
up as recovery error, which is the quantity being measured.

**Clean site (Cappadocia; the alternative site was demoted after 14 of 1,434 training chips
were found to overlap it — checked before any number existed).**

| reference | 1 px | 2 px | 5 px | KLT points |
|---|---|---|---|---|
| real Sentinel-2, different date | 0.033 | 0.003 | 0.243 | 1524 |
| EOX cloudless mosaic | 0.017 | 0.033 | 0.030 | 1164 |
| ESRI basemap | 0.034 | 0.028 | 0.131 | 1738 |
| **GenCP C2** | **0.541** | **1.011** | **3.967** | **388** |

**Critical nuance — do not quote the first number alone.** At a 0.46 m target, which is the
configuration an operational pipeline actually runs (it upsamples the 10 m reference to the
target's resolution), the ordering holds but the gap collapses: EOX 2.06 m < real S2 2.32 m <
GenCP 2.38 m — roughly 15%, not sixteenfold, and all candidates are limited by the resolution
gap rather than by which reference was chosen. Quoting only the 10 m-target result overstates
the case against the method; quoting only the high-resolution result understates it.

**Availability, tested and closed.** 24 stratified extents (12/12 coastal/interior,
12/12 urban/rural, all seven regions; list committed before sampling): 0/24 lacked a usable
Sentinel-2 scene within 365 days, 0/24 lacked one within 90 days, EOX cloudless covered 24/24,
median 2 days since the last cloud-free scene (max 17). Registered in advance that this outcome
would collapse the availability argument. It did.

**Currency, tested and closed.** High-change site (Istanbul 35TPF), same-season pair five years
apart: EOX 2025 0.033 px, real Sentinel-2 from 2021 0.057 px, GenCP from today's OSM 0.120 px.
The registered interaction — whether the synthetic-versus-real gap depends on how much the tile
changed — is null under both change definitions (+0.008 ± 0.031 raw; −0.015 ± 0.031 with the
vegetation control; bar was −0.30). A five-year-old image beats current-OSM synthetic even in
the tiles that changed most. Registered caveat travels with it: **OSM's own lag is an equally
consistent explanation and was not separated** — that would need edit-history analysis.
The seasonal control earned its place: a third of apparent "change" was phenology
(0.230 → 0.154 once vegetation was excluded).

**One property survives well:** GenCP's own georeferencing offset (0.157 px) is *better* than
real Sentinel-2 (0.262) and EOX (0.329). The geometric work is sound; what the product lacks is
matchable content.

**Honest framing for the paper:** at 10 m the constraint that motivates GenCP — copyright-
restricted reference imagery — does not exist, because Sentinel-2 and EOX are free. The
approach's premise should be tested where the constraint actually binds, at VHR.

---

## 8. NUMBER HYGIENE — read before writing any table

This project has repeatedly caught itself quoting numbers measured under different conditions
side by side. Do not reintroduce that.

**All five arms in the 2×2 table must come from the same labelled run.** The C1 and C2 medians
in §3 (1.794 and 0.974) are *not* the same draw as the 1.869 and 0.929 reported in earlier
documents. Mixing them produces a table that is internally inconsistent, and it is the first
thing a careful reader checks.

**Citation rule, binding (corrections-log entry 25).** The **original phase-c C1/C2 numbers are
never quoted** — not 1.869, not 0.929, not the per-stratum column, not the paired
−0.530 / −1.167 / −0.638. **All five arms come from the C45 one-pass recompute**
(`C45_per_chip.csv`), which is the only version of those numbers with a surviving per-chip
layer. The reason is not preference but checkability: the 2026-08-19/20 phase-C scoring run
left no per-chip artifact, so every number in [phase-c-results.md](phase-c-results.md)'s C1 and
C2 columns is unverifiable, while every number in the C45 panel was recomputed from raw
cell-by-cell in [phase-c-audit.md](phase-c-audit.md) §B.1. Where the older figure must be
mentioned at all — the registration's Gate-1 target — cite it *as* the registered target and
put the reproducible same-draw value beside it, exactly as
[phase-c-lpips-results.md](phase-c-lpips-results.md) already does.

**The same applies to the edge-ratio numbers.** An earlier measurement gave pretrained 1.016 /
C1 1.023 / C2 0.218; the C4/C5 package gives C1 1.10 / C4 1.12 / C5 1.16 / C2 0.28. These are
different runs. Pick one set for the paper, state which, and do not interleave.

**Every reported number states which inference path it was measured on.** Test-time dropout is
active in the historical path — this is pix2pix's own design (the paper supplies noise "in the
form of dropout, applied at both training and test time" rather than a z vector), not a defect.
Runs are labelled STOCH or deterministic; a deterministic mode exists and was measured to be
score-neutral (largest |Δ| = 0.040 ± 0.077 px, n = 30 — which rules out shifts larger than
~0.15 px, not all shifts).

**Every reported number states its input provenance.** Three coexist: training inputs were
rendered from a pre-fix Geofabrik extract (`simple` strategy), the evaluation archive from
Overpass, and the production tool from post-fix Geofabrik (`-s smart`). The measured
common-mode effect is +0.33…+0.58 px per arm; the between-arm effect triggered a restatement of
C2's margin over pretrained from −1.167 to approximately −0.97 px on the production path.

**Every B2-derived number states its band conversion.** Two exist and both are registered:
BT.601 single-band (the operational condition) and RGB. They are not interchangeable — C2 is
0.593 ± 0.041 under BT.601 and 0.6030 ± 0.0376 under RGB, and the pretrained baseline differs
far more (1.370 vs 1.6314). Never place a BT.601 arm beside an RGB arm in one table.

**One sign convention throughout:** Δ = candidate − baseline; negative means the candidate is
better; "gain" is defined at point of use as −Δ. Repeat it in every table header.

---

## 9. Limitations the paper must state

- **The institution's own matching software was never measured.** Every number is a proxy for
  it. The value of the matcher-independence result is precisely that it bounds how much the
  proxy choice matters.
- **The discriminator is not published**, so every adversarial arm starts from a random,
  seeded discriminator. §5 shows this does not explain the result, but it is a deviation from
  the published training setup.
- **Train/serve input skew.** Training inputs under-represent forest relative to the production
  render path; measured cost ~0.6 px on forest-heavy chips. It happens to fall on a class the
  intended user masks out — fortunate, not designed.
- **`torchmetrics` 1.9.0** was used; the upstream paper evaluated with 0.11.0. LPIPS
  implementations can drift between versions.
- **Known-displacement recovery was not run for C4/C5** at the clean site; the original harness
  was not preserved and rebuilding it needs its own registration.
- **OSM's own positional accuracy was never separated** from the model's error. Part of the
  residual we attribute to the model is OSM's. The ceiling this implies is unmeasured, and it
  bounds how much further model improvement could achieve.
- **B1's conclusion is read off a curve**, post hoc; the registered bands did not cover the
  observed shape.
- **B3's harness was not preserved** (corrections-log entry 22). `B3_run.py` was deleted and B3
  wrote no configuration beside its outputs, so ORB's `nfeatures`, the `estimateAffinePartial2D`
  3 px threshold, the BFMatcher Hamming cross-check and the 64-bin MI joint histogram cannot be
  verified against any artifact; the first two are attested only by a contemporaneous
  observation log and the last two nowhere at all. B2's inference, mean/warp and KARIOS scripts
  were separately overwritten in place by the C4/C5 package on 24 August; the consequence is
  bounded only because `B2_score.py` survived untouched and every reported number was rebuilt
  from the raw KARIOS CSVs without them. The methods section states the parameters as reported
  rather than as verified.
- **The MI margin is a lower bound, not an estimate.** The registered parabola subpixel
  refinement never ran, so all MI displacements sit on the integer pixel lattice, and the ±8 px
  grid censors 15.8% of measurements at the bound (entry 21).
- **B3 part 2's covariates and part 3's per-chip ratios have no surviving artifact.** Part 2 was
  reconstructed during the audit and matched the reported means and SEs to three decimals, but a
  reconstruction is not the original; part 3's distribution at its original mask definition is
  unrecoverable.
- **The descriptor-family deltas rest on chip intersections, not on the matched counts printed
  beside them** (ORB ank130 n = 29; eu150 AKAZE n = 3). Any table quoting both must label which
  n belongs to which quantity.
- **The phase-C C1/C2 raw layer is gone, and the C4/C5 registration's comparison target sits
  inside it** (corrections-log entry 25). No per-chip artifact survives from the 2026-08-19/20
  phase-C scoring run, so the ten per-stratum values, both ALL values, all three paired deltas
  and R2's correlations are uncheckable — **including the Gate-1 target C2 − C1 =
  −0.638 ± 0.054 px, which is the figure the whole C4/C5 package was registered to replicate.**
  The consequence for the harness-validation argument is specific and must be stated that way:
  the C45 extension is **not** validated by reproducing that target — it cannot be — but by the
  four-digit agreement of the four pre-existing arms with B2's committed production figures
  (1.369802 / 0.764049 / 0.592721 / 0.610947 against 1.3698 / 0.7640 / 0.5927 / 0.6109), which
  [phase-c-audit.md](phase-c-audit.md) §B.1 verified independently, 4/4. The Aug-21 seed-42
  redraw corroborates every lost cell within measured dropout noise and changes no sign or
  verdict; corroboration by a different draw is not recomputation, and the paper must not
  present it as one. See §8's citation rule.

---

## 10. Method and materials

**Model.** pix2pix, U-Net-256 generator (54.414 M parameters), PatchGAN discriminator,
`--direction BtoA`. Fine-tuning: 20 epochs, seed 42, `--lr_policy linear` 10+10, Kaggle T4.
C4/C5 wall time **3 h 28 m and 3 h 33 m** (measured from the Kaggle logs' elapsed field,
corrected 2026-08-24 from the earlier "≈ 3h25m and 3h40m"; LPIPS roughly triples the L1 arms'
75 minutes).

**Data.** OpenStreetMap via dated Geofabrik snapshots, extracted with `osmium extract -s smart`
(the default `simple` strategy silently drops multipolygons crossing the extract boundary — a
real defect we hit). CLC+ Backbone 2021 (10 m, 11 classes) as the land-cover base layer,
identified from the data by a one-to-one legend match. Sentinel-2: Ankara T36TVK 2026-04-30
(2.04% cloud), Cappadocia 36SXJ 2026-05-27, Tuz Gölü 36SWJ 2026-04-30, Istanbul 35TPF.

**Training set.** 5,577 Turkish pairs. Evaluation: 130 Ankara chips stratified into five
quintiles by CLC+ information density, plus 568 held-out European chips from the original
corpus.

**Validation.** KARIOS, `confidence_threshold: 0.8`. Note that `mean_x`/`mean_y` in
`correl_res.txt` are the *global systematic shift*, not a per-point radial error — an earlier
comparison that conflated the two was retracted.

**Rasteriser.** Rebuilt from data (palette, edge kernel, base layer recovered by measurement,
since the upstream rasteriser is unpublished). Held-out acceptance, re-measured through the
corrected input path: +0.119 ± 0.138 px against a bound of 0.15 — PASS. The entire shift sits
on five German-zone chips (+0.61) which carry a pre-registered snapshot-drift caveat; the other
twenty are at −0.004, statistically zero. The caveat's pre-registration is verifiable by commit
timestamp.

**Licences.** OSM ODbL · Copernicus Sentinel-2 and CLC+ · GenCP weights CC-BY 4.0. No
institutional imagery was used. Note for any release: whether ODbL share-alike reaches model
weights trained on ODbL-derived renders is unsettled, which is why the fine-tuned checkpoints
are not publicly released.

---

## 11. Working practice — these apply to paper work too

Eight standing practices, each adopted after a specific failure:

1. Every validation gate states explicitly what it assumes is identical on both sides — data
   source, render path, code path, determinism. Three separate gates were found resting on
   unstated assumptions before this rule existed.
2. Every reported number states which inference path it was measured on.
3. One sign convention, repeated in every table header.
4. Registrations — predictions, reading bands, falsification criteria — committed before the
   numbers they judge; cite the commit hash. Commit ordering is proof; "I registered it first"
   is a claim.
5. A failed gate is reported, never adjusted to pass. A *mis-specified* gate may be
   re-registered, with the reasoning written down and the original preserved as failed.
6. Long runs checkpoint as they go.
7. A counted liveness signal on every long step; absence of error is not presence of progress.
8. At the end of every work package, the open-items register is read from the top and each item
   is closed or explicitly deferred with a written reason.

There is also a corrections log — 18 entries at the time of writing — each recording a claim,
what was actually true, how the discrepancy was caught, and what would have caught it sooner.
Several of the paper's strongest results exist because that log forced a re-examination.

---

## 12. What the paper still needs

- ~~A decision on scope.~~ **Decided 24 August: the letter is the loss-function paper.** The
  2×2 factorial is the spine; E1/E2 appear as two sentences of scope, not as results; T1, the
  contamination pair and E3 go to the second paper. Note that `paper-roadmap.md`'s three-leg
  structure was committed 23 August 20:33, roughly six hours *before* the C4/C5 results existed,
  and does not mention the factorial at all — **the roadmap needs amending to match, and the two
  documents must not be left in disagreement.**
- Figures. Candidates that already exist: the three-panel input/generated/real comparison, the
  per-stratum arm chart, the four-site paired-gain chart with error bars, the chip panels for
  Cappadocia and Tuz Gölü. The single most explanatory panel is `36SXJ_6_20` — empty input,
  high-contrast reality, pretrained invents a parcel mosaic, L1-only declines to invent, both
  score the same. It shows the ceiling: information absent from the input cannot be recovered.
- ~~Related-work positioning.~~ **First full pass done 24 August: `related-work.md`.** No
  pre-emption of the core claim was found; three papers are now must-cites (§16); the blur
  mechanism has precedent in adjacent fields; the remaining leg is the Scopus/WoS query.
- A decision on whether the known-displacement recovery for C4/C5 is worth rebuilding the
  harness for, so the new arms can enter the main comparison table.
- Confirmation of authorship and institutional approval before anything is submitted.

---

## 13. Where things live

```
tubitak/docs/     registrations, results documents scored against pre-committed text,
                  corrections log, standing practices, open-items register
tubitak/scripts/  analysis tools, including c45_eval (the C4/C5 harness, committed —
                  the earlier failure to preserve a harness cost us twice)
tubitak/outputs/  the ODTÜ reference package with its recipient README
tool_runs/C45/    per-chip artifacts for the C4/C5 arms
```

Key documents: `phase-c-lpips-registration.md`, `phase-c-lpips-results.md`,
`phase-c-results.md`, `packageA-results.md`, `positioning-results.md`,
`headline-results.md`, `corrections-log.md`, `standing-practices.md`, `open-items.md`.

Evidence backup: private Kaggle dataset `vedatyildirim/gencp-evidence-backup` — 4,395 files,
including the 130 Ankara evaluation inputs that cannot be regenerated (they predate the
Geofabrik switch and were rendered from a live API with no dated archive).

---

## 14. Venue, timeline, and the speed constraint

The paper is time-critical. Treat speed as a first-class constraint, not a preference. Do not
propose paths that require waiting on anyone.

| Date | Item |
|---|---|
| 5 October 2026 | Full draft to the co-author |
| 15 October 2026 | Comments returned |
| End of October 2026 | arXiv preprint, then IEEE GRSL submission |
| 11 January 2027 | IGARSS 2027 deadline (notification 12 March; second slice only) |

**Venue decision, already made:**

- **arXiv first, always.** A citable identifier within days is the deliverable that matters on
  this timeline; the journal decision is secondary.
- **IEEE GRSL is the target** — 5-page limit, ~30-day average handling, scope explicitly
  "short papers addressing new ideas and formative concepts". Verify GRSL's current preprint
  and supplementary-material policy before submitting.
- **IGARSS 2027** for a second slice if one exists.
- **ISPRS Journal** for the expanded second paper (operational-resolution protocol, E3, the
  contamination apparatus).
- **Not MDPI Remote Sensing.** GRSL is comparably fast and better regarded; MDPI's only
  advantage over it is void.

**Work items already cut for speed** (do not reinstate without asking): the repo-wide
registration audit beyond B2/B3, the T1 ORB+RANSAC half, the E1 paginated re-query, E3
bootstrap CIs, and C1 at 0.5 m.

---

## 15. Authorship, notification, approvals

**Co-author:** Dr. Mustafa Teke, senior researcher, TÜBİTAK UZAY remote sensing group. PhD,
indexed publication record in remote sensing and satellite image processing. Author order:
student first, Teke last (senior position). A one-page proposal covering the extension, the
publication intent, institutional approval, and the author-list question has been sent to him;
**ask before assuming its outcome.**

The author list is his to decide. Others at the institute may have a claim. **Do not finalise
it unilaterally.**

**Institutional approval** for publishing under the TÜBİTAK UZAY affiliation is required and
runs in parallel. It is not a blocker to drafting.

**Notification of the upstream authors, reduced to its minimum:** one paragraph to the
corresponding author at submission time. No reply expected, no follow-up, no approval sought,
nothing held pending. Do not draft, propose, or schedule anything larger than that. The anchor
for a defect report is Figures 22 and 25 (see §19), and the 3.9% qualifier goes in its first
paragraph.

---

## 16. Prior art already established — do not redo this from scratch

**Must be cited.** Its absence would be the first reviewer complaint:

- **Blau & Michaeli, *The Perception-Distortion Tradeoff*, CVPR 2018** (arXiv 1711.06077).
  Proves perceptual quality and distortion are formally at odds. **Our result is best
  positioned as an empirical instance of it in a geometric-task setting.** Two hazards. The
  theorem is Theorem 1 in the CVPR proceedings and Theorem 3 in the arXiv journal-length
  version, so cite the proceedings and do not mix numbering. And Blau and Michaeli sell GANs as
  the *solution* ("a principled way to approach the perception-distortion bound"), so
  **position the result as identifying the consumer, not as contradicting the theory**: a
  matcher lives on the distortion axis, so for it the perceptual end of the bound is the wrong
  end. ~~What the factorial adds and the theory lacks is *substitutability between sources of
  plausibility pressure*, which is what the interaction term measures.~~
  **SUPERSEDED 2026-08-26** — struck, not deleted. The interaction reading failed at 5/6
  across six seeds and the claim is withdrawn ([seed-block-results.md](seed-block-results.md)
  §4), so the factorial may no longer be positioned as adding *substitutability* to the
  theory. **What it does add, and what this bullet should now say:** the factorial identifies
  a downstream consumer for which the perceptual end of the bound is the wrong end, and
  establishes each pressure separately. The comparison to Blau–Michaeli stands on that and
  not on a measured substitutability.
- **Liu, Zhang, Xiong, *On the Classification-Distortion-Perception Tradeoff*, NeurIPS 2019**
  (arXiv 1904.08816). The tradeoff already reaching a downstream task. Not citing it is a
  larger risk than citing it. The distinguishing sentence: their task is semantic classification
  with an error *rate*, where a hallucinated texture that stays in-class costs nothing; ours is
  geometric with a continuous positional outcome, where an invented edge is a confident,
  well-localised observation of something that does not exist.
- **Arar et al., *Unsupervised Multi-Modal Image Registration via Geometry Preserving
  Image-to-Image Translation*, CVPR 2020.** The most dangerous neighbour: the only known loss
  ablation scored against a registration metric, and its sign is opposite to ours (the
  combination wins). The distinction is structural and must be written explicitly — there,
  translation and registration are trained *jointly*, so the adversarial term does
  representation-alignment work inside the training loop; here the generated image is a frozen
  deliverable and the matcher is exogenous.
- **Chen, Ohayon et al., *Looks Too Good To Be True*, NeurIPS 2024** (arXiv 2405.16475). Ties
  hallucination to the pursuit of perceptual quality information-theoretically. "An invented
  edge is a false control point" is its geometric instantiation; citing it turns our mechanism
  from asserted into predicted.

**Near but distinct:**

- *Hallucination Score: Towards Mitigating Hallucinations in Generative Image Super-Resolution*
  (arXiv 2507.14367). Measures hallucination via an MLLM, perceptually. Ours is
  input-conditioned, cheap, reproducible, and tied to a downstream geometric task. The contrast
  favours us and deserves a paragraph.
- SAR-to-optical translation literature: hallucination concerns exist there, never measured via
  matchability.
- Structure-preservation and semantics-distortion work in image translation (Spatially-
  Correlative Loss; CVPR 2022 semantics distortion). Motivated by perceptual consistency, not
  geometric matching.

**The gap**, confirmed against the complete 54-entry reference list obtained from the Crossref
deposit: the upstream paper cites LPIPS (Zhang et al., CVPR 2018), MS-SSIM (Wang, Simoncelli,
Bovik, 2003) and PSNR-versus-SSIM comparisons (Hore & Ziou, ICPR 2010; Setiadi, MTA 2021) —
the original SSIM paper is *not* cited — but no perception-distortion literature and no
GAN-hallucination literature; the word "hallucination" never appears and the only artifact
discussion is "blurring artifacts". We can state that we fill a gap the original left open.

**One qualification, or the claim is refutable by anyone holding the reference list.** The
bibliography contains exactly one adversarial-attack paper, ref [47] Fan, Khairuddin, Liu,
Hasikin, *Perceptual Carlini-Wagner Attack*, IEEE Access 2025, cited only in support of the
statement that LPIPS reflects human perception. Write: **"no
adversarial-robustness-for-geometric-applications literature; the single adversarial-attack
reference is cited only in support of LPIPS as a perceptual metric."** The narrow sentence is
true; the blanket one is not.

**Citation tracking is closed except one index.** Crossref, Semantic Scholar and OpenAlex all
report 0 citations as of 2026-08-24 (published 15 July 2026). Google Scholar is blocked to
automated access and MDPI's own "Cited By" panel could not be retrieved; one manual look is the
only remaining check.

**Full positioning pass, with citations and DOIs:** `tubitak/docs/related-work.md`. It also supplies the
remote-sensing citations a GRSL reviewer expects, the precedent for the blur mechanism
(Pan 2013 on bias reduction by Gaussian pre-filtering; Berg & Malik 2001 on geometric blur),
the Cramér-Rao caveat that must be pre-empted in one sentence, and the 2019 SAR-to-optical
statement that no suitable metric exists — the gap our edge-ratio measurement fills.

**Still required before submission:** a structured Scopus/Web of Science query (the one leg not
yet run; it needs institutional access) and the manual Google Scholar check. Until those are
done, write novelty claims as **"to our knowledge"**, never "first".

---

## 17. How E1/E2 relate to the published paper's stated motivation

The upstream paper names three motivations explicitly: sparse global coverage of ground control
points, the need for periodic resurveying as land cover changes, and licensing policies
limiting globally accessible GCP datasets.

**E1 and E2 test the first two.** This makes them a direct empirical test of the published
premise, not scope-setting context, and they deserve their own section rather than the two
sentences an earlier plan allotted them.

**The distinction that must be written explicitly**, or the objection "you answered a different
question" lands: their premise is framed against *surveyed GCP databases*. We tested whether it
survives when *free satellite imagery* is admitted as reference data. At 10 m in Turkey it does
not. Say it in those words.

---

## 18. E3 — exploratory, and the numbers in §7 come from it

The 0.46 m figures quoted in §7 (EOX 2.06 m < real S2 2.32 m < GenCP 2.38 m) are E3's. They
carry constraints that must travel with them:

- **The reported pass was produced by an unregistered configuration.** Amendment E3-a
  registered winsize 64 with 5/10/20 m displacements and "no other parameter changes"; that
  pass recovered nothing. The reported table came from a *third* configuration (winsize 15,
  displacements 0.5/1/2/3/5 m) that was never registered. Amendment E3-b is a retrospective
  disclosure, explicitly labelled as not a preregistration. Full timeline in corrections-log
  entry 16.
- **E3-a's characterisation of pass 1 was false.** It claimed nothing recovered and no ranking
  existed, "registered before any ranking was read". The sub-window magnitudes had recovered
  and the ordering was on disk 69 seconds before that commit.
- **E3 is labelled exploratory** — a consistency check on direction, not a confirmatory
  measurement. It may be quoted only with that label.
- **No dispersion is reported.** Means only. Point counts are asymmetric (GenCP C2 71, EOX 210,
  real S2 320), so C2's standard error is roughly twice EOX's. Until bootstrap CIs exist, the
  0.32 m spread between candidates cannot be separated from noise. The interpretation rule was
  registered in advance: **if the CIs overlap, the verdict is "the 0.5 m setup does not separate
  the arms"**, and that scope statement, not a ranking, is what gets reported.
- The basemap was excluded as a candidate because it was the target — a coverage gap by
  construction, recorded as such.

**E3 does not appear in the letter.** It may appear in the arXiv long version's discussion,
with its label attached, never in a results table. Verified: no leg of the argument depends
on it.

---

## 19. Published text versus published data, and what the scale error actually weighs

**The scale error's real weight — write this qualifier or the claim overreaches.** The 1/256
error is present in the published paper's means: northing +5.0 to +6.9 m, easting −1.6 to
−3.4 m across four HR measurements, signs and magnitude both consistent with the prediction.
But predicted std is 2.89 m against an observed sigma of 14.5–17.3 m: **the scale error explains
roughly 3.9% of the reported variance.** It does not explain their headline errors and does not
invalidate their conclusions. The paper's own explanation for the dispersion ("RMSE is mainly
driven by residual dispersion") stands. Report the systematic component as a hypothesis
consistent with the means, and nothing more.

**Where the 257 comes from — an earlier framing of this was wrong.** It is neither purely a
training-data issue nor purely an inference bug. The published text says 256×256 patches (and
Table 5 agrees; "257" never appears). The published *dataset* is 257 pixels: every GenCP_HR_DB
raster is 514×257, i.e. side-by-side 257×257 pairs. The upstream `gencp_georeferencing.py`
(telespazio-tim, commit `e218f29`) takes the size from the generated image and the transform
from the reference, so the mismatch is implicit in code and materialises at inference.
**Describe it as a text-versus-data inconsistency, not as a code bug.**

**The cleanest citable evidence:** Figures 22 and 25 print `Pixel size : 10.0 m` on KARIOS
panels whose monitored file is the generated product (`31TFJ_gen_TCI.tif`). This is a
documented contradiction and should be the anchor of any defect report.

**The pattern is broader than one number**, and collecting it is a real contribution for anyone
reusing the dataset:

| Published text | Published artifact |
|---|---|
| 256×256 patches | rasters are 514×257 |
| 23 sites, 5,500 patches | 77 tiles, 5,708 pairs (plus 9 leakage chips) |
| Figures 22/25: `Pixel size : 10.0 m` | true GSD 10.0390625 m |

**No commit is pinned by the publication** — only the repository URL and an access date, and
the Zenodo record points at a differently named repository. State which commit we audited
(`e218f29`).

**Numbers from the upstream paper available for citation:** 31TFJ RMSE 21.93/21.29 m, CE90
35.70/35.23; 30TXT RMSE ~24.4 m, CE90 39.69/39.46. Their own characterisation is quotable:
*"coarse geometric consistency rather than precise GCP-level control"*.

**Cite these to their figures, never to a table.** An independent full-text search of the
preprint found no CE90, no CE95 and no keypoint counts in any table or in the body text, while
`published-paper-audit.md` §§6–7 records all of them. The reconciliation is that they live in
the KARIOS figure panels, consistent with this section's own statement that Figures 22 and 25
are the anchor. Verify the figure numbers against the **published** version rather than the
preprint before quoting. Quoting them as tabulated is an error a reviewer with the PDF open
catches at once.

**Candidate fourth row for the table above, to be checked against the published version.** The
preprint's Table 8 prints independent-site RMSE of 4.4 and 4.3 m against a standard deviation of
23.7 and 23.2 m in the same column, which is arithmetically impossible; `published-paper-audit.md`
reads it as ~24.4 m, i.e. a dropped leading digit. If the published version carries the same
typo it is the cleanest entry in the list, because it refutes itself.

**The objective is confirmed from three independent sources**, which closes the entry-18 loop
from the other side: the paper's Table 5 (HR = adversarial + λ·LPIPS, λ = 100, BCE
discriminator), the released code (`gan_mode` default `vanilla`, `lambda_L1` default 100, LPIPS
with a VGG backbone), and our own run logs. **And the LPIPS substitution is asserted, not
measured** — the paper states only that L1 "was replaced by" LPIPS and presents no comparative
evidence, no L1-versus-LPIPS numbers and no ablation of the adversarial term. Our factorial
supplies the ablation the upstream work did not run, and contradicts an unevidenced design
choice rather than a published measurement. Say it in those words: verifiable, non-inflammatory.

**The Zenodo deposit predates the article.** Record 15044428 is dated 6 December 2024 and is the
VH-RODA-era artifact; neither the record nor the paper states whether the deposited weights
correspond to the models reported in Tables 5–12. Our pretrained baseline is that deposit, so
this belongs in the methods section as one sentence.

**Their keypoint counts support our argument** — an earlier reading that they did not report
them was wrong. They report 2,912/2,798 at a training site dropping to 957/978 at an
independent site, and interpret it as generalising "less effectively". Our contribution is not
that they failed to count; it is that they never compared against real-imagery references and
never connected yield to the objective. **Citing their own numbers is stronger than pointing at
an absence.**

---

## 20. Contamination as an independent methodological contribution

Same tool, same matcher, same distortions; the only difference is train-on-target overlap:

| Site | GenCP recovery error |
|---|---|
| ODTÜ, 14 training chips overlap | 0.008 – 0.11 px, i.e. as good as real imagery |
| Cappadocia, clean | 0.54 – 3.97 px, **20–130× worse** |

This is a direct measurement of how far train-on-target overlap flatters a result, and few
papers in the field demonstrate it this cleanly. Letter: one paragraph and the two tables side
by side. arXiv version: its own section. It also serves as evidence that contamination was
checked *before any number existed*, which is itself a rare claim to be able to make.

**The pretrained baseline is separately clean, and this was verified.** The published
GenCP_HR_DB corpus spans 77 distinct tiles, all in UTM zones 30–34; not one Turkish-belt tile.
Our evaluation tiles (36TVK, 36SXJ, 36SWJ, 35TPF) appear nowhere in it. So no overlap exists
between the pretrained baseline's training corpus and our evaluation sites. **State this; a
reviewer will ask.**

**Related geographic facts.** The HR (10 m) model was trained on 23 European mid-latitude sites
with zero Turkish data, which is what makes the geographic-penalty analysis clean, and should
be said. **The VHR (50 cm) model was trained on Ankara (14 images), so any future VHR
evaluation in Ankara is contaminated by construction** — a constraint on the second paper and
on any super-resolution work.

---

## 21. Audit status and the binding wording rule

Registration audits performed against run artifacts (three checks each: timeline, cell-by-cell
recomputation, config-versus-registration diff):

| Registration | Status |
|---|---|
| T1 | **Audited, holds.** Timeline claim true (only input rasters predate the amendment); 70/70 table cells recomputed from the raw CSV; configs match. One real deviation: the registered ORB+RANSAC secondary matcher never ran and was undisclosed until the audit (corrections-log entry 17) |
| E3 | **Audited, failed** on its central integrity claim (corrections-log entry 16; see §18) |
| B2 | **Audited 24 Aug, holds.** Timeline PASS: no computed score predates the registration commit, and the 26-minute window is fully reconstructed (three agents, B2 and B3 concurrent, 8-way parallelism inside each stage). 384/384 cells reproduce; the mean-of-8 estimator verified byte-identically against its eight draws; chip set identical to the committed urban list, no EU chip entered. One deviation: the registered **RGB half ran but was never reported** (entry 19), now published, and every margin *widens*. B2 is quotable as registered and executed in full |
| B3 | **Audited 24 Aug: part 1 holds, part 2 void as stated.** Part 1's means, SEs, matched counts, ranks and deltas all reproduce. **Entry 20 — the mediation test as run could not detect mediation of any size** (see §5); the "0% mediated" sentence is withdrawn and the corrected statistic shows substantial attenuation on both sets. **Entry 21 — the registered MI parabola subpixel refinement never ran**; the margin is a lower bound. **Entry 22 — the harness is gone**, so four registered matcher parameters cannot be verified against any artifact |
| Everything else | Not audited; cut for speed |

**Consequence for the T1 table:** every number in it is a primary-matcher (KLT/KARIOS) result.
It is quotable as such, not as the full registered protocol, until the ORB half runs or a
reasoned decision not to run it is recorded.

**Binding manuscript wording rule.** Never write:

> "All experiments were pre-registered."

Always write:

> "Experiments were pre-registered where stated; deviations from the registered protocol are
> documented in a public corrections log."

Corrections-log entries 16, 17 and 18 falsify the first sentence and evidence the second.

**Corrections-log entries that constrain the paper:** 16 (E3's registration failure), 17 (T1's
unrun ORB half), 18 (the lsgan documentation error — C1 in fact ran `gan_mode: vanilla`,
matching the published BCE discriminator; the earlier note in `phase-c-config.md` was wrong),
19 (B2's RGB half ran but went unreported — a disclosure failure, not a non-execution, and the
unreported numbers favour us), 20 (**B3's mediation test was uninformative as specified**; the
most consequential entry for the manuscript, see §5), 21 (the MI subpixel refinement never ran;
the margin is a lower bound), 22 (**the B3 harness was deleted and B2's scripts were overwritten
in place** — the entry-10 pattern recurring, and the reason four registered parameters are now
unverifiable).

**The audit base rate, which the discipline claim must be stated against:** of five registrations
audited against run artifacts, two hold in full (T1 with one disclosed deviation, B2 with one),
one holds in part (B3), one failed (E3), and B1 self-reports that its registered bands did not
cover the observed shape. That is the honest denominator, and it is a stronger thing to be able
to report than a clean sweep would be.

---

## 22. Mechanism caveat — the edge ratio does not order the errors

§4 gives the edge ratios and §3 gives the errors. Placed side by side across all five arms they
are **not monotone**, and the paper must say so before a reviewer plots it:

| arm | edge ratio | error (px) |
|---|---|---|
| C2 (L1 only) | 0.28 | 1.376 |
| C5 (LPIPS only) | **1.16 (highest)** | 1.478 |
| C4 (GAN + LPIPS) | 1.12 | 1.965 |
| C1 (GAN + L1) | 1.10 | 2.075 |
| pretrained | 1.02 | 2.563 |

C5 has the highest ratio and the *second-best* positional score; pretrained has the lowest ratio
of the unrestrained arms and the *worst* score. **Within the four inventing arms the ratio does
not order the errors at all.**

**The defensible statement:** the edge ratio separates the restrained arm from the unrestrained
ones; it does not order the errors within the unrestrained group. **Invention is a necessary
condition, not a complete explanation.** The route-difference in §4 (the discriminator produces
unmatchable texture; LPIPS produces matchable but misplaced structure) is the honest partial
account, and it should be offered as such rather than as a mechanism that predicts magnitude.

*Corrected 2026-08-24.* An earlier version of this section said pretrained was not measured in
the C4/C5 panel. It was: `phase-c-lpips-results.md` reports it in the same one-pass recompute as
the other four arms, mean **1.021**, median 1.020, q25–q75 0.94–1.12 (committed B3 value 1.016).
The five-arm edge-ratio comparison therefore comes from a single labelled run and needs no
mixed-panel footnote, which is what §8 requires; pretrained has been added to the §4 table. The
conclusion is unchanged: pretrained still has the lowest ratio of the four unrestrained arms and
the worst score.

---

## 23. One item missing from the supporting results

**The T1 C1 row belongs in the paper.** It is the only place the adversarial contrast appears
inside the known-displacement recovery protocol, and the point counts are nearly equal, which
makes it a *quality* difference rather than a *matchability* difference:

| candidate | intrinsic \|d0\| | KLT points | 1 px | 2 px | 5 px |
|---|---|---|---|---|---|
| GenCP C2 | 0.157 | 388 | 0.541 | 1.011 | 3.967 |
| GenCP C1 | 0.218 | 405 | 1.119 | 2.561 | 5.180 |

Showing this row makes the design rule's support one step from the recovery benchmark rather
than an extrapolation from a different measurement.

---

## 24. REQUIRED TEXT — the interaction disclosure

**Added 2026-08-26. This section is PROTECTED: it is a deliverable of the interaction
consequence, not an optional extra.** Per RULING 1 in
[seed-block-results.md](seed-block-results.md) §4, the consequence removes claims and does
**not** remove the disclosure that a pre-registered test was run and failed. An edit pass
that struck the interaction claims and stopped there would produce a paper that silently
drops a pre-registered failed test — the precise failure this paper accuses the upstream
published work of committing, and the reason §21's binding wording rule exists at all.

**The paragraph below must appear in the manuscript's results or limitations section.** It
may be shortened for the letter format, but it may not lose any of these five elements:
registered in advance; computed on all three registered scales; 5/6 with the same seed
breaking each; no claim made; the other block reported with its weight stated.

> **Interaction: registered, tested, not sign-stable, and therefore not claimed.** Before
> any replication data existed we registered a seed-level interaction between the two
> reconstruction terms, I = (C4 − C5) − (C1 − C2), to be read as negative in every seed and
> to survive a monotone re-scaling, with both re-scalings — a natural-log transform of the
> per-chip residual and a within-chip rank transform — specified in advance. Across the six
> confirmatory seeds the interaction was negative in five and positive in one (seed 46), and
> the same seed reversed the sign on the log and rank scales as well: 5/6 on each of the
> three registered scales. The registered reading therefore fails, and by a consequence
> committed in advance we make no interaction claim in this paper. An earlier two-seed block
> run on different hardware returned a negative interaction in both of its seeds on all three
> scales; it is reported here for completeness and carries no weight against the six-seed
> result, because the two blocks cannot be pooled and a two-seed block does not override a
> six-seed one. The seed-level means are negative on all three scales, and the log-scale and
> rank-scale confidence intervals exclude zero; these are reported, not required, and they do
> not reinstate a reading whose criterion was sign stability across seeds rather than a
> nonzero mean. The single-run estimate this project previously published, I = −0.212, falls
> outside the range spanned by the six replicates on the raw and rank scales, which is
> reported as a finding in its own right below.

### Writing rule that travels with it

**Forbidden**, here and in every document downstream: any sentence of the form *"the interval
excludes zero, so the interaction is real"*, and any sentence that functions as one however
it is phrased. The log-scale and rank-scale interaction intervals do exclude zero; the
raw-scale one does not. State plainly what that means and nothing more — the mean is
reliably negative, the sign is not stable across seeds, and the registered reading was sign
stability. **An interval is not a back door to a reading that failed.** The intervals were
registered as reported-not-required precisely so they could not act as a gate in either
direction.
