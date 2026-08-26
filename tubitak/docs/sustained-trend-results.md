# Sustained main-stage trend at six seeds — results

Written 26 August 2026, immediately after
[sustained-trend-registration.md](sustained-trend-registration.md) was committed and pushed
(`0a7a115`) and the loss logs were downloaded. The registration's per-seed label block, the
sign justification, and the disclosure of prior sight all apply and are not restated here
except where a number depends on them.

**Headline: the registered reading on C1 FAILS at 5/6, and the registered consequence
fires.** C4's holds 6/6. The two non-adversarial readings hold 6/6. Entry 26's
sustained-trend argument is no longer a replicated result in the form it was written.

---

## 1. Retrieval and integrity

**28 of 28 files present on the gencp-out Volume; none missing; nothing substituted.** All
four arms of seeds 45–50 (24 files) and of seed 43 (4 files) were located before any
download began, per the registration's stop-and-name rule. Volume reads only — **zero GPU,
no container started**.

Committed to `docs/gates/loss_logs/` as `s{seed}-{arm}-loss_log.txt`, for the reason the
warm-up logs were committed there: the existing loss logs live under a gitignored
`checkpoints/` path, and evidence for a registered reading should not sit one cleanup away
from gone.

| seed | C1 | C2 | C4 | C5 |
|---|---|---|---|---|
| 43 | `122b2ad2…` | `f7dbdd1f…` | `8b883250…` | `545678ec…` |
| 45 | `22801a99…` | `a1b89103…` | `789f8540…` | `5a21142b…` |
| 46 | `0e1d5be9…` | `681f387e…` | `ec49abf1…` | `b2aed16b…` |
| 47 | `f1891cbc…` | `6b25d4e8…` | `648ff525…` | `8a6e8190…` |
| 48 | `728d7c39…` | `fe705dcf…` | `7f626279…` | `cfb21438…` |
| 49 | `7b0ec791…` | `be697dae…` | `d7790512…` | `7bee85e1…` |
| 50 | `44f4e064…` | `b3151370…` | `5ebde08d…` | `0cd47d21…` |

Full sha256 values are the committed files themselves; the prefixes above are for
eyeballing.

**All registered structural assertions pass on all 28 files**, checked before any value was
computed: C1 and C4 carry two `Training Loss` headers and 18 main-stage epochs (3–20); C2
and C5 carry one header and 20 main-stage epochs (1–20); every epoch in every file carries
exactly 279 logged iterations. Line counts corroborate: 5,582 for every warmed arm, 5,581
for every un-warmed one. **No mismatch to report.**

---

## 2. The registered readings — outcomes

Quantity: proportional change in the per-epoch generator reconstruction loss from the first
to the last main-stage epoch, each run on its own window. `G_L1` for C1 and C2, `G_LPIPS`
for C4 and C5. **Epoch counts travel with every number: C1 and C4 over 18 main epochs, C2
and C5 over 20.**

| seed | C1 (L1, 18 ep) | C2 (L1, 20 ep) | C4 (LPIPS, 18 ep) | C5 (LPIPS, 20 ep) | gap L1 | gap LPIPS |
|---|---|---|---|---|---|---|
| 45 | **−0.99%** | −6.02% | +0.98% | −7.88% | +5.03 | +8.86 |
| 46 | +0.35% | −6.82% | +1.14% | −7.43% | +7.17 | +8.56 |
| 47 | +1.06% | −5.76% | +2.22% | −7.63% | +6.83 | +9.85 |
| 48 | **+0.02%** | −6.23% | +1.08% | −7.55% | +6.24 | +8.63 |
| 49 | +1.31% | −7.83% | +1.41% | −7.98% | +9.14 | +9.39 |
| 50 | +2.02% | −4.78% | +1.86% | −7.25% | +6.79 | +9.11 |

| # | registered reading | outcome | count |
|---|---|---|---|
| 1 | **C1's change positive in all six** | **FAILED** | **5/6 — seed 45 is −0.99%** |
| 2 | C4's change positive in all six | **HELD** | 6/6, P = 1/64 |
| 3 | C2's change negative in all six | **HELD** | 6/6, P = 1/64 |
| 4 | C5's change negative in all six | **HELD** | 6/6, P = 1/64 |
| 5 | within-family gap positive in all six | **HELD** | 6/6 — but see below |

**Reading 5 carries no independent weight**, as registered before the numbers existed: it is
entailed by readings 1–4 arithmetically, and its P = 1/64 is the same 1/64 as readings 1
and 3, not an additional one. It holds here only because C2 and C5 fall so much further than
C1 and C4 move; it would have held even in the seed where reading 1 failed, and it did
(seed 45, gap +5.03, with C1 at −0.99%). **A gap reading cannot detect the failure that
reading 1 detects**, which is exactly why the arm readings were registered separately.

### Seed 45 is REPORTED and NEVER DROPPED

**Seed 45's C1 change is −0.9932%**: from **33.494** at main-stage epoch 3 to **33.161** at
epoch 20, over 18 main epochs. C1's reconstruction loss **fell** in that seed. It is named,
its value printed, and it stays in the count.

**Seed 48 is recorded beside it as a second observation, not as a second failure.** C1's
change there is **+0.0168%** — 33.488 at epoch 3 to 33.493 at epoch 20, a difference of
five thousandths of a loss unit. Positive, so reading 1 is not failed by it, but it is
indistinguishable from no change at all. **Two of the six seeds put C1 at or below zero.**
That is stated as a fact about the spread, not as a re-reading: the registered criterion is
the sign, seed 48's sign is positive, and it counts as such.

### Intervals — REPORTED, NOT REQUIRED

No interval below is a gate. An interval containing zero is not a failed reading, and an
interval excluding zero does not pass one. This binds in both directions, as registered.

