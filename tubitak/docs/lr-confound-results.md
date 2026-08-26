# The learning-rate confound at the positional outcome — results

Written 26 August 2026, immediately after
[lr-confound-registration.md](lr-confound-registration.md) was committed and pushed
(`c937d462`) and the checkpoints were scored. The registration's branch text was fixed before
any positional number for these arms existed.

**Outcome: BRANCH 2. The confound is answered at the positional outcome.** Giving a
non-adversarial arm the adversarial arm's exact learning-rate schedule moves its positional
residual by **+0.0065 px** in the L1 family and **−0.0360 px** in the LPIPS family — 1.0% and
−6.8% of the adversarial gaps they would have to explain, neither reaching the registered
0.10 px threshold, neither reaching 2 SE.

**Nothing is withdrawn and no follow-up is triggered.** The `C1_nowarmup` / `C4_nowarmup`
package is not launched.

---

## 1. What ran

**Zero GPU training.** Volume read plus local scoring, exactly as registered.

Frozen `seed_eval_run.py` (commit `6418febc`), unchanged, through its own documented
ROUTING-ONLY flags:

```
seed_eval_run.py --seed 43 --variant modalwarmup --arms C2,C5
```

**Zero failures: 130/130 chips inferred, 390/390 warps, 260/260 KARIOS runs, 0 skipped in the
edge-ratio pass.**

**The disclosed routing rename was applied and verified.** The Volume stores these arms at
`seed43/C2_warmup/C2_warmup/` and `seed43/C5_warmup/C5_warmup/`; they were copied to
`c{2,5}_checkpoints_s43_modalwarmup/checkpoints/{C2,C5}/` so the frozen runner's arm routing
resolves. **The directories were renamed; the checkpoint files were not modified.** Every
number below names the arm as `C2_warmup` or `C5_warmup`.

**Checkpoint identity check passed**, as registered: `latest_net_G.pth` is **tensor-equal** to
`20_net_G.pth` for both arms, all 82 tensors. Note that the two files' **sha256 values differ**
(`255a752e…` vs `b3155d90…` for C2_warmup; `7f11b5eb…` vs `122fc636…` for C5_warmup) while
their tensor contents are identical — pickle metadata, not weights. **Recorded because a
reader comparing file hashes alone would reach the wrong conclusion**, and because the
project's `verify_latest` practice checks tensors rather than bytes for exactly this reason.

**Baseline validation.** Both published adversarial gaps reproduce **exactly** from the
committed seed-43 Modal per-chip file: D_L1 = C1 − C2 = **+0.6473 px**, D_LPIPS = C4 − C5 =
**+0.5292 px**. The comparison is therefore against the same numbers the hardware gate
published, not against a re-derivation of them.

---

## 2. The registered reading

Per-arm mean over 130 chips of the per-chip median KARIOS residual. Δ is a paired per-chip
difference, sign fixed in advance so that **positive = toward the adversarial arm (worse)**.

### Arm means (px), all six arms at seed 43 Modal

| arm | adversarial | integrated LR | mean residual | median |
|---|---|---|---|---|
| C1 | yes | 13.40 | 2.0172 | 1.8273 |
| C2 | no | 15.00 | 1.3699 | 0.9091 |
| **C2_warmup** | **no** | **13.40** | **1.3764** | 1.0316 |
| C4 | yes | 13.40 | 2.0077 | 1.7963 |
| C5 | no | 15.00 | 1.4785 | 1.1665 |
| **C5_warmup** | **no** | **13.40** | **1.4425** | 1.1142 |

### The two tests

| | **L1 family** | **LPIPS family** |
|---|---|---|
| adversarial gap to explain | D_L1 = C1 − C2 = **+0.6473 px** | D_LPIPS = C4 − C5 = **+0.5292 px** |
| Δ = warmed − un-warmed | **+0.0065 ± 0.0335 px** | **−0.0360 ± 0.0383 px** |
| distance from zero | **0.19 SE** | **0.94 SE** |
| condition 1: \|Δ\| ≥ 0.10 px toward adversarial | **NO** | **NO** |
| condition 2: \|Δ\| ≥ 2 SE | **NO** | **NO** |
| **MATERIAL?** | **NO** | **NO** |
| f = Δ/D *(reported, not required)* | **+0.010** | **−0.068** |

**Neither family shows material movement. Neither condition is met in either family.
BRANCH 2 fires.**

### The LPIPS sign, handled as registered

C5_warmup's residual is **lower** than C5's — movement *away* from the adversarial arm. The
registration anticipated this case and fixed its treatment in advance: negative movement is
neither branch's evidence, counts as branch 2 for the confound question, and is flagged as its
own observation rather than folded into a story.

