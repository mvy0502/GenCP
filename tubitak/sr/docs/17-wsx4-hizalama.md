# WP16 Part B — Test A: the quarter-pixel shift, attributed

**Repository** `mvy0502/GenCP`, branch `tubitak-tr`. **Date** 1 September 2026.
**Time box** three hours. **Finished inside it**, in about two.

WP8 measured wsx4's output sitting a quarter of an output pixel off our grid convention in the
row axis, on 1267 of 1332 chips, and recorded it as **not attributed**. Test B (look for an
alignment declaration in `wsx4_spatrad.yaml`) was done and came back negative. Test A — run
their own tool end to end and measure the same quantity through it — was blocked because no
THEIA product exists for our area.

**Test A is now done. The shift is wsx4's own model.** It is not our seam, not our harness,
and not a grid-convention mismatch: the tool's own output grid and ours agree to 1.5
thousandths of a pixel.

---

## 1. The `--l1c` path: it works

WP5's top open item was whether `sentinel2_superresolution --l1c` completes on a Turkish L1C
product. **It does.**

No CDSE credentials exist on this machine and creating an account is not something this
session does. Google's public Sentinel-2 archive
(`gs://gcp-public-data-sentinel-2`) serves L1C SAFE anonymously over HTTPS and was used
instead. Tile 36SXJ holds 1007 L1C products there, including the L1C of **our own
acquisition**:

```
S2C_MSIL1C_20260527T082601_N0512_R021_T36SXJ_20260527T120938.SAFE
```

Same sensing time and same datatake (`A009000`) as the L2A granule
`params.GRANULES["36SXJ"]` names. So the comparison is not merely the same tile — it is the
same overpass. 826 MiB, fetched in 39 s, stored under gitignored `tubitak/data/wp16_l1c/`.

First run, a 256 × 256 patch, in the WP5 virtualenv, nothing installed:

```
sentinel2_superesolution --l1c -v -i <SAFE> -o <out> -m models/wsx4_spatrad.yaml \
                         -roip 2560 2560 2816 2816
...
Will process SENTINEL2C, 2026-05-27 08:26:01, 36SXJ
Will process the following bands [B02, B03, B04, B08] at 10.0 meter resolution
Target resolution is 2.5 meter
Will process 4 image chunks
Super-resolved output image: ..._2m5_sisr.tif
```

**3.0 s wall clock.** The path that WP5 could not verify runs, on Turkish ground, on the first
attempt.

---

## 2. The declared grid is ours

Before matching anything, what the tool writes in its own GeoTIFF header:

| | value |
|---|---|
| input B02 | 10980 × 10980, 10 m, origin (600000.0, 4400040.0), EPSG:32636 |
| tool output | 4096 × 4096, **2.5 m exactly**, origin (620480.0, 4379560.0), EPSG:32636, 4 bands int16 |
| output origin on the 10 m input lattice | dx **0.000000 m**, dy **0.000000 m** |

Pixel size is exactly src/4, the origin sits on the input lattice, the size is 4× — the tool's
declared output satisfies our Gate S grid contract. Whatever produces the shift, it is not the
georeferencing the tool writes down. That leaves the content.

---

## 3. The measurement

Same matcher as WP8 — `sr_match.pipeline.match`: Laplacian (k=7) → Shi-Tomasi → pyramidal
Lucas-Kanade (win 15, maxLevel 1) → forward-backward at 0.1 px → RANSAC
`estimateAffinePartial2D` (thresh 3.0, 5000 iters, conf 0.99), `cv2.setRNGSeed(20260831)`.
Same sign convention: **keypoints detected on the ARM, tracked into the REFERENCE,
dy = reference − arm.** Run in the `karios` environment — python 3.12.12, **cv2 4.8.1, numpy
1.26.4, scipy 1.17.1** — the stack WP8 recorded, so the inference path is the same one.

1024 × 1024 input pixels (10.24 km) at `-roip 2048 2048 3072 3072`, giving a 4096 × 4096
output, cut into 256 tiles of 256 output pixels. Band B04, the band WP8 measured. The tool was
run with `--bicubic`, so it produces its **own** plain interpolation on its **own** grid.

Their tool applies the L2A radiometric offset and we read raw L1C DN; the measured difference
is **+999 DN**, removed by median before matching. An additive constant is not a geometry and
cannot create or hide a translation, but left in place it would have wrecked the shared uint8
window that `to_uint8_fixed` depends on.

**Output pixel = 2.5 m. A quarter of one = 0.625 m.**

| # | arm vs reference | n | mean dx | mean dy | median dy | std dy | mean inliers |
|---|---|---|---|---|---|---|---|
| 1 | **their SISR vs their own bicubic** | 256 | −0.2022 | **−0.2299** | −0.2339 | 0.1430 | 150 |
| 2 | **their bicubic vs our bicubic** | 256 | +0.0003 | **+0.0015** | +0.0010 | 0.0066 | 1513 |
| 3 | their SISR vs our bicubic | 256 | −0.1948 | −0.2418 | −0.2401 | 0.1528 | 148 |
| 4 | our bicubic vs itself (null) | 256 | +0.0000 | +0.0000 | +0.0000 | 0.0000 | 1531 |

