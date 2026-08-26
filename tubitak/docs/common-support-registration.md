# Registration — common-support re-scoring of the six-seed block

**Registered 2026-08-26, BEFORE any common-support contrast is computed.** What has been done
at the time of writing is **feasibility work only**: counting how many matched points the four
arms share, to establish which operationalisations are constructible at all. **No contrast, no
sign tally, and no per-seed residual has been computed under any common-support definition.**
The counts that feasibility work produced are reported in §2 because they determine the design.

Standing practice 4 governs; standing practice 10 governs the artifacts.

## The problem

Each arm's chip residual is **the median over the matched points that arm itself produced.**
Median surviving points per chip differ systematically by arm: pretrained 51, C1 59, C4 62,
C2 72, **C5 88**. **The number of points entering each arm's median is a post-treatment
variable, and conditioning the outcome on it is selection on a post-treatment variable.**

**The direction of the bias is not the same for every contrast, and that is the reason this
package exists.**

- For the **primary** (C5 − C4), C5 keeps more points than C4. If extra points are more
  marginal and therefore worse, they drag C5's median **up** — toward C4 — so the measured
  primary is **conservative**. A selection artefact makes the primary look *smaller* than it
  is.
- For the **secondary** (C5 − C2), the bias runs **the wrong way**. C5 keeps 88 points against
  C2's 72. The same mechanism drags C5's median up relative to C2's, and the secondary is a
  **positive** contrast of only **+0.063 px** (six-seed mean). **A selection artefact could in
  principle produce the entire secondary effect.**

**The secondary is the reading whose registered consequence controls the title.** That is why
this is being tested rather than noted.

## §2 — Point-level common support is NOT CONSTRUCTIBLE, and this is registered as a finding

The obvious operationalisation — restrict every arm's median to the matched points that **all
four arms found** — cannot be built from these artifacts. Established by counting before any
contrast was computed:

**KLT keypoints are detected independently per arm, on that arm's own generated image.** The
four arms therefore share no point identity. Measured on seed 45, all 130 chips:

| tolerance for calling two points "the same" | common points per chip (mean) | chips with ZERO common points |
|---|---|---|
| exact (x0, y0) match | ≈ 0.01 | ~129 / 130 |
| **2 px** | **4.78** | **69 / 130** |
| 5 px | (larger, but see below) | — |

**At a 2 px tolerance more than half the chips have no common points at all**, and the
surviving chips carry about five points each — against per-arm counts of 50 to 137.

**A larger tolerance does not rescue it; it destroys the measurement.** The residuals being
measured are ~1.4 px (C2) to ~2.0 px (C1). **A tolerance of 2 px is already the size of the
effect, and 5 px is several times it.** Declaring two points "the same" when they sit further
apart than the quantity under test is circular: the matching tolerance would absorb the
signal.

**Registered conclusion: point-level common support is reported as NOT CONSTRUCTIBLE, with
these counts as the evidence, and no tolerance-matched version is computed.** It is not
attempted and then quietly dropped; it is ruled out in advance, in writing, with the numbers
that rule it out.

## §3 — What IS constructible, and what is registered

### PRIMARY — equal-count truncation (targets the stated concern directly)

The concern is not that the arms matched *different* points. It is that **C5's median is taken
over more points, and the extra ones are more marginal.** That can be tested without point
identity, by equalising the **count**.

- For each chip *c*, let **K_c = min over the four arms of that arm's matched-point count on
  chip c**.
- Each arm's chip residual is recomputed as the **median of its own K_c best-scoring points**,
  ranked by the KLT `score` column, **descending (higher score = better match)**.
- Every arm then contributes **exactly the same number of points on every chip**, so no arm's
  median can be inflated or deflated by carrying more marginal matches than another.

**Ranking is by `score`, never by `radial error`.** `radial error` is the outcome; ranking on
it and then taking a median of it would be circular. `score` is a match-quality measure in
[0.01, 0.93] produced by the matcher, and it is the only pre-outcome quality ordering the
artifact provides. **It is still a post-treatment variable, and that limitation is stated with
the result rather than hidden**: this equalises count, which is the specific mechanism under
suspicion, and does not claim to remove all post-treatment conditioning.

