# Warm-up de-confound — results

Written 26 August 2026. Registration:
[warmup-deconfound-registration.md](warmup-deconfound-registration.md), committed
2026-08-25 before the runs launched. The two arms completed overnight and **no curve was
read until this session**, per the registration and the overnight mandate.

**n = 1 seed. This is a mechanism probe, not a confirmatory estimate.** It enters no
registered contrast, it cannot join the Modal confirmatory block (AMENDMENT SEED-c), and
its checkpoints are deliberately not scored through the chip-evaluation pipeline. The
registered readings are the loss-curve reads below and only those. That scope statement is
repeated beside every number in this document because a single-seed mechanism probe is
exactly the kind of number that travels further than it should.

**Order of writing.** The registered branch text is quoted first, in full, before any number
appears. The numbers follow. The branch determination comes last. The record is meant to
show that the branch was matched to the numbers and not the reverse.

---

## 1. The registered readings, quoted before any number

From [warmup-deconfound-registration.md](warmup-deconfound-registration.md), verbatim:

> **Quantity**: the per-epoch mean of the generator reconstruction loss as printed in
> `loss_log.txt` — `G_L1` for C2_warmup, `G_LPIPS` for C5_warmup — with reference curves
> from the existing seed-43 Modal loss logs (C1, C4: the risers; C2, C5: the non-risers).
> "Main-stage epoch k" means the k-th epoch of that run's own main stage.
>
> **PRIMARY — the window.** Rise = mean(main-stage epoch 2) > mean(main-stage epoch 1), the
> same criterion as the coarse half of the stop rule ("rising over the first two main-stage
> epochs").
>
> - **IF C2_warmup and/or C5_warmup RISE** as C1 and C4 did: the window is explained by the
>   LR jump alone, no discriminator required. Entry 26's revised argument is confirmed
>   exactly as already written — the window is confounded; the sustained trend carries the
>   claim. Nothing is withdrawn.
> - **IF NEITHER RISES**: the rise requires the discriminator, and entry 26's revision was
>   more conservative than it needed to be. The window becomes usable again and entry 26
>   gains a paragraph saying so. Nothing is withdrawn.
>
> **SECONDARY — the sustained trend.** The relative change from the first to the last
> main-stage epoch mean, per arm. The un-warmed counterparts fall by roughly 8% over their
> main stage. If C2_warmup and C5_warmup still fall by roughly that much, warm-up does not
> touch the sustained trend — which is what the paper's claim actually rests on.

And the windowing decision, also quoted before the numbers because it determines what gets
compared to what:

> **Decision: state the difference and read the SHAPE — each run's own main-stage window —
> rather than aligning epoch indices or endpoints.** … The primary reading uses each run's
> own main-stage epochs 1–2; the secondary uses each run's own first→last main-stage change,
> with the epoch counts stated beside every number.

**Both branches were written before any curve existed, and both end "Nothing is
withdrawn."** That was deliberate: the probe was designed so that no outcome could be used
to retract a disclosure already made.

---

## 2. Inputs and structure, verified before reading

Both arms ran on Modal at seed 43, commit `a782aa5` (`WARMUP_COMMIT`), sorted enumeration
asserted (ordered-list hash `4b5f2320…`, patched `image_folder.py` `fef294b8…`), TF32 off,
zero failures. C5_warmup 7,307 GPU-s; C2_warmup 1,865 GPU-s; driver-computed $2.80 (which
carries the ×1.13 understatement recorded in
[seed-block-results.md](seed-block-results.md) §5(e)).

**Loss logs, now committed rather than left in a temporary directory.** Both files were
downloaded overnight into a session scratchpad — outside the repository, and under a path
that would not survive a cleanup. They are now committed as
`docs/gates/warmup-s43-C5_warmup-loss_log.txt` and
`docs/gates/warmup-s43-C2_warmup-loss_log.txt`, byte-identical to the downloaded originals:

| file | lines | sha256 |
|---|---|---|
| `warmup-s43-C5_warmup-loss_log.txt` | 5,582 | `57f3ad8b7c04058a24f6d418ba28cabcd8ff2e81bbd6a5e6404086a00fd7217a` |
| `warmup-s43-C2_warmup-loss_log.txt` | 5,582 | `0d5a2beb74e28ddf6c202787e95b81e323778eaf1cfbf695ac309b9b0d71f366` |

This is corrections-log entries 22 and 25 applied without being asked: the evidence for a
registered reading does not live in a temp directory.

**Stage structure, checked against the registered schedule before any value was computed.**
Each warm-up arm's log carries two `Training Loss` headers: stage 1 = epochs 1–2, stage 2 =
epochs 3–20, i.e. **18 main-stage epochs**, 20 total, 279 logged iterations per epoch. That
is exactly the registered schedule (C1's ladder mirrored). The un-warmed comparators carry
one header and **20 main-stage epochs**. The 18-vs-20 asymmetry is the one the registration
decided in advance to state and read around rather than equalise.

**One integrity check, run because the first line looked wrong.** C2_warmup's first logged
iteration is numerically near-identical to Modal seed-43 C1's, which would be what a
mis-configured run that silently inherited C1's discriminator looks like. Compared across
all 3,627 shared iterations: **3 of 3,627 agree**, the rest diverge, and the divergence grows
from the fourth decimal at epoch 1 to whole units by epoch 13 (e.g. epoch 13 iter 5580:
16.395 against 18.104). The near-agreement at iteration 20 is early-training coincidence
under an identical seed, data order and initialisation, not a duplicated configuration.
**C2_warmup is a distinct run.** Recorded because the check was run, not because it failed.

**Reference-curve provenance gap, disclosed.** The registration specifies reference curves
from *"the existing seed-43 Modal loss logs"*. Those Modal logs are not in the working tree
— only a **partial** C1 container log covering epochs 1–13 survives locally
(`docs/gates/modal-seed43-C1-container.log`); the Modal C2, C4 and C5 loss logs were never
downloaded, and the seed-43 loss logs that are complete locally are the **Kaggle** ones.
The references below are therefore Kaggle seed 43 (complete) plus Modal seed 43 C1 (partial,
but covering the primary window). **This crosses the platform boundary the hardware gate
declared NOT POOLED**, and it is disclosed rather than papered over. The one direct
cross-platform comparison available says the curve shape travels: Modal C1 main-epoch 1 =
33.466 against Kaggle C1's 33.459, and the primary window delta is +0.138 against +0.141.
That is one arm at one seed and it is offered as the only evidence available on the point,
not as an equivalence result.

---

## 3. The numbers

Per-epoch means of the generator reconstruction loss. Metric is `G_LPIPS` for the LPIPS arms
(C5, C4) and `G_L1` for the L1 arms (C2, C1), as registered. **Every column below is n = 1
seed.**

### Full per-epoch curves

Warm-up epochs are shaded by the stage column; main stage begins at epoch 3 for every warmed
arm and at epoch 1 for the un-warmed ones.

| epoch | C5_warmup (Modal) | C2_warmup (Modal) | C1 s43 (Kaggle, GAN) | C4 s43 (Kaggle, GAN) | C2 s43 (Kaggle) | C5 s43 (Kaggle) |
|---|---|---|---|---|---|---|
| 1 | 55.578 *(warm-up)* | 31.662 *(warm-up)* | 32.353 *(warm-up)* | 56.311 *(warm-up)* | 30.499 | 53.295 |
| 2 | 52.963 *(warm-up)* | 30.373 *(warm-up)* | 33.071 *(warm-up)* | 55.229 *(warm-up)* | 29.646 | 50.960 |
| 3 | **51.893** | **29.963** | **33.459** | **54.778** | 29.813 | 50.849 |
| 4 | **50.508** | **29.485** | **33.601** | **54.324** | 29.443 | 50.251 |
| 5 | 50.590 | 29.706 | 33.954 | 54.943 | 29.699 | 50.261 |
| 6 | 50.054 | 29.342 | 33.826 | 54.743 | 28.894 | 49.921 |
| 7 | 50.115 | 29.648 | 34.057 | 55.052 | 29.334 | 49.751 |
| 8 | 49.773 | 28.849 | 33.368 | 54.895 | 29.157 | 49.340 |
| 9 | 49.656 | 29.265 | 33.731 | 54.992 | 28.961 | 49.613 |
| 10 | 49.246 | 29.127 | 33.648 | 54.695 | 28.822 | 49.523 |
| 11 | 49.514 | 28.906 | 33.312 | 55.053 | 28.684 | 49.326 |
| 12 | 49.455 | 28.780 | 33.489 | 55.092 | 29.171 | 49.254 |
| 13 | 49.268 | 28.630 | 33.316 | 55.034 | 28.762 | 49.230 |
| 14 | 49.219 | 29.090 | 33.732 | 55.030 | 29.132 | 49.276 |
| 15 | 49.196 | 28.724 | 33.553 | 55.206 | 28.712 | 48.953 |
| 16 | 49.262 | 29.108 | 34.155 | 55.473 | 29.254 | 49.346 |
| 17 | 48.941 | 28.670 | 33.631 | 55.043 | 28.663 | 49.139 |
| 18 | 49.347 | 29.200 | 34.361 | 55.641 | 29.040 | 49.116 |
| 19 | 49.149 | 28.637 | 33.602 | 55.333 | 29.143 | 49.153 |
| 20 | 49.134 | 29.071 | 33.777 | 55.290 | 28.925 | 49.030 |

Bold marks each warmed arm's main-stage epochs 1 and 2 — the registered primary window.

### PRIMARY — the window, each run on its own main-stage epochs 1 and 2

| run | warm-up? | discriminator? | main stage | main-ep 1 | main-ep 2 | delta | rise? |
|---|---|---|---|---|---|---|---|
| **C5_warmup** (Modal s43) | yes | **no** | ep 3–20 (18) | 51.893 | 50.508 | **−1.385** | **no rise** |
| **C2_warmup** (Modal s43) | yes | **no** | ep 3–20 (18) | 29.963 | 29.485 | **−0.478** | **no rise** |
| C1 s43 (Kaggle) | yes | yes | ep 3–20 (18) | 33.459 | 33.601 | +0.141 | **rise** |
| C1 s43 (Modal, partial) | yes | yes | ep 3–13 (11 available) | 33.466 | 33.603 | +0.138 | **rise** |
| C4 s43 (Kaggle) | yes | yes | ep 3–20 (18) | 54.778 | 54.324 | −0.454 | no rise |
| C2 s43 (Kaggle) | no | no | ep 1–20 (20) | 30.499 | 29.646 | −0.853 | no rise |
| C5 s43 (Kaggle) | no | no | ep 1–20 (20) | 53.295 | 50.960 | −2.335 | no rise |
| C1 s42 | yes | yes | ep 3–20 (18) | 33.582 | 34.224 | +0.642 | **rise** |
| C4 s42 | yes | yes | ep 3–20 (18) | 54.374 | 54.650 | +0.276 | **rise** |
| C2 s42 | no | no | ep 1–20 (20) | 30.894 | 30.404 | −0.490 | no rise |
| C5 s42 | no | no | ep 1–20 (20) | 53.013 | 51.283 | −1.730 | no rise |

The seed-42 rows reproduce the values entry 26 and the registration already record
(C4's main stage 54.37 → 54.65, C1's 33.58 → 34.22), which is the parser's check against
numbers committed before this session.

### SECONDARY — the sustained trend, first to last main-stage epoch

Epoch counts stated beside every number, as registered.

| run | warm-up? | discriminator? | first → last | change | over |
|---|---|---|---|---|---|
| **C5_warmup** (Modal s43) | yes | **no** | 51.893 → 49.134 | **−5.32%** | **18 main epochs** |
| **C2_warmup** (Modal s43) | yes | **no** | 29.963 → 29.071 | **−2.98%** | **18 main epochs** |
| C5 s43 (Kaggle, un-warmed) | no | no | 53.295 → 49.030 | −8.00% | 20 main epochs |
| C2 s43 (Kaggle, un-warmed) | no | no | 30.499 → 28.925 | −5.16% | 20 main epochs |
| C4 s43 (Kaggle) | yes | yes | 54.778 → 55.290 | +0.94% | 18 main epochs |
| C1 s43 (Kaggle) | yes | yes | 33.459 → 33.777 | +0.95% | 18 main epochs |
| C5 s42 | no | no | 53.013 → 49.014 | −7.54% | 20 main epochs |
| C2 s42 | no | no | 30.894 → 28.455 | −7.90% | 20 main epochs |
| C4 s42 | yes | yes | 54.374 → 55.732 | +2.50% | 18 main epochs |
| C1 s42 | yes | yes | 33.582 → 33.970 | +1.16% | 18 main epochs |

The four seed-42 percentages are the reference values already recorded in the registration
and in corrections-log entry 26 (C1 +1.16%, C4 +2.50%, C2 −7.90%, C5 −7.54%). They are
reproduced here to four significant figures by the same parser that produced every other
number in this document, which is that parser's check against values committed before this
session.

---

## 4. Which branch fires

**NEITHER C2_warmup NOR C5_warmup RISES.** Both fall across the registered window:
C5_warmup by 1.385 and C2_warmup by 0.478.

**The second registered branch fires**, quoted again so the match is visible:

> **IF NEITHER RISES**: the rise requires the discriminator, and entry 26's revision was
> more conservative than it needed to be. The window becomes usable again and entry 26
> gains a paragraph saying so. Nothing is withdrawn.

**The LR-jump explanation of the window is refuted at this seed.** Both arms received C1's
exact warm-up ladder and therefore the identical 2e-5 → 1e-4 five-fold jump at the same
point in training, with no discriminator. Neither produced the rise. A transient caused by
the learning-rate jump alone would have appeared here, and did not.

### The qualification that travels with it, stated because the reference pattern is not what the registration assumed

The branch text says "as C1 and C4 did", presuming both discriminator arms rise. **At seed
43 they do not: C1 rises (+0.141) and C4 falls (−0.454).** At seed 42 both rise (C1 +0.642,
C4 +0.276), and entry 26 records the reverse asymmetry over the *two* transitions there
("only C4 rises at both transitions; C1 rises then falls"). So which discriminator arm shows
the window rise is not stable across seeds.

Counting every arm-instance available, on the registered main-ep1→ep2 criterion:

| group | rises | instances |
|---|---|---|
| discriminator-bearing, warmed | **3** | 4 (C1 s42, C4 s42, C1 s43, C4 s43) |
| **no discriminator, warmed** — the de-confound | **0** | **2 (C2_warmup, C5_warmup)** |
| no discriminator, un-warmed | 0 | 4 (C2/C5 at s42 and s43) |

**The defensible statement, and the limit of it.** No arm without a discriminator has ever
shown the window rise, including now that two of them have been given the warm-up that was
the competing explanation. But not every arm with a discriminator shows it either, and which
one does varies by seed. So: **the rise does not come from the learning-rate jump, and it
has only ever occurred in the presence of a discriminator — but it is not a reliable
per-arm signal, and a stop rule keyed to it would still fire inconsistently across seeds.**
Entry 26's decision to rest the argument on the sustained trend rather than the window is
therefore retained on its merits, even though the specific confound it named has now been
removed.

### The secondary reading, reported as measured rather than as expected

The registration's expectation was that the warm-up variants would "still fall by roughly
that much" — roughly 8%, the un-warmed counterparts' figure. **They fall, but by less:**
C5_warmup −5.32% against C5's −8.00%, and C2_warmup −2.98% against C2's −5.16% (18 main
epochs against 20 in each pair). Each warmed variant achieves roughly 60% of its un-warmed
counterpart's proportional fall.

**So the registered secondary expectation is not cleanly met, and the sentence "warm-up does
not touch the sustained trend" is too strong as written.** What the numbers support is
weaker and still useful: the sustained fall survives the warm-up in sign and in magnitude
order, and remains categorically opposite to the discriminator arms, which rise (+0.94%,
+0.95% at seed 43; +2.50%, +1.16% at seed 42). The direction that carries the paper's claim
is unaffected. The size of the fall is attenuated by the warm-up.

**One arithmetic observation, disclosed and then refused.** Measured instead from warm-up
epoch 1 — the true start of fine-tuning — to epoch 20, C5_warmup falls 11.6% and C2_warmup
8.2%, both larger than their un-warmed counterparts' main-stage falls, which would make the
secondary expectation look met. **That is not the registered window, it was computed only
after seeing that the registered secondary fell short, and it is not used here.** The
registration decided in advance to read each run's own main-stage window and not to align
endpoints; re-cutting the window after seeing the result is the precise move this project's
standing practice forbids. It is recorded so that a later reader who computes it does not
think it was hidden, and it may not be promoted to the reading without a fresh dated
registration that discloses it was computed first.

### What is withdrawn

**Nothing.** Both branches were written to end that way before any curve existed, and this
one does too. No disclosure made in entry 26 or anywhere else is retracted by this result.

---

## 4a. CORRECTION, 26 August 2026 — the attenuation, redone within platform and within seed

The figures in §3 and §4 above compare **Modal seed-43 warmed arms against Kaggle seed-42 and
seed-43 un-warmed arms**. That crosses the boundary the hardware gate declared **NOT
POOLED**, and it confounds the warm-up with both a platform change and a seed change. The
Modal seed-43 C1, C2, C4 and C5 loss logs have since been downloaded from the Volume
(committed at `docs/gates/loss_logs/`, provenance in
[sustained-trend-results.md](sustained-trend-results.md) §1), so the comparison can now be
made **within platform and within seed**. The cross-platform version is kept beside it,
labelled as what it was, rather than replaced silently.

### The within-platform, within-seed pair — the only test that isolates the warm-up

Every arm below is Modal, seed 43, commit-pinned. The only difference within each pair is
the warm-up.

| family | un-warmed (Modal s43) | warmed (Modal s43) | attenuation | fall retained |
|---|---|---|---|---|
| L1 | C2 **−5.16%** (20 main ep) | C2_warmup **−2.98%** (18 main ep) | **2.18 points** | 57.7% |
| LPIPS | C5 **−7.98%** (20 main ep) | C5_warmup **−5.32%** (18 main ep) | **2.67 points** | 66.6% |

### The cross-seed spread, printed beside it every time

Without this column a reader cannot tell an effect from seed noise, so it travels with the
attenuation wherever the attenuation goes. Spreads are from the six confirmatory seeds
45–50.

| family | attenuation | six-seed spread of the un-warmed arm | verdict |
|---|---|---|---|
| **L1 (C2)** | 2.18 points | **3.05 points** (C2 range −7.83 to −4.78) | **attenuation is WITHIN the seed spread — not distinguishable from seed variation** |
| **LPIPS (C5)** | 2.67 points | **0.73 points** (C5 range −7.98 to −7.25) | **attenuation EXCEEDS the seed spread by 3.7×** |

**The two families do not give the same answer, and the difference is not cosmetic.** C5's
sustained fall is extremely stable across seeds (sd 0.27 over six seeds), so a 2.67-point
attenuation stands well clear of that noise. C2's is not (sd 1.03, range 3.05), so its
2.18-point attenuation could be a seed draw and this n = 1 pair cannot tell. **The warm-up
attenuation is established for the LPIPS family and unestablished for the L1 family.**

### The properly-controlled sustained-trend gap — the number the manuscript carries

The comparison that matters is **adversarial-with-warm-up against non-adversarial-with-warm-
up**, not against non-adversarial-without. Both arms in each controlled gap below carry the
same warm-up ladder, so the warm-up is held fixed and only the discriminator varies.

| family | uncontrolled gap | **controlled gap** | share of the gap attributable to warm-up |
|---|---|---|---|
| L1 | C1 +1.03 vs C2 −5.16 = **6.19** | C1 +1.03 vs C2_warmup −2.98 = **4.00** | **35.3%** |
| LPIPS | C4 +1.01 vs C5 −7.98 = **9.00** | C4 +1.01 vs C5_warmup −5.32 = **6.33** | **29.7%** |

**Roughly a third of what the uncontrolled comparison attributed to the discriminator is
attributable to the warm-up** — 35% in the L1 family and 30% in the LPIPS family, on the
within-platform within-seed pairs. **The argument survives**: in both families the
adversarial arm still fails to fall at all while the warm-matched non-adversarial arm falls
by 3 to 5 percent, and the controlled gap remains large. **But the magnitude is smaller, and
the manuscript carries the controlled number, not the uncontrolled one.**

Two limits on that sentence, stated with it:

1. **The L1 family's 35% is not separable from seed variation** at n = 1 pair, per the
   spread table above. The LPIPS family's 30% is.
2. **Both controlled gaps are n = 1 seed.** The warm-up variants exist only at seed 43. The
   six-seed block has no warmed non-adversarial arms, so the controlled gap cannot be
   replicated without four more runs, and it is a mechanism probe wherever it appears.

### The cross-platform version, kept beside and labelled

The previously reported figures, retained so the correction is visible rather than silent.
These compare Modal seed-43 warmed arms against **Kaggle seed-42** un-warmed arms and
therefore confound warm-up with platform and seed:

| family | uncontrolled | controlled | attenuation |
|---|---|---|---|
| L1 (C1 s42 +1.16 vs C2 s42 −7.90 / C2_warmup −2.98) | 9.06 | 4.14 | 54.3% |
| LPIPS (C4 s42 +2.50 vs C5 s42 −7.54 / C5_warmup −5.32) | 10.04 | 7.82 | 22.1% |

The cross-platform figures disagree with the controlled ones in both directions — they
overstate the L1 attenuation (54% against 35%) and understate the LPIPS one (22% against
30%). **That disagreement is the reason the controlled version is the one that counts**, and
it is a concrete demonstration of what the NOT POOLED verdict was protecting against.

### One consequence for §3 and §4 above

The sentence in §4 that the warmed variants achieve "roughly 60% of the un-warmed
counterpart's proportional fall" was computed cross-platform. **Within platform and seed it
is 57.7% (L1) and 66.6% (LPIPS)** — close, and now for the right reason rather than by
luck. The §3 and §4 text above is left unedited as the record of what was reported before
the Modal comparators were available; this section supersedes its comparator arithmetic.

**Nothing about the alternative warm-up-epoch-1 window is revisited here.** It remains
disclosed and refused, as recorded above.

---

## 5. Proposed addition to corrections-log entry 26 — FOR REVIEW, NOT APPLIED

`corrections-log.md` has **not** been edited. The text below is proposed for review and is
written to be appended to entry 26 as a dated addition with the original preserved verbatim,
per standing practice 4. **Revised 26 August 2026** to carry the six-seed sustained-trend
result, the within-platform comparator, and the specification flaw in the branch text; the
earlier draft is superseded by this one and was never applied.

> **Addition, 2026-08-26. Two things happened to this entry's argument: the confound it
> named was tested directly and refuted, and the argument it fell back on failed to
> replicate at six seeds.** Both are recorded here; neither withdraws anything disclosed
> above.
>
> **1. The LR-jump explanation of the window is refuted.** This entry's revised argument
> rested on a collinearity: warm-up presence and discriminator presence could not be
> separated, so the first two main-stage epochs could not distinguish "the adversarial term
> competes with the reconstruction term" from "a 5× LR jump causes a transient". The
> de-confound registered in
> [warmup-deconfound-registration.md](warmup-deconfound-registration.md) broke that
> collinearity by giving C2 and C5 C1's exact warm-up ladder at seed 43 on Modal, with both
> outcomes written before the runs. **Neither warmed arm rises across the registered
> window** — C5_warmup 51.893 → 50.508 (G_LPIPS), C2_warmup 29.963 → 29.485 (G_L1), each on
> its own main-stage epochs 1–2 of 18. The registered second branch fires: the rise does not
> come from the learning-rate jump, and this entry's revision was more conservative than it
> needed to be on that specific point.
>
> **2. But the window is not restored as a per-arm signal — the discriminator is necessary
> and not sufficient.** Across every arm-instance measured, the window rise occurs in **3 of
> 4** discriminator-bearing arms and **0 of 6** arms without one, including 0 of the 2 that
> were given the warm-up. Which adversarial arm rises varies by seed: at seed 42 both C1 and
> C4 rise at the first main-stage transition (and over both transitions only C4 rises at
> each, while C1 rises then falls, as recorded above); at seed 43 C1 rises (+0.141) and C4
> falls (−0.454). So the rise has never appeared without a discriminator, but it does not
> appear reliably with one. **This entry's decision to rest the argument on the sustained
> main-stage trend rather than on the two-epoch window is retained**, now on the ground that
> the window is an inconsistent per-arm signal rather than on the ground that it is
> confounded with the learning rate. AMENDMENT C45-a, which replaced the coarse stop rule
> outright, is unaffected either way.
>
> **3. A specification flaw in the de-confound's own branch text, recorded and not
> repaired.** The registered branch reads "IF C2_warmup and/or C5_warmup RISE **as C1 and C4
> did**" — presuming both discriminator arms rise, which is true at seed 42 and false at
> seed 43, where C4 does not rise. The branch fires on its antecedent (neither warmed arm
> rises), so the flaw changes no outcome here; but had one warmed arm risen, the clause would
> have had no determinate referent. **The flaw was noticed only after the curves were read**,
> which is the moment at which repairing it is forbidden. It is therefore recorded, the
> post-hoc timing of noticing it is recorded, and the branch stands as written. **This is
> the same family as the hardware gate's single-global-verdict flaw**
> ([hardware-gate-results.md](hardware-gate-results.md)), which was likewise "noticed only
> after seeing which quantity failed" and likewise recorded rather than fixed, with the
> verdict left standing under the rule as written. Forward fix, for future registrations: a
> branch may not name a reference pattern it has not itself established across the seeds it
> will be read at.
>
> **4. The sustained trend, this entry's load-bearing argument, does NOT replicate at six
> seeds in the form written here.** It was registered before the seed-45–50 loss logs were
> downloaded ([sustained-trend-registration.md](sustained-trend-registration.md)) and scored
> at n = 6 ([sustained-trend-results.md](sustained-trend-results.md)). Outcome, per arm:
> **C4's change is positive in all six seeds** (mean +1.45%, range +0.98 to +2.22) — this
> replicates. **C1's is not: five of six, with seed 45 at −0.99%** (its reconstruction loss
> fell) and seed 48 at +0.02% (indistinguishable from no change). Both non-adversarial arms
> reduce their loss in all six (C2 mean −6.24%, C5 mean −7.62%). **The registered
> consequence fires: the manuscript no longer asserts that adversarial arms fail to reduce
> the reconstruction loss as a general finding.** The surviving statements are per arm — C4
> fails to fall in all six seeds; C1 does not fall *reliably*, which is weaker than "fails to
> fall". This entry's seed-42 observation stands as the historical record of what was seen at
> seed 42; what changes is what the manuscript may assert. Note also that this entry's
> "roughly 8%" for the non-adversarial arms is nearer **6–8%** across six seeds, and its
> −7.90% C2 figure lies outside the six-seed C2 range (−7.83 to −4.78).
>
> **5. The magnitude the manuscript carries is the warm-up-matched one, and it is smaller.**
> The comparison that isolates the discriminator is adversarial-with-warm-up against
> non-adversarial-**with**-warm-up, within platform and within seed. On Modal seed 43: the L1
> gap is **6.19 uncontrolled → 4.00 controlled** and the LPIPS gap is **9.00 → 6.33**, so
> **roughly a third of what the uncontrolled comparison attributed to the discriminator is
> attributable to the warm-up** (35% and 30%). The argument survives — the adversarial arm
> still fails to fall at all while the warm-matched non-adversarial arm falls 3–5% — but the
> uncontrolled gap overstates it and is not the number to quote. **The L1 family's attenuation
> (2.18 points) is within the six-seed C2 seed spread (3.05) and is therefore not separable
> from seed variation; the LPIPS family's (2.67 points) exceeds the C5 spread (0.73) by
> 3.7× and is.** Earlier cross-platform figures for the same quantities (54% and 22%) are
> superseded and are retained beside the corrected ones in
> [warmup-deconfound-results.md](warmup-deconfound-results.md) §4a.
>
> **Scope: the de-confound and every controlled gap above are n = 1 seed — a mechanism
> probe, not a confirmatory estimate.** They enter no registered positional contrast and the
> warm-up checkpoints are not scored. The six-seed sustained-trend result is n = 6 and is a
> training-dynamics reading, not a positional one. Full numbers, the reference-curve platform
> gap, and the disclosed-and-refused alternative window are in
> [warmup-deconfound-results.md](warmup-deconfound-results.md) and
> [sustained-trend-results.md](sustained-trend-results.md).

---

## 6. Scope, once more, because this is the number most likely to travel

n = 1 seed, one platform, one commit. **Mechanism probe, not a confirmatory estimate.** It
does not enter the six-seed block, it does not touch any registered contrast, and the
checkpoints it produced are kept but not scored through the chip pipeline. Wherever any
number from this document appears — in the paper, in a talk, in another document — that
scope sentence appears with it.
