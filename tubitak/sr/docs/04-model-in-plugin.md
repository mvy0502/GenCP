# Project 2, WP4 — the trained model in the plugin, ready to demonstrate

**Run:** 2026-08-30. **Repository:** `mvy0502/GenCP`, branch `tubitak-tr`. **No git command
was run.**

**The objective, and whether it is met.** Someone who has never seen the plugin must be able
to open QGIS, follow a written click order, and get a super-resolved output from the trained
model. **That works.** It was verified by following the document itself, from a cold start, in
a fresh QGIS profile: **0 failed steps of 24.**

**The hard boundary held.** `tubitak/qgis_plugin/` — symlinked into the live QGIS profile,
demonstrated the same day — was not touched. `git status --porcelain` against it, against
`tubitak/gencp_core/` and against every upstream path is empty.

---

## 0. The risk that could have cost Friday, checked first

`onnxruntime` inside QGIS's bundled Python on macOS was the highest-risk item, because of the
code-signing split WP0 documented. It was checked **before anything else was built**, because
if it fails nothing else matters.

Run inside the QGIS **application** process (`run_in_qgis.sh`, which uses the app binary, not
the bundled `python3.12`):

```
python 3.12.11  executable .../QGIS-final-4_2_1.app/Contents/MacOS/QGIS-final-4_2_1
onnxruntime 1.29.0 imported OK from /Users/vedat/.local/lib/python3.12/site-packages/...
available providers: ['CoreMLExecutionProvider', 'AzureExecutionProvider', 'CPUExecutionProvider']
InferenceSession constructed in 0.02 s     provider in use: ['CPUExecutionProvider']
  input  input ['batch', 3, 'height', 'width'] tensor(float)
  forward 128 -> (1, 3, 256, 256) in 0.017 s, finite=True
  forward 256 -> (1, 3, 512, 512)            (dynamic axes work inside QGIS)
VERDICT: onnxruntime RUNS the model inside the QGIS application process.
```

**What a failure would have looked like:** an `ImportError` on `import onnxruntime`, or a
`dlopen` refusal naming "different Team IDs" — the exact error WP2B reproduced in the bundled
interpreter. It did not occur here. The split affects the bundled `python3.12`, not the
application binary, and the plugin runs in the application binary.

---

## 1. The blocking item: building a valid input

**Nothing on disk was a valid model input before this.** WP2A downloaded B02, B03 and B04 as
three separate single-band files; the network takes three channels at once.

`tubitak/sr/sr_train/make_model_input.py` stacks them.

**Band order was confirmed, not assumed, against three independent sources:**

| source | says |
|---|---|
| `sr_data.params.BANDS` — the tuple the corpus builder used | `("B02", "B03", "B04")` |
| `03a-corpus-registration.md` §1 | "Bands stored, in this order: B02, B03, B04 (blue, green, red)" |
| the ONNX file's own `band_order` metadata | `B02,B03,B04` |

The builder **refuses to run** if `params.BANDS` and the model's declared `band_order`
disagree. A silently transposed channel order would produce output that looks entirely
plausible and is wrong — this project's dominant failure class.

It also asserts every band is on the same grid, comparing the **transform**, not only CRS and
shape: WP2A open item 4 recorded that all five granules share EPSG:32636 and 10980 × 10980, so
a check omitting the transform passes every wrong pairing.

**Two files were built, both under gitignored `tubitak/data/sr_model_input/`:**

| file | purpose | size | extent |
|---|---|---|---|
| `MODEL_INPUT_36SXJ_20260527_B02-B03-B04_uint16DN_10m.tif` | whole granule | 557,029,309 B | 10980 × 10980 |
| **`DEMO_INPUT_36SXJ_4096px_B02-B03-B04_uint16DN_10m.tif`** | **the demonstration input** | 78,048,507 B | 4096 × 4096 |

Both are **uint16 DN**, 3 bands, band 1 = B02, EPSG:32636, nodata 0, with a
`GENCP_SR_INPUT` provenance tag naming the granule, product ID, band order and the
normalisation to apply at inference. `DEMO_INPUT_` sha256
`7bfa3638f3eacd919fc2ecdcb36286c51e49dcafa2d1ca841be3e32ec63b1aed`.

**36SXJ was chosen deliberately: it is the held-out granule.** The demonstration therefore
runs the model on ground it was never trained on.

---

## 2. Wiring the model in

`tubitak/sr/sr_plugin/onnx_upsample.py` (new, 152 lines) plus edits to `dialog.py`,
`task.py`, `plugin.py`, `strings.py`.

### 2.1 The seam it plugs into

