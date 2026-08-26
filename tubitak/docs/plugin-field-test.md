# First real run of the plugin — what installing it and using it found

**Date: 2026-08-26/27.** Complements `plugin-results.md` (the gate record) and
`plugin-gate-registrations.md`. This is not a gate registration: no predictions were
registered in advance, because the work was to install the plugin the way a user installs
it and then find out what happens. Gates R, G, O and S are unchanged and were re-run
afterwards to confirm nothing here moved them.

**One-line summary.** The plugin worked end to end on the first attempt, 28 of 28 checks,
and that number was misleading: driving its *failure* paths and installing it from a zip
found six real defects, four of which produced confidently wrong output with no error.

---

## What was installed, and where

| | |
|---|---|
| Profile | `~/Library/Application Support/QGIS/QGIS4/profiles/default` |
| Installed as | `python/plugins/gencp_synthetic_reference` — a symlink to `tubitak/qgis_plugin` |
| Enabled by | `gencp_synthetic_reference=true` under `[PythonPlugins]` in `qgis.org/QGIS4.ini` |
| QGIS | 4.2.1-Belém do Pará, Qt 6.11.1 / PyQt 6.11.0, macOS |

A symlink rather than a copy, deliberately: the development profile then tracks the
checkout with no packaging step, and `Path(__file__).resolve()` resolves through it so
`ensure_core_importable()` still finds `gencp_core` one level up in `tubitak/`. The cost
is that the development profile breaks if the repository moves. The **zip** install
(below) is the one that does not depend on the checkout at all, and it is verified
separately for that reason.

`initGui()` completing is asserted through its observable consequence rather than by
watching it run: QGIS registers a plugin in `qgis.utils.plugins` only after `startPlugin`
returns without raising, and the `QAction` exists on the main window afterwards.

---

## The end-to-end run

Driven through the dialog's own code path — `plugin.action.trigger()`, then the real
widgets and the real `Generate` button, never `gencp_core` directly.
Harness: `tubitak/tests/plugin_e2e_run.py`. **35/35 checks.**

Extent: `ank_0_30.tif`, 2570 x 2570 m, EPSG:32636, one tile at 0 m overlap.

### Gate G's contract, re-asserted on this output

`gate_g.py` calls `pipeline.generate` itself, which proves the contract holds for the
library but not that the dialog passes the library the right arguments. So the same
registered arithmetic is read back off the file the `Generate` button wrote:

| assertion | result |
|---|---|
| pixel size exactly 10.0 m, both axes | 10.0, 10.0 |
| origin == reference NW corner | offset 0.0 m, 0.0 m |
| size == ceil(span / GSD) | 257 x 257, expected 257 x 257 |
| transform == the registered affine, term by term | `(10.0, 0.0, 399960.0, 0.0, -10.0, 4422900.0)` |
| output CRS == reference CRS | EPSG:32636 |
| `GENCP_PROVENANCE` embedded | 17 fields |

The output opens as a layer, is valid at 257 x 257 px in EPSG:32636, and its extent
coincides with the reference's. `08_checkerboard_output_vs_reference.png` alternates 8x8
blocks of the generated raster and the real Sentinel-2 reference rendered through the same
`QgsMapSettings`; features continue across block boundaries. It also shows plainly how much
less detailed the synthetic image is than the reference — that is a real property of the
model, not a georeferencing defect, and it is not being hidden here.

### Threading

`GenerateTask.run` was instrumented to record `QThread.currentThread()`. It is not the
main thread. The progress bar advanced through distinct values, and during the cancel test
the event loop was serviced 64 times while the cancel completed, so the GUI was live
throughout.

### Wall clock against the displayed estimate

The dialog predicts `n_tiles x 6 s`. Measured on a cold cache, one tile:

| | seconds |
|---|---|
| Preview render (section 3) | 5.43 |
| `Generate` click to done | 0.48 |
| **What the user actually waits for** | **5.91** |
| **What the dialog predicted** | **6.00** |

**The estimate is honest about the total and badly wrong about where the time goes.**
Against the whole interaction it is out by 1%. Against the step it is attached to — the
`Generate` button, in the section labelled "Run" — it is out by **12x** (6.00 s predicted,
0.48 s actual). Nearly all the cost is rasterisation, and inference is under half a second
per tile.

That is a defensible place to land for a first estimate and it is not being tuned to look
better. What it means for a user is recorded in QUICKSTART.md instead: the preview takes
longer than you expect and Generate takes less.

