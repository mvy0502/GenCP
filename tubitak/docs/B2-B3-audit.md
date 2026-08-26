# B2/B3 registration audit — the E3 test applied to the headline package

Date: 2026-08-24. Work item 1 of [paper-roadmap.md](paper-roadmap.md), first two
registrations. Trigger is the same as T1's: corrections-log entry 16 showed that a
registration-integrity claim of this exact form ("registered … before any number exists")
failed against run artifacts in E3, so every registration the paper leans on gets the
identical three-leg audit — commit timestamps vs artifact mtimes, run configuration
diffed against the registration *text*, and a full recomputation of the reported tables
from raw outputs. Method and structure follow [T1-audit.md](T1-audit.md).

Registration: [headline-registrations.md](headline-registrations.md), commit `8c6d041`.
Results: [headline-results.md](headline-results.md), commit `2302130`.
B1 is out of scope here (it self-reports its band failure in the results document); it
appears below only where it accounts for the 26-minute window.

**Verdict in one line: the timeline claim holds, B2 reproduces cell-for-cell, B3 part 1
reproduces cell-for-cell — and B3 parts 2 and 3 carry four real deviations, one of which
voids a reported conclusion.** Details in §C and the verdict.

## A. Timeline claim — PASS

Claim audited: "**Registered 2026-08-21, branch `tubitak-tool`, before any number
exists.**"

Commit ordering alone cannot carry this claim: the window between the two commits is
**26 min 02 s**, and it has to contain B1 (10 cells × 130 chips), B2 (20 renders, 640
inferences, 240 KARIOS runs across two band conversions), B3 (~2,800 matcher
invocations plus parts 2 and 3), and the writing of three results sections. So the
window is reconstructed artifact by artifact.

| event | time (local, UTC+03) | evidence |
|---|---|---|
| registration decision recorded in the session log (obs 259) | 11:53:16 | claude-mem `159a490c15f6dcff` |
| **registration commit `8c6d041`** | **11:53:25** | git (author = committer; no rebase) |
| B1 launched (async agent) — obs 261 | 11:54:13 | `a6b34c781fbdc5bb` |
| B2 launched (async agent) — obs 262 | 11:54:36 | `a59f615d89452b77` |
| B3 launched (background task `b9coxcyvv`) — obs 268 | 11:56:48 | `2b8bb052d35e90ce` |
| B2 earliest artifact — `B2/extent.osm.pbf` (osmium extract) | 11:58:25 | mtime |
| B2 renders (`B2/inputs/{tif,png}`, 40 files) | 11:58:47 → 11:59:56 | mtime |
| B2 inference, 640 fakes (4 arms × 8 seeds × 20 chips, 8-way concurrent) | 12:00:12 → 12:00:26 | mtime |
| B2 mean-of-8 + warp + BT.601 grays (120 files) | 12:00:49 → 12:00:50 | mtime |
| B2 KARIOS, 160 runs both bands (8 workers) | 12:01:00 → 12:01:52 | mtime |
| **B2 first derived number — `B2_per_chip.csv`, `B2_summary.json`** | **12:02:00** | mtime |
| **B3 first derived number — `B3_scores.csv`** | **12:04:29** | mtime |
| B3 `B3_summary.json` (parts 1–3) | 12:05:37 | mtime |
| B1 harness + checkpoint staging | 12:08:43 → 12:10:13 | mtime |
| B1 inference (2,610 files) and warps (1,300) | 12:10:04 → 12:10:39 | mtime |
| B1 KARIOS, 1,300 runs (14,450 files) | 12:10:47 → 12:17:18 | mtime |
| B1 `B1_per_chip.csv` / `B1_summary.json` | 12:17:30 / 12:18:01 | mtime |
| **results commit `2302130`** | **12:19:27** | git (author = committer) |

**Classification of everything predating 11:53:25.** Across B1/B2/B3 exactly **ten** files
predate the registration commit, all in `B1/ck/`: the ten generator checkpoints
`C{1,2}_e{1,2,5,10,20}/…/latest_net_G.pth`, written 2026-08-19 22:45:42 → 23:10:35 by the
Kaggle download, 217 MB each. Every one is **(i) an input**. **No matcher output, no
summary JSON or CSV, and no file containing a computed score exists before 11:53:25 in
any of the three packages.** B2 and B3 have *zero* files of any kind before the
registration commit.