`sr_core.run.superresolve` gained **one purely additive keyword argument, `upsampler=None`**.
Nothing else in `sr_core` changed; no existing signature or default was altered, and every
existing caller omits it. This is the seam WP1 wrote the `Upsampler` interface for — the Gate
S registration says the arithmetic "must give the same verdict for `BicubicUpsampler` today
and for a trained ONNX model in WP4". A trained model needs a constructor argument the
`METHODS` dictionary cannot supply (a file path), so the object is passed in rather than
looked up.

**Regression check, as the brief required:** the bicubic path's pixel SHA on the same input
is **`ca3b4c41b6661aed8cc3c771d0cdd5a44dd1f70684f18932f1644beba55ad03c`** — identical to
WP2B's. The `sr_core` edit and the `sys.path` change altered no pixel.

### 2.2 Nothing about the model is a literal in the plugin

Normalisation constant, scale factor, channel count, band order, corpus registration id and
the training tile are all read from the ONNX file's `metadata_props` at selection time. The
dialog displays them:

```
gencp_sr_x2_v1.onnx · DN/5000 · 2× · 3 bant B02,B03,B04 · adım 16306/20000
```

A plugin that hard-coded `5000.0` would keep working and be silently wrong the day a model is
retrained with a different divisor. A model missing any required key is **refused**, not run
under guessed defaults.

`onnxruntime` is imported **lazily**, inside the constructor, so the bicubic path still loads
and runs where it cannot be imported at all.

### 2.3 The refusal — triggered, not assumed

**This is the check that matters most, and it was verified by actually doing it.**

Feeding the 8-bit TCI to the model path, inside QGIS, through the dialog:

* **Run went dim** (`blocked_input_not_model`);
* **no output file was written** — the refusal happens before any tile runs;
* the status line showed, in Turkish:

> Model **16 bit tam sayı (uint16)** yansıtma değerleri bekler; seçilen dosyanın veri tipi
> **uint8**.
>
> TCI dosyası 8 bitlik *görsel* bir birleşimdir; modelin eğitildiği veri bu değildir ve model
> bu dosyayla anlamsız sonuç üretir.
>
> Model yolu için adı **MODEL_INPUT_** ile başlayan, B02,B03,B04 bantlarını içeren yansıtma
> dosyasını seçin. TCI dosyasını **Bikübik** yöntemiyle kullanabilirsiniz.

It names what was expected, what was given, and which file to use instead. The same refusal
fires from the CLI and writes nothing.

**Three separate guards, because band count alone is not enough** — the TCI has three bands:

| guard | catches |
|---|---|
| band count vs `in_channels` | a 1-band or 4-band raster |
| **dtype must be uint16** | **the 8-bit TCI — this is the one that fires** |
| clear-pixel p99.9 ≥ 300 DN | a TCI someone has *converted* to uint16, which would pass the dtype check |

### 2.4 Two WP2B open items closed

**`sys.path.append` instead of `insert(0)`.** WP2B demonstrated that inserting at position 0
made a bare `import strings` anywhere in the QGIS process resolve to this plugin's module.
Verified with a planted rival: a `strings.py` earlier on `sys.path` **now wins**. Stated
precisely, because the first version of this test over-claimed: appending guarantees that
another provider of a name wins; it cannot stop us resolving a name **nothing else provides**,
and `import strings` with no rival present still finds ours. That is not shadowing.

**`rasterio` checked at plugin load.** `missing_requirements()` runs before the dialog opens
and shows a Turkish message naming the package, instead of a `ModuleNotFoundError` behind a
bare `Başarısız:`.

---

## 3. Speed

### 3.1 Inference tile size, measured

The network is fully convolutional and the graph has dynamic spatial axes, so the inference
tile need not match the training tile. Fixed extent, 4096 × 4096 source px of 36SXJ, overlap
32 throughout:

| tile | tiles | wall clock | overlap redundancy |
|---|---|---|---|
| 128 (the training tile) | 1849 | **32.6 s** | 1.778× |
| 256 | 361 | 23.2 s | 1.306× |
| **512 (chosen)** | **81** | **22.4 s** | **1.138×** |

On a smaller 2048² extent, 1024 and 2048 were *slower* than 512 (9.2 s and 4.6 s against
5.6 s at 256), so nothing above 512 was carried forward. **512 is 1.46× faster than 128.**

**Pixel agreement against tile 128**, on the 2048² extent:

| tile | max abs difference | mean | pixels differing |
|---|---|---|---|
| 256 | 8 DN | 0.0109 | 1.030 % |
| 512 | **8 DN** | 0.0074 | 0.699 % |
| 1024 | 8 DN | 0.0093 | 0.887 % |

