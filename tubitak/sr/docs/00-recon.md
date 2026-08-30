# Project 2, WP0 — reconnaissance and data inventory

**Run:** 2026-08-30, read-only. **Repository:** `/Users/vedat/Documents/GenCP-Generative-Goruntu-Uretimi-OpenStreetMap`,
branch `tubitak-tr`, working tree clean at the start and at the end of this work package.
**Written by this work package:** this file only. Nothing else was created, modified or committed.

Every number below names the file or the command it came from. Where a fact could not be
established it is written as **not determined** with the reason, not filled with a default.

---

## 0. Repository state

| item | value | how established |
|---|---|---|
| root | `/Users/vedat/Documents/GenCP-Generative-Goruntu-Uretimi-OpenStreetMap` | `git rev-parse --show-toplevel` |
| branch | `tubitak-tr` | `git branch --show-current` |
| working tree | clean (`git status --porcelain` produced no output) | `git status --porcelain` |
| `tubitak/sr/` before this WP | did not exist (`ls: No such file or directory`) | `ls -la tubitak/sr` |

Last six commits (`git log --oneline -6`):

```
6c0eb65 docs: publish Turkey CLC+, document the zero-account route, write the handover
9141da2 perf+fix: cache the OSM index, split the estimate, and enforce the metric assumption
042c781 fix: the coverage warning never fired, because 300 metres was added to degrees
19d2a94 feat: one file for all of Turkey - download button, pinned mirror, country default
2261a0d feat: an extract that does not cover the extent now blocks before generation
f94d1fc docs: seam hypothesis refuted, buildings confirmed present, shares corrected
```

---

## 1. Reuse surface

### 1.1 `tubitak/gencp_core/` — classification for a raster-in / raster-out SR pipeline

The classification axis is: **does this function need vectors, land cover, or the 257-px
generation grid?** SR is raster-in / raster-out. Anything that touches OSM, CLC+ or
WorldCover is not applicable. Anything that is pure extent/grid/transform arithmetic is
reusable, but almost all of it is parameterised by module-level constants (`SRC_PX = 257`,
`OUT_PX = 256`, `NOMINAL = 10.0`, `TILE_M = 2570`), so "reusable with a parameter change"
below almost always means *those constants*, which are currently **module globals, not
arguments** — see risk R2.

#### `extent.py` (12,188 bytes, 258 lines)

