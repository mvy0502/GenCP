# Reconciled word budget — the whole letter, 2026-08-26

Produced before Section IV is drafted, because the Section III/IV transfer of 180 words was
recorded as "absorbed within their combined 4.0 columns" and **that deferred the overrun
rather than paying it.** Nobody had added the letter up end to end. This does.

**Counting method.** Section II is **drafted**, so its figure is measured by script over the
prose. Every other section is **specified, not drafted**, so its figure is the sum of its live
per-item word allocations in the skeleton, with struck items excluded and two unlabelled items
allocated from their own spec prose (I.3 "two sentences only" → 50; V.3 "one sentence" → 25).

---

## The table

| section | allocated | committed | Δ | basis |
|---|---|---|---|---|
| Title block + abstract | 200 | 200 | **0** | spec, unchanged |
| I. Introduction | 600 | 500 | **−100** | related work 220 → 150 (decision 2) |
| **II. Materials and methods** | **750** | **926** | **+176** | **DRAFTED, measured;** after decision 1 removed the 1/256 finding |
| III. Results | 980 | 980 | **0** | revised allocation; the interaction's 120 words are spent on the mandatory disclosure, not returned |
| IV. Alternative explanations | 320 | 400 | **+80** | revised allocation; mediation row **and** its 176-word footnote struck |
| V. Discussion | 450 | 435 | **−15** | spec, unchanged |
| **TOTAL** | **3,300** | **3,441** | **+141** | |

**The letter is 141 words over budget.**

## Do decisions 1 and 2 close the gap? No.

| state | total | vs 3,300 |
|---|---|---|
| before decisions 1 and 2 | 3,570 | **+270** |
| after decisions 1 and 2 | **3,441** | **+141** |

**They closed 129 of the 270. They bought less than expected**, and the reason is worth
recording: decision 1 was costed at "~100 words plus the ~50-word variance qualifier", but the
1/256 block in the **drafted** Section II was already compressed to 109 words, and keeping the
one-clause disclosure costs 50 of those back. **Decision 1 therefore yielded 59 words, not
150.** Decision 2 yielded the expected 70.

## What nobody had added up

**Section IV is 80 words over its own revised allocation, and that is the deferred overrun.**
When 180 words moved from Section IV to Section III, Section IV's allocation dropped
500 → 320 while its *content* stayed at 400 (90 blur + 90 cold-D + 60 georeferencing +
120 matcher + 40 mechanistic note). Striking the mediation row removed its 176-word footnote
from the count — which is the only reason the gap is 80 rather than 256. **The transfer was
recorded as absorbed; it was not.**

Section III, by contrast, balances **exactly** at its revised 980, because the two new
subsections (80 + 100) were costed correctly and the interaction's 120 words were explicitly
re-spent on the disclosure rather than returned.

---

## The warning the table does not show, and it is the larger number

**Section II is the only section that has actually been drafted, and it came in at 926 against
a 750 spec — 1.23× its allocation.** Every other figure in the table is a *plan*, not a
measurement.

**If the remaining sections draft at the same ratio, the letter lands near 4,060 words, not
3,441 and not 3,300.** That is a 760-word overrun, roughly two and a half columns, and it
would not be recoverable by trimming related work.

I do not claim the ratio will hold — Section II absorbed two new evidence blocks that the
other sections do not have equivalents of, and it is plausibly the worst case. **But the one
data point available says specs in this skeleton under-cost their content by about a quarter,
and the reconciliation above assumes every remaining spec is achievable as written.** That
assumption should be tested on the next section drafted, not at the end.

---

## Recommendation: do not cut yet. Item 4 decides more than the gap.

**The Phase D regeneration (item 4) controls 150 of Section IV's 400 words**, and its outcome
is not yet known:

- **The blur row (90 words)** and **the corrected-georeferencing row (60 words)** are the two
  rows whose evidence did not survive — no per-chip artifact, no committed script
  ([phase-d-audit.md](phase-d-audit.md) §C).
- **If they regenerate and reproduce**, they stay, and Section IV needs its 400 words plus a
  mandatory disclosure that the originals were lost and the numbers regenerated on
  2026-08-26 — which makes Section IV *larger*, not smaller.
- **If they do not reproduce, both rows leave Table II.** Section IV falls to 250 against an
  allocation of 320, and the letter total falls to **3,291 — under budget**, with no further
  cut required anywhere.

**So the gap is either −9 or roughly +200, and item 4 decides which.** Cutting 141 words now
would in one branch be unnecessary and in the other branch be insufficient.

**Recommended order: run item 4 first, then re-reconcile.** If cuts are still needed after it,
the candidates in priority order, none applied:

1. **Section IV to its own allocation (−80).** It is over its line regardless of item 4's
   outcome; the georeferencing row at 60 words is the first candidate if it survives item 4 at
   all.
2. **Section V limitations, 180 → 140 (−40).** The longest single block in the letter and the
   one where compression costs least, since each limitation is a sentence rather than an
   argument.
3. **Section II's Disclosure block, 60 → 40 (−20).** It restates in Section II what Section IV
   proves; a pointer would do.

**Not candidates, recorded so they are not proposed later:** Section III's interaction
disclosure (protected text — removing it produces a paper that silently drops a pre-registered
failed test), the Arar citation (its omission would read as suppressing contrary evidence),
and Section II's two new evidence blocks (they answer the objections a reviewer reaches first).

---

## One note on the timing measurement, kept with the budget because it will be read together

The 2 m 02 s Section II draft time is **the marginal cost of drafting with the evidence
settled**, and that caveat travels with the number wherever it is cited.

**The schedule consequence is that prose generation is not the binding constraint — evidence
settlement and review passes are.** This must not be read as "the letter is nearly written."
On today's evidence the binding items are the Phase D regeneration, Table I's six-seed
rebuild, the packageA and phase-d corrections-log entries, and the two audits still to be
answered. **The prose is the cheapest remaining input, and the budget above is a plan whose
only measured line already exceeds its allocation by a quarter.**
