# Project 2, WP2B — QGIS plugin shell on the bicubic path

**Run:** 2026-08-30. **Repository:** `mvy0502/GenCP`, branch `tubitak-tr`.

**`sr_core` was NOT modified.** `git status --porcelain tubitak/sr/sr_core` is empty. No
change to it proved necessary, including for cancellation — see §4.2, where the mechanism
and the reason it needed no new interface are set out. Project 1's plugin
(`tubitak/qgis_plugin/`) was read as a pattern and is likewise unmodified, as are
`tubitak/gencp_core/` and the upstream pix2pix tree. Nothing under `tubitak/sr/sr_data/`
was read or written; that directory belongs to the concurrent session.

**Headline results.**

| question | answer |
|---|---|
| Runs inside QGIS on a real granule? | **Yes.** 10980 x 10980 → 21960 x 21960, 529 tiles, **37.7 s**, layer added and confirmed aligned. |
| Matches the CLI pixel for pixel? | **Yes.** One pixel-SHA256 across four independent runs in three environments. |
| Loads and completes with `onnxruntime` unimportable? | **Yes**, verified by making it unimportable two different ways, not by reading the code. |
| Cancellation leaves a truncated file? | **No.** Destination byte-identical after cancel; the `.part` existed during the run and was gone after. |
| Gate S on the plugin's output? | **PASS 5/5**, on the fixture, the full granule, and the clean-profile output. |
| Plugin vs CLI wall clock | 37.7 s against WP1's 26.90 s. **It is not the QgsTask** — §7. |

---

## 1. Environment and versions

**Machine:** MacBook Pro, Apple M4 Max, 14 cores (10P + 4E), 36 GB unified memory.
`platform.platform()` reports `macOS-26.5.1-arm64-arm-64bit` in both interpreters.

Two Python stacks are involved, and **they are not the same stack**. This turns out to
matter for §7, so both are recorded in full:

