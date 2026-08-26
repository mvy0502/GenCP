<!-- PROVENANCE HEADER — added on import, 2026-08-26. The body below this rule is
     unmodified. -->

**Provenance of this document.**

- **Originated in the Claude project** at `claude/mektup-iskeleti.md`, written **2026-08-24**
  by the supervising session, **on single-seed (seed 42) data**.
- **Imported into the repository unchanged on 2026-08-26**, so that the six-seed revisions
  can be recorded as revisions against a version-controlled original rather than against a
  document that exists only outside the repository.
- **Fidelity caveat, stated because it is true.** The imported text was transcribed from the
  project document by the supervising session and **has not been cryptographically verified
  against it**. **The project copy remains canonical for any dispute.**
- **It now lives in the repository** because the writer needs to read it, and because this
  project keeps its record under version control.

**Two candidate files were present at import. The divergence was RESOLVED on 2026-08-26
against the canonical project copy, and the resolution is recorded here so it cannot be
re-litigated.** Both files were 300 lines and differed in exactly one place, line 280,
binding sentence 13.

| file | sha256 | mtime | line 280 | status |
|---|---|---|---|---|
| `letter-skeleton.md` | `e014d9264d4d579f089b36c16de1fc107e52e58f0a01bc89983c76b0925a8a2a` | 2026-08-24 14:44 | "…not a code bug." | **IMPORTED. CONFIRMED to match the canonical project copy.** |
| `letter-skeleton-ORIGINAL-24aug.md` | `5f6b4d8ab234eb0af1b2dc2d0c9d14936a8c667a93e2c17507870745f248e041` | 2026-08-26 11:23 | "…not **as** a code bug." | **DRIFTED. A transcription made by the supervising session, in which the inconsistency was normalised. MUST NOT be imported later.** |

**The resolution.** The supervising session re-read the canonical project copy on 2026-08-26
and confirmed that it reads **"not a code bug"** at binding sentence 13 and **"not as a code
bug"** in the §3 Materials-and-methods bullet. **The project original is itself internally
inconsistent**, and the Aug 24 file reproduces that inconsistency faithfully. The second file
is not an earlier or better original: it is the supervising session's own transcription, in
which the inconsistency was normalised without the change being noticed. **The fidelity
caveat above turned out to describe the transcription rather than the import.**

**The import stands and no correction commit was made.** The internal inconsistency was
preserved at import time deliberately, under the byte-for-byte rule, and that decision is now
confirmed correct rather than merely defensible. Binding sentence 13 was subsequently brought
into line with the methods bullet as an ordinary dated editorial correction **in the revision
layer, with the original struck** — see the note at §4 item 13. That is a revision, not a
retroactive change to the import, and the two must not be confused.

---

# GRSL letter skeleton and page budget

Drafted 2026-08-24 by the paper supervisor session. Structural decisions recorded before
drafting, per standing practice. Supersedes nothing; it implements the amended scope in
`paper-roadmap.md` (amendment `c809ee8`).

**Working title.** *Plausibility Pressure Degrades Generated Reference Imagery for Geometric
Matching.* Alternative if a venue prefers concreteness: *Adversarial and Perceptual Losses Cost
Positional Accuracy in Generated Georeferencing References.*

**Target.** IEEE GRSL, 5 pages including references, two columns, roughly 10 columns total.
arXiv preprint first.

---

## 1. Page budget

| Element | Columns | Words |
|---|---|---|
| Title, authors, abstract, index terms | 0.5 | 200 |
| I. Introduction (related work folded in) | 1.5 | 600 |
| II. Materials and methods | 2.0 | 750 |
| III. Results — includes Table I and Fig. 1 | 2.5 | ~~800~~ **980** |
| IV. Alternative explanations — includes Table II | 1.5 | ~~500~~ **320** |
| V. Discussion, limitations, design rule | 1.0 | 450 |
| References (~30) | 1.0 | — |
| **Total** | **10.0** | **~3,300** |

Figures and tables consume roughly two of those ten columns. The budget has no slack. Any
section that overruns takes the space from Section IV, which is the only one that degrades
gracefully (a row can move to the arXiv version).

**REVISED 2026-08-26 — 180 words moved III ← IV, and the column figures are unchanged.** The
word counts for Sections III and IV are struck above and replaced; the column allocations are
not, because 180 words is roughly a fifth of a column and the two sections are adjacent — the
overrun is absorbed within their combined 4.0 columns. The 180 words pay for two new Results
subsections that the six-seed block made mandatory: the out-of-range result (III.9, 80 words)
and the sustained training trend (III.10, 100 words). **Taken from Section IV per the rule
this section already states**, and the mediation row is the designated casualty if 320 words
will not hold five rows. **Total word count rises from ~3,300 to ~3,300 — unchanged, because
this is a transfer and not an expansion.**

**Two figures, two tables. Not three of either.**

- **Fig. 1** — the three-panel input / generated / real comparison, chip `36SXJ_6_20`. Empty
  input, high-contrast reality, pretrained invents a parcel mosaic, L1-only declines to invent,
  both score the same. It shows the ceiling: information absent from the input cannot be
  recovered. This is the single most explanatory panel we have and it earns a full column width.
- **Fig. 2** — dose-response: adversarial penalty by epoch, both reconstruction families on one
  axis. Half column. Supports Section IV's cold-discriminator row.
- **Table I** — the five-arm panel *with the edge ratio as a column* (see §2).
- **Table II** — alternative explanations, four columns: candidate / test / result / verdict.

**Cut from the letter, recorded so it is not reinstated by accident:** the ODTÜ/Cappadocia
contamination pair (moves to the second paper with T1 and E3), the known-displacement recovery
protocol, E3 in any form, and the E1/E2 tables. E1/E2 survive as two sentences in Section I.

---

## 2. The structural decision that pays for the budget

**Table I merges the positional panel and the edge ratio into one table.**

