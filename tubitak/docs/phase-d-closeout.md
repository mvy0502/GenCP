# Phase D closeout — the design argument, and the housekeeping

Written 2026-08-26, after the regeneration was stopped
([phase-d-regeneration-STOP.md](phase-d-regeneration-STOP.md)) and the blur row was replaced
by a six-seed positive test ([informative-mask-results.md](informative-mask-results.md)).
Writing only; no computation, no GPU, no published number changed.

---

## C. The georeferencing row — answered by design. VERIFIED, does not stop.

**The objection:** the fine-tuned arms' advantage comes from corrected georeferencing in the
fine-tuning pairs rather than from the loss. **That objection is about a
fine-tuned-versus-pretrained comparison.**

**Verified against the registrations, not taken on assertion.** Every registered positional
reading, checked verbatim against AMENDMENT SEED-c (d):

| registered reading | arms compared | involves pretrained? |
|---|---|---|
| PRIMARY C5 − C4 | LPIPS-only vs adversarial+LPIPS | **no** |
| SECONDARY C5 − C2 | LPIPS-only vs L1-only | **no** |
| C1 − C2 | adversarial+L1 vs L1-only | **no** |
| C4 − C5 | adversarial+LPIPS vs LPIPS-only | **no** |
| I_raw | the four 2×2 cells | **no** |

**All five are within the 2×2, and all four arms are fine-tuned on the same 5,577 pairs.** Any
georeferencing improvement in those pairs is therefore common to all four arms and **cancels
in every registered contrast.** `phase-c-lpips-registration.md` contains no registered band
against pretrained either — its only mention of pretrained is the design note that the
published weights occupy the adversarial+LPIPS cell.

**The argument holds. The row can be answered by design rather than by measurement, and the
lost 86% figure is not needed.**

### One mismatch found, disclosed rather than smoothed over

**The registered mechanism reading says "the four arms"; the frozen harness compares five.**
SEED-c (d) reads *"C5's edge mean the highest of **the four arms** in all six"* — the four
being C1, C2, C4, C5. But `seed_analysis.py:212` implements the tie rule as
`for a in ("pre", "C1", "C2", "C4")`, **including pretrained.**

Recorded because it is a registration-versus-implementation gap of the same family as the
"as C1 and C4 did" flaw, and because it means one registered reading's *implementation* does
touch pretrained.

**It does not weaken the design argument, for a reason that is about the quantity rather than
about the arms.** The georeferencing objection concerns **alignment** — better-registered
training targets producing better-aligned outputs. The edge ratio measures **how much
structure an arm invents in input-silent regions**, which is not an alignment quantity;
corrected georeferencing in the training pairs does not systematically change how much an arm
invents where the input says nothing. **So even the C5-versus-pretrained edge comparison is
not exposed to this objection.**

The harness was *stricter* than the registration here, which is the safe direction, and the
reading held 6/6 either way.

### Text for Section IV, 28 words

> No registered contrast compares a fine-tuned arm with the pretrained generator: all four
> arms are fine-tuned on identical pairs, so any georeferencing improvement is common to them
> and cancels.

**This is stronger than the 86% figure it replaces**, because it depends on the design rather
than on an artifact — and unlike the 86%, nothing can be lost that would make it
unverifiable.

---

## D. Housekeeping

### D-1. Check 7b's registered conditional, discharged

The registration required: *"If the improvement is mostly scatter, the georeferencing
candidate is not doing the work and restraint/blur (check 3) carries the burden."* The
improvement was mostly scatter (~86%). **The conditional was triggered and never stated.** It
is discharged here:

> **The improvement was mostly scatter, so the corrected-georeferencing candidate was not
> doing the work, and the burden transferred to restraint. That burden is now carried by the
> six-seed informative-mask test** ([informative-mask-results.md](informative-mask-results.md))
> **rather than by the single-seed blur control that originally received it**, whose artifacts
> did not survive.

**The transfer is recorded as having happened at the time and only being written down now.**
It is not presented as a fresh decision.

### D-2. Entry 32 gains its second reason — before it is applied

The drafted corrections-log entry 32 records that the "regenerable end-to-end from committed
scripts" claim was false **because the scripts were never committed**. It is false for a
second and larger reason, and the entry must carry both before it is applied:

> **…and because the input imagery is gone as well.** The European hold-out retains only
> `inputs/`, `ref/` and `ref_warp/` — no arm output, no pretrained render, no C2 render, no
> KARIOS result set. Every site run directory holds exactly one arm's generated images, and
> the survivor is the pretrained arm; **no C2 output survives at any site.** The procedures
> could therefore not have been re-run even if every script had been committed, because the
> imagery they consume no longer exists.

### D-3. The stochastic-path argument, recorded because it outlives this decision

Moot for the cheap version now that the blur row is replaced, and recorded anyway because it
governs any future attempt to "just re-run" a lost measurement in this project:

**Re-running inference produces a replication, not a reproduction.** The path is stochastic —
test-time dropout is active, registered as a labelled property rather than a defect — so a
second run of the same checkpoint on the same input is a different sample.

**For ratios of two small gains this matters more than for main effects.** The blur recovered
fraction is −6.1%: a near-zero numerator over C2's gain. Draw-to-draw noise that is immaterial
to a 0.6 px main effect can move such a ratio by a large relative amount. **A regenerated −2%
or −11% would neither confirm nor refute the published −6.1%**, and describing either as "the
number reproduced" would be false.

**The project's own bound does not cover this case.** Registration A bounded the
**deterministic-versus-stochastic** gap at |Δ| ≤ 0.05 px at n = 30. That is not a bound on the
difference between two stochastic draws, and it is not a bound on a ratio.

### D-4. Two registered items are unrecoverable. Reported without softening.

**Check 5's Ankara arm.** The registration names the sets explicitly — *"Europe, **Ankara**,
Cappadocia, Tuz Gölü, and the salt/non-salt splits"* recomputed under point floors 0/10/20/30.
**No floor-sensitivity line for Ankara exists in any document.** Recomputing it needs both
arms' per-chip residuals and point counts on Ankara; **only the pretrained arm survives.**

**Check 7a's per-stratum gains.** The ratio addendum required them to be reported alongside R
*"so the aggregation hides nothing"*. Only the aggregate (1.188 / 1.258 = 0.945) was
published. Recomputing them needs both arms at Cappadocia and Ankara; **only the pretrained
arm survives.**

**Both are registered requirements that were not met, whose artifacts no longer exist.** This
is corrections-log **entry 19's shape — a registered half that ran and was not reported — in
its unresolvable form**: with no artifact, the audit **cannot determine whether the Ankara
sweep and the per-stratum gains ran and went unreported, or were never run at all.**

**That distinction cannot now be recovered, and neither reading can be ruled out.** It is
stated that way deliberately. The generous reading — that they ran and the writing lapsed — is
not available as a default, and the record should not imply it.

---

## What this closes and what it does not

**Closes:** the georeferencing row (by design, 28 words, verified), the blur row (replaced by
a six-seed positive test), check 7b's conditional, and entry 32's second reason.

**Does not close:** check 5's Ankara arm and check 7a's per-stratum gains, which are
permanently unrecoverable and are reported as such.

**Table II is now three rows on better evidence than five were**: cold-discriminator
(checkpoint sweep, table-reportable), matcher independence (two independent registrations),
and blur/restraint (six-seed positive test). The georeferencing row's content becomes a
28-word design argument rather than a table row, and the mediation row is struck.

Corrections-log entries 30–34 remain **drafted, not applied**. `corrections-log.md` is
untouched.
