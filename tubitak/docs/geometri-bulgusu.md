# Geometry finding: the 257→256 scale error in GenCP HR outputs

**Status:** investigation only. No pipeline code was modified, no outputs were regenerated.
**Date:** 2026-08-18
**Verdict:** the 0.39 % scale error is **real, and exactly as predicted** — not larger, not smaller.

---

## 1. Observation

Input OSM rasters in `GenCP_HR_demo/data/dataset/test/` are 257×257 px at 10 m, i.e. 2570 m
on the ground. Model outputs are 256×256 px. `gencp_georeferencing.py` copies the input's
affine transform verbatim:

```python
with rasterio.open(reference_path) as src:
    with rasterio.open(out_image, "w", driver="GTiff",
                       height=test_img.shape[1],   # 256, from the generated array
                       width=test_img.shape[2],    # 256
                       crs=src.crs,
                       transform=src.transform):   # 10 m pixel size, from the 257-px source
```

The written raster therefore pairs a **256-px grid** with a transform whose pixel size is
**10.0 m**, declaring a footprint of 2560 m. If the 257×257 content was resampled to fill
256×256, the true ground sample distance is 2570/256 = 10.0390625 m and every GeoTIFF
carries a scale error that is zero at the origin and grows to one full pixel at the far corner.

This was flagged because it is the same order of magnitude as the accuracy budget KARIOS
is about to measure.

---

## 2. Method

Three independent lines of evidence were used, deliberately chosen so that no two share a
failure mode:

1. **Code path** — resolved dataloader options read from the run's own saved options file,
   plus the transform code actually executed.
2. **Hypothesis test** — reconstruct each candidate transform from the source raster and
   compare to the network's own recorded input, `_real.png`.
3. **Direct measurement** — subpixel phase correlation between `_real.png` and the source
   raster on a 4×4 grid of windows, which infers the geometry from the imagery alone and
   is independent of both the code reading and the resize hypotheses.

### Shift estimator and its validation

Translation was estimated by phase correlation with upsampled-DFT refinement
(Guizar-Sicairos et al., *Opt. Lett.* **33**, 156, 2008), implemented directly on NumPy so
the analysis needs no extra dependency. Windows were Hann-tapered and mean-subtracted.

The estimator was validated against known sub-pixel shifts before use. A first
implementation was **rejected**: it showed errors up to 1.14 px, comparable to the effect
being measured. The corrected implementation gives:

| true (dy, dx) | estimated (dy, dx) | error |
|---|---|---|
| 0.00, 0.00 | 0.000, 0.000 | 0.000 |
| 0.13, 0.13 | 0.070, 0.070 | −0.060 |
| 0.38, 0.38 | 0.270, 0.270 | −0.110 |
| 0.63, 0.63 | 0.710, 0.710 | +0.080 |
| 0.88, 0.88 | 0.920, 0.920 | +0.040 |
| 1.00, 0.00 | 0.990, 0.000 | −0.010 |
| −0.50, 0.75 | −0.460, 0.830 | +0.040 / +0.080 |
| 2.25, −1.40 | 2.110, −1.270 | −0.140 / +0.130 |

**Validated accuracy: RMS 0.076 px, max 0.14 px.** The estimator slightly under-reads small
shifts (a known windowing bias). This matters for interpretation and is handled in §4.3.

---

## 3. Measurements

### 3.1 Resolved dataloader options

From `GenCP_HR_demo/checkpoints/genCP_HR_RGB_model/test_opt.txt`, written by our own run:

| option | value in saved file | value actually in effect |
|---|---|---|
| `preprocess` | `resize_and_crop` | `resize_and_crop` |
| `load_size` | `256` | `256` |
| `crop_size` | `256` | `256` |
| `no_flip` | `False` | **`True`** |

> **The saved options file is misleading for three fields.** `test.py` writes the file during
> `parse()`, then overrides `no_flip → True`, `serial_batches → True` and `num_threads → 0`
> at lines 45–48, *before* `create_dataset(opt)` at line 50. The effective `no_flip` is
> therefore `True` — no random flip was applied. `preprocess`, `load_size` and `crop_size`
> are **not** overridden, so the saved values stand for those.

