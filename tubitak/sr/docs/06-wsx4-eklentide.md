# Project 2, WP6 — hosting wsx4 in the plugin

**Run:** 2026-08-30. **Repository:** `mvy0502/GenCP`, branch `tubitak-tr`. **No git command
was run.** `tubitak/qgis_plugin/` and `tubitak/gencp_core/` are untouched.

**This is the last work package that touches the plugin.** Nothing is left half-wired: the
three methods, the crop-tiling path, the contract resolution and the guards were all driven
through the real dialog and the demonstration document was followed from a cold start.

---

## 0. Result

**wsx4 runs in QGIS on a Turkish scene, through the dialog, in 25–27 s.**

| | |
|---|---|
| scene | 36SXJ (Cappadocia), the held-out granule |
| extent | 1024 × 1024 source px = **10.24 km square** |
| output | **4096 × 4096, 4 bands, 2.5 m**, 107,069,223 B |
| tiles | 36, tile 256 source px, overlap 65, **crop margin 130 output px** |
| wall clock, through the dialog | **27.0 s** and **25.2 s** on two runs |
| **Gate S at scale 4** | **PASS 5/5** — pixel size exactly 2.5 m, origin offset 0.0, 4096 = 4 × 1024, worst pixel-centre offset `dx 0.0, dy 0.0` |
| plugin vs CLI | **pixel-identical**, `6b71d037…` both |

And the three regressions, all clean:

| check | result |
|---|---|
| **bicubic pixel SHA** | **`ca3b4c41b6661aed8cc3c771d0cdd5a44dd1f70684f18932f1644beba55ad03c` — unchanged** |
| our scale-2 model path | pixel-identical to WP4's output, `5e3de3cf…` |
| wsx4 weights in the repo, the zip, or the installed plugin | **0, 0, 0** |

---

## 1. Crop the margin, do not feather

### 1.1 Where the margin comes from

**From the reference tool's own configuration, not from our provenance mechanism**, because
`wsx4_spatrad.onnx` carries **no `metadata_props` at all** — established in WP5 and
re-confirmed here. Its parameters live in `wsx4_spatrad.yaml` beside it, which is the file
the tool itself reads:

```yaml
bands: [B2, B3, B4, B8]
factor: 4.0
margin: 130
model: wsx4_spatrad.onnx
```

**margin = 130 OUTPUT pixels** = 130 / 4 = **32.5 source pixels** = 325 m.
`run.py:326` confirms the unit: `margin_in_meters = target_resolution * margin`.

The plugin reads that yaml rather than restating its numbers, so a different model of theirs
is a different sidecar and not a code change.

### 1.2 The geometry, and how it is guaranteed

`sr_core.mosaic.crop_keep_bounds` computes a keep-box per tile and **proves the boxes
partition the output exactly** — asserted on the intervals, in integer arithmetic over a few
hundred numbers, rather than by painting a coverage raster, which at 21960² would cost half a
gigabyte to learn the same fact less reliably.

The rule, per axis: a tile keeps from where its predecessor stopped, to `margin` inside its
own trailing edge; the first starts at 0 and the last runs to the end. **A boundary side is
never cropped**, because there is no neighbour to supply its context and cropping it would
leave the raster border unwritten.

That forces the overlap: `kept_start[i] >= tile_start[i]·s + margin` requires
**overlap ≥ 2·margin / s = 2 × 130 / 4 = 65 source pixels**. `min_overlap_for_margin`
computes it and the dialog sets it; a smaller overlap is **refused before any tile runs**:

```
tile 1 would keep output pixels from 1918, which is less than 130 px inside its own
leading edge at 1920. The overlap is too small for a margin of 130 output px: it must
be at least 65 source px, and the tile layout gives less.
```

Verified on paper before any raster, four layouts:

| layout | tiles | kept area vs output area |
|---|---|---|
| 512², tile 128, overlap **65** | 64 | 4,194,304 == 4,194,304 — **EXACT** |
| 512², tile 128, overlap **32** | — | **REFUSED**, message above |
| 1000², tile 256, overlap 65 | 25 | 16,000,000 == 16,000,000 — EXACT |
| 300², tile 128, overlap 65 | 16 | 1,440,000 == 1,440,000 — EXACT |

`CropMosaic.close()` additionally asserts that the pixels actually written equal
`out_h × out_w`. **Zero uncovered, zero written twice**, both by construction and by
assertion.

### 1.3 Measured against a single-tile reference

