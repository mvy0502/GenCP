# SEED-c six-seed Modal block — registered readings applied

Written 26 August 2026, the morning after the block completed. Inputs are the frozen
per-seed evaluations of seeds 45–50 (`tubitak/data/tool_runs/C45_s{45..50}_modal/`), scored
through the pre-committed analysis script `tubitak/scripts/seed_eval/seed_analysis.py`
(commit `6418febc`, sha256 `d22053e1…`, committed before any seed was scored). The block's
numbers were first tabulated overnight without interpretation in
[gates/seed-block-morning-report.md](gates/seed-block-morning-report.md) §6; every value
there is reproduced here by the frozen script and matches.

Registration: [seed-replication-registration.md](seed-replication-registration.md),
AMENDMENT SEED-c (committed `9ab599e`, 25 August 2026, before any seed-45–50 run launched).
n = 6, df = 5, t*(0.975, 5) = 2.571.

**This document is not a corrections-log entry, and none is filed for it.** A registered
consequence executing as written is the system working as designed, not a correction to it.

**One note on how the script was run.** The frozen script reads `C45_s{seed}/`; the Modal
runs live in `C45_s{seed}_modal/`. Rather than edit code that the registration freezes, it
was run through its own `--root` argument against a scratch directory of symlinks pointing
at the real `_modal` directories. The script is byte-unchanged (`dirty: false`), and its
provenance block pins the sha256 of every CSV actually read — those hashes match the ones
recorded in the overnight log.

---

## 1. Outcome of each registered reading

Per SEED-c (d). All are sign-replication readings, distribution-free.

| registered reading | outcome | count | note |
|---|---|---|---|
| **PRIMARY** — C5 − C4 negative in all six | **HELD** | 6/6 | P = 1/64 under the null, direction fixed in advance by seed 42 |
| **SECONDARY** — C5 − C2 positive in all six | **HELD** | 6/6 | P = 1/64; smallest margin +0.0068 at seed 46 |
| C1 − C2 positive in all six | **HELD** | 6/6 | |
| C4 − C5 positive in all six | **HELD** | 6/6 | |
| I_raw negative in all six | **FAILED** | 5/6 | seed 46 = **+0.0594** |
| edge C2 mean < 0.5 in all six | **HELD** | 6/6 | |
| edge C5 mean highest of the four fine-tuned arms in all six | **HELD** | 6/6 | registered tie rule applied per seed; C5 is strictly higher against every competitor in every seed, never merely tied |

### Per-seed values, raw scale

| seed | C5 − C4 | C1 − C2 | C4 − C5 | C5 − C2 | I_raw |
|---|---|---|---|---|---|
| 45 | −0.6153 | +0.6749 | +0.6153 | +0.0619 | −0.0597 |
| 46 | −0.6462 | +0.5868 | +0.6462 | **+0.0068** | **+0.0594** |
| 47 | −0.6162 | +0.7010 | +0.6162 | +0.0665 | −0.0847 |
| 48 | −0.5942 | +0.7544 | +0.5942 | +0.0799 | −0.1602 |
| 49 | −0.6054 | +0.7024 | +0.6054 | +0.1085 | −0.0970 |
| 50 | −0.5775 | +0.6444 | +0.5775 | +0.0519 | −0.0669 |

### Per-seed edge-ratio means (the registered statistic: per-arm mean of the 130 per-chip ratios)

| seed | pretrained | C1 | C2 | C4 | C5 |
|---|---|---|---|---|---|
| 45 | 1.0208 | 1.0845 | 0.2791 | 1.1173 | 1.1442 |
| 46 | 1.0208 | 1.0768 | 0.2713 | 1.1207 | 1.1511 |
| 47 | 1.0208 | 1.0951 | 0.2844 | 1.1267 | 1.1484 |
| 48 | 1.0208 | 1.0828 | 0.2727 | 1.1251 | 1.1607 |
| 49 | 1.0208 | 1.1203 | 0.2765 | 1.1314 | 1.1557 |
| 50 | 1.0208 | 1.0718 | 0.2790 | 1.1438 | 1.1504 |

Medians are carried in `seed_per_seed.csv` beside every mean and must never be interchanged
with them (corrections-log entry 24).

