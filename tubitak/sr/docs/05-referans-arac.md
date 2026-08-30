# Project 2, WP5 — the reference tool, and whether our plugin can host its model

**Run:** 2026-08-30, inside a two-hour box. **Repository:** `mvy0502/GenCP`, branch
`tubitak-tr`. **No git command was run.**

**Nothing under `tubitak/sr/` was modified except this file**, which is the named
deliverable. `tubitak/qgis_plugin/`, `tubitak/gencp_core/` and the plugin demonstrated on
Friday are untouched. Everything else this work package produced — the tool, its virtualenv,
the weights, the test rasters — lives under gitignored `tubitak/data/wp5_reference/`.
Nothing was installed into QGIS's bundled Python.

---

## 0. The answer, first

**Yes. Our plugin can host wsx4, and the largest piece of the work is already done by them:
the weights ship as ONNX.** No torch export is needed, because there is nothing to export.

Measured, not argued — their `wsx4_spatrad.onnx` driven through **our** `sr_core.upsample`
seam, on a real 4-band Sentinel-2 chip, with `sr_core` unmodified:

```
  method            wsx4_spatrad
  512x512 -> 2048x2048  (25 tiles)      10 m -> 2.5 m
  dtype uint16  bands 4  crs EPSG:32636
  wall clock        4.7 s
```

and **Gate S: PASS, 5/5** at scale 4 — S2 exact pixel size 2.5 m, S3 origin offset 0.0,
S4 2048 = 4 × 512, S5 worst offset `dx 0.0, dy 0.0` over 400 pixel centres.

**The blocker is not the model. It is the input.** The tool reads only THEIA/MAJA or ESA
SAFE products through `sensorsio`; it cannot read our Copernicus COGs or a plain GeoTIFF.
Our plugin does not have that problem, which is the strategic point: **hosting wsx4 in our
plugin removes the constraint that stops the tool being used on Ankara.**

---

## 1. The tool

| | |
|---|---|
| repository | `github.com/Evoland-Land-Monitoring-Evolution/sentinel2_superresolution` |
| upstream | `framagit.org/jmichel-otb/sentinel2_superresolution.git` (the setup.cfg URL) |
| author | Julien Michel, `julien.michel4@univ-tlse3.fr` (CESBIO / Université de Toulouse) |
| **licence** | **Apache-2.0**, `LICENSE` in the repo root, `license_files = LICENSE` in setup.cfg |
| version installed | **2.0.2.post1.dev1+gcc5dec8c9** |
| console script | **`sentinel2_superesolution`** — the typo is real and is in the package, matching the supervisor's message |
| dependencies | `sensorsio` (CNES, from git), `onnxruntime`, `tqdm`, `pyyaml` |
| **runtime** | **onnxruntime. No torch at inference.** |
| last push | 2026-08-27 |

Installed into an isolated virtualenv at `tubitak/data/wp5_reference/venv`, outside the
repository's Python and outside QGIS's. **Install took 44 seconds and succeeded** —
`sensorsio` 1.0.0.post1.dev45 built without trouble.

That it depends on `onnxruntime` and not torch is worth stating early: **the reference tool
is already an ONNX-inference tool, exactly like our plugin.**

---

## 2. What it accepts as input — established empirically

`run.py` dispatches on two flags (lines 268–284):

| invocation | reader | product |
|---|---|---|
| default | `sensorsio.sentinel2.Sentinel2` | **THEIA / MAJA L2A** |
| `--l1c` | `sensorsio.sentinel2_l1c.Sentinel2L1C` | **ESA L1C SAFE** |
| `--l3a` | `sensorsio.sentinel2_l3a.Sentinel2L3A` | THEIA L3A |

**Tested by running it, not by reading the README.** Three inputs, same failure:

| input given | result |
|---|---|
| `tubitak/data/s2_reflectance_l2a/36SXJ_20260527` — our directory of Copernicus L2A COGs | `FileNotFoundError: Could not find root XML file in product directory` |
| a plain 4-band GeoTIFF | same error, same line |
| a THEIA-shaped path that does not exist | same error, same line |

All three raise at `sensorsio/sentinel2.py:484`, in `build_xml_path`. **The tool requires a
product directory containing the MAJA root XML.** A directory of COGs is not one, and neither
is a GeoTIFF. There is no `-i some.tif` path and no flag that creates one.

### Can Ankara be done at all?

**Partly determined, and the news is better than the L2A picture suggests.**

The old THEIA endpoint (`theia.cnes.fr/atdistrib/resto2`) is **dead** — HTTP 000, no
response. CNES has moved to GEODES (`geodes-portal.cnes.fr/api/stac/search`), which answers.
Querying it by bounding box, 50 results each:

