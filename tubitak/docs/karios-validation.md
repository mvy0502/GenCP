# KARIOS validation of the GenCP geometry findings

**Status:** instrument validated, arms built, predictions registered. Results below the
pre-registration line.
**KARIOS:** v2.2.0-dev, commit `e61d312eac996f22e4b3eaa69dddde08138aeccf` (2026-07-03), installed in
its own `karios` conda environment (Python 3.12, GDAL 3.8, OpenCV 4.8) — the `gencp` environment
was left untouched.
**Companions:** [`geometry-finding.md`](geometry-finding.md) ·
[`train-test-scale-mismatch.md`](train-test-scale-mismatch.md) ·
[`hallucinated-structure.md`](hallucinated-structure.md)

---

## 1. Instrument validation

Before anything else, KARIOS was run on two cases with a known answer.

| test | expectation | result |
|---|---|---|
| image vs **itself** | 0 | **dx = dy = 0.000000**, std 0, 339 points |
| image vs copy shifted by exactly (dy=+5, dx=+3) px | (5, 3) | **dy = +5.0000 ± 0.0014, dx = +2.9999 ± 0.0014** (197 interior points) |

The shifted case used a circular roll, so points within ~20 px of the wrap seam are invalid by
construction; the interior figures above exclude them. Including them the means are unchanged
(dy +5.0003, dx +2.9982) with a wider spread, as expected.

**KARIOS is being driven correctly.**

Two behaviours worth recording:

* **Sign convention.** The per-point CSV reports `dx`/`dy` in image pixel coordinates (dy positive
  = increasing row). The `correl_res.txt` summary negates y (`mean_y = -4.9990` for the same run),
  i.e. it reports in a map convention with y up. Both were checked against the known shift.
* **`outliers_filtering: true` discards everything on a degenerate input.** On the
  image-vs-itself case with the GenCP config it reported `NbPoints(init/final): 2405 / 0` — with
  zero variance, the statistical outlier test rejects every point. Harmless on real data (the
  shifted case kept 1247 points) but it means surviving-point count is not a pure quality measure
  at the noise-free limit.

### Configuration

The GenCP README's published KARIOS settings, translated to the KARIOS 2.2 schema
(`tubitak/configs/karios_gencp.json`):

| parameter | value | source |
|---|---|---|
| `minDistance` | 1 | GenCP README |
| `blocksize` | 5 | GenCP README |
| `matching_winsize` | 15 | GenCP README |
| `qualityLevel` | **0.1** | GenCP README (`quality_level`) |
| `laplacian_kernel_size` | 7 | GenCP README |
| `tile_size` | 4000 | GenCP README |
| `outliers_filtering` | **true** | GenCP README |
| `confidence_threshold` | 0.8 | GenCP README ("Confidence value: 0.8") |
| `maxCorners` | 20000 | **deviation** — README says 0; KARIOS 2.2 defaults to 20000 and 0 is not a documented "unlimited" in this version |

KARIOS 2.2's own defaults differ (`minDistance` 10, `blocksize` 15, `matching_winsize` 25,
`outliers_filtering` **false**, `confidence_threshold` 0.4) and were used only for the first
validation run above.

---

## 2. Method: why the arms must be warped

**KARIOS requires the monitored and reference rasters to have identical pixel dimensions.** Feeding
a 256 px chip against a 257 px reference fails outright:

```
Error during processing: Monitored image geo info not compatible with reference image:
        X Size: 256 / Y Size: 256
        X Size: 257 / Y Size: 257
```

It matches on the shared pixel grid and uses the transform only to convert results to metres. Fed
directly, **arms A and B would return identical shift fields**, since they contain the same pixels
and differ only in declared pixel size — the georeferencing would never be exercised and the
experiment would be vacuous.

Each arm is therefore **reprojected onto a common ground grid using its own declared transform**,
which is what a real GCP workflow does when placing a chip on a target image's grid. A wrong
transform then displaces the content and KARIOS can see it.

| arm | pixels | declared transform | ground covered |
|---|---|---|---|
| **A** stock | generated 256 | origin O, **10.0 m** (copied verbatim from the 257 source) | claims 2560 m |
| **B** affine-corrected | *identical pixels to A* | origin O, **10.0390625 m** | 2570 m |
| **C** scale-matched | generated via 257→286 + centre-crop 256 | origin O + 134.79 m, **8.9860140 m** | central 2300.42 m |

