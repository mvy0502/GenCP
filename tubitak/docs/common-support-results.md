# Common-support re-scoring — results

Written 26 August 2026, after
[common-support-registration.md](common-support-registration.md) was committed and pushed
(`89eee9f4`) and before any contrast was computed. Re-scoring of committed artifacts only:
no training, no inference, no GPU, frozen pipeline untouched.

**THE GATE HOLDS. The secondary is positive in all six seeds under every common-support
version tested.** Execution continues.

**All four registered readings survive**, under equal-count truncation and under all four
chip-level floors. **The point-count asymmetry is real and large — C5 discards 38–39% of its
points to equalise — but it accounts for only about 11% of the secondary effect, not for the
effect.**

---

## 1. The point-count asymmetry is exactly as suspected, and it is large

Under equal-count truncation, K_c = min over arms of that chip's matched-point count. Every
arm then contributes the same number of points on every chip. **All 130 chips are retained in
every seed** — no chip had an arm with zero matches.

| seed | chips | mean K_c | C1 drops | C2 drops | C4 drops | **C5 drops** |
|---|---|---|---|---|---|---|
| 45 | 130 | 67.3 | 12.4% | 33.1% | 7.4% | **39.1%** |
| 46 | 130 | 68.4 | 11.7% | 32.6% | 5.6% | **38.2%** |
| 47 | 130 | 68.4 | 11.6% | 32.9% | 6.5% | **38.7%** |
| 48 | 130 | 70.0 | 9.1% | 31.4% | 6.8% | **36.4%** |
| 49 | 130 | 68.2 | 12.5% | 31.9% | 7.1% | **38.3%** |
| 50 | 130 | 68.2 | 10.9% | 32.3% | 6.7% | **38.6%** |

**C5 gives up nearly two-fifths of its matched points and C4 gives up one-fifteenth.** The
selection concern was well founded: the arms were not being compared on comparable point sets,
and the imbalance runs in exactly the direction that motivated this package.

---

## 2. Every registered reading, both versions side by side

Original numbers are never replaced. Both appear in every table.

### PRIMARY — C5 − C4, registered negative in all six

| seed | original | equal-count | change |
|---|---|---|---|
| 45 | −0.6153 | −0.6306 | −0.0153 |
| 46 | −0.6462 | −0.6309 | +0.0153 |
| 47 | −0.6162 | −0.6117 | +0.0045 |
| 48 | −0.5942 | −0.5907 | +0.0035 |
| 49 | −0.6054 | −0.6307 | −0.0253 |
| 50 | −0.5775 | −0.6249 | −0.0474 |
| **tally** | **6/6** | **6/6 — HOLDS** | mean −0.6091 → **−0.6199** |

### SECONDARY — C5 − C2, registered positive in all six *(the gated reading)*

| seed | original | equal-count | change |
|---|---|---|---|
| 45 | +0.0619 | +0.0446 | −0.0173 |
| 46 | +0.0068 | +0.0199 | +0.0131 |
| 47 | +0.0665 | +0.0739 | +0.0074 |
| 48 | +0.0799 | +0.0888 | +0.0089 |
| 49 | +0.1085 | +0.1044 | −0.0041 |
| **50** | +0.0519 | **+0.0024** | **−0.0495** |
| **tally** | **6/6** | **6/6 — HOLDS** | mean +0.0626 → **+0.0557** |

Seed-level 95% CI under equal-count (df = 5, t\* = 2.571): **[+0.0136, +0.0978]**.
**Reported, not required** — the registered reading is the sign tally.

### Main effects

| contrast | original tally | equal-count tally | mean original → equal-count |
|---|---|---|---|
| C1 − C2 positive in all six | 6/6 | **6/6 — HOLDS** | +0.6773 → +0.6775 |
| C4 − C5 positive in all six | 6/6 | **6/6 — HOLDS** | +0.6091 → +0.6199 |

### Chip-level common support — floors applied to all four arms jointly

| floor | chips retained per seed | C5 − C2 per seed | tally |
|---|---|---|---|
| K ≥ 1 | 130 ×6 | +0.0619 +0.0068 +0.0665 +0.0799 +0.1085 +0.0519 | **6/6** |
| K ≥ 10 | 129–130 | +0.0715 +0.0068 +0.0665 +0.0799 +0.1085 +0.0519 | **6/6** |
| K ≥ 20 | 123–125 | +0.0828 +0.0121 +0.0790 +0.0876 +0.1546 +0.0801 | **6/6** |
| K ≥ 30 | 115–118 | +0.0917 +0.0373 +0.0890 +0.1131 +0.1418 +0.0944 | **6/6** |