| area | product types returned |
|---|---|
| Cappadocia, 36SXJ (34.0–35.5 E, 38.5–39.8 N) | `S2MSI1C` × 50 |
| Ankara, 36TVK (32.0–33.1 E, 39.6–40.6 N) | `S2MSI1C` × 49, `SR_1_SRA_A_` × 1 |
| Toulouse, 31TCJ — the control | `S2MSI1C` × 48, **`REFLECTANCE` × 2** |

`REFLECTANCE` is the THEIA L2A product type and it appears over France, not over Turkey.
**So the default (THEIA L2A) path is very likely unavailable for Ankara** — consistent with
THEIA's known France-plus-selected-sites footprint.

**But `S2MSI1C` — ESA L1C SAFE — is available over both Turkish sites, and the tool has a
`--l1c` flag for exactly that.** L1C SAFE is free from Copernicus and needs only a CDSE
account, which is a self-service registration, not an institutional request.

**Not determined, and what I would do next:** whether the `--l1c` path actually completes on
a Turkish L1C product, and what it costs scientifically. L1C is top-of-atmosphere, not
surface reflectance, so a model trained on surface-reflectance statistics is being fed a
different radiometric domain. I would download one L1C SAFE over 36SXJ from CDSE, run
`sentinel2_superesolution --l1c -i <SAFE> -m wsx4_spatrad.yaml`, and compare the output
against the same model driven from our L2A COGs through our own plugin. That is about an
hour's work and it was outside this box.

---

## 3. `wsx4_spatrad.yaml`, and the parameters that are not in it

The file is **76 bytes**, reproduced complete:

```yaml
bands:
- B2
- B3
- B4
- B8
factor: 4.0
margin: 130
model: wsx4_spatrad.onnx
```

That is the whole configuration. **The rest of what our plugin would have to assert is not in
the yaml** — it is in `run.py` and inside the graph. Read out of the artifacts:

| parameter | value | where it came from |
|---|---|---|
| architecture | ESRGAN-family: 96 `Conv`, 93 `LeakyRelu`, 92 `Concat`, 2 `Resize` — dense residual blocks with a residual scale of 0.2 | the graph's node census |
| bands and order | **B2, B3, B4, B8** (blue, green, red, NIR) | yaml |
| channels | **4 in, 4 out** | graph IO: `[batch, 4, H, W]` → `[batch, 4, H', W']` |
| scale factor | **4.0** | yaml; **verified empirically**: 64→256, 128→512, 100→400, 256→1024 |
| input GSD | **10 m** (`source_resolution = 10.0` when any of B2/B3/B4/B8 is requested) | `run.py:287-288` |
| output GSD | **2.5 m** (`target_resolution = source_resolution / factor`) | `run.py:291` |
| **input normalisation** | **NONE applied by the caller — raw reflectance DN.** The graph divides by 10000 on entry and multiplies by 10000 on exit, internally | `run.py:411` reads with `scale=1.0`; the graph's own constants: `Div [10000.0]`, `Mul [10000.0]` |
| tile size | **1000 output pixels** by default (`-ts`), i.e. 250 source pixels | `run.py:194-199`, `tile_size_in_meters = target_resolution * tile_size` |
| **margin** | **130 output pixels = 32.5 source pixels = 325 m** | yaml `margin: 130`; `margin_in_meters = target_resolution * margin` (`run.py:326`) |
| margin handling | the source area is **padded** by the margin, and the margin is **cropped off the output** — tiles then abut exactly, with **no blending** | `run.py:109-114`, `424-428` |
| input resampling | `Resampling.cubic` when sensorsio reads the padded area | `run.py:413` |
| nodata | input NaN; output NaN → **−10000** | `run.py:380, 421` |
| output dtype | **int16** | `run.py:377` |
| opset / producer | **opset 17**, exported from **pytorch 2.5.1** | the graph header |
| dynamic axes | **yes**, batch and both spatial axes | graph IO |
| `metadata_props` | **NONE** | the graph carries no provenance at all |

**Every one of those has an equivalent in our provenance mechanism, and two of them differ
from ours in a way that matters:**

* we apply `DN / 5000` **outside** the graph; they apply `DN / 10000` **inside** it. A plugin
  that applied its own normalisation to their model would divide twice.
* their graph has **no `metadata_props`**. Ours reads the normalisation constant, scale,
  channel count and band order out of the ONNX file and refuses a model that lacks them.
  **Their model would be refused by our own guard**, because the yaml is the sidecar that
  carries what we expect to find inside the file.

