# DRAFT — Section III, Results

**Draft 1, 2026-08-26.** Structure and word allocation follow the letter skeleton's Section III
spec as revised, including the two new subsections and the +60 point-count material moved from
Section II-D. **Per-block word counts and the hypothesis verdict are at the foot of this file.**

Manuscript prose begins below the rule.

---

## III. RESULTS

### A. The panel

Table I gives all five arms over 130 Ankara chips, averaged across six independent training
seeds. The ordering is **L1-only < LPIPS-only < adversarial+LPIPS < adversarial+L1 <
pretrained**, from 1.39 px to 2.56 px, and it is the same ordering in every seed. Both
adversarial arms sit above both non-adversarial ones; the two adversarial arms are separated by
0.005 px, and the two non-adversarial arms by 0.063 px.

### B. Primary result

**Removing the adversarial term improves positional accuracy under the perceptual
reconstruction loss in all six seeds.** Per seed, LPIPS-only minus adversarial+LPIPS is −0.615,
−0.646, −0.616, −0.594, −0.605 and −0.578 px. The direction was fixed in advance from an
earlier seed and registered before these six were trained, so under a null of no effect the
probability of six agreeing signs is **1/64**.

The seed-level mean is −0.609 px, with a 95% interval of [−0.634, −0.585] at five degrees of
freedom. **That interval is reported, not required:** the registered reading is the sign
replication, and no interval was a gate for it in either direction.

Inference is at the seed level throughout. The treatment was applied once per training run, so
a standard error computed across evaluation chips measures how consistently one checkpoint
beats another, not how consistently the intervention works. **Every contrast in this section is
one number per seed, with variability taken across seeds.**

### C. Interaction: registered, tested, not sign-stable, not claimed

Before any replication data existed we registered a seed-level interaction between the two
reconstruction terms — the adversarial penalty under a perceptual loss minus the adversarial
penalty under L1 — to be read as negative in every seed **and** to survive a monotone
re-scaling, with both re-scalings specified in advance: a natural-log transform of the
per-chip residual, and a within-chip rank transform across the four arms.

**Across the six confirmatory seeds the interaction was negative in five and positive in one,
and the same seed reversed the sign on the log and rank scales as well: five of six on each of
the three registered scales.** The registered reading therefore fails, and by a consequence
committed in advance we make no interaction claim in this paper.

An earlier two-seed block, run on different hardware, returned a negative interaction in both
of its seeds on all three scales. It is reported here for completeness and carries no weight
against the six-seed result, because the two blocks cannot be pooled and two seeds do not
override six.

The seed-level means are negative on all three scales, and the log-scale and rank-scale
intervals exclude zero. **These are reported, not required, and they do not reinstate a reading
whose criterion was sign stability across seeds rather than a nonzero mean.**

### D. Secondary result

**The perceptual reconstruction loss carries its own positional penalty with no discriminator
present**: LPIPS-only minus L1-only is positive in all six seeds, again P = 1/64, with a
seed-level mean of +0.063 px and a 95% interval of [+0.027, +0.098] at five degrees of freedom,
reported not required. **The narrowest seed clears zero by 0.007 px.** This is a consistent
small positive effect, six times out of six, and it should be read as consistent rather than as
comfortable.

### E. Dose-response

The adversarial penalty under the perceptual loss, measured at epochs 1, 2, 5, 10 and 20, runs
0.334, 0.254, 0.441, 0.496 and 0.487 px, every value at six standard errors or more, with the
same dip-then-grow-then-plateau shape as the L1 family. Training longer with a discriminator
widens the gap under both reconstruction terms. **This is a training-time curve and is
confounded with convergence; it is reported as a shape, not as a dose.**

### F. Mechanism

