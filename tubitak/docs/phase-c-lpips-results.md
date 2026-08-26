# Arms C4/C5 — results, scored against the registration

> **Conventions:** Δ = candidate − baseline; **negative = candidate better**. Registration:
> [phase-c-lpips-registration.md](phase-c-lpips-registration.md), commit `b07e719`, before any
> run. KARIOS config `tubitak/configs/karios_gencp.json`, unchanged. Harness:
> `tubitak/scripts/c45_eval/` (committed — the B3 lesson). Per-chip artifacts:
> `tubitak/data/tool_runs/C45/`.

**Headline: the registered generalisation case fired in full.** The adversarial main effect
replicates under LPIPS (C5 − C4 = −0.487 ± 0.053 px, t = −9.2); C5 hallucinates exactly as
the corrected framing predicted (edge ratio 1.16 — the highest of all five arms); ~~and the
interaction lands in the registered *substitutes* band (t = −3.07)~~. **The right level of
description is "plausibility pressure", not "adversarial".** The claim generalises from "the
adversarial term degrades matchable content" to "any plausibility pressure does" ~~— and the
two pressures act on the same lever, not additively~~.

**SUPERSEDED 2026-08-26, in part.** The two struck clauses are preserved above rather than
deleted; the rest of the headline stands and is confirmed at six seeds. The registered
seed-level interaction reading failed at 5/6 across the six confirmatory seeds on the raw,
log and rank scales alike, and the pre-committed consequence removed "substitutes" and "the
same lever" from the paper — see [seed-block-results.md](seed-block-results.md) §4. **What
survives is stronger than what was struck**: the primary (C5 − C4 negative) replicated 6/6 at
P = 1/64, the secondary (C5 − C2 positive) 6/6, and the mechanism readings 6/6, so the
generalisation from "adversarial" to "plausibility pressure" is now a six-seed result rather
than a single-seed one. Only the claim about how the two pressures *combine* is withdrawn.

## The training runs