---

## 4. The weights

**`hal-04723225` is the paper, not the weights.** It resolves to Michel, Kalinicheva &
Inglada, *"Revisiting remote sensing cross-sensor Single Image Super-Resolution: the
overlooked impact of geometric and radiometric distortion"* (2025), `hal.science/hal-04723225v3`,
licensed **CC-BY-SA 4.0**. The HAL record links a PDF and supplementary materials and
**carries no code or weights link** — I checked every `soft*`, `code*`, `repo*`, `link*`,
`swhid*` and `file*` field in the record.

The name `spatrad` is the paper's subject: **spat**ial and **rad**iometric distortion.

**The weights are committed inside the GitHub repository:**

| | |
|---|---|
| path | `src/sentinel2_superresolution/models/wsx4_spatrad.onnx` |
| **format** | **ONNX** — not a torch checkpoint, not TorchScript |
| size | **17,996,501 bytes** (17.2 MB) |
| sha256 | `d476439786bb0c6079b61875ea9cda5c62a5963115193a056e5f65bb94bc053e` |
| **licence** | **Apache-2.0**, the repository's licence |

**On the licence, stated carefully because it is a redistribution question.** The weights
carry **no separate licence file and no separate licence statement**. I grepped the README
for any weights-specific term and found only the repository's Apache-2.0 badge. So the
weights inherit Apache-2.0 by virtue of being repository content — which **permits
redistribution, including inside our plugin zip, with attribution and the licence text**.

**Two caveats I would not sign off without:** first, absence of a separate statement is not
the same as an explicit grant over model weights, and some projects intend the code licence
to cover code only. Second, wsx4 is trained on **WorldStrat**, whose own dataset licence
(CC-BY-SA / non-commercial variants exist) may impose terms on derived weights that the
repository does not mention. **If we ship their weights, ask the author directly.** It is one
email to a named academic address and it is cheap compared with discovering the answer later.

---

## 5. Running it

**The tool was installed successfully and was NOT run to completion on a product, because no
THEIA L2A product exists for our area and none was downloaded inside the box.** That is the
one item of the six not finished, and it is reported rather than worked around.

What was run instead, many times: **the wsx4 graph itself**, which is the part that matters.

| test | result |
|---|---|
| session construction | 0.02 s, `CPUExecutionProvider` |
| 64² → 256² | factor 4.00, 0.051 s |
| 128² → 512² | factor 4.00, 0.190 s |
| **100² → 400²** (not a multiple of 8) | factor 4.00, 0.098 s — **arbitrary sizes accepted** |
| 256² → 1024² | factor 4.00, 0.709 s |
| finite output | yes, in every case |

**Gate S on their model's output, driven through our pipeline** (source: a real 4-band
36SXJ chip; output: 2048² at 2.5 m; scale 4): **PASS, 5/5.** Their model satisfies the
georeferencing contract our plugin asserts. That question is settled and the answer is the
good one.

---

## 6. Can our plugin host wsx4? Evidence, cost, and the one real risk

### 6.1 The export question does not arise

The brief asks whether the model can be exported to ONNX and driven by our `Upsampler`
interface. **It is already ONNX.** There is nothing to export and no export to fail.

### 6.2 It was driven by our interface, and it worked

I wrote a 30-line adapter — `tubitak/data/wp5_reference/host_wsx4.py`, outside the repository
tree — presenting their graph as an `sr_core.upsample.Upsampler`: `scale = 4`, `name`,
`n_clipped`, `n_total`, and `upsample(H×W×C) → sH×sW×C`. It fed
`sr_core.run.superresolve(..., scale=4, upsampler=...)` **with `sr_core` unmodified**, using
the `upsampler=` seam WP4 added.

Result: 512² → 2048², 4 bands, 25 tiles, 4.7 s, 0 uncovered pixels, Gate S 5/5.

### 6.3 What it would cost — six concrete items

