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
| **II. Materials and methods** | **750** | **901** | **+151** | **DRAFTED, measured;** after decision 1 and after the point-count result moved to III |
| III. Results | 980 | 1,040 | **+60** | item 7 extended 100 → 160 to carry the common-support answer, per the Methods/Results split |
| IV. Alternative explanations | 320 | 400 | **+80** | revised allocation; mediation row **and** its 176-word footnote struck |
| V. Discussion | 450 | 435 | **−15** | spec, unchanged |
| **TOTAL** | **3,300** | **3,476** | **+176** | |

**The letter is 176 words over budget.**

> **UPDATED 2026-08-26 after the Methods/Results split was applied.** The split was projected
> at II −40 / III +60, net +20, giving +161. **Measured, it is II −25 / III +60, net +35,
> giving +176.** The method sentences that had to stay in II-D — the ranking rule, the
> non-constructibility of point-level common support, and the post-treatment caveat on score —
> are longer than the estimate allowed. **The projection is recorded beside the measurement
> rather than replaced by it**, because the gap between them is the same class of error the
> transfer rule below exists to catch: a number agreed in advance and not checked afterwards.

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

---

## STANDING RESERVE CUT — decided 2026-08-26 on merit. NOT APPLIED.

**Fig. 2, the epoch-wise dose-response, together with the ~80 words of Section III item 5
that feed it. Half a column and 80 words.**

**Decided now, deliberately, so that it is not decided later under budget pressure.** If item 4
reproduces, Section IV grows and the three named candidates (−140) will not cover it; this is
the fourth, and it is recorded with its reasoning **before** the pressure exists, so that
taking it can never be an act of convenience dressed as editorial judgement.

**The justification is on merit, not on space. Each of these three would be a reason to cut it
even in a letter with room to spare:**

1. **"Dose-response" is an overreach for a training-time curve**, which is confounded with
   convergence — the arms are not being dosed with anything, they are being trained for longer.
   **This was accepted without dispute in the hostile review pass**, and a claim we have already
   conceded is not one to spend half a column illustrating.
2. **Its terminal point is out of range in our own data.** The curve ends at 0.487, which is
   seed 42's C4 − C5, and the six-seed block places that value **outside** the range spanned by
   the six replicates ([seed-block-results.md](seed-block-results.md) §5(c)). **Printing an
   out-of-range terminal point as a figure, in the paper whose own result is that single-run
   estimates land outside replicate ranges, is indefensible.** A reviewer who notices it has
   found us doing the thing we are reporting.
3. **It supports the weaker leg of the cold-discriminator row.** That row's actual evidence is
   the checkpoint sweep — C1 at epoch 1 already better than pretrained, −0.399 ± 0.064 at
   6.3 SE, the wrong sign for damage — which is **table-reportable and needs no figure**. The
   figure is illustrative rather than load-bearing, and the six-seed sustained-trend material
   now covers the same ground more rigorously and at seed level.

**Condition for applying it: only if the budget requires it after item 4 reports.** If item 4's
rows leave Table II, the letter is under budget and **this cut is not taken** — the figure
stays, weak but harmless, and the three reasons above are then arguments for the arXiv version
to carry it with its caveats rather than for deleting it.

**What the letter loses if it is taken:** one illustrative figure and the epoch-by-epoch shape.
**What it keeps:** the cold-discriminator refutation entire, in the table, on its stronger leg.

---

# STRUCTURAL DECISION, 2026-08-26 — the arXiv version is drafted at full length

**Read this before treating any per-block word allocation in this document as live. Most of
them are not.**

## The decision

**The binding deliverable on 15 October is the arXiv preprint, and arXiv has no page limit.
The GRSL submission is separate and later.** Therefore:

- **The arXiv version is drafted at full length.** Every section is written at the length its
  content requires.
- **The GRSL letter becomes a condensation of it**, performed in October, after the deadline
  that matters has been met.
- **Drafting against the per-block word allocations stops.** They were set on 24 August.

## Why

The 5-page format was chosen on 24 August. Since then the evidence has grown by the six-seed
block, two consequence firings, the out-of-range result, the sustained trend, the
common-support answer and the informative-mask test. **None of that is padding; all of it is
measured answers to reviewer objections.** Compressing it to fit a format chosen before it
existed would mean deleting answers to objections a reviewer will raise.

