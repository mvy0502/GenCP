# Headline measurements B1–B3 — results, scored against the registrations

> **Conventions:** Δ = candidate − baseline; negative = candidate better. Registration:
> [headline-registrations.md](headline-registrations.md), commit `8c6d041`, before any
> number. Paths/provenance per row; standing practice 5.

## B1 — C1's loss is a loss-function effect; the cold-D artefact is ruled out
**[STOCH seed42, OVP inputs, n=130, single draw]**

| epoch | C1 Δ vs pre ± SE | C2 Δ vs pre ± SE | C1 − C2 ± SE |
|---|---|---|---|
| 1 | −0.399 ± 0.064 | −0.945 ± 0.068 | +0.546 ± 0.048 |
| 2 | −0.651 ± 0.064 | −1.052 ± 0.067 | +0.402 ± 0.039 |
| 5 | −0.757 ± 0.064 | −1.141 ± 0.072 | +0.384 ± 0.052 |
| 10 | −0.610 ± 0.072 | −1.162 ± 0.063 | +0.552 ± 0.055 |
| 20 | −0.487 ± 0.075 | −1.187 ± 0.065 | +0.700 ± 0.059 |

**The registered cold-D signature is absent**: C1 at epoch 1 is already *better* than
pretrained (−0.399, 6.3 SE) — the wrong sign for damage; no dip exists at any epoch.
Formally the verdict is reading C ("in between") because C1 is not monotone (best at e5,
degrades to e20) — but the shape decides the question: **the C1−C2 deficit exists from
epoch 1 and WIDENS with continued adversarial training** (+0.55 → +0.70), the opposite of a
cold-D transient, which would shrink as D warms. At most ~0.16 px of the early e1→e5
narrowing could be a cold-D component. The control (C2) improves near-monotonically and
plateaus. **Consequence: no warm-start rename; the confirmatory D-warm-up run is not
triggered; "the adversarial term is a liability for GCP generation" survives as a
loss-function statement** — with the B20 caveat and this sweep cited as its test. The
counter-evidence that motivated B1 (fewer points AND worse residuals under C1) is now
explained by B3's direct measurement: the adversarial term buys invented busyness, not
matchable structure.

## B2 — the headline survives the production path
**[STOCH mean-of-8, POST inputs, K=8, n=20]**

Production BT.601 urban C2 = **0.5927 ± 0.0409 px** vs the quoted 0.591 → Δ +0.0017 px,
inside the 0.15 registered trigger: **headline stands, now measured on-path**. The
institution-facing sentence: **0.593 px (production path, K = 8, n = 20)**. Full table:
pretrained 1.370 / C1 0.764 / C2 0.593 / C3 0.611 (BT.601); C2 − pretrained −0.777 ± 0.125
(20/20 chips), C2 − C1 −0.171 ± 0.042 (19/20). Ordering C2 > C3 > C1 > pretrained on POST
urban inputs. Production render path shown extent-invariant (overlapping renders bitwise
identical to task3's). The standing-practice-5 violation (quoting the off-path 0.591 as
headline) is recorded in [open-items.md](open-items.md) item 2 and corrected by this
measurement.

## B3 — "matcher-independent" is earned
**[STOCH archived fakes; OVP (ank130/eu150), POST+OVP (ank30)]**

1. **Different-family matchers** (ORB, AKAZE + RANSAC; mutual information):
   ank130 and eu150 rank **C2 > C1 (> pretrained) under all three** — ORB Δ(C2−C1)
   −0.613 ± 0.135 (~4.5 SE), AKAZE −0.148 ± 0.048, MI −1.260 ± 0.261 (ank130); eu150 same
   direction. **No flip at ≥ 2 SE anywhere → the registered withdrawal condition does not
   trigger.** Caveats reported, not hidden: descriptor matchers match only a subset of
   chips (ORB ank130: C2 53/130, C1 34, pretrained 15; AKAZE fewer) — the verdicts hold on
   the matched subsets, and **matchability itself ranks C2 first**, a new favorable
   operational fact (more usable descriptor matches from C2 outputs). The ank30 descriptor
   cells are unmatched-dominated (n ≤ 8): reported without verdict. MI covers every chip
   and agrees with the descriptor ranks.
2. **Mediation:** the C2−C1 KLT gap conditioned on photometric + gradient similarity loses
   **0% of its magnitude** (ank130 −0.702 → −0.702; eu150 −0.434 → −0.434; both still
   significant at α=0.01). The "trained-on-the-metric" explanation receives no support.
3. **Restraint measured directly** (input-silent regions, edge ratio fake/real, n=130):
   **pretrained 1.016, C1 1.023, C2 0.218.** The first two fill input-silent terrain to
   real-image busyness with invented structure (reproducing the historical busy-ratio ≈ 1.0
   finding); C2 emits ~22% of it. Restraint is no longer inferred by elimination.

**Registered decision: the phrase "matcher-independent" is kept**, quoted with its
boundaries: verified across KLT/NCC/phase (area family), ORB/AKAZE (descriptor family,
matched subsets), and MI (statistical); Georef itself remains unmeasurable and every number
is a proxy.