The primary is 6/6 at every floor as well (most negative value −0.6340, least −0.5447).

**The floor sweep moves the secondary in the opposite direction to a selection artefact.**
Restricting to chips where *all four arms* match well makes the secondary **larger**, not
smaller — at K ≥ 30 every seed is at least +0.0373 and the narrowest margin more than
quintuples. If marginal points were manufacturing the secondary, removing the chips that
depend on them most would have shrunk it.

---

## 3. What this establishes

**The predicted directions both appeared, and both are small.** The registration recorded
before the numbers that if the count asymmetry were doing work, the primary should grow and
the secondary should shrink. **Both did.** The primary grew by 0.0108 px (1.8%) and the
secondary shrank by 0.0069 px (11%).

**So the selection artefact is real and it is not the explanation.** It accounts for roughly
**11% of the secondary**, leaving 89% standing after the arms are equalised on point count and
C5 has surrendered 38% of its matches. The hypothesis that a selection artefact "could produce
all of it" is **tested and rejected**.

**This strengthens the secondary rather than merely sparing it.** Before this re-scoring, the
+0.063 px was open to the objection that it was an artefact of C5 keeping more marginal
points. That objection now has a measured answer, and the answer survives four floor variants
that each cut the data a different way.

---

## 4. Where it got more fragile, stated because the tally alone would hide it

**The 6/6 holds as a sign reading. Two seeds now sit within one chip-level standard error of
zero, and the narrowest seed changed identity.**

- **Seed 50 is the new narrowest margin at +0.0024 px**, down from +0.0519 — the single
  largest movement in the table. Its chip-level paired SE is ±0.0505, so the margin is
  **1/20th of its own noise**.
- Seed 46, previously narrowest at +0.0068, moved *up* to +0.0199 (SE ±0.0426).

**Both are far inside their own chip-level uncertainty, and were before this re-scoring too.**
The registered reading is sign replication across seeds, not per-seed significance, and it is
that reading which holds — six independent seeds all landing positive is the evidence, and
P = 1/64 is unchanged. **But the manuscript should not describe the secondary as comfortable.
It is a consistent small positive effect, six times out of six, whose narrowest seed is
effectively zero.** That sentence is more defensible than the tally alone and it is the one to
write.

**The interaction moved further from its already-failed reading.** I_raw is negative in
**4 of 6** seeds under equal-count truncation, down from 5 of 6 — seed 50 joins seed 46 in
flipping positive. The interaction reading had already failed at 5/6 and its consequence
already fired ([seed-block-results.md](seed-block-results.md) §4); this makes the failure less
marginal, changes no decision, and is reported for completeness.

---

## 5. Limitations, stated with the result

**Point-level common support was not constructible and was not attempted.** KLT keypoints are
detected independently per arm on that arm's own generated image, so the arms share no point
identity: at a 2 px tolerance, 69 of 130 chips have zero common points. A tolerance large
enough to produce a usable set would exceed the residuals under test and absorb the signal.
Ruled out in the registration, in writing, before any contrast was computed.

**Equal-count truncation ranks by `score`, which is itself post-treatment.** This was
registered as a known limitation rather than discovered afterwards. Ranking by `radial error`
would have been circular — it is the outcome. **What this procedure removes is the count
asymmetry, which is the specific mechanism under suspicion; it does not claim to remove all
post-treatment conditioning**, and no result here should be described as "unbiased".

**These are chip-level standard errors within each seed.** The inference is at the seed level
across six seeds, as the whole seed-replication package requires; the per-seed ± values quoted
in §4 are context for how close a given seed sits to zero, not evidence about the treatment.

---

## 6. Artifacts

Per standing practice 10, committed to `tubitak/docs/evidence/common_support/`:

- `common_support.json` — every per-seed figure in this document.
- `common_support_rescore.py` — the script, committed at
  `tubitak/scripts/common_support/`, because an output without its producer is
  re-implementable rather than reproducible.

**This is not a corrections-log entry.** A registered robustness check returning its registered
readings is the system working. **No published number is modified**; the common-support values
are reported beside the originals, and which version the manuscript leads with is a separate
decision recorded after both exist.
