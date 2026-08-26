# Common-support audit of the reported arm comparisons — results

Registered in [plugin-gate-registration-C2.md](plugin-gate-registration-C2.md) (`901dfc3`)
before any contrast below existed. Convention: **Δ = candidate − baseline; negative =
candidate better.** Inference path: all arms are the stochastic (dropout-active) evaluated
path, as originally scored — **nothing was re-inferred and nothing was re-scored by KARIOS**.
This is a re-reading of committed point-level artifacts.

**Why this exists.** Gate D showed that when two arms yield different numbers of matched
points, the arm with fewer points can look better purely because the points it loses are the
hard ones — about 79% of the observed advantage in that case. The mechanism is not specific
to Gate D.

---

## Pass 1 — the screen

Threshold stated before any number was looked at: **materially different ⇔
|median(n_A) − median(n_B)| / max(median) ≥ 10%.** Gate D's own case was 60→50 (17%) and
61→48 (21%), both above the line.

### Median matched points per arm

| package | per-arm medians | pairwise comparisons ≥ 10% |
|---|---|---|
| C45 (2×2: pre, C1, C2, C4, C5) | pre **51**, C1 59, C4 62, C2 72, C5 **88** | **9 / 10** |
| C45 b2 (adds C3) | pretrained **92**, C4 156, C1 164, C3 210, C5 224, C2 **235** | **12 / 15** |
| C45 e1 | C4_e1 60, C5_e1 74 | 1 / 1 |
| C45 epoch sweep | C4_e* 59–62, C5_e* 74–88 | 29 / 45 |
| B1 (epoch sweep) | pre **51**, C1_e* 55–63, C2_e* 70–74 | 36 / 55 |
| B2 (band conversions) | pretrained_rgb **78** … C2_bt601 **235** | 26 / 28 |

**Nothing is "close" enough to skip.** Almost every comparison this project reports is
between arms with materially unequal matched-point counts. Saying so explicitly, as
instructed, rather than skipping silently: **there is no package in which all pairwise
comparisons fall under 10%.**

### The direction is the opposite of Gate D's, and that matters

In **every** flagged comparison, the arm with **more** points has the **lower** median error
— pretrained carries the fewest points (51) and the worst error (2.588 px); C5 carries the
most (88) and among the best (1.134 px). Gate D's survivorship signature is the reverse: there
the arm with **fewer** points looked **better**.

So the two mechanisms are distinguishable, and both had to be tested:

