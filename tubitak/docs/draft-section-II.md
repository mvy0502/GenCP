# DRAFT — Section II, Materials and methods

**Status: first manuscript text. Draft 1, 2026-08-26.** Structure and word allocation follow
the letter skeleton's Section II spec; the deltas against that spec come from work completed
after the skeleton was written. **Word count and overrun are reported at the foot of this
file — the budget is not silently exceeded.**

Manuscript prose begins below the rule. Internal document names, repository paths and
registration codenames do not appear in it.

---

## II. MATERIALS AND METHODS

**Sign convention, used throughout this letter: Δ = candidate − baseline, so a negative Δ
means the candidate is better.** Residuals are positional errors in pixels at 10 m ground
sampling; lower is better.

### A. Model and fine-tuning

We fine-tune a published conditional GAN that renders a Sentinel-2-like image from
OpenStreetMap vectors and land-cover raster: a U-Net-256 generator (54.414 M parameters) with
a PatchGAN discriminator, trained image-to-image in the direction from map to image. Training
used 5,577 Turkish image pairs, 20 epochs, one seed per arm on a single T4 GPU, under the
generator's own linear schedule — ten epochs at the base learning rate followed by ten
decaying to zero.

The arms carrying an adversarial term also carry a two-epoch warm-up at 2×10⁻⁵ before eighteen
main epochs at 10⁻⁴; the arms without one run twenty main epochs at 10⁻⁴. **Integrated over
training this gives the adversarial arms 13.40 against 15.00 in units of 10⁻⁴ epochs, a
10.67% deficit, borne by the arms that score worse.** The warm-up exists because joint
training from a randomly initialised discriminator at full learning rate is unstable, so the
asymmetry is a property of the design rather than an accident of it.

**Its consequence is measured rather than assumed negligible.** Giving a non-adversarial arm
that exact schedule moves its positional residual by +0.007 ± 0.034 px, roughly 1% of the
0.647 px gap the schedule would have to explain (one seed, chip-level bound). **The
LPIPS-only versus L1-only contrast is immune to it by construction**, both arms being
un-warmed twenty-epoch arms at identical integrated learning rate.

### B. The design

A 2×2 factorial crosses an adversarial term with the reconstruction loss: adversarial + L1,
L1 alone, adversarial + LPIPS, and LPIPS alone. **Held fixed across all four cells:** training
data, seed, initialisation, evaluation chips, matcher, and matcher configuration. **The
learning-rate schedule is an explicit exception to that list, quantified in II-A, not an
omission from it.**

The published pretrained weights already occupy the adversarial-plus-LPIPS cell, trained on
European data rather than fine-tuned on ours; they are reported as a fifth arm rather than
presented as an empty cell. Our adversarial-plus-LPIPS and LPIPS-only arms reproduce **the
repository's executable definition** of the published objective — adversarial + λ·LPIPS with
λ = 100 and a binary cross-entropy discriminator — since the published text does not name the
LPIPS backbone and the released code uses VGG.

### C. Disclosure

The discriminator is not published; only the generator is deposited. Every arm with an
adversarial term therefore begins from a randomly initialised, seeded discriminator, recorded
in a provenance file per run. Section IV shows this is not what causes the adversarial arms to
lose, but it is a deviation from the published training setup and we state it as one.

### D. Evaluation

Residuals are KLT feature matches against real Sentinel-2, at a confidence threshold of 0.8,
over 130 Ankara chips stratified into five quintiles by land-cover information density. Every
number states its inference path and input provenance. Test-time dropout is active — it is the
generator's own design, not a defect — and a deterministic mode was measured to be
score-neutral within ±0.15 px.

**Each arm's chip residual is a median over the matches that arm itself produced, and the
arms do not produce equally many:** median surviving points are 51 for the pretrained
generator, 59 for adversarial + L1, 62 for adversarial + LPIPS, 72 for L1 alone and 88 for
LPIPS alone. **This is selection on a post-treatment variable and we name it as such.**

We test it by equalising counts. On each chip every arm is truncated to the best *K* of its
own matches, ranked by match score, where *K* is the smallest count any arm achieved on that
chip; the LPIPS-only arm surrenders 38% of its points and the adversarial-plus-LPIPS arm 7%.
A minimum-match-count sweep over all four arms jointly is reported alongside it. **Both are
reported in Section III.**

**Point-level common support is not constructible here, and we report that rather than
approximating it.** KLT keypoints are detected independently per arm on that arm's own
generated image, so the arms share no point identity: at a two-pixel tolerance, 69 of 130
chips have no common points at all, and a tolerance wide enough to yield a usable set would
exceed the 1.4–2.0 px residuals under test and absorb the signal. Equal-count truncation is
therefore the only available substitute. It is ranked by match score and never by residual,
which would be circular; **match score is itself post-treatment, so this removes the count
asymmetry rather than all conditioning, and no result here is unbiased.**