The executed path in `data/base_dataset.py::get_transform` is:

- `'resize' in preprocess` → `transforms.Resize([256, 256], BICUBIC)` — a **full-extent
  resample** of the 257×257 image onto a 256×256 grid.
- `'crop' in preprocess`, `params is None` → `transforms.RandomCrop(256)` applied to an image
  that is *already* 256×256 — **a no-op**, only one crop position exists.
- `not opt.no_flip` is `False` → no flip.

### 3.2 Hypothesis test (8 tiles)

Each candidate was reconstructed from the source `.tif` and compared to `_real.png`.
Mean over 8 tiles; per-tile figures were consistent to within ±0.3 MAD.

| hypothesis | mean MAD (DN) | max diff | mean corr |
|---|---|---|---|
| **H1 resize 257→256 (pipeline)** | **0.0574** | **1** | **0.999995** |
| H2 resize(load=256) + crop 256 | 0.0574 | 1 | 0.999995 |
| H2′ counterfactual, load=286 | 14.2272 | 244–255 | 0.810684 |
| H3 crop TL `[0:256, 0:256]` | 4.0486 | ~180 | 0.971214 |
| H3 crop TR `[0:256, 1:257]` | 3.9646 | ~190 | 0.972486 |
| H3 crop BL `[1:257, 0:256]` | 4.2364 | ~200 | 0.966857 |
| H3 crop BR `[1:257, 1:257]` | 4.2774 | ~200 | 0.967718 |

H1's residual is **max 1 DN** across every pixel of every tile — that is the
float→uint8 round-trip in `util.tensor2im`, not a geometric difference. The four H3 crops
are ~70× worse in MAD and reach ~200 DN maximum error.

**H2 is numerically identical to H1 here**, because `load_size == crop_size == 256` makes the
crop degenerate. H2 is not a distinct hypothesis under these options.

### 3.3 Direct measurement — 4×4 shift field

Representative tile `31TEJ_0704_00`. Windows are 64×64 px; "measured" compares the source
raster against `_real.png`; "control" compares the source raster against a *known* H1
resample produced locally. Sign convention: negative means `_real` content sits at smaller
row/column indices than the same content in the 257-px source.

| window | centre (y, x) px | measured dy | measured dx | control dy | control dx | conf |
|---|---|---|---|---|---|---|
| 0,0 | 31.5, 31.5 | −0.070 | −0.050 | −0.070 | −0.050 | 364 |
| 0,1 | 31.5, 95.5 | −0.040 | −0.210 | −0.040 | −0.210 | 286 |
| 0,2 | 31.5, 159.5 | −0.020 | −0.810 | −0.020 | −0.810 | 491 |
| 0,3 | 31.5, 223.5 | −0.060 | −0.940 | −0.060 | −0.940 | 367 |
| 1,0 | 95.5, 31.5 | −0.210 | −0.060 | −0.210 | −0.060 | 299 |
| 1,1 | 95.5, 95.5 | −0.230 | −0.230 | −0.230 | −0.230 | 176 |
| 1,2 | 95.5, 159.5 | −0.370 | −0.810 | −0.370 | −0.810 | 124 |
| 1,3 | 95.5, 223.5 | −0.280 | −0.910 | −0.280 | −0.910 | 195 |
| 2,0 | 159.5, 31.5 | −0.830 | −0.050 | −0.830 | −0.050 | 512 |
| 2,1 | 159.5, 95.5 | −0.720 | −0.320 | −0.720 | −0.320 | 131 |
| 2,2 | 159.5, 159.5 | −0.770 | −0.740 | −0.770 | −0.740 | 140 |
| 2,3 | 159.5, 223.5 | −0.690 | −0.950 | −0.690 | −0.950 | 165 |
| 3,0 | 223.5, 31.5 | −0.910 | −0.110 | −0.910 | −0.110 | 189 |
| 3,1 | 223.5, 95.5 | −0.930 | −0.170 | −0.930 | −0.170 | 227 |
| 3,2 | 223.5, 159.5 | −0.950 | −0.750 | −0.950 | −0.750 | 255 |
| 3,3 | 223.5, 223.5 | −0.960 | −0.970 | −0.960 | −0.970 | 348 |