| arm | objective | mean (px) | median (px) | points (med.) | edge ratio |
|---|---|---|---|---|---|
| pretrained | adv + LPIPS (European) | 2.563 | 2.588 | 51 | 1.02 |
| C1 | adv + L1 | 2.075 | 1.794 | 59 | 1.10 |
| C2 | L1 | **1.376** | **0.974** | 72 | **0.28** |
| C4 | adv + LPIPS | 1.966 | 1.918 | 62 | 1.12 |
| C5 | LPIPS | 1.478 | 1.134 | **88** | **1.16** |

*All five arms from one labelled run: STOCH seed 42, Overpass inputs, n = 130 Ankara chips.
Δ = candidate − baseline; negative means the candidate is better. Edge ratio = edge density in
input-silent regions relative to the real image; 1.0 means the arm fills terrain it has no
information about to exactly the busyness of reality.*

> **TABLE I REQUIRES A REBUILD FROM THE SIX-SEED BLOCK — flagged 2026-08-26, not yet done.**
> The table above is **single-seed** (seed 42) and seed 42 is the generating observation, not
> a replicate. It is left standing because it is the layout decision this section exists to
> record, and the layout survives; only the numbers in it do not.
>
> **Columns that change** — every one of these becomes a six-seed quantity (seeds 45–50), with
> the seed count in the caption and seed 42 reported beside the table rather than inside it:
> **mean (px)**, **median (px)**, **points (med.)**, and **edge ratio** for the four
> fine-tuned arms C1, C2, C4, C5. The six-seed edge-ratio means are already computed
> ([seed-block-results.md](seed-block-results.md) §1) and differ from the single-seed values in
> the third decimal, not the first — C2 0.277 against 0.28, C5 1.152 against 1.16 — so **the
> non-monotonicity this table exists to display survives the rebuild**, which is the one thing
> worth knowing before the rebuild is done.
>
> **The column that does NOT change: the `pretrained` row.** Pretrained is
> **training-independent** — it is the deposited generator, not a fine-tuning arm, so it has
> no seed and its numbers are identical across every seed in the block (edge ratio 1.0208 in
> all six, byte-identically). Its row is carried over unchanged and the caption must say why,
> or a reader will ask which seed it came from.
>
> **What else the caption must gain:** the run label changes from "STOCH seed 42" to the
> six-seed block with its n, and the sign convention and Δ definition are unaffected.
> **Do not draft Table I until the rebuild is done** — it is the table the headline sits in.

Two reasons, and the second matters more than the space saving.

It saves half a column, which the budget needs.

And it puts the non-monotonicity in front of the reader in the same table that carries the
headline. C5 has the highest ratio and the second-best score; pretrained has the lowest ratio of
the unrestrained arms and the worst score. Within the four inventing arms the ratio does not
order the errors at all. A reviewer who plots these five points will find that. Presenting them
together, with the honest reading attached, converts a discoverable weakness into a stated
scope limit. The sentence that must sit beside the table: **invention is a necessary condition,
not a complete explanation.**

---

## 3. Section-by-section content

### Title block and abstract (200 words)

Abstract must contain, in this order: the setting (generated reference imagery for satellite
georeferencing), the design (2×2 factorial crossing an adversarial term with L1 versus LPIPS
reconstruction, everything else held fixed), the primary number ~~(C5 − C4 = −0.487 ± 0.053 px,
t = −9.2, better on 113/130 chips)~~ **REVISED 2026-08-26 — the abstract's primary number is
now the seed-level six-seed sign replication:** *adversarial-off beats adversarial-on under
LPIPS in all six confirmatory seeds (P = 1/64, direction fixed in advance)*, the generalisation
(the effect replicates under both
reconstruction terms, and LPIPS alone invents more than either adversarial arm), the mechanism
(edge density in input-silent regions), and the design rule.

*Two changes, and the second is a rule. **(i)** The struck number is chip-level and
single-seed: ±0.053 measures how consistently one checkpoint beats another across 130 chips,
not how consistently the treatment works, and that conflation is the correction the whole
seed-replication package exists to make. **(ii) The abstract carries NO interval at all**, per
the adversarial pass's instruction to strike the primary interval from the abstract — a sign
replication with its P-value is the claim, and an interval in an abstract invites exactly the
chip-level-as-treatment-level reading. Results III.2 may report the interval; the abstract may
not. Six-seed values are in [seed-block-results.md](seed-block-results.md) §1 and §5(a).* Index terms: image registration,
generative adversarial networks, ground control points, perceptual loss, georeferencing,
Sentinel-2.

### I. Introduction (600 words)

1. **Setting, 100 words.** Satellite georeferencing needs reference imagery; GCP chip databases
   are the standard instrument; generated references are proposed to sidestep licensing.
2. **The instance, 80 words.** GenCP: pix2pix renders a Sentinel-2-like image from OpenStreetMap
   plus land cover. Its published HR objective is adversarial + λ·LPIPS with λ = 100 and a BCE
   discriminator, and **the LPIPS substitution is stated without supporting evidence in the
   upstream text** — no L1-versus-LPIPS comparison, no ablation of the adversarial term.
3. **Scope, two sentences only.** At 10 m the premise does not bind: free Sentinel-2 and EOX
   cloudless mosaics were available in 24/24 stratified Turkish extents with a median of two
   days since the last cloud-free scene, and a five-year-old real scene beat current-OSM
   synthetic even on the highest-change tile. Footnote to the arXiv version for both. **Do not
   argue this in the letter; state it and move on.** It sets scope, it is not the contribution.
