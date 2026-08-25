# Registration — seed replication of the 2×2 loss factorial: is the treatment effect, or one checkpoint pair?

**Status: REGISTERED before any run. Committed and pushed before any seed other than 42
exists.** Date: 24 Aug 2026. Conventions: Δ = candidate − baseline; **negative = candidate
better** (standing practice 6). Inference path and input provenance stated per row (standing
practice 5). Structural model: [phase-c-lpips-registration.md](phase-c-lpips-registration.md).
Practice numbers are cited from [standing-practices.md](standing-practices.md), which is the
authority; [paper-context-addendum.md](paper-context-addendum.md) §11 renumbers them and must
not be used for this.

## Why this package exists — the gating weakness, stated as it was found

An adversarial review pass of the paper's argument found the weakness below. **We did not see
it ourselves.** It survived the C4/C5 registration, the results document, and a three-leg
registration audit of that package ([phase-c-audit.md](phase-c-audit.md)) which checked
timeline, recomputation and configuration and did not think to check the unit of replication.
That is recorded here because the pattern matters more than the instance: every check we ran
was a check on *whether the numbers are what we say they are*, and none was a check on *what
the numbers are evidence about*.

**Consequence for the audit method, adopted from this package: a fourth leg.** After timeline,
recomputation and configuration, registration audits now ask *at what level was the treatment
applied, at what level is the error bar computed, and are they the same level?* — and more
generally whether the design can support the claim the document draws from it. Recorded as
**standing practice 9** in [standing-practices.md](standing-practices.md), with this package
named as its origin, so the class is caught next time rather than this instance.

**The treatment is applied once per cell.** One seed, one initialisation, four runs. Each
2×2 cell contains exactly one trained checkpoint.

**Every standard error in the paper is chip-level.** The primary result C5 − C4 =
−0.487 ± 0.053 px, t = −9.18, is the mean and standard error of 130 per-chip paired
differences. What that t-statistic measures is **how consistently one C4 checkpoint loses to
one C5 checkpoint across 130 evaluation chips**. It does not measure how consistently an
adversarial term costs positional accuracy, because the adversarial term was applied once.
**The 130 chips replicate the evaluation, not the intervention.** A chip-level SE answers
"would another chip agree?"; the claim in the paper is "would another training run agree?",
and nothing in the package addresses it.

**The interaction has no run-level error bar at all.** I = (C4 − C5) − (C1 − C2) =
−0.212 ± 0.069, t = −3.07, is the only quantitative support for "the two pressures act on the
same lever". It is a contrast among **four numbers, one per cell**, and its ± is again
chip-level. At the level the claim is made — that the *design factors* interact — the
interaction is a single observation with no replication whatsoever.

**Seed 42 also fixes a nuisance factor that is not balanced across arms.** The discriminator
is not published (only `latest_net_G.pth` is released), so C1 and C4 build a cold D with
`make_cold_start_D()` seeded 42, while C2 and C5 have no discriminator to initialise. One seed
therefore fixes one particular random discriminator draw, and that draw is a factor the
adversarial arms carry and the non-adversarial arms do not. Any effect of *which* cold D was
drawn is currently indistinguishable from the effect of *having* a discriminator.

**What this package does not claim.** It does not claim the reported effects are wrong. The
seed-42 numbers reproduce from raw output cell-by-cell (audit §B.1) and the effect is large.
It claims only that the inference published against them is stated at the wrong level, and
that the fix is to replicate the intervention rather than to argue about it.

## Design

**Re-run the full 2×2 at additional training seeds. The training seed is the only thing that
varies.** Same 5,577 Turkish pairs, same packaged dataset (`vedatyildirim/gencp-tr` v1), same
schedules — C1 and C4 keep the 2-epoch warm-up at 2e-5 with `--lr_policy step
--lr_decay_iters 50` then linear 10+10 at 1e-4 and `epoch_count 3`; C2 and C5 run C2's single
linear 10+10 stage at 1e-4 with `epoch_count 1` — 20 epochs, batch 4, load 286 / crop 256,
BtoA, `unet_256`, norm batch, `gan_mode vanilla`, λ = 100, `save_epoch_freq 1`, same Kaggle
image and T4 machine shape. Evaluation through the **committed** `tubitak/scripts/c45_eval/`
harness (commit `40cde9b`), same 130 Ankara chips, same archived OVP inputs, same warp
geometry, same KARIOS config `karios_gencp.json` (sha256 `8eaa5bd8…`), STOCH path, **single
draw** — n = 130 ≥ 60, so standing practice 2's K-draw averaging does not apply and single-draw
is the registered choice, identical to seed 42's.

**Varying the training seed also varies the cold-D initialisation in the adversarial arms.
That is intended, not a confound to be removed.** The question "does an adversarial term cost
accuracy" is a question about the procedure *including* whatever discriminator that procedure
happens to draw. Holding the D draw fixed across seeds would answer a narrower question than
the paper asks.

### Stage 1 — this week: seeds 43 and 44, all four cells

Eight training runs. GPU budget, from the measured elapsed field of each seed-42 Kaggle log
rather than from an estimate:

| arm | measured seed-42 wall time |
|---|---|
| C1 (GAN + L1) | 1 h 15 m (4,528.4 s) |
| C2 (L1 only) | 1 h 16 m (4,573.1 s) |
| C4 (GAN + LPIPS) | 3 h 28 m (12,486.8 s) |
| C5 (LPIPS only) | 3 h 33 m (12,835.9 s) |
| **per seed** | **9 h 33 m** (34,424.2 s) |
| **two seeds** | **19 h 07 m** (68,848.4 s) |

Against **22 h 57 m** remaining quota this week, leaving **3 h 49 m** margin. *(The figures
9 h 31 m / 19 h 02 m used when this package was proposed come from summing the per-arm times
after rounding each down; the exact sum is three minutes per seed larger. The conclusion is
unchanged and the margin is still comfortable, but the arithmetic is stated from the logs so
the record does not carry a rounded number as if it were measured.)* **Nothing else runs on
GPU this week** — the margin is reserve for a failed kernel restart, not for other work.

### Stage 2 — next week, conditional on stage 1

