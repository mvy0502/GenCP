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

**Two candidate files were present at import, and the discrepancy is recorded rather than
resolved silently.** Both were 300 lines; they differ in exactly one place.

| file | sha256 | mtime | line 280 (binding sentence 13) |
|---|---|---|---|
| `letter-skeleton.md` — **IMPORTED** | `e014d9264d4d579f089b36c16de1fc107e52e58f0a01bc89983c76b0925a8a2a` | 2026-08-24 14:44 | "…not a code bug." |
| `letter-skeleton-ORIGINAL-24aug.md` | `5f6b4d8ab234eb0af1b2dc2d0c9d14936a8c667a93e2c17507870745f248e041` | 2026-08-26 11:23 | "…not **as** a code bug." |

**Why the first was chosen:** it is the file the supervising session named, and its
modification time matches the document's own stated drafting date of 2026-08-24, whereas the
second was created on the day of import. **Note that the imported text is internally
inconsistent** — §3's Materials-and-methods bullet already reads "not **as** a code bug"
while binding sentence 13 reads "not a code bug", and the second candidate file resolves
that inconsistency. **The inconsistency is preserved deliberately**: the import rule is byte
for byte, change nothing, not even a typo. If the project copy proves to match the second
file, this header is the record needed to correct the import.

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
| III. Results — includes Table I and Fig. 1 | 2.5 | 800 |
| IV. Alternative explanations — includes Table II | 1.5 | 500 |
| V. Discussion, limitations, design rule | 1.0 | 450 |
| References (~30) | 1.0 | — |
| **Total** | **10.0** | **~3,300** |

Figures and tables consume roughly two of those ten columns. The budget has no slack. Any
section that overruns takes the space from Section IV, which is the only one that degrades
gracefully (a row can move to the arXiv version).

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
reconstruction, everything else held fixed), the primary number (C5 − C4 = −0.487 ± 0.053 px,
t = −9.2, better on 113/130 chips), the generalisation (the effect replicates under both
reconstruction terms, and LPIPS alone invents more than either adversarial arm), the mechanism
(edge density in input-silent regions), and the design rule. Index terms: image registration,
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
4. **The claim, 60 words.** Plausibility pressure degrades generated reference imagery for
   geometric matching; the adversarial term and a perceptual reconstruction loss are both such
   pressures and act on the same lever. Where the conditioning input carries no information, a
   loss that rewards plausibility causes the generator to invent structure; an invented edge is
   a false control point, and a false control point is worse than no control point because it
   displaces the solution silently.
5. **Related work, 220 words, compressed hard.** Blau and Michaeli give the theory; position as
   identifying the consumer, not contradicting it. Liu, Zhang and Xiong extend it to a
   downstream task, but a semantic one where an in-class hallucination costs nothing. Arar et
   al. is the only prior loss ablation scored against a registration metric and its sign is
   opposite, because there translation and registration train jointly. Chen, Ohayon et al. prove
   information-theoretically that pursuing perceptual quality converts uncertainty into
   confidently rendered false detail — our mechanism, predicted. Fuentes Reyes et al. named
   "fiction" in SAR-to-optical translation in 2019 and wrote that no suitable metric existed;
   seven years later the field still evaluates with FID and LPIPS. Merkle et al. established
   feeding translation output into a matching pipeline and never asked whether a matched point
   was real.
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
- **A geometric error in the published pipeline, 100 words + repo pointer.** 257×257 rasters at
  10 m resampled to 256×256 with the transform copied unchanged gives a true GSD of
  10.0390625 m against a declared 10.0, an error of exactly 1/256, up to 14.1 m at the chip
  corner. Corrected in our path. **Carry the qualifier or the claim overreaches: the systematic
  component is consistent with the signs and magnitudes of the published means, but predicted
  std is 2.89 m against an observed sigma of 14.5–17.3 m, so it explains roughly 3.9% of the
  reported variance and does not invalidate their conclusions.** Describe it as a
  text-versus-data inconsistency, not as a code bug. Pin the audited commit.
- **Registration statement, 40 words.** The binding wording, verbatim.

### III. Results (800 words, Table I, Fig. 1)

1. **The panel, 80 words.** Table I. Point at the ordering C2 < C5 < C4 < C1 < pretrained.
2. **Primary result, 120 words.** C5 − C4 = −0.487 ± 0.053 px (t = −9.2, better on 113/130
   chips; registered band was ≥ 2 SE). Adversarial OFF beats ON under *both* reconstruction
   terms. The main effect is replicated, not observed once.
3. **Interaction, 120 words.** Adversarial penalty under L1 = +0.700 ± 0.059; under LPIPS =
   +0.487 ± 0.053; I = −0.212 ± 0.069 (t = −3.07): substitutes. LPIPS already supplies part of
   the plausibility pressure, so the discriminator adds less on top of it. Consistent with
   C4 − C1 = −0.110 (1.9 SE) — **write "not significant at the registered threshold", never
   "null".**
4. **Secondary, 60 words.** C5 − C2 = +0.103 ± 0.042 (t = 2.5): perceptual reconstruction
   carries its own positional penalty with no discriminator present.
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
8. **The honest limit, 100 words.** The edge ratio separates the restrained arm from the
   unrestrained ones; it does not order the errors within the unrestrained group. Invention is a
   necessary condition, not a complete explanation. Offer the route difference as the partial
   account it is: the discriminator produces texture that is largely unmatchable (high ratio,
   low point count); LPIPS produces structure that is matchable but misplaced (high ratio,
   highest point count). Both hurt, by different routes.

### IV. Alternative explanations (500 words, Table II)

Table II, four columns. Rows and the prose each row gets:

| candidate | test | result | verdict |
|---|---|---|---|
| It is blur, not restraint | low-pass the adversarial arm to match the L1-only spectral profile (fitted σ = 0.45) | recovers −6.1% (Europe) / +1.7% (Cappadocia) of the gain; support band was ≤ 25% | refuted |
| Corrected georeferencing in the fine-tuning pairs | decompose the European gain | ~86% is scatter reduction; the systematic component slightly worsened | refuted |
| Cold-started discriminator damage | checkpoint sweep at epochs 1, 2, 5, 10, 20 | C1 at epoch 1 already better than pretrained (−0.399 ± 0.064, 6.3 SE), wrong sign for damage; deficit exists from epoch 1 and grows (+0.55 → +0.70) | refuted, post hoc |
| Optimising the evaluation metric | matchers from three families | ORB −0.613 ± 0.135 (n = 29 intersection), AKAZE, MI −1.260 ± 0.261 (lower bound); ordering preserved in 48 of 49 cells | refuted |
| The gain is mediated by output similarity | condition the gap on photometric and gradient similarity | see footnote | narrowed |

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
    described as a text-versus-data inconsistency, not a code bug.
14. **Invention is a necessary condition, not a complete explanation.**

---

## 5. Blocking items before drafting begins

- **`phase-c-lpips-registration.md` is not audited.** It is the registration behind the primary
  result. Table I cannot be drafted before it clears. This is the top of the work list.
- **`phase-c-registration.md` is not audited** either, and it governs the C1/C2 arms that supply
  half of Table I.
- The Scopus/Web of Science query, which gates the novelty language in Section I.
- Author list and institutional approval, which gate submission but not drafting.

## 6. Order of drafting

Section II first, because it is the section that does not depend on the outstanding audits and
it fixes the vocabulary every other section uses. Then Section IV, which is written from
material already audited or already self-disclosed. Then Section III once the C4/C5 audit
clears. Then Section I, whose related-work paragraph is the most compressible and should be
written when the remaining word budget is known exactly. Section V last.