### Seed 46 is REPORTED and NEVER DROPPED

Per the registration's own rule, the seed that breaks a reading is named, its value printed,
and the reading reported as failed — it is not removed, down-weighted, or set aside pending
a re-run.

**An observation about seed 46, stated as an observation.** Seed 46 is both the only seed
with a positive I_raw (+0.0594) and the seed with the smallest C5 − C2 (+0.0068). Both of
its unusual values come from the same place arithmetically: its C2-relative gaps are
compressed relative to the other five seeds — C1 − C2 is its smallest (+0.5868 against a
six-seed range up to +0.7544) and C5 − C2 is its smallest (+0.0068). Since
I_raw = (C4 − C5) − (C1 − C2), a compressed C1 − C2 raises I_raw directly.

**No explanation is offered for why seed 46's C2-relative gaps are compressed, and none
should be constructed here.** Seed 46 was also the seed whose driver chain ran roughly 50
minutes behind its siblings; that lag is documented in the morning report as container
queueing between arms, with per-arm GPU seconds indistinguishable from the other seeds, and
it is recorded here only so that a reader who notices it in the logs does not have to
wonder whether it was concealed. Connecting it to the numbers would be a post-hoc
mechanism built from a single seed.

---

## 2. Why the interaction reading failed, and why the failure is not a choice made after the fact

**The registered interaction reading is a conjunction.** From the registration
([seed-replication-registration.md:239](seed-replication-registration.md)): the interaction
is read as *negative at seed level* **AND** *negative after a monotone re-scaling*.

**The first conjunct's original phrasing admitted two readings.** "Negative at seed level"
can mean *negative in every seed* or *the seed-level mean is negative*. These do not agree
on this block:

- **All six seeds negative:** 5/6. **Fails.**
- **Seed-level mean negative:** mean I_raw over the six seeds = **−0.0682**. This
  **would have passed.**

The second number is printed here deliberately. A reader is entitled to know exactly what
the alternative reading would have delivered, so that the choice between readings can be
audited rather than trusted.

**The ambiguity is already resolved, and it was not resolved by us today.** AMENDMENT
SEED-c (d), committed at **`9ab599e` on 25 August 2026, before any seed-45–50 run was
launched**, restates the reading for this block's n as:

> C1 − C2 positive in all six; C4 − C5 positive in all six; **I_raw negative in all six**;
> C2's edge mean below 0.5 and C5's edge mean the highest of the four arms in all six.

That is the binding wording at n = 6. It says *in all six*. It is 5/6. **The first conjunct
fails, so the conjunction fails, and no property of the second conjunct can change that.**

**The two-way ambiguity in the original stage-2 phrasing was noticed only after the 5/6
result was known.** That is precisely the moment at which re-reading the phrase in the
direction that passes becomes forbidden, whatever its merits as English. The timing is
recorded here because the timing is the whole point: a rule re-read after seeing which way
it cuts is indistinguishable from a rule adjusted to pass.

**Standing treatment, cited rather than invented.** This is the same situation the hardware
gate already faced and already settled.
[hardware-gate-results.md](hardware-gate-results.md) records a specification flaw in that
gate's acceptance rule and disposes of it in these terms: the flaw *"was noticed only after
seeing which quantity failed — precisely the moment at which fixing it is forbidden"*, so
the flaw was recorded, the post-hoc timing of noticing it was recorded, and the verdict
stood unchanged under the rule as written. The same disposal applies here. The ambiguity is
recorded, the timing is recorded, and the reading stands failed under the wording as
committed.

The forward fix, for future registrations rather than this one: a sign-replication reading
states *in all N* or *the mean across N* explicitly, never "at seed level".

---

## 3. The two monotone re-scalings

**Read this before the numbers below.** The log and rank transforms are computed here
because the registration requires them to be computed and reported, and because the paper
should show what a monotone re-scaling does to a contrast whose raw scale has a floor at
zero. **They are not computed to re-test a reading whose first conjunct has already
failed.** Whatever they show, the interaction reading stays **FAILED**.

### Definitions, exactly as registered