Common grid: **228 × 228 at 10 m, inset 145 m** from the chip origin — strictly inside every arm's
footprint including arm C's, so no arm contributes nodata or is advantaged by edge padding.
Reference: the real satellite half, warped onto the same grid with the same kernel.

**Ground truth needs no download.** Each `image_pairs` chip is `[satellite | OSM]`, and the OSM half
corresponds to a georeferenced raster of the same name, whose CRS and transform the satellite half
inherits. Layout was verified per chip by two independent signals (correlation against the
georeferenced raster, and a flatness signature), not assumed: **566 of 568 chips, all
`[satellite | OSM]`, no mixed layouts**; 2 skipped as ambiguous and named in §5.

**Dataset note:** only 243 of the 566 OSM halves are byte-identical to their georeferenced raster;
the other 323 correspond but differ slightly (MAD ~2 DN, corr ~0.95), consistent with rendering
from different OSM snapshots. Geometry is unaffected — both depict the same named tile at 257×257
and 10 m — but it is recorded as a further dataset observation.

**Sample:** 90 chips spanning 37 MGRS tiles, drawn from the corpus test split with the 9 leaked
chips excluded.

---

## 3. PRE-REGISTRATION

**Registered at 2026-08-18 11:58:47 UTC, before any arm was run.**
Committed in this state; results appear only in §4, below this line.

### 3.1 Arm A vs arm B — the georeferencing scale error

Arm A declares 10.0 m for content whose true GSD is 10.0390625 m, so after warping its content is
compressed toward the chip origin by a factor 10/10.0390625 = 0.996109. Residual displacement
should therefore grow linearly with distance from the **NW chip origin**:

| position on the common grid | distance from chip origin | predicted residual |
|---|---|---|
| NW corner of grid | 145 m | 0.56 m (0.056 px) |
| grid centre | 1285 m | 5.00 m (0.500 px) per axis |
| SE corner of grid | 2425 m | 9.43 m (0.943 px) per axis |

**Predictions:**

* **P1** Arm A shows a systematic residual **ramp** growing NW→SE, with slope ≈ **0.0039 px per px**
  in both dx (vs column) and dy (vs row), reaching ~0.94 px at the SE corner.
* **P2** Arm A mean radial error ≈ **0.7 px (7 m)**, dominated by that ramp.
* **P3** Arm B shows **no ramp**: slope of residual against position statistically indistinguishable
  from zero.
* **P4** Arm B mean radial error **lower than arm A's**, by roughly the ramp contribution.
* **P5** Surviving point counts for A and B are **similar** — the pixels are identical, so corner
  detectability is essentially unchanged.

**Falsified if:** arm A shows no position-dependent ramp; or arm A's and arm B's slopes are
statistically indistinguishable; or arm B is *worse* than arm A. Any of these would mean either the
scale error is not real as characterised, or KARIOS cannot see it — and §12.4 of
`geometry-finding.md` (that the published ~7 m mean error is largely this defect) would be refuted.

### 3.2 Arm C — the training-matched scale

Arm C's transform is internally consistent, so it should be geometrically correct like arm B. The
open question is whether its extra high-frequency detail (HF energy ratio 0.72 → 0.86) helps
matching.

**Predictions:**

* **P6** Arm C shows **no ramp** (its transform is consistent).
* **P7** Arm C's surviving point count is **equal to or higher** than arm B's — more high-frequency
  detail gives KLT more corners.
* **P8** Arm C's mean error and RMSE are **not significantly better** than arm B's. The measured HF
  improvement was modest and did not move SSIM or RMSE, so I do not expect it to move a matching
  metric either.

**Falsified if:** arm C substantially outperforms arm B (say >30 % lower RMSE, or a large gain in
surviving points with lower error). That would mean the scale mismatch matters more than the
pixel-metric comparison suggested, and "does not by itself justify changing the inference path"
would be wrong.

### 3.3 Per-chip outcome vs OSM information content