One case needs stating explicitly rather than being left implicit. B3 part 2 is
conditioned on per-chip KLT residuals that live in `pkgA/pkgA_scores.csv`
(mtime 2026-08-21 **11:04:38**, i.e. 49 minutes *before* registration), and the raw
unconditioned C2−C1 gap **−0.70 ± 0.06** was already published in
[packageA-results.md](packageA-results.md) line 31 before B3 was registered. This is not
a pre-dated result: B3 part 2 is registered as a "**Mediation check (no new runs)**" whose
input is exactly that Package A residual set. The *new* quantity B3 claims — the
conditional gap — has no artifact before 12:04:29. Classified **(i) input, registered as
such**.

**Elapsed wall time and parallelism**, so the 26-minute window is explained rather than
asserted: B2 = 3 min 35 s end-to-end (11:58:25 → 12:02:00), B3 = 7 min 41 s
(11:56:48 → 12:05:37, overlapping B2 entirely), B1 = 9 min 18 s (12:08:43 → 12:18:01).
The three ran as separate agents/background tasks; B2 and B3 overlap, B1 follows. Inside
B2, the 640 inferences ran 8 concurrent CPU processes (`gpu_ids: -1`, 20 images per
process, all 8 seeds of an arm finishing in the same second — 12:00:14 pretrained,
12:00:18 C1, 12:00:22 C2, 12:00:26 C3) and the 160 KARIOS runs ran 8-way in 52 s. The
window is tight but fully accounted for; 3 min 24 s of it is unexplained by artifacts and
covers the writing of the results document itself.

**Session/observation log.** It exists and covers 11:00–12:30 in full (56 observations,
same claude-mem database that decided entry 16). Its decisive lines *support* the claim,
which is the opposite of E3:

> **obs 259, 11:53:16** — "File: tubitak/docs/headline-registrations.md, registered
> 2026-08-21 before any number computed … **No numbers exist yet; every design is
> frozen.**"

> **obs 262, 11:54:36** — B2 launch, recording the materiality rule *before* the run:
> "if BT.601 C2 differs from quoted 0.591 px by >0.15 px, headline is RESTATED and
> restated number goes to institution regardless of direction".

> **obs 286, 12:02:10** — the verdict read *after* the artifacts: "Production path C2
> BT.601: 0.5927±0.0409 px … Difference: +0.0017 px".

The log also records a false start worth preserving: **obs 263 (11:54:50)** reports
"packageA-urban-chips.csv query returns zero Ankara urban rows", and **obs 264
(11:54:57)** corrects it — the filter had used columns `$2/$3` instead of `$1/$4`. Seven
seconds, no artifact, no consequence; recorded here so the log's own contradiction is not
discovered later and read as something else.

**Leg A verdict: PASS. This is not the E3 failure repeating.** No B2 or B3 score predates
the registration commit.

## B. Reported tables vs raw outputs

### B2 — PASS, 384/384 cells

Recomputed from the 160 raw KARIOS KLT files
(`B2/karios/{band}/{arm}/{stem}/*/KLT_matcher_*.csv`) under the documented formula
(per-chip statistic = median `hypot(dx, dy)`; per-arm = mean of the 20 per-chip medians;
SE = sd/√20; paired = mean of per-chip differences). Tolerance 1e-9 against
`B2_per_chip.csv`, 5e-4 against the rounded summary.

- **320/320 per-chip cells** (20 chips × 4 arms × 2 bands × {median, point count})
  reproduce exactly. Zero mismatches.
- **40/40 per-arm summary cells** (8 arm×band × {mean, SE, median-of-medians,
  points-median, zero-point count}) reproduce: pretrained 1.3698 ± 0.1612 / C1 0.7640 ±
  0.0712 / C2 **0.5927 ± 0.0409** / C3 0.6109 ± 0.0375 (BT.601) — matching the reported
  1.370 / 0.764 / 0.593 / 0.611 and the headline 0.5927 ± 0.0409.
- **20/20 paired cells** (4 pairs × {mean, SE, t, n, chips-first-better}) reproduce:
  C2 − pretrained = **−0.7771 ± 0.1247**, t = −6.23, C2 better on **20/20** chips;
  C2 − C1 = **−0.1713 ± 0.0420**, t = −4.08, better on **19/20**. Both match the
  reported −0.777 ± 0.125 (20/20) and −0.171 ± 0.042 (19/20).
- **4/4 restatement cells:** |0.5927 − 0.591| = 0.0017 px < 0.15 → not fired. Correct.

**Estimator confirmed as mean-of-8, not a single draw.** All 8 seed directories
`out_{arm}/s{42…49}` exist for all four arms with 20 fakes each (640 total). Each of the
80 `mean8/{arm}/{stem}.png` files was recomputed from its 8 draws as
`round(mean(draws))`: **80/80 byte-identical**, and **0/80** equal to any single draw.
The draws are genuinely distinct (mean |draw42 − draw43| = 1.20–2.29 DN on the first five
C2 chips) — test-time dropout is active, as standing practice 2 assumes.