Seeds 45 and 46, all four cells (another 19 h 07 m, to be re-checked against next week's quota
before launch), **plus the D-warm-up control run that
[headline-registrations.md](headline-registrations.md) B1 promised and never launched**. B1's
own words, quoted so the commitment is visible: *"The honest fix is ONE confirmatory run
(D-only warm-up, G frozen ~200 iters, else identical to C2's schedule) — **reported first, not
launched in this package.**"* It was reported first and not launched, and it has stayed
unlaunched since 21 August. It is scheduled here. Expected cost ≈ 1 h 16 m (C2's schedule
plus a ~200-iteration D-only warm-up).

**The stage-2 condition, registered now:** stage 2 launches if and only if the stage-1 primary
reading below holds. If it does not, stage 2 is **not** launched on this design — see
Registered consequences.

## Seed-42 comparability — the caveat, registered before the analysis

Seed 42 is not a clean member of the seed factor. Its **C4 and C5 were trained 23–24 August on
the current code path**; its **C1 and C2 were trained 19–20 August on an earlier one**, and
that C1 additionally carries the corrections-log entry 5 restart (`--lr_policy step` applied to
stage 1 after the original run was discarded). Including seed 42 therefore mixes code paths
*within one level of the seed factor* — the C1/C2 half and the C4/C5 half of seed 42 did not
come from the same build.

**Registered disposition, in advance:**

1. Seed 42 **is included** at stage 1, giving **n = 3 seeds**, with the caveat stated wherever
   the number appears.
2. **Its position within the range of seeds 43 and 44 is checked and reported** for every
   primary quantity (C5 − C4, C1 − C2, C4 − C5, I, C5 − C2, and each arm's edge ratio).
3. **If seed 42 falls outside the range spanned by seeds 43 and 44 on any primary quantity,
   that is reported as a finding**, not smoothed over — it is direct evidence that the code-path
   difference is doing work.
4. At **stage 2 the entire analysis is repeated on the four new seeds alone** (43, 44, 45, 46),
   which share one code path. **If the two versions disagree, the four-seed version governs**
   and the five-seed version is reported beside it as the mixed-path comparison it is.

## Inference level — the correction this package exists to make

**All primary inference is at the SEED level.** Per seed and per contrast: compute the paired
per-chip difference across all 130 chips, average it to **one number for that seed**, then
infer across seeds. The unit of analysis is the training run, because the training run is the
unit the treatment was applied to.

**Chip-level statistics are reported separately and labelled "within-run consistency".** They
are legitimate and informative — they say how uniform an effect is across terrain — and they
are **never** presented as evidence about the treatment. Every chip-level t-statistic in the
paper is relabelled accordingly, including the t = −9.18 that currently reads as the primary
result's strength.

**The statistical weakness of this design, stated now rather than discovered later, and
counted against the CONFIRMATORY seeds.** *(Corrected 2026-08-24: an earlier version of this
paragraph counted seed 42 as a replicate and therefore quoted df = 2 at stage 1 and df = 4 at
stage 2. Demoting seed 42 to the generating observation removes one seed from each count. The
corrected figures are worse, and they are the ones that govern.)*

| stage | confirmatory seeds | df | t*(0.975, df) |
|---|---|---|---|
| **stage 1** | **2** (43, 44) | **1** | **12.71** |
| **stage 2** | **4** (43, 44, 45, 46) | **3** | **3.18** |

At **df = 1 the 95% multiplier is 12.71** against 1.96 asymptotically. An interval built on
two seeds is therefore about six and a half times wider than a large-sample one and will
include zero for any effect this package could plausibly produce. **This is not a marginal
weakness to be noted and worked around: at stage 1 the seed-level interval carries no
information.** Stage 2's df = 3 and multiplier 3.18 is a real improvement and still weak.
**This package cannot deliver a tight seed-level interval and is not designed to.**
Therefore:

- **Sign consistency is the stage-1 read, and at df = 1 that is no longer a judgement call —
  it is the only read available.** Does the effect point the same way in both independently
  trained replicates? That is a binary, distribution-free question that two seeds can answer,
  and with the direction pre-specified by seed 42 the null probability is ½ × ½ = **1/4**.
- **The interval is the stage-2 read**, and even there it is reported with its degrees of
  freedom and its multiplier in the sentence, not in a footnote.

A wide interval at stage 1 is an expected outcome and will not be described as a null result.
An interval reported at stage 1 must carry "df = 1, t* = 12.71" in the same sentence, so no
reader mistakes its width for a measurement.

## Seed 42 generated the hypothesis and therefore cannot confirm it

**The direction under test was read off seed 42.** "C5 − C4 is negative" is not a prediction
this package inherited from theory; it is the seed-42 observation, and the mechanism story was
built to explain it after it was seen. A hypothesis cannot be confirmed by the observation that
generated it, so **seed 42 contributes no confirmatory evidence to any reading below.**

**At stage 1 the confirmatory evidence is TWO independent replicates, seeds 43 and 44 — not
three.** Seed 42 is reported alongside them, labelled as the generating observation, and its
position within the range of the new seeds is checked per the comparability rule above. It
earns its place in the tables as context and as a code-path check, never as a third vote.

The same correction applies to the main effect, the secondary reading and the mechanism
reading: **each is a confirmatory test on the new seeds**, with seed 42 as the generating
observation. Stage 2 adds seeds 45 and 46, giving **four confirmatory replicates**.

## Registered readings

All contrasts are seed-level means of per-chip paired differences, on the ank130 panel,
STOCH single draw, OVP inputs. **Every reading below is scored on the new seeds only.**

**Primary.** C5 − C4 **negative in both new seeds (43 and 44)** at stage 1, with seed 42
reported beside them as the generating observation.

**Stage 2's primary reading, re-registered now because the old one no longer maps.**
*(Corrected 2026-08-24: it read "at least four of the five seeds", which counted seed 42 as a
replicate. There are **four** confirmatory seeds at stage 2, not five, so "four of five" is
undefined. The replacement is registered here, before any stage-2 data exists.)*

- **Registered stage-2 primary: C5 − C4 negative in all four confirmatory seeds (43, 44, 45,
  46)**, and the seed-level interval (df = 3, t* = 3.18) reported with its multiplier whether
  or not it excludes zero. The interval is **reported, not required** — at four seeds it can
  fail to exclude zero for an effect that is real, and pre-committing to it as a gate would
  invite reading a wide interval as a null.
- **At three of four:** the primary is reported as **replicating with one exception**, the
  exception seed is named, its value printed, and its position relative to the other three
  examined for a cause (code path, resume, cold-D draw). The paper may state the effect as
  replicated **only** with that exception disclosed in the same sentence — never as "four
  seeds agree" and never with the outlier dropped. Under the null the chance of at least
  three of four matching a pre-specified direction is 5/16, so three of four is **weak
  evidence and is written that way**.
- **At two or fewer of four:** the primary has not replicated. The consequence in the
  Registered consequences section applies in full.

**The null probability, with the reasoning corrected.** Under a null of no treatment effect,
each seed's sign is a fair coin, and the direction is **pre-specified** because seed 42 fixed
it. So P(both new seeds negative) = ½ × ½ = **1/4**. An earlier draft of this document
justified the same 1/4 as "the chance of three matching signs" across seeds 42, 43 and 44 —
which is arithmetically true as a *two-sided* statement (2 × ½³ = ¼) but is not the reasoning
that applies here, because it counts seed 42 as evidence and it tests "all three agree in
either direction" rather than "the new seeds agree with a direction fixed in advance". **The
two calculations coincide at 1/4 by coincidence, not by equivalence**: one is two-sided over
three observations, the other one-sided over two. The one-sided-over-two version is the one
this package is entitled to, and it is the weaker of the two — 1/4 is not a small number, which
is exactly why sign consistency is a stage-1 read and not a conclusion.

**Main effect (both reconstruction terms).** C1 − C2 > 0 **and** C4 − C5 > 0 **in both new
seeds**, and in seeds 45 and 46 at stage 2. This is the adversarial penalty stated as the
design factor it is, once under each reconstruction term.

**Interaction.** I = (C4 − C5) − (C1 − C2) negative at seed level **AND** negative after a
monotone re-scaling. **Both transforms are registered now, before any seed is run:**

1. **Natural log of the per-chip residual**: I_log = (ln C4 − ln C5) − (ln C1 − ln C2), per
   chip, averaged per seed. Zero or non-finite per-chip residuals are excluded pairwise and the
   exclusion count reported per seed; if any seed loses more than 5 of 130 chips this way, the
   log transform is reported as unusable for that seed rather than silently thinned.
2. **Rank transform within chip across arms**: for each chip the four arms are ranked 1–4 by
   residual (1 = best), and I_rank = (rank C4 − rank C5) − (rank C1 − rank C2) is averaged per
   seed. Ties by mid-rank.

**Why both, registered as the reason and not as a hedge:** the residual scale has a hard floor
at zero, so a contrast between a large gap and a small gap is *expected* to shrink on the raw
scale for purely arithmetic reasons. **Sub-additivity on a raw scale with a floor at zero is
the null expectation, not a mechanistic finding.** Accordingly: **the raw-scale interaction
alone will not be reported as mechanistic** under any outcome. "The same lever" requires the
sign to survive at least one monotone re-scaling.

**Secondary.** C5 − C2 **positive in both new seeds** (and in 45, 46 at stage 2) — the
LPIPS-alone positional penalty.

**Mechanism.** Edge ratio in input-silent regions, computed per seed for all four arms under
the definition already implemented in `c45_eval/c45_edge_ratio.py`, unchanged.

**The statistic is the per-arm MEAN of the 130 per-chip ratios**, stated explicitly because
this project has already had one correction about which statistic a committed edge-ratio value
was (corrections-log entry 24 — the seed-42 scalars turned out to be medians where the prose
did not say so). The mean is chosen not on merit but because **it is the statistic the
seed-42 registered bands were written on** — "near 1.0 = **mean** ratio ≥ 0.8; well below
1.0 = **mean** ratio ≤ 0.5" ([phase-c-lpips-registration.md](phase-c-lpips-registration.md)) —
so the comparison across seeds is like-for-like. **The median is reported beside it in every
table**, and the two must never be interchanged: seed 42's C2 is **0.284 mean / 0.218 median**,
and both clear the 0.5 threshold, but only one of them is the registered quantity.

Readings, both on the mean, per seed, not pooled:

- **C2 mean edge ratio < 0.5 in both new seeds.**
- **C5 mean edge ratio highest or tied-highest of the four arms in both new seeds.**

**"Tied" is defined now, operationally, so it is not decided after seeing the data.** C5 counts
as **tied** with a competing arm if the absolute difference between their per-seed mean ratios
is **smaller than the standard error of that difference computed across the 130 chips**
(paired per-chip differences, SE = sd/√130). If C5's mean is below a competitor's by more than
that SE, C5 is **not** highest and not tied, and the reading fails for that seed.

**Training curves — free corroboration, no extra GPU cost.** Per-epoch reconstruction loss is
already written to every Kaggle log. Pre-committed prediction, registered before any new seed
runs: **in every seed, the two discriminator-bearing arms (C1, C4) fail to reduce their
reconstruction loss over the main stage, while the two without one (C2, C5) fall by roughly
eight percent.** Seed-42 values for reference: C1 +1.16%, C4 +2.50%, C2 −7.90%, C5 −7.54%.

**This observation cannot separate the discriminator explanation from a warm-up explanation,
and is registered with that limit attached.** Warm-up presence is perfectly collinear with
discriminator presence in this design — C1 and C4 carry the 2-epoch 2e-5 warm-up, C2 and C5 do
not — so "the discriminator competes with the reconstruction term" and "the arms that had a
warm-up behave differently after it" predict the same pattern, in every seed, no matter how
many seeds are run. **Replication cannot break a collinearity.** Breaking it needs **one extra
run that changes one factor while holding the other**: either **C5 with the warm-up** or **C4
without it**, ≈ 3 h 30 m. **It is recorded here as available and is deliberately not
scheduled** — stage 1's quota does not hold it, and it is listed for a later package rather
than left as an unstated gap. Until it runs, the training-curve observation is corroboration
of a pattern, not evidence for a mechanism, and must be written that way.

**Multiplicity, stated in one sentence so five sign tests are not read as five independent
confirmations.** This registration contains **five sign-based readings** — primary, main effect
(two contrasts), interaction, secondary, mechanism (two thresholds) — of which **only the
primary is a protected reading**; the rest are **reported as measured**, and no multiplicity
correction is applied because none is being claimed as an independent confirmation of the
primary. A reader should treat the non-primary readings as descriptions of whether the picture
hangs together, not as four further tests that passed.

## Operational rules registered in advance

### An interrupted run is disclosed, never silently equated

Kaggle sessions die. `--save_epoch_freq 1` means a killed run **resumes** rather than
restarts (standing practice 7), but **a resumed run does not have the same RNG stream as an
uninterrupted one**: the dataloader shuffle, the dropout masks and — in the adversarial arms —
the discriminator's update sequence all restart from a re-seeded state at the resume point. A
resumed run is therefore **not the same draw of the seed** as an uninterrupted run of that
seed, and this registration does not pretend otherwise.

Registered now, before any interruption has happened:

1. **Any run that is interrupted and resumed is DISCLOSED in the results document, with its
   resume epoch recorded.** Not "was resumed" — the epoch number.
2. **Resumed runs are identified in every table** in which their numbers appear, by a marker
   in the row, not by a footnote elsewhere.
3. **If more than one run within a seed is resumed, that seed is flagged in the analysis** and
   **its position relative to the unresumed seeds is reported** for every primary quantity —
   the same treatment seed 42 gets for its code-path mixing.
4. No rule is registered that treats a resumed run as equivalent to an uninterrupted one,
   because we do not know that it is.

### If stage 1 cannot complete within the quota, the incomplete seed is not analysed

The 3 h 49 m margin covers **exactly one** failed C4 or C5 restart (3 h 28 m / 3 h 33 m). Two
such failures put stage 1 past the week's quota.

**Registered: if stage 1 cannot complete all eight runs within the week, the incomplete seed is
NOT analysed, and the package waits for the quota reset.** An unbalanced factorial is not
scored — a seed missing one of its four cells cannot produce the paired contrast that seed
exists to supply, and a seed missing its C4 or C5 cannot produce the primary at all.

**The temptation being foreclosed, named so this reads as a decision rather than an
oversight:** analysing the one complete seed because it is there, and reporting "the primary
replicated in the seed we finished". That would convert a resource failure into a one-replicate
result and would reproduce, at the level of seeds, exactly the error this whole package exists
to correct. The partial seed's runs are kept, disclosed as partial, and finished after the
reset.

### The seed-level analysis script is committed before any seed is scored

The evaluation harness is already committed (`tubitak/scripts/c45_eval/`, `40cde9b`), but the
**seed-level analysis is new code**: the per-seed averaging, the log and rank transforms with
the pairwise exclusion rule, the interaction on all three scales, the seed-level intervals with
their degrees of freedom, the tie rule, and the seed-42 range check. **Corrections-log entries
22 and 25 exist because an uncommitted analysis layer cost this project twice** — once when
B3's harness was deleted and four registered matcher parameters became unverifiable, once when
phase-C's per-chip layer vanished and took the Gate-1 target with it.

**Registered: `tubitak/scripts/seed_eval/seed_analysis.py` is written and committed BEFORE any
seed is scored.** Any change to it after scoring begins **must be registered** — an amendment
to this document, dated, with the original preserved, per standing practice 4. A change made
silently mid-analysis is the failure mode, not a change as such.

## Registered consequences — verbatim, decided before the numbers exist

- **If the interaction is not sign-stable across seeds:** *"the same lever", "substitutes" and
  the word "interaction" are dropped from the paper and the adversarial main effect is
  published alone.*
- **If C5 − C2 is not positive in every seed:** *the LPIPS-alone penalty moves from a result to
  a discussion-section hypothesis and the claim narrows from "plausibility pressure" to "the
  adversarial term".*
- **If the primary is not negative in BOTH confirmatory seeds at stage 1 (43 and 44):**
  *stage 2 is not launched on this design; the package is re-planned and the failure
  reported.* (Corrected 2026-08-24 from "all three seeds", which counted seed 42 as a
  replicate; seed 42 cannot pass or fail a reading it generated.)
- **If the edge-ratio ordering is not stable:** *the mechanism is presented as arm-separating
  rather than arm-ordering.*

These are the consequences, not a menu to choose from after seeing the data. Standing practice
4 governs: registrations before numbers; failed gates reported, never adjusted; a
mis-specified gate may be re-registered only with the original preserved and labelled failed.

## Stop rule

**AMENDMENT C45-a governs these runs prospectively** — which is the point of having scoped it
that way when it was written ([phase-c-lpips-registration.md](phase-c-lpips-registration.md),
corrections-log entries 26 and 27). Restated here so the scope cannot be misread: **C45-a does
not retroactively bless the completed seed-42 arms**, which stand on the original rule that
fired and was not acted on, defended by the mis-specification argument and the epoch-2 /
epoch-5 counterfactual recorded there.

These runs are the **first genuine test of C45-a**, on curves nobody has seen. The coarse half:
*the run stops if the per-epoch reconstruction loss rises more than 10% above the lowest value
seen so far in the main stage (running minimum), sustained over two consecutive epochs.*

**The sharp half has no committed threshold, and this registration had to find that out rather
than quote it.** C45-a describes the sharp half as "unchanged", and the intent was to quote the
original C1 threshold here so that if it fires the record says what fired. There is nothing to
quote. Searching the repository: [phase-c-config.md](phase-c-config.md) defines it only in
words — *"a generator-loss spike in the first few hundred iterations, the actual cold-D
signature"* — with no magnitude; corrections-log entry 5 reports the only quantified trace,
*"zero spike events against a 20-row running median"*, which fixes a **baseline** but not a
**threshold**; and there is **no spike-detection code anywhere** — not in
`tubitak/kaggle/train_c1_c2.py`, not in `tubitak/scripts/`. So for two packages the sharp half
has been the half that "remains the operative divergence test" while being unspecified and
unimplemented, and it has never fired because nothing was watching.

**Registered here, calibrated on the four completed seed-42 runs rather than guessed.** The
quantity is the logged **reconstruction** loss (`G_L1`, or `G_LPIPS` on the C4/C5 arms). The
statistic is its ratio to its own **trailing 20-row running median** — the window inherited
from entry 5, so the baseline stays continuous with what was used to assess C1's warm-up. The
evaluation window is the **first 500 optimizer steps = the first 2,000 images = the first 100
logged rows** at `--print_freq 10` with batch 4, which the log emits one row per 5 steps.

**What normal looks like on this model, this data and this schedule** — maximum ratio in that
window, measured from the four seed-42 logs, per stage and per run (the adversarial arms have
two stages and the check runs on each):

| run | warm-up stage | main / single stage | **per-run max** |
|---|---|---|---|
| C1 (GAN + L1) | 1.3806 | 1.5692 | **1.5692** |
| C2 (L1 only) | — | 1.5091 | **1.5091** |
| C4 (GAN + LPIPS) | 1.1626 | 1.1041 | **1.1626** |
| C5 (LPIPS only) | — | 1.0906 | **1.0906** |

Highest anywhere in those four runs with the window restriction lifted: **1.8792** (C2).

**Registered threshold: 2.5**, with two rows over it required to stop the run. The margin is
printed rather than asserted: 2.5 is **1.59× the highest windowed value** (1.5692) and **1.33×
the highest ratio seen anywhere in four runs that all finished normally** (1.8792). All six
stage-windows were replayed through the exact implementation and produce **zero hits**, so the
rule does not fire on healthy training — which is the necessary condition, not evidence that
it catches anything.

**Why the quantity is the reconstruction loss and not `G_GAN` — the mechanistic reason, with
the variance figures as supporting evidence rather than as the argument.** The failure this
gate exists to catch is **cold-D damage to the generator**, and cold-D damage shows up as
degraded generator *output quality*. The reconstruction loss is a direct measure of output
quality: it compares G's output to the target. `G_GAN` measures something else entirely — the
**state of the adversarial game**, i.e. how well D is currently distinguishing G's output —
and early in training, against a discriminator initialised from noise, that quantity is
*expected* to swing hard as D learns. A large early `G_GAN` movement is the game equilibrating,
which is the normal course of the thing we are watching, not evidence that G has been damaged.
**`G_GAN` is therefore the wrong quantity for a damage detector regardless of its variance**,
and it would remain the wrong quantity even if it were perfectly stable.

The variance figures corroborate that reasoning rather than carrying it: `G_GAN` in normal
training reaches **3.75×** on C1 and **2.85×** on C4 against the same trailing-median
statistic, so a `G_GAN` detector at this threshold would also have false-fired on healthy
runs. Both facts point the same way; only the first is a reason.

**Label, stated precisely and not overstated.** This rule is **newly specified**, not quoted
from any prior document; **calibrated on the four completed seed-42 runs**, which is disclosed
because it means the threshold has seen these arms; **prospective only**, on the same footing
as C45-a, governing these runs and reaching back to no completed arm; and **a NOVELTY
detector, not a validated divergence test** — it catches a run that looks unlike anything we
have seen, and it has never been shown to catch divergence, because divergence has never been
observed here.

**Where it runs, so it can actually fire.** Implemented in
[`tubitak/kaggle/train_c1_c2.py`](../kaggle/train_c1_c2.py) as `run_train()`, which streams
each training stage's output, echoes every line unchanged, and **evaluates the rule at the end
of the first epoch of every stage** — roughly ten minutes on the LPIPS arms, so the cost of
watching is bounded. On firing it prints the offending rows with their ratios, terminates the
child process and exits non-zero. `--print_freq 10` is **explicit in the launch config**, not
assumed: it is in the `base` argument list every stage is invoked with, and the window
depends on it.

**If C45-a fires on any new run, that run stops and the firing is reported, whatever it costs
this package.** Including the case where it fires on an adversarial arm and thereby removes a
cell from the factorial; including the case where it fires late and wastes most of a seed's
quota. A stop rule that is only honoured when it is cheap is not a stop rule, and this project
has already recorded one instance of a gate that fired and was not acted on.

## Invariances (standing practice 1)

Stated explicitly for both sides of every comparison, because a gate that does not state its
invariances does not know what it is measuring:

| assumed identical | on both sides of every comparison |
|---|---|
| training data | the 5,577 Turkish pairs, `vedatyildirim/gencp-tr` v1, zero EU mix |
| schedules | C1/C4 = 2-epoch warm-up 2e-5 (`step`, `lr_decay_iters 50`) + linear 10+10 at 1e-4, `epoch_count 3`; C2/C5 = linear 10+10 at 1e-4, `epoch_count 1` |
| model and optimiser | `unet_256`, batch 4, load 286 / crop 256, BtoA, norm batch, `gan_mode vanilla` (BCE) where a D exists, λ = 100, `save_epoch_freq 1` |
| initialisation | the released `latest_net_G.pth`, identical file, every arm and every seed |
| hardware and image | Kaggle T4, same image, same torchmetrics 1.9.0 (recorded from each log and reported) — **superseded for runs after 2026-08-25 by AMENDMENT SEED-b below** |
| data source | OSM/CLC+ archived **OVP** evaluation inputs — the same files seed 42 used |
| render path | none; no rendering occurs in this package, the inputs are archived rasters |
| code path | the current build for **all** new runs; the seed-42 C1/C2 exception is the disclosed one above |
| determinism | none claimed — the **STOCH** dropout-active path throughout, single draw, as in seed 42 |
| evaluation harness | `tubitak/scripts/c45_eval/`, committed at `40cde9b`, unmodified; any change to it before or during this package invalidates the comparison and must be registered |
| evaluation set | the same 130 Ankara chips, same warp geometry (GSD 10.0390625, 228-grid), same BT.601 conversion |
| matcher | KARIOS, config `karios_gencp.json`, sha256 `8eaa5bd8cdae066d2580a4105169262f873523cadf0b450a8aa134a31ed4ca84` |
| inference | STOCH single draw per chip per arm per seed, **dropout shim `_shims/s42` for every training seed** — see AMENDMENT SEED-a below |
| **evaluation hardware** | **the same local machine for every seed, 42/43/44 included** — added 2026-08-25, see the note below |

> **Evaluation hardware, stated 2026-08-25 as an assumption we had been relying on without
> writing down.** Every seed's evaluation — inference, warp, KARIOS, edge ratio, scoring — has
> run on the **same local machine**, seeds 42, 43 and 44 alike, through `seed_eval_run.py`.
> That makes evaluation hardware a **constant across the whole seed set**, and it must stay
> one. Only *training* moves to Modal (AMENDMENT SEED-b); **evaluation does not, and must
> not.** Moving it would introduce for the evaluation step precisely the hardware question
> this package spent AMENDMENT SEED-b resolving for training — a second uncontrolled axis, on
> the side of the pipeline that produces the reported numbers rather than the checkpoints.
> Recorded here because it was true of every run so far and had never been asserted, which is
> the same defect corrections-log entry 29 records: an invariance relied on without being
> stated, and therefore without being checkable.
>
**The one thing that is not identical: the training seed**, and through it the cold-D draw in
the adversarial arms. That is the manipulated factor.

> **AMENDMENT SEED-a, 2026-08-24 — the inference dropout seed is held at 42 for every
> training seed. Dated, with the original row preserved above (it read "STOCH single draw per
> chip per arm per seed" and nothing more). Written and committed BEFORE any seed is
> evaluated.**
>
> **This makes explicit what the invariance table already commits to; it is not a new
> choice.** The table's closing sentence says the training seed is the only thing that
> varies. Letting the inference dropout draw follow the training seed would vary **two**
> things at once — what was trained and how it was sampled at test time — and would
> contradict the invariance this registration is built on. Seed 42's evaluation used shim
> `_shims/s42`; every replication seed uses the same shim, so the evaluation draw is common
> across seeds and the training seed stands alone as the manipulated factor.
>
> **The statistical reason.** The across-seed variance is the quantity every registered
> reading is inferred from, and the question is *whether the effect survives retraining*. That
> variance must therefore contain **training variance only**. Varying the evaluation draw as
> well would inflate it with measurement noise, widening every interval and answering a
> blurrier question — "does the effect survive retraining *and* resampling" — which is not the
> question registered. With df = 1 at stage 1 there is no variance budget to spend on noise
> that the design does not need.
>
> **The counter-argument, recorded rather than only the conclusion: a common draw cannot
> reveal draw-dependence.** If a result held only under one particular dropout draw, this
> design would not detect it. That risk is bounded by the evidence that exists: the
> deterministic-mode measurement was **score-neutral at largest |Δ| = 0.040 ± 0.077 px
> (n = 30)** ([paper-context-addendum.md](paper-context-addendum.md) §8), which rules out
> shifts larger than about **0.15 px** — against a primary effect of **0.487 px**. Draw
> dependence large enough to manufacture that effect is excluded by a measurement already in
> the record; draw dependence smaller than 0.15 px cannot account for it.
>
> **This is a scoping decision, not a closed door.** Draw-dependence remains cheaply
> answerable later: K seeded draws over the **existing** checkpoints, no GPU training, exactly
> the standing-practice-2 procedure already used for the B2 production row. If it is ever
> wanted it can be added as its own registered question, and nothing in this package forecloses
> it.

> **AMENDMENT SEED-b, 2026-08-25 — remaining GPU work moves from Kaggle T4 to Modal L4.
> Dated; the original invariance row is preserved above verbatim. Written and committed
> BEFORE any Modal run. The hardware gate defined here has NOT run at the time of writing,
> and its acceptance rule is registered below before it does.**
>
> **The move, and why.** Remaining runs execute on **Modal** instead of Kaggle T4 (Turing,
> sm_75). *(GPU choice: L4 as first written, superseded by A10G below before any run.)* Reasons: no weekly quota; roughly **3.5x the T4 in fp32** on this
> workload; detached execution, so the machine driving it can be closed; and the whole
> remaining program fits inside Modal's **$30/month free credits**.
>
> **SUPERSEDED BEFORE ANY RUN, 2026-08-25: A10G (Ampere, sm_86), not L4.** The L4 choice
> above is preserved rather than deleted, because the reason it was replaced is the record's
> whole point.
>
> **The deciding fact: `sm_89` is not in the pinned build's arch list.** The recovered arch
> list is `['sm_70','sm_75','sm_80','sm_86','sm_90','sm_100','sm_120']`. L4 is Ada = sm_89 and
> is absent; **A10G is Ampere = sm_86 and is present**, natively supported, no JIT, no
> compatibility argument to make.
>
> **The reason is not speed.** fp32 throughput is **31.2 TFLOPS (A10) vs 30.3 (L4)** —
> effectively identical, and either would have done. The reason is that running on an
> architecture outside the pinned build's arch list means the paper would have to carry the
> argument *"CUDA guarantees binary compatibility within a major version, so sm_86 code runs
> on sm_89."* That argument is **probably right**. Corrections-log **entry 9** exists because
> a probably-right hardware assumption — `torch.cuda.is_available()` returning True on a P100
> torch could not emit code for — cost this project an entire preflight. **About $4.50 across
> the whole remaining program removes the argument entirely**, and an argument not made cannot
> be attacked.
>
> **The sm_89 gap was found BEFORE any run, not after.** It surfaced while pinning the Modal
> image against the recovered Kaggle arch list, which is the same act that surfaced entry 29.
> That is the practice working as intended: the cost was a decision changed on paper instead
> of a result withdrawn later.
>
> **TF32 is explicitly DISABLED** — `torch.backends.cudnn.allow_tf32 = False` and
> `torch.backends.cuda.matmul.allow_tf32 = False`, set before any model is constructed. The
> reason is the point of the whole exercise: **the T4 is Turing and has no TF32 at all**, so
> leaving Ampere's TF32 on would change convolution and matmul precision *as well as* hardware,
> and two factors would move where we intend one. This costs speed on the L4 and **we accept
> that cost knowingly**.
>
> **Hardware becomes a second factor across the seed set, and is registered as an additional
> source of training variation rather than as contamination.** If the effect survives across
> seeds AND across hardware, that is a *stronger* replication than seeds alone — it rules out
> a per-architecture numerical artefact that no number of same-hardware seeds could exclude.
> What must not happen is pooling across hardware when hardware shifts the result
> systematically; the gate below is what decides which case we are in.
>
> **Every contrast must be internally clean: both arms of any comparison run on the same
> hardware.** A Modal arm is never compared against a Kaggle arm. Contrasts are formed within
> a seed, and a seed is trained entirely on one platform.
>
> ### The hardware gate, with its reading registered in advance
>
> **Re-run seed 43, all four arms, on Modal A10G** — identical in every other respect: same
> 5,577 pairs, same schedules, same 20 epochs, same seed 43, TF32 off, evaluated through the
> same `seed_eval_run.py`. Cost approximately 3 A10G-hours (~$3.30 of the $30 monthly credit). **SUPERSEDED — see the throughput measurement above: on the Volume this projected to ~15 h and ~$16.50; with tar staging it returns to roughly the original estimate. The wrong figure is kept here rather than edited away.**
>
> Compared against the **Kaggle T4 seed-43 values already measured**:
>
> | quantity | Kaggle T4 seed 43 |
> |---|---|
> | C5 − C4 | −0.5485 |
> | C1 − C2 | +0.6636 |
> | C4 − C5 | +0.5485 |
> | C5 − C2 | +0.1275 |
> | I_raw | −0.1151 |
> | edge mean pretrained / C1 / C2 / C4 / C5 | 1.021 / 1.083 / 0.279 / 1.121 / 1.154 |
>
> **Registered acceptance rule, committed before the gate runs.** The reference scale is the
> **observed seed-to-seed spread between seeds 43 and 44** on each quantity — the amount that
> quantity already moves when only the training seed changes.
>
> - **If every Modal-vs-Kaggle difference at seed 43 is smaller than the corresponding
>   s43-to-s44 spread:** hardware behaves like seed noise or less. **Modal runs may be pooled
>   with Kaggle runs, with the hardware difference disclosed** wherever the pooled set is
>   reported.
> - **If any quantity exceeds its s43-to-s44 spread:** hardware is a larger factor than seed.
>   **Modal runs are then analysed as their own homogeneous block and compared to the Kaggle
>   block, never pooled.** The seed count is reported per block, not summed across blocks.
>
> Both branches are written here so neither is chosen after seeing the number.
>
> **Runner routing for the Modal evaluation, 2026-08-25, before any Modal arm is scored.**
> The Modal checkpoints must not collide with the Kaggle `*_s43` directories or the
> `C45_s43` outputs, and only `latest_net_G.pth` is downloaded per arm. `seed_eval_run.py`
> therefore gains two ROUTING-ONLY parameters — `--variant` (suffixes the checkpoint and
> output directories: `*_checkpoints_s43_modal`, `C45_s43_modal`) and `--arms` (subset, for
> the C2_unsorted control which is a single arm) — and the latest==20 tensor-equality check
> runs Modal-side (`gencp_modal.py::verify_latest`, where both files live) when
> `20_net_G.pth` is absent locally, with the downloaded file's sha256 asserted against the
> Modal-reported value. Per-step numeric logic is untouched, and the seed-42 reproduction
> gate was wiped and re-run AFTER this change to verify that
> ([gates/](gates/)`seed-eval-runner-gate42-at-*`; the gate path takes the defaults, so it
> exercises the modified code).
>
> **EVALUATION CODE FREEZE, 2026-08-25, while the four-arm Modal evaluation runs and before
> C2_unsorted is scored.** The five Modal arms must be scored by ONE version of the
> evaluation code — the same requirement the f2dc962 training pin enforces on the training
> side, imposed here before it can be violated rather than after. The code is frozen as it
> stands at commit `48ced64`, sha256 pinned per file:
>
> | file | sha256 |
> |---|---|
> | `seed_eval/seed_eval_run.py` | `3df87c807cefce860b4c870a36ba5e7e9c3d09051a63395ffed945b8ad46f977` |
> | `seed_eval/seed_analysis.py` | `d22053e1c3640f548c726cd4e871a3fc949f98a19d6a2c8fbd072c9bcee6e1f8` |
> | `c45_eval/c45_b2_score.py` | `ec35efc7f095b397422ce23cd2bed04ebef145be7e3cbee9f532aa48cf599f6c` |
> | `c45_eval/c45_e1.py` | `be6ecc8979c6d78df30358fb4d84d440fd47ebb424b94654c773bd89ff715174` |
> | `c45_eval/c45_edge_ratio.py` | `93819668ed7c60c0d46f41547e3f097af9007e15aa59b0b8eee755a057f5f269` |
> | `c45_eval/c45_infer.py` | `3b220f4e217a2df489125a536b75a8c271fb931d089a3e2c68a377f3c1516a86` |
> | `c45_eval/c45_karios.py` | `d4826fa07188d6227eb38a9fa8130e6701fddb52d814bab2751e5159fa92f231` |
> | `c45_eval/c45_score.py` | `02d3063d455334de3eb1c4dae65ed8b8b3bdfd8e911396be697ee5a5eab566ce` |
> | `c45_eval/c45_sweep.py` | `38bc9d58da2edd189170a62a8e36853b98d53a446f09d0f153a80676e82279e2` |
> | `c45_eval/c45_warp.py` | `3d965bcd610f060beb3b817ca2871f647cbc884b43d155ea73426946c4d37541` |
>
> No file above is edited until all five Modal arms are scored. **If a change becomes
> necessary before then, it INVALIDATES the four-arm evaluation already produced: both
> evaluations must be re-run from scratch on the changed code, after a fresh seed-42 gate.**
> That is the price of breaking the freeze, stated here so it is paid knowingly, not
> discovered afterwards.
>
> **POST-VERDICT NOTES, 2026-08-25, written after the gate returned NOT POOLED
> ([hardware-gate-results.md](hardware-gate-results.md)). Nothing here alters the verdict.**
>
> **1. Specification flaw in the acceptance rule, noticed post-hoc, not repaired.** The rule
> above issues one global verdict while scaling each quantity to its own spread, so the most
> reproducibly-measured quantity governs the package: edge_C1's spread (0.0042) set a bar an
> order of magnitude lower than the positional quantities', and one quantity vetoed ten. A
> per-quantity verdict would have been the better specification. The flaw was noticed only
> after seeing which quantity failed — when refining it would be indistinguishable from
> adjusting a gate to pass — so the verdict stands under the rule as written, and the fix is
> registered forward only: **future gates of this shape return a verdict per quantity, not
> one for the package.**
>
> **2. Platform allocation under the no-pooling verdict, decided before either package is
> designed.** The extra {C2, C5} seeds for the secondary reading (which needs n = 6; two
> Kaggle seeds are held) **move back to Kaggle T4**: under NOT POOLED, Modal seeds cannot
> contribute to that count, and Kaggle's quota is free — four seeds of the two short arms is
> roughly 19 hours, inside one week. Slower, but **poolable, which is the property that
> matters for that count**. The **warm-up de-confound stays on Modal**: that package is
> self-contained — warm-up on versus off, all arms on Modal, compared only to each other —
> so no pooling with Kaggle is required and the faster platform is free to be used there.
> **Neither package runs until its own registration is written.**
>
> **3. A Modal seed-44 replication was considered and DECLINED.** It would exist only to
> give the Modal block a seed spread of its own. Under the allocation above, the Modal
> block never has to carry a spread — the only package that lives there is internally
> self-contained. Recorded so it does not resurface as an open item.
>
> ### Data staging, enumeration order, and the throughput inversion
>
> **The measured problem.** Training directly off the Modal Volume stalled the dataloader at
> **0.120–0.491 s per image** against Kaggle's steady **0.003 s**, because pix2pix reads 5,577
> individual small files per epoch and the Volume is network-backed. Compute was **4.9× faster
> than the T4** (0.014 vs 0.0690 s/image) and the run was still **~2× slower end to end**
> (13.2 img/s vs 24.6). Projected **~15 h and ~$16.50** against the ~3 h / $3.30 first
> recorded here. **That first estimate was wrong and is preserved below rather than edited
> away**, with the measurement that replaced it.
>
> **What caught it: end-to-end throughput, not the component speedup.** A sample of
> **1,580 images in 120 seconds** contradicted a GPU that was genuinely five times faster.
> Stated as the general lesson: **a 4.9× faster component produced a 2× slower system, and
> only the end-to-end number showed it.** Component benchmarks would have confirmed the move
> and been wrong.
>
> **The fix, and the first attempt at it that also failed.** `cp -r` from the Volume was tried
> first and blew a 30-minute timeout without finishing — the same small-file network cost.
> Staging is therefore a **single 2.06 GB tar** on the Volume, one sequential read, extracted
> to container-local disk in seconds.
>
> **Enumeration order — the precondition that made the fix non-neutral.**
> `data/image_folder.py:make_dataset()` does `for root, _, fnames in sorted(os.walk(dir))`,
> which sorts the walk tuples but **not** `fnames`, so per-directory order is whatever the
> filesystem returns. Measured under both paths:
>
> | path | ordered file-list sha256 | n |
> |---|---|---|
> | Modal Volume | `4b5f232034261ed1a2b051db6e17d1dd6a1424ba9225bb49c5e3433e8493cad9` | 5,577 |
> | container-local copy | `a4171d8815059227fc8d61afd956ead164eea695e186c7913625f9faa8006099` | 5,577 |
>
> **They differ.** Without this check the gate would have run on a different file order — the
> seeded shuffle mapping to different files, batch composition changed — and nothing would
> have reported it. The pretrained generator is byte-identical after staging
> (`5938…a022` both sides), which is exactly why content hashing alone was insufficient.
>
> **The sort restores the Volume's own order on local disk; it does not impose a new one.**
> The Volume already enumerated sorted (`36SVJ_0_0.tif`, `36SVJ_0_1.tif`, `36SVJ_0_10.tif`);
> the local copy did not. Sorting explicitly **preserves the network layer's behaviour after
> the data moves**, rather than changing how the data is ordered.
>
> **The patch is committed, not applied at runtime.** `tubitak/modal/patches/image_folder_sorted.patch`
> is applied with `git apply`, which verifies the pre-state and fails loudly if upstream ever
> differs, and the **sha256 of the resulting `data/image_folder.py`** is logged at preflight
> beside the **ordered file-list hash**. A `sed` against a fresh clone would have been an
> unrecorded code path — the class entries 22 and 25 record.
>
> **Registered before it runs: the order effect is measured, not left ambiguous.** Kaggle's
> enumeration order was never recorded and cannot be recovered, so the gate alone cannot
> separate hardware from ordering. **C2 is therefore run twice inside the gate — once sorted,
> once unsorted — at fixed hardware and fixed seed. That difference IS the order effect.**
> Registered reading: report the C2 sorted-vs-unsorted difference **beside the s43-to-s44 seed
> spread and state which is larger.** If the order effect is small relative to the seed spread,
> the gate's interpretation is clean whatever Kaggle's order was, and the paper carries a
> number instead of a "we cannot know". If it is large, that must be known before any further
> seed is added. Cost ≈ 30 minutes, ≈ $0.50.
>
> **Enumeration order is a THIRD unrecorded axis**, beside the image version and the seed-42
> code path. From now on the ordered file-list hash is captured at preflight, per the
> generalised prevention on corrections-log entry 29.
>
> **Code version for the unsorted arm, decided 2026-08-25 before its launch.** C2_unsorted
> checks out the pinned `f2dc962` — the commit whose `train_c1_c2.py` (sha256 `839e1aad…`)
> every completed seed-43 Modal arm ran — not the branch head, which by launch time carried a
> later code-review pass (96503b7). One commit for every arm of the replication is simpler
> and stricter than proving equivalence for each change; 96503b7 touches nothing in the
> training path, and if a training-path fix ever becomes necessary it gets its own
> equivalence run against a completed arm before adoption. corrections-log entry 29 (sixth
> instance) records the near-miss that forced the pin: 96503b7 landed at 19:16 while C5 was
> still training, and the pin (80206b4) was committed at 19:51 — after the exposure, not
> before.
>
> ### The LPIPS backbone weights — a fifth unrecorded axis
>
> `vgg16-397923af.pth` was being **downloaded at run time** on both platforms. Those weights
> are not an incidental dependency: torchmetrics' LPIPS uses this VGG-16 as its feature
> extractor, so **they are part of C4 and C5's objective function.** If the file differed
> between Kaggle and Modal, those two arms would be training against a different loss and
> nothing in the pipeline would report it.
>
> **Now baked into the image at build time**, with the full sha256 pinned and asserted at
> preflight beside the ordered-list hash and the patched-file hash:
>
>     vgg16-397923af.pth
>     sha256 397923af8e79cdbb6a7127f12361acd7a2f83e06b05044ddf496e83de57a5bf0
>     553,433,881 bytes
>
> **What is confirmed for Kaggle, and what is not.** All six Kaggle LPIPS runs (c4/c5 at seeds
> 42, 43, 44) log the identical line — `Downloading:
> "https://download.pytorch.org/models/vgg16-397923af.pth" to
> /root/.cache/torch/hub/checkpoints/vgg16-397923af.pth` — so **the URL is confirmed identical
> on both platforms**, and torchvision's own download check verified the filename's hash tag,
> which did not error. But that check validates only the **8-hex, 32-bit prefix**, and **no
> Kaggle run ever recorded the full sha256**. So the Kaggle-side file is **strongly evidenced
> to be the same file and not verified to be** — recorded as an **unverifiable axis** rather
> than assumed. From this point forward it is pinned and checked; retrospectively it cannot be.
>
> The runtime download disappearing is a **side effect of pinning, not the reason for it**.
>
> ### Things this move caught
>
> Recorded as evidence the practice works, not only the failures it records:
>
> 1. **`sm_89` absent from the pinned build's arch list** — found while pinning the image,
>    changed the GPU choice on paper instead of producing a run that needed a
>    binary-compatibility argument to defend.
> 2. **The throughput inversion** — found by measuring end-to-end images/second, stopped a
>    15-hour, $16.50 gate at 20 minutes and $0.35.
> 3. **The enumeration-order difference** — found by hashing the ordered list rather than the
>    file contents, stopped a gate that would have silently trained on a different file order.
> 4. **The AppleDouble doubling** — the staged set was 11,154 files, not 5,577; caught by the
>    preflight capture added the same day, before any training step ran.
> 5. **The LPIPS backbone weights** — part of C4/C5's loss, downloaded at run time on both
>    platforms and never hash-recorded on either.
>
> The first three were caught before costing anything. The fourth cost nothing but was found
> only because the capture had just been added. **The fifth was found after a C4 failure whose
> cause was never established — see below; it must not be recorded as that failure's
> diagnosis.**
>
> None of the three was visible in the thing that looked like the obvious check: the GPU was
> real, the bytes were identical, the versions matched.
>
> ### Environment pins
>
> Pinned exactly, read from the Kaggle seed-43 logs:
>
> | package | pinned version | source |
> |---|---|---|
> | torch | **2.10.0+cu128** | `[preflight] torch=2.10.0+cu128` in every seed-42/43/44 log |
> | torchmetrics | **1.9.0** | `[deps] torchmetrics 1.9.0 already in the image` |
>
> **RECOVERED 2026-08-25, and labelled as recovery rather than capture.** `torchvision`,
> `Pillow`, `numpy` and the Python version were **never recorded by any run**: the script
> logged only torch and torchmetrics, and `requirements.txt` carries floors
> (`torchvision>=0.5.0`) not pins. They were recovered by a throwaway probe kernel run on
> 2026-08-25, **about 20 hours after the seed-43/44 runs**. Kaggle images are versioned and
> updated, so **this is not a capture of the image those runs used; it is a later observation
> of an image that may or may not be the same one.**
>
> Full recovered environment — Kaggle **GPU** image, `NvidiaTeslaT4`:
>
> | item | recovered value |
> |---|---|
> | image digest | `gcr.io/kaggle-gpu-images/python@sha256:37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461` |
> | image BUILD_DATE | `20260629-122508` (LAST_FORCED_REBUILD `20260508`) |
> | OS | Ubuntu 22.04.5 LTS, glibc 2.35 |
> | Python | **3.12.13** |
> | torch | **2.10.0+cu128** (`torch.version.cuda` 12.8, cudnn 91002, git `449b1768…`) |
> | torchvision | **0.25.0+cu128** |
> | torchmetrics | **1.9.0** |
> | numpy | **2.0.2** |
> | Pillow | **11.3.0** |
> | scipy | **1.16.3** |
> | CUDA_VERSION | 12.8.1 |
>
> **The consistency check, and what it does and does not establish.** The two values the runs
> themselves logged both match: torch `2.10.0+cu128` and torchmetrics `1.9.0`. That is
> **evidence the image is the same one, not proof.** Strengthening it: the recovered image's
> BUILD_DATE is **2026-06-29**, which predates *every* run in this package (19 August and
> 24 August), so unless Kaggle rotated the digest between those dates and today, all runs used
> this image. Weakening it: **the digest the runs actually used was never logged**, so the
> rotation cannot be excluded from our own records. The pins below are therefore adopted on
> evidence, and that word is used deliberately.
>
> **First probe attempt failed as designed, and the failure is recorded rather than hidden.**
> The probe was first run CPU-only. It returned `KAGGLE_DOCKER_IMAGE =
> gcr.io/kaggle-images/python@sha256:dafd4ce5…`, `COLAB_IMAGE_TYPE = cpu`, torch
> **2.10.0+cpu** and torchvision **0.25.0+cpu** — a *different image*, because Kaggle's CPU
> and GPU images are separate builds. The registered consistency check caught it immediately
> (torch `+cpu` ≠ the logged `+cu128`). The probe was re-run with `enable_gpu: true` on a T4,
> costing roughly one minute of GPU quota, which is a deliberate deviation from the
> "CPU-only" instruction and is disclosed here because the CPU image demonstrably could not
> answer the question.
>
> Why this mattered — the training transform chain
> (`data/base_dataset.py:get_transform`, `preprocess=resize_and_crop`, load 286 / crop 256) is
> `Resize([286,286], BICUBIC) → RandomCrop(256) → RandomHorizontalFlip → ToTensor → Normalize`:
>
> - `RandomCrop` and `RandomHorizontalFlip` **consume the seeded torch RNG**. If a torchvision
>   version changes how many draws they take, the augmentation stream diverges and the run is
>   a different experiment, not a hardware comparison.
> - `Resize(..., BICUBIC)` on PIL input **delegates to PIL**, so the resampled pixel values
>   depend on **Pillow's** version.
>
> An unpinned image would have made the gate a test of "hardware **plus** library versions",
> which is exactly what it must not be.
>
> ### The gap is wider than the Modal move
>
> **The image was never captured for ANY run in this package**, so "same image" is an
> unverified assumption *within* the Kaggle set as well, not only across the hardware move.
> Seed 42's C1/C2 ran **19 August**, its C4/C5 and seeds 43/44 ran **23–24 August**, and
> today's probe cannot tell us what any of them used. **The image is an unrecorded axis across
> the whole seed set.** This sits beside the seed-42 code-path caveat already registered
> above, and is the same class of defect: an invariance asserted without evidence.
> Corrections-log **entry 29** records it, and every run from now on logs `pip freeze` at
> preflight — wired into `tubitak/kaggle/train_c1_c2.py:log_environment()` in the same commit,
> so it applies on Kaggle and Modal alike.

**Known asymmetries, inherited and disclosed rather than removed** (they are part of the
comparison being replicated, identical in kind and size to seed 42's): the adversarial arms
carry the warm-up and a 14.7% summed-LR disadvantage; each stage's final epoch runs at lr 0
(upstream off-by-one, symmetric); the cold D exists only where a D exists.

## Runs and artifacts

Eight Kaggle training runs at stage 1 (seeds 43, 44 × arms C1, C2, C4, C5), arms in separate
sessions, checkpoints every epoch (standing practice 7: long detached runs checkpoint as they
go, so a session limit resumes rather than restarts). Per-seed evaluation through the committed
harness into `tubitak/data/tool_runs/C45_s{43,44}/`, per-chip CSV and summary JSON per seed —
**a per-chip artifact is written for every run**, which corrections-log entries 22 and 25 exist
to enforce.

Nothing in this package is launched until this registration is committed, pushed, and read.

## Evaluation — no new metrics

The seed-42 panel exactly, so the seeds are directly comparable: KARIOS positional residual on
ank130 (primary), edge-density ratio in input-silent regions, KLT surviving-point counts,
per-epoch reconstruction loss from the training logs. **No new metric is introduced by this
package**, and none may be added after the seeds are scored.