Row 3 is the end-to-end quantity and reproduces WP8's −0.25 through an entirely different
route: their tool, their reader, their tiling, their product, at their native scale.

---

## 4. What this attributes

**Row 2 removes the grid convention as an explanation.** Their bicubic and our bicubic are both
plain interpolations of the same 10 m input to the same 2.5 m grid, one by their tool and one
by `sr_core.BicubicUpsampler`. They agree to **+0.0015 px, standard deviation 0.0066, over 1513
inliers per tile**. If the tool's output convention differed from ours by a quarter pixel, this
row would show it. It does not.

**Row 1 places the shift inside the model.** Their SISR output is compared with their own
bicubic — same tool, same reader, same product, same grid, same tiling, same write path. The
only difference between the two rasters is that one went through wsx4 and the other through
interpolation. The shift is **−0.23 px**, essentially the whole effect.

### The sharp-versus-blurred confound, tested

Rows 1 and 3 compare a sharp arm against a blurred reference; rows 2 and 4 do not. If the
tracker were biased by that asymmetry alone, the attribution would collapse. Two controls:

| control | mean dx | mean dy | std |
|---|---|---|---|
| unsharp-masked copy of our bicubic vs our bicubic — a symmetric kernel, **zero shift by construction** | +0.0002 | **+0.0004** | 0.0099 |
| our own x4 model vs our bicubic — a real model, sharp against blurred | +0.0194 | **−0.0263** | 0.0481 |

Both are two orders of magnitude below wsx4's −0.23. Sharpness asymmetry does not produce the
effect. (The second control ran our L2A-trained model on L1C TOA input — the wrong radiometric
domain, and irrelevant here, because the only thing being measured is a translation.)

### Verdict

> **The quarter-pixel row-axis shift is intrinsic to the wsx4 model.** It is present in the
> vendor's own tool, on the vendor's own product, at the vendor's native scale, measured
> against the vendor's own bicubic on a grid that matches ours to 0.0015 px. WP8's finding
> stands, and WP5's `--l1c` open item is closed.

Nothing in this changes any GenCP number. `host_wsx4.py` and our seam are exonerated; wsx4 was
never used to produce a GenCP result, only as a comparison arm.

---

## 5. One thing that disagrees with WP8, and is now the open question

WP8 measured **dx +0.0322 against dy −0.2500** and argued from it:

> "the shift is in **y only**. `dx` is +0.032 px, an order of magnitude smaller. A pixel-centre
> convention disagreement would displace both axes equally. A single-axis offset is more
> consistent with something in row handling than with a symmetric grid convention."

In wsx4's **native** domain the shift is in **both** axes and roughly isotropic: dx −0.2022,
dy −0.2299 (row 1). That argument therefore does not carry over, and the interpretation has to
change with it.

The two experiments differ in several ways at once — 40 m → 10 m through our degradation versus
10 m → 2.5 m native; L2A BOA reflectance versus L1C TOA; our seam versus their tiling — so the
disagreement is not yet attributable either. What can be said is narrower than WP8's sentence
and is now the recorded position: **the shift is roughly isotropic at native scale and
row-dominant in the 40 m → 10 m experiment, and why it is anisotropic there is not known.**

Note also that a quarter of an output pixel is 0.0625 of an input pixel, which is not a member
of the `(s−1)/2s` family (0.375 at s = 4) or of the align-corners family (0.5 output px). No
standard convention offset predicts it. That is consistent with learned behaviour rather than a
declared convention, and it is consistent with `wsx4_spatrad.yaml` declaring no convention at
all.

---

## 6. Inference paths, stated

| number | path |
|---|---|
| rows 1–4, controls | L1C SAFE (GCS public archive) → `sentinel2_superresolution 2.0.2.post1.dev1+gcc5dec8c9`, `sensorsio 1.0.0.post1.dev45`, WP5 venv python 3.11.15 → GeoTIFF at 2.5 m → `sr_match.pipeline.match` in `karios` (cv2 4.8.1, numpy 1.26.4, python 3.12.12), seed 20260831 |
| our bicubic reference | same L1C window read at 10 m → `sr_core.upsample.BicubicUpsampler(scale=4)`, `n_clipped = 0` |
| our x4 model control | same window → `gencp_sr_x4_b4.onnx`, onnxruntime CPU, divisor 10000 |
| grid comparison (§2) | GeoTIFF transforms only, no matching |

These are **not** comparable with WP8's table, which was measured 40 m → 10 m on L2A through
our seam. Two numbers from different paths are not comparable; both are reported with their
path attached, and the agreement in §3 row 3 is agreement of a *conclusion*, not of a
measurement.

---

## 7. Open items