4. **The claim, 60 words.** ~~Plausibility pressure degrades generated reference imagery for
   geometric matching; the adversarial term and a perceptual reconstruction loss are both such
   pressures and act on the same lever.~~ **REVISED 2026-08-26 — the claim now reads:**
   *Plausibility pressure degrades generated reference imagery for geometric matching; the
   adversarial term and a perceptual (LPIPS) reconstruction loss are each such a pressure,
   established separately.* Where the conditioning input carries no information, a
   loss that rewards plausibility causes the generator to invent structure; an invented edge is
   a false control point, and a false control point is worse than no control point because it
   displaces the solution silently.

   *"and act on the same lever" is dropped: the registered interaction reading failed at 5/6
   across six confirmatory seeds on all three registered scales and the pre-committed
   consequence fired ([seed-block-results.md](seed-block-results.md) §4). **This wording is
   copied verbatim from [paper-context-addendum.md](paper-context-addendum.md) §1, which is
   the live claim statement; the two must not drift, and a change to either requires the same
   change to the other in the same commit.** "Separately" is load-bearing — it marks the
   absence of a joint claim rather than leaving a reader to supply one.*
5. ~~**Related work, 220 words, compressed hard.**~~ **REVISED 2026-08-26: ~150 words,
   FOUR citations.** The original bullet is preserved below. The skeleton itself names this
   paragraph as the most compressible in the letter, and this is where the Section II
   overrun is paid from — related work compresses without losing a result; Section IV's rows
   *are* results.

   **The four that survive, with the reason each is non-negotiable — recorded so the choice
   is not re-litigated when Section I is drafted:**

   - **Blau and Michaeli** — the perception-distortion tradeoff itself. Everything the letter
     says about *why* plausibility costs accuracy rests on it. Position as identifying the
     consumer, never as contradicting the theory.
   - **Arar et al.** — **NON-NEGOTIABLE.** The only prior loss ablation scored against a
     registration metric, **and its sign is opposite to ours.** Omitting it would read as
     suppressing contrary evidence, which is the single accusation this letter can least
     afford. The distinguishing sentence stays: joint training there, frozen deliverable and
     exogenous matcher here.
   - **Chen, Ohayon et al.** — proves information-theoretically that pursuing perceptual
     quality converts uncertainty into confidently rendered false detail. Our mechanism,
     predicted in advance by someone else; it makes the finding expected rather than odd.
   - **Merkle et al.** — established feeding translation output into a matching pipeline and
     never asked whether a matched point was real. Without it the letter has no statement of
     what the field currently does.

   **Moved to the arXiv version:** Liu, Zhang and Xiong (the downstream-task extension — a
   semantic task where an in-class hallucination costs nothing, so the distinction is real
   but not load-bearing) and Fuentes Reyes et al. (named "fiction" in SAR-to-optical in 2019
   and observed that no suitable metric existed — rhetorically strong, evidentially
   redundant once Chen/Ohayon is cited). **Both are cut for space, not for disagreement, and
   the arXiv version carries them.** Freirich, Michaeli and Meir is **not** in this list and
   is not cut for space: it was removed on its merits when the interaction claim was
   withdrawn, since it supported only that claim.

   *Original bullet, preserved:*

   > 5. **Related work, 220 words, compressed hard.** Blau and Michaeli give the theory; position as
   >    identifying the consumer, not contradicting it. Liu, Zhang and Xiong extend it to a
   >    downstream task, but a semantic one where an in-class hallucination costs nothing. Arar et
   >    al. is the only prior loss ablation scored against a registration metric and its sign is
   >    opposite, because there translation and registration train jointly. Chen, Ohayon et al. prove
   >    information-theoretically that pursuing perceptual quality converts uncertainty into
   >    confidently rendered false detail — our mechanism, predicted. Fuentes Reyes et al. named
   >    "fiction" in SAR-to-optical translation in 2019 and wrote that no suitable metric existed;
   >    seven years later the field still evaluates with FID and LPIPS. Merkle et al. established
   >    feeding translation output into a matching pipeline and never asked whether a matched point
   >    was real.

6. **Contributions, 3 bullets, 60 words.** (i) A 2×2 factorial isolating plausibility pressure
   with a positional outcome. (ii) A cheap, input-conditioned, reproducible measurement of
   invention, tied to matchability rather than to perception. (iii) A design rule for anyone
   generating reference imagery for a geometric consumer. All phrased "to our knowledge".

### II. Materials and methods (750 words)

- **Model and fine-tuning, 120 words.** pix2pix, U-Net-256 generator (54.414 M parameters),
  PatchGAN discriminator, `--direction BtoA`. 5,577 Turkish pairs, 20 epochs, seed 42,
  `--lr_policy linear` 10+10, single T4.
- **The design, 120 words.** The 2×2 table. State what is held fixed: training data, schedule,
  seed, initialisation, evaluation chips, matcher, KARIOS configuration. State that the
  pretrained weights already occupy the C4 cell, trained on European data rather than fine-tuned
  on ours, rather than presenting C4 as an empty cell. State that C4 and C5 reproduce **the
  repository's executable definition** of the published objective, in those words.
- **Disclosure, 60 words.** The discriminator is not published; only the generator is deposited.
  Every arm with an adversarial term starts from a randomly initialised, seeded discriminator,
  recorded in a provenance file. Section IV shows this is not what causes the adversarial arms
  to lose, but it is a deviation from the published training setup.
- **Evaluation, 150 words.** KARIOS, KLT feature matching, `confidence_threshold: 0.8`, against
  real Sentinel-2. 130 Ankara chips stratified into five quintiles by land-cover information
  density. One sign convention, repeated in every table header. Every number states its
  inference path and input provenance; test-time dropout is active and is pix2pix's own design,
  not a defect, and a deterministic mode was measured to be score-neutral within ±0.15 px.
- **The invention measurement, 120 words.** Input-silent pixels defined as canonical Sobel ≤ 20
  on the input render; edge fraction (Sobel > 20) of each arm's output over the real chip's edge
  fraction on the same pixels; per-chip ratio, reported per arm. Say why the denominator is the
  input and not the ground truth: it separates "invented where nothing was known" from "wrong
  where something was known", which is the distinction every existing hallucination metric
  lacks.