| quantity | mean | sd | 95% CI (df = 5, t\* = 2.571) | contains zero |
|---|---|---|---|---|
| C1 | +0.63% | 1.06 | [−0.49, +1.74] | **yes** |
| C2 | −6.24% | 1.03 | [−7.32, −5.16] | no |
| C4 | +1.45% | 0.50 | [+0.93, +1.97] | no |
| C5 | −7.62% | 0.27 | [−7.91, −7.33] | no |
| gap L1 (C1 − C2) | +6.87 | 1.34 | [+5.46, +8.27] | no |
| gap LPIPS (C4 − C5) | +9.07 | 0.49 | [+8.55, +9.58] | no |

**C1's interval contains zero and its sign reading failed. These are two separate facts and
neither is offered as the reason for the other.** The registered criterion was sign
stability; it failed at 5/6; the consequence fires on that. The interval is printed because
the registration says print it.

**C1 and C4 are not alike, and the numbers say so plainly.** C4's spread is a fifth of C1's
(sd 0.50 against 1.06), its range never approaches zero, and its reading holds. C1's range
spans −0.99 to +2.02. Whatever "the adversarial term prevents the reconstruction loss from
falling" describes, it describes C4 far more consistently than C1.

---

## 3. The consequence, executed

From the registration, quoted:

> **IF either adversarial arm's change is NOT positive in all six seeds**: entry 26's
> sustained-trend argument **is no longer a replicated result**. It is reported as a
> **seed-42 observation**, with the six-seed counts printed beside it and the failing seed
> named and its value printed, never dropped. **The manuscript does not assert that
> adversarial arms fail to reduce the reconstruction loss as a general finding.**

**C1's change is not positive in all six seeds. The consequence fires.**

**What the manuscript may no longer assert:** that adversarial arms fail to reduce the
reconstruction loss, as a general finding of this design. That sentence covered both arms
and it does not survive at six seeds.

**What survives, stated per arm rather than as a general finding:**

- **C4 (LPIPS + adversarial) fails to reduce its reconstruction loss in all six seeds**,
  mean +1.45%, range +0.98 to +2.22, sd 0.50. This replicates and may be stated with its
  n = 6 and its epoch count attached.
- **C1 (L1 + adversarial) does not replicate**: five of six positive, one negative
  (seed 45, −0.99%), one effectively zero (seed 48, +0.02%), interval spanning zero. The
  honest statement is that C1's reconstruction loss **does not fall reliably**, not that it
  fails to fall.
- **Both non-adversarial arms reduce their loss in all six seeds**, C2 mean −6.24% and C5
  mean −7.62%. The "roughly 8%" of entry 26 is closer to **6–8%** across six seeds, and C2's
  six-seed range (−7.83 to −4.78) does not include entry 26's −7.90 figure.

**Nothing already disclosed is withdrawn**, as both branches were written to end. Entry 26's
record of what was observed at seed 42 stands as the historical record; what changes is what
the manuscript is entitled to assert.

**This is not a corrections-log entry.** A registered consequence executing as written is the
system working. The proposed addition to entry 26 in
[warmup-deconfound-results.md](warmup-deconfound-results.md) §5 carries this result and
remains a draft for review.

---

## 4. Seeds reported beside the block, never inside it

Per the registration's disclosure table, each with its own label.

| quantity | s42 *(generating, fully seen)* | s43 Kaggle *(never counted, fully seen)* | s43 Modal *(comparability)* | six-seed range | s43 Modal position |
|---|---|---|---|---|---|
| C1 | +1.16% | +0.95% | **+1.03%** — **PARTIALLY-INFORMED** | [−0.99, +2.02] | inside |
| C2 | −7.90% | −5.16% | −5.16% | [−7.83, −4.78] | inside |
| C4 | +2.50% | +0.94% | +1.01% | [+0.98, +2.22] | inside |
| C5 | −7.54% | −8.00% | −7.98% | [−7.98, −7.25] | outside the bottom by 0.01 |

**The C1 cell carries its label from the registration and it is not quietly dropped now that
the number is favourable.** Epochs 1–13 of Modal seed-43 C1 had been read before the
registration was written, including main-stage epoch 3 — one of the two endpoints of this
very quantity. Its +1.03% is therefore a partially-informed comparability value. It happens
to sit comfortably inside the six-seed range, which is a reassuring outcome and not an
independent check.

**Seed 42 falls outside the six-seed range on two of four arms** — C2 by 0.07 points and C4
by 0.28 — reported as findings under the registration's comparability rule rather than
smoothed over. Both are small relative to the seed spreads (C2's range spans 3.05 points),
and neither is in the class of the interaction result recorded in
[seed-block-results.md](seed-block-results.md) §5(c), where the single-run estimate sat
beyond the whole replicate range on the quantity a claim was built on. **Entry 26's C4
figure of +2.50% is nonetheless the largest of any seed measured**, and the manuscript should
carry the six-seed mean of +1.45%, not it.

**One cross-platform observation, recorded and not built on.** Modal seed-43 C2 gives
−5.1602% and Kaggle seed-43 C2 gives −5.1608% — agreement to four significant figures on a
quantity whose seed-to-seed spread is 3 points. The hardware gate's NOT POOLED verdict stands
and this does not revisit it; it is one arm on one seed, noted because it was observed.

---

## 5. Scope

**Training-dynamics reading, not a positional one.** It supports the mechanism discussion. It
enters no registered positional contrast, does not touch the primary, secondary, main-effect
or edge-ratio readings, and cannot repair or substitute for the failed interaction reading.
A reconstruction loss that does or does not fall is a fact about the optimisation; the step
to "the generator invents structure" is carried by the edge-ratio measurement, not by these
curves.