The proxy measurement found Spearman rho of **−0.41 to −0.48** between the three OSM
information-content scores and a local match-failure rate. Arm B is used because it is
geometrically correct, so scale does not confound the result.

**Predictions:**

* **P9** Surviving point count correlates **positively** with all three OSM scores.
* **P10** Residual magnitude correlates **negatively** with all three OSM scores.
* **P11** |rho| lands in the **0.3–0.5** band, i.e. the proxy was measuring something real.

**Falsified if:** |rho| < 0.15 and not statistically significant. That would mean the proxy was
measuring its own noise, and **the chip-selection guidance in `hallucinated-structure.md` §7 must
be withdrawn**, not softened.

### 3.4 What I expect to be uncertain

Local matching between generated and real imagery was already measured as poor (56-84 % window
failure). If matching noise dominates, the arm A→B improvement may be partially masked even if the
ramp is clearly present in the surviving points. The **slope** test (P1/P3) is therefore the primary
discriminator, and the **mean error** comparison (P4) secondary.

---

## 4. RESULTS

**Run completed 2026-08-18 12:13:14 UTC.** 116 chips x 3 arms = 348 KARIOS runs, 25,574 surviving key points.
The pre-registration above was committed in `6a9c4e8` before any arm was run.

### 4.1 Arm comparison

| arm | chips | points | mean \|d\| (px) | mean \|d\| (m) | RMSE (px) | RMSE (m) | median dx | median dy |
|---|---|---|---|---|---|---|---|---|
| **A** stock | 116 | 8353 | 2.2274 | 22.27 | 2.7131 | 27.13 | −0.2462 | −0.4441 |
| **B** affine-corrected | 116 | 8500 | 2.0908 | 20.91 | 2.5958 | 25.96 | +0.1891 | +0.0024 |
| **C** scale-matched | 116 | 8721 | 2.0480 | 20.48 | 2.5809 | 25.81 | +0.2108 | +0.0394 |

Paired per-chip comparison (same 116 chips, median residual per chip):

| comparison | mean difference (px) | SE | t | chips improved |
|---|---|---|---|---|
| A → B | **−0.0992** | 0.0390 | **−2.54** | 75/116 |
| A → C | −0.0713 | 0.0513 | −1.39 | 71/116 |
| B → C | +0.0279 | 0.0475 | +0.59 | 61/116 |

### 4.2 The primary test — residual slope against position

Predicted slope for an uncorrected arm: **+0.003891 px per px**.

| arm | dx vs column | dy vs row | significance |
|---|---|---|---|
| **A** | **−0.003276 ± 0.000330** | **−0.002208 ± 0.000328** | 9.9σ, 6.7σ |
| **B** | −0.001067 ± 0.000321 | +0.000260 ± 0.000312 | 3.3σ, 0.8σ |
| **C** | +0.000326 ± 0.000313 | +0.000312 ± 0.000303 | 1.0σ, 1.0σ |

Figure: [`figures/karios-residuals.png`](figures/karios-residuals.png). Arm A shows a visibly
coherent field with residuals reaching 14 m; arm B's field is incoherent and reaches 7.5 m.

### 4.3 Scorecard against the pre-registration

| # | prediction | outcome | evidence |
|---|---|---|---|
| **P1** | Arm A shows a ramp, slope ≈ 0.0039 px/px | **CONFIRMED** | 9.9σ (dx), 6.7σ (dy); dx magnitude 0.00328 = 84 % of predicted, dy 0.00221 = 57 % |
| **P2** | Arm A mean radial ≈ 0.7 px (7 m) | **FALSIFIED** | actual 2.23 px (22.3 m), 3x larger |
| **P3** | Arm B shows no ramp | **PARTLY CONFIRMED** | dy fully corrected (6.7σ → 0.8σ); dx reduced 67 % but a 3.3σ residual slope remains |
| **P4** | Arm B mean error < arm A | **CONFIRMED** | 2.091 vs 2.227 px; paired t = −2.54, 75/116 chips improved |
| **P5** | A and B have similar point counts | **CONFIRMED** | 8353 vs 8500; +1.3 ± 1.0 per chip, not significant |
| **P6** | Arm C shows no ramp | **CONFIRMED** (strongest) | 1.0σ in both axes — the cleanest arm geometrically |
| **P7** | Arm C point count ≥ arm B | **CONFIRMED** (weakly) | +1.9 ± 1.3 per chip |
| **P8** | Arm C not significantly better than B | **CONFIRMED** | paired B→C t = +0.59, i.e. C is if anything marginally *worse* in median residual; far below the 30 % falsification threshold |
| **P9** | rho(points, OSM info) > 0 | **CONFIRMED** | +0.675, +0.485, +0.665 |
| **P10** | rho(residual, OSM info) < 0 | **CONFIRMED** | −0.794, −0.588, −0.705 |
| **P11** | \|rho\| in the 0.3-0.5 band | **EXCEEDED** | actual 0.485-0.794 — the effect is *stronger* than predicted, not weaker |