- **I_log** = (ln C4 − ln C5) − (ln C1 − ln C2), per chip, averaged per seed. Chips with a
  zero or non-finite residual in any of the four arms are excluded pairwise (the whole chip
  drops, since the contrast needs all four), and the exclusion count is reported per seed.
  If a seed loses more than 5 of its 130 chips this way, the log transform is reported
  **unusable for that seed** rather than silently thinned.
- **I_rank** = (rank C4 − rank C5) − (rank C1 − rank C2), where the four arms are ranked
  1–4 within each chip by residual (1 = best), ties by mid-rank, averaged per seed.

**Exclusions: zero chips dropped in every one of the six seeds** (s45 = 0, s46 = 0,
s47 = 0, s48 = 0, s49 = 0, s50 = 0). All 130 chips enter the log transform in all six
seeds. The "unusable" branch of the registered rule does not fire anywhere in this block,
and no seed is thinned.

### All three scales side by side

| seed | I_raw | I_log | I_rank | log chips dropped |
|---|---|---|---|---|
| 45 | −0.0597 | −0.0470 | −0.1846 | 0 |
| 46 | **+0.0594** | **+0.0118** | **+0.1231** | 0 |
| 47 | −0.0847 | −0.0615 | −0.1385 | 0 |
| 48 | −0.1602 | −0.1262 | −0.2462 | 0 |
| 49 | −0.0970 | −0.0895 | −0.2615 | 0 |
| 50 | −0.0669 | −0.0526 | −0.2154 | 0 |
| **sign tally (negative in all six?)** | **5/6 — NO** | **5/6 — NO** | **5/6 — NO** | |

**The same seed breaks all three scales.** Seed 46 is positive on the raw scale, on the log
scale and on the rank scale. The monotone re-scalings do not rescue the reading and they do
not independently condemn it: they reproduce it. Sign stability across seeds is absent on
every scale the registration named.

This also removes a question a reader might otherwise ask. The registration's stated reason
for requiring a monotone re-scaling was that sub-additivity on a raw scale with a floor at
zero is the null expectation, so the raw scale alone cannot be read as mechanistic. On this
block that argument never gets to do any work: the raw scale did not deliver the sign in
the first place, and neither transform does either.

**Frozen-script verdict, quoted from its own output:** `REGISTERED INTERACTION READING (raw
negative AND at least one monotone re-scaling negative): FAILS`.

---

## 4. The registered consequence, executed

The consequence, reproduced verbatim from the registration's "Registered consequences"
section:

> **If the interaction is not sign-stable across seeds:** *"the same lever", "substitutes"
> and the word "interaction" are dropped from the paper and the adversarial main effect is
> published alone.*

The interaction is not sign-stable across seeds on any registered scale. **The consequence
fires.**

**What survives.** The adversarial main effect is published alone: the primary
(C5 − C4 negative 6/6), both main-effect contrasts (C1 − C2 and C4 − C5 positive 6/6), the
secondary (C5 − C2 positive 6/6, which fired and therefore does **not** trigger its own
narrowing consequence — the "plausibility pressure" framing and the title survive that
reading intact), and the mechanism readings (C2 edge mean below 0.5, C5 highest, 6/6 each).

**What does not survive as a claim.** The interaction as a mechanistic result, the
"substitutes" band language, and the "same lever" / "two pressures act on one lever"
formulation.

**No file has been edited to execute this.** §6 below is the review list of every place the
three terms appear in a claim sense; the edits happen after that list is reviewed.

### Ruling on the edge-scale interaction, recorded now before anyone is tempted by it

The quantity (edge C4 − edge C5) − (edge C1 − edge C2) is strikingly stable across the
block:

| seed | 45 | 46 | 47 | 48 | 49 | 50 | mean |
|---|---|---|---|---|---|---|---|
| edge-scale interaction | −0.8323 | −0.8359 | −0.8324 | −0.8456 | −0.8681 | −0.7994 | **−0.8356** |

Negative in all six, spread 0.069, and negative in seed 43 on both platforms (−0.8224
Modal, −0.8374 Kaggle) and in seed 42 (−0.8526) as well.

**It is ruled out as a substitute for the failed positional interaction, now, in advance of
anyone proposing it.** The reasons:

