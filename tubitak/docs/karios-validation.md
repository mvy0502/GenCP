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

