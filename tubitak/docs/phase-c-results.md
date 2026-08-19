# Phase C results — scored against the registration

**Date:** 2026-08-19/20 · 130 Ankara held-out chips (26 per CLC+ stratum), KARIOS
`confidence_threshold` 0.8 unchanged, same geometry and configuration as every prior run.
Registration: [phase-c-registration.md](phase-c-registration.md) (committed 09:29 UTC, before
any training existed). Checkpoint discipline fixed before any number was seen: **epoch 20 only**
(`latest_net_G.pth`, verified tensor-for-tensor equal to `20_net_G.pth` for both arms); the other
19 per-epoch checkpoints are descriptive material only and none was evaluated.

**Provenance notes.** C1 is the amended run (stage-1 `--lr_policy step`; the discarded first
run and the reason are corrections-log entry 5 and the amendment in
[phase-c-config.md](phase-c-config.md)). All three arms' fakes were generated in one local
environment; the Phase B pretrained fakes are not byte-reproducible locally (generation-
environment numerics), so the pretrained arm was regenerated and re-scored as a gate: paired
regen − published = **+0.034 ± 0.045 px** (statistically zero). Published Phase B numbers stand;
paired statistics below are quoted against the published baseline, with the same-environment
baseline in parentheses where it differs materially (it never does).

## The numbers

Median residual (px) / median surviving points per chip:

| stratum | pretrained | C1 (GAN+L1) | C2 (L1-only) |
|---|---|---|---|
| Q1 | 3.480 / 37 | 3.532 / 38 | **2.649 / 43** |
| Q2 | 3.106 / 38 | 2.720 / 47 | **1.452 / 56** |
| Q3 | 2.492 / 52 | 2.019 / 62 | **0.983 / 76** |
| Q4 | 2.084 / 56 | 1.483 / 73 | **0.711 / 108** |
| Q5 | 1.240 / 91 | 0.712 / 120 | **0.552 / 194** |
| **ALL** | **2.588 / 51** | **1.869 / 61** | **0.929 / 75** |

Paired per chip: C1 − pretrained **−0.530 ± 0.070** (t = −7.6, 32/130 chips worse);
C2 − pretrained **−1.167 ± 0.074** (t = −15.9, 8/130 worse);
C2 − C1 **−0.638 ± 0.054**, median −0.524 (t = −11.9, 9/130 worse).

## R1 — which arm wins on KARIOS residual, and by how much

> **Predicted winner: C2 (L1-only), by 0.15–0.40 px** on the 130-chip paired median residual.
> [...] **C2 wins residual, C1 wins points and appearance.**

**Outcome:** C2 wins, paired median 0.524 px (mean 0.638 ± 0.054). C2's surviving-point count
is **higher** than C1's (per-chip ratio median 1.29; totals 13,334 vs 9,813).

**Verdict: winner HELD; magnitude EXCEEDED the registered band** (~1.5× its upper edge).
**The points half of the prediction is FALSIFIED** — C2 wins points as well as residual.
"Fewer but honest" was the wrong picture: restraint produced *more* survivable structure, not
less. The appearance half held (see the visual section below).

## R2 — where fine-tuning helps

> **Prediction: improvement over pretrained correlates POSITIVELY with OSM/CLC+ information
> content** (rho ≥ +0.3 between chip density and improvement). Fine-tuning teaches the model to
> render *Anatolian-looking* structure where the input specifies structure; it does not teach it
> to stop inventing where the input specifies nothing. Q1 chips improve least or not at all;
> Q4–Q5 improve most.

**Outcome:** against CLC+ density — C1: rho **+0.232** [95% CI +0.065, +0.385], Q1 improvement
−0.078 ± 0.171 (zero). C2: rho **+0.032** [−0.161, +0.224], Q1 improvement **−0.843 ± 0.220**.

