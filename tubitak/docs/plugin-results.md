
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