| | QGIS application process (where the plugin runs) | CLI environment (WP1's numbers) |
|---|---|---|
| host | QGIS **4.2.1-Belém do Pará**, Qt **6.11.1**, PyQt **6.11.0** | — |
| Python | **3.12.11** (`Contents/MacOS/QGIS-final-4_2_1`) | **3.11.15** (`miniforge/envs/gencp`) |
| **Pillow** — does the resampling | **12.2.0** | **12.3.0** |
| numpy | **2.5.0** | **2.4.6** |
| rasterio | **1.5.0** | **1.4.4** |
| GDAL (via rasterio) | **3.12.4** | **3.12.3** |
| `gdal.GetCacheMax()` | 1,932,735,280 | 1,932,735,280 (identical) |
| `GDAL_NUM_THREADS` | unset | unset |

**Random seed.** The bicubic path draws no random numbers; `sr_core` records
`"random_seed": null, "stochastic": false` in the provenance of every output. The only
seeded code in this work package is the benchmark fixture generator (§7), seed
**20260830**, and the guard's synthetic fixtures, which are literal text.

---

## 2. What was built

`tubitak/sr/sr_plugin/` — 6 modules, 846 lines. A shell: no super-resolution logic.

| file | lines | what it holds |
|---|---|---|
| `__init__.py` | 15 | `classFactory` |
| `plugin.py` | 63 | menu/toolbar registration, `ensure_core_importable()` |
| `dialog.py` | 461 | the dialog. **No Turkish literal** — enforced, see §3 |
| `strings.py` | 160 | every user-facing string, 53 keys (`S` labels + `TIP` tooltips) |
| `task.py` | 118 | `SuperResolveTask(QgsTask)` |
| `qtcompat.py` | 29 | Qt5/Qt6 enum lookup |
| `metadata.txt` | — | QGIS plugin manifest |

Two files outside that directory, both new, neither an edit to anyone else's work:

* `tubitak/sr/tests/plugin_guards.py` (§3) — a static verifier. Placed with the other
  `tubitak/sr/tests/` verifiers because that is where a future reader will look for it. It
  is a fourth reader of `tubitak/tests/_guard.py`, which CLAUDE.md's deletion rule makes
  worth recording.
* `tubitak/sr/build_sr_plugin_zip.py` (§8) — builds the installable zip with `sr_core`
  vendored. Needed because the demo document is not reproducible without one. Not placed
  under `tubitak/scripts/`, which is Project 1's.

### 2.1 The dialog, against the requirement

| requirement | what is there |
|---|---|
| input as a loaded layer **or** a file | two radio buttons; `QgsMapLayerComboBox` filtered to raster layers, and a `QgsFileWidget`. Both paths tested (§5, §9) |
| scale shown and fixed at 2 | a **label** reading `2 ×  (çözünürlük iki katına çıkar)`. A disabled spinbox would invite the user to try to change it; a label states the value and does not pretend to be a control. `SCALE = 2` is one named constant, so the estimate, the run parameters and the label cannot disagree |
| method selector, bicubic selected | `QComboBox`, one item, `bicubic` |
| model-file field present, may be disabled | `QgsFileWidget` present and **disabled**, with a Turkish note saying why. This is where WP4 plugs in |
| output path | `QgsFileWidget` in save mode; auto-filled beside the source as `<name>_sr_x2.tif` if the user has not set one |
| run, cancel, progress | `Çalıştır` / `Durdur`, a `QProgressBar`, and a status line reading `Karo 412 / 529` |

Two additions beyond the requirement, both small and both stated here rather than slipped
in: a collapsed **Gelişmiş** group holding tile size and overlap (WP1 measured that
overlap below 8 px makes tile seams visible, and a user with a memory problem needs the
tile knob), and an **estimate** line showing tile count and output size. The demo document
tells the reader not to touch the advanced group.

**Why the run button is disabled is always stated.** `_blocker()` returns one reason and
the button's tooltip carries it — no input, unreadable input, no output path, output equals
input, or a job already running. A dead button that does not say why is a support call.

---

## 3. The static guard, and the two defects it caught

`tubitak/sr/tests/plugin_guards.py` asserts three properties:

* **G1** no user-facing Turkish literal outside `strings.py` (docstrings excluded — they are
  developer documentation, not UI);
* **G2** no import of `onnxruntime`, `pyproj`, `multiprocessing` or `gencp_core` anywhere in
  the package;
* **G3** every `t()` / `tip()` key used in the package is defined in `strings.py`.

**Known-false first, per standing practice 11.** The failing fixture was written before the
guard was trusted, and `--self-test` runs it on every invocation ahead of the real verdict:

```
  KF  known-false fixture -> 5 offences ['G1', 'G2', 'G3']
        G1 dialog.py:8  Turkish literal outside strings.py: 'Çalıştır'
        G2 dialog.py:0  forbidden import 'gencp_core'
        G2 dialog.py:0  forbidden import 'onnxruntime'
        G2 dialog.py:0  forbidden import 'pyproj'
        G3 <any>:0  string key 'no_such_key_at_all' used but not defined
  KT  known-true fixture  -> 0 offences
  DG  empty package      -> refused: no .py files ... - nothing to check
```

The known-false fixture's *docstring* contains Turkish and is correctly **not** reported,
so G1 discriminates rather than matching any non-ASCII text. Degenerate invocations:
`--scalee=2` → exit 2, a bare positional argument → exit 2, `--pkg=/no/such/dir` → refuses
with "nothing to check" rather than printing a pass.

**On its first real run the guard failed the plugin, and it was right.** Two Turkish
literals were sitting in `dialog.py`:

```
  [FAIL] G1 dialog.py:33   'GeoTIFF (*.tif *.tiff *.TIF *.TIFF);;Tüm dosyalar (*)'
  [FAIL] G1 dialog.py:147  'ONNX (*.onnx);;Tüm dosyalar (*)'
```

File-dialog filters are user-facing text and I had not thought of them as strings. They are
now `filter_raster` and `filter_model` in `strings.py`. This is the guard earning its
place: I wrote the rule, I believed I had followed it, and I had not.

**Final verdict:** 6 files, 180 string literals outside `strings.py`, 37 keys used, 53
defined — **PASS on all three guards**.

**Mechanical path check** (CLAUDE.md): every repository path referenced by
`tubitak/sr/sr_plugin/`, `plugin_guards.py`, `build_sr_plugin_zip.py` and the demo document
was resolved — **14 paths checked, 0 missing.**

---

## 4. The three traps, and how each was paid rather than rediscovered

### 4.1 `onnxruntime` must not be needed — verified by making it unimportable

The requirement is explicit that this be verified by making the import fail, not by reading
the code. It was done **two independent ways**, and the second is the real macOS failure
rather than a simulation of it.

**(a) A `sys.meta_path` blocker in the QGIS application process**, installed before the
plugin is loaded, raising `ImportError` for `onnxruntime` and anything beneath it. Proved
to fire before anything else ran:

```
onnx-block  ACTIVE: import onnxruntime -> ImportError: onnxruntime is blocked by the WP2B test (onnxruntime)
loadPlugin -> True
startPlugin -> True
onnxruntime in sys.modules after load: False
...
status : Bitti · 9 karo · 0.6 sn · 11 MB Katman eklendi ve girdiyle hizalı.
onnxruntime in sys.modules at end: False
```

**(b) The genuine code-signing split.** QGIS's bundled `python3.12` (with `PYTHONHOME` set,
which it needs before it will start at all) cannot load onnxruntime's native extension:

```
ImportError: dlopen(.../onnxruntime/capi/onnxruntime_pybind11_state.so, 0x0002):
  code signature ... not valid for use in process:
  mapping process and mapped file (non-platform) have different Team IDs
```

In that same interpreter, on that same run, `sr_core` imported and a real job completed:

```
onnxruntime UNIMPORTABLE here: dlopen(... ) ...
stack: Pillow 12.2.0 numpy 2.5.0 rasterio 1.5.0
job completed: 9 tiles, 0.45 s 11377845 bytes
onnxruntime in sys.modules at end: False
```

There is no `import onnxruntime` anywhere in `sr_plugin` or `sr_core`; G2 enforces that it
stays that way.

**A finding from (b), worth carrying.** That output's **pixel hash is identical** to every
other run — `41b54b77…` — but its **file size is 11,377,845 bytes against 11,376,632
elsewhere**, because that interpreter had no `proj.db` or `GDAL_DATA` and GDAL wrote a
different CRS encoding. The CRS itself is `EPSG:32636` in both files and the transforms are
identical. So this is a **second, independent mechanism** by which file bytes diverge while
pixel content does not — WP1 found the first (`GDAL_CACHEMAX`). It strengthens WP1's open
item 3: an SR Gate R must hash pixels.

### 4.2 `pyproj` never runs on the worker thread

`pyproj` on a `QgsTask` worker segfaults QGIS 4.2.1 if the main thread built a CRS first.
`sr_core` reads CRS through **rasterio's own PROJ binding** and imports `pyproj` nowhere;
`sr_plugin` does not import it either, and G2 fails the build if that changes.

**The distinction actually observed, and stated rather than blurred:** `pyproj` **is** in
`sys.modules` at the end of a run — QGIS itself imports it at startup. Loaded-in-the-process
is not the same as called-on-this-thread. `task.py` logs both facts at worker start so the
claim is visible in the QGIS log rather than argued about later:

```
worker start: pyproj loaded, onnxruntime not loaded
```

What is asserted is the narrow, true thing: **nothing on the SR code path calls it.** What
is not asserted is that it is absent from the process, because it is not.

### 4.3 No `multiprocessing`, and the work is off the main thread

The tiling loop is serial inside `superresolve`. G2 refuses a `multiprocessing` import. The
whole chain runs on a `QgsTask`; §5 shows QGIS staying responsive, and §7 shows the task
wrapper costing 0.19 s.