**The first measurement of this was wrong and is worth recording.** The first run reported
0.6 s and would have been reported as a 10x-pessimistic estimate. It was fast because a
render left in the shared cache six hours earlier was silently reused — the same bug
described below. Every timing here is from a cache cleared immediately before the run.

---

## The six defects

Ranked by how badly a user would be misled. `SILENT` means it produces an output that
looks fine and is wrong, with nothing said.

### 1. Render cache collision — SILENT, and the worst of them

`render_inputs` skipped rendering when its cache file existed, and `generate` defaulted
the cache to a fixed directory under the system temp path. The file name was
`t_{i}_{j}.tif` — the tile **index** and nothing else. Two different extents both produce
a tile (0,0).

Measured, not argued: `ank_0_30` and `ank_0_41`, 28 km apart, produced a **byte-identical**
raster. No error, no warning.

Worse than it first looks. The Preview section rendered into a fresh `mkdtemp` every time,
so it showed the *correct* new input while the file written to disk was the *old* one.
The dialog exists to let a user check the render and then trust the output, and this
severed exactly that link.

Fixed two ways. Cache names are now content addressed over tile origin, tile size, working
CRS, base product, OSM source (path + size + mtime) and CLC+ path. And the preview now
writes into the same cache the run reads from, so the pixels the user approves are
literally the pixels used, rather than a second render that is merely expected to match.

Regression test: `tubitak/tests/plugin_cache_probe.py`. It asserted "outputs identical =
True" before the fix and asserts False after, and separately confirms a repeat of the same
extent still hits the cache (0.22 s, no new render).

### 2. An exception inside a Qt slot on every dialog construction — CRASH

`_prefill_paths()` and `_prefill_model()` ran from the middle of `_build_ui`, before
sections 3-6 had created `btn_preview`, `cb_write` and `out_edit`. Setting a `QLineEdit`'s
text emits `textChanged`, which is connected to `_validate`, which touches all three.
Result: two `AttributeError`s **every single time the plugin was opened**.

PyQt cannot propagate an exception out of a slot, so it calls `sys.excepthook`, which in
QGIS opens a modal Python error dialog. A user opening the plugin got two error boxes,
and the dialog then finished building and worked — which is precisely why 25/25 headless
checks and 28/28 e2e checks passed over it.

Found by accident, and only because of the offscreen platform: a modal `QMessageBox` never
returns offscreen, so the failure-path harness hung instead of failing, and the sampled
main-thread stack showed `QDialog::exec()` underneath `_PyErr_PrintEx`. Under a normal GUI
this would have kept working, visibly wrong, indefinitely.

Prefills moved to the end of `_build_ui`; `_validate` also returns early until an
`_ui_ready` flag is set. Both harnesses now install an excepthook that records slot
exceptions and assert the count is zero.

### 3. The preview ignored the CLC+ path the user typed — SILENT

`GENCP_CLC_PATH` was set in `_start()` only. The preview therefore rendered against
whatever default `gencp_core` had, while the run used the user's file: two different base
rasters under one checkbox reading "I have looked at the render above and it is correct".

Found by pointing the CLC+ field at a text file. The preview reported **success**.
Extracted to `_apply_clc_path()`, now called before the preview as well. The same case now
reports the underlying reader's error in a message box, and the dialog survives.

### 4. Non-metric CRS accepted silently — SILENT

`resolve()` tested `crs == "EPSG:4326"` and treated everything else as projected metres.

- **EPSG:3857.** A 2570 m reference measured 3391 units at Ankara's latitude. The chain
  built a 340 x 341 px raster where 257 x 257 was correct and called every pixel 10 m.
- **EPSG:4258.** Geographic, but not the one hard-coded string, so its degrees were read
  as metres. Extent span 0.0, output grid **1 x 1 px**.

Both produced a file. Neither said anything.

`classify_crs()` now decides from the CRS's own properties: any geographic CRS reprojects
to UTM, and Pseudo-Mercator or non-metre axis units are refused with a message naming the
fix. The dialog disables its buttons rather than printing red text and letting `Generate`
be pressed anyway. EPSG:4258 now resolves to EPSG:32636 with a 2636.6 m span, and
EPSG:3857 gets a sentence telling the user to reproject and how.

### 5. No OSM coverage rendered as plausible countryside — SILENT