All 16/16 windows had sufficient texture (confidence ≫ 8); none were discarded.

Fitted slope (least squares through the origin), 6 tiles:

| tile | measured dy/y | measured dx/x | control dy/y | control dx/x | measured − control |
|---|---|---|---|---|---|
| 31TEJ_0451_00 | −0.004328 | −0.004032 | −0.004332 | −0.004039 | +0.000005 |
| 31TEJ_0691_00 | −0.003962 | −0.004197 | −0.003962 | −0.004200 | +0.000001 |
| 31TEJ_0699_00 | −0.004280 | −0.004247 | −0.004277 | −0.004254 | +0.000002 |
| 31TEJ_0700_00 | −0.004035 | −0.004198 | −0.004035 | −0.004203 | +0.000002 |
| 31TEJ_0704_00 | −0.004176 | −0.004198 | −0.004176 | −0.004198 | 0.000000 |
| 31TEJ_0706_00 | −0.004084 | −0.004200 | −0.004084 | −0.004200 | 0.000000 |
| **mean** | **−0.004144** | **−0.004179** | **−0.004144** | **−0.004183** | **≤ 5×10⁻⁶** |

Shift field figure: [`figures/geometri-kayma-alani.png`](figures/geometri-kayma-alani.png).
Measured magnitudes on the representative tile run from **0.86 m** (NW) to **13.65 m** (SE),
i.e. 0.086 → 1.365 output pixels.

### 3.4 Input geometry, independently confirmed (5 tiles)

| file | size | transform a, e | bounds W–E (m) | (bounds width)/(px count) |
|---|---|---|---|---|
| 31TEJ_0451_00 | 257×257 | +10.0, −10.0 | 603580 → 606150 = 2570 | 2570/257 = **10.0** |
| 31TEJ_0691_00 | 257×257 | +10.0, −10.0 | 606770 → 609340 = 2570 | 2570/257 = **10.0** |
| 31TEJ_0699_00 | 257×257 | +10.0, −10.0 | 605380 → 607950 = 2570 | 2570/257 = **10.0** |
| 31TEJ_0700_00 | 257×257 | +10.0, −10.0 | 600620 → 603190 = 2570 | 2570/257 = **10.0** |
| 31TEJ_0704_00 | 257×257 | +10.0, −10.0 | 607550 → 610120 = 2570 | 2570/257 = **10.0** |

All are `EPSG:32631`, north-up (b = d = 0), and internally self-consistent. **All 630** test
rasters are 257×257 at (10.0, 10.0) — uniform, not a subset of odd files.

---

## 4. Which hypothesis is confirmed

**H1 — full-extent resample — on three independent grounds.**

### 4.1 Code
`preprocess=resize_and_crop` with `load_size=256` executes `Resize([256,256], BICUBIC)` on
the 257×257 image. The subsequent `RandomCrop(256)` is a no-op on an already-256 image.

### 4.2 Reconstruction
H1 reproduces `_real.png` to a maximum of 1 DN (MAD 0.057, corr 0.999995). The best H3 crop
is off by MAD 4.05 and up to ~180 DN. H3 is excluded decisively.

### 4.3 Direct measurement
The shift field is a **linear ramp with its fixed point at the NW chip origin**, growing to
≈1 px at the SE corner — the H1 signature. It is not zero (excludes H3), not a uniform
offset (excludes a displaced crop), and shows no rotation or shear.

The strongest single piece of evidence is the **control column**: measuring the source
raster against a locally-produced, known-H1 resample yields the same slope as measuring it
against `_real.png`, agreeing to **≤ 5×10⁻⁶ px/px**. Whatever residual bias the estimator
has, it affects both equally, and `_real.png` is geometrically indistinguishable from a
known full-extent resample.