The edge-ratio column of Table I measures, per chip, how much structure an arm renders where
the conditioning input asserts none, relative to the real image. **With no discriminator
anywhere, the perceptual loss alone invents the most: 1.15 against 1.13 for adversarial+LPIPS,
1.09 for adversarial+L1 and 1.02 for the pretrained generator.** L1-only is the outlier in the
other direction at 0.28. Every value is a six-seed mean and the ordering holds in all six.

This was the registered prediction for the LPIPS-only arm, and it is the single result that
widens the claim from "the adversarial term degrades matchable content" to "any plausibility
pressure does". **An arm with no discriminator invents more than either arm that has one.**

### G. The point-count argument, and the selection objection

The obvious objection to the L1-only result is that it simply produces fewer features, and
fewer-but-better is a trivial trade. **The LPIPS-only arm refutes it on this panel**, which is
named in the sentence: it produces more surviving matches than L1-only, 88 against 72 at the
median, and still scores worse. The harm is not about feature count; it is about features with
no grounding in the input.

**A second, sharper form of the objection is that each arm's residual is a median over the
matches that arm itself produced.** Equalising counts per chip — every arm truncated to the
smallest count any arm achieved there, ranked by match score — the LPIPS-only arm surrenders
38% of its points. **Under equalised counts the primary contrast grows by 1.8%, the LPIPS-only
penalty shrinks by 11%, and both hold in all six seeds.** A minimum-match-count sweep moves the
penalty **upward**, every seed at or above +0.037 px at a floor of 30 matches — the opposite of
what a selection artefact predicts.

### H. Restraint, not smoothing

A remaining explanation is that L1-only is simply blurrier, and that the matcher prefers
smoother imagery. **Computing the same edge ratio on the complementary mask — the pixels where
the input does assert structure — separates the two, because blur suppresses edges uniformly
while restraint suppresses them conditionally.** L1-only reproduces the real image's edge
density to within 1.5% there (0.986) while sitting at 0.277 where the input says nothing: a
factor of 3.6 between the two masks, in all six seeds, against thresholds fixed in advance. A
smoothing explanation predicts suppression on both masks. **The suppression is conditional on
what the input knows.**

### I. The single-run estimate outside the replicate range

The interaction we previously published from one run, −0.212 px, **falls outside the range
spanned by six replicates of the same treatment** on the raw scale and on the rank scale. The
treatment was applied once per cell, so every error bar on that number was chip-level. Six
replicates do not contain it, and its sign flips in one of them.

Falling outside a six-replicate range is not a significance test and no p-value attaches to it.
What makes it reportable is that it happens on the quantity a mechanistic claim was built on,
in the direction that favoured the claim, while the registered reading on that same quantity
independently fails.

### J. The sustained training trend

Registered before the training logs were read and scored at six seeds. **What the data
supports: in every seed, each adversarial arm reduces its reconstruction loss less than its
non-adversarial counterpart** — six of six in both families. **What it does not support:
that adversarial arms fail to reduce the reconstruction loss.** That arm-level reading holds
for adversarial+LPIPS in all six seeds, mean +1.45%, but fails for adversarial+L1, which falls
in one seed and is indistinguishable from flat in another.

Adversarial+LPIPS is the arm whose training-stability rule fired, so the operative form of the
argument is the one that replicates. The comparison that isolates the discriminator holds the
learning-rate schedule fixed on both sides and gives a gap of 6.33 points under the perceptual
loss; the L1-family figure of 4.00 rests on an arm whose sign is not stable and on an
attenuation inside the seed spread, and is not quoted as equivalent.

### K. The honest limit

The edge ratio separates the restrained arm from the unrestrained ones; it does not order the
errors within the unrestrained group. **Invention is a necessary condition, not a complete
explanation.** The route difference is offered as the partial account it is: the discriminator
produces texture that is largely unmatchable, high ratio and low point count, while the
perceptual loss produces structure that is matchable but misplaced, high ratio and the highest
point count of any arm. Both hurt, by different routes.

---

## Word count, by script