1. **It is not a registered reading.** The registered mechanism readings are the per-arm
   edge ratio and its two thresholds — C2's mean below 0.5, and C5's mean highest of the
   four arms. An edge-scale interaction appears in no registration in this package.
2. **It is a different quantity on a different metric.** The failed reading is about
   positional residuals in pixels. This is about edge density in input-silent regions. A
   sign that replicates on the second says nothing about the first, and swapping one for
   the other after the first failed is exactly the substitution-of-a-different-test failure
   [phase-c-audit.md](phase-c-audit.md) already scored against this project once.
3. **Its stability is partly structural.** C2's edge mean sits near 0.28 while the other
   three arms sit near 1.08–1.16, so the C1 − C2 term is dominated by one arm's very
   different level in every seed. Stability of a difference driven by a level gap that
   large is not, on its own, evidence of a mechanism.

**Ruling: if this quantity appears in the paper at all, it appears in the discussion,
explicitly labelled a post-hoc observation, and never as the interaction result or as
evidence for "the same lever".** It may not be promoted to a result by a later document
without a fresh, dated registration written before the number is looked at again — and the
number has now been looked at, which means any such registration must say so.

---

## 5. The remaining registered analysis

### (a) Seed-level t-intervals, df = 5, t* = 2.571

**These intervals are REPORTED, NOT REQUIRED.** Per SEED-c (d): no interval is a gate. An
interval that includes zero is **not** a failed reading, and an interval that excludes zero
does **not** rescue a failed one. The registered readings are the sign replications in §1
and only those. Both directions of that sentence matter in this block, and the interaction
rows below are exactly why.

| scale | contrast | mean | sd | 95% CI (df = 5, t* = 2.571) | contains zero |
|---|---|---|---|---|---|
| raw | C5 − C4 | −0.6091 | 0.0233 | [−0.6335, −0.5847] | no |
| raw | C1 − C2 | +0.6773 | 0.0573 | [+0.6172, +0.7374] | no |
| raw | C4 − C5 | +0.6091 | 0.0233 | [+0.5847, +0.6335] | no |
| raw | C5 − C2 | +0.0626 | 0.0336 | [+0.0273, +0.0979] | no |
| raw | I | −0.0682 | 0.0720 | [−0.1438, +0.0074] | **yes** |
| log | C5 − C4 | −0.3995 | 0.0175 | [−0.4179, −0.3811] | no |
| log | C1 − C2 | +0.4603 | 0.0338 | [+0.4249, +0.4958] | no |
| log | C4 − C5 | +0.3995 | 0.0175 | [+0.3811, +0.4179] | no |
| log | C5 − C2 | +0.0778 | 0.0226 | [+0.0541, +0.1015] | no |
| log | I | −0.0608 | 0.0461 | [−0.1092, −0.0125] | no |
| rank | C5 − C4 | −1.5526 | 0.0518 | [−1.6069, −1.4982] | no |
| rank | C1 − C2 | +1.7064 | 0.1244 | [+1.5759, +1.8369] | no |
| rank | C4 − C5 | +1.5526 | 0.0518 | [+1.4982, +1.6069] | no |
| rank | C5 − C2 | +0.2500 | 0.1027 | [+0.1422, +0.3578] | no |
| rank | I | −0.1538 | 0.1427 | [−0.3036, −0.0041] | no |
| edge | C1 mean | 1.0886 | 0.0175 | [1.0702, 1.1069] | — |
| edge | C2 mean | 0.2772 | 0.0048 | [0.2722, 0.2822] | — |
| edge | C4 mean | 1.1275 | 0.0093 | [1.1177, 1.1373] | — |
| edge | C5 mean | 1.1517 | 0.0058 | [1.1457, 1.1578] | — |

**The interaction rows are the case the "reported, not required" rule was written for.** The
log-scale and rank-scale interaction intervals **exclude zero**, and the raw-scale one does
not. None of that is a reading. The registered reading is sign stability across seeds; it is
5/6 on all three scales; the consequence in §4 fires. **An interval excluding zero is not a
gate and does not reopen a failed sign reading** — reading it that way would be the same
error as reading a zero-containing interval as a failed gate, in the opposite direction, and
the registration forbids both by forbidding the interval as a gate at all.

