# DRAFT — Section IV, Alternative explanations

**Draft 1, 2026-08-26. Drafted at the length its content requires**, per the structural
decision of the same date: the arXiv version is the binding deliverable and the GRSL letter is
a condensation performed later. **Per-block counts at the foot — measurement, not a gate.**

Three rows survive. The mediation row is struck on merit (void as stated), and the
corrected-georeferencing row is answered by design in prose rather than by measurement.

---

## IV. ALTERNATIVE EXPLANATIONS

Four explanations compete with the account above. Three are tested and refuted; the fourth is
answered by the design itself and needs no test. Table II summarises; the prose gives each row
the evidence that supports it and the caveat that qualifies it.

### A. It is blur, not restraint

**The objection.** The L1-only arm produces smoother output, and feature matchers prefer
smoother imagery. If so, its advantage is a mechanical consequence of blur rather than of any
learned decision about what to render.

**The test.** The invention measurement is defined on input-silent pixels — those where the
conditioning input asserts no structure. Computing the *same* ratio on the complementary mask,
where the input does assert structure, separates the two explanations exactly, because **blur
suppresses edges uniformly while restraint suppresses them conditionally.** A smoothing
explanation predicts the L1-only arm below unity on both masks. A restraint explanation
predicts it near unity where the input is informative and far below where it is not. The
thresholds separating "near unity" from "suppressed" were fixed in advance at 0.80 and 0.50,
reusing the bands already registered for the original measurement rather than choosing new
ones.

**The result.** Across six seeds the L1-only arm reproduces the real image's edge density to
within 1.5% on the informative mask — 0.986, range 0.980 to 0.989 — while sitting at 0.277 on
the input-silent mask. **A factor of 3.6 between the two masks, in the same arm, on the same
chips, with the same operator, in every seed.** Both conditions hold six times out of six.
The other three arms sit between 1.03 and 1.05 on the informative mask, slightly above reality,
consistent with the 1.07 to 1.16 they show where the input says nothing.

**The reading.** Every arm except the L1-only one adds edges everywhere. The L1-only arm adds
them only where the input warrants it. **That is conditional suppression, which blur cannot
produce**, and the objection is refuted by a positive test rather than by a negative control.

**What this row is not.** It does not establish that the L1-only arm is optimal, nor that
restraint is the only mechanism in play — Section III's honest-limit paragraph stands. It
establishes that the smoothing explanation, specifically, does not fit the data.

### B. Cold-started discriminator damage

**The objection.** The published generator is deposited without its discriminator, so every
adversarial arm here begins from a randomly initialised one. Adversarial arms might therefore
lose because of a damaged start rather than because of the adversarial objective.

**The test.** A checkpoint sweep at epochs 1, 2, 5, 10 and 20, comparing each arm to the
pretrained generator and to its own counterpart.

**The result.** At epoch 1 the adversarial+L1 arm is **already better than pretrained**, by
−0.399 ± 0.064 px at 6.3 standard errors. **That is the wrong sign for startup damage**: an arm
crippled by a cold discriminator would begin worse than the checkpoint it started from, not
better. The adversarial deficit relative to the non-adversarial arm is present from epoch 1 at
+0.546 ± 0.048 and reaches +0.700 by epoch 20.

**The caveat, and it is ours rather than a reviewer's.** The path from epoch 1 to epoch 20 is
not monotone: it dips to +0.384 at epoch 5 before growing. **The registered bands for this
sweep did not anticipate that shape, and the conclusion is read off the curve rather than
matched to a band.** We state it that way because presenting it as a clean band hit would
misrepresent how it was obtained. The refutation does not depend on the shape — it depends on
the epoch-1 magnitude, which is large and correctly signed.

### C. Optimising the evaluation metric

**The objection.** The result might be an artefact of the KLT matcher used to produce it.

**The evidence, from two independent registrations.** The first varied the *descriptor family*:
ORB, AKAZE and mutual information all rank L1-only ahead of adversarial+L1 on both the Ankara
and European sets, with ORB at −0.613 ± 0.135 px. **Two caveats travel with these numbers and
are stated rather than buried.** The ORB figure is a paired difference over the **29 chips
where both arms matched**, not over the 53 chips where the L1-only arm matched at all; the
AKAZE figure rests on 11 paired chips. And the mutual-information margin of −1.260 ± 0.261 is
a **lower bound**, not an estimate: the registered subpixel refinement never ran, and the
search grid censors 15.8% of chips at its bound, censoring the worse arms harder and therefore
compressing the margin toward zero.

