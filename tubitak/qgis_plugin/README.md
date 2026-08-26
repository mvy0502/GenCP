# GenCP Synthetic Reference — QGIS plugin

Generates a georeferenced synthetic 10 m reference raster over a chosen extent, adds it to
the map as a layer and/or writes it to disk as a GeoTIFF.

**Matching and GCP extraction are out of scope.** A separate application consumes this
output and does the matching. That is why the georeferencing is treated as an interface
contract (Gate G) rather than a nicety: a half-pixel offset is invisible here and becomes
wrong GCPs downstream.

## Architecture

```
tubitak/gencp_core/      no Qt, no qgis imports, plain Python — all the logic
    extent.py            bbox + CRS validation, the tile grid, the output-grid snapping rule
    vectors.py           OSM acquisition (local .osm.pbf or Overpass) + CLC+ base
    rasterize.py         the upstream rendering spec, lifted verbatim (Gate R)
    infer.py             ONNX inference over tiles (no PyTorch)
    mosaic.py            feather blending, georeferencing, GeoTIFF write (Gate G)
    pipeline.py          orchestration, so the dialog holds none
    export.py            build-time only: PyTorch -> ONNX (Gate O)
    palette.py           loads the upstream palette by path, hash-pinned

tubitak/qgis_plugin/     shell only — calls gencp_core, contains no generation logic
    metadata.txt  __init__.py  plugin.py  dialog.py  task.py  qtcompat.py
```

`tubitak/tests/test_no_qgis_imports.py` enforces the boundary statically: it parses every
file under `gencp_core/` and fails if any imports `qgis`, `PyQt5`, `PyQt6` or `processing`.
The point is not tidiness — the same core is what would run in an embedded or offline
context later, and it is what makes the chain testable without QGIS running.

## Quick start

For someone who just wants to produce one output: **`QUICKSTART.md`** (Turkish, numbered
clicks only). Installable archive and what is and is not in it:
https://github.com/mvy0502/gencp-validation/releases/tag/plugin-v0.2.0

What installing it and using it in anger actually found — six defects, four of them silent
wrong output, plus timings and screenshots: **`tubitak/docs/plugin-field-test.md`**.

## Installing

1. **Dependencies into QGIS's own Python.** Everything else the plugin needs (numpy, GDAL,
   rasterio, PIL, scipy, shapely, geopandas, pyproj) already ships with QGIS.

   ```bash
   # macOS, adjust the app name for your version
   A=/Applications/QGIS-final-4_2_1.app/Contents
   PYTHONHOME=$A/Frameworks \
   PYTHONPATH=$A/Resources/python3.12/site-packages:$A/Resources/python \
     $A/MacOS/python3.12 -m pip install onnxruntime osmium
   ```

   `osmium` is needed only for the local `.osm.pbf` source; `osmnx` only for Overpass.

2. **Copy the plugin.** Copy `tubitak/qgis_plugin/` into your QGIS plugin directory as
   `gencp_reference/`, and copy `tubitak/gencp_core/` inside it. `plugin.py` also finds
   `gencp_core` one or two levels up, so it runs from a repository checkout unchanged.

3. **Palette.** `gencp_core/palette.py` loads `GenCP_HR_demo/genCP_HR_osm_colors.py` and
   verifies its SHA-256. Outside the repository, copy that one file to
   `gencp_core/_vendored_osm_colors.py` or point `GENCP_PALETTE` at it. A hash mismatch is
   a hard error, because every render depends on those tables.

4. **CLC+ Backbone raster.** Set `GENCP_CLC_PATH`, or enter the path in section 2 of the
   dialog. CLC+ Backbone covers Europe only.

5. **Model.** Export one with `python -m gencp_core.export --arm C3 --out model.onnx`, then
   choose it in section 4. The weights path is configurable and deliberately not
   bundled-and-hardcoded.

## Version support — what is tested and what is not

**Executed end to end on QGIS 4.2.1 (Qt 6.11.1 / PyQt 6.11.0), macOS.** `metadata.txt`
declares `qgisMinimumVersion=3.28`, `supportsQt6=True`.

**3.28 is reasoned about, not tested.** No QGIS 3.x is installed here, so no 3.x load has
been verified, and neither has any Windows load. The basis for the claim: every Qt import
goes through the `qgis.PyQt` shim (no direct `PyQt5.*`/`PyQt6.*` anywhere), enum members
are resolved through `qtcompat.member()` so both the Qt5 flat names and the Qt6 scoped
names work, no Qt5-only API (`exec_()`, `QDesktopWidget`, `QRegExp`, `QVariant(...)`,
`QStringList`, `toAscii`) is used, and the QGIS API surface is all QGIS 3.0-era. `QAction`
— which Qt6 moved from `QtWidgets` to `QtGui` — was specifically checked: the QGIS shim
exposes it from both.

Treat a first run on the institution's QGIS as a test, not a formality.

## macOS note that will otherwise cost you an afternoon

The QGIS **application** executable is signed with
`com.apple.security.cs.disable-library-validation`; the bundled **`python3.12`** executable
is not. Under the hardened runtime, third-party native extensions (onnxruntime, pyosmium)
therefore load fine in the QGIS process the plugin runs in, and are refused in `python3.12`
with *"different Team IDs"*. If you want to test headlessly, drive the app binary:

```bash
QT_QPA_PLATFORM=offscreen /Applications/QGIS-final-4_2_1.app/Contents/MacOS/QGIS-final-4_2_1 \
    --nologo --code your_script.py
```

`tubitak/tests/run_in_qgis.sh` does this. `QT_QPA_PLATFORM=offscreen` replaces Xvfb, which
does not exist on macOS.

## Determinism

The exported graph has dropout removed, and BatchNorm is exported in **batch-statistics**
mode — the path every number in this project was measured on. `torch.onnx.export` would
default to running-statistics BatchNorm, which changes the output by mean 32 DN over 100%
of pixels. See `gencp_core/export.py` and the Gate D section of
`tubitak/docs/plugin-results.md`.

## Sizes

About **300 MB fixed** (fp32 ONNX model 217.7 MB + onnxruntime 82.7 MB), plus roughly
**3.3 MB per 1000 km²** of coverage for OSM and CLC+ data. Full table in
`tubitak/docs/plugin-results.md`.