**Stated tolerance: max 8 DN, on 0.7 % of pixels, all at tile seams. That is 20 % of the
model's own measured MAE of 39.7 DN** (WP3B §5.3: 0.00794 normalised × 5000). Within that
tolerance the larger tile gives the same pixels; it is not bit-identical and is not claimed
to be. The overlap stays 32, still above the measured receptive field of 31 px.

**The model's declared `infer_tile_src_px` (128) remains the TRAINING contract and is what
the model reports.** 512 is a plugin-side inference choice, documented at
`dialog.MODEL_INFER_TILE_PX` with these measurements in the comment.

### 3.2 The demonstration extent

**`DEMO_INPUT_36SXJ_4096px_…tif` — 4096 × 4096 source px = 40.96 km square, 36SXJ.**

| path | measured, in QGIS, through the dialog |
|---|---|
| **model on the demo extent** | **22.0 – 23.3 s** across three runs |
| bicubic on the full 36SVJ TCI | 38.9 s |
| model on a full granule (extrapolated from 22.4 s at 4096², ×7.18 area) | ~161 s — **shown as a pre-computed result, not run live** |

The live click-through uses the 4096 px extent and finishes in about 23 seconds. The
document says so.

---

## 4. Verification

**Gate S on the model path's output** (source = the demo input, output = the raster QGIS
produced, scale 2): **PASS, 5/5.** S5 compared 441 pixel centres, worst offset `dx 0.0,
dy 0.0`. S4: 8192 × 8192 from a 4096 × 4096 source.

**Plugin against CLI, model path, same input, same tile:**

| output | pixel SHA-256 |
|---|---|
| plugin, through the QGIS dialog | `5e3de3cfcf4cf60910d6763712350fbfe42a1116abe4767fc77542bc0f374cd2` |
| CLI, `run_model.py` | `5e3de3cfcf4cf60910d6763712350fbfe42a1116abe4767fc77542bc0f374cd2` |

**Identical.** File sizes also matched at 322,765,811 B, which is incidental and not the
claim — WP1 established that identical pixels can produce different file bytes under a
different `GDAL_CACHEMAX`.

That is the whole verification budget. No metrics were added.

---

## 5. In-QGIS test, and the two defects it found

21 checks, driven through the dialog in the default profile with both plugins installed:
the model path runs and adds an aligned layer; the TCI is refused; the bicubic path still
works. **21/21 after two fixes. The first run was 19/21, and both failures were real.**

**Defect A — switching method left a stale refusal on screen.** After the model refused the
TCI, selecting Bikübik re-enabled Run but the model's refusal text stayed in the status line:
two contradictory signals at once. `_on_method` was calling `_validate()` without
`_recheck_input()`. Fixed.

**Defect B, the serious one — selecting a different layer did nothing.** The
`layer_cb.layerChanged` connection **has never fired** in QGIS 4.2.1 / PyQt6. Every earlier
test, in WP2B as well as here, passed only because the chosen layer was already current when
the dialog was **constructed**, so `__init__`'s own `_refresh_source()` had read it. Switching
layers in an open dialog left the source line, the estimate and the model input check all
stale — and **switching layers is exactly what the demonstration document tells the presenter
to do** in Bölüm 4 and Bölüm 5. It would have shown wrong information live, and the TCI
refusal would not have fired. Fixed by additionally connecting `currentIndexChanged`, which
does fire. Found only by driving the dialog with two layers loaded; it is invisible to code
reading and to any test that loads one layer.

**Defect C — a decimal period where `terimler.md` requires a comma.** The completion line
read `23.0 sn`; the document said `23,0 sn`. The document was right. WP2B shipped this and
its walkthrough missed it because that check compared only the line's prefix. Fixed in the
dialog, and the walkthrough now asserts the comma with a regular expression.

---

## 6. Following the demonstration document

`02b-demo-tik-sirasi.md` was extended to cover both methods and then **executed from a cold
start in a fresh QGIS profile** (`wp4_demo`), following its steps in order — building the zip,
installing through QGIS's own `installFromZipFile`, adding the layer, selecting the model,
running, and deliberately feeding it the wrong file.

**24 checks, 0 failed.** Every string the document quotes verbatim matched what the dialog
showed, character for character:

```
3.2.9   '4096 × 4096 piksel · 3 bant, uint16 · EPSG:32636 · 10 m çözünürlük'
3.2.13  'gencp_sr_x2_v1.onnx · DN/5000 · 2× · 3 bant B02,B03,B04 · adım 16306/20000'
3.3.18  'Bitti · 81 karo · 21,8 sn · 323 MB Katman eklendi ve girdiyle hizalı.'
```