| | C4 (GAN + LPIPS) | C5 (LPIPS only) |
|---|---|---|
| kernel | `vedatyildirim/gencp-phase-c-arm-c4-gan-lpips` v1 | `vedatyildirim/gencp-phase-c-arm-c5-lpips-only` v1 |
| wall time (T4) | **3 h 28 m** (12,486.8 s, measured from the log's elapsed field; corrected 2026-08-24 from "≈ 3 h 25 m") | **3 h 33 m** (12,835.9 s; corrected from "≈ 3 h 40 m") |
| protocol | C1's exactly: 2-epoch warm-up 2e-5 (step policy, **held — verified in log**) + 10+10 linear 1e-4 | C2's exactly: 10+10 linear 1e-4 |
| loss flags | `LPIPS: True`, `gan_mode: vanilla`, λ = 100 | same + `[C5] adversarial term zeroed` (patch fired, log line) |
| seed | 42 (seed-hook line in log, both stages) | 42 |
| torchmetrics | **1.9.0** (image default; paper's evaluation used 0.11.0 — disclosed per registration) | 1.9.0 |
| stop rule | **FIRED, and was not acted on** (corrected 2026-08-24; this cell previously read "not triggered"). The registered coarse rule is "G_LPIPS rising over the first two main-stage epochs"; G_LPIPS rose **54.37 → 54.65 → 55.02** across exactly those two transitions, so the rule fired and the run continued to epoch 20. The earlier "not triggered" was reached by citing the **cold-D spike test** instead — true on its own terms (54.37 is the run minimum, below the warm-up's 56.24) but not the registered coarse test, and the substitution was not disclosed: **corrections-log entry 27, a reporting error.** Why the run was allowed to stand, argued separately and retrospectively: the rule is mis-specified for an arm carrying a discriminator (**AMENDMENT C45-a**, [phase-c-lpips-registration.md](phase-c-lpips-registration.md); corrections-log entry 26). Drift 54.37 → 55.73 (+2.50%) across the main stage, against C1's G_L1 wiggle band 32.8–34.3 | decrease 53.0 → 49.0 (**−7.54%** across the main stage; falling trend with five small upward steps in the last third — not strictly monotone, corrected here) — optimisation without the adversarial term |
| checkpoints | 20/20 epochs saved; `latest_net_G.pth` tensor-equal to `20_net_G.pth` (asserted) | same |

Note for the mechanism section: C5's final training LPIPS (49.0) is **lower** than C4's
(55.7) — the discriminator pulls G away from the LPIPS optimum, yet C4 still *scores* worse
positionally than C5. Plausibility pressure hurts through the output distribution, not
through reconstruction-loss underfitting.

## The numbers — ank130 primary panel

**[STOCH seed42, OVP inputs] n = 130, single draw (standing practice 2).** Pairing base:
`B1_per_chip.csv` (regenerated seed-42 draws; C1/C2 = epoch 20), so all five arms sit on one
draw family, one warp geometry, one KARIOS config. Mean / median of per-chip median residual
(px), median surviving KLT points:

| arm | mean | median | pts med |
|---|---|---|---|
| pretrained | 2.563 | 2.588 | 51 |
| C1 (GAN+L1) | 2.075 | 1.794 | 59 |
| C2 (L1 only) | 1.376 | 0.974 | 72 |
| **C4 (GAN+LPIPS)** | **1.965** | **1.918** | **62** |
| **C5 (LPIPS only)** | **1.478** | **1.134** | **88** |

Paired deltas (per chip, mean ± SE):

| Δ | value | t | first-arm better |
|---|---|---|---|
| **C5 − C4** (primary) | **−0.487 ± 0.053** | **−9.18** | 113/130 |
| C2 − C1 (same draw family) | −0.700 ± 0.059 | −11.82 | 116/130 |
| C2 − C1 (committed target, phase-c-results.md) | −0.638 ± 0.054 | −11.9 | 121/130 |
| C4 − C1 | −0.110 ± 0.058 | −1.89 | 68/130 |
| C5 − C2 | +0.103 ± 0.042 | +2.46 | 44/130 |
| C4 − pretrained | −0.597 ± 0.061 | −9.85 | 109/130 |
| C5 − pretrained | −1.084 ± 0.071 | −15.18 | 122/130 |

## Scored against the registration

**PRIMARY — FIRED.** C5 − C4 negative at 9.2 SE (band: ≥ 2 SE). Adversarial OFF beats
adversarial ON under both reconstruction terms. The main effect is replicated, not merely
observed once.

**SECONDARY (mechanism) — the corrected framing's prediction confirmed.** Edge-density ratio
in input-silent regions, all five arms recomputed in one pass with the committed B3
definition (mask = input PNG warped to the 228 grid, BT.601, Sobel ≤ 20; validated against
the committed values before use):

| arm | mean | median | q25–q75 | registered band | committed B3 |
|---|---|---|---|---|---|
| pretrained | 1.021 | 1.020 | 0.94–1.12 | near 1.0 (≥ 0.8) | 1.016 |
| C1 | 1.096 | 1.046 | 0.96–1.17 | near 1.0 | 1.023 |
| C2 | 0.284 | 0.218 | 0.12–0.38 | well below (≤ 0.5) | 0.218 |
| **C4** | **1.119** | **1.082** | 1.00–1.20 | **near 1.0** | — |
| **C5** | **1.159** | **1.117** | 1.03–1.27 | **near 1.0** | — |

C1, C4, C5 near 1.0; C2 well below — all four registered predictions hold, including the
critical one: **C5 hallucinates**. With no discriminator anywhere in its objective, LPIPS
alone drives input-silent terrain to (slightly above) real-image busyness. The mechanism is
plausibility pressure, and LPIPS is one. (The small recompute-vs-committed offsets on
pretrained/C1 are mask-recipe sensitivity, disclosed at reconstruction time; C2 reproduces
essentially exactly. All cross-arm comparisons here use the one-pass recompute.)

~~**INTERACTION — substitutes, the richer mechanistic result.** Adversarial penalty under L1:
D_L1 = C1 − C2 = +0.700 ± 0.059. Under LPIPS: D_LPIPS = C4 − C5 = +0.487 ± 0.053.
I = D_LPIPS − D_L1 = **−0.212 ± 0.069 (t = −3.07)**, with D_LPIPS itself positive at 9 SE:
the registered *substitutes* band. The discriminator adds less on top of LPIPS than on top
of L1 because LPIPS already supplies part of the same pressure — two mechanisms, one lever.
Consistent with the (unregistered, noted) near-null C4 − C1 = −0.110 ± 0.058: swapping the
reconstruction term barely matters once a discriminator is present.~~

**SUPERSEDED 2026-08-26.** Struck in full, preserved verbatim above as the record of what
this document reported on seed-42 data. Every number in it is a single run with a chip-level
error bar. At six confirmatory seeds the registered sign reading on the interaction failed
**5/6** — seed 46 is positive on the raw scale (+0.0594) and reverses on the log (+0.0118)
and rank (+0.1231) scales too — so the pre-committed consequence fired and "substitutes",
"the same lever" and the interaction claim are removed from the paper
([seed-block-results.md](seed-block-results.md) §4). The −0.212 above additionally falls
**outside** the range spanned by the six replicates on the raw and rank scales, recorded as
a result in its own right at §5(c) of that document. **The paper carries the required
disclosure at [paper-context-addendum.md](paper-context-addendum.md) §24 in place of this
section's claim.**

**NULL INTERPRETATION 2 — also fired, as a separate finding.** C5 − C2 = +0.103 ± 0.042
(t = +2.46): perceptual reconstruction carries its own positional penalty even without a
discriminator. This is not in tension with the primary result — it *is* the generalisation:
C5 hallucinates (1.159) and pays for it against the restrained arm. The full ordering
C2 < C5 < C4 < C1 on the mean tracks the plausibility-pressure dose, not the presence of a
discriminator per se.

**RETRACTION CONDITION — not fired.** The four fine-tuned arms are not within noise of each
other (five of six pairwise deltas ≥ 2 SE).

**Unregistered observations, flagged as such:** (1) C5's surviving-point median (88) is the
highest of all arms, above C2's 72 — under LPIPS, removing the discriminator *gains* both
points and accuracy, strengthening the operational case exactly as C2 did against C1.
(2) C5's edge ratio (1.159) is nominally the highest of the five arms, slightly above the
adversarial arms' — LPIPS is, if anything, not the weaker plausibility pressure.

## Secondary row — 20-chip urban production subset

**[STOCH mean-of-8 K=8 (seeds 42–49), POST inputs] n = 20, BT.601. Secondary per the
registration — no registered band.** Run on the extended B2 harness; the four existing arms
reproduce the committed headline figures to the fourth digit (pretrained 1.370 / C1 0.764 /
C2 0.593 / C3 0.611 — headline-results.md B2), which validates the extension byte-for-byte.

| arm | mean | median | pts med |
|---|---|---|---|
| pretrained | 1.370 | 1.051 | 92 |
| C1 | 0.764 | 0.642 | 164 |
| C2 | 0.593 | 0.534 | 235 |
| C3 | 0.611 | 0.550 | 210 |
| **C4** | **0.844** | **0.654** | **156** |
| **C5** | **0.663** | **0.554** | **224** |

> **The per-arm ± SE column was removed on 2026-08-24 (corrections-log entry 24).** It
> previously read ± 0.108 / 0.043 / 0.041 / 0.043 / 0.054 / 0.045. Five of those six values
> trace to no computation: `C45_b2_summary.json` stores 0.1612 / 0.0712 / 0.0409 / 0.0375 /
> 0.0949 / 0.0660 — `sd/√20`, and identical to what B2 committed for the four pre-existing
> arms — and the printed five match neither that nor the SE of the median, a bootstrap
> median SE, a MAD- or IQR-based SE, nor the RGB-band SEs. Rather than reprint numbers whose
> origin is unknown, the column is dropped: **the paired deltas below carry the uncertainty
> for every comparison this row supports, and they reproduce from raw exactly.** The means,
> medians and point counts above are unaffected and were verified cell-by-cell
> ([phase-c-audit.md](phase-c-audit.md) §B.1).

Paired: **C5 − C4 = −0.182 ± 0.054 (t = −3.36, 16/20)** — the main effect holds on the
production path, and its size there matches the L1 pair's (C2 − C1 = −0.171 ± 0.042,
recomputed here −0.171 ± 0.042, 19/20). C5 − C2 = +0.070 ± 0.042 (t = 1.68): the perceptual
own-penalty is visible in the same direction but below 2 SE at n = 20 — reported as
measured, no claim. C4 − C1 = +0.080 ± 0.038 (t = 2.10). Production ordering:
C2 < C3 < C5 < C1 < C4 < pretrained.

## Dose-response sweep (epochs 1, 2, 5, 10, 20)

Run in the registered order: endpoints first (they showed the relationship — C5 improves
e1→e20 at 4.25 SE, C4 flat at 0.24 SE, penalty grows), then the middle epochs.
**[STOCH seed42, OVP inputs] n = 130, single draw.** Mean of per-chip medians (px):

| epoch | C4 (GAN+LPIPS) | C5 (LPIPS only) | penalty C4 − C5 | t |
|---|---|---|---|---|
| 1 | 1.978 | 1.644 | +0.334 ± 0.040 | 8.3 |
| 2 | 1.822 | 1.568 | +0.254 ± 0.040 | 6.4 |
| 5 | 1.927 | 1.486 | +0.441 ± 0.039 | 11.3 |
| 10 | 1.989 | 1.493 | +0.496 ± 0.047 | 10.7 |
| 20 | 1.965 | 1.478 | +0.487 ± 0.053 | 9.2 |

The same qualitative dose-response as the L1 family (B1_summary.json: C2 monotone
1.618 → 1.376; C1 U-shaped 2.164 → 1.806 → 2.075; penalty dip-then-grow
0.546 → 0.384 → 0.700): under LPIPS the no-adversarial arm improves and plateaus, the
adversarial arm dips at epoch 2 and reverts, and the penalty dips early then grows and
saturates. **The dose-response relationship replicates under LPIPS, at every epoch at
≥ 6 SE.** Training longer with a discriminator does not close the gap; it widens it to a
plateau — under both reconstruction terms.

## Cappadocia known-displacement recovery — deferred, disclosed

Not run. The T1 harness script was not preserved (only its inputs/outputs; the same
preservation failure the corrections log documents for B3), so adding C4/C5 to the paper's
main recovery table requires reconstructing the distortion/recovery protocol from artifacts
first — real work with real protocol-drift risk (the E3 lesson: an unregistered
reconstruction is how false "pass" claims happen). Logged in [open-items.md](open-items.md)
rather than improvised here. The registered qualifier was "if cheap"; it is not.

## Consequence

The paper's central claim upgrades from a single observation to a replicated 2×2 main
effect, and its causal vocabulary changes: not "the adversarial objective degrades generated
reference imagery" but **"plausibility pressure degrades generated reference imagery for
matching; the adversarial term and LPIPS are both such pressures, acting on the same
lever."** C2 (L1-only) remains the best arm measured — restraint, not realism, is what
matching rewards. The internship report's scope statement is unchanged by design: its claim
stays on the GAN+L1 configuration; these results widen the *paper's* claim only.

## Invariance note

Everything held fixed per the registration's invariance section: same 5,577 Turkish training
pairs, same schedules (C4=C1's, C5=C2's, verified in logs including the held warm-up), same
seed 42, same released-G initialisation and cold-D construction, same eval chips, same
archived OVP inputs, same STOCH seed-42 inference, same warp geometry (GSD 10.0390625,
228-grid), same KARIOS config, same BT.601. Known inherited asymmetries (warm-up summed-LR
14.7% toward the no-adversarial arm; final epoch at lr 0, symmetric) disclosed in the
registration. New-to-package: torchmetrics 1.9.0 vs the paper's 0.11.0 (VGG backbone per the
repository's code either way).
