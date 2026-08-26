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

## 5. Proposed paragraph for corrections-log entry 26 — FOR REVIEW, NOT APPLIED

`corrections-log.md` has **not** been edited. The text below is proposed for review and is
written to be appended to entry 26 as a dated addition with the original preserved verbatim,
per standing practice 4.

> **Addition, 2026-08-26 — the confound named in this entry has now been tested directly,
> and the LR-jump explanation is refuted at seed 43.** This entry's revised argument rested
> on a collinearity: warm-up presence and discriminator presence could not be separated, so
> the first two main-stage epochs could not distinguish "the adversarial term competes with
> the reconstruction term" from "a 5× LR jump causes a transient". The de-confound
> registered in [warmup-deconfound-registration.md](warmup-deconfound-registration.md) broke
> that collinearity by giving C2 and C5 C1's exact warm-up ladder at seed 43 on Modal, with
> both outcomes written before the runs. **Neither warmed arm rises across the registered
> window** — C5_warmup 51.893 → 50.508 (G_LPIPS), C2_warmup 29.963 → 29.485 (G_L1), each on
> its own main-stage epochs 1–2 of 18. The registered second branch therefore fires: the
> rise does not come from the learning-rate jump, and this entry's revision was more
> conservative than it needed to be. **Nothing recorded in this entry is withdrawn.**
>
> **The window is nonetheless not restored as a per-arm signal, for a reason the de-confound
> also exposed.** Which discriminator-bearing arm shows the rise varies by seed: at seed 42
> both C1 and C4 rise at the first main-stage transition (and, over both transitions, only
> C4 rises at each while C1 rises then falls, as recorded above); at seed 43 C1 rises
> (+0.141) and C4 falls (−0.454). Across every arm-instance measured, the rise has occurred
> in 3 of 4 discriminator-bearing arms and in 0 of 6 arms without one — including 0 of the 2
> that were given the warm-up. So the rise has never appeared without a discriminator, but it
> does not appear reliably with one. **This entry's decision to rest the argument on the
> sustained main-stage trend rather than on the two-epoch window is retained**, now on the
> ground that the window is an inconsistent per-arm signal rather than on the ground that it
> is confounded with the learning rate. AMENDMENT C45-a, which replaced the coarse stop rule
> outright, is unaffected either way.
>
> **The sustained trend, checked on the same runs.** The warmed non-adversarial arms still
> fall over their main stage — C5_warmup −5.32% and C2_warmup −2.98% over 18 main epochs —
> against −8.00% and −5.16% over 20 for their un-warmed counterparts at the same seed. The
> fall survives the warm-up in sign and remains categorically opposite to the adversarial
> arms, which rise; it is **attenuated**, at roughly 60% of the un-warmed proportional fall,
> so the stronger form "warm-up does not touch the sustained trend" is not supported and is
> not adopted.
>
> **Scope: n = 1 seed, a mechanism probe and not a confirmatory estimate.** It enters no
> registered contrast and its checkpoints are not scored. Full numbers, the reference-curve
> platform gap, and the disclosed-and-refused alternative window are in
> [warmup-deconfound-results.md](warmup-deconfound-results.md).

---

## 6. Scope, once more, because this is the number most likely to travel

n = 1 seed, one platform, one commit. **Mechanism probe, not a confirmatory estimate.** It
does not enter the six-seed block, it does not touch any registered contrast, and the
checkpoints it produced are kept but not scored through the chip pipeline. Wherever any
number from this document appears — in the paper, in a talk, in another document — that
scope sentence appears with it.