- ~~**A geometric error in the published pipeline, 100 words + repo pointer.** 257×257 rasters at
  10 m resampled to 256×256 with the transform copied unchanged gives a true GSD of
  10.0390625 m against a declared 10.0, an error of exactly 1/256, up to 14.1 m at the chip
  corner. Corrected in our path. **Carry the qualifier or the claim overreaches: the systematic
  component is consistent with the signs and magnitudes of the published means, but predicted
  std is 2.89 m against an observed sigma of 14.5–17.3 m, so it explains roughly 3.9% of the
  reported variance and does not invalidate their conclusions.** Describe it as a
  text-versus-data inconsistency, not as a code bug. Pin the audited commit.~~

  **MOVED TO THE ARXIV VERSION, 2026-08-26.** Struck here, not deleted, and not withdrawn —
  the finding stands and is published, in the extended version where it has room. Three
  reasons: **(i)** it does not support the claim; **(ii)** its own paragraph has to walk it
  back, since it explains 3.9% of the upstream variance and the qualifier is mandatory;
  **(iii)** it opens a second front in a letter with one thesis. **Reason (iii) got heavier
  on 2026-08-26: the GenCP authors will be reading this draft, and a primary critique that
  also carries a secondary fight is both weaker as an argument and harder to send.**
  **What stays in Section II is one clause**: that our path corrects a ground-sampling-distance
  inconsistency in the published resampling step, so our geometry is not identical to theirs,
  with a pointer to the extended version. **The finding leaves; the disclosure that our
  geometry differs stays** — a reader must not be able to think the two pipelines are
  identical. Saves ~59 words in the drafted Section II.

- **Registration statement, 40 words.** The binding wording, verbatim.

### III. Results (800 words, Table I, Fig. 1)

1. **The panel, 80 words.** Table I. Point at the ordering C2 < C5 < C4 < C1 < pretrained.
2. **Primary result, 120 words.** ~~C5 − C4 = −0.487 ± 0.053 px (t = −9.2, better on 113/130
   chips; registered band was ≥ 2 SE). Adversarial OFF beats ON under *both* reconstruction
   terms. The main effect is replicated, not observed once.~~

   **REVISED 2026-08-26 — the primary is now stated at seed level, where the treatment was
   applied.** *C5 − C4 is negative in all six confirmatory seeds (45–50), P = 1/64 with the
   direction fixed in advance by seed 42; per-seed values −0.6153, −0.6462, −0.6162, −0.5942,
   −0.6054, −0.5775 px. Adversarial OFF beats ON under both reconstruction terms. The main
   effect is replicated across seeds, not observed once.* The seed-level mean is −0.609 px
   with a 95% interval of [−0.634, −0.585] (df = 5, t\* = 2.571) — **and that interval is
   reported, not required: the registered reading is the sign replication and only that.**
   Attach the phrase, not just the number.

   *The struck version was the single-seed chip-level statement. It is preserved because it is
   what the plan said before the block ran, and because the difference between the two is the
   paper's own methodological point. Seed 42's −0.487 is now reported beside the block as the
   generating observation, and it falls **outside** the six-seed range on this quantity
   ([seed-block-results.md](seed-block-results.md) §5(c)) — do not present it as one of the
   replicates.*
3. ~~**Interaction, 120 words.** Adversarial penalty under L1 = +0.700 ± 0.059; under LPIPS =
   +0.487 ± 0.053; I = −0.212 ± 0.069 (t = −3.07): substitutes. LPIPS already supplies part of
   the plausibility pressure, so the discriminator adds less on top of it. Consistent with
   C4 − C1 = −0.110 (1.9 SE) — **write "not significant at the registered threshold", never
   "null".**~~

   **DEAD, SUPERSEDED 2026-08-26. This subsection is replaced in full, not amended.** The
   registered seed-level interaction reading failed at 5/6 across the six confirmatory seeds —
   seed 46 is positive on the raw scale and reverses on the log and rank scales too — and the
   pre-committed consequence removed "substitutes", "the same lever" and the interaction claim
   from the paper ([seed-block-results.md](seed-block-results.md) §4). **The 120 words do not
   return to the budget: they are spent on the disclosure that replaces the claim**, which is
   mandatory, not optional. What goes here is the letter-length version of the required text
   installed at [paper-context-addendum.md](paper-context-addendum.md) §24:

   > **Interaction: registered, tested, not sign-stable, not claimed.** Before any replication
   > data existed we registered a seed-level interaction between the two reconstruction terms,
   > I = (C4 − C5) − (C1 − C2), to be read as negative in every seed and to survive a monotone
   > re-scaling, with both re-scalings — a log transform of the per-chip residual and a
   > within-chip rank transform — specified in advance. Across six confirmatory seeds it was
   > negative in five and positive in one, and the same seed reversed the sign on the log and
   > rank scales as well: 5/6 on each of the three registered scales. The registered reading
   > fails, and by a consequence committed in advance we make no interaction claim. An earlier
   > two-seed block on different hardware returned a negative interaction in both seeds on all
   > three scales; it is reported for completeness and carries no weight against the six-seed
   > result, since the blocks cannot be pooled and two seeds do not override six.

   *Three rules travel with this paragraph. **(i)** It may be shortened for the format but may
   not lose any of five elements: registered in advance, all three scales, 5/6 with the same
   seed breaking each, no claim made, the other block reported with its weight stated.
   **(ii)** The log and rank interval do exclude zero and the raw one does not — **never write
   any sentence of the form "the interval excludes zero, so the interaction is real"**, or
   anything that functions as one. An interval is not a back door to a failed reading.
   **(iii)** C4 − C1 keeps its own binding sentence (§4, item 3) and is unaffected by this
   change.*