For completeness, the per-seed values on the two transformed scales for the non-interaction
contrasts:

| contrast | s45 | s46 | s47 | s48 | s49 | s50 |
|---|---|---|---|---|---|---|
| log C5 − C4 | −0.4006 | −0.4194 | −0.4202 | −0.3778 | −0.3852 | −0.3937 |
| log C1 − C2 | +0.4476 | +0.4077 | +0.4816 | +0.5040 | +0.4747 | +0.4463 |
| log C5 − C2 | +0.0704 | +0.0465 | +0.0751 | +0.0932 | +0.1124 | +0.0694 |
| rank C5 − C4 | −1.5385 | −1.5846 | −1.6385 | −1.5000 | −1.5462 | −1.5077 |
| rank C1 − C2 | +1.7231 | +1.4615 | +1.7769 | +1.7462 | +1.8077 | +1.7231 |
| rank C5 − C2 | +0.2154 | +0.0769 | +0.2615 | +0.2538 | +0.3846 | +0.3077 |

### (b) Seed 43 (Modal) comparability, per SEED-c (c)

Modal seed 43 is **excluded from the confirmatory n** — it is the gate seed, and its
contrasts are already published in [hardware-gate-results.md](hardware-gate-results.md), so
it is a seen observation for exactly the quantities this block tests. It is reported beside
the block, and its position within the range spanned by the six confirmatory seeds is
checked for every primary quantity.

| quantity | seed 43 (Modal) | six-seed range | position |
|---|---|---|---|
| C5 − C4 | −0.5292 | [−0.6462, −0.5775] | **outside**, above the top by 0.0483 = 0.70× the range width |
| C1 − C2 | +0.6473 | [+0.5868, +0.7544] | inside |
| C4 − C5 | +0.5292 | [+0.5775, +0.6462] | **outside** (the mirror of the row above), by 0.0483 |
| C5 − C2 | +0.1086 | [+0.0068, +0.1085] | **outside by 0.0001** — effectively on the top edge; seed 49 is +0.1085 |
| I_raw | −0.1181 | [−0.1602, +0.0594] | inside |
| I_log | −0.0771 | [−0.1262, +0.0118] | inside |
| I_rank | −0.2462 | [−0.2615, +0.1231] | inside |
| edge C1 mean | 1.0650 | [1.0718, 1.1203] | **outside**, below the bottom by 0.0068 = 0.14× the range width |
| edge C2 mean | 0.2803 | [0.2713, 0.2844] | inside |
| edge C4 mean | 1.1207 | [1.1173, 1.1438] | inside |
| edge C5 mean | 1.1584 | [1.1442, 1.1607] | inside |

**Reading, kept to what the numbers support.** Seed 43's adversarial main effect under
LPIPS is milder than any of the six confirmatory seeds, by two-thirds of the width they
span; its C5 − C2 sits at the very top edge; its C1 edge mean is marginally below the block.
Its signs all agree with the block. Nothing here is a gate — SEED-c (c) asks for the
position to be checked and reported, and that is what this table is. Seed 43's edge C1 was
also the single quantity that failed the hardware gate (4.2× its seed spread across
platforms), so its position outside the block on that same quantity is consistent with what
the gate already recorded and should not be read as a second, independent finding.

### (c) Seed 42 comparability, per the existing rule

Seed 42 is the **generating observation, not a replicate** — the direction under test was
read off it, so it cannot confirm it. Its position within the six-seed range:

| quantity | seed 42 | six-seed range | position |
|---|---|---|---|
| C5 − C4 | −0.4871 | [−0.6462, −0.5775] | **outside**, above the top by 0.0904 = 1.31× the range width |
| C1 − C2 | +0.6995 | [+0.5868, +0.7544] | inside |
| C4 − C5 | +0.4871 | [+0.5775, +0.6462] | **outside** (mirror), by 0.0904 |
| C5 − C2 | +0.1025 | [+0.0068, +0.1085] | inside |
| I_raw | −0.2123 | [−0.1602, +0.0594] | **outside**, below the bottom by 0.0521 |
| I_log | −0.1125 | [−0.1262, +0.0118] | inside |
| I_rank | −0.4154 | [−0.2615, +0.1231] | **outside**, below the bottom by 0.1538 |
| edge C1 mean | 1.0965 | [1.0718, 1.1203] | inside |
| edge C2 mean | 0.2839 | [0.2713, 0.2844] | inside |
| edge C4 mean | 1.1194 | [1.1173, 1.1438] | inside |
| edge C5 mean | 1.1594 | [1.1442, 1.1607] | inside |