**Chip roster confirmed.** `B2_stems.txt` is **set-identical** to
`packageA-urban-chips.csv` filtered to `site == ankara AND urban == 1` (n = 20 of 46
urban; the 26 EU urban chips are excluded, as registered). No EU chip entered: every stem
carries the `ank_` prefix.

**"Overlapping renders bitwise identical to task3's" — CONFIRMED, and it rests on 2
chips, not 20.** Only two of the 20 B2 stems exist in `tool_runs/task3/renders/`
(`ank_33_34`, `ank_38_22`); for both, the B2 post-fix Geofabrik render is **pixel-identical
and grid-identical** (transform and CRS equal) to the task3 render. The task3 renders do
still exist (30 files). The claim is true as far as it goes; the audit records its
support size because the results sentence ("Production render path shown
extent-invariant") reads as broader than a 2-chip check.

**Reference invariance confirmed.** The 20 BT.601 reference grays B2 scored against are
**byte-identical** to Package A's `pkgA/gray/ref_ank/bt601/` (20/20), and the RGB
references are the same files (`ankara/run/ref/<stem>_warp.tif`). The registered
invariance "same references as the Package A urban rows" holds.

### B3 part 1 — PASS, all cells

Recomputed from `B3/B3_scores.csv` (930 rows = 4 sets × arms × chips; columns
`orb, orb_inl, akaze, mi`).

- **All 34 per-arm means and SEs** in `B3_summary.json` reproduce to 5e-4, and every
  `n_matched` count matches the raw non-null count exactly.
- **All 12 arm rankings** reproduce.
- **All 9 computable Δ cells reproduce once the formula is identified as a *paired*
  difference on the intersection subset** (chips where *both* compared arms matched),
  not a difference of independent means: ORB ank130 **−0.6127 ± 0.1354**, AKAZE ank130
  **−0.1483 ± 0.0484**, MI ank130 **−1.2600 ± 0.2613**; eu150 ORB −0.4107 ± 0.1739,
  AKAZE −0.5389 ± 0.4744, MI −1.4956 ± 0.2744. All match the reported −0.613 ± 0.135,
  −0.148 ± 0.048, −1.260 ± 0.261 and the eu150 direction.
- **Matched-subset counts** ORB ank130 C2 **53**/130, C1 **34**, pretrained **15** —
  exactly as reported. Matchability does rank C2 first in every ORB and AKAZE cell on
  ank130 and eu150.
- **eu150 direction:** C2 first under all three matchers. Correct.
- **ank30 cells** exist for both sources and all four arms and are reported without
  verdict, as stated.

Three precision notes on the surrounding prose are in §C (m1–m3); they do not change a
number.

### B3 part 2 (mediation) — the reported statistic is an algebraic identity

`B3_summary.json` reports ank130 raw −0.702 ± 0.062 → `cond_both` −0.702 ± 0.060,
`lost_pct` 0; eu150 raw −0.434 ± 0.046 → −0.434 ± 0.044, `lost_pct` 0.

**The raw halves reproduce exactly** from `pkgA/pkgA_scores.csv` (band = bt601,
matcher = klt): ank130 **−0.7023 ± 0.0622** (n = 130), eu150 **−0.4337 ± 0.0461**
(n = 150).

**The conditional halves were reconstructed** by recomputing the registered covariates
from the surviving grays (photometric similarity = Pearson r of the arm's BT.601 gray vs
the reference gray; gradient similarity = Pearson r of their Sobel magnitudes; covariate
= the C2 − C1 difference of each) and fitting the registered OLS
`y ~ 1 + Δphoto + Δgrad`. The reconstruction identifies the reported statistic exactly:

| set | statistic | value |
|---|---|---|
| ank130 | raw mean | −0.7023 ± 0.0622 |
| ank130 | **OLS fitted value at the covariate means** (= reported `cond_both`) | **−0.7023 ± 0.0605** |
| ank130 | OLS intercept, i.e. the gap at Δsimilarity = 0 | **−0.3948 ± 0.1239** (t = −3.19) |
| eu150 | raw mean | −0.4337 ± 0.0461 |
| eu150 | **OLS fitted value at the covariate means** (= reported `cond_both`) | **−0.4337 ± 0.0436** |
| eu150 | OLS intercept, i.e. the gap at Δsimilarity = 0 | **−0.1056 ± 0.0877** (t = −1.20) |

Both reported means and both reported SEs are recovered to three decimals, which fixes
the model beyond reasonable doubt.

**The finding: an OLS fitted value evaluated at the covariate means is algebraically
equal to the raw mean, for any covariates whatsoever.** "Loses **0%** of its magnitude"
is therefore a property of the estimator, not a measurement — the test as executed cannot
return any other number, and cannot detect mediation of any size. The contemporaneous log
shows the same 0% for the photometric-only, gradient-only and both-covariate variants
(obs 288), which is the signature of the identity rather than three agreeing results.

The mediation-capable reading of the *same* fit — the gap that survives at zero
similarity difference — attenuates substantially: **ank130 loses 43.8%** of its magnitude
and stays significant at α = 0.01 (t = −3.19); **eu150 loses 75.6%** and **loses
significance** (t = −1.20, p ≈ 0.23). The gradient-similarity slope carries it
(−1.92 ank130, −2.09 eu150); photometric similarity is inert (+0.36, +0.003).

Scored against the registered definition of "fully mediated" (≥ 80% magnitude loss **AND**
loss of significance at α = 0.01, jointly), **neither set triggers** — so the registered
withdrawal condition still does not fire on this leg. But the registration's own fallback
applies: "Partial mediation … = reported as measured, **wording narrowed
proportionally**", and eu150 at 76% attenuation with significance lost is exactly that.
The reported sentence "**the 'trained-on-the-metric' explanation receives no support**"
is not supported by the artifact and must be withdrawn. → **corrections-log entry 20**.

*Provenance of this recomputation:* the covariate values are **not** preserved anywhere
(see §C, C-4); they were recomputed by this audit from `pkgA/gray/**` at
2026-08-24. Path: deterministic (no inference; a fixed function of archived grays).

### B3 part 3 (restraint) — scalars confirmed as medians; distribution supplied

The three reported scalars (pretrained 1.016, C1 1.023, C2 0.218) **are medians**:
`B3_summary.json` stores `median` alongside `q25`, `q75` and `frac_gt_1_5`, and the
reported values are the `median` fields verbatim. Confirmed independently by the later
one-pass recompute in [phase-c-lpips-results.md](phase-c-lpips-results.md)
(`C45/C45_edge_ratio.csv`), whose C2 median is 0.2177 against a C2 **mean** of 0.2839 —
only the median matches the committed 0.218.

The registered read-out was "the per-arm ratio **distribution**". It exists in the
artifact only at quartile resolution, because **no per-chip file was written for part 3**
(§C, C-4). Both layers are given here.

Distribution as stored by the B3 run (n = 130):

| arm | q25 | median | q75 | frac > 1.5 |
|---|---|---|---|---|
| pretrained | 0.934 | **1.016** | 1.098 | 0.000 |
| C1 | 0.958 | **1.023** | 1.130 | 0.010 |
| C2 | 0.129 | **0.218** | 0.384 | 0.000 |

Full distribution from the later one-pass recompute (`C45_edge_ratio.csv`, n = 130 —
same definition, mask taken from the warped input PNG rather than the B3 run's mask
source, which is why the C1 median moves by 0.023):

| arm | min | p10 | q25 | median | q75 | p90 | max | mean ± sd | frac < 0.5 |
|---|---|---|---|---|---|---|---|---|---|
| pretrained | 0.374 | 0.801 | 0.943 | 1.020 | 1.121 | 1.235 | 1.527 | 1.021 ± 0.195 | 0.023 |
| C1 | 0.842 | 0.922 | 0.959 | 1.046 | 1.174 | 1.330 | 2.105 | 1.096 ± 0.193 | 0.000 |
| C2 | 0.029 | 0.072 | 0.120 | 0.218 | 0.382 | 0.617 | 1.154 | 0.284 ± 0.222 | **0.846** |

The distribution is more favourable to the reported reading than the median alone: C2's
ratio is below 0.5 on **84.6%** of chips and never exceeds 1.154, while C1's is below
0.842 on none. The reported conclusion stands; only its evidentiary form was incomplete.

## C. Registered protocol vs what ran

| registered | ran | status |
|---|---|---|
| **B2** — 20 Ankara urban chips from `packageA-urban-chips.csv`, EU-26 excluded | set-identical, 20/20; no EU chip | ✓ |
| B2 — inputs rendered from post-fix Geofabrik, `-s smart` extract, CLC+ base | `B2_render.py` → `o2r.make_chip(..., pbf=extent.osm.pbf, base_product="clcplus")`; extract `extent.osm.pbf` 17.5 MB | ✓ |
| B2 — all four arms | pretrained, C1, C2, C3 present, 20 chips each | ✓ |
| B2 — K = 8 seeded draws, seeds 42…49, mean-of-8 estimator | 8 seed dirs per arm, 640 fakes; 80/80 mean8 files reproduce as `round(mean(8))`; per-seed `sitecustomize.py` sets `random/numpy/torch` seeds | ✓ |
| **B2 — "score RGB KLT and BT.601-gray KLT"** | **both ran (240 KARIOS runs); the results document reports BT.601 only and does not say the RGB half is missing from it** | **✗ — deviation, entry 19** |
| B2 — report value ± SE, plus paired C2−pretrained and C2−C1 | present, both bands, in the artifact | ✓ |
| B2 — restatement criterion 0.15 px, direction-blind | encoded in `B2_score.py` (`BAND_PX = 0.15`, verdict string both ways); not fired at 0.0017 px | ✓ |
| B2 — invariance: same references, warp, KARIOS config as Package A urban rows | ref grays byte-identical to pkgA 20/20; warp target grid asserted equal to the ref grid per chip; KARIOS config identical (below) | ✓ |
| **B3 — sets: ank130 pre/C1/C2, eu150 C1/C2, ank30 both sources × 4 arms** | exactly these 13 arm-set combinations, 930 rows; stems set-identical to the pkgA grays for all four sets | ✓ |
| B3 — ORB nfeatures 2000 | **not verifiable from any artifact** (harness deleted); contemporaneous log obs 268 records "ORB+RANSAC (2000 features, 3px threshold)" | ⚠ log only |
| B3 — BFMatcher Hamming, cross-check | **not verifiable from any artifact and not recorded in the log** | ⚠ unverifiable |
| B3 — `estimateAffinePartial2D` threshold 3 px | **not verifiable from any artifact**; obs 268 records "3px threshold" | ⚠ log only |
| B3 — statistic = median displacement magnitude of RANSAC inliers | obs 268 records "median displacement for ORB/AKAZE"; consistent with the data (`orb_inl` integral, present iff `orb` present) | ⚠ log + consistency |
| B3 — < 10 inliers ⇒ unmatched, counted separately | **consistent with the data**: 234 ORB rows, `min(orb_inl) = 10`, zero rows below 10, zero rows with a count but no score | ✓ (by data) |
| B3 — MI grid search ± 8 px | **confirmed from the data**: max MI = 11.3137 = hypot(8, 8) exactly; no value beyond the grid | ✓ (by data) |
| B3 — MI 64-bin joint histogram | **not verifiable from any artifact and not recorded in the log** | ⚠ unverifiable |
| **B3 — MI parabola subpixel refinement** | **all 930/930 MI values lie exactly on the integer pixel lattice (every value equals hypot(i, j) for integers i, j ∈ [−8, 8] to 1e-7). No subpixel refinement was applied.** | **✗ — deviation, entry 21** |
| B3 part 2 — conditioning model (partial correlation / OLS on the similarity difference) | OLS with both covariates, as registered — **but the reported conditional statistic is the fitted value at the covariate means, which is identically the raw mean** | **✗ — deviation, entry 20** |
| B3 part 2 — "fully mediated" = ≥ 80% magnitude loss AND α = 0.01 significance loss | criterion evaluated against a statistic that cannot move; on the mediation-capable statistic neither set meets it jointly (44% / 76%) | see entry 20 |
| **B3 part 3 — per-arm ratio distribution, Ankara-130** | computed for n = 130 and stored at quartile resolution; **three medians carried into the results document** | **✗ — minor, entry 19 scope** |
| **B2/B3 — run harness preserved** | **`B3/B3_run.py` no longer exists** (obs 268 names it); no per-chip artifact for B3 parts 2 or 3. B2's `_infer/_karios/_mean_warp` scripts were **overwritten in place on 2026-08-24** by the C4/C5 package | **✗ — deviation, entry 22** |
| KARIOS config identity across B2 arms and bands | **234 per-run config copies under `B2/karios/**`, all one sha256 `8eaa5bd8…`, equal to `configs/karios_gencp.json`** (`matching_winsize` 15) | ✓ |
| KARIOS config identity across B3 matcher cells | B3 part 1 does not invoke KARIOS; its inputs are the pkgA warps, whose **1,671 per-run configs are all the same sha256 `8eaa5bd8…`** | ✓ |
| (cross-check) B1 KARIOS config identity | **1,185 per-run configs, all `8eaa5bd8…`** | ✓ |

### C-1 (load-bearing) — the RGB half ran; it was not reported

**RGB artifacts exist.** 20 KARIOS runs per arm under `B2/karios/rgb/`, written
12:01:00–12:01:45 alongside the BT.601 half, and the full RGB table sits in
`B2_summary.json`. This is therefore **an undisclosed reporting omission, not a
non-execution** — it is *not* the entry-17 pattern. The registered protocol was executed
in full; the results document narrowed to one conversion without saying so.

The RGB table, recomputed here from raw (all 8 arm-cells and 4 paired cells reproduce to
5e-4):

| arm | RGB mean ± SE (px) | RGB median-of-medians | RGB pts median | BT.601 mean ± SE (px) |
|---|---|---|---|---|
| pretrained | 1.6314 ± 0.2103 | 1.2669 | 78.5 | 1.3698 ± 0.1612 |
| C1 | 0.8610 ± 0.1205 | 0.6369 | 136.5 | 0.7640 ± 0.0712 |
| **C2** | **0.6030 ± 0.0376** | 0.5394 | 204.0 | **0.5927 ± 0.0409** |
| C3 | 0.6372 ± 0.0377 | 0.5861 | 181.5 | 0.6109 ± 0.0375 |

| paired | RGB | BT.601 |
|---|---|---|
| C2 − pretrained | −1.0284 ± 0.1876 (t = −5.48, 20/20) | −0.7771 ± 0.1247 (t = −6.23, 20/20) |
| C2 − C1 | −0.2580 ± 0.0901 (t = −2.86, 18/20) | −0.1713 ± 0.0420 (t = −4.08, 19/20) |

Zero-point chips: 0 in every arm and both bands.

**Consequences, stated in both directions.** The RGB half *strengthens* every reported
comparison (C2's margin over pretrained widens from −0.777 to −1.028 px; over C1 from
−0.171 to −0.258 px) and preserves the reported ordering C2 > C3 > C1 > pretrained — so
the omission runs *against* our own claims, which under the corrections-log test permits
the record to be corrected rather than the run. The restatement criterion is unaffected:
on RGB, |0.6030 − 0.591| = 0.012 px, also inside the 0.15 band. And the criterion was
correctly evaluated on BT.601, which is the conversion the quoted 0.591 px was measured
under — the registered comparison is like-for-like. **B2 remains quotable as registered;
what changes is that the RGB half must now appear.** → **corrections-log entry 19**.

### C-2 (minor) — B3 part 3 scalars are medians; the distribution is now supplied

Confirmed (above, §B): the three reported values are the `median` fields of
`B3_summary.json`. The registered read-out — the per-arm ratio distribution — is supplied
in §B in both available forms. Folded into entry 19 as the same class of finding: a
registered reporting *form* narrowed at writing time without saying so.

### C-3 (minor precision items, disclosed here, no number changes)

- **m1 — the descriptor Δ values rest on the intersection, not the matched subsets
  quoted beside them.** headline-results.md prints "ORB Δ(C2−C1) −0.613 ± 0.135" and, two
  clauses later, "ORB ank130: C2 53/130, C1 34, pretrained 15". The Δ is a paired
  difference over the **29** chips where both C2 and C1 matched; AKAZE ank130 Δ rests on
  **11** paired chips and eu150 AKAZE on **3**. The formula is defensible (pairing is the
  right choice) but a reader will read 53 as the support for −0.613. Wording should carry
  the paired n.
- **m2 — "No flip at ≥ 2 SE anywhere" is one word too strong.** Sweeping all 25
  computable C2-vs-other paired cells finds exactly one nominal flip at ≥ 2 SE:
  `ank30_ovp` AKAZE, C2 − C3 = +0.156 ± 0.010 (t = +16.2) on **n = 2 paired chips**. It
  sits inside the cells the same paragraph already excludes from verdicts, so nothing
  substantive turns on it — but "anywhere" should read "in any verdict-bearing cell".
  (`ank30_prod` ORB also ranks C2 last, at t = +0.95 on n = 4 — directional, not
  significant.)
- **m3 — "the ank30 descriptor cells are unmatched-dominated (n ≤ 8)"** is true of
  `ank30_prod` (max n = 8, C2 ORB) but not of `ank30_ovp`, where ORB matches 14 chips for
  C2 and 12 for C3. The "reported without verdict" treatment is unaffected.
- **m4 — MI is censored at the search bound, in the conservative direction.** 147/930 MI
  values (15.8%) sit at radius ≥ 8 px and 39 are pegged exactly at the corner
  hypot(8, 8); the censoring is heavier for the worse arms (ank130: pretrained 27.7% at
  ≥ 8 px, C1 17.7%, C2 8.5%), so it **compresses** the reported MI margins toward zero.
  The reported −1.260 ± 0.261 is a lower bound on the true MI margin, not an inflated
  one. Disclosed, not corrected.
- **m5 — 3 of 160 B2 KARIOS runs have no config copy** (`bt601/pretrained` on
  `ank_25_37`, `ank_28_37`, `ank_38_24`) — a report-writing race under 8 concurrent
  workers. All 160 KLT CSVs are present and all 160 runs used the same config by
  construction (`B2_karios.py` passes one `CONF` constant). Evidence-layer note only.

### C-4 — what could not be checked, and what would have preserved it

Three checks in the task specification **cannot be run**, and no weaker substitute is
offered in their place:

1. **ORB `nfeatures = 2000`, BFMatcher Hamming with cross-check, and the 64-bin MI joint
   histogram cannot be verified against any configuration**, because `B3/B3_run.py` —
   named in the contemporaneous log as the script that produced every B3 number — no
   longer exists, and B3 wrote no config JSON beside its outputs. Two of the three are
   attested only by the observation log's summary of the script at launch time; the
   Hamming cross-check and the bin count are attested nowhere. What would have preserved
   them: committing the harness to git beside the results, which is exactly the practice
   the C4/C5 package adopted two days later ("harness preserved in git", commit `40cde9b`)
   after corrections-log entry 16's lesson — and which B3 predates.
2. **B3 part 2's covariates and part 3's per-chip ratios have no artifact at all.** Part 2
   was reconstructed here from surviving grays and matched the reported scalars to three
   decimals, which is strong but is a reconstruction, not the original. Part 3's per-chip
   distribution is unrecoverable at the original mask definition; the C45 recompute is a
   different mask source and reproduces C2's median to 0.0003 but C1's only to 0.023.
   What would have preserved them: a per-chip CSV per part, the same convention B2 and
   B1 followed in the same session.
3. **B2's as-run inference, mean/warp and KARIOS scripts are unrecoverable byte-for-byte**
   — `B2_infer.sh`, `B2_karios.py`, `B2_mean_warp.py` were **overwritten in place at
   2026-08-24 02:52–02:53** by the C4/C5 package, which extended their arm lists. This is
   the corrections-log entry 10 pattern (a tool writing into a directory holding untracked
   originals) recurring. Consequence is bounded: the *scoring* script that produced the
   reported table (`B2_score.py`, mtime 2026-08-21 12:02:10) is untouched, the Aug-21
   outputs are untouched, and every reported number was reproduced in this audit directly
   from the raw KARIOS CSVs without using the mutated scripts. What would have preserved
   it: copying the harness aside — or committing it — before extending it.

→ items 1 and 2 are **corrections-log entry 22**; item 3 is folded into the same entry as
the same class.

## D. Evidence layer

`tubitak/data/*` is gitignored, so mtimes and raw outputs live outside version control.
Pinned here (sha256, 2026-08-24):

```
335b077be011204af77688291bcc7abbcec771a6b9f0ae890acafb1c8ee1dbad  B2/B2_per_chip.csv
4b76f4df19bad95aa90fa276b2b214bd731f8da888791bcf0f2eaf3d0a2da444  B2/B2_summary.json
c7d4c71d4a5d7715fabe16cb15605891364952cf9b84d11fecc7f5bc1441c6f0  B3/B3_scores.csv
d33f56d382b77624137c7d9a5289d7084fde181ec1f988511ea6b0f11d3b0416  B3/B3_summary.json
2d8cf4b0794c4cdaa14fb7651a4e0152f3c3a9fb066aff5bf5556f8112f2553a  pkgA/pkgA_scores.csv
38a18a87a385959291f2d8834762b17c5b31d066c3704a6c993eb024da0e61a3  B2/_scripts/B2_score.py
ea0bf1e34ea9e21647277bddbb2b04673631839e7354e64db0ffbbb6be58b1a2  B2/_scripts/B2_render.py
3da1db04acb5b8d2937705dad273cabd85608bb7c23bfa364f5147f686991361  B2/_scripts/B2_stems.txt
a3a0fc237935992c50da34e5ddabd13ba3c8bd868bdbf8598bcf89aa21e7fd00  B2/_scripts/B2_origins.csv
b8f035cd766a7c7099967defd4b85301e4410d028abf6af0c7b09172e2a6a7f3  B2/extent.osm.pbf
8eaa5bd8cdae066d2580a4105169262f873523cadf0b450a8aa134a31ed4ca84  configs/karios_gencp.json
0a7525a9082079a74cf4af6e044a02c01eeda278f77cb544d8c8cc488f238a59  C45/C45_edge_ratio.csv
f1e303305a00998b9ceddfa40aadfa39d3a937651716f42e57cd1d6c68caf7b7  docs/packageA-urban-chips.csv
```

`8eaa5bd8…` is the single KARIOS configuration hash shared by **all** 234 B2, 1,185 B1
and 1,671 pkgA per-run copies and by the committed master config — the config-identity
invariance, pinned as one number.

Observation-log records cited in §A (claude-mem `content_hash`, database outside version
control, same source as [E3-session-log-excerpt.md](E3-session-log-excerpt.md)):
obs 259 `159a490c15f6dcff`, 262 `a59f615d89452b77`, 263 `258e2d429155c0c1`,
264 `4a31360120837165`, 268 `2b8bb052d35e90ce`, 277 `86940fef94f44643`,
286 `feb9cf0c770c7b1e`, 288 `a16ecdd868d0fa5a`, 289 `c4ad0dbcfcb5b253`.

Off-machine copy: the Kaggle evidence backup
([evidence-backup-manifest.txt](evidence-backup-manifest.txt)) — note that it predates B2
and B3 and contains **neither** package's outputs.

## Verdict

**Per leg:**

- **A. Timeline — PASS.** The claim "registered before any number exists" is literally
  true for B2 and B3. Zero files of any kind exist in either package before the
  registration commit; the only pre-registration artifacts anywhere in the headline
  package are ten B1 generator checkpoints, which are inputs. The 26-minute window is
  fully reconstructed from mtimes and a contemporaneous observation log that supports the
  claim rather than falsifying it. **This is not E3 repeating.**
- **B. Tables vs raw — PASS on everything that has raw data.** B2: 320/320 per-chip cells
  and 64/64 summary cells reproduce exactly, mean-of-8 and seeds 42–49 confirmed, chip
  roster confirmed, references byte-identical to Package A. B3 part 1: every mean, SE,
  count, rank and Δ reproduces. B3 parts 2 and 3: the raw halves reproduce; the
  conditional half reproduces only under a reconstruction, and reproducing it is what
  exposed the deviation below.
- **C. Registered vs ran — FAIL on four items.** Entries 19–22 below.

**Deviations:**

| # | what | class | consequence |
|---|---|---|---|
| 19 | B2's registered RGB half ran but was not reported; B3 part 3's registered distribution reduced to three medians | undisclosed reporting omission | numbers unaffected and RGB is *more* favourable; both now published in §B/§C-1 |
| 20 | B3 part 2's conditional statistic is the OLS fitted value at the covariate means — algebraically the raw mean; "loses 0% of its magnitude" cannot be false | registered test executed with an inert statistic | **the sentence "the 'trained-on-the-metric' explanation receives no support" is withdrawn.** On the mediation-capable statistic: ank130 −44%, still significant; eu150 −76%, **significance lost**. Registered "fully mediated" still not met jointly, so "matcher-independent" is not withdrawn — but the registration's own "narrow the wording proportionally" rule now applies |
| 21 | MI parabola subpixel refinement registered, never applied (930/930 values on the integer lattice) | registered element not run — entry-17 class | MI is an integer-pixel statistic, additionally censored at ±8 px on 15.8% of chips in the conservative direction. Its rank agreement with ORB/AKAZE survives; its magnitudes are coarse and should be quoted as such |
| 22 | `B3_run.py` and all B3 part-2/part-3 per-chip artifacts absent; B2's inference/warp/KARIOS scripts overwritten 2026-08-24 | evidence not preserved | four registered B3 parameters unverifiable from artifacts (two attested only by the session log, two attested nowhere); B2's numbers survive because they were reproduced from raw KARIOS output without the mutated scripts |

**What B2 and B3 are quotable as.** B2 is quotable as **registered and executed in full**,
with entry 19's disclosure — the 0.593 px production-path headline reproduces from raw
data on both band conversions and the restatement criterion was applied correctly.
B3 part 1 is quotable as registered, with the paired-n and MI-coarseness caveats
(m1, entry 21). **B3 part 2 is not quotable in its current form**: its reported result is
an identity, and the honest statement of what the data show is partial mediation on
ank130 and substantial, significance-destroying mediation on eu150. B3 part 3 is
quotable, now with its distribution.

The manuscript wording rule is unchanged and is further evidenced, not weakened:
*"Experiments were pre-registered where stated; deviations from the registered protocol
are documented in a public corrections log."* The audited base rate moves to **2 clean
timelines / 1 falsified timeline (E3) / 3 registrations with disclosed protocol
deviations (T1, B2, B3)**.

Next in [paper-roadmap.md](paper-roadmap.md) item 1: `phase-c-registration`,
`phase-c-europe-registration`, `phase-d-checks-registration`, `packageA-registration`,
the four `tool-*registration` files, T3.