4. **Secondary, 60 words.** ~~C5 − C2 = +0.103 ± 0.042 (t = 2.5): perceptual reconstruction
   carries its own positional penalty with no discriminator present.~~

   **REVISED 2026-08-26 — six-seed, seed-level:** *C5 − C2 is positive in all six confirmatory
   seeds, P = 1/64; perceptual reconstruction carries its own positional penalty with no
   discriminator present.* Seed-level mean +0.063 px, 95% interval [+0.027, +0.098]
   (df = 5, t\* = 2.571), **reported, not required**. The smallest margin is +0.0068 px at
   seed 46 — **state it; it is the thinnest of the registered readings and a reader who finds
   it unaided will trust the rest less.**

   *Why this subsection matters more than its 60 words suggest: **the secondary holding 6/6 is
   what kept the title.** The registered consequence for C5 − C2 was that if it failed in any
   seed, the LPIPS-alone penalty would drop from a result to a discussion-section hypothesis
   and the claim would narrow from "plausibility pressure" to "the adversarial term", **taking
   the title with it**. It held, so the working title survives — but on a 6/6 sign replication
   whose narrowest seed clears zero by seven thousandths of a pixel, not on a comfortable
   margin.*
5. **Dose-response, 80 words + Fig. 2.** Penalty by epoch under LPIPS: 0.334 → 0.254 → 0.441 →
   0.496 → 0.487, all ≥ 6 SE, the same dip-then-grow-then-plateau shape as the L1 family.
   Training longer with a discriminator widens the gap under both reconstruction terms.
6. **Mechanism, 140 words + Fig. 1.** The edge-ratio column. With no discriminator anywhere,
   LPIPS alone invents more than the adversarial arms do — the registered primary prediction for
   C5, and the single result that widens the claim from "adversarial" to "plausibility pressure".
7. **The point-count argument, 100 words.** The objection: L1-only simply produces fewer
   features, and fewer-but-better is a trivial trade-off. C5 refutes it **on this panel, and the
   panel is named in the sentence**: C5 produces more surviving matches than C2 (median 88 vs 72)
   and still scores worse. The harm is not about feature count; it is about features with no
   grounding in the input. **Do not cite the production-path point counts here — they reverse.**

   **EXTENDED 2026-08-26 — item 7 becomes 160 words (100 + 60).** The original argument above
   is unchanged and still leads. It is now followed by the common-support answer, moved here
   from Methods by decision: **counts equalised per chip, the primary grows 1.8% and the
   LPIPS-only penalty shrinks 11%, both holding in all six seeds; and the minimum-match-count
   sweep moves the penalty UPWARD, every seed at or above +0.0373 px at K ≥ 30 — the opposite
   of what a selection artefact predicts.**

   **Why this is in Results and not Methods, recorded so it is not moved back:** a reviewer
   attacking the point-count objection reads Results. **If the answer sits in Methods they
   conclude there is no answer and write that in their report, and we only get to correct it
   in a rebuttal** — a worse position than the twenty words this costs. Methods keeps the
   procedure only: that equal-count truncation exists, that it ranks by the KLT score column
   and never by radial error which would be circular, that point-level common support is not
   constructible with the counts that rule it out, and that score is itself post-treatment.

8. **The honest limit, 100 words.** The edge ratio separates the restrained arm from the
   unrestrained ones; it does not order the errors within the unrestrained group. Invention is a
   necessary condition, not a complete explanation. Offer the route difference as the partial
   account it is: the discriminator produces texture that is largely unmatchable (high ratio,
   low point count); LPIPS produces structure that is matchable but misplaced (high ratio,
   highest point count). Both hurt, by different routes.
9. **NEW, ADDED 2026-08-26 — the single-run estimate outside the replicate range, 80 words.**
   The interaction we previously published from one run, I = −0.212, falls **outside the range
   spanned by six replicates of the same treatment** on the raw scale ([−0.160, +0.059]) and on
   the rank scale ([−0.262, +0.123]). The treatment was applied once per cell, so every error
   bar on that number is chip-level: it measures consistency across 130 chips, not consistency
   of the treatment. Six replicates do not contain it, and its sign flips in one of them.

   *Write this as a **result**, not an apology. It is the paper's own methodological thesis
   demonstrated on the paper's own data, against the paper's own earlier claim — which is what
   makes it the strongest available version of the demonstration and not a weaker one, because
   it is not borrowed from someone else's work and it is not free: it costs us the interaction
   claim. **Scope sentence required in the same paragraph:** falling outside the range of six
   replicates is not a significance test and no p-value attaches to it; what makes it
   reportable is that it happens on the quantity a mechanistic claim was built on, in the
   direction that favoured the claim, while the registered reading on that same quantity
   independently fails at 5/6. Seed 42's code-path caveat stays attached. Full numbers at
   [seed-block-results.md](seed-block-results.md) §5(c).*
10. **NEW, ADDED 2026-08-26 — the sustained training trend, 100 words.** Registered before the
    six-seed loss logs were downloaded
    ([sustained-trend-registration.md](sustained-trend-registration.md)) and scored at n = 6.
    **The arm-versus-gap distinction is the whole of it and must be written precisely:**

    - **CAN say:** *in every seed, the adversarial arm reduces its reconstruction loss less
      than its non-adversarial counterpart* — the gap reading, **6/6 in both families**.
    - **CANNOT say:** *adversarial arms fail to reduce the reconstruction loss* — the arm
      reading, which **fails for C1 at 5/6** (seed 45 is −0.99%, its loss fell; seed 48 is
      +0.02%, indistinguishable from none).

    **C4 alone fails to fall in all six seeds** (mean +1.45%, range +0.98 to +2.22). **C4 is
    the arm the stop rule fired on**, so entry 26's operative defence — the sustained trend,
    which it adopted precisely because the two-epoch window was confounded — is now replicated
    at n = 6 for the arm the defence was needed for. The gap readings are entailed by the arm
    readings and carry no independent weight; do not present them as a second confirmation.

    *Warning on the controlled magnitudes, because the two families do not carry equal weight
    and must not be written as if they did. The warm-up-matched gap is **6.33 in the LPIPS
    family and 4.00 in the L1 family**. **The 4.00 figure is the weaker of the two twice
    over**: it rests on C1, whose sign is not stable across seeds, and on a warm-up attenuation
    of 2.18 points that fell **inside** the six-seed C2 seed spread of 3.05 and so is not
    separable from seed variation. The LPIPS figure rests on an arm that replicates 6/6 and an
    attenuation (2.67) that exceeds its seed spread (0.73) by 3.7×. **Quote 6.33 as the
    controlled result; quote 4.00 only with both caveats in the same sentence.**
    ([warmup-deconfound-results.md](warmup-deconfound-results.md) §4a.)*