### 4.4 Per-chip outcome vs OSM information content (arm B, n = 116)

| OSM score | rho vs surviving points | rho vs median residual |
|---|---|---|
| edge density | **+0.675** | **−0.794** |
| class count | +0.485 | −0.588 |
| non-dominant fraction | +0.665 | −0.705 |

**The proxy did not disappear — it strengthened.** The proxy metric in
[`hallucinated-structure.md`](hallucinated-structure.md) gave rho = −0.41 to −0.48; the real
instrument gives **−0.59 to −0.79** against residual magnitude and **+0.49 to +0.68** against
surviving point count. Measured on the geometrically correct arm, so scale is not confounding it.

**The chip-selection guidance stands and is strengthened.** Edge density is now the strongest single
predictor (rho = −0.794 against residual), displacing non-dominant fraction.

---

## 5. What this changes

### 5.1 The scale error is real and visible to the instrument — but it is not the dominant error

The ramp is unambiguous: **9.9σ in arm A, and it is removed by correcting the affine**. That is the
scale finding confirmed by an independent tool, and arm A's residual field is visibly coherent
where arm B's is not.

But **P2 was falsified and that matters more than P1 being confirmed.** Absolute errors are ~2.2 px
(22 m), roughly 3x what the scale error alone predicts, so **matching noise dominates**. Correcting
the affine improves mean error by only **6.1 %** (0.137 px). Errors add in quadrature: against a
~2.1 px noise floor, removing a ~0.5 px systematic contributes very little.

**This refutes the hypothesis in [`geometry-finding.md`](geometry-finding.md) §12.4** that the
published ~7 m mean error is largely the georeferencing defect. Our arm A RMSE (27.1 m) is close to
upstream's reported 24 m, but our mean radial (22.3 m) is far above their reported 7 m, and
correcting the scale moves our number by only 1.4 m. Either their "mean error" is a different
statistic from mean radial, or their matching is substantially cleaner than ours. §12.4 should be
read as **not supported by this run**.

### 5.2 Arm C is geometrically the cleanest, but no better at matching

Arm C is the only arm whose residual slope is consistent with zero in **both** axes (1.0σ, 1.0σ),
better even than arm B. Yet its matching performance is statistically indistinguishable from arm B
(paired t = +0.59, marginally worse in median). This is exactly P8, and it is consistent with the
pixel-metric finding: the training-matched scale recovers detail but does not make outputs match
reality better. **The scale-mismatch decision remains "not worth changing the inference path"**, now
on a task-based metric rather than a proxy.

### 5.3 Chip selection is the highest-value lever

With rho up to −0.79 between OSM edge density and residual magnitude, **input information content
predicts match quality far more strongly than any of the geometry corrections do**. Correcting the
affine buys 6 %; choosing well-covered sites moves residuals across a much wider range. For Turkish
site selection this reorders the priorities: site choice first, affine correction second, inference
scale not at all.

### 5.4 Unexplained: arm B's residual dx slope

Arm B retains a −0.00107 ± 0.00032 px/px slope in dx (3.3σ) after correction, while dy is fully
corrected and arm C is clean in both axes. Candidate explanations, none tested: a sub-pixel bias in
the warp resampling; imperfect co-registration between the satellite and OSM halves of the corpus
pairs themselves; or an artefact of the common-grid inset. It is a third of the uncorrected slope
and does not affect the conclusions, but it is not understood and is recorded rather than smoothed
over.

---

## 6. Limitations