## What changes

- **The budget table is DEMOTED, not deleted.** It is now a **measurement of the condensation
  task ahead**, not a constraint on drafting. Every line is re-costed below against current
  required content and labelled **measured** (drafted) or **estimated** (not yet drafted) —
  because until now most were estimates presented as plan.
- **The reserve cut is SUSPENDED, not taken.** Fig. 2's merits are re-decided for the arXiv
  version on their own terms. **The out-of-range-endpoint objection is still real and still
  argues against it** — its terminal point is seed 42's value, which the six-seed block places
  outside the replicate range — but that is now a **merit** question, not a space one, and it
  is not decided here.
- **Material cut FOR SPACE returns to the arXiv version:** the 1/256 geometric-error finding
  with its variance qualifier, and the Liu/Zhang/Xiong and Fuentes Reyes citations.

## THE ONE CONSTRAINT, AND IT IS FIRM

> **LENGTH RELIEF IS NOT SCOPE RELIEF.**

The arXiv version carries the letter's material at proper length **plus what the letter cut for
space**. It does **not** reopen decisions made **on merit**. Explicitly and by name:

| cut | reason | status |
|---|---|---|
| 1/256 geometric error | **space** | **returns** |
| Liu/Zhang/Xiong; Fuentes Reyes | **space** | **return** |
| Mediation row | **merit** — "void as stated", corrections-log entry 20: the registered test could not have detected mediation of any size | **stays out** |
| Freirich, Michaeli, Meir | **merit** — supported only the withdrawn interaction claim | **stays out** |
| Cappadocia / ODTÜ contamination pair | **merit** — belongs to the second paper | **stays out** |
| λ_LPIPS sweep | **merit** — null manipulation on C5 (Adam is scale-invariant), non-monotone construct on C4 | **stays dead** |
| Held-out geography evaluation | **merit** — cancelled | **stays cancelled** |
| E3 in any form; E1/E2 tables; known-displacement recovery protocol | **merit/scope** — second paper | **stay out** |

**If a later session finds itself arguing that something cut on merit now fits because there is
room: the answer is no. Write the argument down and bring it to the supervising session
instead of acting on it.** Room is not a reason.

## The cause of block C's +96, recorded as a cause and not as an estimation miss

**The interaction disclosure's 120-word allocation was sized by subtraction, not by
requirement.** It was set to what the deleted interaction paragraph vacated — the old paragraph
was 120 words, so the replacement got 120 words. **The replacement is protected text with five
mandatory elements** (registered in advance; all three scales; 5/6 with the same seed breaking
each; no claim made; the other block reported with its weight stated). **Five mandatory
elements do not fit in 120 words, and the number was never checked against them.**

This is the supervising session's error and is recorded as such. It is also the clearest
instance of the general fault the other three concentrated overruns share: **allocations set
against what was known on 24 August, never re-costed when the required content grew.**

## Re-costed budget — measured versus estimated

| section | figure | basis | note |
|---|---|---|---|
| Title block + abstract | ~200 | **estimated** | abstracts stay short regardless of format |
| I. Introduction | ~570 | **estimated** | related work returns to ~220 with Liu/Zhang/Xiong and Fuentes Reyes restored |
| II. Materials and methods | **960** | **measured 901 + estimated 59** | drafted at 901; the 1/256 block returns, restoring the ~109-word treatment in place of the 50-word clause |
| III. Results | **1,327** | **MEASURED** | drafted; includes the 103-word informative-mask block |
| IV. Alternative explanations | **1,109** | **MEASURED** | drafted 2026-08-26 at required length; old letter allocation for the surviving content was 400 |
| V. Discussion | ~435 | **estimated** | not re-costed against current content; likely low, since the limitations list has grown |
| **Total so far** | **4,601** | four of six lines measured | against a 5-page format that held ~3,300. **The condensation task is ~1,300 words, and it is now measured rather than feared** |

**Two things this table now says that the old one did not.** First, **which numbers are
measurements and which are guesses** — three of six are guesses, and the two largest measured
lines both exceeded their guesses. Second, **the condensation task's size**: the arXiv draft is
already over the letter format by more than 200 words with two sections undrafted and Section V
likely under-costed. **That is the work to be scheduled for October, and it is now visible
instead of being discovered.**