**Seed 42 has the largest-magnitude interaction of any seed in the package, on the raw and
rank scales alike, and it sits outside the confirmatory range on both.** The interaction
result that the paper currently carries (I = −0.212 ± 0.069, t = −3.07) is seed 42's value,
with a chip-level error bar. The six confirmatory seeds put it outside their own spread.
This is the correction the whole SEED-c package exists to make, arriving on the one quantity
whose consequence fires: a single-cell contrast with a chip-level ± was carrying a claim,
and at seed level the sign does not hold up.

Seed 42's code-path caveat (its C1/C2 trained 19–20 August on an earlier build than its
C4/C5) remains attached to every seed-42 number and is not resolved by this block.

### (d) The Kaggle block, reported separately — consistency only, per SEED-c (f)

The Kaggle confirmatory block closed at **n = 2** (seeds 43 and 44), **df = 1,
t* = 12.71**. Its role is **consistency, not inference**. **No pooled statistic appears
anywhere in this document or in the manuscript**: the Modal block and the Kaggle block are
never combined, because the hardware gate returned NOT POOLED.

| contrast | s43 | s44 | mean | 95% CI **at df = 1, t\* = 12.71** |
|---|---|---|---|---|
| C5 − C4 | −0.5485 | −0.5847 | −0.5666 | [−0.7964, −0.3367], **df = 1** |
| C1 − C2 | +0.6636 | +0.6404 | +0.6520 | [+0.5046, +0.7995], **df = 1** |
| C4 − C5 | +0.5485 | +0.5847 | +0.5666 | [+0.3367, +0.7964], **df = 1** |
| C5 − C2 | +0.1275 | +0.0530 | +0.0902 | [−0.3831, +0.5636], **df = 1** |
| I_raw | −0.1151 | −0.0558 | −0.0855 | [−0.4629, +0.2920], **df = 1** |
| I_log | −0.0921 | −0.0680 | −0.0801 | [−0.2332, +0.0731], **df = 1** |
| I_rank | −0.3538 | −0.2154 | −0.2846 | [−1.1645, +0.5953], **df = 1** |

Kaggle edge-ratio means: s43 C1 1.0827 / C2 0.2788 / C4 1.1206 / C5 1.1541; s44 C1 1.0785 /
C2 0.2853 / C4 1.1224 / C5 1.1440. Log-transform exclusions: 0 chips in both seeds.

**The Kaggle block's interaction is negative in both its seeds, on all three scales. It does
not and cannot rescue the failed Modal reading.** Three reasons, all of them registered
before the numbers existed: the two blocks may never be pooled (hardware gate: NOT POOLED);
the Kaggle block's role was demoted to consistency by SEED-c (f); and the confirmatory
count for these readings is the six-seed Modal block, n = 6, by SEED-c (b). Two seeds
agreeing on a direction, at df = 1 with intervals this wide, is the situation the six-seed
block was commissioned to replace. It is reported because the registration says report both
blocks, and for no other purpose.

### (e) Cost reconciliation

The **$1.10 per GPU-hour constant used by the drivers understates the true cost by a factor
of 1.13**, i.e. an effective **≈ $1.25 per GPU-container-hour**. Modal bills CPU cores and
memory on top of the GPU rate, and the driver containers themselves accrue while sequencing
arms. Every driver-computed `usd` figure in this package's records carries that
understatement.

- Settled dashboard usage this cycle: **$53.00**.
- Out-of-pocket (after credits): **$23.00**.
- Settled wave cost: 53.00 − 11.77 (launch baseline) = **$41.23** against the
  driver-computed **$36.33** → ratio **1.13**.