1. **116 chips, 228x228 px each.** KARIOS is designed for large scenes; these are small crops, which
   limits the number of key points per chip (median 70) and inflates per-chip variance.
2. **Warping resamples.** Every arm passes through one bilinear reprojection onto the common grid.
   All arms are treated identically, but the noise floor is raised for all of them.
3. **Generated-vs-real matching is intrinsically hard**, as established independently: the generator
   synthesises plausible rather than actual scenes. The ~2 px noise floor is a property of the task,
   not of KARIOS.
4. **Not upstream's test site or chip set**, so the comparison with their published figures in §5.1
   is indicative only.
5. **`maxCorners` deviates** from the published config (20000 vs 0) as recorded in §1.
6. **One config only.** No sensitivity analysis over `qualityLevel`, `matching_winsize` or
   `outliers_filtering`.

---

## 7. Reproducing

```bash
# ground truth (gencp env)
conda activate gencp
python tubitak/scripts/build_reference_set.py --out tubitak/data/karios/reference
python tubitak/scripts/build_karios_arms.py \
    --gen-a tubitak/data/karios/gen/out_a/genCP_HR_RGB_model/test_latest/images \
    --gen-c tubitak/data/karios/gen/out_b/genCP_HR_RGB_model/test_latest/images

# the runs (karios env)
conda activate karios
python tubitak/scripts/run_karios_arms.py --arms A B C

# analysis (gencp env)
conda activate gencp
python tubitak/scripts/analyse_karios.py --figure tubitak/docs/figures/karios-residuals.png
```

All imagery and results live under `tubitak/data/`, which is gitignored.
KARIOS itself is installed at `~/tools/karios` outside this repository.

---

## 8. Statistic reconciliation — did we compare the wrong quantity?

### 8.1 Q1: what `mean_x`/`mean_y` actually are (read from source)

From `karios/accuracy_analysis/accuracy_statistics.py`:

```python
self.v_x = points["dx"]  # vector of dx displacements
self.v_y = points["dy"]  # vector of dy displacements
# reverse y (line/northing) if image have SRS (carto representation)
if carto:
    self.v_y = -self.v_y
self.v_c = points["score"]  # vector of dc displacements
```

```python
self.median_x = np.median(vx)
self.mean_x   = np.mean(vx)
self.std_x    = np.std(vx)
```

where `vx = self.v_x_th` is the confidence-filtered vector of **signed** per-point `dx`.

**`mean_x`/`mean_y` are therefore the signed arithmetic means of the per-point displacements —
the GLOBAL SYSTEMATIC SHIFT (bias), not a per-point error magnitude.** A field of large but
randomly-oriented residuals averages to nearly zero on this statistic. This confirms from source
what the (5,3) validation showed behaviourally.

Three further facts from the same reading:

* The `carto` branch is the y sign flip observed in §1: `correl_res.txt` reports northing-up while
  the per-point CSV reports image rows.
* `self.v_c = points["score"]` is the **KLT score**, not a displacement — the inline comment
  "vector of dc displacements" is wrong. So `mean_c`/`std_c` are score statistics.
* **`correl_res.txt` contains no radial and no RMSE column.** Its columns are exactly:
  `refImg secImg total_valid_pixel sample_pixel confidence_th min_x max_x median_x mean_x std_x
  min_y max_y median_y mean_y std_y`.

RMSE appears only in the report, derived per axis in `karios/report/circular_error_plot.py`:

```python
def _rmse(mean, std, img_res=None):
    ...
    return np.sqrt(_mean * _mean + _std * _std)
```

so **RMSE = sqrt(mean² + std²) per axis** — bias and scatter combined. A separate CE90 (90th
percentile of sqrt(x²+y²)) exists but is printed to console/HTML only, not to `correl_res.txt`.

**Consequence.** Upstream's *"mean error around 0.7 pixel (7m) and a RMSE around 2.5 pixels (24m)"*
is consistent with `mean_x` ≈ 0.7 px and per-axis RMSE ≈ 2.5 px, which via the formula above
implies their **std ≈ sqrt(2.5² − 0.7²) ≈ 2.40 px**. In §4 we compared our *per-point mean radial*
(2.23 px) against their *global shift* (0.7 px). **Those are different quantities and the comparison
was invalid.**