This also resolves the apparent discrepancy between the measured slope (−0.004162) and the
theoretical H1 slope (−0.003891, i.e. −(1 − 256/257)). The measurement is ~7 % steeper, but
the control — which *is* H1 by construction — reproduces exactly the same 7 %. The offset is
estimator bias (§2), not evidence against H1. The theoretical value stands.

### 4.4 H2 explicitly addressed
H2 cannot be "the answer rather than H1": with `load_size == crop_size == 256` the crop is
degenerate and H2 **is** H1. The order-of-magnitude-larger error would require
`load_size > crop_size`; with the pix2pix default `load_size=286` the error would be
286/256 = 1.1172, i.e. **11.72 %** rather than 0.39 %. That is not what this configuration does.

---

## 5. Quantified impact

Confirmed geometry: the 2570 m of input content is rendered onto 256 output pixels, but the
transform declares 10.0 m pixels.

- True GSD of output content: 2570/256 = **10.0390625 m**
- Declared GSD: 10.0 m
- **Scale error: +0.390625 % = exactly 1/256**
- The GeoTIFF declares a 2560 m footprint; the content spans 2570 m — **short by 10.0 m**

Ground displacement between where a feature actually sits and where the transform says it
sits, for one chip (error accumulates linearly from the NW origin):

| point | u, v (px) | dx (m) | dy (m) | radial (m) | radial (output px) |
|---|---|---|---|---|---|
| NW corner (origin) | 0, 0 | 0.000 | 0.000 | **0.000** | 0.000 |
| NE corner | 255, 0 | 9.961 | 0.000 | **9.961** | 0.996 |
| SW corner | 0, 255 | 0.000 | 9.961 | **9.961** | 0.996 |
| SE corner | 255, 255 | 9.961 | 9.961 | **14.087** | 1.409 |
| centre | 127.5, 127.5 | 4.980 | 4.980 | **7.043** | 0.704 |
| SE outer edge | 256, 256 | 10.000 | 10.000 | **14.142** | 1.414 |

The error is **systematic and fully deterministic**, not noise: it is the same ramp in every
chip, always anchored at the NW corner. Mean radial displacement over the chip area is
roughly 7 m; worst case 14.1 m.

---

## 6. Is 257 intentional? (training-data check)

**The HR training set is not available locally** — only the 630 test rasters (121 MB) and the
model weights were downloaded. It was **not** downloaded for this investigation, per instruction.

Indirect evidence available locally:

| dataset | present locally | chip size |
|---|---|---|
| HR demo test rasters | yes, 630 files | **257×257** (uniform) |
| VHR demo `images/` | yes, 21 files | **256×256** |
| VHR demo `masks/` | yes, 21 files | **256×256** |
| HR **training** pairs | **no** | unknown |

The VHR branch of the same project uses 256×256. That is suggestive that 257 is an artefact
of how *this* HR demo dataset was rasterised (e.g. an inclusive-bounds off-by-one when
cutting tiles) rather than a deliberate convention — but it is indirect. **The decisive
question, whether the HR training pairs were also 257 px, cannot be answered locally.**

---

## 7. Upstream awareness

Searched the whole repository — `.py`, `.md`, `.txt`, and notebook **source cells** (an
initial grep matched base64 image data in notebook *outputs* and was discarded as a false
positive).

- No occurrence of `257` in any source file or notebook cell.
- No mention of `resample`, `rescale`, `scale factor`, `GSD`, or `ground sample`.
- `gencp_georeferencing.py` applies **no scale factor**. It takes `width`/`height` from the
  generated 256-px array and `transform` from the 257-px source, with nothing reconciling them.
- No comment or docstring anywhere acknowledges the size change.

**Conclusion: there is no evidence the upstream authors considered this.** The pairing of a
256-px grid with a 257-px source transform appears to be unexamined rather than a deliberate
approximation.

---

## 8. What remains uncertain