The ×1.38 / $1.52-per-hour figures in
[gates/seed-block-morning-report.md](gates/seed-block-morning-report.md) §3 were the live
estimate read at 04:01 while containers were still open; they were superseded by the settled
figures at 05:03 and are kept there rather than edited away. **The settled reconciliation is
×1.13, ≈ $1.25 per GPU-container-hour**, and that is the figure the paper's compute
statement should use.

---

## 6. Review list for the consequence — not yet applied

Every place the three terms appear in a **claim** sense, for review before any edit. Places
where the terms appear **inside a registration describing the test itself**, or inside an
audit/correction record of what was claimed at the time, are listed separately and **stay
unchanged**: they are the historical record, and rewriting them would erase the evidence
that the consequence was pre-committed and honoured.

Nothing in this section has been edited.

### 6.1 Claim-sense occurrences — candidates for the consequence

| file | line | text | why it is claim-sense |
|---|---|---|---|
| [paper-context-addendum.md](paper-context-addendum.md) | 41 | "…and they act on the **same lever**." | The closing clause of **the paper's stated claim**, quoted as a block at the head of the document. This is the load-bearing one. |
| [paper-context-addendum.md](paper-context-addendum.md) | 104–107 | "**Interaction — substitutes.** … Interaction I = −0.212 ± 0.069 (t = −3.07). LPIPS already supplies part of the plausibility pressure…" | Reports the interaction as a result, with a chip-level error bar, in the results summary the paper draws from. |
| [paper-context-addendum.md](paper-context-addendum.md) | 592–593 | "What the factorial adds and the theory lacks is *substitutability between sources of plausibility pressure*, which is what the **interaction** term measures." | Positions the interaction as this work's contribution against Blau–Michaeli. Claim-sense, in the related-work argument. |
| [paper-roadmap.md](paper-roadmap.md) | 138–139 | "**Interaction: −0.212 ± 0.069, t = −3.07**, the registered *substitutes* band." | The GRSL letter's scope decision lists the interaction as spine content. |
| [phase-c-lpips-results.md](phase-c-lpips-results.md) | 12–15 | "…the **interaction** lands in the registered *substitutes* band (t = −3.07)… the two pressures act on the **same lever**, not additively." | The headline paragraph of the results document. Both terms, both claim-sense. |
| [phase-c-lpips-results.md](phase-c-lpips-results.md) | 88–94 | "**INTERACTION — substitutes, the richer mechanistic result.** … two mechanisms, one lever." | The full interaction result section. |
| [related-work.md](related-work.md) | 90–94 | "…says nothing about *substitutability between sources of plausibility pressure*. The **interaction** term (I = -0.212 +/- 0.069) is a measurement of exactly that… supporting citation for the '**same lever**' half of the claim." | Builds the citation strategy on the interaction and names the "same lever" half of the claim explicitly. |
| [phase-c-audit.md](phase-c-audit.md) | 125–127 | "**Interaction reproduces**: … ≥ 2 SE → *substitutes*, as reported." | Audit **verdict** affirming the interaction as reproduced — a claim about a result, not a description of the test. Borderline; flagged for your call. |
| [phase-c-audit.md](phase-c-audit.md) | 443, 455 | "…the **interaction**, the dose-response and the edge-ratio…" / "**Quotable as:** the primary result, the **interaction**, …" | Lists the interaction among the quotable results. The "quotable as" line is directly claim-sense. |
| [scripts/c45_eval/c45_score.py](../scripts/c45_eval/c45_score.py) | 100 | `i_band = "substitutes (I < 0 at >=2 SE, D_LPIPS > 0 at >=2 SE): LPIPS already supplies the pressure"` | Emits the claim wording as scored output. Code, so an edit here is a code change with its own freeze considerations — see 6.3. |

### 6.2 Registration / historical-record occurrences — these stay