### E. The invention measurement

Input-silent pixels are those with canonical Sobel response ≤ 20 on the input render. For each
chip we take the edge fraction (Sobel > 20) of an arm's output over the real chip's edge
fraction on those same pixels, and report the per-chip ratio per arm. **The denominator is the
input, not the ground truth, deliberately:** it separates *invented where nothing was known*
from *wrong where something was known* — a distinction existing hallucination metrics do not
draw.

### F. Geometry

Our path corrects a ground-sampling-distance inconsistency in the published resampling step;
the correction is applied to every chip scored here, so our geometry is not identical to the
published pipeline's. The finding itself, its magnitude and its bounded contribution to the
published variance are reported separately in the extended version.

### G. Registration statement

**Experiments were pre-registered where stated; deviations from the registered protocol are
documented in a public corrections log.**

---

## Word count and budget

Counted on the manuscript prose only — everything below the first rule and above the second,
excluding the subsection headings.

| block | spec | draft | Δ |
|---|---|---|---|
| sign convention *(new line, not in spec)* | — | 34 | +34 |
| A. Model and fine-tuning | 120 | 223 | **+103** |
| B. The design | 120 | 132 | +12 |
| C. Disclosure | 60 | 60 | 0 |
| D. Evaluation | 150 | 332 | **+182** |
| E. The invention measurement | 120 | 78 | −42 |
| F. Geometric error | 100 | 109 | +9 |
| G. Registration statement | 40 | 17 | −23 |
| **total** | **710** *(spec sums to 710 of a 750 budget)* | **985** | **+275** |

Counts produced by script over the prose block, not estimated by eye.

**THE DRAFT OVERRUNS BY 235 WORDS AGAINST THE 750 BUDGET** (985 against 750; +275 against the spec's own 710). It is not trimmed to fit, because
what would have to go is the new material this draft was written to carry.

**Where the overrun is, and what it buys:**

- **Evaluation, +182.** All of it is the matched-point asymmetry and the common-support
  answer. This is the section a reviewer will attack first, because the LPIPS-only penalty is
  0.063 px and the arm that wins it keeps 22% more points than the arm it beats. **Cutting
  this returns the letter to a state where that objection has no answer in the text.**
- **Model and fine-tuning, +103.** The learning-rate asymmetry, its measured bound, and the
  immunity of the LPIPS-only contrast. Roughly 60 words of this is the disclosure itself and ~45 is the measured bound; the bound is what turns a confession into a measurement.
- **Everything else nets to −10**, so the two new blocks account for the whole overrun and slightly more than it.

**Three ways to absorb it, for your decision — I have not chosen one:**

1. **Take it from Section IV (500 → 320 → ~180).** Section IV is the only block the skeleton
   designates as degrading gracefully, and it has already given 180 words to Section III. A
   second 243 leaves it too thin for four rows plus prose; realistically two rows would move
   to the arXiv version.
2. **Take it from Section I's related work (220 of its 600).** The skeleton already calls this
   paragraph "the most compressible" and says it should be written last, when the remaining
   budget is known. Cutting it to ~120 words means naming three prior works instead of seven.
3. **Split the difference and cut within Section II**: the geometric-error block (F) could
   drop to ~60 words by moving its variance qualifier to a footnote, and the invention
   measurement (E) is already under spec. That recovers perhaps 50 of the 235 without touching
   the new material.

**My recommendation is 2 then 3.** Related work is compressible without losing a result;
Section IV's rows are results. But the trade is yours, and the two new blocks are the part I
would defend keeping whichever way it goes.

---

## Wall-clock

**Start 09:30:14 UTC, end 09:32:16 UTC, 2026-08-26. Elapsed: 2 minutes 2 seconds.**

Measured with `date -u` at both ends, not estimated. The clock covers re-reading the
Section II spec and binding sentence 1, writing the draft, scripting the per-block word
count, and correcting the budget table against the measured counts. It excludes the two
bookkeeping fixes committed immediately before it, and it excludes this commit.

**One caveat on what this number measures.** It is generation wall-clock for a first draft
written against a spec that already existed and from results already computed and committed.
**It is not the cost of producing Section II from nothing** — the registrations, the six-seed
block, the two probes and the audits are what made the section writable, and they took the
preceding day. Read it as the marginal cost of drafting once the evidence is in hand, which
is the variable that was unmeasured, and not as a schedule estimate for the remaining
sections, which differ in how much settled material they can draw on.
