# QGIS plugin work package — results, scored against the registrations

> **Conventions.** Every paired difference is **Δ = candidate − baseline; negative =
> candidate better**. The **inference path is stated for every number**. Registrations:
> [plugin-gate-registrations.md](plugin-gate-registrations.md), committed (`844dbec`)
> before any number below existed.

**Date:** 2026-08-26, branch `tubitak-tr`.

> **Cross-references.** Commit `b815b46` moved the research record out of this fork and
> into `mvy0502/gencp-validation` while this work package was running. Links here to
> measurement-phase documents — `tool-results.md`, `tool-gate-registration-2.md`,
> `corrections-log.md`, `standing-practices.md`, `tool-registrations-3.md`,
> `tool-registration-4.md` — resolve **in gencp-validation**, which shares this history
> from merge base `96503b7`, and not in this fork. Every number quoted from those documents
> is reproduced inline here, so nothing in this file depends on following a link.
>
> That same commit deleted this file (it removed `tubitak/docs/**` except the
> registrations). The Environment, Gate R, Gate O and Gate D sections below were restored
> from commit `814f06c`, where they were first committed. Recorded rather than silently
> repaired.

---

## Environment finding (resolved before Step 4, as required)

**QGIS runs here, headless, with working Python bindings.** This was not assumed; it was
tested.

