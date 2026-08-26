# Registration — the sustained main-stage trend, at six seeds

Date: 2026-08-26, written and committed **before the seed-45–50 loss logs are downloaded
from the gencp-out Volume**. Standing practice 4 governs: no reading below is adjusted after
any curve has been seen. The disclosure block immediately following states, per seed,
exactly what had and had not been seen when this document was written.

## Why this registration exists

Corrections-log **entry 26**'s load-bearing argument is the **sustained main-stage trend** in
the generator reconstruction loss: neither adversarial arm reduces it, while both
non-adversarial arms reduce it by roughly 8%. That argument currently rests on **one run,
seed 42**. Entry 26 chose it over the two-epoch window precisely because the window was
confounded — and the warm-up de-confound
([warmup-deconfound-results.md](warmup-deconfound-results.md)) has since removed that
confound while leaving the window an unreliable per-arm signal. So the sustained trend now
carries more of the argument than it did, and it is still a single-seed observation.

The six-seed Modal block's loss logs exist on the Volume and have never been read. This
registration fixes the readings before they are.

---

## LABEL — prospective per seed, not as one word

A single-word label would be wrong in one direction or the other, so the label is stated per
seed.

| seed | status at the time this document was written | role |
|---|---|---|
| **45, 46, 47, 48, 49, 50** | **PROSPECTIVE. No curve read. No number known.** The logs are on the Volume, undownloaded. | **The confirmatory block, n = 6, df = 5.** The P = 1/64 arithmetic below is computed over these six and only these six. |
| **42** | **Fully seen.** C1 +1.16%, C2 −7.90%, C4 +2.50%, C5 −7.54%. | **Generating observation. Excluded from the confirmatory count.** Reported beside. |
| **43 Kaggle** | **Fully seen, and all four registered signs already observed to hold**: C1 +0.95%, C2 −5.16%, C4 +0.94%, C5 −8.00%. | Reported beside. **Never counted** — a different platform, NOT POOLED, and demoted to consistency by AMENDMENT SEED-c (f). |
| **43 Modal — C2, C4, C5** | **Unseen.** | Comparability, per the SEED-c (c) rule. |
| **43 Modal — C1** | **Partially seen: epochs 1–13**, from the container log recovered during the hardware gate. That range **includes the first main-stage epoch (33.466), one of the two endpoints of the registered quantity**, and excludes the last. | Comparability, but reported as a **PARTIALLY-INFORMED** value and labelled per arm. It is not an unseen check and may not be presented as one. |
| **43 Modal — C2_warmup, C5_warmup** | **Fully seen**: −2.98% and −5.32%. | Not among the four registered arms. Part of the warm-up package, reported there. |

**Nothing in this table is a caveat added after the fact.** It is the state of the record at
the moment of writing, and it is written before the download so that it can be checked
against the commit history rather than taken on trust.

### The sign justification, stated accurately

The four arm directions under test are **fixed by seed 42 and already observed to replicate
at seed 43 Kaggle.** They are **not** "fixed in advance by seed 42" alone, and this document
does not say so. Writing the shorter sentence would claim more innocence than the record
supports.

**P = 1/64 survives that correction unchanged**, and the reason is worth stating rather than
assuming: the probability is a statement about the sampling distribution of **six unseen
seeds** under a null of no treatment effect. Having seen other seeds beforehand fixes the
*direction* being tested — which is what a one-sided sign reading requires — but it does not
alter the distribution of the six draws that have not been taken. Prior sight would
invalidate the arithmetic only if it were prior sight **of these six**, and it is not. What
prior sight does cost is rhetorical, not statistical: this registration cannot claim that
the direction was a blind guess, and it does not.

### Why the prior sight happened — cause, not excuse

**The sight was mandated, not strategic.** Reading the seed-42 and seed-43 comparator curves
was a **required** part of the warm-up de-confound's registered secondary reading, which
specifies the relative first-to-last main-stage change "per arm" with "the un-warmed
counterparts" as the reference. That reading could not be executed without computing exactly
the quantity this document now registers, on exactly those comparator seeds. It was executed
on 26 August and is recorded in
[warmup-deconfound-results.md](warmup-deconfound-results.md).

The six-seed sustained-trend registration was conceived **afterward**. The supervising
session specified the warm-up secondary two prompts before specifying this registration, and
did not check that earlier instruction against the "before any download" condition when
writing it. The conflict is therefore an ordering oversight in the supervising instructions,
disclosed here plainly and attributed where it belongs. **No one chose to look first.**