### SECONDARY — chip-level common support

- A chip enters only if **all four arms produced at least K matched points on it**, for
  **K = 1, 10, 20, 30** reported side by side (the floor sweep already used and registered in
  [phase-d-checks-registration.md](phase-d-checks-registration.md) check 5, applied here to
  all four arms jointly rather than per pair).
- Arms' medians are otherwise unchanged.

This addresses selection at the chip level — chips that only match well in some arms — which
is a different mechanism from the within-chip one the primary targets.

### Reported for every version

Per seed, for each of the six Modal seeds (45–50):

1. **Common-support n**: chips retained, and K_c summed or averaged.
2. **What each arm loses**: points discarded per arm, absolutely and as a fraction — this is
   where the asymmetry is visible, and C5 is expected to lose the most by construction.
3. **Every registered contrast recomputed**: C5 − C4, C1 − C2, C4 − C5, C5 − C2, and I_raw,
   with **per-seed values and sign tallies**.
4. **Both versions side by side.** The original numbers are never replaced, overwritten or
   silently updated. Every table carries both.

Seed-level t-intervals (df = 5, t\* = 2.571) are **reported, not required**, as everywhere
else in this package.

## §4 — REGISTERED READINGS

Scored on the six confirmatory Modal seeds only, as sign replications, exactly as the original
readings were:

1. **PRIMARY: C5 − C4 negative in all six seeds under common support.**
2. **SECONDARY: C5 − C2 positive in all six seeds under common support.**
3. C1 − C2 positive in all six; C4 − C5 positive in all six.

**Expected direction of change, recorded before the numbers so that "as predicted" cannot be
claimed afterwards.** If the point-count asymmetry is doing work, then under equal-count
truncation the **primary should get LARGER** (its bias was conservative) and the **secondary
should get SMALLER** (its bias ran the wrong way). Neither movement is a reading; the readings
are the sign tallies above. **This paragraph exists so that a shrinking secondary is
recognised as the predicted direction rather than presented as a surprise.**

## §5 — THE GATE

> **If the secondary's 6/6 does not survive common-support re-scoring, execution STOPS and
> the result is reported IMMEDIATELY.** No further analysis, no document edits beyond
> recording the result, and no attempt to find a variant under which it survives.

**What is at stake, written before the answer.** The secondary's registered consequence is
that if C5 − C2 is not positive in every seed, the LPIPS-alone penalty moves from a result to
a discussion-section hypothesis, the claim narrows from "plausibility pressure" to "the
adversarial term", **and the title changes with it**. If the 6/6 was a selection artefact, that
consequence fires on the corrected numbers, and it fires whichever version the paper prefers.

**The original 6/6 is not defended by being first.** If the two versions disagree, both are
reported, the disagreement is the finding, and the decision about which governs is the
supervising session's — it is not taken here and it is not taken by whichever number is more
convenient.

## §6 — Scope

- **This is a re-scoring of existing artifacts. No training, no inference, no GPU.** It reads
  the committed KARIOS per-point CSVs under `tubitak/data/tool_runs/C45_s{45..50}_modal/`.
- **It does not modify the frozen pipeline or any published number.** The original per-chip
  CSVs are untouched inputs.
- **n = 6 seeds**, the same confirmatory block, so the sign readings carry the same
  P = 1/64 arithmetic as the originals **if and only if** they are read as replications of the
  same pre-fixed directions — which they are.
- Common-support results are a **robustness re-scoring**, reported beside the registered
  numbers. They do **not** silently become the headline; which version the manuscript leads
  with is a decision recorded separately after both exist.

## §7 — Artifacts

Per standing practice 10, the per-seed common-support outputs and the script that produces
them are committed to `tubitak/docs/evidence/common_support/`, with sha256 values in the
manifest, **including if the result is inconvenient.**

Nothing is computed until this registration is committed and pushed.