**Here it is not an observation worth much: −0.0360 px at 0.94 SE is indistinguishable from
zero.** It is reported because it was registered to be reported, not because it means
anything. **It must not be written up as "the shorter schedule helps."**

### Mechanism measure, reported alongside

The edge-ratio means barely move either, which is consistent with the same conclusion:

| arm | edge ratio | vs un-warmed |
|---|---|---|
| C2 | 0.2803 | — |
| **C2_warmup** | **0.2730** | −0.0074 |
| C5 | 1.1584 | — |
| **C5_warmup** | **1.1553** | −0.0031 |

C2_warmup remains far below the registered 0.5 threshold and C5_warmup remains high. **The
schedule does not move the invention measure any more than it moves the residual.** These are
descriptive; no mechanism reading was registered for this probe.

---

## 3. What this establishes, and what it does not

**Established.** The ~11% integrated-LR deficit carried by the adversarial arms
(13.40 against 15.00, a 10.67% shortfall computed from pix2pix's own `lambda_rule`) **does not
account for the adversarial main effect.** A non-adversarial arm given that exact deficit
moves 1.0% of the L1 gap and −6.8% of the LPIPS gap. To explain the main effect the schedule
would have to move an arm by roughly 0.6 px; it moves it by roughly 0.01.

**The manuscript therefore states the LR asymmetry as a disclosed design asymmetry**, with
this probe cited as the test that bounded it, and **the adversarial attribution stands.** The
asymmetry was already listed among the "known asymmetries, inherited and disclosed rather than
removed" in [seed-replication-registration.md](seed-replication-registration.md); what changes
is that its consequence is now measured rather than assumed to be small.

**Not established, and the registration said so in advance.** This probe tests the schedule's
effect **on the non-adversarial arms only.** It asks whether the schedule alone can produce an
adversarial-sized penalty, and the answer is no. **It does not establish that the adversarial
arms would be unaffected by the reverse manipulation** — that requires `C1_nowarmup` /
`C4_nowarmup`, which is not run and whose launch is not triggered by this outcome.

**Scope, repeated because this number will travel.** **n = 1 seed. A mechanism probe, not a
confirmatory estimate.** It enters no registered contrast, modifies no published number, and
cannot repair or strengthen the failed interaction reading. Within platform and within seed
(Modal, seed 43, both sides) — the control the warm-up package's first attempt lacked.

**One thing this probe could not have overturned, recorded before it ran.** The **secondary**
contrast C5 − C2 compares two un-warmed 20-epoch arms with **identical integrated LR
(15.00 each)** and is therefore structurally immune to this confound. The registration states
this ahead of the numbers. Had branch 1 fired, the secondary — and with it the LPIPS-alone
penalty and the title — would still have stood.

---

## 4. DECISION, 2026-08-26 — C1_nowarmup / C4_nowarmup will NOT be run

**Recorded today with its full reasoning, rather than left to be reconstructed under
review.** The registration named this follow-up as the only test of the reverse manipulation
and left the decision to the supervising session. The decision is **not to run it**, for four
reasons, in descending order of weight.

**1. The measured effect is too small by two orders of magnitude.** The schedule moves a
non-adversarial arm by +1.0% of the gap in the L1 family and −6.8% in the LPIPS family,
neither at 2 SE. For the schedule to overturn the adversarial attribution it would have to act
on the adversarial arms **far more strongly than on the non-adversarial ones**. Two ways to
size that, both given because they differ and the conservative one is the honest one to quote:

- On the **point estimate**, closing the L1 gap needs 0.6473 px against the 0.0065 px measured
  — a factor of **≈ 100**.
- On the **2 SE upper bound** of the measured movement (0.0065 + 2 × 0.0335 = 0.0735 px),
  which is the right bound to use because the point estimate is itself indistinguishable from
  noise — a factor of **≈ 9**.

**Quote the ≈ 9.** It is the conservative figure and it is still an implausible asymmetry: no
mechanism has been proposed by which an identical learning-rate ladder would act nine times
more strongly on a network that also has a discriminator attached.

**2. The reverse manipulation is not a cleaner control — it is a different training regime.**
[phase-c-config.md](phase-c-config.md) already registers *why* the warm-up exists: joint
training from a cold discriminator at full learning rate is an **unstable configuration**, and
the low-LR joint warm-up was the chosen protocol precisely to avoid it. So removing it does
not isolate the schedule; it introduces instability as a second changed factor. **A worse
`C1_nowarmup` could not separate "the schedule matters" from "the run destabilised", and a
null `C1_nowarmup` would only confirm what this probe already shows.** An experiment whose
adverse outcome is uninterpretable and whose null outcome is redundant is not worth $21 or a
night — it is worth less than that, because a misread adverse outcome would cost the
attribution the probe just secured.

**3. Independent evidence rules out a schedule-concentrated mechanism, from the shape of the
curve.** The adversarial deficit is present at **epoch 1** and is large there:
C1 − C2 = **+0.546 ± 0.048 px** at epoch 1 ([headline-results.md](headline-results.md)
checkpoint sweep), which is over 11 SE, and C1 versus pretrained is already **−0.399 ± 0.064
(6.3 SE)** — the wrong sign for cold-discriminator damage. **An effect produced by an LR
ladder that has barely begun to diverge at epoch 1 does not appear full-size at epoch 1.**

> **Correction to the reasoning as it was put to this session, made rather than passed
> through.** The deficit does **not** grow *monotonically*. The committed sweep is
> +0.546 (e1) → +0.402 (e2) → +0.384 (e5) → +0.552 (e10) → **+0.700 (e20)** — a
> **dip-then-grow-then-plateau** shape, the same shape the LPIPS family shows and the same
> one [headline-results.md](headline-results.md) already flags as *not* covered by its
> registered bands. **The argument survives the correction and does not depend on
> monotonicity**: what rules out the schedule explanation is that the deficit is already
> +0.546 at epoch 1, not the path it takes afterwards. Writing "grows monotonically" in the
> manuscript would be false against our own committed table.

**4. The title-bearing reading was never exposed to this confound.** The secondary contrast
C5 − C2 compares two un-warmed 20-epoch arms with **identical integrated LR of 15.00 each**.
It is immune by construction, as the registration recorded before the numbers existed. The
follow-up could not have protected it, because it was never at risk.

**What this decision does not do.** It does not claim the reverse manipulation was run, and it
does not claim the adversarial arms are *known* to be unaffected by schedule removal. **It
records that the question was asked, bounded from one side, and judged not worth the
experiment that would bound it from the other** — with the reasons written down while they
were live rather than assembled afterwards. If a reviewer asks for `C1_nowarmup`, this section
is the answer, and reason 2 is the load-bearing half of it.

### The pseudoreplication objection, raised here rather than waited for

**This probe's ±0.0335 and ±0.0383 are CHIP-LEVEL standard errors at a single seed.** That is
the same class of statistic this paper criticises the upstream work for, and the same class
the whole seed-replication package exists to correct. **Stating it beside the number rather
than in a limitations paragraph, because a reader who finds it themselves is entitled to
assume we did not notice.**

**The conclusion survives it, and the reason is arithmetic rather than rhetorical.** The
measured movements sit **0.19 SE** and **0.94 SE** from zero, against a gap they would need to
close of roughly **0.6 px**. A seed-level interval on this quantity would be wider than the
chip-level one — the seed-block's own contrasts show seed-level spreads two to three times
chip-level SEs — but **widening ±0.0335 by a factor of three gives ±0.10 px, which is still
six times too small to reach the gap.** The probe is not close to its threshold in a way that
a better error bar could rescue or destroy; it is two orders of magnitude away.

**What a single seed genuinely cannot do here is bound the seed-to-seed variability of the
schedule effect itself.** If the schedule's effect on residuals varied wildly across seeds,
one seed would not reveal it. That limitation stands, is not repaired by this probe, and is
the honest residual uncertainty in the branch-2 conclusion.

### The manuscript line this supports

> **The learning-rate asymmetry is a disclosed design asymmetry whose consequence is
> MEASURED rather than assumed small — bounded at roughly 1% of the adversarial gap by a
> within-seed, within-platform probe — with the secondary contrast immune by construction.**

Not "negligible", not "controlled for". **Measured, bounded, and with the bound's own scope
attached.**

---

## 5. Artifacts

Per standing practice 10, committed to `tubitak/docs/evidence/C45_s43_modalwarmup/`:

| file | sha256 |
|---|---|
| `C45_per_chip.csv` | `736bb74648d9bc01650aadc01a403d8642b1aa31613a0d8983828844d310c970` |
| `C45_edge_ratio.csv` | `f124f9c800cbe2238594472d56f563c7062fd795ab8f1ebe3ebeea50599ec62a` |

Both hashes are as printed by the frozen runner at the end of its own scoring step.

**This is not a corrections-log entry.** A registered probe returning its registered
branch is the system working.