### 4.4 Cancellation, and why it needed no change to `sr_core`

`sr_core.run.superresolve` takes `progress(k, n)` and **ignores its return value**. A
`return False` convention would therefore have required widening that interface — which
another session is importing right now, and which this work package must not touch.

Cancellation is implemented instead by **raising out of the progress callback**
(`SRCancelled`), checked after tile *k* is fully blended and before tile *k+1* is read.

This is not a workaround for a missing feature; it is the path that produces the required
on-disk guarantee. `superresolve` writes inside `sr_core.mosaic.atomic_path`, whose
`except BaseException` arm unlinks the temporary file and leaves the destination exactly as
it was. A `return False` would instead have forced `superresolve` to decide what to do with
a half-built file — a decision `atomic_path` already makes correctly. §6 is the measurement.

---

## 5. It runs inside QGIS

Driven through the real dialog and the real `QgsTask`, with `onnxruntime` blocked.

| | |
|---|---|
| dialog title | `GenCP Süper Çözünürlük` |
| source line (read from the file, not guessed) | `1024 × 1024 piksel · 3 bant, uint8 · EPSG:32636 · 10 m çözünürlük` |
| estimate | `9 karo · çıktı 2048 × 2048 piksel · 5 m çözünürlük · yaklaşık 13 MB` |
| model field enabled | **False**, as required |
| progress observed | 5 distinct samples, first `(0, 'Başlatılıyor…')`, last `(99, 'Karo 9 / 9')` |
| final status | `Bitti · 9 karo · 0.6 sn · 11 MB Katman eklendi ve girdiyle hizalı.` |
| layer in project | `plugin_fixture_x2` |

On the full granule (§7) the progress line stepped through `Karo 5 / 529` … `Karo 524 / 529`
over 37.7 s while QGIS stayed responsive.

### 5.1 The output is loaded as a layer, and the alignment check can fail

Requirement 3. On success `_add_and_check` opens the output as a `QgsRasterLayer`, adds it
to the project, and compares CRS authid and extent against the source, with a tolerance of
half an **output** pixel.

That confirmation had, until it was tested, only ever said "aligned" — which is the exact
shape of the three checks CLAUDE.md records as having been written last, assumed to work,
and capable of catching nothing. So it was shown a mismatch:

```
KNOWN-TRUE : 36SVJ output vs 36SVJ source
  -> 'Katman eklendi ve girdiyle hizalı.'
KNOWN-FALSE: the SAME 36SVJ output vs the 36SXJ source
  -> '<b>Çıktı katmanı girdiyle hizalı değil.</b> ...'
  (both EPSG:32636? True; both 10980x10980? True;
   origins 399960.0,4400040.0 vs 600000.0,4400040.0)
VERDICT: the alignment check CAN report a mismatch
```

The two granules share CRS **and** dimensions, so only the extent separates them — the same
trap Gate S's known-false case exposed at the grid level, and the reason a check comparing
CRS and shape alone would pass every wrong pairing here.

**What this check is and is not.** It is a UI-level confirmation that the layer QGIS
actually opened covers the source's ground. It is **not** the grid contract; that is Gate S,
which asserts exact affine arithmetic with no tolerance. The two are reported separately on
purpose, so a green dialog can never be mistaken for a passed gate.

---

## 6. Cancellation, measured on disk

A **known-good sentinel** was placed at the destination first, so the claim "the
destination is left exactly as it was" could be checked by hash rather than by the weaker
"no file appeared". A full-granule job was started and `Durdur` was clicked at tile 60.

```
sentinel at destination BEFORE: 11376632 bytes  md5 b5fcc2ffeeda8b1eac9d1580551f62de
overwrite prompt shown: 'cancel_target.tif zaten var. Üzerine yazılsın mı?';
  buttons ['Evet', 'Hayır']; clicking 'Evet'
pressing Durdur at tile 60/529; .part present during run: ['.cancel_target.tif.r3by72ul.part']
task ended 3.90 s after start
status label : Durduruldu. Diske eksik dosya yazılmadı.
was_cancelled flag was set: True
destination AFTER : 11376632 bytes  md5 b5fcc2ffeeda8b1eac9d1580551f62de
DESTINATION UNCHANGED: True
leftover .part files: []
```

