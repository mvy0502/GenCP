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

## CORRECTED 2026-08-26 — the specs are accurate; the overrun is uncosted material

**The earlier reading in this document was wrong and is corrected here rather than quietly
replaced.** It said Section II's 1.23× ratio suggested the specs systematically under-cost
their content, and extrapolated the letter to ~4,060 words. **That extrapolation was wrong and
must not drive planning.**

Decompose Section II's 926 by whether the material was costed in the spec at all:

| | words |
|---|---|
| **Uncosted material added after the skeleton** — Model-and-fine-tuning excess (+103, the LR asymmetry and its bound), Evaluation excess (+182, the matched-point asymmetry and common support), and the sign-convention lead-in (34, not in the spec) | **319** |
| Section II **without** that material | **607** |
| against a section budget of | **750** |
| | **−143** |

On the narrower decomposition — removing only the two named blocks' excess (+285) — Section II
is **641 against 750, under by 109.** Either way the answer is the same.

**And the costed blocks, measured individually, came in at −53 against their own allocations:**
B +12, C 0, E −42, F 0, G −23. **Not one costed block overran materially.**

**Section III is the confirming case.** It balances **exactly** at its revised 980, and the
reason is that its two new subsections were *costed before being added* (80 + 100) and the
interaction's 120 words were explicitly re-spent rather than returned. Costed new material fit.

### The hypothesis, recorded as a hypothesis and not as a conclusion

> **COSTED MATERIAL FITS THE SPEC. UNCOSTED MATERIAL DOES NOT.**

Two sections are consistent with it and neither tests it hard: Section II is one drafted
section, and Section III's balance is a property of its *plan*, not of drafted prose.

**The next drafted section tests it.** Section III is the right test and is drafted next, for
two reasons: at 980 words it is the largest section in the letter, and **a spec that holds on
a small section tells you much less than one that holds on the largest.** If Section III
drafts at or under 980 with every item costed in advance, the hypothesis stands and the
budget is a plan worth trusting. If it overruns on costed items, the hypothesis fails and the
earlier systematic-under-costing worry returns with real evidence behind it instead of one
data point.

## THE TRANSFER RULE — second occurrence, so it becomes a rule

> **A word transfer between sections is recorded in BOTH allocations at the same time, or it
> is not a transfer — it is a deferral.**

**First occurrence:** Section III's two new subsections were costed at 180 words and the
transfer was recorded as "absorbed within their combined 4.0 columns." Section III's
allocation rose 800 → 980; **Section IV's fell 500 → 320 on paper while its content stayed at
400.** The 180 was never paid, and that is exactly the +80 this reconciliation found.

**Second occurrence:** the same sentence pattern — "absorbed" — was used again for the column
allocations, which were left unchanged on the argument that 180 words is a fifth of a column
and the two sections are adjacent. **That is the same deferral in the same document.**

The rule applies to columns as well as words. **"Absorbed" is not an accounting entry.**

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
   proves; a pointer would do. **QUALIFIED 2026-08-26: it may lose length but not substance.**
   Three things must survive any trim, because they are **binding sentence 6**: the
   discriminator is not published; every adversarial arm starts from a **seeded random**
   discriminator recorded in a provenance file; and this is a **deviation from the published
   setup**. **And if the GenCP authors supply the discriminator weights, this block is
   rewritten from scratch rather than trimmed** — the disclosure would no longer be describing
   our deviation but a resolved one, which is a different paragraph and possibly a different
   experiment.

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

---

## Section III — costing check BEFORE drafting

Run against the seven items Section III must now carry. **Six are costed. One is not.**

| must carry | costed? | where |
|---|---|---|
| Table I rebuilt from the six-seed block | **yes**, 80 | item 1, "The panel" — the rebuild is a table; 80 words is the prose about it |
| Primary at seed level, interval reported-not-required | **yes**, 120 | item 2, revised 2026-08-26 |
| Secondary at seed level, same treatment | **yes**, 60 | item 4, revised 2026-08-26 |
| Out-of-range result as its own subsection | **yes**, 80 | item 9, costed when added |
| Sustained trend with the arm-versus-gap distinction | **yes**, 100 | item 10, costed when added |
| Honest-limit paragraph | **yes**, 100 | item 8, unchanged |
| **PROTECTED interaction disclosure** | **yes**, 120 | item 3's allocation, explicitly re-spent rather than returned |
| **Point-count argument WITH the equal-count and floor-sweep answers** | **NO — see below** | item 7 costs 100 words for the *original* argument only |

### The uncosted item, reported before drafting rather than absorbed

**Item 7's 100 words cover the original point-count argument only** — that the LPIPS-only arm
produces *more* surviving matches than the L1-only arm and still scores worse, so the harm is
not about feature count. That argument predates the common-support work.

**The equal-count and floor-sweep answers are new, completed 2026-08-26, and have no
allocation in Section III.** Estimated **60–80 words** to state the results: counts equalised,
primary +1.8%, LPIPS-only penalty −11%, both 6/6, floor sweep moving the penalty upward.

**There is a complication, and it is a decision rather than an arithmetic problem.** Part of
this material **already sits in the drafted Section II-D**, which currently says: *"Under
equalised counts the primary contrast grows by 1.8% and the LPIPS-only penalty shrinks by 11%;
both hold in all six replication seeds."* **That is a result, and it is sitting in Methods.**
Three ways to resolve it, none applied:

1. **Leave it in II-D and give item 7 a pointer (0 extra words in III).** Defensible — it reads
   as methods validation, showing the procedure was checked rather than merely described. But
   a reviewer looking for the robustness result in Results will not find it.
2. **Move it to III (III +60, II −40).** Cleanest by convention: methods describe the
   procedure, results report the numbers. Net +20 to the letter.
3. **Split: II-D keeps one clause that the check was run, III carries the numbers
   (III +60, II −20).** Net +40, and it is the most duplicative.

**Recommendation: option 2.** It is the only one that puts a result in Results, and its net
cost of +20 is the smallest real change. **Not applied — flagged before drafting, as required,
and the +60/−40 is not yet in the table above.**

**If option 2 is taken, Section III's committed figure becomes 1,040 against 980 (+60)** and
Section II falls to 886 against 750 (+136); the letter total is unchanged at +141 plus the net
+20, i.e. **+161** before item 4 reports.