| # | item | cost |
|---|---|---|
| 1 | **B08 is not in our corpus.** WP2A downloaded B02/B03/B04 only. | One COG per granule, **238 MB, 16 s** — already done for 36SXJ. `make_model_input.py` needs a 4-band mode. Small. |
| 2 | **Scale 4, not 2.** `dialog.SCALE = 2` is a module constant. | Read the scale from the model's sidecar instead of the constant. Half a day, and it is the change the dialog was designed to accept. |
| 3 | **Four channels, not three.** | `sr_core` already handles band count from the source profile; WP1 exercised a 4-band uint16 path. Near zero. |
| 4 | **No `metadata_props` in their graph.** Our loader requires `norm_divisor_dn`, `scale_factor`, `in_channels`, `band_order` and **refuses a model without them**. | Either accept a yaml sidecar beside the ONNX, or write the metadata into a copy of their file. The second is cleaner and takes minutes — but it forks their artifact, and the fork must record the original sha256. |
| 5 | **Their normalisation is internal, ours is external.** | A per-model flag: "the graph normalises itself". If missed, we would divide by 5000 on top of their internal divide by 10000 and get output ~10× low **that still looks like an image**. This is the dangerous one. |
| 6 | **Their tiling is crop-the-margin; ours is overlap-and-feather.** | Measured below. Not free. |

### 6.4 The one real technical risk: tiling is not equivalent

Their strategy pads by a 130-output-pixel margin, crops it off, and lets tiles abut with **no
blending**. Ours overlaps and feather-blends. For a GAN-family model these are not the same
operation, and I measured the difference against a **single-tile reference** (the whole 512²
chip through the graph in one call, no tiling at all):

| our overlap (source px) | = output px | max abs diff | mean | pixels > 16 DN |
|---|---|---|---|---|
| 32 (our current default) | 128 | **37 DN** | 0.1612 | 691 |
| 40 | 160 | 30 DN | 0.1054 | 80 |
| 48 | 192 | 36 DN | 0.0667 | 50 |
| 64 | 256 | **20 DN** | 0.0347 | 7 |

**The error falls with overlap but does not vanish**, even at 64 source pixels — twice their
declared 32.5. So the residual is not only context starvation: feather-blending two valid but
different ESRGAN predictions is not the same as either of them. Their crop-margin scheme
avoids that by never averaging two predictions.

The mean difference is tiny (0.03–0.16 DN, against reflectance values in the hundreds), so
this is not a correctness catastrophe. But if we host their model we should **implement their
crop-margin tiling rather than reuse our feather blend**, and `sr_core.mosaic` always
feathers. That is the largest single piece of work in the list.

### 6.5 One more measured detail

Casting their float output to `uint16` clipped **3,745 of 26,214,400 values (0.0143 %)** —
negative predictions clamped to zero. Their own writer uses **int16 with nodata −10000**,
which keeps negatives. If we host their model we should follow them and write int16, not
uint16.

---

## 7. Open items and what I did not determine

1. **The tool was never run end to end on a product.** No THEIA L2A exists for our area and
   none was fetched. **What I would do next:** download one ESA L1C SAFE over 36SXJ from CDSE
   and run `--l1c`.
2. **Whether the `--l1c` path works over Turkey is not determined**, and it is the single
   most valuable unknown left. GEODES shows `S2MSI1C` available over both Ankara and
   Cappadocia, so the data exists; whether `sensorsio`'s L1C reader and the model behave on
   it is untested.
3. **The scientific cost of L1C is not assessed.** L1C is top-of-atmosphere; the model's
   training domain is not. Even if it runs, the output may not mean what an L2A output means.
4. **Whether Apache-2.0 truly covers the weights, and whether WorldStrat's licence reaches
   them, is not settled** (§4). It needs one email to the author, not more investigation.
5. **`s2v2x4_spatrad`** — a second ×4 model, on bands B5/B6/B7/B8A at 20 m — exists in the
   repo and was not examined. It may be the better comparison arm for a 20 m → 5 m claim.
6. **No comparison of their output against ours** on the same ground, because their tool never
   produced an output. The single-tile graph reference in §6.4 is the closest thing and it
   compares their model against itself, not against our model.
7. **The GEODES coverage query is a 50-item page, not a coverage statement.** It is
   suggestive, not proof, that THEIA L2A is unavailable over Turkey. A definitive answer needs
   a properly filtered, paged query on `product:type`.
8. **`sensorsio` was pulled from git at an unpinned commit** (`1.0.0.post1.dev45+g3372db58e`).
   Anything reproducible built on this tool must pin it.

---

## 8. What this means for the project, in one paragraph

If the deliverable becomes their model in our plugin, then **the plugin stops being a vehicle
for our model and becomes a vehicle for any ONNX super-resolution model** — which is what it
was designed to be, and WP4 already proved the seam works by hosting our own. The work is
five small changes and one real one (tiling). The thing that would block it is not technical:
it is whether we may ship their weights, and that is a question for the author rather than for
more measurement. Meanwhile **our own model does not become worthless** — it becomes the
comparison arm, and it has something wsx4 does not: a registered, leak-checked corpus and a
paired margin measured against a registered control on a held-out granule.