1. Why the shift is roughly isotropic at native scale and row-dominant in WP8's 40 m → 10 m
   experiment. Superseding WP8's "y only" reading, this is now the unresolved part.
2. The scientific cost of L1C for any purpose beyond geometry is still not assessed; L1C is
   top-of-atmosphere, and the model was trained on surface reflectance. This measurement is a
   translation and does not depend on radiometry, but no radiometric claim can be made from it.
3. Only band B04 and one 10.24 km window were measured. WP8's finding covered 1332 chips; this
   covers 256 tiles from one scene.
4. Whether the shift is worth reporting to the wsx4 authors. It is now a reproducible
   observation in their own tool, which is the form such a report needs.

---

## Appendix — draft issue for the Evoland repository

**Status: DRAFT. Not sent.** Sending it is Vedat's decision. Facts only; no recommendation and
no claim about cause. Target repository
`Evoland-Land-Monitoring-Evolution/sentinel2_superresolution`.

---

**Title:** wsx4 output is offset ~0.23 of an output pixel from a bicubic upsample of the same
input, measured through `sentinel2_superresolution --l1c`

**Body:**

Reporting a measurement, not a defect claim — I have no view on the cause.

**Setup**

- Tool: `sentinel2_superresolution 2.0.2.post1.dev1+gcc5dec8c9`, `sensorsio
  1.0.0.post1.dev45+g3372db58e`, python 3.11.15, installed in a clean virtualenv.
- Model: `wsx4_spatrad.yaml` as shipped, unmodified.
- Input: ESA L1C SAFE `S2C_MSIL1C_20260527T082601_N0512_R021_T36SXJ_20260527T120938.SAFE`,
  tile 36SXJ, from the public Google Sentinel-2 archive.
- Invocation, single run, both outputs from it:

      sentinel2_superesolution --l1c --bicubic -i <SAFE> -o <out> \
          -m wsx4_spatrad.yaml -roip 2048 2048 3072 3072

  1024 x 1024 input pixels at 10 m, giving a 4096 x 4096 output at 2.5 m.
- Measurement: band B04, cut into 256 tiles of 256 output pixels. Per tile: Laplacian
  (ksize 7), Shi-Tomasi corners, pyramidal Lucas-Kanade (window 15, maxLevel 1),
  forward-backward consistency at 0.1 px, then RANSAC `cv2.estimateAffinePartial2D`
  (threshold 3.0 px, 5000 iterations, confidence 0.99). OpenCV 4.8.1, numpy 1.26.4,
  `cv2.setRNGSeed(20260831)`. Keypoints are detected on the first-named image and tracked into
  the second; the reported offset is second minus first. Tiles with fewer than 10 inliers are
  dropped; none were.
- The tool applies the L2A radiometric offset while the L1C DN we read does not. The measured
  difference is +999 DN and is removed additively before matching.

**Result**

| # | first vs second | n | mean dx (px) | mean dy (px) | median dy | std dy | mean inliers |
|---|---|---|---|---|---|---|---|
| 1 | `_2m5_sisr.tif` vs `_2m5_bicubic.tif` (both from the run above) | 256 | −0.2022 | −0.2299 | −0.2339 | 0.1430 | 150 |
| 2 | `_2m5_bicubic.tif` vs an independent bicubic 4x upsample of the same 10 m input | 256 | +0.0003 | +0.0015 | +0.0010 | 0.0066 | 1513 |
| 3 | `_2m5_sisr.tif` vs that independent bicubic | 256 | −0.1948 | −0.2418 | −0.2401 | 0.1528 | 148 |
| 4 | the independent bicubic vs itself (null control) | 256 | +0.0000 | +0.0000 | +0.0000 | 0.0000 | 1531 |

Row 2 indicates the tool's output grid and the independent one agree to within 0.0015 px. The
`_2m5_sisr.tif` header declares 2.5 m pixels with its origin exactly on the 10 m input lattice.

**Confound tested**

Rows 1 and 3 compare a sharp image against a blurred one; rows 2 and 4 do not. Two controls for
a possible tracker bias from that asymmetry, same tiles and same settings:

| control | mean dx | mean dy | std |
|---|---|---|---|
| an unsharp-masked copy of the independent bicubic vs that bicubic (symmetric kernel, zero shift by construction) | +0.0002 | +0.0004 | 0.0099 |
| a different super-resolution model's output vs that bicubic | +0.0194 | −0.0263 | 0.0481 |

**Magnitude in ground units**

At the model's native scale the output pixel is 2.5 m, so −0.23 px is **about 0.58 m**, or
roughly 6% of a Sentinel-2 10 m pixel, applied uniformly across the scene.

**Note on provenance of the measurement**

Both rasters in row 1 were produced by a single invocation of `sentinel2_superesolution` on an
L1C SAFE product, reading through `sensorsio`, tiling and writing through the tool. **The model
was not run through any third-party hosting or re-implementation, so this is not an artefact of
how someone else loaded the weights.**

Happy to share the exact window, the per-tile numbers, or to re-run with different settings.