### 8.2 PRE-REGISTRATION (registered 2026-08-18 12:28:01 UTC, before extracting any `correl_res.txt`)

Declared inputs: I already know from §4.1 that arm B's per-point **median** dx is +0.189 and dy
+0.0024, and arm A's are −0.246 and −0.444. The means are not yet extracted. Predictions below use
those medians as priors and say so.

**Q2 — arm B global shift vs upstream's 0.70 px.**
Predict **smaller**: global radial shift sqrt(mean_x² + mean_y²) in the range **0.10-0.40 px**,
most likely ≈ **0.20 px**, i.e. roughly one third of upstream's 0.70 px. Basis: the per-point
medians above give a radial ≈ 0.19 px; the mean may exceed the median given heavy tails, hence the
range rather than a point value.

**Q3 — does the affine correction reduce the GLOBAL shift by more than the 6.1 % it reduced the
per-point mean by?**
Predict **yes, by a large margin**. The scale ramp is a *systematic* displacement, which is exactly
what a signed mean captures, whereas the per-point radial mean is dominated by random scatter the
correction cannot touch. Over the common grid the ramp's mean displacement is 1285 m × 0.003891
= 5.0 m = **0.50 px per axis**, so arm A's signed means should exceed arm B's by about that.
Quantitatively: predict arm A global radial ≈ **0.45-0.60 px**, arm B ≈ **0.15-0.25 px**, a
reduction of **≥ 50 %** (most likely 55-75 %), against 6.1 % on the per-point mean.

**Q4 — what would make the reconciliation FAIL.**
It fails, and we really are worse than upstream rather than measuring a different quantity, if
**either**:

* arm B's global radial shift is **≥ 0.70 px** — then we are not better on their own statistic; or
* our per-axis **std substantially exceeds ~2.40 px** (say > 3.6 px, i.e. 50 % worse) — then our
  scatter is genuinely worse and the "different statistic" explanation covers only part of the gap.

A partial outcome is possible and must be reported as such: better on bias, worse on scatter. In
that case the honest statement is that we are better on the statistic upstream reports and worse on
one they also report, and §12.4 stays retracted.

### 8.3 RESULTS (2026-08-18 12:33:58 UTC)

All 348 `correl_res.txt` files parsed (116 chips x 3 arms). Every value below is a statistic
**KARIOS itself wrote**, averaged over chips.

| arm | chips | mean_x | mean_y | global shift (radial) | std_x | std_y | RMSE_x | RMSE_y |
|---|---|---|---|---|---|---|---|---|
| **A** stock | 116 | −0.1177 | +0.2313 | **0.2595** | 0.8973 | 0.9015 | 0.9050 | 0.9307 |
| **B** affine-corrected | 116 | +0.0532 | +0.1455 | **0.1549** | 1.0280 | 0.9018 | 1.0294 | 0.9135 |
| **C** scale-matched | 116 | +0.2347 | +0.1344 | 0.2705 | 1.0175 | 1.1057 | 1.0442 | 1.1139 |

RMSE columns use KARIOS's own per-axis formula sqrt(mean² + std²).

### 8.4 The second invalidity: we were also using a different POINT SET

`correl_res.txt` applies `confidence_threshold` = 0.8. That is far more aggressive than assumed:

| arm | points in the raw CSV (used in §4) | points KARIOS actually reports on | kept |
|---|---|---|---|
| A | 8353 | **327** | 3.9 % |
| B | 8500 | **363** | 4.3 % |
| C | 8721 | **372** | 4.3 % |

So §4's per-point statistics were computed over a point set **23x larger and much noisier** than the
one KARIOS's own summary uses. Two independent errors therefore made the §4 comparison invalid: the
wrong statistic *and* the wrong point set.

Every distinct "error" quantity for arm B, side by side:

| quantity | n | value |
|---|---|---|
| global shift, all raw points | 8500 | 0.1718 px |
| global shift, confidence ≥ 0.8 | 363 | 0.1499 px |
| **global shift, KARIOS `correl_res.txt`** | **363** | **0.1549 px** |
| mean radial, all raw points (**the §4 number**) | 8500 | 2.0908 px |
| mean radial, confidence ≥ 0.8 | 363 | 1.9968 px |
| RMSE radial, all raw points | 8500 | 2.5958 px |
| RMSE radial, confidence ≥ 0.8 | 363 | 2.4565 px |
| pooled std_x / std_y, confidence ≥ 0.8 | 363 | 1.8149 / 1.6537 px |
| **KARIOS mean per-chip std_x / std_y** | 363 | **1.0280 / 0.9018 px** |