1. **Whether the training data shared this geometry.** This is the one thing that changes the
   *interpretation*. If training pairs were also 257 rasters resampled to 256, the model
   learned on this geometry, the generated content genuinely corresponds to the full 2570 m
   extent, and the problem is **metadata-only** — the pixels are right, the transform is wrong.
   If training chips were natively 256, the situation is more complicated. Resolving this
   requires the Zenodo HR training set (~1.7 GB), deliberately not downloaded.
2. **Estimator bias.** Validated RMS 0.076 px, and it under-reads small shifts. This affects
   the absolute slope by ~7 % but not the conclusion, because the control absorbs it.
3. **Sub-pixel behaviour of BICUBIC resampling** on hard-edged categorical OSM rasters may
   introduce edge-dependent bias not modelled here. It does not affect the scale factor,
   which is fixed by the 257→256 grid ratio, not by the kernel.
4. **Whether 10.0390625 m or 10.0 m is the "intended" GSD** is a project decision, not a
   measurement. §5 quantifies the discrepancy; it does not adjudicate which is correct.
5. **KARIOS interaction.** KARIOS may itself fit and report a scale/shift term. Whether this
   ramp should be subtracted beforehand or left in and interpreted is a validation-design
   choice, not settled here.

---

## 9. Options (proposals only — nothing implemented)

### Option A — correct the affine at georeferencing time
Write the transform with a 10.0390625 m pixel size, keeping the same NW origin.

- **Changes:** outputs become geometrically correct; the 10 m footprint discrepancy disappears.
  Cheap — only metadata; the existing 50 outputs can be rewritten without re-running inference.
- **Risks:** outputs carry a non-round GSD, which some downstream tools and mosaicking steps
  dislike; the GenCP_DB then differs from anything produced by the stock upstream script, so
  results are no longer bit-comparable with the published demo.
- **Upstream code:** touched **only if** `gencp_georeferencing.py` is edited. It can be avoided
  entirely by writing a separate script under `tubitak/`.

### Option B — resample outputs back onto the 257 grid
Resample each 256×256 output to 257×257 and keep the original 10.0 m transform.

- **Changes:** outputs align exactly with the input grid and keep a round 10 m GSD.
- **Risks:** introduces a **second interpolation** over generated imagery. This softens texture
  and alters pixel statistics — directly harmful to the radiometric and texture metrics KARIOS
  and FID-style scores are meant to measure. Strongly disfavoured for an accuracy study.
- **Upstream code:** none, if done in a new script.

### Option C — leave the data alone, model the bias in validation
Keep the GeoTIFFs as they are; subtract a known 0.390625 % scale ramp (anchored at the NW
corner) when interpreting KARIOS results.

- **Changes:** nothing on disk. The bias becomes a documented, exactly-known quantity rather
  than an unexplained residual.
- **Risks:** every downstream consumer must know; easy to forget later or for another team
  member. If KARIOS reports a scale term, it must be recognised as expected rather than an error.
- **Upstream code:** none.

### Option D — remove the resample at source
Run inference with `--preprocess none` (or a crop) so the model sees a 256 window of the
257 raster with no rescaling.

- **Changes:** eliminates the error at its origin rather than patching metadata.
- **Risks:** **changes what the model sees**, and therefore the generated imagery — all outputs
  must be regenerated, and results diverge from the published demo. If the model was trained on
  resampled 257→256 chips, this introduces a train/test mismatch that could *degrade* output
  quality. Should not be considered until §8.1 is resolved.
- **Upstream code:** no edit needed (CLI options only), but results change.

### Option E — report upstream
Open an issue on `telespazio-tim/GenCP` describing the 257/256 transform mismatch.

- **Changes:** nothing locally.
- **Risks:** none; independent of whichever of A–D is chosen.
- **Upstream code:** none.

**No option has been implemented. This is a decision for the project owner.**

---

## 10. Reproducing these measurements

The analysis was run from throwaway scripts in a scratch directory and is **not** committed,
per instruction (only this document and its figure are). The method is fully specified above:
§2 gives the estimator and its validation protocol, §3.2 the hypothesis reconstructions,
§3.3 the 4×4 windowing scheme and the control construction. No pipeline file was modified and
no output was regenerated at any point.