**Verdict: scored as two mutually inconsistent registered claims, not a simple falsification.**
R1 predicted C2 would win *because hallucination is an adversarial-loss product*. R2 predicted
fine-tuning would teach Anatolian-looking invention rather than restraint. These cannot both
hold for the same arm: if R1's mechanism is right, R2's mechanism cannot operate where the
adversarial loss is absent. Both were registered and the inconsistency went unnoticed until the
data exposed it.

The data resolve it cleanly along the loss function:

- **Where the adversarial term is present (C1), R2's mechanism operates:** rho +0.232, Q1
  improvement statistically zero — invention persists on empty inputs and improvement
  concentrates where the input has content. The C1 panel of the sparsest chip shows invented
  Anatolian-textured terrain, exactly as R2 described.
- **Where it is absent (C2), R2's mechanism cannot operate and does not:** rho +0.032 —
  improvement is uniform across strata, including −0.843 px on Q1, the stratum R2 said should
  not improve. The C2 panel of the same chip is a near-featureless field with a road: the model
  learned restraint, which is what removing the busyness-demanding objective permits.

**Corrected scope statement, for future registrations to inherit:** *the invention mechanism is
conditioned on the adversarial term. "Fine-tuning teaches invention, not restraint" holds only
while a discriminator demands realistic busyness; under a pure reconstruction loss, fine-tuning
teaches restraint wherever the input underdetermines the output.* R2's mechanism was not wrong —
its scope was wrong, and it survives exactly where its condition holds.

## R3 — what falsifies the L1-only hypothesis

> C1 beats C2 on paired KARIOS residual by ≥ 0.15 px, or C2's surviving-point count collapses so
> far (> 50 % below C1) that accuracy gains are swamped for GCP-database purposes.

**Outcome:** C2 beats C1 (−0.638 px paired), and C2's point count is 29 % **above** C1's, not
50 % below. **Verdict: neither falsifier triggered; the sign of the second one is reversed.**

## R4 — what would mean fine-tuning is not worth doing

> Neither arm improves on the pretrained baseline by more than **0.15 px** paired [...] or any
> arm *degrades* dense-stratum performance (Q5 worse by > 0.15 px) while improving sparse strata.

**Outcome:** both arms clear +0.15 px paired by wide margins (C1 −0.530, C2 −1.167); Q5
*improves* in both (C1 −0.564 ± 0.088, C2 −0.892 ± 0.099). **Verdict: not triggered —
fine-tuning is worth doing on this evidence.**

## What the images show ([figure](figures/three-arm-visual.png))

The registered "looks worse, scores better" profile is confirmed: C2 is visibly blurrier
everywhere — near-featureless on the sparsest inputs, smoothed vegetation with crisp roads on
mid-density chips, soft but structurally faithful city fabric on dense urban (0.50 px / 390
points on the densest chip vs pretrained's 1.11 / 163). C1 is sharper and more photorealistic
throughout and scores in between. Two flags: a faint transpose-convolution checkerboard pattern
in some C2 outputs (watch item registered in
[phase-c-europe-registration.md](phase-c-europe-registration.md) with a fixed metric); and on
the Q3-sparsest chip both fine-tuned arms are worse than pretrained — the wins are not universal
chip-by-chip (8/130 lose under C2).

## Standing caveat — scene adaptation

C2's fine-tuning pairs share tile 36TVK and the 2026-04-30 acquisition with the evaluation
imagery (chip exclusion proven pixel-wise; scene, atmosphere, sun angle, phenology shared).
"Learned this April scene" and "learned Anatolia" both produce the table above. The
decomposition is registered and in progress:
[phase-c-europe-registration.md](phase-c-europe-registration.md) (forgetting bound) and
[phase-d-ratio-addendum.md](phase-d-ratio-addendum.md) (Cappadocia transfer ratio). Until those
report, the 64 % headline is a within-scene number.

## Consequence

C3 (EU mixing) applies to **C2**, per the registration's sequential design. The corrections log
([corrections-log.md](corrections-log.md)) collects every registered-vs-actual divergence,
including the discarded C1 warm-up run referenced above.