KARIOS reports **no** radial statistic in `correl_res.txt`, which is why upstream quote only a mean
and an RMSE. Note also that KARIOS's std is a **per-chip** scatter averaged over chips (1.03 px),
while the pooled std across all chips is 1.81 px — the difference is between-chip variance, which
§9 decomposes.

### 8.5 Scorecard

| Q | prediction | outcome |
|---|---|---|
| **Q2** | arm B global shift 0.10-0.40 px, likely ≈0.20, smaller than 0.70 | **CONFIRMED** — 0.1549 px, within range, 4.5x smaller than upstream's 0.70 |
| **Q3** | arm A ≈0.45-0.60, arm B ≈0.15-0.25, reduction ≥50 % | **PARTLY CONFIRMED** — arm B 0.1549 within range; **arm A 0.2595 is below the predicted range**, and the reduction is **40.3 %**, short of the predicted ≥50 %. The qualitative claim holds decisively: 40.3 % on the global shift versus 6.1 % on the per-point mean, a 6.6x difference |
| **Q4** | fails if arm B global ≥0.70, or per-axis std ≫2.40 | **NOT FAILED** — 0.1549 px, and per-axis std 0.90-1.03 px against upstream's implied ≈2.40 px |

### 8.6 Answer: on the statistic upstream reports, are we better, worse, or equivalent?

**Better, on both statistics they publish.**

| statistic | upstream (README) | ours, arm B | ratio |
|---|---|---|---|
| mean error (= `mean_x`, global shift) | 0.70 px (7 m) | **0.155 px (1.55 m)** | **4.5x better** |
| RMSE (per axis) | 2.50 px (24 m) | **1.03 / 0.91 px** | **~2.5x better** |
| implied std | ≈2.40 px | **1.03 / 0.90 px** | ~2.4x better |

**The §4 conclusion that we were "3x worse than upstream" was wrong**, and wrong for two compounding
reasons: it compared our per-point mean radial against their global shift, and it did so over a
point set 23x larger because the 0.8 confidence threshold had not been applied.

**Caveat, stated because it cuts against the tidy version of this story:** our arm A global shift
(0.2595 px) is itself well *below* the ≈0.71 px that the scale ramp predicts as a mean radial
displacement over this grid. So our own data does not reproduce a 0.7 px bias from the scale error
alone. Contributing factors, none isolated: the common grid is inset (145-2425 m rather than the
full 0-2570 m), only ~3 confidence-filtered points survive per chip, and our chips are not upstream's.

### 8.7 Status of `geometry-finding.md` §12.4 — partially un-retracted

The retraction in §4 rested on an invalid comparison and is withdrawn. The hypothesis is **re-opened
but not confirmed**:

* **For it:** the scale error's predicted mean radial displacement over a full chip is
  0.003891 × 1285 m × sqrt(2) ≈ **7.07 m = 0.707 px**, which matches upstream's reported 0.70 px
  almost exactly. And correcting the affine reduces this statistic by **40.3 %**, not the 6.1 %
  that §4's per-point figure suggested — so the correction matters far more on upstream's statistic
  than we had concluded.
* **Against it:** our own arm A global shift is only 0.2595 px, so we do not directly measure a
  0.7 px bias attributable to the scale error.

**Correct status: plausible and numerically consistent, not demonstrated.** It should not be
asserted in an upstream issue as established; it should be offered as a hypothesis with the
arithmetic shown.

---

## 9. Where the noise floor comes from — variance decomposition (2026-08-18 12:47:51 UTC)

The question: is the ~2 px scatter our own reference construction (each chip displaced as a unit),
or the task's local matching floor? Decomposed on arm B, the geometrically correct arm.

### 9.1 Between-chip vs within-chip