**Budget for items 9 and 10, taken as §1 requires.** 180 words (80 + 100) move **from Section
IV to Section III**: Section III 800 → 980, Section IV 500 → 320. §1 names Section IV as the
only section that degrades gracefully, and the mediation row is the one to move to the arXiv
version if the remaining 320 will not hold five rows — it is the row already marked "narrowed"
rather than "refuted", and its footnote is the longest prose item in the section. **This is a
budget decision recorded before drafting, not a discovery made while writing.**

### IV. Alternative explanations (500 words, Table II)

Table II, four columns. Rows and the prose each row gets:

| candidate | test | result | verdict |
|---|---|---|---|
| It is blur, not restraint | **edge ratio on the COMPLEMENTARY (informative) mask, Sobel(input) > 20, six seeds** | C2 = **0.986** where the input asserts structure vs **0.277** where it does not — a factor of 3.6, **6/6 seeds**, both against pre-committed bands. Blur suppresses uniformly; this is conditional | refuted |
| ~~Corrected georeferencing in the fine-tuning pairs | decompose the European gain | ~86% is scatter reduction; the systematic component slightly worsened | refuted~~ **— row REMOVED, answered by design in 28 words of prose instead (see note)** | |
| Cold-started discriminator damage | checkpoint sweep at epochs 1, 2, 5, 10, 20 | C1 at epoch 1 already better than pretrained (−0.399 ± 0.064, 6.3 SE), wrong sign for damage; deficit exists from epoch 1 and grows (+0.55 → +0.70) | refuted, post hoc |
| Optimising the evaluation metric | **two independent registrations**: descriptor families (ORB, AKAZE, MI) and matcher families (KLT, NCC, phase correlation) | **B3:** ORB −0.613 ± 0.135 (paired n = 29 intersection; AKAZE n = 11), AKAZE −0.148 ± 0.048, MI −1.260 ± 0.261 (**lower bound**). **Package A:** C2 ranks first, or ties C3 within noise, in every condition cell except two — both EU-150 urban, phase correlation, one per band — far below 2 SE | refuted |
| ~~The gain is mediated by output similarity | condition the gap on photometric and gradient similarity | see footnote | narrowed~~ | | | |

> **TABLE II REVISED 2026-08-26 — it is FOUR rows, not five, and the matcher row is
> re-attributed.**
>
> **Matcher row (row 4) — re-attributed across two registrations.** It previously read
> "matchers from three families … ordering preserved in 48 of 49 cells", which fused two
> separate packages into one apparent test. **Package A ran KLT, NCC template grid and phase
> correlation; it never ran ORB, AKAZE or mutual information** — those are B3's
> descriptor-family results. **Saying so makes the row stronger, not weaker: the candidate is
> refuted by two independent registrations rather than one**, and the letter should claim
> that. Each half carries its own n and its own caveats: B3's ORB Δ rests on a **29-chip
> paired intersection** (AKAZE on 11) and must never be quoted beside the 53/130 match count
> as if that were its support (binding sentence 12); B3's MI figure is a **lower bound**,
> because the registered parabola subpixel refinement never ran and the ±8 px grid censors
> 15.8% at the bound, censoring the worse arms harder and so compressing the margin toward
> zero (corrections-log entry 21).
>
> **"48 of 49" is STRUCK and must not be quoted.** It is not reproducible from the artifact
> under any counting scheme, and the only scheme that yields a denominator of 49 yields a
> numerator of 47. **A second exception was also unreported**: EU-150 urban under phase
> correlation flips in *both* band conversions, C1 ahead by 0.0246 ± 0.2080 and
> 0.0092 ± 0.2168, both far below the registered 2 SE threshold so no ordering change is
> claimed either way ([packageA-audit.md](packageA-audit.md) §C-2, §C-3).
>
> **Mediation row (row 5) — STRUCK.** [paper-roadmap.md](paper-roadmap.md) already rules that
> "**B3 part 2 (mediation) does not appear at all — it is void as stated**"
> (corrections-log entry 20: the registered test reported the conditional gap as the fitted
> value at the covariate means, which is algebraically identical to the raw mean and so could
> not have detected mediation of any size). **The skeleton was the document that was wrong**:
> it was drafted 2026-08-24 carrying the row, and the roadmap's ruling predates it. Recorded
> that way round rather than presented as a new decision.
>
> **Table II is therefore four rows, and after the matcher re-attribution it is four rows on
> firmer ground than five was** — every surviving row is either refuted by two registrations
> or refuted outright, with no row carrying a "narrowed" verdict that a reviewer can push on.
> **The freed word budget is NOT reclaimed here**; Section IV's allocation stands as revised
> and the slack absorbs the blur and georeferencing rows' provenance disclosure (§5 blockers).

