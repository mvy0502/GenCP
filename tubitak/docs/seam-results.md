# Results: the visible tile grid, and whether buildings reach the model

Registered in [seam-registration.md](seam-registration.md) (`3acbe61`) before any mosaic was
measured. Corpus: the İstanbul scene, 567 tiles at 640 m overlap, C2 arm. No institutional
imagery is reproduced here; only summary numbers.

## Part 1 — buildings

**Buildings reach the model. Part 1 is closed.** Measured by rendering each tile twice,
once with building features and once without, and differencing:

| tile | building features | footprint | pixels changed | mean change |
|---|---|---|---|---|
| Fatih | 18,079 | 49.2% of the tile | 78.65% | 63.82 DN |
| Kadıköy | 8,633 | 28.3% | 55.91% | 40.61 DN |
| Şişli | 9,229 | 34.3% | 58.78% | 36.50 DN |

The rasteriser draws `building`, `water`, `natural`, `landuse`, `leisure`, `waterway`
(polygons, plus river/canal lines) and `highway` lines. Buildings are painted **last**, over
everything else, so nothing occludes them.

### But the diagnostics cannot see them, and that is what misled us

Counting pixels of the exact building colour gives 0.73% for Fatih, because the 4x
downsample and the fitted blend move most building pixels off the palette. That was the
wrong measurement and it is the one the interface reports.

Worse, and separately: **the confidence module's palette has 22 classes and no `building`
entry.** The rasteriser adds `RGB["building"] = (165, 42, 42)` on top of the upstream
palette; `confidence.class_map` classifies against the upstream palette alone. A pure
building pixel is therefore assigned to its nearest palette colour, which is **`red_road`,
104.8 DN away**. Consequences:

* The dialog's "N bina" readout counts class `light_gray`, which is not buildings and not
  what buildings are classified as. It under-reports buildings by about two orders of
  magnitude. This is the "0 bina" that started the investigation.
* Building pixels are counted as **roads** in the same readout.
* `conf_D` sees a building as a primary road. This does **not** invalidate the confidence
  bands: calibration ran through the identical `class_map`, so the score is internally
  consistent. It does mean the score cannot distinguish built-up from road-dense.

**Not fixed here.** The readout can be corrected from the vector features without touching
the rasteriser, but changing anything `class_map` sees would move `conf_D` and therefore the
calibrated bands. That is a deliberate decision, not a cleanup.

### The upstream question

The pinned palette is `GenCP_HR_demo/genCP_HR_osm_colors.py`, 22 colours, and it has **no
building class** — the string "building" does not appear in it, nor anywhere in the upstream
HR demo notebook. The VHR palette has `building_colors`; the HR one, which is what the
deployed 10 m model uses, does not. No HR palette entry equals `#a52a2a`.

So the direction is the opposite of the one feared: **upstream HR does not render buildings
and we do.** The building colour is foreign to the palette the pretrained generator was
trained on.

This is not a clean train/serve mismatch for the deployed arm, and the distinction matters:
`tubitak/scripts/tile_pipeline.py` builds training inputs through `osm_to_raster.make_chip`,
the same renderer, so the **fine-tuned** C-arms did see buildings during fine-tuning. It is
the **pretrained** base that never did. Whether ~50%-coverage brown in an unseen colour is
adequately learned by fine-tuning on Ankara is not settled by this package.

## Part 2 — the tile grid

### All three registered predictions failed

| # | registered prediction | measured | verdict |
|---|---|---|---|
| 1 | S1/C1 > 1.3 in train mode | **0.979** | FALSIFIED |
| 2 | eval mode cuts the S1/C1 excess by ≥25% | 0.979 → 1.019 | no excess existed |
| 3 | S2 falls ≥30% in eval mode | 35.98 → **45.43** (rose) | FALSIFIED |

Stratifying by texture, in case land was diluting a sea-only effect, does not rescue it:

| stratum | S1 | C1 | S1/C1 |
|---|---|---|---|
| uniform (sea, fill) | 0.901 | 0.971 | 0.928 |
| textured (land) | 8.980 | 8.781 | 1.023 |
| all | 4.910 | 5.015 | 0.979 |