| point set | axis | total var | mean within-chip var | var of chip means | **between share** |
|---|---|---|---|---|---|
| all points (8500, ~73/chip) | dx | 3.4288 | 3.9595 | 0.2532 | **6.0 %** |
| all points | dy | 3.2805 | 3.8978 | 0.2128 | **5.2 %** |
| confidence ≥ 0.8 (363, ~3/chip) | dx | 3.2939 | 3.2577 | 2.0794 | 39.0 % |
| confidence ≥ 0.8 | dy | 2.7349 | 2.6126 | 1.3820 | 34.6 % |

**The all-points row is the trustworthy one and the confidence-filtered row is an artefact.** With
only ~3 surviving points per chip, the *mean* of those 3 points carries a sampling variance of
σ²/3 ≈ 1.1 px², which is counted as "between-chip" variance even when no real per-chip offset
exists. The 39 % is therefore mostly sampling noise, not structure.

Correcting the all-points figure for the same effect: the observed variance of chip means (0.2532)
includes a sampling term of σ²_within/n̄ ≈ 3.96/73 = 0.054, leaving a true between-chip component of
≈ 0.199, i.e.

> **between-chip ≈ 4.8 % of the total; within-chip ≈ 95 %.**

### 9.2 WITHIN-chip dominates — the answer

**The noise floor is local matching, not our reference construction.** Chips are not being displaced
as a unit: 95 % of the variance is scatter *inside* each chip.

This is the reassuring branch of the two you set out. Our georeferencing of the satellite half by
inheriting the OSM raster's transform is **not** inflating the measurements, and no
reference-registration test is needed. The ~2 px floor is a property of matching generated imagery
against reality — consistent with the independent finding that the generator synthesises plausible
rather than actual scenes.

### 9.3 The per-chip component that does exist

A small coherent per-chip offset is present, and it is worth stating rather than rounding to zero:

| statistic | median dx | median dy | magnitude |
|---|---|---|---|
| mean over chips | +0.180 | +0.036 | 0.611 |
| median over chips | +0.146 | −0.028 | 0.553 |
| std over chips | 0.495 | 0.496 | 0.385 |
| range | −1.695 … +1.988 | −1.103 … +1.627 | 0.049 … 2.107 |

**18 of 116 chips (16 %) carry a median shift above 1 px**, one above 2 px. So per-chip offsets are
real but small against the ~2 px within-chip scatter — they cannot be the main story.

### 9.4 Structure in the per-chip offsets

* **Per-tile:** of chips in MGRS tiles with ≥3 members (15 tiles, 85 chips), between-tile variance is
  **24 %** of the per-chip shift variance. Some clustering by tile exists — plausible if OSM
  vintage or rendering differs by region — but three quarters of the variation is chip-to-chip
  within a tile.
* **Spatial:** correlations of per-chip shift with easting and northing are all |r| ≤ 0.17, i.e.
  no continental-scale gradient.

### 9.5 A caveat on KARIOS's own std

`self.std_x = np.std(vx)` uses numpy's default `ddof=0`, which is biased low for small samples. With
the 0.8 confidence threshold leaving ~3 points per chip, KARIOS's reported per-chip std
underestimates σ by roughly sqrt(2/3) ≈ 0.82. This affects the §8.3 std and RMSE columns for our
small chips. It would not matter on a large scene with thousands of points, so it does not affect
the comparison with upstream's figures — but our own absolute std/RMSE are slightly optimistic.

---

## 10. Is the chip-selection effect GenCP-specific, or generic matchability?

### 10.1 Partial correlation, controlling for surviving point count

The confound: richer OSM means more real structure, more corners, more points — so the residual
correlation might be nothing but "more points average better".

| OSM score | raw rho vs residual | partial rho (controlling for point count) | change |
|---|---|---|---|
| edge density | −0.7936 | **−0.6060** | +0.1876 |
| class count | −0.5883 | **−0.3972** | +0.1912 |
| non-dominant fraction | −0.7048 | **−0.4435** | +0.2613 |

rho(OSM edge density, point count) = +0.6749, so the confound is genuinely present — controlling for
it removes roughly a quarter of each correlation. **But the effect survives comfortably:** −0.61
against a p<0.01 critical value of 0.241 at n = 116.

**The relationship is not an artefact of having fewer points to average over.**