**What was observed on disk, precisely.** The `.part` file **existed during the run** and
was **gone afterwards**. That ordering is the whole point: had the listing been empty both
times, the test would have proved only that nothing was ever written, not that the cleanup
ran. The destination's md5 is unchanged, so a later run cannot mistake a cancelled run's
leavings for a cache hit — the failure Project 1 hit once.

Cancellation was honoured **3.90 s** after the click, at the tile boundary, exactly as
designed.

**A defect in my first version of this test, and how it was caught.** It bypassed the
overwrite prompt by monkey-patching `os.path.exists`. The dialog uses `pathlib.Path.exists`,
which does not route through it, so the modal appeared, no script could answer it, and the
test hung for ten minutes before I killed it — reporting nothing. Had I read the disk state
at that point I would have seen an unchanged destination and no `.part`, and could have
called it a pass, when in fact the job had never started. The corrected test answers the
modal from a timer inside the modal's own event loop, which also exercises the overwrite
prompt shown above.

---

## 7. The equivalence check, and the timing

### 7.1 Pixel identity — the claim

Four independent full-granule runs of the same input, in three environments:

| run | environment | thread | pixel SHA-256 | file bytes |
|---|---|---|---|---|
| WP1's CLI output | gencp env | main | `ca3b4c41…a55ad03c` | 1,254,567,338 |
| CLI, re-run here | gencp env | main | `ca3b4c41…a55ad03c` | 1,254,567,338 |
| **plugin, `QgsTask`** | **QGIS app process** | **worker** | **`ca3b4c41…a55ad03c`** | **1,254,567,338** |
| `superresolve` direct | QGIS app process | main | `ca3b4c41…a55ad03c` | 1,254,567,338 |

**Distinct pixel hashes: 1.** The same holds on the 1024 px fixture — `41b54b77…` across
the CLI, the plugin, the clean-profile install, and the bundled interpreter.

**Which is the claim and which is incidental.** The **pixel hash is the claim**. The file
size is **incidental** and is reported only so it is on the record. WP1 established that
identical pixel content produces 1,275,560,750-byte and 1,254,567,338-byte files under
different `GDAL_CACHEMAX`, and that GDAL sizes its cache from installed RAM. Here the file
sizes happen to agree because `gdal.GetCacheMax()` is **1,932,735,280 in both stacks** (§1)
— an agreement of configuration, not a property being asserted. §4.1(b) shows the same
pixels landing in a **different-sized file** as soon as one environment variable changes.

That the pixel hash survives Pillow 12.2.0 vs 12.3.0, numpy 2.4.6 vs 2.5.0, rasterio 1.4.4
vs 1.5.0 and GDAL 3.12.3 vs 3.12.4 is a stronger result than the requirement asked for, and
was not assumed: §1 records the version split precisely because it could have broken this.

### 7.2 Gate S on the plugin's output

`tubitak/sr/tests/gate_s.py`, unmodified, run on three plugin-produced rasters:

| source | output | verdict |
|---|---|---|
| `fixture_1024.tif` | plugin (default profile) | **PASS 5/5**, S5: 441 centres, worst offset `dx 0.0, dy 0.0` |
| `tiles36SVJ/TCI.tif` (full granule) | plugin, `QgsTask` | **PASS 5/5**, 441 centres, `dx 0.0, dy 0.0` |
| `fixture_1024.tif` | plugin, clean profile | **PASS 5/5**, 441 centres, `dx 0.0, dy 0.0` |

### 7.3 Timing, and what the difference actually is

**Same granule, same 529 tiles, same machine.**

