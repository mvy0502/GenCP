# GenCP — TÜBİTAK UZAY workspace

Generating synthetic satellite imagery from OpenStreetMap vector data with **pix2pix**
(a conditional GAN). This folder (`tubitak/`) holds the internship work and is kept
separate so it never collides with upstream (`telespazio-tim/GenCP`) files.

- **Setup date:** 18 August 2026
- **Repository root:** `~/Documents/GenCP-Generative-Goruntu-Uretimi-OpenStreetMap`
- **Working branch:** `tubitak-tr` (upstream's default branch is `master`)
- **Hardware:** MacBook Pro, Apple M4 Max (arm64), 36 GB RAM — no CUDA, runs on CPU

## Findings summary

Six findings, each measured rather than asserted, and each written up with its method, numbers and
falsification criteria. Nothing below has been fixed in the pipeline — Options A-E remain
unimplemented and `GenCP_DB` is untouched.

| # | finding | status | where |
|---|---|---|---|
| 1 | **Georeferencing scale error.** `gencp_georeferencing.py` pairs a 256-px grid with a 257-px source transform: true GSD 10.0390625 m vs 10.0 declared, **+0.390625 % = exactly 1/256**. Zero at the NW corner, **14.1 m at the SE corner**. | **Confirmed 4 ways**, including KARIOS at **9.9σ** | [geometry-finding.md](docs/geometry-finding.md) |
| 2 | **Network alignment is not a contributor.** Equivariance certified to **0.008 px (8 cm)**; the absolute offset is **exactly 0** analytically, since `p == (k−s)/2` holds at every layer. | Settled | [geometry-finding.md §11](docs/geometry-finding.md) |
| 3 | **Train/inference scale mismatch.** Training resizes 257→286 + random crop, inference 257→256 — the model sees content **11.7 % coarser** at inference. | Real but **not worth acting on**: arm C is geometrically cleanest yet matches no better (paired t = +0.59) | [train-test-scale-mismatch.md](docs/train-test-scale-mismatch.md) |
| 4 | **The generator invents structure.** It emits **2.1× the edge density of its OSM input** and matches the real satellite's busyness (ratio 0.996) *regardless* of what the input specifies. | Confirmed; **no usable threshold** — rank sites, don't filter them | [hallucinated-structure.md](docs/hallucinated-structure.md) |
| 5 | **Sparse OSM chips lose positional accuracy — and this is GenCP-specific.** rho = **−0.61** (partial, controlling for point count) between OSM edge density and residual. A ceiling control on *real* imagery gives **rho ≈ +0.06, null** — so it is not generic matchability. | Confirmed with the real instrument | [karios-validation.md §10](docs/karios-validation.md) |
| 6 | **Dataset defects** for an upstream report: 9 leaked test chips, 25 demo/train overlaps, 323 of 566 OSM halves not byte-identical to their georeferenced raster. | Recorded | [geometry-finding.md §12](docs/geometry-finding.md) |

### What the KARIOS run established

* **On upstream's own statistic we are 4.5× better**, not worse. Their "mean error 0.7 px" is
  KARIOS's `mean_x`/`mean_y` — the *global systematic shift* — not a per-point error magnitude. Our
  arm B gives **0.155 px** against their 0.70 px, and per-axis RMSE 1.03/0.91 px against their 2.50.
  An earlier claim that we were "3× worse" was based on comparing two different quantities and has
  been withdrawn.
* **Correcting the affine reduces the global shift by 40.3 %** (against 6.1 % on the per-point mean),
  because a scale error is systematic and a signed mean is what captures it.
* **The ~2 px noise floor is local matching, not our setup.** Variance decomposition puts **~95 %
  within-chip**; our ground-truth construction is not inflating the measurements.

### Turkish pipeline — status

**Turkey is absent from the training corpus.** It spans UTM zones 30-34 (western/central Europe);
Turkey is in zones 35-38, ~520 km further east. Running the pretrained model on Turkish data is
therefore a **genuine geographic generalisation test**, which is the stronger experiment.

The OSM rasteriser is **built and fitted** (edge profile matched to 0.023 px; palette an exact
subset; geometry identical) but **FAILED its KARIOS acceptance gate** (+0.55 px, −24 % points,
11/30 chips with zero key points). Diagnosis: the reference rasters are OSM vectors composited
over a **per-pixel land-cover base layer** (the released `CLC_color_mapping`'s purpose) — sea and
large water (74 % of reference water) and forest speckle texture come from that raster, not from
OSM. See [renderer-tolerance.md](docs/renderer-tolerance.md) §4. Adding a land-cover base
(e.g. ESA WorldCover 10 m) is the identified fix, deliberately not implemented pending decision.

Ankara acquisition is complete and verified: see [ankara-acquisition.md](docs/ankara-acquisition.md). The palette is pinned down from data (11 colours, closed), but
the renderer is not: the one released colour table is demonstrably not the one used (buildings
missing, three colours never rendered), and 45 % of every raster is anti-aliasing from unknown
tooling. See [osm-palette.md](docs/osm-palette.md) §7 for the recommended next step.

### Priority order this implies

1. **Site selection** — the largest lever by a wide margin. Rank AOIs by OSM information content.
2. **Affine correction** (Option A) — worth doing for correctness; a 40 % improvement on the
   systematic-shift statistic, but small against total error.
3. **Inference scale** — leave alone; measured and rejected on a task-based metric.

### Practical note

KARIOS is **single-threaded** (measured: 19.7 s per chip, `user` ≈ `real`). On this 14-core machine
the runs are embarrassingly parallel — running 8-wide cut a 25-minute batch to about 3 minutes.
Worth doing for any full campaign.

## Repository layout

| Remote | URL |
|---|---|
| `origin` | https://github.com/mvy0502/GenCP.git (fork) |
| `upstream` | https://github.com/telespazio-tim/GenCP.git |

```
tubitak/
├── README.md
├── environment.yml     # conda environment (from-history + pip section)
├── scripts/
│   ├── fix_openmp.sh            # OpenMP conflict fix (required after setup)
│   ├── verify_georeferencing.py # georeferencing verification
│   ├── visualize.py             # visual comparison / verification grid
│   ├── shift_estimator.py       # subpixel shift estimators + self-test (reusable module)
│   ├── shift_field.py           # NxN shift field between any two rasters + quiver figure
│   ├── hypothesis_test.py       # how 257x257 becomes 256x256
│   ├── network_alignment.py     # cross-modal alignment attempt (superseded)
│   ├── paired_alignment.py      # alignment vs real satellite (superseded)
│   ├── equivariance_test.py     # alignment certification (0.008 px)
│   ├── corpus_overlap.py        # is the demo site in the training corpus?
│   ├── receptive_field_check.py # absolute alignment: conv/deconv arithmetic
│   ├── hallucination_analysis.py# invented structure vs OSM information content
│   ├── scale_experiment.py      # train/inference scale comparison
│   ├── build_reference_set.py   # georeferenced ground truth from the corpus pairs
│   ├── build_karios_arms.py     # the three KARIOS arms on a common grid
│   ├── run_karios_arms.py       # drive KARIOS (runs in the `karios` env)
│   └── analyse_karios.py        # arm comparison + residual figure
├── configs/
├── notebooks/
├── docs/
│   ├── geometry-finding.md      # 257->256 georeferencing scale error
│   ├── train-test-scale-mismatch.md  # 286-vs-256 domain shift (principal open question)
│   ├── hallucinated-structure.md     # invented detail and GCP chip selection
│   ├── karios-validation.md          # 3-arm KARIOS run against real ground truth
│   ├── osm-palette.md                # OSM raster palette + edge profile + snapshots
│   ├── data-sources.md               # consolidated reproducibility record
│   └── figures/
├── data/               # gitignored
└── outputs/            # gitignored
```

## Environment setup

Miniforge was installed (conda-forge, native Apple Silicon) — **not** Anaconda.

```bash
brew install --cask miniforge
conda init zsh
conda create -n gencp python=3.11 -y
conda activate gencp
conda install -c conda-forge rasterio osmnx geopandas matplotlib jupyterlab visdom -y
pip install torch torchvision dominate wandb
```

### Recreating the environment from scratch (TWO steps — the second is mandatory)

```bash
conda env create -f tubitak/environment.yml
conda activate gencp
bash tubitak/scripts/fix_openmp.sh
```

The second step **cannot be skipped**. `environment.yml` alone does not produce a working
environment: installation completes, but `import torch` crashes because of an OpenMP
conflict (see [Known issues](#known-issues--environment-gotchas)). `fix_openmp.sh` is
idempotent — on an already-fixed environment it exits without doing anything.

### Verified versions

| Package | Version |
|---|---|
| Python | 3.11.15 |
| torch | 2.13.0 |
| torchvision | 0.28.0 |
| rasterio | 1.4.4 |
| osmnx | 2.1.1 |
| geopandas | 1.1.4 |
| numpy | 2.4.6 |

`torch.backends.mps.is_available()` → **True**. `torch.cuda.is_available()` → `False` (expected).

## Known issues / environment gotchas

This section documents problems hit during setup that **will be hit again**. Neither one
appeared in the reference environment; both are specific to this machine.

### 1. OpenMP conflict — `OMP: Error #15`

**Symptom.** Without doing anything else, just:

```
OMP: Error #15: Initializing libomp.dylib, but found libomp.dylib already initialized.
```

The process dies with `abort` (exit 134). `import torch` **on its own** is enough; nothing
that uses torch works, including `test.py`.

**Root cause.** Two separate OpenMP runtimes are loaded into the same process:

| Source | Runtime it brings |
|---|---|
| conda-forge (`numpy`, `rasterio`, `libopenblas`) | `$CONDA_PREFIX/lib/libomp.dylib` (`llvm-openmp`) |
| pip `torch` wheel | `.../site-packages/torch/lib/libomp.dylib` (bundled inside the package) |

conda-forge numpy loads conda's libomp first; torch then tries to initialise its own copy
and the OpenMP guard halts the process. This does not happen when all packages come from a
single source — the problem is created by mixing conda and pip.

**Fix.** Torch's bundled copy is backed up and symlinked to conda's, leaving exactly **one**
OpenMP runtime in the process:

```bash
conda activate gencp
bash tubitak/scripts/fix_openmp.sh
```

**Why `KMP_DUPLICATE_LIB_OK=TRUE` was NOT used.** That variable is not a fix — it silences
the guard and permits two runtimes to coexist. As OpenMP's own warning says, this can crash
or **silently produce incorrect results**. In a GAN inference pipeline a silently wrong
number is far worse than a noisy crash: the output still looks plausible but is wrong. The
symlink instead eliminates the problem by leaving a single runtime. Verified: after linking,
the torch↔numpy matmul difference is `0.0`.

**⚠️ It is not permanent.** The symlink lives inside `site-packages`; neither
`environment.yml` nor git captures it. **Any** operation that reinstalls or upgrades torch
(`pip install -U torch`, `pip install --force-reinstall`, deleting and recreating the
environment) restores the bundled copy and brings the crash back. Just run the script again —
it is idempotent, so running it unnecessarily is harmless.

### 2. `visdom` cannot be installed with pip — `pkg_resources`

**Symptom.**

```
ModuleNotFoundError: No module named 'pkg_resources'
ERROR: Failed to build 'visdom' when getting requirements to build wheel
```

**Root cause.** `visdom`'s `setup.py` imports `pkg_resources`, which setuptools 82 removed.
pip's build-isolation environment installs a current setuptools, so the build fails before
it starts.

**Careful — silent side effect.** pip resolves all dependencies first, so this error aborts
the **entire** command. That means:

```bash
pip install torch torchvision dominate visdom wandb   # ← nothing installs, because of visdom
```

leaves torch uninstalled too. It is easy to miss, because the error message mentions only visdom.

**Fix.** Install visdom from conda-forge and the rest from pip:

```bash
conda install -c conda-forge visdom      # 0.2.4
pip install torch torchvision dominate wandb
```

### 3. The VHR demo was not installed

`GenCP_VHR_demo/requirements_VHR.txt` pins `tensorflow==2.10.1` and `gdal==3.6.4`.
There is no macOS arm64 wheel for TensorFlow 2.10.1, so it was left out of scope.
GDAL was not installed separately either — `rasterio` ships its own.

## Model weights

405 MB, downloaded from Zenodo; kept out of the repository by `.gitignore`.

```bash
cd GenCP_HR_demo
curl -L -o HR_weights.zip \
  "https://zenodo.org/records/15044428/files/GenCP_HR_Model_Weights.zip?download=1"
unzip -q HR_weights.zip
mkdir -p checkpoints
cp -r HR_Model_Weights/* checkpoints/
rm -rf HR_weights.zip HR_Model_Weights
```

Result: `checkpoints/genCP_HR_RGB_model/latest_net_G.pth` and
`checkpoints/genCP_HR_B04_model/latest_net_G.pth` (~218 MB each).

## Running the pipeline

All commands are run from inside `GenCP_HR_demo/` with the `gencp` environment active.

### 1. Image generation (CPU)

`--gpu_ids -1` enables CPU mode; no code changes are needed.

```bash
python ../test.py \
  --dataroot "./data/dataset" \
  --name "genCP_HR_RGB_model" \
  --model "test" \
  --results_dir "./data/fake_images" \
  --checkpoints_dir "./checkpoints" \
  --dataset_mode "single" \
  --norm "batch" \
  --netG "unet_256" \
  --gpu_ids -1
```

Expected: `[Network G] Total number of parameters : 54.414 M`.
If this number differs, the wrong model was loaded — stop.

Output: 100 files under `data/fake_images/genCP_HR_RGB_model/test_latest/images/`
(50 `_real.png` + 50 `_fake.png`).

> The test folder contains 630 `.tif` files; only 50 tiles are processed because
> `test.py`'s `--num_test` defaults to 50. Raise `--num_test` for more.

### 2. Georeferencing

```bash
python gencp_georeferencing.py \
  -t "./data/fake_images/genCP_HR_RGB_model/test_latest/images" \
  -i "./data/dataset/test" \
  -o "./data/GenCP_DB"
```

Output: 50 georeferenced GeoTIFFs in `data/GenCP_DB/`.

### 2b. Affine correction (Option A — REQUIRED for new outputs)

`gencp_georeferencing.py` declares 10.0 m pixels for content whose true GSD is 10.0390625 m
(geometry-finding.md §5; KARIOS measured the correction to cut the systematic global shift by
40 %). All new chip sets — the Turkish outputs in particular — go through the correction by
default; existing `GenCP_DB` files are left as published:

```bash
python tubitak/scripts/fix_georeferencing.py --dir <output_dir> --out-dir <corrected_dir>
```

Metadata-only (pixels byte-identical); verified against the KARIOS arm-B rasters: 90/90
fixed-then-warped chips byte-identical to the trusted arm B set.

`NotGeoreferencedWarning` is **normal** — the generated PNGs carry no geospatial metadata;
the script takes that information from the input rasters.

### 3. Verification

```python
import rasterio
with rasterio.open('data/GenCP_DB/31TEJ_0451_00.tif') as s:
    print('CRS:', s.crs, '| size:', s.width, 'x', s.height, '| resolution:', s.res)
```

Expected: `CRS: EPSG:32631 | size: 256 x 256 | resolution: (10.0, 10.0)`
(all 50 files were verified to carry these values).

> **This check alone is NOT sufficient.** `gencp_georeferencing.py` copies the `crs` and
> `transform` fields from the reference raster **verbatim**, so all three fields look correct
> even if the wrong PNG was written. For real verification see
> [Verification scripts](#verification-scripts).

> **Known geometry caveat.** The declared 10.0 m pixel size is not exact: inputs are 257×257
> and are resampled to 256×256, so the true ground sample distance is 10.0390625 m — a
> +0.39 % scale error reaching ~14 m at the far corner. Measured and quantified in
> [`docs/geometry-finding.md`](docs/geometry-finding.md). Nothing in the pipeline was changed.

## Verification scripts

### `verify_georeferencing.py`

Closes the gap the CRS/size/resolution check cannot. For every file in `data/GenCP_DB/` it
runs three checks:

1. **Identity** — does the GeoTIFF pixel array match `_fake.png` or `_real.png` exactly?
   The correct answer is `_fake`. A `_real` match is a hard failure (it would mean the input
   image was written instead of the generated one).
2. **Transform** — is the output's affine transform element-by-element identical to that of
   the same-named input raster?
3. **Pairing** — is the filename mapping 1:1, and was any output derived from a
   differently-named input?

```bash
python tubitak/scripts/verify_georeferencing.py
```

Read-only; it writes nothing. Returns a non-zero exit code on failure.
Last run: **50/50 PASS** on all three checks.

### `visualize.py --verify`

The visual counterpart of the identity check above. Produces a three-row grid: row 1 the OSM
input, row 2 the generated `_fake.png`, row 3 the GeoTIFF read back from `GenCP_DB/`.
**Rows 2 and 3 must be pixel-identical**; the script also verifies this by array comparison
and errors out if they differ.

```bash
python tubitak/scripts/visualize.py --verify -n 6 --seed 7
```

Output: `tubitak/outputs/verification_grid.png`. Last run: 6/6 identical.

## Geometry analysis tools

Measurement code behind [`docs/geometry-finding.md`](docs/geometry-finding.md). `shift_estimator.py`
is an importable module, intended for reuse during KARIOS validation:

```python
import sys; sys.path.insert(0, "tubitak/scripts")
from shift_estimator import phase_shift, ncc_shift, prepare
```

**Always run the self-test before trusting a measurement.** Two estimators are provided because
one is not enough: phase correlation is accurate to 0.076 px RMS *within a modality* but fails
outright across modalities (errors of 40-64 px), where bounded-search NCC is needed instead.

```bash
python tubitak/scripts/shift_estimator.py --self-test
python tubitak/scripts/shift_estimator.py --self-test --mode gradient
```

### `shift_field.py` — shift field between any two rasters

Takes an arbitrary raster pair, so it can be pointed at Turkish AOIs or KARIOS inputs rather than
only the demo. It reports a per-window table, a fitted slope and a plain-language interpretation
(zero field / linear ramp / uniform offset / no clean category), and optionally writes a quiver
figure.

```bash
python tubitak/scripts/shift_field.py REFERENCE.tif MOVING.tif \
    --pixel-size 10 --figure out.png

# cross-modal pairs must use gradient correlation, not intensity
python tubitak/scripts/shift_field.py A.tif B.png --mode gradient
```

### `hypothesis_test.py` — how 257x257 becomes 256x256

Reconstructs each candidate transform and compares it to the network's own recorded input,
printing every candidate's score rather than only the winner.

```bash
python tubitak/scripts/hypothesis_test.py --tiles 8
```

### Alignment: three scripts, one answer

Alignment was measured three ways; the first two are kept because their failures are informative,
and each records the numbers that ruled it out.

| script | compares | bound achieved |
|---|---|---|
| `network_alignment.py` | OSM input vs generated output (cross-modal) | ~0.9 px |
| `paired_alignment.py` | generated output vs **real** satellite half | ~1.9 px (worse) |
| `equivariance_test.py` | two outputs from a **known-offset input** | **0.008 px** |

Both ground-truth comparisons are limited by content mismatch — the generator makes a *plausible*
scene, not the real one. Removing ground truth from the question tightened the bound by two orders
of magnitude.

```bash
python tubitak/scripts/equivariance_test.py \
    --out-p tubitak/data/equivariance/out_p/genCP_HR_RGB_model/test_latest/images \
    --out-q tubitak/data/equivariance/out_q/genCP_HR_RGB_model/test_latest/images --offset 16
```

### `corpus_overlap.py` — is the demo site in the training corpus?

Compares exact chip names, not just MGRS tiles. Answer: the 50 processed chips are all 31TEJ and
appear **nowhere** in the corpus, so demo results are held out.

```bash
python tubitak/scripts/corpus_overlap.py
```

### `receptive_field_check.py` — absolute alignment

Equivariance (0.008 px) does not exclude a *constant* offset. This settles it from the conv/deconv
arithmetic, and includes a random-weight control that shows why the empirical Jacobian probe is
inconclusive below ~1 px.

```bash
python tubitak/scripts/receptive_field_check.py --quiet
```

### `hallucination_analysis.py` — invented structure and chip selection

Measures how much structure the generator invents and whether it degrades local matching. Directly
informs site selection — see [`docs/hallucinated-structure.md`](docs/hallucinated-structure.md).

```bash
python tubitak/scripts/hallucination_analysis.py \
    --figure tubitak/docs/figures/hallucination-analysis.png
```

### `scale_experiment.py` — train/inference scale comparison

Scores the current inference path against the training-matched path on four metrics over two
evaluation grids. See [`docs/train-test-scale-mismatch.md`](docs/train-test-scale-mismatch.md).

```bash
python tubitak/scripts/scale_experiment.py --figure tubitak/docs/figures/scale-comparison.png
```

> **Note on the training set.** `docs/geometry-finding.md` §6 measures `GenCP_HR_DB.zip` (1.71 GB)
> from Zenodo. It is **not** in the repository — it lives in `tubitak/data/`, which is gitignored.
> Re-download it from <https://zenodo.org/records/15044428> if those measurements need repeating.

## KARIOS validation

KARIOS runs in its **own** conda environment (`karios`, Python 3.12 + GDAL 3.8), installed at
`~/tools/karios` — never in `gencp`. See
[`docs/karios-validation.md`](docs/karios-validation.md) for the pre-registered three-arm run.

```bash
conda activate gencp
python tubitak/scripts/build_reference_set.py --out tubitak/data/karios/reference
python tubitak/scripts/build_karios_arms.py

conda activate karios
python tubitak/scripts/run_karios_arms.py --arms A B C

conda activate gencp
python tubitak/scripts/analyse_karios.py --figure tubitak/docs/figures/karios-residuals.png
```

## Visualisation

```bash
python tubitak/scripts/visualize.py --seed 42 -n 4
```

Picks 4 random tiles and writes the OSM input on the top row and the generated image on the
bottom row to `tubitak/outputs/sample_output.png`.

> `tubitak/outputs/` and `tubitak/data/` are covered by `.gitignore`; generated figures do
> not enter the repository, only the scripts are tracked.

## VS Code

Select the `gencp` conda environment as the interpreter:

```
/opt/homebrew/Caskroom/miniforge/base/envs/gencp/bin/python
```
