# Registration — common-support audit of the arm comparisons the six-seed block did not cover

**Registered 2026-08-26, before any contrast below is computed.** Convention:
**Δ = candidate − baseline; negative = candidate better.** Inference path: all arms are the
stochastic (dropout-active) evaluated path, as originally scored — nothing is re-inferred.

## Why this is narrow

The mechanism is the one Gate D measured: when two arms yield different numbers of matched
points, the difference in their medians can be an artefact of *which* points each arm kept
rather than of accuracy.

**Most of this ground is already covered.**
[common-support-registration.md](common-support-registration.md) and
[common-support-results.md](common-support-results.md) audited the six-seed block —
arms **C1, C2, C4, C5** — and established two things this registration inherits rather than
re-derives:

1. **Point-level common support is not constructible for these arms.** KLT keypoints are
   detected independently per arm on that arm's own generated image, so at a 2 px tolerance
   more than half the chips have **zero** common points. (The Gate D common-support test hit
   the same wall from the other side: only ~14 of ~66 points paired at 1 px and 10–12 of
   30 chips fell below the floor.)
2. **Equal-count truncation is the constructible substitute**, and it was validated: the
   asymmetry is real and large (C5 surrenders 38–39% of its points) but accounts for only
   ~11% of the secondary effect.

**What that work did not cover is every contrast involving `pretrained`**, and the B2 band
conversions. Those are what this registration tests, and they matter because the screen
(Pass 1) shows `pretrained` carries the **fewest** matched points of any arm — median 51
against C5's 88 — so it is the arm most exposed to the mechanism.

## Method — the prior package's rule, unchanged

Per chip, **K_c = min over the two arms in the contrast** of that chip's matched-point count.
Each arm's chip residual is then the **median of its own K_c best-scoring points, ranked by
the KLT `score` column descending**. Ranking is never by radial error, which would be
selection on the outcome. This is exactly `tubitak/scripts/common_support/common_support_rescore.py`'s
PRIMARY rule, reused so the two packages' numbers are commensurable.

## Invariances — assumed identical on both sides

Same chips (the 130-chip Ankara set), same references, same KARIOS config and outputs, same
warp geometry, same analysis code path. Nothing is re-inferred or re-scored by KARIOS: this
is a re-reading of committed point-level artifacts. The only thing that changes between the
"original" and "equal-count" columns is how many of each arm's points enter its median.

**Control, run before any contrast:** each arm's per-chip median and point count must be
reconstructible from its KLT CSVs and match the committed `C45_per_chip.csv` exactly. Already
executed: **8/8 chips exact, worst |diff| 0.000000, for all five arms** (`pre` from
`ankara/run/results`, `C1`/`C2` from `B1/karios/C{1,2}_e20`, `C4`/`C5` from
`C45/karios/C{4,5}`). Had it not matched, nothing below would mean anything.

## Contrasts

1. `pre` vs each of **C1, C2, C4, C5** on the 130-chip Ankara set.
2. B2 band conversions: **rgb vs bt601** within each of pretrained, C1, C2, C3.

## Registered predictions

**Primary prediction — the pretrained contrasts should HOLD, and should WIDEN.** Under
equal-count truncation the higher-count arm discards its *lowest-scoring* points, which are
its most marginal, so its median improves; `pretrained`, having the fewest points, discards
fewest or none and is left near-unchanged. The gap in favour of the fine-tuned arms should
therefore grow. **This is the opposite of the Gate D situation**, where the arm with fewer
points was the one that looked better.

**Secondary prediction — B2's within-arm rgb-vs-bt601 contrasts should be little moved.** The
count differences there are 13–17%, well below the 30–40% seen between arms, and both sides
of each contrast are the same model.

**The alternative outcome, stated so it cannot be explained away.** If any `pretrained`
contrast **shrinks materially (≥ 0.15 px, the project's standing band) or flips sign**, then
the fine-tuned-beats-pretrained conclusion rests partly on point-count asymmetry and must be
restated. That outcome is reported plainly and the affected document is named — but nothing
is amended in this work package.

## Bands and limitation

Standing bands: |Δ change| ≤ 0.05 px indistinguishable; > 0.15 px material.

**The power limitation stated for Gate D applies here too and is restated rather than
assumed:** equal-count truncation removes the count asymmetry but does not make the point
*sets* identical — the arms still matched different places. It bounds how much of a contrast
the asymmetry can explain; it does not prove two arms were compared on the same ground.