**There is no step at tile boundaries anywhere.** The instance-normalisation mechanism as
stated is refuted: it predicts a discontinuity at the join, and there is none.

### What the grid actually is: periodicity, not discontinuity

Autocorrelation of the sea region along x, normalised, baseline −0.101:

| lag | value |
|---|---|
| 96 px (half pitch) | −0.496 |
| **193 px = the tile stride** | **+0.923** |
| 386 px = 2x stride | +0.916 |

The strongest peak beyond lag 20 is at exactly 193 px, the tile pitch.

The mechanism, measured directly: four widely separated open-sea tiles were rendered and
run through the generator. Two of them had **byte-identical inputs** (0.00 DN apart) because
open water carries no OSM and one CLC+ class — and their outputs were **byte-identical too**
(0.00 DN). The generator is deterministic. Featureless tiles receive the same input, so they
emit the same hallucinated texture, and that patch is laid down once per tile.

This also explains the overlap observation better than the original hypothesis did.
Blending 640 m of overlap cannot remove the pattern because **the neighbouring tile carries
the same pattern**: averaging two copies of one texture returns that texture.

### Eval mode, measured anyway

| | train-mode (shipped) | eval-mode (`gencp_C2_evalbn_fp32.onnx`) |
|---|---|---|
| S1/C1 | 0.979 | 1.019 |
| S2 | 35.98 | 45.43 |
| autocorrelation at the tile pitch | **+0.923** | **+0.428** |

Eval mode halves the periodicity without touching the seam metrics, which is what the
repetition mechanism predicts: it changes *what* the hallucinated texture is, not the fact
that every identical tile gets an identical one. The two mosaics differ over 83.1% of pixels
by more than 8 DN (mean 15.56 DN), so this is a substantial change to the imagery.

### The trade-off, both numbers, same corpus, same inference path

From [plugin-results.md](plugin-results.md) Item C, registered in
`plugin-gate-registration-C.md` (`57d25aa`). Δ = evalbn − det_onnx, negative = eval better:

| arm | Δ on full sets | Δ on common support | dropped-point median error | surviving |
|---|---|---|---|---|
| C2 | −0.1861 ± 0.4836 px (t=−1.72) | **−0.0396 ± 0.1444 px (t=−1.23), indistinguishable** | 1.6530 px | 0.5067 px |
| C3 | −0.2824 ± 0.4240 px (t=−2.83) | −0.0594 ± 0.1500 px (t=−1.68) | 1.4513 px | 0.5576 px |

About **79% of eval mode's apparent matching advantage disappears** on common support, and
the points it drops carry roughly 1 px more error at t > 5.6. On that basis the project
already decided to keep batch-statistic normalisation.

So the two criteria now point in different directions: eval mode is **better on periodicity**
(+0.428 vs +0.923) and **not better on matching error** once survivorship is removed.

**Visible image quality has never been a gate in this project. Every registered gate scores
matching error.** That is precisely why this surfaced only when someone looked at a large
mosaic over water. Whether to add an image-quality criterion, and what it would cost in
matching error, is a decision for the project owner. Nothing is adopted here.

## Part 3 — corrected confidence shares

The reported figure covers the whole output rectangle, which includes the rotated scene's
black-fill corners and the Marmara Sea — neither has OSM or useful land cover.

| domain | green | amber | red | pixels |
|---|---|---|---|---|
| whole output rectangle (as reported) | 55.4 | 5.8 | **38.8** | 20,548,770 |
| valid-data footprint only | 59.0 | 5.9 | 35.1 | 13,550,384 |
| **land within the valid footprint** | **85.7** | **8.2** | **6.0** | 8,613,985 |
| rural Ankara demo tile, for comparison | 29.6 | 29.0 | 41.4 | — |

The footprint is 65.9% of the rectangle and land is 63.6% of the footprint. The uncorrected
number understated the tool badly: red falls from 38.8% to **6.0%** once sea and fill are
excluded. Reported correctly, İstanbul land is 85.7% green against rural Ankara's 29.6%.
