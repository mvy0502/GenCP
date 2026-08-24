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

**The registered bands did not cover the observed shape. The conclusion below is read off
the curve, not matched to a band — stated plainly, because presenting it as a clean band hit
would misrepresent how it was obtained.**

The registration anticipated two shapes: (A) C1 dips below pretrained at epochs 1–2 then
recovers → cold-D damage; (B) C1 improves monotonically and plateaus → loss-function
reading. Neither occurred. C1 **never dips below pretrained at any epoch** — at epoch 1 it
is already *better* by −0.399 px at 6.3 SE, the wrong sign for damage — and it is **not
monotone** either: it improves to epoch 5 (1.806) then degrades to epoch 20 (2.075). The
mechanical rules therefore return the residual category C ("anything between"), which is
the registration admitting it did not foresee this curve.

**What the curve shows, and why it still answers the question:** the diagnostic separating
the two hypotheses is not monotonicity but the *direction of travel of the C1−C2 deficit*.
A cold-D transient must SHRINK as D warms. The observed deficit exists from epoch 1
(+0.546) and **WIDENS with continued adversarial training** (+0.700 at e20), minimum at e5
(+0.384). At most ~0.16 px of the early e1→e5 narrowing is consistent with a cold-D
component that then disappears; the dominant, growing term tracks the adversarial objective
itself. This inference is **post-hoc with respect to the registered bands** and is offered
as such — its strength comes from the sign and monotone growth of the deficit (t = 11.4 at
e1, 11.8 at e20), not from a pre-committed rule. The control (C2) improves near-monotonically and
plateaus. **Consequence: no warm-start rename; the confirmatory D-warm-up run is not
triggered; "the adversarial term is a liability for GCP generation" survives as a
loss-function statement** — with the B20 caveat and this sweep cited as its test. The
counter-evidence that motivated B1 (fewer points AND worse residuals under C1) is now
explained by B3's direct measurement: the adversarial term buys invented busyness, not
matchable structure.

## B2 — the headline survives the production path
**[STOCH mean-of-8, POST inputs, K=8, n=20]**

> **Disclosed deviation (corrections-log entry 19):** the registration says "score **RGB
> KLT and BT.601-gray KLT**". Both halves ran; **this section reports the BT.601 half
> only and did not say so.** The RGB half is more favourable, not less — C2 0.6030 ±
> 0.0376 px vs pretrained 1.6314 ± 0.2103 / C1 0.8610 ± 0.1205 / C3 0.6372 ± 0.0377;
> paired C2 − pretrained −1.0284 ± 0.1876 (20/20), C2 − C1 −0.2580 ± 0.0901 (18/20);
> same ordering, and the restatement check also passes (|0.6030 − 0.591| = 0.012 px).
> Full RGB table and the raw-data recomputation of both halves: [B2-B3-audit.md](B2-B3-audit.md).
> Every number in this section reproduced from raw KARIOS output, 384/384 cells.

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

> **Disclosed deviations (corrections-log entries 20, 21, 22), found by
> [B2-B3-audit.md](B2-B3-audit.md). Part 1 below reproduces from the raw scores in full;
> parts 2 and 3 do not stand as written.**
>
> - **Entry 20 — part 2's mediation result is void as stated.** The reported conditional
>   is the OLS fitted value at the covariate means, which is **algebraically the raw
>   mean** for any covariates; "loses 0% of its magnitude" could not have come out
>   otherwise and measures nothing. **The sentence "the 'trained-on-the-metric'
>   explanation receives no support" is withdrawn.** On the mediation-capable statistic
>   (the gap at Δsimilarity = 0, same fit): ank130 −0.395 ± 0.124, **43.8% lost**, still
>   significant; eu150 −0.106 ± 0.088, **75.6% lost, significance lost**. The registered
>   "fully mediated" threshold (≥80% **and** loss of significance) is still not met on
>   either set, so **"matcher-independent" is not withdrawn** — but the registration's own
>   fallback applies and the wording must be narrowed proportionally when it is carried
>   into the manuscript.
> - **Entry 21 — the registered MI parabola subpixel refinement was never applied**: all
>   930 MI values sit exactly on the integer pixel lattice. The ±8 px grid is confirmed,
>   and it censors 15.8% of measurements at the bound — more heavily for the worse arms,
>   so −1.260 ± 0.261 is a **lower** bound on the MI margin. MI is quotable as an
>   integer-pixel, bound-censored statistic; its rank agreement with ORB/AKAZE survives.
> - **Entry 22 — B3's harness (`B3_run.py`) and every part-2/part-3 per-chip artifact are
>   gone.** ORB's `nfeatures 2000` and 3 px RANSAC threshold are attested only by the
>   session log; the BFMatcher Hamming cross-check and the 64-bin MI histogram are
>   attested nowhere.
> - **Precision, part 1:** the descriptor Δ values are **paired differences on the
>   intersection** — ORB ank130 n = 29 (not the 53/34 quoted beside it), AKAZE ank130
>   n = 11, eu150 AKAZE n = 3. "No flip at ≥ 2 SE anywhere" holds in every verdict-bearing
>   cell; one nominal flip exists in a no-verdict cell (ank30_ovp AKAZE C2−C3, n = 2).
>   "ank30 … n ≤ 8" is true of ank30_prod; ank30_ovp reaches n = 14.
> - **Part 3 (entry 19 scope):** the three values below are **medians**; the registered
>   read-out was the per-arm **distribution**, supplied in the audit. C2's ratio is below
>   0.5 on 84.6% of chips and never exceeds 1.154 — more favourable than the median alone.

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