> **TABLE II REVISED AGAIN 2026-08-26 — the two Phase D rows are replaced, not restored.**
>
> **Blur row — REPLACED by a stronger test.** The original was a single-seed negative control
> whose artifacts did not survive ([phase-d-regeneration-STOP.md](phase-d-regeneration-STOP.md)):
> it could not be re-run, because the generated imagery it consumed is gone as well as its
> outputs. It is replaced by a **six-seed positive test** — the registered edge ratio computed
> on the complementary mask ([informative-mask-results.md](informative-mask-results.md)).
> **C2 reproduces the real image's edge density to within 1.5% where the input asserts
> structure and suppresses it to 0.277 where the input says nothing.** Blur cannot do that: a
> Gaussian suppresses edges wherever they are, so a smoothing explanation predicts C2 below
> 1.0 on both masks. **A negative control on one seed became a positive test on six.**
>
> **Georeferencing row — REMOVED from the table and answered in prose.** The objection applies
> to a fine-tuned-versus-pretrained comparison, and **not one registered positional contrast is
> against pretrained** — C5−C4, C5−C2, C1−C2, C4−C5 and I_raw are all within the 2×2, with all
> four arms fine-tuned on the same pairs, so any georeferencing improvement is common to them
> and cancels. Verified against the registrations
> ([phase-d-closeout.md](phase-d-closeout.md) §C), including one disclosed
> registration-versus-harness mismatch that does not affect it. **Section IV gains 28 words:**
>
> > *No registered contrast compares a fine-tuned arm with the pretrained generator: all four
> > arms are fine-tuned on identical pairs, so any georeferencing improvement is common to them
> > and cancels.*
>
> **This is stronger than the 86% figure it replaces, because it depends on the design rather
> than on an artifact** — and unlike the 86%, nothing can be lost that would make it
> unverifiable.
>
> **Table II is now THREE rows** — cold-discriminator, matcher independence, blur/restraint —
> **on better evidence than five were.** Budget effect: the georeferencing row's 60 words
> become 28 of prose (−32) and the blur row's 90 words stand. **Section IV falls to roughly
> 368 against its 320 allocation**, so it remains over its own line but by less; the reserve
> cut is not required by this change and is not taken.

Prose, roughly 90 words each for blur and cold-D, 60 for georeferencing, 120 for the
matcher-family row, and the mediation footnote below.

**The mediation footnote, and it must be written carefully.** The registered mediation test
reported the conditional gap as the fitted value at the covariate means, which is algebraically
identical to the raw mean, so it could not have detected mediation of any size; this is recorded
in the corrections log. The mediation-capable statistic from the same fit gives −0.395 ± 0.124
on Ankara (43.8% of the magnitude lost, still significant) and −0.106 ± 0.088 on Europe (75.6%
lost, significance lost). The registered "fully mediated" threshold (≥ 80% *and* loss of
significance, jointly) is not met on either set, **but the threshold is pre-registered while the
statistic it is applied to was chosen after the fact, and the paper says so.** Add one sentence
of interpretation, labelled as interpretation: gradient similarity is plausibly on the causal
path from restraint to positional accuracy rather than a confound beside it, so this attenuation
does not separate the trained-on-the-metric explanation from the proposed mechanism. **The
evidence that does separate them is the cross-family replication**, and the row rests on that.

**Mechanistic note worth 40 words, because it explains why the result is matcher-independent:**
a blurred template gives a broad correlation peak; invented structure gives a sharp peak in the
wrong place; a broad peak in the right place localises better than a sharp peak in the wrong one.

### V. Discussion, limitations, design rule (450 words)

1. **The design rule, 60 words.** If you generate a reference image for a geometric consumer, do
   not train it with an adversarial loss, and prefer a per-pixel reconstruction term to a
   perceptual one. State the operational figure: on urban chips in the panchromatic-equivalent
   band, C2 = 0.593 ± 0.041 px on the production path (K = 8, n = 20), better than pretrained on
   20/20 chips.
2. **Relation to the theory, 90 words.** An empirical instance of the perception-distortion
   tradeoff in a geometric-task setting. The consumer framing. What the factorial adds that the
   theory lacks: substitutability between sources of plausibility pressure.
3. **The Cramér-Rao pre-emption, one sentence.** The classical result says variance scales
   inversely with gradient energy — sharper is better — for a *correct* model; ours is a bias
   argument, not a variance argument.
4. **Limitations, 180 words, compressed.** The institution's own matching software was never
   measured and every number is a proxy; the matcher-independence result bounds how much the
   proxy choice matters. The discriminator is not published. OSM's own positional accuracy was
   never separated from the model's error, so part of the residual we attribute to the model is
   OSM's, and the ceiling this implies is unmeasured. `torchmetrics` 1.9.0 was used against the
   upstream's 0.11.0 and LPIPS implementations drift. Known-displacement recovery was not run
   for C4/C5. Training inputs under-represent forest relative to the production render path,
   costing ~0.6 px on forest-heavy chips. B3's harness was not preserved, so four registered
   matcher parameters are reported as configured rather than as verified.
5. **What generalises, 80 words.** Not "GANs are bad". The claim is about the *consumer*: any
   loss that rewards plausibility will fill regions the conditioning input does not constrain,
   and any downstream task that treats structure as evidence of location will pay for it. Name
   the settings where the same test applies: SAR-to-optical translation used as a matching
   bridge, super-resolution before registration, simulated references generally.

---

## 4. Binding sentences — check every one before submission

1. **"Experiments were pre-registered where stated; deviations from the registered protocol are
   documented in a public corrections log."** Never "All experiments were pre-registered";
   corrections-log entries 16, 17 and 20 falsify it.
2. Novelty claims read **"to our knowledge"**, never "first", until the Scopus/Web of Science
   query and the manual Google Scholar check are done.
3. C4 − C1 is **"not significant at the registered threshold"**, never "null".
4. The point-count argument names the Ankara-130 panel. The production point counts are never
   cited in its support.
5. The mediation result carries both labels: pre-registered threshold, post-hoc statistic.
6. The discriminator is not published; every adversarial arm starts from a seeded random
   discriminator.
7. C4 and C5 reproduce **the repository's executable definition** of the published objective.
8. The Arar distinction: joint training there, frozen deliverable and exogenous matcher here.
9. The Liu/Zhang/Xiong distinction: semantic task with an error rate there, geometric task with
   a continuous positional outcome here.