### Why this is not labelled "retrospective"

Because it would be inaccurate, and inaccuracy in the humble direction is still inaccuracy.
Six seeds are genuinely unseen; every registered reading below is scored on those six; the
P = 1/64 arithmetic rests on nothing else. Calling that "retrospective" would misdescribe it.

It would also **debase a word this project uses precisely.** AMENDMENT C45-a is retrospective
in the full sense: a rule re-registered after the data that failed it were in hand, labelled
as such, with the original preserved and recorded FAILED. If "retrospective" also covers a
registration written before six unseen seeds are downloaded, the word stops distinguishing
those two situations, and the corrections log loses the ability to say which one it means.
**Labels are accurate in both directions or they carry no information.**

---

## The quantity

**Per-arm proportional change in the per-epoch generator reconstruction loss, from the first
to the last main-stage epoch, using each run's own main-stage window.**

- **Metric per arm**: `G_L1` for C1 and C2; `G_LPIPS` for C4 and C5, as printed in that
  arm's `loss_log.txt`. The two metrics are never compared across families; every reading
  below compares an arm to itself over time, or compares two arms sharing a metric.
- **Per-epoch value**: the arithmetic mean of every logged iteration within that epoch
  (279 logged iterations per epoch at this batch size and dataset).
- **Change**: (last main-stage epoch mean − first main-stage epoch mean) / first main-stage
  epoch mean, expressed as a percentage.
- **Main-stage window, per arm, and the epoch counts that travel with every number**:
  - **C1 and C4** carry a 2-epoch warm-up at lr 2e-5, then **18 main-stage epochs**
    (epochs 3–20 of 20). Their window is epochs 3 → 20.
  - **C2 and C5** carry no warm-up and have **20 main-stage epochs** (epochs 1–20). Their
    window is epochs 1 → 20.
  - The window is identified mechanically from the log: an arm whose `loss_log.txt` carries
    **two** `Training Loss` headers has a warm-up and its main stage begins at the second
    header; an arm with **one** header has no warm-up and its main stage begins at epoch 1.
    This is checked against the expected epoch counts above before any value is computed,
    and a mismatch is reported rather than resolved.

**The 18-versus-20 asymmetry is not equalised, and the epoch count is stated beside every
number.** This is the shape-reading decision already registered in
[warmup-deconfound-registration.md](warmup-deconfound-registration.md) and it is carried here
unchanged, for the same reason: the LR ladder is part of the arm definition, so no windowing
can equalise the schedules without deleting the thing being measured.

---

## Seeds and inference level

- **Confirmatory block: seeds 45, 46, 47, 48, 49, 50**, Modal, all four arms.
  **n = 6, df = 5, t\*(0.975, 5) = 2.571.**
- **Seed 42 is the generating observation and is excluded from the confirmatory count**, its
  values reported beside, with its standing code-path caveat attached (its C1/C2 trained
  19–20 August on an earlier build than its C4/C5).
- **Seed 43 Modal is reported beside under the SEED-c (c) comparability rule**, its position
  within the range spanned by the six confirmatory seeds checked and reported for every arm.
  **C1's value carries the PARTIALLY-INFORMED label** from the disclosure block above.
- **Seed 43 Kaggle is reported beside and never counted.** NOT POOLED; consistency only.
- **No pooled statistic anywhere.** One number per arm per seed; inference across seeds.

---

## REGISTERED READINGS — sign replication, distribution-free

Scored on the six confirmatory seeds only.

1. **C1's change is POSITIVE in all six seeds** (the L1 adversarial arm fails to reduce its
   reconstruction loss). **P = 1/64.**
2. **C4's change is POSITIVE in all six seeds** (the LPIPS adversarial arm fails to reduce
   its reconstruction loss). **P = 1/64.**
3. **C2's change is NEGATIVE in all six seeds.** **P = 1/64.**
4. **C5's change is NEGATIVE in all six seeds.** **P = 1/64.**
5. **The adversarial-minus-non-adversarial gap is POSITIVE in all six seeds, within each
   reconstruction family** — C1 − C2 on this quantity, and C4 − C5 on this quantity.
   **P = 1/64.**

Each P is computed over the six unseen seeds with the direction fixed as described above.

### The fifth reading is ENTAILED by the first four and adds no evidence

Stated here, before the numbers, so it is not later mistaken for a fifth independent
confirmation. **If C1's change is positive in all six and C2's is negative in all six, then
C1 − C2 is positive in all six as a matter of arithmetic**, and the same holds for C4 − C5.
Reading 5 can therefore only fail in a way readings 1–4 have not already failed, and it can
never pass independently of them.