An extent the chosen `.osm.pbf` does not cover yields zero OSM features. The CLC+ base is
still drawn, so the render is a clean, credible empty landscape rather than anything that
looks like a failure. Verified: 0 features, 946 distinct colours, output written, nothing
reported.

`make_chip` now reports feature counts through an out-parameter — an out-parameter and not
a changed return value, and a JSON sidecar rather than a GeoTIFF tag, because `gate_r.py`
compares those bytes. `render_inputs` carries the counts across cache hits, and the dialog
shows a warning banner **directly above the confirmation checkbox**, where the decision is
made, rather than in the message log.

### 6. The zip was not self-contained — found only by installing it

`gencp_core/palette.py` lists four places it looks for the GenCP colour tables, one being
"a copy vendored beside this file, made by the packaging step". Nothing made that copy. In
a checkout the fourth candidate — the upstream file two directories up — always resolves,
so this could not be seen from the development profile.

From the zip in a clean profile: the plugin installed, started, created its menu action,
opened its dialog, read the extent, and then failed at the first render with "GenCP palette
module not found". `build_plugin_zip.py` now vendors it verbatim, verifies the hash at
build time, ships attribution separately (`palette.py` would reject a file with a comment
added), and fails the build if either is missing.

A seventh, minor: `gencp_core` was not importable between `startPlugin()` and the first
click, because `ensure_core_importable()` was called from `run()` only. `initGui()` calls
it too now.

---

## Failure paths, classified

Worst first: `SILENT` > `FREEZE` > `CRASH` > `MESSAGE` > `BLOCKED`.
Harness: `tubitak/tests/plugin_failure_paths.py`.

| case | before | after |
|---|---|---|
| CLC+ path empty | BLOCKED | BLOCKED |
| CLC+ path does not exist | BLOCKED | BLOCKED |
| `.osm.pbf` does not exist | BLOCKED | BLOCKED |
| ONNX model does not exist | BLOCKED | BLOCKED |
| CLC+ path exists but is not a raster | **SILENT** (preview reported success) | MESSAGE |
| reference in EPSG:4326 | HANDLED | HANDLED |
| reference in EPSG:3857 | **SILENT** (wrong scale) | MESSAGE, naming the fix |
| reference in EPSG:4258 | **SILENT** (1 x 1 px output) | HANDLED (reprojects to UTM) |
| extent with no OSM coverage | **SILENT** | WARNED, banner above the checkbox |
| Cancel pressed mid-run | MESSAGE | MESSAGE |
| exceptions inside Qt slots | **2 per dialog open** | 0 |

**Cancel behaves.** Pressed at 12.5% of a four-tile run it stopped after 2.3 s, the event
loop was serviced 64 times while it did (so no freeze), the status line read "Cancelled.",
and **no partial GeoTIFF was left on disk** — which was the dangerous outcome to check for.

### Not fixed, and why

- **The message for a corrupt CLC+ raster is the underlying reader's**, not one the plugin
  wrote: `"... not recognized as being in a supported file format."` It names the file and
  the problem, the dialog survives, and wrapping every library error in our own prose would
  cost more than it returns. Recorded rather than fixed.
- **Overpass results are cached like file results.** The cache key distinguishes Overpass
  from a local extract and keys on the tile, but a live source that changes upstream will
  still be served from cache within a session. Not a correctness bug for a single sitting;
  worth revisiting if Overpass becomes the common path.
- **`ensure_core_importable()` puts `gencp_core` on `sys.path` as a top-level module.** Two
  plugins vendoring different versions would collide. No such plugin exists; noted.
- **`GENCP_CLC_PATH` persists for the QGIS session.** If a user sets a bad path and then
  clears the field, the stale value survives — but an empty field is blocked before it can
  be used, so this is not reachable through the dialog.

---

## The zip, and installing from it

`gencp_plugin.zip`, 47 KB: one top-level folder named for the plugin, `metadata.txt` at
its root, `gencp_core` and the palette vendored, no bytecode. The build asserts that layout
on the archive it has just written rather than trusting the loop that wrote it.

Verified by `tubitak/tests/run_zip_install.sh` into a profile that is destroyed and
recreated per run, through `pyplugin_installer.instance().installFromZipFile` — the
"Install from ZIP" button's own code path. **23/23 checks**, including that `gencp_core`
resolves to the copy inside the installed plugin and not to the checkout, one generation
run end to end, and the Gate G contract asserted on the raster it produced.

### A macOS fact that cost several runs