| file | line | what it is |
|---|---|---|
| [seed-replication-registration.md](seed-replication-registration.md) | 40–44 | Records that the interaction has no run-level error bar — the reason this package exists. |
| [seed-replication-registration.md](seed-replication-registration.md) | 239–255 | The registered interaction reading and both transforms, including "'The same lever' requires the sign to survive at least one monotone re-scaling". |
| [seed-replication-registration.md](seed-replication-registration.md) | 304, 354 | Multiplicity statement; the analysis-script commitment. |
| [seed-replication-registration.md](seed-replication-registration.md) | 367–368 | **The consequence itself, verbatim.** Must never be edited. |
| [phase-c-lpips-registration.md](phase-c-lpips-registration.md) | 135–148 | The pre-registered interaction bands (additive / substitutes / super-additive / degenerate) and the "same lever" band definition. Registration text, preserved. |
| [phase-c-audit.md](phase-c-audit.md) | 283 | Audit checklist row naming the registered bands. |
| [phase-c-audit.md](phase-c-audit.md) | 314, 453 | "…the substitution is not disclosed as one" / "by substituting a different test" — a different sense of "substitute" (swapping a test), and a correction record. |
| [hardware-gate-results.md](hardware-gate-results.md) | 29 | Gate result reporting where the interaction sat relative to its spread. Historical measurement record. |
| [standing-practices.md](standing-practices.md) | 64 | The standing practice that exists *because* of the un-error-barred interaction. |
| [corrections-log.md](corrections-log.md) | 94, 105 | Correction entries. Entry 105's "substituted" is about data sources, unrelated. |
| [gates/seed-block-morning-report.md](gates/seed-block-morning-report.md) | 89 | States the readings were *not* evaluated overnight. Record of process. |
| [B2-B3-audit.md](B2-B3-audit.md) | 365 | "no weaker **substitute** is…" — unrelated sense (substituting a check). |
| [tool-registrations-3.md](tool-registrations-3.md) | 33 | "substituting our rasteriser's renders" — unrelated sense. |
| [modal/gencp_modal.py](../modal/gencp_modal.py) | 39 | "the registration forbids **substituting** one" (a base image) — unrelated sense. |

### 6.3 Different quantity — NOT covered by this consequence

The consequence is about the **2×2 loss factorial's** interaction. These use the word for a
different measured quantity and are outside its scope; flagging them so nobody
search-and-replaces them by accident:

| file | line | what it actually is |
|---|---|---|
| [positioning-registrations.md](positioning-registrations.md) | 83–87 | The **E-series positioning interaction** (does the synthetic-versus-real gap depend on tile change?) — a different registration, a different quantity. |
| [positioning-results.md](positioning-results.md) | 57 | That positioning interaction's result (null). |
| [paper-context-addendum.md](paper-context-addendum.md) | 301 | The same positioning interaction, reported as null. |
| [final-report-skeleton.md](final-report-skeleton.md) | 59 | "interaction null at <0.5 SE" — again the positioning interaction. |
| [geometry-finding.md](geometry-finding.md) | 366 | "KARIOS **interaction**" — whether KARIOS itself fits a scale/shift term. Unrelated. |
| [scripts/seed_eval/seed_analysis.py](../scripts/seed_eval/seed_analysis.py) | 123–158, 285–288, 353–403 | Function names and printed labels in the **frozen analysis script**. This code is registration-frozen; it computes the reading and must keep computing it, including for this document. **Do not edit.** |
| [scripts/c45_eval/c45_score.py](../scripts/c45_eval/c45_score.py) | 15, 91, 105, 120 | Interaction computation and band assignment in the evaluation harness (committed `40cde9b`, frozen at `48ced64` pins). Computation stays; only line 100's claim wording is a candidate, and changing frozen eval code needs its own dated registration. |

### 6.4 Vendored repository snapshots — do not touch

**562 further matches** across **13 copies** of the repository vendored under
`tubitak/outputs/*_checkpoints*/GenCP/` — these are checkout snapshots captured inside the
checkpoint download directories at training time. They are frozen provenance artifacts
recording what the code and docs said when each arm trained. They are not the live
documents, they are not the paper, and editing them would destroy the provenance they exist
to preserve.

---

## 7. What is deliberately not in this document

- **The warm-up de-confound curves are untouched.** `loss_log.txt` for C5_warmup and
  C2_warmup is downloaded and unread. That package has its own registered branches and its
  own session.
- **No manuscript, title or claim text has been edited.** §6 is a review list; the edits
  follow review.
- **No corrections-log entry.** See the head of this document.
