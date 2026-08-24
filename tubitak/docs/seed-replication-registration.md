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
| hardware and image | Kaggle T4, same image, same torchmetrics 1.9.0 (recorded from each log and reported) |
| data source | OSM/CLC+ archived **OVP** evaluation inputs — the same files seed 42 used |
| render path | none; no rendering occurs in this package, the inputs are archived rasters |
| code path | the current build for **all** new runs; the seed-42 C1/C2 exception is the disclosed one above |
| determinism | none claimed — the **STOCH** dropout-active path throughout, single draw, as in seed 42 |
| evaluation harness | `tubitak/scripts/c45_eval/`, committed at `40cde9b`, unmodified; any change to it before or during this package invalidates the comparison and must be registered |
| evaluation set | the same 130 Ankara chips, same warp geometry (GSD 10.0390625, 228-grid), same BT.601 conversion |
| matcher | KARIOS, config `karios_gencp.json`, sha256 `8eaa5bd8cdae066d2580a4105169262f873523cadf0b450a8aa134a31ed4ca84` |
| inference | STOCH single draw per chip per arm per seed, **dropout shim `_shims/s42` for every training seed** — see AMENDMENT SEED-a below |

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