| run | wall clock |
|---|---|
| WP1's CLI figure (`00-recon` sibling, `01-wp1.md` §3) | **26.90 s** |
| CLI re-run here, gencp env | **25.65 s** |
| **plugin, `QgsTask`, inside QGIS** | **37.70 s** (core) / **37.89 s** (dialog `_start` → finish handler) |
| `superresolve` on the **main thread** inside QGIS | **38.22 s** |

**It is not threading overhead. Stated plainly, and it is measurable rather than inferred.**
Two figures settle it. The `QgsTask` wrapper costs **0.19 s** — the gap between the dialog's
own 37.89 s and `sr_core`'s internal 37.70 s. And running the *identical* call on the QGIS
**main thread**, with no task at all, takes **38.22 s** — if anything slower than the worker.
Threading accounts for none of the 12.6 s.

**It is the library stack.** Four micro-benchmarks, each run in both interpreters, same
seeded input, isolating one stage:

| stage | CLI env | QGIS process | difference |
|---|---|---|---|
| bicubic resample, 529 tiles equivalent (Pillow) | 7.19 s | 9.87 s | **+2.68 s** |
| `StreamingMosaic._emit` normalise arithmetic (numpy) | 1.57 s | 5.11 s | **+3.54 s** |
| deflate write, 21960² × 3 (GDAL) | 11.13 s | 12.42 s | **+1.29 s** |
| read 529 source tiles (GDAL) | 0.80 s | 0.83 s | +0.03 s |
| **attributed total** | | | **+7.54 s** |
| **observed difference** | 25.65 s | 38.22 s | **+12.57 s** |

The largest single contributor is not the resampler but **numpy's normalise arithmetic,
3.3× slower under numpy 2.5.0 than 2.4.6** for `_emit`'s divide-where / rint / clip / cast
chain at full scene width. That was not what I expected before measuring, and is recorded
because a future reader will otherwise assume the resampler.

**The residual is not determined.** 7.54 s of the 12.57 s is attributed; **the remaining
5.03 s (40 %) is not.** The benchmarks run each stage in isolation while the real pipeline
interleaves them under different memory pressure — measured peak RSS 2.967 GB inside QGIS
against 2.663 GB in the CLI — so some residual is expected, but its size is not accounted
for and I am not going to guess at it. What *is* settled, and is what the requirement asked
for, is that the difference is **not** the `QgsTask`.

**Consequence for the demonstration:** none. 38 s for a full Sentinel-2 granule is a
demonstration that finishes while someone is still describing it.

---

## 8. The clean-profile test

The closest available stand-in for "does it work on someone else's machine". Run under the
**cocoa** platform, not offscreen: a fresh profile cannot start headless on macOS because
QtKeychain's write never returns there.

A brand-new profile `gencp_sr_clean` was created, the zip unpacked into it, and the plugin
loaded the way QGIS loads it:

```
profile dir : .../QGIS4/profiles/gencp_sr_clean/
platform    : (default = cocoa)
available   : ['gencp_super_resolution']
loadPlugin  -> True
startPlugin -> True
menu action : GenCP Super-Resolution...
sr_core from: .../gencp_sr_clean/python/plugins/gencp_super_resolution/sr_core/__init__.py
status      : Bitti · 9 karo · 0.5 sn · 11 MB Katman eklendi ve girdiyle hizalı.
output      : exists=True bytes=11376632
layers      : ['clean_profile_x2']
```