10. Blau and Michaeli are not contradicted; the consumer is identified.
11. The MI margin is a lower bound, not an estimate — the registered subpixel refinement never
    ran and the search grid censors 15.8% at the bound.
12. Descriptor-family deltas are computed on chip intersections; any table quoting both the
    delta and the matched counts labels which n belongs to which.
13. The 1/256 scale error carries the 3.9%-of-variance qualifier in the same paragraph, and is
    described as a text-versus-data inconsistency, ~~not a code bug~~ **not as a code bug**.

    *Editorial correction, 2026-08-26, revision layer only.* The original wording is struck
    above and preserved. §3's Materials-and-methods bullet gives the same instruction as
    "Describe it as a text-versus-data inconsistency, **not as** a code bug", and the two are a
    grammatical variant of one instruction rather than two different ones. **The canonical
    project original carries this inconsistency and the import reproduced it faithfully** (see
    the provenance header); it is corrected here rather than at import because the import rule
    was byte for byte. **This is a binding sentence the manuscript gets checked against, so
    its wording should be clean** — a checker comparing the two phrasings should not have to
    decide whether they mean different things.

    **AMENDED 2026-08-26 — this is now an ARXIV-VERSION rule, not a letter rule.** Not
    deleted: the sentence binds wherever the 1/256 finding is published, and per the
    decision above that is the extended version. **It does not bind the letter, because the
    finding is not in the letter.** The letter carries only the one-clause disclosure that
    our geometry differs, which needs no variance qualifier because it states no magnitude.
    A checker running this list against the letter should mark item 13 *not applicable*
    rather than *unmet*.

14. **Invention is a necessary condition, not a complete explanation.**
15. **ADDED 2026-08-26. The interaction consequence removes claims, not the disclosure.** The
    pre-committed consequence struck "the same lever", "substitutes" and the interaction claim
    from the paper. It does **not** license removing the record that the test was registered,
    run and failed. The disclosure at III.3 is mandatory text
    ([paper-context-addendum.md](paper-context-addendum.md) §24). **A submitted draft that
    contains no interaction claim and no interaction disclosure has silently dropped a
    pre-registered failed test — the exact failure this paper attributes to the upstream work,
    and the one error that would discredit every other claim in it.** Check for the presence of
    the disclosure, not merely for the absence of the claim.
16. **ADDED 2026-08-26. The cross-platform attenuation figure disagrees with the
    within-platform one in both directions, and this is reported rather than quietly
    corrected.** Measuring the warm-up attenuation against Kaggle seed-42 comparators gives
    **54% in the L1 family and 22% in LPIPS**; measuring it within platform and within seed
    (Modal seed 43, the only comparison that isolates the warm-up) gives **35% and 30%**. The
    cross-platform version **overstates** one and **understates** the other. **Report this as a
    concrete demonstration of what the NOT POOLED verdict protected against** — a hardware
    gate that returned "do not pool" is otherwise an abstract piece of housekeeping, and here
    is the number that shows what pooling would have cost. The within-platform figures are the
    ones quoted; the cross-platform ones appear only as this demonstration
    ([warmup-deconfound-results.md](warmup-deconfound-results.md) §4a).

---

## 5. Blocking items before drafting begins

- ~~**`phase-c-lpips-registration.md` is not audited.** It is the registration behind the primary
  result. Table I cannot be drafted before it clears. This is the top of the work list.~~
- ~~**`phase-c-registration.md` is not audited** either, and it governs the C1/C2 arms that supply
  half of Table I.~~
- The Scopus/Web of Science query, which gates the novelty language in Section I.
- Author list and institutional approval, which gate submission but not drafting.

**REVISED 2026-08-26 — the first two are cleared and are struck above; the second two stand
unchanged.** Both phase-C registrations have since been audited in
[phase-c-audit.md](phase-c-audit.md): leg B passes on every cell backed by an artifact —
1,300 per-chip cells, 25 per-arm summary cells, 30 paired cells, 25 sweep cells and 20
edge-ratio cells all reproduce from raw — with the stop-rule caveat (corrections-log entries
26 and 27) attached. **Neither is a blocker any longer.** Note that the audit's "Quotable as"
line was itself amended on 2026-08-26: the interaction is no longer quotable, though
everything else on that line remains so.

**What actually blocks now:**

- **`packageA` is not audited.** Section V's design rule quotes its production-path figure
  (C2 = 0.593 ± 0.041 px, K = 8, n = 20, better than pretrained on 20/20 chips), which is the
  single operational number the letter offers a practitioner. **The design rule cannot be
  drafted on an unaudited number.**
- **`phase-d` is not audited.** It supplies the ratio material behind the mechanism section's
  supporting claims.
- The Scopus/Web of Science query, which gates the novelty language in Section I. **Stands
  unchanged** — binding sentence 2 keeps every novelty claim at "to our knowledge" until it is
  done.
- Author list and institutional approval, which gate submission but not drafting. **Stands
  unchanged.**

**A new blocker the six-seed block created, which did not exist when this list was written:**
**Table I must be rebuilt from the six-seed block** before Section III can be drafted (see the
flag in §2). That is not an audit item — the numbers exist and are committed — but it is
drafting-blocking in exactly the way the two struck audit items were.

**Note on drafting order (§6), which is unaffected.** Section II remains the right place to
start, and its reasoning now holds more strongly than when it was written: it was chosen
because it does not depend on the outstanding audits, and the outstanding audits have changed
identity (packageA and phase-d rather than the phase-C pair) without touching Section II's
independence from them.

## 6. Order of drafting

Section II first, because it is the section that does not depend on the outstanding audits and
it fixes the vocabulary every other section uses. Then Section IV, which is written from
material already audited or already self-disclosed. Then Section III once the C4/C5 audit
clears. Then Section I, whose related-work paragraph is the most compressible and should be
written when the remaining word budget is known exactly. Section V last.