The second registration varied the *matcher family* rather than the descriptor: KLT, an NCC
template grid, and phase correlation, crossed with two band conversions and an urban subset
over 6,510 scored comparisons. **The arm ordering is preserved in every condition cell except
two**, both at the European urban subset under phase correlation, one in each band conversion,
and both far below the threshold at which an ordering change would be claimed. A registered
prediction that the template matcher would favour the sharper arm **failed in the direction
that strengthens the result**: the L1-only arm's margin grew rather than shrank, in all eight
set-by-conversion combinations.

**The reading.** The candidate is refuted by two registrations that share no matcher, no chip
set and no scoring code. **That is stronger evidence than either alone**, and it is the reason
this row is reported as two tests rather than one.

### D. Corrected georeferencing in the fine-tuning pairs

**The objection.** The fine-tuning pairs may be better georeferenced than the data the
published generator saw, so the advantage would come from the training data rather than from
the loss.

**The answer is in the design and needs no measurement.** No registered positional contrast
compares a fine-tuned arm with the pretrained generator: all four arms are fine-tuned on
identical pairs, so any georeferencing improvement is common to them and cancels.

**Why this replaces a measurement we previously reported.** An earlier decomposition attributed
roughly 86% of the European gain to scatter reduction rather than to a systematic shift, and
was reported as refuting this candidate. **That measurement's per-chip artifacts did not
survive and it cannot be reproduced**, which is disclosed in the data-availability statement.
The design argument is not a fallback: **it is stronger, because it depends on the structure of
the experiment rather than on a computation, and nothing can be lost that would make it
unverifiable.**

### E. Why the result is matcher-independent, mechanically

A blurred template gives a broad correlation peak; invented structure gives a sharp peak in the
wrong place. **A broad peak in the right place localises better than a sharp peak in the wrong
one**, and that is true of any matcher that localises by correlation. This is offered as the
mechanical reason the previous row's result is unsurprising, not as further evidence for it.

---

## Word count, by script

| block | old letter allocation | drafted |
|---|---|---|
| lead-in | — | 43 |
| A. It is blur, not restraint | 90 | 325 |
| B. Cold-started discriminator damage | 90 | 229 |
| C. Optimising the evaluation metric | 120 | 290 |
| D. Corrected georeferencing in the fine-tuni | 60 | 157 |
| E. Why the result is matcher-independent, me | 40 | 65 |
| **total** | **400** | **1109** |

**Section IV drafts at 1109 words.** The old letter allocation for the surviving content was
400 (90 blur + 90 cold-D + 120 matcher + 60 georeferencing + 40 mechanistic note), against a
revised section budget of 320 that it already exceeded.

**This is a measurement, not a gate.** Per the structural decision of 2026-08-26, sections are
drafted at the length their content requires and the budget records the condensation task.

**Where the length went, and none of it is padding:**

- **The blur row (A) is a different row from the one it replaces.** The letter's version was a
  90-word summary of a single-seed negative control. This is a six-seed positive test with a
  pre-committed threshold, a stated discriminating principle, and an explicit statement of what
  it does *not* establish.
- **The matcher row (C) carries two registrations instead of one**, because the audit found the
  letter's version had fused them. Both halves need their own n and their own caveats — the
  29-chip paired intersection and the mutual-information lower bound — and those caveats are
  binding sentences, not optional colour.
- **The cold-discriminator row (B) states its own non-monotonicity**, which the letter version
  did not. That is a caveat against ourselves and it costs words.
- **The georeferencing row (D) is prose, not a table row**, and it carries the disclosure that
  the measurement it replaces cannot be reproduced.

**For the October condensation**, the compressible parts of this section in priority order are
the "what this row is not" paragraph in A, the mechanical note in E, and the second half of C's
caveat text — roughly 649 words recoverable before anything load-bearing is touched.