| block | spec | draft | Δ |
|---|---|---|---|
| A. The panel | 80 | 68 | -12 |
| B. Primary result | 120 | 155 | +35 |
| C. Interaction disclosure (protected) | 120 | 216 | +96 |
| D. Secondary result | 60 | 79 | +19 |
| E. Dose-response | 80 | 73 | -7 |
| F. Mechanism | 140 | 118 | -22 |
| G. Point-count + selection | 160 | 170 | +10 |
| H. Restraint, not smoothing | — | 103 | n/a |
| I. Out-of-range | 80 | 111 | +31 |
| J. Sustained trend | 100 | 153 | +53 |
| K. Honest limit | 100 | 81 | -19 |
| **total** | **1,040** | **1,327** | **+287** |

**Section III drafts at 1,327 words against a 1,040 allocation: +287.**

**Note on block H.** "Restraint, not smoothing" has **no spec allocation** — it is the
informative-mask test, which did not exist when the skeleton was written and replaced the lost
blur control only today. It is therefore **uncosted material by definition**, and at 103 words
it is the single largest contributor to any overrun. Every other block was costed in advance.

## THE HYPOTHESIS — IT FAILED

> **COSTED MATERIAL FITS THE SPEC. UNCOSTED MATERIAL DOES NOT.**

**Costed blocks only** (A–G, I–K, excluding the uncosted H): spec **1,040**, drafted
**1,224**, **+184**.

**Verdict: the hypothesis FAILS, and it is not close.** Excluding the one block that could not
have been costed, the costed blocks still overran their combined allocation by 184 words —
18%. The Section II evidence that suggested the hypothesis (costed blocks there came in at
−53) does not generalise.

**Where the overrun is, and it is not spread evenly:**

| block | Δ | costed? | comment |
|---|---|---|---|
| C. Interaction disclosure | **+96** | yes, 120 | The largest single miss. It is **protected text** with five mandatory elements, and 120 words was never enough to carry all five. **The allocation was wrong when it was written**, not overspent when it was drafted |
| J. Sustained trend | **+53** | yes, 100 | Carries a can-say/cannot-say distinction, an arm-versus-gap split, and two magnitudes with unequal weight. Three ideas in 100 words |
| B. Primary result | +35 | yes, 120 | Six per-seed values, the P-value, the interval with its disclaimer, and the seed-level inference statement |
| I. Out-of-range | +31 | yes, 80 | The result plus its mandatory scope sentence |
| D. Secondary | +19 | yes, 60 | The narrowest-margin sentence was added after costing |
| G, A, E, F, K | −50 net | yes | **Five blocks came in under.** The spec is not uniformly optimistic |

**The honest diagnosis is narrower than "specs under-cost".** Five of ten costed blocks came in
at or under allocation. **The overrun concentrates in blocks whose content grew after the
allocation was set** — C, J, B and I together are +215 of the +184 net, and every one of them
gained mandatory content from the six-seed work, the consequence firings, or the audits.
**Their allocations were costed against what the skeleton knew on 24 August, and the content
they must now carry is larger.** That is a stale-allocation problem, not an estimation-bias
problem, and the fix is different: **re-cost a block when its required content changes, not
only when new blocks are added.**

**What this means for the budget.** The reconciled budget's Section III line of 1,040 is wrong
and should be **1,327**, of which 103 is the informative-mask block that did not exist when the
budget was built. The letter's total moves accordingly and **the reserve cut is now likely to
be needed** — but that is a decision for the supervising session, not one taken here, and no
cut has been made.

**One thing the failure does not undermine.** The two blocks that were costed *at the time they
were added* — the out-of-range result and the sustained trend, both added 2026-08-26 — came in
at +31 and +53. **Costing at the moment of addition was better than not costing at all, and
still not sufficient.** The lesson is that a 100-word estimate for material that does not yet
exist in draft is an estimate, and should be labelled as one.
