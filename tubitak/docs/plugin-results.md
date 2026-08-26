# QGIS plugin work package — results, scored against the registrations

> **Conventions.** Every paired difference is **Δ = candidate − baseline; negative =
> candidate better**. The **inference path is stated for every number**. Registrations:
> [plugin-gate-registrations.md](plugin-gate-registrations.md), committed (`844dbec`)
> before any number below existed.

**Date:** 2026-08-26, branch `tubitak-tr`.

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