The whole 512 × 512 chip through the graph in **one** forward pass, no tiling at all, is the
reference. Everything else is compared against it:

| scheme | tile | overlap | tiles | **max abs diff** | mean | pixels > 16 DN |
|---|---|---|---|---|---|---|
| **CROP, margin 130** | 256 | 65 | 9 | **1 DN** | 0.0000 | **0** |
| **CROP, margin 130** | 128 | 65 | 64 | **1 DN** | 0.0001 | **0** |
| feather (WP5's scheme) | 128 | 32 | 25 | 37 DN | 0.1612 | 691 |
| feather (WP5's scheme) | 128 | 64 | 49 | 20 DN | 0.0347 | 7 |

**Cropping removes the artefact: 1 DN against feather's 37 and 20.** One DN is float32
rounding at the uint16 cast, not a difference in kind. This confirms WP5's diagnosis — the
residual was the *blending*, not context starvation, and no overlap was ever going to fix it,
because averaging two ESRGAN predictions is not the same as either of them.

**The feather path is unchanged** and is still what our own L1-trained model uses. Nothing
above the WP6 section in `mosaic.py` was edited; a model that does not ask for cropping never
reaches the new code. The bicubic SHA (§0) is the evidence.

---

## 2. Scale and normalisation come from the model

`dialog.SCALE = 2` is gone. What replaced it:

* **`BICUBIC_SCALE = 2`** — for the bicubic path only.
* **`_scale()`** — returns the model's own scale when a model is loaded. Gate S passes at
  s = 4 exactly as at s = 2; four is a power of two, so the exact-equality assertion in the
  Gate S registration holds without amendment.

### 2.1 The normalisation declaration, and the guard fired on purpose

| model | normalisation | why |
|---|---|---|
| ours, `gencp_sr_x2_v1.onnx` | **external**, `DN / 5000` applied by the caller | our export writes it into `metadata_props` |
| **wsx4** | **internal** — the graph does `Div 10000` in and `Mul 10000` out itself, and `run.py` reads with `scale=1.0` | WP5, from the graph's own constants |

`OnnxUpsampler.upsample` honours the declaration. **Deliberately mis-declaring it**, on a
128 × 128 chip of real 36SXJ data (input DN median 517):

**Predicted, before running:** the graph normalises internally, so an external divisor D
makes the network see an input D× too small; the graph's `Mul` and our un-normalise do **not**
cancel the two divides, because the network has biases and LeakyReLU and is not linear. So the
output is not wrong by one clean factor — the give-away is a ratio nowhere near 1.

**Observed:**

| wsx4, wrongly declared | median output | median ratio to correct | max abs diff |
|---|---|---|---|
| correct (internal, honoured) | 504 | 1.0 | — |
| external, divisor 10000 | **0** | **0.0000** | 65535 DN |
| external, divisor 5000 | **0** | **0.0000** | 65535 DN |

The prediction held in direction and was **stronger than predicted in degree**: the image does
not merely shift, it collapses to zero with saturated outliers.

### 2.2 A correction to what WP5 assumed, which matters more

WP5 warned that a mis-normalised output would "look like an ordinary image". For **wsx4 that
is wrong** — it is visibly black. But the symmetric error, on **our own model**, is exactly
the silent failure WP5 feared:

| ours, wrongly declared `internal` (raw DN into a graph expecting DN/5000) | |
|---|---|
| correct median | 344 |
| wrong median | **346** |
| **median ratio** | **1.0051** |
| max abs diff | 247 DN |

**It looks almost right.** The explanation is architectural: our model is
`output = nearest-neighbour upsample of the input + learned residual`. Feeding raw DN leaves
the *base* term correct — it is a shuffle of the input, not a learned function — while the
residual branch saturates. So the model degrades to nearest-neighbour upsampling: a plausible,
blocky image with the learned detail destroyed and a median ratio of 1.005. **That is the
dangerous direction, and it is ours, not theirs.**

### 2.3 Band order

Read from **`wsx4_spatrad.yaml`** — `bands: [B2, B3, B4, B8]` — and asserted against the
input's band count before any tile runs. Never assumed.

**What happens if the order is wrong**, measured by feeding B4,B3,B2,B8 and un-swapping the
output: **max 1328 DN, median 36 DN different**. The model is not channel-symmetric, a wrong
order silently changes every pixel, and the result still looks like an image. That is why the
order is read from the tool's own config rather than inferred from a filename.

---

## 3. Input data

`sr_train/make_model_input.py` already refused to build an input whose band order the model
does not expect. For wsx4 the fourth band was fetched:

| | |
|---|---|
| B08 for 36SXJ | `sentinel-cogs` COG, **238,172,241 B in 16.4 s** |
| demonstration input | `tubitak/data/sr_model_input/DEMO_INPUT_WSX4_36SXJ_1024px_B2-B3-B4-B8_uint16DN_10m.tif` |
| | 6,366,566 B, 4 bands `['B2','B3','B4','B8']`, uint16, 1024 × 1024, EPSG:32636 |
| grid | `(10.0, 0.0, 645720.0, 0.0, -10.0, 4357320.0)` |

Band order taken from the yaml at build time and asserted (`assert order == ["B2","B3","B4","B8"]`),
with the band descriptions written into the file so a reader can check without trusting the
filename.

---

## 4. In QGIS — three methods

`Bikübik` (default, first), `Eğitilmiş model — GenCP (2×)`, `Referans model — wsx4 (4×)`.

**Both model entries take the model path; only the default FILE differs.** Everything that
distinguishes wsx4 from ours — scale, channels, band order, normalisation mode, tiling scheme,
margin — is read from the chosen file's contract, never from which entry was clicked. The
entries are a convenience for finding the right file, not a second place where parameters
live.

Driven through the real dialog, **17 of 17 checks**:

```
model info: wsx4_spatrad.onnx · normalleştirme modelin içinde · 4× ·
            4 bant B2,B3,B4,B8 · kırpmalı birleştirme (kenar 130 px)
estimate  : 36 karo · çıktı 4096 × 4096 piksel · 2,5 m çözünürlük · yaklaşık 134 MB
status    : Bitti · 36 karo · 27,0 sn · 107 MB Katman eklendi ve girdiyle hizalı.
```

### 4.1 The wrong-input guard, with three methods and three files

Every combination triggered, in QGIS:

| method | file given | result | message key |
|---|---|---|---|
| wsx4 | 8-bit TCI | **refused**, Run off | `err_bands` |
| wsx4 | our 3-band input | **refused**, Run off | `err_bands` |
| GenCP | wsx4's 4-band input | **refused**, Run off | `err_bands` |
| GenCP | our 3-band input | accepted, Run on | — |
| Bikübik | 8-bit TCI | accepted, Run on | — |

What the user sees when wsx4 is given the 3-band file:

> Model **4 bant** bekler (B2,B3,B4,B8); seçilen dosyada **3 bant** var.
> Adı **MODEL_INPUT_** ile başlayan yansıtma dosyasını seçin.

**No file is written.** Note the guard that fires is now the band count, not the dtype: with
three methods the band count separates the two model inputs from each other, and the dtype
check still separates both from the TCI.

### 4.2 Three defects found by driving it, not by reading it

**A — a `TypeError` swallowed by Qt.** `model_desc` formatted `{norm:.0f}`, and wsx4's
`norm_divisor_dn` is `None` because it normalises internally. The exception was raised inside
a Qt signal handler, **which swallowed it silently**: the model loaded, but the label stayed
on "no model selected" and the tile/overlap were never applied, so the run then failed with
the `CropLayoutError` above. The guard caught the consequence; nothing caught the cause. Fixed
by pre-formatting `norm`, `tiling` and `steps` as strings — a format spec that only works for
some models is a defect, not a formatting choice.

**B — the model path could not be pre-filled once installed.** An installed plugin has no
repository above it to guess from, so the wsx4 entry offered nothing. That is *correct* — we
do not ship the weights and cannot know where the user put them — but it made the entry
useless on first use. Now the dialog remembers the last file **per method**; one shared slot
would have handed wsx4 our 3-band model on every switch.

**C — the output filename carried the wrong factor.** The name is suggested when the source is
chosen, before a model is picked, so a 4× run was proposed as `_sr_x2.tif`. Now re-suggested
when the scale changes, and only when the current name is one we generated — once the user
edits it, their choice stands.

---

## 5. Where the weights live

| | |
|---|---|
| path | `tubitak/data/wp5_reference/models/wsx4_spatrad.onnx` |
| beside it, and required | `wsx4_spatrad.yaml` — the graph carries no metadata, so this file **is** the contract |
| size | 17,996,501 B |
| sha256 | `d476439786bb0c6079b61875ea9cda5c62a5963115193a056e5f65bb94bc053e` |

**Confirmed by command, not by intention:**

```
git status --porcelain --untracked-files=all tubitak/data/wp5_reference   ->  0 lines
git check-ignore -v .../wsx4_spatrad.onnx  ->  .gitignore:54: tubitak/data/*
.onnx files inside the plugin zip                    ->  0
.onnx files inside the installed plugin directory    ->  0
```

The weights are not committed, not copied into the plugin directory, and not in anything that
would be distributed. **The user supplies the file locally and selects it in the dialog.**

The licence question WP5 raised is unchanged and still open — the repository is Apache-2.0
with no weights-specific statement, and wsx4 is trained on WorldStrat, whose terms may reach
derived weights. Not shipping them means that question does not have to be answered before
Friday, but it will have to be answered before anything is redistributed.

---

## 6. The demonstration document

`02b-demo-tik-sirasi.md` now covers three methods, with **wsx4 as the headline** since it is
the named target, and a method-to-file table at the top. It records the file the weights are
not shipped with, and the one detail that will otherwise waste ten minutes on the day: the
yaml must sit beside the onnx or the model is refused.

**Followed from a cold start, in a fresh QGIS profile, 24 checks — 0 failed** after defect C
above was fixed. Every string the document quotes verbatim matched the dialog character for
character, including the Turkish decimal comma:

```
1024 × 1024 piksel · 4 bant, uint16 · EPSG:32636 · 10 m çözünürlük
wsx4_spatrad.onnx · normalleştirme modelin içinde · 4× · 4 bant B2,B3,B4,B8 · kırpmalı birleştirme (kenar 130 px)
36 karo · çıktı 4096 × 4096 piksel · 2,5 m çözünürlük · yaklaşık 134 MB
Bitti · 36 karo · 25,2 sn · 107 MB Katman eklendi ve girdiyle hizalı.
gencp_sr_x2_v1.onnx · DN/5000 · 2× · 3 bant B02,B03,B04 · yumuşak geçişli birleştirme · adım 16306/20000
```

All 15 absolute paths the document names resolve on this machine.

---

## 7. Repository hygiene

`tubitak/qgis_plugin` and `tubitak/gencp_core`: **0 changes each.**
`git status --porcelain --untracked-files=all tubitak/data`: **0 lines.**
`plugin_guards.py`: **PASS** on G1/G2/G3 — 7 files, 48 string keys used, 77 defined.
Plugin zip 47,496 B → rebuilt at each install; **14 files, no `.onnx` of any kind.**

Modified: `sr_core/mosaic.py` (+~150, all below a WP6 marker), `sr_core/run.py` (crop branch,
additive), `sr_plugin/{dialog,strings,task}.py`, `sr_train/run_model.py`,
`docs/02b-demo-tik-sirasi.md`. New: this document.

---

## 8. Open items

1. **The crop path is measured on one extent of one granule.** 1 DN against the single-tile
   reference is convincing, but it is 512 × 512 of 36SXJ, not a survey.
2. **Our own model is the one that fails silently when mis-normalised** (§2.2, median ratio
   1.0051). Nothing detects it at run time: the contract is read from the file, so it is only
   wrong if the file is wrong. A cheap guard would be to assert the output's median is within
   a stated factor of the input's, and it is not implemented.
3. **wsx4's output is not validated against the reference tool's own output**, because WP5
   could not run the tool for want of a THEIA product. The single-tile graph reference
   compares their model against itself, not against their pipeline. The gap is the tool's
   `sensorsio` read path and its `bb_snap` ROI handling, neither of which we reproduce.
4. **wsx4 quality is not measured at all.** No PSNR, no SSIM, no comparison against our model.
   The verification budget here was the grid contract and the tiling, deliberately.
5. **The scientific meaning of running an L2A-trained model on our COGs is unexamined** — as
   is whether wsx4 expects surface or top-of-atmosphere reflectance. WP5 left this open and
   this work package did not touch it.
6. **The weights licence is still unsettled** (§5).
7. **`CropMosaic` writes each tile straight to the dataset**, so its output is not streamed
   through a row band like `StreamingMosaic`. On a full granule at scale 4 that is a
   21960 × 21960 × 4 output; peak memory was not measured, and the demonstration extent is far
   below where it would matter.
8. **Only `wsx4_spatrad` was hosted.** The repository also ships `wsx2_spatrad`,
   `s2v2x2_spatrad`, `s2v2x4_spatrad` and a 10-band `carn` model; the sidecar reader should
   handle all of them, and none was tried.