| item | finding |
|---|---|
| QGIS | **4.2.1 "Belém do Pará"**, `/Applications/QGIS-final-4_2_1.app` |
| bundled interpreter | Python **3.12.11** at `Contents/MacOS/python3.12` |
| headless | works via `QT_QPA_PLATFORM=offscreen` — **no Xvfb needed** (macOS has no X server; Qt's offscreen platform plugin replaces it) |
| CRS / PROJ | works once `PROJ_DATA`/`PROJ_LIB` and `GDAL_DATA` point into `Contents/Resources/qgis/` |
| gotcha | the bundle's interpreter carries a stale build-machine `sys.prefix`; `PYTHONHOME=Contents/Frameworks` is required or it dies with `ModuleNotFoundError: encodings` |

Packages already present **inside QGIS's own Python**: numpy 2.5.0, GDAL 3.12.4,
rasterio 1.5.0, PIL 12.2.0, scipy 1.18.0, shapely 2.1.2, pip 26.1.2. **Missing:
`onnxruntime`** — which is the one thing the plugin must add, and it is a single wheel.

The working command, recorded so it is reproducible:

```bash
A=/Applications/QGIS-final-4_2_1.app/Contents
QT_QPA_PLATFORM=offscreen PYTHONHOME=$A/Frameworks \
PYTHONPATH=$A/Resources/python3.12/site-packages:$A/Resources/python \
PROJ_DATA=$A/Resources/qgis/proj PROJ_LIB=$A/Resources/qgis/proj \
GDAL_DATA=$A/Resources/qgis/gdal $A/MacOS/python3.12 -c "import qgis.core"
```

Consequence for reporting: dialog behaviour in this package is **executed**, not merely
written. Where something could not be exercised headlessly it is said so explicitly.

---

## Gate R — byte-identical raster gate: **PASS (3/3)**

**Predicted:** all three pass; the lift is mechanical.

**Tiles** (registered rule — first three `acc_clcgate` stems with census `byte_exact == 1`,
ascending lexicographic): `30TXQ_0830_00`, `30TXQ_0934_00`, `30UYD_0907_00`.

| tile | core vs stored original | georeferencing | differing px | core vs existing script |
|---|---|---|---|---|
| 30TXQ_0830_00 | **byte-identical** | transform + CRS equal | 0 / 66,049 | identical |
| 30TXQ_0934_00 | **byte-identical** | transform + CRS equal | 0 / 66,049 | identical |
| 30UYD_0907_00 | **byte-identical** | transform + CRS equal | 0 / 66,049 | identical |

The lift into `gencp_core/rasterize.py` changed nothing. The supporting measurement — the
*existing* `scripts/osm_to_raster.py` run in the same process — is byte-identical to the
core on all three, so the render path is unchanged and the archive is still reproducible
today.

**Disclosed false start.** The first run of this gate failed 0/3 with a dominant
`light_green -> forest_green` flow. Cause: the registration named
`tubitak/data/rasteriser/chips/`, inherited verbatim from
[tool-gate-registration-2.md](tool-gate-registration-2.md); that directory holds the
**WorldCover-era** corpus (18 Aug 19:43), rendered before the CLC+ base layer landed in
`e15f5a9` (19 Aug 11:48). The CLC+ renders the census scored are in
`rasteriser/chips_clc/` (55 files, matching the census's 55 rows). The reference path was
corrected in registration amendment 1; **the criterion, the tile-selection rule and the
byte-identity bar are unchanged.** The lift was exonerated *before* the correction, by the
supporting measurement: the existing script failed identically and core-vs-script was
byte-identical in both runs. The path error is also present in the earlier registration's
text and is flagged there.

---

## Gate O — PyTorch/ONNX parity: **PASS on fp32**, fp16 fails the same bound

**Predicted:** pass; a plain convolutional U-Net exports bit-close in fp32.

**Tiles:** first 20 `acc_clcgate` stems, ascending lexicographic. Both sides deterministic
(dropout removed), BatchNorm in batch-statistics mode.

**Input identity is measured, not assumed:** `gencp_core.infer.preprocess` (plain PIL +
numpy) against the torchvision pipeline `test.py` uses — **max abs diff 0.0, bit-identical**.

| model | R max / mean | G max / mean | B max / mean | overall max | bound | verdict | size |
|---|---|---|---|---|---|---|---|
| **fp32** | 0.000547 / 0.000034 | 0.000471 / 0.000024 | 0.000498 / 0.000018 | **0.000547 DN** | 0.003922 | **PASS** | 217.68 MB |
| fp16 | 0.435565 / 0.028531 | 0.368820 / 0.022284 | 0.292493 / 0.023554 | **0.435565 DN** | 0.003922 | **FAIL** | 108.86 MB |

All figures in 8-bit units (DN), measured on the continuous network output before
quantisation so that rounding neither hides nor invents a difference. **fp32 is what
ships.** fp16 halves the file at the cost of failing the registered bound by ~110x; it is
reported because the registration asked for both sizes, and it is **not** deployed. (Its
max error 0.436 DN is below the 0.5 DN that would usually change a rounded byte, so a
casual look would call it "the same image" — the registered bound is what decides, and it
fails it.)

### The export decision that mattered

`torch.onnx.export` calls `model.eval()` by default. The generator is built with
`--norm batch` and `test.py` never calls `eval()`, so **every number this project has
measured used BatchNorm batch statistics**. Exporting the default way would have switched
it to running statistics — measured on the C3 checkpoint as **mean 32 DN, max 94 DN,
affecting 100% of pixels**. That is a plugin that silently generates different images from
the ones the evaluation phase scored.

At batch size 1, BatchNorm2d in train mode is exactly InstanceNorm2d with the same affine
parameters (**verified: max abs diff 0.0**), so each BatchNorm2d is replaced by that
equivalent before export. The shipped graph reproduces the evaluated path and is
deterministic, because instance statistics depend only on the input.

---

## Gate D — determinism

**Registered prediction:** deterministic inference leaves the residual statistically
unchanged (within 0.05 px), and if anything is very slightly better, because disabling the
noise source suppresses invented structure.

**Arms.** (1) seeded stochastic — the evaluated path, from Registration A's committed
per-chip CSV, not re-run. (2) dropout-off, batch-statistics BatchNorm — the current tool
default, also from Registration A. (3) **dropout-off + `--eval` (running-statistics
BatchNorm)** — what this work package asked for, and the arm Registration A deliberately
did not measure. Plus `det_onnx`, a **control**: arm 2 re-run through the new ONNX harness.

30 task3 production-input Ankara chips, arms C3 and C2, KARIOS config unchanged, warp
geometry asserted equal to Registration A's own artifact.

### Control — the harness reproduces the recorded path

| arm | Δ (det_onnx − regA det) | verdict |
|---|---|---|
| C3 | **+0.0203 ± 0.0611 px** (SE 0.0112, n=30) | indistinguishable |
| C2 | **+0.0021 ± 0.0194 px** (SE 0.0035, n=30) | indistinguishable |

The control is what makes the rest of this section quotable, and it earned its place — see
the disclosed error below.

### Results, Δ = candidate − baseline, negative = candidate better

| arm | comparison | Δ (px) | SE | t | band |
|---|---|---|---|---|---|
| C3 | regA det − seeded *(recorded)* | −0.0280 ± 0.3855 | 0.0704 | −0.40 | indistinguishable |
| C3 | **evalbn − seeded** | **−0.0561 ± 0.4607** | 0.0841 | −0.67 | documented difference |
| C3 | evalbn − det (tool default) | −0.0281 ± 0.6332 | 0.1156 | −0.24 | indistinguishable |
| C2 | regA det − seeded *(recorded)* | −0.0210 ± 0.5022 | 0.0917 | −0.23 | indistinguishable |
| C2 | **evalbn − seeded** | **−0.2588 ± 0.4988** | 0.0911 | −2.84 | **materially different** |
| C2 | evalbn − det (tool default) | −0.2378 ± 0.5536 | 0.1011 | −2.35 | **materially different** |

**Verdict against the registered decision rule: eval-mode is NOT worse.** On C3 it is
indistinguishable-to-slightly-better; on C2 it is materially **better** by ~0.24–0.26 px.
The registered rule says that when deterministic is not worse we keep it, so nothing is
referred back to the institution as a penalty decision.

**Caveat that must travel with these numbers — the comparison is not on a common support.**
Point counts differ systematically: median points per chip drop from 60 to 50 (C3) and from
61 to 48 (C2) under eval-mode BatchNorm, about 20% fewer. A median residual computed over a
*smaller, differently selected* point set is not a strictly paired comparison of the same
points, and lower residual over fewer points is exactly what a selection effect would look
like. This project has already established that point-count asymmetry is not benign (the
common-support re-scoring work). **The C2 advantage is therefore reported as measured, and
is not claimed as a proven accuracy gain.**

**What the plugin ships, and why it is the conservative choice.** Both candidates are
deterministic, so determinism does not decide between them. Batch-statistics BatchNorm
**reproduces the evaluated path** (control: +0.002 to +0.020 px) — every number this project
has published applies to it unchanged. Eval-mode BatchNorm is a different output
distribution whose apparent advantage rests on a non-common support. So the plugin
**defaults to batch-statistics BatchNorm**, and the eval-mode model is exported, measured
and available. Following registration D's adoption discipline, a switch of default is
**reported first, not changed in the same step**.

### Disclosed error — the control caught a wrong reference

The first Gate D run used `tubitak/data/ankara/run/arms/<stem>.tif` as the KARIOS
reference. **That directory holds a warped generated arm, not a reference** — it differs
from the warped satellite reference by mean 53.8 DN over 100% of pixels. The control fired
immediately (det_onnx − regA det = **−0.44 px**, materially different), and under that wrong
reference the eval-mode arm looked materially **worse** (+0.42 px on C3, +0.77 px on C2) —
the opposite of the corrected result.

Diagnosis was by elimination, each step ruling out one candidate: the generated images were
byte-equal to Registration A's own warps (max 1 DN); the residual formula reproduced
Registration A's recorded numbers from its own KARIOS output **exactly** (max abs diff
0.0000, point counts equal); the saved KARIOS config was byte-identical to the current one;
the KARIOS install predated Registration A. What remained was the reference, and rebuilding
it the documented way — warping the 257 px satellite reference `ankara/run/ref/<stem>.tif`
onto the same 228 grid, as `build_karios_arms.py` does for its `ref` arm — reproduced
Registration A's recorded value **exactly** (1.940379 px, n = 19 on `ank_0_30`).

Two things follow, and both are recorded rather than tidied away. First, **the sign of this
gate's headline flipped between the wrong and right reference**, so the control was not
ceremony. Second, Registration A's harness was never committed (only its per-chip CSV),
which is why its reference had to be reconstructed by inference at all — an instance of the
class standing practice 22 exists to prevent. The reconstructed harness is committed here
as `tubitak/tests/gate_d_*.py`.
---

## Gate G — georeferencing contract: **PASS (12/12)**

Reference layer `ank_0_30.tif`, EPSG:32636, extent
`(399960.0, 4420330.0, 402530.0, 4422900.0)`. Numbers, not "passed":

### A. Grid alignment

| assertion | measured | verdict |
|---|---|---|
| output CRS == reference CRS | EPSG:32636 == EPSG:32636 | PASS |
| pixel size == 10.0 m, both axes | x = `10.0`, y = `10.0` (exact float equality) | PASS |
| NW corner == reference NW corner | origin offset **x 0.0 m, y 0.0 m** (0.0 px, 0.0 px) | PASS |
| size == ceil(span / GSD) | 257 × 257, expected 257 × 257 (span 2570.0 × 2570.0 m) | PASS |
| E/S overhang within one pixel | east **0.000000 m**, south **0.000000 m** (rule permits [0, 10)) | PASS |
| transform term by term | `(10.0, 0.0, 399960.0, 0.0, -10.0, 4422900.0)` both | PASS |
| grid is an integer offset of the reference grid | fractional part **x 0.0, y 0.0** | PASS |

### B. Content placement (sub-pixel)

| assertion | measured | verdict |
|---|---|---|
| mosaic == independent corrected-affine warp | max abs difference **0.497043 DN** (uint8 rounding allows 1) | PASS |
| cross-correlation integer peak | lag (dy, dx) = **(0, 0)** over 56,169 px | PASS |
| sub-pixel refined peak within 0.05 px | **dy = +0.000181 px, dx = −0.000013 px** = **+1.8 mm, −0.1 mm** | PASS |

**The snapping rule, restated because the downstream consumer depends on it.** The grid is
anchored at the reference extent's **north-west corner exactly** — not snapped to a multiple
of the GSD — and grows east and south in whole 10 m pixels, so
`width = ceil((xmax−xmin)/10)`, `height = ceil((ymax−ymin)/10)`, transform
`(10.0, 0, xmin_ref, 0, −10.0, ymax_ref)`. The east and south edges may extend up to one
pixel beyond the requested extent. This is embedded verbatim in every output's
`GENCP_PROVENANCE` tag alongside the model SHA-256, the inference path and the corrected
GSD 10.0390625 — 17 fields, so a consumer that finds a GCP wrong can tell exactly what
produced the raster.

**What this gate deliberately does not test.** It does not correlate the synthetic output
against real satellite imagery. How well generated imagery matches a real scene is a
scientific question, already measured by KARIOS at a median residual of roughly 1.9 px, and
it is **not** a georeferencing defect. Mixing the two would have made a georeferencing gate
that fails for reasons unrelated to georeferencing, so content placement is checked against
an independently computed warp of the same generated tile.

---

## Gate S — size table (measured on disk, no estimates)

**Test area:** `(399960.0, 4390200.0, 509760.0, 4500000.0)` in EPSG:32636 —
109.8 km × 109.8 km = **12,056 km²**, stated so the normalisation is checkable.

| item | MB | MB per 1000 km² |
|---|---:|---:|
| ONNX model, fp32 **(deployed)** | **217.68** | n/a |
| ONNX model, fp16 (not deployed — fails Gate O) | 108.86 | n/a |
| `onnxruntime` installed footprint | 82.72 | n/a |
| OSM subset, `.osm.pbf` cut with `-s smart` | 23.41 | **1.94** |
| CLC+ clip, deflate GeoTIFF | 16.22 | **1.35** |

**Fixed cost, independent of coverage: 300.4 MB** (fp32 model + onnxruntime).
**Per-area data: 3.3 MB per 1000 km².**

| coverage | total |
|---|---|
| the 12,056 km² test area | **340 MB** |
| Ankara province (~25,600 km²) | 385 MB |
| all of Turkey (~783,600 km²) | 2,877 MB |

Two things this table does *not* say, stated so the number is not misread:

- The CLC+ row is the size of a **clip for the area**, not of the 8.2 GB continental CLC+
  Backbone source. The plugin window-reads that source and never ships it. **CLC+ Backbone
  covers Europe only**, which matters for any Turkish coverage east of its extent.
- Data is measured **in the format the plugin actually consumes** — a `-s smart` `.osm.pbf`
  and a windowed CLC+ clip — not as an intermediate or a database export.

**Short answer for Mustafa Bey:** about **300 MB fixed** (model plus runtime), plus roughly
**3.3 MB per 1000 km²** of coverage. Ankara province lands near 385 MB; the whole of Turkey
would be about 2.9 GB.

---

## Step 4 — plugin shell: built and **executed** in real QGIS (25/25 checks)

Because headless QGIS works here, the dialog was **run**, not just written. The harness
(`tubitak/tests/test_plugin_headless.py`, driven by `tubitak/tests/run_in_qgis.sh`)
constructs the real `QDialog`, drives the real widgets and runs a real `QgsTask` through
the real task manager inside QGIS 4.2.1.

| section | check | result |
|---|---|---|
| — | `gencp_core` imports inside QGIS's Python | PASS |
| — | **PyTorch is not required** inside QGIS | PASS |
| — | onnxruntime available | PASS (1.29.0) |
| 1 Input | reads and displays extent, CRS, tile count and a time estimate | PASS (extent, `EPSG:32636 — WGS 84 / UTM zone 36N`, 2 tiles) |
| 2 Data source | **blocks** until the source is resolved; unblocks when it is | PASS (both directions) |
| 3 Preview | renders the rasterised input on screen | PASS (384 px, 5.5 s) |
| 3 Preview | not reduced to a thumbnail | PASS (384 px) |
| 3 Preview | **generation does not start until the user confirms** | PASS (Run stays disabled with everything else filled in) |
| 4 Model | shows model file name and modification date | PASS (`gencp_C3_fp32.onnx`, modified 2026-08-26 16:27:01) |
| 5 Run | **inference runs OFF the main thread** | **PASS** (verified on the QgsTask worker thread) |
| 5 Run | progress bar advances | PASS |
| 5 Run | cancel stops the task | PASS |
| 6 Output | writes a GeoTIFF to the chosen path | PASS |
| 6 Output | adds the result to the map as a layer | PASS |

**25/25.** The two hard requirements — inference off the main thread, and Preview as a real
gate on generation rather than decoration — are both verified by execution.

The dialog holds no generation logic: every numeric or geometric decision is delegated to
`gencp_core` (`extent` for extents and tile grids, `rasterize` for rendering, `pipeline`
for the run).

### Deployment findings worth carrying forward

1. **macOS code signing splits the two interpreters.** The QGIS **application** executable
   is signed with `com.apple.security.cs.disable-library-validation`; the bundled
   **`python3.12`** executable is **not**. Under the hardened runtime, onnxruntime's and
   pyosmium's native extensions load normally in the QGIS process the plugin runs in, and
   are refused in `python3.12` with *"different Team IDs"*. Testing through `python3.12`
   reports a failure that does not exist in deployment. `run_in_qgis.sh` drives the app
   binary for this reason.
2. **Dependencies QGIS does not already have:** `onnxruntime` (required) and `osmium`
   (only for the local `.osm.pbf` source); `osmnx` only for Overpass. Everything else the
   chain needs — numpy, GDAL, rasterio, PIL, scipy, shapely, geopandas, pyproj — already
   ships inside QGIS 4.2.1.
3. **QGIS 4 is PyQt6, QGIS 3 is PyQt5**, and Qt6 removed the flat enum names
   (`Qt.AlignCenter` → `Qt.AlignmentFlag.AlignCenter`). `qgis_plugin/qtcompat.py` resolves
   enum members either way so the plugin runs on both.