Module constants, [extent.py:16-27](../../gencp_core/extent.py#L16):

```
SIZE = 257 · GSD = 10.0 · SUPERSAMPLE = 4
SRC_PX = 257 · OUT_PX = 256 · NOMINAL = 10.0
TRUE_GSD = SRC_PX * NOMINAL / OUT_PX = 10.0390625
TILE_M = SRC_PX * NOMINAL = 2570
DEFAULT_OVERLAP_M = 640.0
```

| symbol | line | what it does | SR verdict |
|---|---|---|---|
| `class ExtentError(ValueError)` | 30 | Raised when a requested extent or CRS cannot be used. | **reusable unchanged** |
| `utm_for(lon, lat) -> str` | 34 | UTM CRS whose zone contains a lon/lat, as an EPSG authority string. | **reusable unchanged** |
| `validate_bbox(bbox)` | 40 | Checks a 4-tuple is well-formed and non-degenerate; returns floats. | **reusable unchanged** |
| `_crs_name(c)` | 68 | Human name for a CRS, whatever binding is available. (private) | reusable unchanged |
| `_transform_points(src, dst, xs, ys)` | 86 | Coordinate transform; thread-safe inside QGIS (pyproj is not). (private) | **reusable unchanged** — the thread-safety reason applies identically to an SR QgsTask |
| `classify_crs(crs) -> (kind, detail)` | 94 | Decides how a requested CRS must be treated. | **reusable unchanged** |
| `resolve(bbox, crs)` | 147 | Resolves a requested extent to a metric working CRS; reprojects geographic CRSs to the extent-centre UTM zone. | **reusable unchanged** |
| `output_grid(extent)` | 168 | The output raster grid under the registered snapping rule (NW-anchored, `ceil(span/NOMINAL)`). Returns `(width, height, Affine)`. | **reusable with a parameter change** — `NOMINAL`. SR output is 5 m, so this must produce a 5 m transform. `NOMINAL` is read from module scope, not passed. |
| `tile_grid(extent, overlap_m=640.0, align_origin=None)` | 185 | Lays out generation tiles, `TILE_M` square, stepping by `TILE_M - overlap_m`. | **reusable with a parameter change** — `TILE_M`. An SR net's tile is its own patch size, not 2570 m. `align_origin` is already an argument and is exactly the hook needed to make an SR tile coincide with a Wald chip footprint. |
| `index_cost(pbf_path=None, cached=False)` | 240 | Seconds for the one-time vector index step. | **not applicable** — vector-only |
| `estimate(extent, overlap_m, sec_per_tile=None, pbf_path=None, index_cached=False)` | 255 | Tile count, output size, wall clock, split into one-time and per-tile terms. | **reusable with a parameter change** — the *shape* (split estimate) transfers; the constants `SEC_PER_TILE = 0.48` (line 228) and `INDEX_PARSE_SEC` (233) are Project-1 measurements and must be re-measured, not inherited. |

#### `vectors.py` (17,794 bytes)

| symbol | line | what it does | SR verdict |
|---|---|---|---|
| `require_metric(crs, who)` | 32 | Refuses a CRS whose units are not metres where metres are about to be assumed. | **reusable unchanged** — and it should be used. `CLAUDE.md` records four metre-as-degree bugs; SR adds new metre arithmetic. |
| `clc_path(explicit=None)` | 62 | Resolves the CLC+ raster (arg → `GENCP_CLC_PATH` → default). | **not applicable** |
| `fetch_clcplus(bounds_utm, crs, clc_path_override=None)` | 73 | CLC+ classes on the supersample grid. | **not applicable** |
| `wc_tiles(lonlat_bounds)` | 94 | SW-corner names of the 3° WorldCover tiles covering a bbox. | **not applicable** |
| `fetch_worldcover(bounds_utm, crs)` | 106 | WorldCover classes on the supersample grid. | **not applicable** |
| `_margin_bbox(bounds_utm, crs)` | 137 | Tile footprint plus `MARGIN_M = 300` in EPSG:4326. | **not applicable** (also the site of one of the four metre-as-degree bugs, fixed in `042c781`) |
| `_pbf_rows(pbf_path, bbox=None)` | 156 | Every KEEP-tagged feature in an extract, as dict rows. | **not applicable** |
| `pbf_header_bounds(pbf_path)` | 230 | The extract's declared bbox, instant, no parse. | **not applicable** |
| `pbf_coverage(pbf_path, bbox_4326)` | 252 | Features intersecting a bbox, without geopandas. | **not applicable** |
| `class PbfIndex` (`__init__`, `__len__`, `query`) | 285 | Read a `.osm.pbf` once per run, answer per-tile queries from memory. | **not applicable** — but see note below |
| `fetch_pbf(bounds_utm, crs, pbf_path)` | 372 | OSM features for a UTM footprint from a local extract. | **not applicable** |
| `fetch(bounds_utm, crs, cache_folder=None)` | 388 | OSM features from Overpass via osmnx. | **not applicable** |

**Note on `PbfIndex`.** The *class* is not applicable, but the *pattern* it embodies —
read the expensive source once for a whole run, serve per-tile windows from memory,
content-address the cache — is the single largest performance lesson of Project 1
(measured 37× on the Turkey extract, `9141da2`). An SR pipeline reading a 10980×10980
granule per tile would repeat the mistake it fixed.

#### `rasterize.py` (8,814 bytes)

| symbol | line | what it does | SR verdict |
|---|---|---|---|
| `_hex2rgb(h)` | 29 | Hex colour to RGB tuple. | not applicable |
| `classify(g)` | 64 | Splits a feature frame into paint groups. | **not applicable** |
| `render(bounds_utm, crs, polys, lines, base=None, base_map=None)` | 101 | Paints the OSM+land-cover input chip. | **not applicable** |
| `write(path, arr, bounds_utm, crs)` | 147 | Writes a rendered array as a georeferenced chip. | **reusable with a parameter change** — it is a thin `rasterio` write of an array over a UTM footprint; the parameter is the pixel size implied by `bounds_utm` and `arr.shape`. Small enough that rewriting is as cheap as adapting. |
| `make_chip(bounds_utm, crs, out_path, gdf=None, use_worldcover=True, pbf=None, base_product=None, stats=None)` | 157 | Whole input-chip production. | **not applicable** |

Module constants `BLEND_SIGMA = 0.6` (26), `ROAD_W` (45), `WC_MAP` (51), `CLC_MAP` (58) are all vector/land-cover: not applicable.

#### `infer.py` (6,717 bytes)

This is the most transferable module in the package. Its docstring
([infer.py:1-23](../../gencp_core/infer.py#L1)) states the two reasons, both of which hold
unchanged for SR: QGIS's Python cannot be asked to carry PyTorch, and a delivered tool must
be deterministic.

| symbol | line | what it does | SR verdict |
|---|---|---|---|
| `INPUT_PX = 256`, `MEAN, STD = 0.5, 0.5` | 27-28 | Network input size and normalisation. | constants, see below |
| `preprocess(img)` | 31 | PIL image (any size) → NCHW float32 in [-1,1]. Reproduces `data/base_dataset.get_transform` under `--load_size 256 --crop_size 256`: bicubic resize to 256, `/255`, `(x-0.5)/0.5`. | **reusable with a parameter change** — `INPUT_PX`. The **resize is the problem**: it is correct for pix2pix, where a 257 px render is resized to 256. An SR network must not resize its input, because the resize *is* the resampling the network is supposed to learn. For SR this function must become a no-resize path or take an explicit `resize=False`. |
| `postprocess(y)` | 43 | NCHW [-1,1] → HWC uint8, matching `util.util.tensor2im`. | **reusable unchanged** |
| `class OnnxGenerator` | 50 | Loaded ONNX session. `providers=["CPUExecutionProvider"]` is pinned deliberately (line 63-65: "the plugin must not silently pick up a GPU provider whose kernels would move the numbers off the gated ones"). `.is_fp16`, `.run_tensor`, `.run_image`, `.run_path`. | **reusable unchanged** — model-agnostic; it reads input/output names from the graph |
| `generate_tiles(model, tile_paths, progress=None, cancelled=None)` | 88 | Runs every tile through the model, with progress and cancellation. | **reusable unchanged** |
| `class StochasticOnnxGenerator` | 106 | N dropout draws for the confidence spread term (`._masks`, `.spread`). | **reusable with a parameter change** — the mechanism is model-agnostic, but the *calibration* is not: the confidence bands were measured on one Project-1 model. Reusing the class without re-measuring would carry a band that means nothing. |

#### `mosaic.py` (14,060 bytes)

| symbol | line | what it does | SR verdict |
|---|---|---|---|
| `feather_weight(overlap_px, size=OUT_PX)` | 29 | Separable raised-cosine ramp over the overlap margin, 1.0 in the interior. | **reusable with a parameter change** — `size` is already an argument defaulting to `OUT_PX`; pass the SR tile size |
| `build(tiles, fakes, work_crs, extent, overlap_m, progress=None)` | 40 | Blends generated tiles onto the output grid via `reproject` with the corrected affine. | **reusable with a parameter change** — `TRUE_GSD` and `output_grid` are imported at module scope ([mosaic.py:26](../../gencp_core/mosaic.py#L26)) and hard-wired at line 62 (`src_T = Affine(TRUE_GSD, 0, tx, 0, -TRUE_GSD, ty)`, commented "THE CORRECTED TRANSFORM — hard-wired; no 10.0 m tile path exists"). For SR both the source GSD and the target GSD change. |
| `write_qml_sidecar(tif_path)` | 105 | Writes `<output>.qml` so QGIS draws RGB, not a blend, on a 4-band output. | **reusable unchanged** |
| `write_qml_if_alpha(tif_path)` | 127 | Writes the sidecar only if the file carries an alpha band. | **reusable unchanged** |
| `write_geotiff(path, rgb, crs, transform, provenance=None, alpha=None)` | 146 | Writes the mosaic in its native metric CRS; never reprojects. Embeds a `GENCP_PROVENANCE` tag. | **reusable unchanged** |
| `reproject_geotiff(src_path, out_path, dst_crs, provenance=None)` | 196 | Reprojects a written mosaic; leaves the source alone. | **reusable unchanged** |
| `write_osm_mosaic(path, render_paths, provenance=None)` | 234 | Mosaics the rasterised OSM inputs so the preview survives as a layer. | **not applicable** |
| `seam_metric(rgb, transform, tiles)` | 262 | Gradient energy in ±2 px buffers around interior tile edges vs elsewhere. | **reusable unchanged** — seam measurement is generic to tiled generation, and SR will tile |
| `write_band_geotiff(path, bands, crs, transform, provenance=None, colours=None)` | 295 | Single-band uint8 raster with a colour table. | **reusable unchanged** |

**Summary count.** 17 reusable unchanged, 8 reusable with a named parameter change, 17 not
applicable, across the 42 symbols tabulated above (37 public plus 5 private helpers).

### 1.2 `tubitak/qgis_plugin/`

Contents: `dialog.py` (1158 lines), `task.py` (69), `download_task.py` (47),
`plugin.py` (65), `qtcompat.py` (27), `strings.py` (97 `S` keys + 21 `TIP` keys),
`__init__.py` (11), plus `metadata.txt`, `icon.png`, `README.md`, `QUICKSTART.md`.

| file / symbol | line | what it does | SR verdict |
|---|---|---|---|
| `plugin.py::ensure_core_importable()` | 13 | Makes `gencp_core` importable from inside QGIS by inserting candidate paths into `sys.path` (lines 22-23). | **reusable unchanged** — this is the whole import bootstrap and it is 15 lines |
| `plugin.py::GenCPPlugin` (`initGui`, `unload`, `run`) | 28 | Menu/toolbar action lifecycle. | **reusable unchanged** as a template (names change) |
| `qtcompat.py::member(cls, name)` | 16 | Returns an enum member Qt5-flat or Qt6-scoped, so one codebase runs on QGIS 3 (PyQt5) and QGIS 4 (PyQt6). | **reusable unchanged** |
| `task.py::GenerateTask(QgsTask)` | 26 | Runs the chain off the main thread. `STAGE_WEIGHTS = {'render':0.8,'infer':0.06,'confidence':0.06,'mosaic':0.08}` (22) and `STAGE_START` (23) map stage progress onto one bar. | **reusable with a parameter change** — the class is 69 lines and generic; `STAGE_WEIGHTS`/`STAGE_START` are Project-1 measurements. SR has no render stage, so these two dicts are wrong by construction and must be re-measured. |
| `download_task.py::DownloadTask(QgsTask)` | 15 | Fetches the country OSM extract off-thread, verified before it is put in place. | **not applicable** as-is; **reusable as a template** if SR ever fetches a granule |
| `strings.py::S`, `TIP`, `t(key, **kw)`, `tip(key)` | 22 / 171 / 236 / 245 | Every user-visible string in Turkish, in one place. Header rule: "Nothing in dialog.py may contain a Turkish literal; a missing string here is the bug." Terminology fixed by `tubitak/docs/terimler.md` against QGIS's own Turkish localisation; decimal comma; "%34" with the sign in front. | **reusable unchanged as a mechanism and a terminology authority**; the 118 entries themselves are Project-1 content and mostly not applicable |
| `dialog.py::OverlapSpinBox(QSpinBox)` | 88 | Tile overlap in metres, constrained to whole multiples of the grid spacing and strictly below one tile — enforced in `validate()` (126) and `fixup()` (145), never silently. Limits read from `gencp_core.extent`, not restated. | **reusable with a parameter change** — constructed at [dialog.py:376](../../qgis_plugin/dialog.py#L376) as `OverlapSpinBox(int(_ext.NOMINAL), _ext.TILE_M)`; pass the SR grid spacing and SR tile size |
| `dialog.py::GenCPDialog` (~50 methods) | 159 | The whole UI. Holds no generation logic: "every numeric or geometric decision is delegated to `gencp_core`" (`tubitak/docs/plugin-results.md`). | mostly **not applicable** (its inputs are OSM/CLC+); **reusable unchanged as structure** — the patterns worth carrying are `_remember`/`_recall` (178/182, project-then-settings-then-default), `_msg` (661, one message-bar line), `_blocker` (957, one next action phrased as the fix), `_invalidate_preview` (809), `_draw_rgb_opaque` (1053), `_style_bands` (1087) |

**Architectural guard.** `tubitak/tests/test_no_qgis_imports.py` asserts by AST that
`gencp_core` never imports `qgis`, `PyQt5`, `PyQt6`, `qgis.PyQt` or `processing`. Its
docstring gives the reason: "the same gencp_core is what would run in an embedded or
offline context later, and it is what makes the whole chain testable without QGIS running."
An SR core should inherit this test.

### 1.3 The Gate G georeferencing contract — the actual assertion code

Source: [`tubitak/tests/gate_g.py`](../../tests/gate_g.py). The gate separates **A. grid
alignment** (exact arithmetic on transforms) from **B. content placement** (cross-correlation
against an independently computed single-tile warp), and its docstring says why keeping them
apart matters. The three assertions asked for, verbatim:

**Output pixel size exact** — [gate_g.py:122-125](../../tests/gate_g.py#L122):

```python
    px, py = o_T.a, -o_T.e
    check("output pixel size == 10.0 m exactly, both axes",
          px == NOMINAL and py == NOMINAL,
          f"x = {px!r} m, y = {py!r} m  (exact float equality against {NOMINAL!r})")
```

Note this is `==` on floats, deliberately: the detail string says "exact float equality".

**Origin offset exactly 0.0 m** — [gate_g.py:127-133](../../tests/gate_g.py#L127):

```python
    exp_w, exp_h, exp_T = gext.output_grid(ref_extent)
    dx0 = o_T.c - ref_extent[0]
    dy0 = o_T.f - ref_extent[3]
    check("output NW corner == reference NW corner (snapping rule)",
          dx0 == 0.0 and dy0 == 0.0,
          f"origin offset  x {dx0!r} m, y {dy0!r} m  "
          f"(= {dx0/NOMINAL!r} px, {dy0/NOMINAL!r} px)")
```

**Sub-pixel offset** — [gate_g.py:222-236](../../tests/gate_g.py#L222). The tolerance
asserted is 0.05 px; **0.0002 px is the measured result, not the bound**:

```python
    A = np.where(m, a - a[m].mean(), 0.0)
    B = np.where(m, b_ - b_[m].mean(), 0.0)
    F = np.fft.rfft2(A) * np.conj(np.fft.rfft2(B))
    corr = np.fft.irfft2(F, s=A.shape)
    corr = np.fft.fftshift(corr)
    c0 = (A.shape[0] // 2, A.shape[1] // 2)
    win = corr[c0[0]-4:c0[0]+5, c0[1]-4:c0[1]+5]
    k, (sy, sx) = subpixel_peak(win)
    lag = (k[0] - 4, k[1] - 4)
    check("cross-correlation peaks at integer lag (0, 0)",
          lag == (0, 0), f"integer peak at lag (dy, dx) = {lag}")
    check("sub-pixel refined peak within 0.05 px of the origin",
          abs(sy) <= 0.05 and abs(sx) <= 0.05,
          f"sub-pixel offset dy = {sy:+.6f} px, dx = {sx:+.6f} px "
          f"(= {sy*NOMINAL:+.4f} m, {sx*NOMINAL:+.4f} m)")
```

Two further parts of the contract that an SR plugin must also preserve — the snapping rule
and the transform, [gate_g.py:134-154](../../tests/gate_g.py#L134):

```python
    check("output size == ceil(span / GSD)", (o_w, o_h) == (exp_w, exp_h), ...)
    over_e = ob.right - ref_extent[2]
    over_s = ref_extent[1] - ob.bottom
    check("E/S overhang within one pixel, as the rule allows",
          0 <= over_e < NOMINAL + 1e-9 and 0 <= over_s < NOMINAL + 1e-9, ...)
    check("transform == the registered affine, term by term",
          tuple(o_T)[:6] == tuple(exp_T)[:6], ...)
    cx = (o_T.c - ref_T.c) / ref_T.a
    cy = (o_T.f - ref_T.f) / (-ref_T.e)
    check("output pixel grid is an integer offset of the reference grid",
          float(cx).is_integer() and float(cy).is_integer(), ...)
```

**Recorded outcome** (path: `tubitak/data/plugin_gates/gate_g/gate_g_results.json`, 12/12 True):

| assertion | recorded detail |
|---|---|
| pixel size | `x = 10.0 m, y = 10.0 m` |
| origin offset | `x 0.0 m, y 0.0 m  (= 0.0 px, 0.0 px)` |
| size | `got 257 x 257, expected 257 x 257 (span 2570.0 x 2570.0 m)` |
| E/S overhang | `east 0.000000 m, south 0.000000 m` |
| transform | `(10.0, 0.0, 399960.0, 0.0, -10.0, 4422900.0)`, term-by-term equal |
| grid offset | `x 0.0, y 0.0 (fractional part x 0.0, y 0.0)` |
| single-tile vs independent warp | `max abs difference 0.497043 DN (uint8 rounding allows 1)` |
| integer lag | `(0, 0)`, over `56169 px compared` |
| **sub-pixel** | **`dy = +0.000181 px, dx = -0.000013 px (= +0.0018 m, -0.0001 m)`** |

**Two properties of this gate worth carrying into SR.** First, it refuses arguments it does
not understand (`strict_argv(known=('--overlap=',), positional=0)`,
[gate_g.py:43](../../tests/gate_g.py#L43)) — the project found 18 of 23 verifiers exiting 0
on degenerate invocations. Second, at line 205 it distinguishes **NOT MEASURED** from
**PASS**: past a certain overlap tile 0 has zero exclusive pixels and part B is undefined,
so the gate returns exit code 3 and says so rather than reporting a pass for a measurement
it did not make.

**Assertion the SR gate will need that this one does not have.** Gate G asserts the output
pixel size equals the *input* nominal 10 m. An SR output is 5 m. The equivalent SR assertion
is `px == 5.0 and py == 5.0` **and** that the 5 m grid is an exact integer refinement of the
10 m source grid — otherwise the sub-pixel offset check inherits a half-pixel bias from the
2× refinement itself. That second half has no Project-1 analogue and must be written new.

### 1.4 Importing `onnxruntime` inside QGIS's Python on macOS

The mechanism, reproducible:

1. **There is no code doing anything special.** `gencp_core/infer.py` does a plain
   `import onnxruntime as ort` inside `OnnxGenerator.__init__`
   ([infer.py:54](../../gencp_core/infer.py#L54)) and `StochasticOnnxGenerator.__init__`
   (line 120). The import is deferred into the constructor rather than at module scope, so
   importing `gencp_core` does not require onnxruntime to be present.
2. **The wheel is installed into QGIS's own interpreter**, documented in
   `tubitak/qgis_plugin/QUICKSTART.md:144-166`. Get the path from
   **Eklentiler > Python Konsolu** with `import sys; print(sys.executable)`, then:

   ```bash
   /Applications/QGIS.app/Contents/MacOS/bin/python3 -m pip install onnxruntime
   ```

   Restart QGIS afterwards. `osmium` is also needed if a local `.osm.pbf` is used.
3. **The code-signing split is the non-obvious part**, documented at
   `tubitak/docs/plugin-results.md:686-691` and restated in
   `tubitak/tests/run_in_qgis.sh:4-8`:

   > The QGIS **application** executable is signed with
   > `com.apple.security.cs.disable-library-validation`; the bundled **`python3.12`**
   > executable is **not**. Under the hardened runtime, onnxruntime's and pyosmium's native
   > extensions load normally in the QGIS process the plugin runs in, and are refused in
   > `python3.12` with *"different Team IDs"*. Testing through `python3.12` reports a
   > failure that does not exist in deployment.

4. **Therefore all in-QGIS testing goes through the app binary**, not the bundled
   interpreter. `tubitak/tests/run_in_qgis.sh` does this: it resolves the app binary
   (`ls "$APP/Contents/MacOS/" | grep -E '^QGIS' | head -1`), sets
   `QT_QPA_PLATFORM=offscreen` (macOS has no X server, so this replaces Xvfb), and runs
   `"$APP/Contents/MacOS/$BIN" --nologo --code "$@"`, polling for up to 1800 s and reading
   results back from `$GENCP_TEST_OUT`.

**Verified in this work package, both directions.** Running the same probe script two ways:

- through the app binary via `run_in_qgis.sh` → `onnxruntime 1.29.0`,
  `providers=['CoreMLExecutionProvider','AzureExecutionProvider','CPUExecutionProvider']`,
  `python 3.12.11`, `qgis.core 4.2.1-Belém do Pará`. **Import succeeds.**
- through `/Applications/QGIS-final-4_2_1.app/Contents/MacOS/python3.12` directly → the
  interpreter does not even reach the import: `Fatal Python error: init_fs_encoding: failed
  to get the Python codec of the filesystem encoding / ModuleNotFoundError: No module named
  'encodings'`, because `sys.prefix` still points at the CI build path
  `/Users/runner/work/QGIS/QGIS/build/vcpkg_installed/arm64-osx-dynamic-release`.

  **This is a different failure from the documented one.** The documented symptom is
  "different Team IDs" at native-extension load; what was reproduced today is that the
  bundled interpreter will not bootstrap standalone at all without `PYTHONHOME` set. The
  operational conclusion is the same and stronger — do not test through `python3.12` — but
  the specific Team-ID error was **not reproduced** in this work package and is reported
  here on the authority of `plugin-results.md`, not on a measurement made today.

*What a failing case would have looked like:* the app-binary probe writing
`onnxruntime ABSENT (ImportError: ... different Team IDs ...)` into `$GENCP_TEST_OUT`. The
probe distinguishes present from absent per module and did report `torch ABSENT
(ModuleNotFoundError)` in the same run, so the check can and did discriminate.

### 1.5 Tiling and overlap-blending parameters in use

| parameter | value | file:line |
|---|---|---|
| tile ground footprint `TILE_M` | 2570.0 m | [gencp_core/extent.py:25](../../gencp_core/extent.py#L25) (`SRC_PX * NOMINAL`) |
| tile input pixels `SRC_PX` | 257 | [extent.py:21](../../gencp_core/extent.py#L21) |
| tile output pixels `OUT_PX` | 256 | [extent.py:22](../../gencp_core/extent.py#L22) |
| network input `INPUT_PX` | 256 | [gencp_core/infer.py:27](../../gencp_core/infer.py#L27) |
| output grid spacing `NOMINAL` | 10.0 m | [extent.py:23](../../gencp_core/extent.py#L23) |
| true tile GSD `TRUE_GSD` | 10.0390625 m (`257*10/256`) | [extent.py:24](../../gencp_core/extent.py#L24) |
| default overlap `DEFAULT_OVERLAP_M` | 640.0 m | [extent.py:27](../../gencp_core/extent.py#L27) — comment: "measured default: seam ratio 1.008, no point clustering" |
| UI default overlap | 640 | [qgis_plugin/dialog.py:86](../../qgis_plugin/dialog.py#L86), set at [dialog.py:377](../../qgis_plugin/dialog.py#L377) |
| overlap legal range | `[0, 2570)`, whole multiples of 10 m | enforced in [dialog.py:126-157](../../qgis_plugin/dialog.py#L126) and [extent.py:200-202](../../gencp_core/extent.py#L200) |
| stride | `TILE_M - overlap_m` = 1930 m at the default | [extent.py:203](../../gencp_core/extent.py#L203) |
| overlap in pixels | `int(round(overlap_m / TRUE_GSD))` = 64 px at 640 m | [mosaic.py:53](../../gencp_core/mosaic.py#L53) |
| **blend function** | separable raised cosine, `0.5 - 0.5*cos(pi*(arange(r)+0.5)/r)`, ramped over the first and last `r` columns/rows and 1.0 in the interior, made 2-D by outer product | [mosaic.py:29-37](../../gencp_core/mosaic.py#L29) |
| blend accumulation | weighted average: `reproject` weight and `arr*weight` separately, then `acc/wac`; `valid = wac > 1e-6` | [mosaic.py:54-79](../../gencp_core/mosaic.py#L54) |
| supersample for hard edges | `SUPERSAMPLE = 4`, box-averaged down | [extent.py:18](../../gencp_core/extent.py#L18) |
| render blend sigma | `BLEND_SIGMA = 0.6` | [rasterize.py:26](../../gencp_core/rasterize.py#L26) (vector rendering only) |
| stage progress weights | `render 0.8 · infer 0.06 · confidence 0.06 · mosaic 0.08` | [qgis_plugin/task.py:22](../../qgis_plugin/task.py#L22) |
| per-tile cost | `SEC_PER_TILE = 0.48` s (render 0.343 + infer 0.016 + confidence 0.031 + mosaic 0.087) | [extent.py:228](../../gencp_core/extent.py#L228) |

The `align_origin` argument of `tile_grid` ([extent.py:185](../../gencp_core/extent.py#L185))
pins the NW corner of tile (0,0) — "which is what lets a tile be made to coincide exactly
with an existing evaluation chip footprint." That is directly the hook a Wald evaluation
needs.

---

## 2. Sentinel-2 inventory

### 2.1 Search method and its negative result

Four independent sweeps, so that a miss in one would show as a disagreement:

1. `find $HOME -maxdepth 8/10` for `S2*_MSIL*`, `*.SAFE`, `*.jp2`, `*sentinel*`,
   `*MSIL1C*`, `*MSIL2A*`, `*_T3[0-9][A-Z][A-Z]*`, `*_T4[0-9][A-Z][A-Z]*`.
   **Result: zero SAFE products, zero JP2 files, zero S2 product-named files.** The only
   `*sentinel*` hits were a Music library file, a Claude Code hook, and three Python
   `sentinel.py` modules — none imagery.
2. Spotlight (`mdfind`) for `MSIL`, `.SAFE`, `*.jp2`, `S2A_`, `S2B_`. **Zero imagery hits.**
3. `find $HOME -type f -iname "*.tif" -size +50M` (no depth limit). Eight files, listed below.
4. `find $HOME -type f \( -iname "*.tif" -o "*.tiff" -o "*.jp2" -o "*.img" -o "*.nc" -o "*.he5" \) -size +5M`
   grouped by directory, plus a sweep of `/Users/Shared`, `/opt`, `/Library`, `/var`.
   `/Volumes` contains only the boot disk symlink — **no external drives are attached.**

**So: no L1C anywhere, no SAFE archives, no raw band files (B02/B03/B04/B08), no JP2.**
Everything present is a derived 8-bit GeoTIFF. This is the single most consequential finding
in this section — see §3 and risk R1.

### 2.2 The five scenes

All five are **Sentinel-2 L2A TCI** (True Colour Image) plus, for four of them, the matching
**SCL** (Scene Classification Layer). Product level established from
`tubitak/docs/data-sources.md:20` (`S2C_36TVK_20260430_0_L2A`) and
`tubitak/docs/ankara-acquisition.md` for Ankara; for the other four from
`tubitak/docs/phase-cd-preparation.md` and `phase-c-config.md`, which name L2A dates and
cloud percentages. Pixel data presence was verified by reading a 512×512 corner window from
every file (see the read column) — a truncated or stub file would have raised on the read.

| # | path | product | tile | date | bands | dtype | px | CRS | on-disk | read |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `tubitak/data/ankara/TCI_36TVK_20260430.tif` | L2A TCI | 36TVK | 2026-04-30 | 3 (R,G,B) | uint8 | 10 m | EPSG:32636 | 0.357 GB | OK, corner nonzero 0.9996 |
| 2 | `tubitak/data/ankara/SCL_36TVK_20260430.tif` | L2A SCL | 36TVK | 2026-04-30 | 1 | uint8 | 20 m | EPSG:32636 | 0.0047 GB | OK |
| 3 | `tubitak/data/tiles36SVJ/TCI.tif` | L2A TCI | 36SVJ | 2026-04-30 | 3 | uint8 | 10 m | EPSG:32636 | 0.359 GB | OK, 1.0000 |
| 4 | `tubitak/data/tiles36SVJ/SCL.tif` | L2A SCL | 36SVJ | 2026-04-30 | 1 | uint8 | 20 m | EPSG:32636 | 0.0038 GB | OK |
| 5 | `tubitak/data/tiles36SWJ/TCI.tif` | L2A TCI | 36SWJ | 2026-04-30 | 3 | uint8 | 10 m | EPSG:32636 | 0.244 GB | OK, 1.0000 |
| 6 | `tubitak/data/tiles36SWJ/SCL.tif` | L2A SCL | 36SWJ | 2026-04-30 | 1 | uint8 | 20 m | EPSG:32636 | 0.0028 GB | OK |
| 7 | `tubitak/data/tiles36SXJ/TCI.tif` | L2A TCI | 36SXJ | 2026-05-27 | 3 | uint8 | 10 m | EPSG:32636 | 0.363 GB | OK, 1.0000 |
| 8 | `tubitak/data/tiles36SXJ/SCL.tif` | L2A SCL | 36SXJ | 2026-05-27 | 1 | uint8 | 20 m | EPSG:32636 | 0.0041 GB | OK |
| 9 | `tubitak/data/tiles36TUK/TCI.tif` | L2A TCI | 36TUK | 2026-04-30 | 3 | uint8 | 10 m | EPSG:32636 | 0.338 GB | OK, corner 0.0000 (granule-edge nodata; interior verified via SCL) |
| 10 | `tubitak/data/tiles36TUK/SCL.tif` | L2A SCL | 36TUK | 2026-04-30 | 1 | uint8 | 20 m | EPSG:32636 | 0.0043 GB | OK |

Every TCI is 10980 × 10980 px; every SCL is 5490 × 5490 px. All ten are `GTiff`,
`compress=deflate`, `tiled=True`, `nodata=0.0`, no band descriptions, and carry only
`OVR_RESAMPLING_ALG` (`AVERAGE` for TCI, `MODE` for SCL) and `AREA_OR_POINT=Area` as tags —
**no embedded acquisition metadata, no product ID, no cloud-cover tag.** Dates and cloud
figures below therefore come from the docs, not from the files.

Extents (EPSG:32636 / WGS84), all 109.8 × 109.8 km:

| tile | easting | northing | lon | lat | site |
|---|---|---|---|---|---|
| 36TVK | 399960–509760 | 4390200–4500000 | 31.817–33.115 | 39.656–40.651 | **Ankara** (documented, `ankara-acquisition.md`) |
| 36TUK | 300000–409800 | 4390200–4500000 | 30.635–31.949 | 39.638–40.646 | west of Ankara; documented only as position "W" — the place name is **not determined** |
| 36SVJ | 399960–509760 | 4290240–4400040 | 31.832–33.114 | 38.755–39.750 | south of Ankara; documented only as position "S" — the place name is **not determined** |
| 36SWJ | 499980–609780 | 4290240–4400040 | 33.000–34.281 | 38.754–39.750 | **Tuz Gölü** (documented, `phase-cd-preparation.md:92`) |
| 36SXJ | 600000–709800 | 4290240–4400040 | 34.151–35.448 | 38.736–39.744 | **Cappadocia** (documented, `phase-cd-preparation.md:93`) |

Cloud cover (from scene metadata as recorded at acquisition time, **not** re-read from the
files, which carry no such tag):

| tile | scene cloud | source |
|---|---|---|
| 36TVK | 2.04 % | `data-sources.md:20`, `ankara-acquisition.md:32` |
| 36SVJ | 0.0 % | `phase-cd-preparation.md:65` |
| 36SWJ | 1.19 % (elsewhere 1.2 %) | `phase-cd-preparation.md:92` / `:67` |
| 36SXJ | 0.20 % | `phase-cd-preparation.md:93` |
| 36TUK | 2.5 % | `phase-cd-preparation.md:66` |

**Provenance and licence.** Public Copernicus, no institutional imagery. The Ankara scene's
source is recorded as "Element84 Earth Search STAC + the public `sentinel-cogs` S3 bucket —
no registration, no quota" (`ankara-acquisition.md:36`) with an md5 in `data-sources.md:20`.
`tubitak/docs/paper-context-addendum.md:481-482` states: "OSM ODbL · Copernicus Sentinel-2
and CLC+ · GenCP weights CC-BY 4.0. **No institutional imagery was used.**" Nothing found in
this sweep contradicts that.

**Reproducibility gap, reported as not determined.** For the four expansion granules
(36SVJ, 36SWJ, 36SXJ, 36TUK) the repository records the tile, date and cloud percentage but
**no full product ID, no platform (S2A/S2B/S2C), no md5, and no download script.** A grep for
`S2._36SVJ|S2._36SWJ|S2._36SXJ|S2._36TUK` across all of `tubitak/` returns exactly one hit,
and it is a *different* scene (`S2B_36SXJ_20260820_0_L2A` in
`tubitak/data/tool_runs/T1_capp/candidates_meta.json`, an August acquisition, not the May one
in use). `data-sources.md` lists only the Ankara pair. These four cannot be re-fetched
byte-identically from the record as it stands.

**Storage.** All ten S2 files together: **1,681,260,688 bytes = 1.681 GB**
(`ls -l` summed). `tubitak/data/` in total is 104 GB, gitignored at `.gitignore:54`
(`tubitak/data/*`, confirmed with `git check-ignore -v`).

### 2.3 Totals

| | |
|---|---|
| distinct MGRS tiles | **5** (36TVK, 36TUK, 36SVJ, 36SWJ, 36SXJ) |
| distinct acquisition dates | **2** — 2026-04-30 (four tiles) and 2026-05-27 (36SXJ only) |
| total S2 on disk | **1.681 GB** |
| product levels | L2A only; **no L1C present** |
| bands | RGB visual composite only; **no B08/NIR, no 20 m or 60 m bands, no reflectance** |
| CRS | EPSG:32636 for all five, so no cross-zone handling is needed |

### 2.4 Derived products already built on these scenes

Not S2 data, but they exist and bear on §3:

| directory | contents |
|---|---|
| `tubitak/data/{tile}/chip_grid.csv` | 1764 rows each (42×42 grid of 257 px chips), with `nodata`, `cloud_scl`, `snow` fractions per chip |
| `tubitak/data/{tile}/minipbf/` | per-chip osmium-cut `.osm.pbf` extracts — 1763 / 1174 / 1683 / 1400 for 36SVJ / 36SWJ / 36SXJ / 36TUK; Ankara has none (its extracts live elsewhere) |
| `tubitak/data/{tile}/clc_renders/` | 1174–1763 rendered input chips per tile |
| `tubitak/data/{tile}/pairs/`, `ankara/train_pairs/` | 514×257 RGB GeoTIFFs, `[satellite \| OSM+CLC+ render]` side by side — 1763 / 980 / 1400 / 1434 files. **The left half of each is real 10 m S2 imagery already chipped.** |
| `tubitak/data/plugin_models/` | six ONNX generators, 104–208 MB each (C2/C3, fp32/fp16, evalbn, stochastic) |

---

## 3. Wald feasibility verdict

### 3.1 The arithmetic

Two independent paths, reported separately because they were computed differently.

**Path A — the screens Project 1 already computed.** Source:
`tubitak/data/{tile}/chip_grid.csv`, 42×42 = 1764 chips of 257×257 px per tile, screened by
`tubitak/scripts/tile_pipeline.py::valid()` (nodata ≤ 0.005, cloud_scl ≤ 0.01, snow ≤ 0.02):

| tile | rows | valid | rej nodata | rej cloud | rej snow |
|---|---|---|---|---|---|
| 36TVK | 1764 | 1564 | 0 | 180 | 38 |
| 36SVJ | 1764 | 1763 | 0 | 1 | 0 |
| 36SWJ | 1764 | 1174 | 447 | 117 | 51 |
| 36SXJ | 1764 | 1683 | 0 | 80 | 1 |
| 36TUK | 1764 | 1400 | 122 | 239 | 26 |
| **total** | **8820** | **7584** | | | |

**Path B — recomputed here from each scene's own `SCL.tif`, at 256 px.** 10980 // 256 = 42,
so also 42×42 = 1764 windows per tile; each 256 px chip is 128 px on the 20 m SCL grid.
Classes: 0 nodata, {3, 8, 9, 10} shadow/cloud-medium/cloud-high/cirrus, 11 snow. Same
thresholds as Path A.

**The counter was calibrated before its output was used**, per standing practice 11:

```
  all-clear   -> 1764 windows, 1764 valid, rej n/c/s = 0/0/0      (expected all valid)
  all-cloud   -> 1764 windows,    0 valid, rej n/c/s = 0/1764/0   (expected 0 valid)
  all-nodata  -> 1764 windows,    0 valid, rej n/c/s = 1764/0/0   (expected 0 valid)
```

| tile | windows | valid | nodata | cloud | snow | clear % |
|---|---|---|---|---|---|---|
| 36TVK | 1764 | 1568 | 0 | 177 | 19 | 88.9 |
| 36SVJ | 1764 | 1763 | 0 | 1 | 0 | 99.9 |
| 36SWJ | 1764 | 1177 | 440 | 110 | 37 | 66.7 |
| 36SXJ | 1764 | 1687 | 0 | 76 | 1 | 95.6 |
| 36TUK | 1764 | 1398 | 122 | 235 | 9 | 79.3 |
| **total** | **8820** | **7593** | | | | **86.1** |

The two paths agree to 9 chips in 7590 (0.12 %). The difference is explained by the window
size (257 vs 256 px) and by the nodata source (Path A reads TCI RGB == 0, Path B reads
SCL class 0). Either number is usable; the rest of this section uses Path B, since it is the
one computed at the 256 px size the question asks about.

**Path B corrected for granule overlap.** Sentinel-2 granules overlap. Measured footprint
intersections (EPSG:32636, all five scenes in the same zone):

```
  36TVK-36SVJ: 109.80 x  9.84 km = 1,080 km^2
  36TVK-36SWJ:   9.78 x  9.84 km =    96 km^2
  36TVK-36TUK:   9.84 x 109.80 km = 1,080 km^2
  36SVJ-36SWJ:   9.78 x 109.80 km = 1,074 km^2
  36SVJ-36TUK:   9.84 x  9.84 km =    97 km^2
  36SWJ-36SXJ:   9.78 x 109.80 km = 1,074 km^2
```

Dropping any clear chip whose centre falls inside an earlier-listed granule's footprint
(first-come rule, order 36TVK → 36SVJ → 36SWJ → 36SXJ → 36TUK):

```
  36TVK: 1568 clear -> keep 1568, drop   0
  36SVJ: 1763 clear -> keep 1595, drop 168
  36SWJ: 1177 clear -> keep 1009, drop 168
  36SXJ: 1687 clear -> keep 1519, drop 168
  36TUK: 1398 clear -> keep 1299, drop  99
```

### 3.2 The answer

> **Non-overlapping 256×256 chips at 10 m, cut from cloud-free areas of what exists:**
> **7593 raw**, of which **6990 are geographically distinct** once granule overlap is removed.
> Chip area (256 × 10 m)² = 6.5536 km²; distinct clear ground = **45,810 km²**.
>
> **Distinct geographies: 5 MGRS granules, but effectively one region.** All five lie in
> EPSG:32636 between 30.6–35.4 °E and 38.7–40.7 °N, and they tile contiguously: 36SVJ–36SWJ–
> 36SXJ form an east–west strip, with 36TUK–36TVK a second strip directly north. The union is
> a single connected block of the central Anatolian plateau.

### 3.3 Verdict

**Yes for the mechanics; no for the claim the mechanics would support.**

*Yes.* 6990 distinct cloud-free 256 px chips is far more than a Wald 20→10 m experiment
needs. A conventional split — say 5000 train / 1000 val / 990 test — is available today with
no download, no account, and no network. The degradation step (10 m → 20 m by area-average,
then the model recovers 10 m) needs nothing that is not on this disk. The chips are already
in one CRS, one grid, one dtype, and 88 % of them share a single acquisition date, which
holds phenology almost constant. `chip_grid.csv` already carries a per-chip cloud screen, and
`extent.tile_grid(..., align_origin=)` already lets an SR tile be pinned to a chip footprint,
so the evaluation geometry is a solved problem rather than a new one.

*No.* Three limits are structural, and none is fixed by cutting more chips:

1. **The pixels are an 8-bit visual composite, not reflectance.** There is no L1C, no SAFE,
   no B02/B03/B04/B08, no 20 m or 60 m band anywhere on this machine — verified by four
   independent sweeps (§2.1). TCI is a gamma-stretched, clipped, 8-bit rendering of three
   bands. Wald's protocol assumes a physical resolution relationship between scales; a model
   trained to invert a *downsample of an already non-linear, already clipped RGB product*
   learns the statistics of that product, not the sensor's. That is a defensible experiment,
   but it must be stated as "super-resolution of the S2 TCI visual product", never as
   "super-resolution of Sentinel-2 imagery", and the Friday presentation is exactly where
   that distinction gets lost.

2. **One region, two dates, one season.** Central Anatolian plateau, late April / late May
   2026: steppe, dryland agriculture, one salt lake, one karst-badlands area, one city. No
   coastline, no dense forest, no high-relief alpine terrain, no metropolitan area at
   İstanbul density, no winter, no summer, no snow (snow chips are screened *out*). An SR
   model trained on this and applied elsewhere is extrapolating, and Project 1 has already
   measured that this exact corpus generalises unevenly by landform
   (`tubitak/docs/phase-d-results.md`: Cappadocia −0.780 ± 0.093 px on a clean test).

3. **The 10 m → 5 m application step is unvalidatable with what exists.** Wald trains
   20→10 where the target is real, then applies 10→5 where no target exists. Nothing on this
   machine is real imagery finer than 10 m over these footprints. The one sub-10 m raster
   present is `tubitak/data/tool_runs/E3/target_esri_z18.tif` — Esri basemap, a different
   sensor, different radiometry, different date, and (like the Google Earth imagery the
   project rules already restrict) not distributable. So the 5 m output can be assessed for
   *self-consistency* — does downsampling it back to 10 m reproduce the input, does Gate G's
   georeferencing contract hold at 5 m — but **not for accuracy against ground truth**. That
   is a bounded, honest limitation if registered in advance, and a fatal one if discovered
   after the presentation.

### 3.4 If more data were wanted

Nothing needs to be downloaded to start. If the reflectance objection in (1) is to be
removed, the item to fetch is the **L2A 10 m and 20 m band rasters** (B02, B03, B04, B08 at
10 m; B05, B06, B07, B8A, B11, B12 at 20 m) for the five granules already in use, from the
same source already used and documented for Ankara: **Element84 Earth Search STAC over the
public `sentinel-cogs` S3 bucket** — no registration, no quota
(`tubitak/docs/ankara-acquisition.md:36`). Size, estimated from the observed TCI figure:
each 10980² uint16 band is ~241 MB raw, and the observed deflate ratio on TCI is roughly
0.44 (0.244–0.363 GB for three uint8 bands of 120.6 Mpx), so ≈ 0.20–0.25 GB per 10 m band
and ≈ 0.05–0.06 GB per 20 m band compressed. Four 10 m bands plus six 20 m bands is
**≈ 1.2 GB per granule, ≈ 6 GB for all five.** That figure is an **estimate from the local
compression ratio, not a measured download** — no fetch was performed, per the constraints.
Disk is not a constraint: 411 GB free.

A second, cheaper option exists for objection (2): the same document lists four already
scouted, never downloaded expansion granules with near-zero cloud —
`36TWK` (0.1 %, 2026-04-07), `36TVL` (7.6 %, 2026-04-15), Kars `38TLL` (0.5 %, 2026-04-28),
Black Sea `37TFF` (0.1 %, 2026-04-16) — at ~350 MB TCI + 5 MB SCL each
(`phase-cd-preparation.md:44, 68-69`). `37TFF` and `38TLL` are the two that would actually
add a new landform class rather than more plateau.

---

## 4. Environment

### 4.1 Python interpreters and library versions

Four interpreters exist. The relevant two are `gencp` (development, training, analysis) and
the QGIS app process (deployment).

| | `/opt/homebrew/Caskroom/miniforge/base/envs/gencp/bin/python` | QGIS app process | miniforge base | `/usr/bin/python3` |
|---|---|---|---|---|
| Python | **3.11.15** | **3.12.11** | 3.13.13 | 3.9.6 |
| torch | **2.13.0**, `mps_available=True`, `mps_built=True`, `cuda=False` | absent | absent | absent |
| onnxruntime | **1.29.0**, providers `['CoreML','Azure','CPU']` | **1.29.0**, same providers | absent | absent |
| rasterio | **1.4.4** | **1.5.0** | absent | absent |
| GDAL | **3.12.3** (via rasterio) | **3.12.4** (`osgeo.gdal.__version__`) | absent | absent |
| numpy | 2.4.6 | 2.5.0 | absent | absent |
| geopandas | 1.1.4 | 1.1.3 | absent | absent |
| pyosmium | present (no `__version__` attribute) | present (same) | absent | absent |
| osmnx | 2.1.1 | 2.1.1 | absent | absent |
| scipy | 1.17.1 | 1.18.0 | absent | absent |
| shapely | 2.1.2 | 2.1.2 | absent | absent |
| pyproj | 3.7.2 | 3.7.2 | absent | absent |
| qgis.core | — | **4.2.1-Belém do Pará** | — | — |

Also present: `osmium` CLI 1.19.1 / libosmium 2.23.1 at
`/opt/homebrew/Caskroom/miniforge/base/envs/gencp/bin/osmium` — **not on the default PATH**,
which matters because `tubitak/scripts/tile_pipeline.py:70` shells out to bare `osmium`.

The QGIS column was measured **inside the QGIS application process** via
`tubitak/tests/run_in_qgis.sh`, not through the bundled `python3.12` — see §1.4 for why that
distinction is load-bearing. The base miniforge and CommandLineTools interpreters are bare
and can be disregarded.

Two version pairs differ between the development env and deployment: **GDAL 3.12.3 vs
3.12.4** and **numpy 2.4.6 vs 2.5.0**. Standing practice 9 requires recording these per run.

### 4.2 GPU

| | |
|---|---|
| machine | MacBook Pro, Mac16,6, **Apple M4 Max** |
| CPU | 14 cores (10 P + 4 E) |
| GPU | Apple M4 Max, **32 cores**, Metal 4, built-in |
| unified memory | 36 GB (`hw.memsize = 38654705664`) |
| **MPS** | **available** — `torch.backends.mps.is_available() = True`, `is_built() = True`, in the `gencp` env |
| CUDA | `torch.cuda.is_available() = False` (no NVIDIA hardware) |
| onnxruntime GPU path | `CoreMLExecutionProvider` is available in both interpreters, but `infer.OnnxGenerator` pins `providers=["CPUExecutionProvider"]` deliberately ([infer.py:63-65](../../gencp_core/infer.py#L63)) |
| free disk | 411 GB of 926 GB |

So local SR training on MPS is possible. Note that MPS is not the same numerics as CUDA, and
any Modal/Kaggle GPU run would not reproduce local results bit-for-bit.

### 4.3 QGIS

| | |
|---|---|
| application | `/Applications/QGIS-final-4_2_1.app` |
| version | **4.2.1** (`CFBundleShortVersionString`; `Qgis.QGIS_VERSION` reports `4.2.1-Belém do Pará`) |
| profiles root | `~/Library/Application Support/QGIS/QGIS4/profiles/` — note **QGIS4**, not `QGIS3` |
| profiles present | `default`, `gencp_stranger`, `gencp_zip_test` |
| plugin directory | `~/Library/Application Support/QGIS/QGIS4/profiles/<profile>/python/plugins/` |
| installed in `default` | `gencp_synthetic_reference`, `sentinel_stac_loader`, `stac_browser` |
| installed in `gencp_stranger`, `gencp_zip_test` | `gencp_synthetic_reference` |

`sentinel_stac_loader` is *Quick VRT Imagery Loader* v1.0.1 (author Vagner Teixeira,
`github.com/vagnertxr/quickvrt`) and already supports **Element84 Earth Search** and
Microsoft Planetary Computer, loading Sentinel-2 as VRT. It is a ready-made path for pulling
the reflectance bands of §3.4 without writing a fetcher.

### 4.4 Modal and Kaggle — which is ready today

**Both are ready. Neither was used to launch anything.**

| | Modal | Kaggle |
|---|---|---|
| CLI | `/opt/homebrew/Caskroom/miniforge/base/bin/modal`, **client 1.5.4** | `/opt/homebrew/Caskroom/miniforge/base/bin/kaggle`, **Kaggle CLI 2.2.4** (a second copy at `~/.venvs/kaggle/bin/kaggle`, same config) |
| token | `~/.modal.toml`, profile `[mvy0502]`, `active = true` | `~/.kaggle/access_token` (38 bytes, mode 600); **no `kaggle.json`** — auth method is `ACCESS_TOKEN` |
| auth verified by | `modal profile current` → `mvy0502`; `modal app list` → returned the apps table (empty; no running apps) | `kaggle config view` → username `vedatyildirim`; `kaggle kernels list --mine` → **returned 10 prior GenCP kernels, exit 0** |
| repository setup | `tubitak/modal/gencp_modal.py`, `tubitak/modal/patches/` | `tubitak/kaggle/build_kernels.py`, `train_c1_c2.py`, `dataset-metadata.json`, `prepare_dataset.sh`, `setup_kaggle_cli.sh` |
| track record | app list currently empty — no evidence in this check of a completed Modal run | ten completed GPU training kernels, most recent `gencp-env-probe-gpu-image` 2026-08-25, and the Phase C arms C1/C2/C4/C5 across seeds 43/44 (2026-08-23/24) |

*What a failing case would have looked like:* an unauthenticated Modal prints an
`AuthError` instead of the table; an unauthenticated Kaggle prints `401 Unauthorized` from
`kernels list`. Both returned real data and exit 0, so the checks discriminated.

**Which is ready to use today: Kaggle, on evidence; Modal, on configuration.** Kaggle's
token authenticates against the live API *and* has ten completed GPU training runs for this
exact project behind it, with the kernel-building code checked in. Modal's token
authenticates and `tubitak/modal/gencp_modal.py` exists, but `modal app list` is empty, so
this check found no evidence of a successful job. That is not evidence of failure — it is an
absence, and WP3 should treat it as one.

---

## 5. Open risks

Ranked by how much time they can cost before Friday 4 September 2026.

**R1 — There is no reflectance data, only an 8-bit visual composite, and this changes what
the result means.** (§2.1, §3.3) No L1C, no SAFE, no B02/B03/B04/B08, no 20 m bands, verified
by four independent sweeps. A Wald protocol run on TCI is a valid experiment about the TCI
product; it is not super-resolution of Sentinel-2 reflectance. The cost of getting this wrong
is not implementation time — it is a claim in a presentation that has to be retracted. The
decision (accept and state the scope, or spend ≈ 6 GB and a download to fix it) should be
made in WP1, before any model is trained, because it determines what the training data is.

**R2 — Every reuse-critical constant in `gencp_core` is a module global, not an argument.**
(§1.1) `SRC_PX`, `OUT_PX`, `NOMINAL`, `TILE_M`, `TRUE_GSD`, `INPUT_PX` are read from module
scope by `output_grid`, `tile_grid`, `mosaic.build`, `feather_weight` and `infer.preprocess`.
`mosaic.py:62` hard-wires `Affine(TRUE_GSD, ...)` with a comment saying no 10.0 m path exists
— which is correct and deliberate for Project 1 and directly in the way for Project 2. There
are two options and they have very different risk profiles: parameterise the shared module
(touches gated Project-1 code, risks breaking Gate G and Gate R), or fork the arithmetic into
`tubitak/sr/` (duplicates code, but leaves the gated chain untouched). This is an
architecture decision for WP1, and picking it late means rewriting whatever was built first.
Note also that `CLAUDE.md`'s ownership boundary makes `gencp_core` ours to change — the
constraint here is the passing gates, not permission.

**R3 — `infer.preprocess` resizes, and for SR the resize *is* the thing being learned.**
(§1.1) `preprocess` bicubic-resizes any input to 256 px, because pix2pix consumes a 257 px
render at 256 px. Reused unmodified in an SR pipeline it silently resamples the input before
the network sees it, and the network then learns to undo a bicubic resize on top of whatever
degradation the Wald protocol applied. The output would look plausible and the error would be
invisible in every metric that compares generated to target. This is the same failure class
`CLAUDE.md` calls the dominant one: wrong but plausible.

**R4 — The four expansion granules cannot be re-fetched from the record.** (§2.2) No product
ID, no platform, no md5, no download script for 36SVJ, 36SWJ, 36SXJ, 36TUK; the single
matching grep hit is a *different* Cappadocia scene from August. If any of these four files is
lost or corrupted, reconstructing the exact scene requires a STAC query and a judgement call,
not a checksum. Standing practice 5 (registration text must name the exact corpus) cannot be
satisfied for these four as things stand. Cost is small to fix now — one STAC query per
granule to recover the IDs — and large to fix after a training run has cited them.

**R5 — The 10 m → 5 m step has no ground truth, and nothing on this machine can supply one.**
(§3.3) The only sub-10 m raster present is `tool_runs/E3/target_esri_z18.tif`, which is Esri
basemap data: different sensor, different date, and not distributable. Registering the 5 m arm
as self-consistency-only *before* results exist is cheap; discovering the gap while preparing
slides is not. Standing practice 4 applies directly.

**R6 — `SEC_PER_TILE`, `INDEX_PARSE_SEC` and `STAGE_WEIGHTS` are Project-1 measurements that
will be silently wrong.** (§1.5) `extent.SEC_PER_TILE = 0.48` decomposes as render 0.343 +
infer 0.016 + confidence 0.031 + mosaic 0.087. SR has no render stage at all, so 71 % of that
constant is a stage that will not run, and `task.py`'s `STAGE_WEIGHTS` gives `render` 0.80 of
the progress bar. Inherited unchanged, the SR plugin's time estimate and progress bar are both
wrong on their first run — the exact defect fixed in commit `9141da2` for Project 1.

**R7 — GDAL and numpy differ between the development env and the QGIS deployment
environment.** (§4.1) GDAL 3.12.3 vs 3.12.4, numpy 2.4.6 vs 2.5.0. Under standing practice 9
these belong in every option dump. For an SR model whose output is asserted at sub-pixel
tolerance, a resampling-kernel difference between GDAL minor versions is exactly the kind of
thing that makes a gate pass locally and fail in QGIS.

**R8 — `osmium` is not on the default PATH.** (§4.1) `tubitak/scripts/tile_pipeline.py:70`
calls bare `osmium` via `subprocess.run(..., capture_output=True)`, which swallows the error.
The binary exists only inside the `gencp` env. Not on the SR critical path, but it is a
loaded gun in a script that will plausibly be reused to cut chips.

---

## 6. Open items carried out of this work package

1. Place names for 36TUK and 36SVJ — recorded only as positions "W" and "S". **Not determined.**
2. Full product IDs, platforms and checksums for the four expansion granules (R4). **Not determined.**
3. The "different Team IDs" onnxruntime symptom was **not reproduced today** (§1.4); the
   bundled interpreter fails earlier, on `init_fs_encoding`. The documented finding stands on
   `plugin-results.md`, not on a measurement in this work package.
4. Evidence of a completed Modal job — `modal app list` is empty. Configuration verified,
   execution not (§4.4).
5. Whether to parameterise `gencp_core` or fork the arithmetic into `tubitak/sr/` (R2) — a
   WP1 decision, deliberately not made here.