- **Survivorship** (Gate D's): the low-count arm discarded its hard points, so its median is
  artificially low. Correcting would make the low-count arm *worse* and the gap **wider**.
- **Marginal-point inflation**: the high-count arm found extra easy points, so *its* median is
  artificially low. Correcting would make the gap **narrower**.

---

## What was already covered, and is not re-derived here

[common-support-registration.md](common-support-registration.md) and
[common-support-results.md](common-support-results.md) audited the six-seed block — arms
**C1, C2, C4, C5** — and established two things this package inherits:

1. **Point-level common support is not constructible for these arms.** KLT keypoints are
   detected independently per arm on that arm's own generated image, so at 2 px tolerance
   more than half the chips have **zero** common points (~4.78 per chip against per-arm counts
   of 50–137). *The Gate D common-support test hit the same wall from the other side: only
   ~14 of ~66 points paired at 1 px, and 10–12 of 30 chips fell below the 5-pair floor.*
2. **Equal-count truncation is the constructible substitute**, and it was validated: C5
   surrenders 38–39% of its points, the primary (C5−C4) holds 6/6 and grows, the secondary
   (C5−C2) holds 6/6 and shrinks by ~11%. The asymmetry is real and is **not** the
   explanation.

**Pass 2 therefore tests only what that work left out: every contrast involving `pretrained`,
plus B2's band conversions.** Method is the prior package's PRIMARY rule verbatim — per chip
`K_c = min` over the two arms; each arm's residual is the median of its own `K_c`
**best-scoring** points, ranked by the KLT `score` column descending, never by radial error.

**Control, run before any contrast:** all five arms reconstruct their committed
`C45_per_chip.csv` medians and counts exactly — **8/8 chips, worst |diff| 0.000000**.

---

## Pass 2 — results. Nothing flips; nothing moves materially

130-chip Ankara set (B2: 20 chips). Δ = candidate − baseline, negative = candidate better.

### A. Contrasts involving pretrained — not previously covered

| contrast | points | discarded | Δ original | Δ equal-count | change | verdict |
|---|---|---|---|---|---|---|
| C1 − pre | 51 vs 59 | pre 2.6%, C1 27.7% | −0.4874 (t=−6.47) | **−0.5056** (t=−6.43) | −0.0182 | holds, **widens** |
| C2 − pre | 51 vs 72 | pre 1.3%, C2 45.6% | −1.1869 (t=−18.15) | **−1.1966** (t=−17.74) | −0.0097 | holds, **widens** |
| C4 − pre | 51 vs 62 | pre 2.5%, C4 27.5% | −0.5972 (t=−9.85) | **−0.6048** (t=−9.47) | −0.0076 | holds, **widens** |
| C5 − pre | 51 vs 88 | pre 0.5%, C5 49.4% | −1.0844 (t=−15.18) | **−1.0986** (t=−14.50) | −0.0142 | holds, **widens** |

**The registered primary prediction is confirmed.** All four widen. C5 discards **49.4%** of
its matched points to equalise with pretrained and the contrast still grows.

### B. Cross-check against the six-seed block (single seed here, so directional only)

| contrast | Δ original | Δ equal-count | change | verdict |
|---|---|---|---|---|
| C5 − C4 | −0.4871 (t=−9.18) | −0.5020 (t=−9.40) | −0.0149 | holds, widens |
| C5 − C2 | +0.1025 (t=+2.46) | +0.1017 (t=+2.39) | −0.0008 | holds, narrows |
| C2 − C1 | −0.6995 (t=−11.82) | −0.7044 (t=−11.67) | −0.0050 | holds, widens |

Directionally consistent with the six-seed block: the primary grows, the secondary shrinks
slightly. This is a different, single-seed run, so it corroborates rather than replicates.

### C. B2 band conversions, rgb vs bt601 within each arm

| arm | points | Δ original | Δ equal-count | change | verdict |
|---|---|---|---|---|---|
| pretrained | 78 vs 92 | −0.2616 (t=−2.35) | −0.2906 (t=−2.79) | −0.0290 | holds, widens |
| C1 | 136 vs 164 | −0.0970 (t=−1.60) | −0.0975 (t=−1.64) | −0.0005 | holds, widens |
| C2 | 204 vs 235 | −0.0103 (t=−0.43) | −0.0100 (t=−0.42) | +0.0003 | holds, narrows |
| C3 | 182 vs 210 | −0.0262 (t=−1.96) | −0.0336 (t=−2.09) | −0.0074 | holds, widens |

**The registered secondary prediction is confirmed** — B2 barely moves; largest change
−0.0290 px.

### Summary

**0 sign flips. 0 changes beyond 0.15 px. 0 changes even beyond 0.05 px.** The largest
movement anywhere is **−0.0290 px** (B2 pretrained), and the largest among the headline
contrasts is **−0.0182 px** (C1 − pre).

---

## Which reported conclusions survive

| conclusion | status |
|---|---|
| Fine-tuned arms beat pretrained (C1, C2, C4, C5 each) | **survives unchanged — and strengthens.** All four widen under equal-count |
| C2 beats C1 | **survives unchanged** (−0.6995 → −0.7044) |
| C5 beats C4 (primary) | **survives unchanged** (−0.4871 → −0.5020); six-seed block already showed 6/6 holds |
| C5 − C2 positive (secondary) | **survives** here (+0.1025 → +0.1017); the six-seed block is the governing evidence and already reported it holds 6/6 with the caveat that its narrowest seed is effectively zero |
| B2 band-conversion contrasts | **survive unchanged**, all four |
| Gate D: eval-mode "materially better on C2" | **does not survive** — already withdrawn in [plugin-results.md](plugin-results.md) Item C |

**Nothing weakens.** The only conclusion in this project that the mechanism actually
overturned is Gate D's, and that was found and withdrawn before this audit ran.

---

## Limitation, restated rather than assumed

**Equal-count truncation removes the count asymmetry; it does not make the point sets
identical.** The arms still matched different places on the ground. What this bounds is *how
much of a contrast the count asymmetry can explain* — measured here as at most 0.03 px, and
by the six-seed block as ~11% of the secondary. It does **not** establish that two arms were
compared on the same ground, and no amount of truncation can, because point-level common
support is not constructible for independently-detected keypoints.

This is the same power limitation stated for Gate D, and it applies to every row above.

---

## What would need amending, if anything

**Nothing is amended in this package.** For the record, the list is empty: no reported
conclusion changed sign, and none moved by more than 0.03 px. The documents that describe
these contrasts — [common-support-results.md](common-support-results.md),
[seed-block-results.md](seed-block-results.md), [phase-c-results.md](phase-c-results.md),
[B2-B3-audit.md](B2-B3-audit.md) — stand as written.

The one thing worth considering, and it is an addition rather than an amendment: the papers
and audits could state that the pretrained contrasts were **also** checked under equal-count
truncation, since `pretrained` is the arm most exposed to the mechanism and was the one gap
in the earlier coverage.