The `sr_core from:` line is the one that matters: the core was resolved from the
**vendored copy inside the profile**, not from the repository checkout. Without vendoring
the plugin installs, loads, and fails on the first click — the failure Project 1's zip had
once. `build_sr_plugin_zip.py` therefore checks its own output before it exits: metadata
present, `classFactory` module present, `sr_core/run.py` present, no `.pyc` leaked (a stale
`.pyc` compiled by a different Python installs cleanly and fails on someone else's machine).

Project 1's plugin and the two STAC plugins in the default profile were left untouched.

---

## 9. Following my own demo document, and the two defects that found

`docs/02b-demo-tik-sirasi.md` was written first, then executed from a cold start against a
**fresh profile** (`gencp_sr_demo`), following its steps in order — including
`build_sr_plugin_zip.py` from a deleted `sr_dist/`, installing through QGIS's own
`installFromZipFile`, and choosing the input **from a loaded layer**, which is the path the
document tells the reader to use and which nothing had exercised until then.

**20 scripted checks, 18 passed on the document as written.** Every line the document
quotes verbatim — the source line, the scale label, the estimate, the final status — matched
character for character. Two defects were found and fixed:

**Defect 1 — step 2.11 told the reader to do something QGIS had already done.** The
document said "Bu adımı atlamayın" and instructed the reader to tick the enable checkbox.
Measured on a genuinely fresh profile, after `ZIP'ten Kur` and nothing else:

```
QgsSettings PythonPlugins/gencp_super_resolution = True
started (present in qgis.utils.plugins)          = True
menu action registered                           = GenCP Super-Resolution...
```

QGIS enables and starts a zip-installed plugin itself. The instruction would have sent a
beginner hunting for an unticked box that is already ticked — worse than no instruction at
all, for exactly the reader this document is written for. It is now a **verification** step
that says so, with the fallback kept for the case where the box somehow is not ticked.

*(The walkthrough's own `startPlugin -> False` line is this same fact seen from the other
side: `qgis.utils.startPlugin` returns False when the plugin is already started. That was a
defect in my test script, not in the plugin — the menu action was registered and every
subsequent step passed.)*

**Defect 2 — the document promised a progress reading the user will not see.** It said the
status would show `Karo 1 / 529`, `Karo 2 / 529`. Polling at 150 ms, the first value
actually observed was `Karo 5 / 529`; tiles complete at roughly fifteen a second. The
document now says a number like `Karo 12 / 529` appears and climbs quickly, that the first
few cannot be caught, and that what matters is the number **not stopping**.

The document carries a note at the top saying it was tested once, that 2 of 20 steps were
wrong, and pointing here.

---

## 10. Terminology

`tubitak/docs/terimler.md` is the authority and was **not edited** — it belongs to Project 1
and this work package has no mandate over it. Four terms this package needed are not in it,
because Project 1 had no scale factor and no resampler. They are recorded in `strings.py`'s
module docstring and here:

| English | Turkish | note |
|---|---|---|
| super-resolution | süper çözünürlük | |
| scale factor | ölçek katsayısı | |
| bicubic | bikübik | a proper name, not translated |
| upsampler / method | yöntem | the dialog calls the setting "Yöntem" |

Existing terms are used as that file fixes them: katman, raster katman, KRS, kapsam, karo,
karo bindirmesi, çözünürlük, ilerleme çubuğu. Decimal comma is used in displayed numbers
(`10 m`, `37,7 sn`), and no suffix is glued to a numeral, because Turkish suffixes follow
how a number is read and cannot be produced by string formatting.

---

## 11. Repository hygiene

`sr_core`, `gencp_core`, Project 1's plugin, and the upstream pix2pix tree are all
unmodified — `git status --porcelain` against each is empty. Nothing under
`tubitak/sr/sr_data/` was read or written. No `git add`, `git commit`, `git checkout` or
`git stash` was run.

New files, all of them mine:

```
tubitak/sr/sr_plugin/{__init__,plugin,dialog,strings,task,qtcompat}.py, metadata.txt
tubitak/sr/tests/plugin_guards.py
tubitak/sr/build_sr_plugin_zip.py
tubitak/sr/docs/02b-plugin.md
tubitak/sr/docs/02b-demo-tik-sirasi.md
```

All rasters written under `tubitak/data/sr_wp2b/` and `tubitak/data/sr_dist/`;
`git status --porcelain --untracked-files=all tubitak/data` returns **zero lines**.

Two QGIS profiles were created for testing (`gencp_sr_clean`, `gencp_sr_demo`) plus one for
the enable probe (`gencp_sr_enable`). They live in
`~/Library/Application Support/QGIS/QGIS4/profiles/`, outside the repository. The plugin was
also installed into the `default` profile; Project 1's plugin there was not touched.

No packages were installed. No institutional imagery was involved: the only raster read is
`tubitak/data/tiles36SVJ/TCI.tif`, public Copernicus Sentinel-2 L2A, product
`S2C_36SVJ_20260430_0_L2A` (`02a-reflectance-corpus.md` §1).

---

## 12. Open items

1. **`rasterio` is the dependency most likely to be missing on another machine, and the
   plugin fails at the first click if it is.** `sr_core` reads and writes through
   `rasterio`, and the dialog uses it to read the source's properties. It is present in
   this QGIS 4.2.1 macOS build's `site-packages`, but rasterio is **not** a standard part
   of the QGIS stack the way `osgeo.gdal` is — QGIS always ships the GDAL Python bindings
   and does not always ship rasterio. `numpy` and `Pillow` are far safer bets. Nothing in
   the plugin currently checks for it or reports its absence in Turkish: the failure would
   surface as a `ModuleNotFoundError` in the log and an unhelpful `Başarısız:` line. A
   startup check that names the missing module, and a decision about whether to port
   `sr_core`'s I/O to `osgeo.gdal`, both belong to whoever hands this to someone else.
2. **QGIS 3.x and non-macOS are reasoned about, not tested.** All Qt access goes through
   the `qgis.PyQt` shim and `qtcompat.member`, and no Qt5-only or Qt6-only API is used, so
   `qgisMinimumVersion=3.28` is an argument rather than a measurement. `metadata.txt` says
   so in its `about` field.
3. **5.03 s of the 12.57 s CLI-to-QGIS gap is not determined** (§7.3). Attributing it would
   need the stages instrumented inside one real run rather than benchmarked in isolation.
4. **numpy 2.5.0 is 3.3× slower than 2.4.6 on `_emit`'s arithmetic** (§7.3). Not
   investigated. It is the single largest attributed cost and will matter more, not less,
   when WP4 adds inference alongside it.
5. **`onnxruntime` is importable in the QGIS *application* process on this machine** (it is
   only the bundled interpreter that cannot load it). The bicubic path's independence from
   it was therefore verified by blocking it (§4.1a) and separately in an interpreter where
   it genuinely fails (§4.1b) — but a machine where the *app process* also cannot load it
   has not been tested, and that is the machine WP4 will care about.
6. **The model field is disabled and wired to nothing.** WP4 must add the method to
   `sr_core.run.METHODS`, enable the field when that method is selected, and extend
   `_blocker()` to refuse a missing model file. The dialog has the slot; it has no
   behaviour behind it.
7. **`scale` is fixed at 2 in the dialog.** `sr_core` accepts any power of two and WP1
   exercised only 2 end to end. Making it a control means deciding what the fixed label
   becomes and re-checking the estimate arithmetic.
8. **Peak RSS inside QGIS is 2.967 GB for one granule**, against 2.663 GB for the CLI, on a
   36 GB machine. It is fine now and will matter when an ONNX session sits alongside it;
   `Gelişmiş → Karo boyutu 256` roughly halves the accumulator's share.
9. **`qtcompat.py` is duplicated** between this plugin and Project 1's, deliberately (a
   shared import would couple two plugins that must install independently). If a third
   plugin appears, the duplication should be revisited rather than tripled.
10. **The demo document names absolute paths under `/Users/vedat/`.** Correct for the
   demonstration machine and wrong for anyone else's. Making it portable means either a
   placeholder the reader substitutes, or shipping the zip somewhere stable.
11. **Nodata is still bicubic-blind** — WP1's open item 1, unchanged and inherited. 36SVJ is
    a full granule so the demonstration does not hit it, but a demonstration on 36SWJ
    (25.4 % nodata) would mix the fill value into valid pixels along the granule edge.