The zip-install runner deliberately does **not** set `QT_QPA_PLATFORM=offscreen`. On a
profile QGIS has never seen, `QgisApp` calls
`QgsAuthManager::createAndStoreRandomMasterPasswordInKeyChain()`, and QtKeychain's macOS
*write* never completes under the offscreen platform: six runs hung in
`passwordHelperWrite()` for 10-22 minutes each, with an empty output file, and the stack
was sampled to the same frame every time. `QGIS_AUTH_PASSWORD_FILE`, `QGIS_AUTH_DB_DIR_PATH`
and a read-only auth directory were probed in isolation and all still hung. The same
trivial probe under the cocoa platform started in seconds. The login keychain is unlocked
and the session is Aqua, so this is neither a locked keychain nor an authorization prompt.

`run_in_qgis.sh` can stay offscreen because the **default** profile already has a stored
master password, so QGIS reads instead of writing, and reads do complete offscreen. The
consequence is that the zip-install run briefly opens a real QGIS window.

### Published

`gencp_plugin.zip` only, at
https://github.com/mvy0502/gencp-validation/releases/tag/plugin-v0.2.0.

**The ONNX weights are deliberately not published.** `evidence/BACKUP.md` known risk 4
records that the weights derive from GenCP's CC-BY 4.0 weights while the fine-tuning
inputs were rendered from OpenStreetMap under ODbL, and that whether ODbL's share-alike
obligation reaches such weights is unsettled — private backup and direct institutional
handover need no such decision, public release would. Rather than settle that question by
publishing, the weights are handed over directly. The release notes and QUICKSTART.md both
say so and say why.

---

## Screenshots

`tubitak/docs/evidence/plugin_screens/`, produced by `plugin_e2e_run.py` via
`QWidget.grab()`, which renders through the paint system and needs no display. Every state
the work package asked for was capturable offscreen; none is a mock-up.

| file | what it shows |
|---|---|
| `01_dialog_on_open.png` | the dialog as it opens, no layer chosen, extent `—`, Generate disabled |
| `02_reference_selected.png` | reference chosen; extent, CRS and tile count filled in |
| `03_preview_rendered.png` | the preview section with the rasterised input actually rendered |
| `03b_preview_tile_only.png` | that preview pixmap on its own |
| `04_run_in_progress.png` | mid-run, progress bar at 25% |
| `05_after_completion.png` | after completion, output added as a layer |
| `05b_full_form.png` | all six sections in one image (the dialog scrolls, so a window-sized grab cuts 5 and 6 off) |
| `06_canvas_output_only.png` | the generated raster through QGIS's own renderer |
| `07_canvas_reference_only.png` | the real Sentinel-2 reference, same map settings |
| `08_checkerboard_output_vs_reference.png` | the two interleaved in 8x8 blocks |

The checkerboard replaced a stacked-layers image that was worthless as evidence: the
output is opaque and simply hid the reference, so the composite was pixel-identical to the
output alone.

Two layout defects are visible in the first version of `03` and were fixed: the one label
without word wrap set the form's minimum width and put a horizontal scrollbar under every
section, cutting the path fields off at the right edge; and "1 tiles" now reads "1 tile".
`icon.png` was added — `metadata.txt` named it and it did not exist, so the toolbar button
was blank.

---

## Re-verification after all changes

| | |
|---|---|
| Gate R | PASS, 3/3 tiles byte-identical to stored originals — renders did not move |
| Gate G | PASS, 12/12 assertions |
| `test_plugin_headless.py` | 25/25 |
| `plugin_e2e_run.py` | 35/35 |
| `plugin_cache_probe.py` | PASS in both directions |
| `plugin_failure_paths.py` | no SILENT verdicts remain, 0 slot exceptions |
| `run_zip_install.sh` | 23/23 in a clean profile |

Gate R passing matters most: `make_chip` gained a parameter and `render_inputs` gained a
sidecar file, and the rendered bytes are unchanged.

---

## Still not verified

- **QGIS 3.x.** Code is written against the `qgis.PyQt` shim with no Qt5-only or Qt6-only
  API, and `qtcompat.member()` handles the enum move, but 3.28 is reasoned about, not run.
- **Windows.** Not run. `tempfile.gettempdir()` is used rather than a `/tmp` fallback
  precisely for this, but that is care, not evidence.
- **Overpass as the vector source.** Every run here used a local `.osm.pbf`.
- **Multi-tile mosaics beyond four tiles**, and any extent large enough for the seam
  metric to be interesting.
