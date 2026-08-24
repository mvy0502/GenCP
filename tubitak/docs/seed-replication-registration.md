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

**The statistical weakness of this design, stated now rather than discovered later.** With
three seeds a t-interval has **two degrees of freedom**; the 95% multiplier is 4.30 against
1.96 asymptotically, so the interval will be wide and will very likely include zero even if
the effect is real and large. Five seeds (stage 2) gives four degrees of freedom and a
multiplier of 2.78 — better, still weak. **This package cannot deliver a tight seed-level
interval and is not designed to.** Therefore:

- **Sign consistency is the stage-1 read.** Does the effect point the same way in every
  independently trained replicate? That is a binary, distribution-free question that three
  seeds can answer, and under a null of no effect the chance of three matching signs is 1/4.
- **The interval is the stage-2 read**, and even there it is reported with its degrees of
  freedom in the sentence, not in a footnote.

A wide interval at stage 1 is an expected outcome and will not be described as a null result.

## Registered readings

All contrasts are seed-level means of per-chip paired differences, on the ank130 panel,
STOCH single draw, OVP inputs.

**Primary.** C5 − C4 **negative in all three seeds** at stage 1. At stage 2: negative in **at
least four of the five seeds**, with the seed-level interval excluding zero.

**Main effect (both reconstruction terms).** C1 − C2 > 0 **and** C4 − C5 > 0 **in every
seed**. This is the adversarial penalty stated as the design factor it is, once under each
reconstruction term.

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

**Secondary.** C5 − C2 **positive in every seed** — the LPIPS-alone positional penalty.

**Mechanism.** Edge ratio in input-silent regions, computed per seed for all four arms under
the definition already implemented in `c45_eval/c45_edge_ratio.py`: **C5 highest or tied
highest in every seed**, and **C2 below 0.5 in every seed**. Reported per seed, not pooled.

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

## Registered consequences — verbatim, decided before the numbers exist

- **If the interaction is not sign-stable across seeds:** *"the same lever", "substitutes" and
  the word "interaction" are dropped from the paper and the adversarial main effect is
  published alone.*
- **If C5 − C2 is not positive in every seed:** *the LPIPS-alone penalty moves from a result to
  a discussion-section hypothesis and the claim narrows from "plausibility pressure" to "the
  adversarial term".*
- **If the primary is not negative in all three seeds at stage 1:** *stage 2 is not launched on
  this design; the package is re-planned and the failure reported.*
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

These runs are the **first genuine test of C45-a**, on curves nobody has seen. The rule: *the
run stops if the per-epoch reconstruction loss rises more than 10% above the lowest value seen
so far in the main stage (running minimum), sustained over two consecutive epochs.* The sharp
half — a generator-loss spike in the first few hundred iterations, the cold-D signature —
is unchanged.

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
| inference | STOCH single draw per chip per arm per seed |

**The one thing that is not identical: the training seed**, and through it the cold-D draw in
the adversarial arms. That is the manipulated factor.

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