The document carries the failure-recovery table the brief asked for, including the one
instruction that matters if the model path breaks on the day: **fall back to Bikübik**, which
needs no model file and no `onnxruntime`.

---

## 7. The three-panel comparison — presentation material, not evidence

`tubitak/data/sr_compare/three_panel_36SXJ.png` (gitignored).

**Location:** 36SXJ, source window col 1800 row 1500, 256 × 256 px = **2.56 km square**, UTM
north-west corner E 648720 N 4354320, EPSG:32636.

**Stretch, stated:** per-band **2nd–98th percentile computed on the SOURCE only** and applied
**identically** to all three panels. Nearest-neighbour zoom, so no panel is resampled for
display beyond integer replication.

| band | stretch range |
|---|---|
| B02 | 114 – 1514 DN |
| B03 | 369 – 2235 DN |
| B04 | 167 – 2644 DN |

Panels: source 10 m (256 px) · bicubic 5 m (512 px) · model 5 m (512 px). **This is a
picture, not a measurement.** The measurements are in WP3B §5 and they carry their own scope
caveat.

---

## 8. What was traded for a working demonstration

The brief said to take the working demonstration where it conflicts with rigour, and to write
down what was traded. Three things:

1. **The inference tile is 512, not the 128 the model declares.** Faster by 1.46×, at a cost
   of up to 8 DN on 0.7 % of pixels at tile seams. Setting it to 128 restores exactness at
   32.6 s instead of 22.4 s on the demo extent.
2. **The demonstration runs a 40.96 km square, not a granule.** A full granule is ~161 s on
   the model path — presentable as a pre-computed result, not as a live click-through.
3. **The three-panel image uses a stretch fitted to the source.** It flatters all three panels
   equally, but it is a chosen stretch and a different one would change how the difference
   reads.

---

## 9. Repository hygiene

`tubitak/qgis_plugin`, `tubitak/gencp_core`, `models/`, `data/`, `options/`, `util/`,
`test.py`, `train.py` — **0 changes each.** `git status --porcelain --untracked-files=all` on
`tubitak/data` returns **0 lines**: the input rasters, the outputs, the model and the
comparison image are all gitignored. **No git command was run.** 16 repository paths
referenced by the new files all resolve.

Modified: `sr_core/run.py` (+20 −5, additive), `sr_plugin/{dialog,plugin,strings,task}.py`,
`tests/plugin_guards.py`, `docs/02b-demo-tik-sirasi.md`. New: `sr_plugin/onnx_upsample.py`,
`sr_train/{make_model_input,run_model}.py`, this document.

Plugin zip `tubitak/data/sr_dist/gencp_super_resolution.zip`, 42,655 B, sha256
`350f3b76de2aa54009184298dcf095d27a02df3c71c606b470692829b26468e1`, 14 files with `sr_core`
vendored. `plugin_guards.py` passes G1/G2/G3 — its G2 rule was **refined**, not relaxed:
`onnxruntime` is now permitted but **only lazily**, and a module-level import is still caught
by the known-false fixture, with a new known-true fixture proving a lazy import is accepted.

---

## 10. Open items

1. **`layerChanged` never fired** (§5, Defect B) and was invisible to every prior test. The
   lesson generalises: a UI signal test that loads one layer cannot detect a broken selection
   handler. Other single-object handlers in this dialog have the same blind spot and were not
   audited.
2. **The model path depends on `onnxruntime` being importable in the QGIS application
   process.** It is, on this machine. On a machine where it is not, the model option fails and
   the fallback is bicubic — which the demo document covers, but which has not been tested on
   such a machine.
3. **The 8 DN tile-seam difference at tile 512** is measured on one extent of one granule.
4. **`MODEL_INPUT_` for the other four granules has not been built.** Only 36SXJ exists; the
   builder takes a `--granule` argument and each takes about a minute.
5. **The demonstration input is the held-out granule, which is honest but not typical.** No
   model output has been produced over a training granule for comparison.
6. **Nothing here re-measures accuracy.** WP3B's numbers stand, with their scope caveat: the
   model inverts a known synthetic blur measured 20 m → 10 m, and **this work package produces
   no evidence about 10 m → 5 m either.** The 5 m output may be shown as what the pipeline
   produces; it may not be called validated.
7. **`last.pt.TRUNCATED`** from WP3B is still in the run directory, and the training save path
   still has no atomic-write discipline (WP3B open item 3).