It is registered anyway because **the gap is the quantity the manuscript will state**, and a
quantity the paper reports should have a registered reading rather than being assembled from
two others after the fact. But its P = 1/64 is **the same 1/64 as readings 1 and 3**, not an
additional one, and no multiplicity argument may treat the five readings as five independent
tests. A reader should count **four** sign readings here, of which the fifth is a restatement.

### Intervals

**Seed-level t-intervals (df = 5, t\* = 2.571) are computed and printed for every arm and
every gap. They are REPORTED, NOT REQUIRED.** No interval is a gate. An interval that
includes zero is not a failed reading, and an interval that excludes zero does not pass a
reading whose criterion is sign stability. This is the same rule SEED-c attaches to the
positional contrasts, and it binds in both directions.

---

## THE CONSEQUENCE — decided now, both branches written before any curve is downloaded

**IF both adversarial arms' changes are positive in all six seeds** (readings 1 and 2 hold):
entry 26's sustained-trend argument is a **replicated result** at n = 6. The manuscript may
state that adversarial arms fail to reduce the reconstruction loss as a general finding of
this design, with the seed count, the epoch counts and the n = 6 attached, and with the
warm-up-matched comparator required by
[warmup-deconfound-results.md](warmup-deconfound-results.md) rather than the uncontrolled
one.

**IF either adversarial arm's change is NOT positive in all six seeds**: entry 26's
sustained-trend argument **is no longer a replicated result**. It is reported as a
**seed-42 observation**, with the six-seed counts printed beside it and the failing seed
named and its value printed, never dropped. **The manuscript does not assert that adversarial
arms fail to reduce the reconstruction loss as a general finding.** The observation may still
appear in the mechanism discussion, labelled as a single-seed observation that did not
replicate at six.

**Nothing already disclosed is withdrawn under either branch.** Entry 26's record of what was
observed at seed 42, and the reasoning it recorded, stand as the historical record in both
cases; what changes is only what the manuscript is entitled to assert.

**If readings 3 or 4 fail** (a non-adversarial arm fails to reduce its loss in some seed):
that seed is named and its value printed, the "roughly 8%" figure is replaced by the observed
six-seed range, and the failure is reported in the same sentence as any statement of the
gap. It does not on its own withdraw the adversarial-arm finding, which readings 1 and 2
govern.

---

## What this reading CANNOT do

**It is a training-dynamics reading, not a positional one.** It measures what happens to a
loss curve during training. It says nothing directly about positional residuals on the
evaluation chips.

- It **supports the mechanism discussion** and nothing more.
- It **enters no registered positional contrast**. It does not touch the primary
  (C5 − C4), the secondary (C5 − C2), the main effects, or the edge-ratio mechanism
  readings, and it cannot repair, reinforce or substitute for the failed interaction reading
  recorded in [seed-block-results.md](seed-block-results.md).
- It is **not evidence about matchability**. A reconstruction loss that fails to fall is a
  fact about the optimisation, and the step from there to "the generator invents structure"
  is an interpretation carried by the edge-ratio measurement, not by this curve.
- The **collinearity this quantity was once confounded by has been broken but not
  eliminated**: the warm-up de-confound tested it at n = 1 seed, and its comparator
  requirement — adversarial-with-warm-up against non-adversarial-with-warm-up — applies to
  any magnitude stated from this reading.

---

## Analysis procedure, fixed before the download

So that no step is chosen after seeing a curve:

1. Download `loss_log.txt` for all four arms of seeds 45–50 (24 files) and seed 43 (4 files)
   from the gencp-out Volume. **Volume reads only — zero GPU.**
2. Record the sha256 of every file and commit all of them into `docs/gates/`, for the reason
   the warm-up logs were committed there: evidence for a registered reading does not live one
   cleanup away from gone.
3. **If any file is absent from the Volume, name it and stop.** No substitution of a
   different seed, arm or platform to fill a gap.
4. Parse per-epoch means with the header-counting window rule above; assert 279 iterations
   per epoch and the expected epoch counts per arm; report any mismatch rather than
   resolving it.
5. Compute the five readings, the sign tallies, and the t-intervals; report each outcome
   against the branch text above.
6. Report seeds 42, 43 Modal and 43 Kaggle beside the block with their labels from the
   disclosure table, never inside the count.

Nothing in this package is downloaded until this registration is committed and pushed.
