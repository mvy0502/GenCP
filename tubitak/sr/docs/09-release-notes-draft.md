# DRAFT release notes — not published

**Nothing has been published.** This file shows exactly what a release would contain so the
decision can be made on the actual content. Publishing is Vedat's call.

| | |
|---|---|
| **repository** | `mvy0502/gencp-validation` — the convention the existing `plugin-v0.2.0` and `clcplus-turkey-2026-08-30` releases already follow |
| **tag** | **`sr-plugin-v0.1.0`** — `version=0.1.0` in `sr_plugin/metadata.txt`, prefixed `sr-` to keep it distinct from Project 1's `plugin-v*` |
| **title** | GenCP Super-Resolution 0.1.0 — QGIS plugin and models |

## Attachments

| file | size | sha256 |
|---|---|---|
| `gencp_super_resolution.zip` | 49,379 B | `59b72bb9d6004c4d9c089658fe215bc3f771f628a7a3e120ca8d685ac17bf962` |
| `gencp_sr_x2_v1.onnx` | 1,964,122 B | `3fcb34a2ff5e07f00aefe426f08e3f60243388270bbcbd8e11749f25b0375ef7` |
| `gencp_sr_x4_b4.onnx` | 2,086,466 B | `f3f2ffbde52c92eff81b0741b6c180e9d4a5a117fbd91ac5eaa77c789f0ad4ba` |

**wsx4 is deliberately NOT attached.** It is not this project's work. See "The third method"
below.

---

## Release body (draft)

### GenCP Super-Resolution 0.1.0

A QGIS plugin that super-resolves Sentinel-2 imagery onto the exact integer refinement of its
own grid, with three methods: **bicubic** (a control, needs no model and no `onnxruntime`),
**GenCP SR** (the models attached here), and **wsx4** (the Evoland/CESBIO reference model,
hosted but not shipped).

Output geometry is asserted rather than assumed. **Gate S** requires the output CRS to equal
the input's, the pixel size to be exactly the input's divided by the scale, the origin to be
unchanged, and each source pixel centre to fall at the centre of its output block.

#### Install

1. Download `gencp_super_resolution.zip`.
2. QGIS: **Plugins → Manage and Install Plugins → Install from ZIP**.
3. For the model methods, `onnxruntime` must be importable from QGIS's Python. The bicubic
   path deliberately does not import it, so the plugin loads and completes a job without it.

Verified on **QGIS 4.2.1, macOS**, installed from this zip into a throwaway profile with no
access to the source tree: QGIS discovered, loaded and started the plugin, and bicubic ran end
to end with the Gate S contract holding exactly. **QGIS 3.x is written for but has never been
run. Windows is untested.**

#### The models

| | `gencp_sr_x2_v1.onnx` | `gencp_sr_x4_b4.onnx` |
|---|---|---|
| scale | 2 | 4 |
| bands | B02, B03, B04 | B02, B03, B04, B08 |
| normalisation | `DN / 5000` | `DN / 10000` |
| training | 16,306 of a registered 20,000 steps, stopped on wall-clock budget | **20,000 of 20,000**, `stop_reason = steps` |
| seed | 20260831 | 20260831 |
| opset | 17 | 17 |

Both carry their provenance inside the graph, in ONNX `metadata_props`: corpus and split
registrations, band order, normalisation divisor, the registered schedule beside what actually
ran, the training seed, library versions, and the scope caveat. **A model whose step count
differs from its registered schedule is a different model, not a noisier one**, and the graph
says which it is.

#### What has been measured, with its scope

On the **held-out granule 36SXJ** (1332 chips, in no training set in any work package):

- **Pixel fidelity**, scale 4, four bands, in `DN/10000`, paired per chip against a registered
  bicubic control: **+2.971 dB PSNR**, worse on 1 chip in 1332. The scale-2 model's **+5.574 dB**
  is in `DN/5000` on a different task and **the two must not be compared**.
- **Matching**, the reason this exists: real 10 m Sentinel-2 degraded to 40 m and restored,
  matched against the real 10 m with this project's own KLT detector and parameters —
  **the model yields 3.8x bicubic's usable control points** (478.6 against 126.9 RANSAC inliers
  per chip) and halves the correspondence error (0.605 px against 0.972 px).

**Every number above is 40 m → 10 m on one granule, one band (B04), one detector.** The plugin
in normal use performs 10 m → 5 m or 10 m → 2.5 m, where no ground truth exists to measure
against. Beating bicubic at inverting a blur we applied ourselves is not the same claim as
super-resolving real imagery.

#### The third method: wsx4 is hosted, not shipped

The plugin can run the Evoland/CESBIO **wsx4** model, which is **not this project's work and is
not attached here.**

To use it, download from the upstream project — **https://github.com/IGNF/sentinel2_superresolution**
— both files:

- `wsx4_spatrad.onnx`
- `wsx4_spatrad.yaml`

and place them **in the same directory as each other**, anywhere on disk. The plugin reads the
`.yaml` sitting beside the model for the scale, normalisation and crop margin, because the
wsx4 graph carries no embedded provenance. Then select the file in the plugin's model field.

`PyYAML` is required only for this, and is checked lazily: without it, bicubic and our own
models still work.

#### How wsx4 was compared, and why the comparison is loaded

wsx4 was run **40 m → 10 m, when it was trained for 10 m → 2.5 m** — outside its domain. This
is unavoidable: the only ground truth in this repository is real Sentinel-2 at 10 m, so any
experiment with a real reference must degrade to 40 m first. **The asymmetry favours our
model** and is stated in the experiment's registration rather than its conclusion. wsx4 was
also re-run with the 130-pixel crop margin its own `.yaml` declares; it improved and no
ranking changed.

#### Known limits

- QGIS 3.x written for, never run. Windows untested. Verified only on QGIS 4.2.1 / macOS.
- Nothing measured at the resolution the tool is actually used at.
- wsx4's output sits about a quarter of an output pixel off our grid convention in the row
  axis; the cause is **not attributed** and the decisive test has not been run.

#### Reports

The full record, including registrations written before measurement and predictions that
failed, is in [`tubitak/sr/docs/`](https://github.com/mvy0502/GenCP/tree/tubitak-tr/tubitak/sr/docs).
