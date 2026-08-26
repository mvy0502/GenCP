# QGIS plugin work package — gate registrations

**Registered 2026-08-26, branch `tubitak-tr`, before any number in
[plugin-results.md](plugin-results.md) exists.** Scope confirmed by Mustafa Bey
(WhatsApp, 26 Aug): the plugin adds the generated image as a QGIS layer and/or writes it
to disk; matching/GCP extraction is out of scope; total model + data size is requested as
a byproduct with real measured file sizes.

Per standing practice (the invariance rule from the three ill-posed gates,
[standing-practices.md](standing-practices.md)), **every gate below carries a mandatory
section listing what it assumes identical on both sides.** A failed gate is reported, not
adjusted.

---

## Gate R — byte-identical raster gate (Step 1)

**Claim under test:** lifting the rendering spec out of `tubitak/scripts/osm_to_raster.py`
into `tubitak/gencp_core/rasterize.py` changed nothing. The model was trained on inputs
drawn in a specific visual language; a subtly different render produces a plausible-looking
but wrong output, silently. Byte-identity is therefore the only acceptable criterion.

**Tile selection rule — stated before the gate runs, so it cannot be shopped.** The three
tiles are the **first three stems in ascending lexicographic order of the `acc_clcgate`
corpus whose `byte_exact` field is `1`** in the committed stale-render census
`tubitak/data/tool_runs/task4/acc_census.csv` (corrections-log entry 15). That census
already establishes which archived renders reproduce from the current post-fix path, so
this rule selects tiles whose stored originals are *known sound* and excludes the stale
two-thirds. The rule yields:

| # | stem | census diff_frac |
|---|---|---|
| 1 | `30TXQ_0830_00` | 0.0 |
| 2 | `30TXQ_0934_00` | 0.0 |
| 3 | `30UYD_0907_00` | 0.0 |

Tiles 1 and 2 were separately proven byte-exact under
[tool-gate-registration-2.md](tool-gate-registration-2.md) criterion 1; tile 3 is new to
this gate and is a genuine additional test. `30TXQ_0879_00` — the chip that failed the
earlier gate — is **excluded by the rule, not by preference**: its census `byte_exact` is
`0`, i.e. its archived render is itself a stale pre-fix artifact, so no correct renderer
can reproduce it.

**Invariances — this gate assumes identical on both sides:**
- **OSM data source:** the same per-chip post-fix `-s smart` extract,
  `tubitak/data/geofabrik/chips/<stem>.osm.pbf` (unmodified, read-only to this gate).
- **Base product:** CLC+ Backbone 2021 V1_1, the same local raster, `base_product="clcplus"`.
- **Footprint and CRS:** read from `tubitak/data/karios/reference/satellite/<stem>.tif`.
- **Palette:** the upstream `GenCP_HR_demo/genCP_HR_osm_colors.py`, SHA-256
  `7876d9d3ae2b646cacd2b32fd1ea47e62484d7c99c247f4a4aae1c133cbaf919`, pinned and verified
  at import; upstream file not modified.
- **Code path:** identical numerical operations in identical order — the lift moves code
  between files and must not re-express it.
- **Environment:** one process, `gencp` conda env, so library versions cannot differ
  between the two sides.

**Amendment 1 (2026-08-26, after a failed first run — disclosed, not silently fixed).**
This registration originally named the stored originals as
`tubitak/data/rasteriser/chips/<stem>.tif`, a path inherited verbatim from
[tool-gate-registration-2.md](tool-gate-registration-2.md). **That path is wrong and the
error is in the earlier registration's text as well.** `rasteriser/chips/` holds the
**WorldCover-era** corpus (mtime 18 Aug 19:43), rendered *before* the CLC+ base layer was
added in commit `e15f5a9` (19 Aug 11:48). The CLC+ renders — the ones the census scored and
the ones this gate must compare against — are in **`tubitak/data/rasteriser/chips_clc/`**
(55 files, mtime 19 Aug 11:46, matching the census's 55 rows exactly).

The first run of this gate was therefore comparing a CLC+ render against a WorldCover
render and failed 0/3 with a dominant `light_green -> forest_green` flow — the signature of
a different base product, not of a broken lift. It is recorded here because the run
happened. **This is a correction to which artifact the gate reads, not a change to the
criterion, the tile selection rule, or the tolerance** — all three are unchanged, and the
byte-identity bar was never relaxed. The correction is independently verifiable: the
supporting measurement showed the *existing* script failed identically, and the
core-vs-script comparison was byte-identical in both runs, so the lift was exonerated
before the reference path was corrected.

**Criterion:** for each of the three tiles, the GeoTIFF written by
`gencp_core.rasterize.make_chip` must be **byte-identical** to the stored original
`tubitak/data/rasteriser/chips/<stem>.tif` — compared as **raster payload** (all three
bands, exact array equality) **and** as **georeferencing** (transform and CRS exactly
equal). Container-level byte equality of the file is reported separately and is *not* the
criterion, because GeoTIFF headers legitimately carry writer-version and timestamp fields.

**Registered prediction:** all three pass. The lift is mechanical; a failure means the lift
changed the spec.

**On failure:** report the diff (fraction of differing pixels and the dominant class flow,
in the same form as the census) and **stop**. Do not proceed to Steps 2–5. Do not introduce
a tolerance.

**Supporting measurement (not a gate):** the same three tiles rendered through the
*existing* `tubitak/scripts/osm_to_raster.make_chip` in the same process, to confirm the
stored originals are still reproducible today and so distinguish "the lift broke it" from
"the archive drifted".

---

## Gate O — PyTorch/ONNX parity (Step 2)

**Claim under test:** the ONNX export of the generator is numerically equivalent to the
PyTorch generator, so the plugin can drop the PyTorch dependency inside QGIS's Python.

**Invariances — assumed identical on both sides:** the same 20 input tiles (same files,
same preprocessing to the network's input tensor), the same checkpoint, the same weights,
and **the same dropout state**. Dropout state is made identical by construction: the export
and both sides of the comparison run the **deterministic path (dropout off)**, which is the
only way "identical dropout state" is well-defined across two runtimes with different RNGs.
This is stated here rather than discovered later — a seeded comparison across PyTorch and
onnxruntime would be comparing two different RNG streams, not two implementations.

**Tile selection rule:** the first 20 stems in ascending lexicographic order of the
`acc_clcgate` corpus (all 30 exist; no filtering on outcome).

**Criterion:** **max abs diff <= 1/255** in 8-bit units. Reported per channel: max abs diff
and mean abs diff, in 8-bit units, over all 20 tiles.

**Registered prediction:** pass. fp32 ONNX export of a plain convolutional U-Net is
normally bit-close; the expected max difference is well below 1 DN, arising only from
float32 op-ordering differences between ATen and onnxruntime kernels.

**Amendment 2 (2026-08-26) — units pinned, after the outcome was seen. Disclosed.**
The criterion above says "max abs diff <= 1/255 **in 8-bit units**", and that text is
ambiguous: `1/255` is a normalised-unit value, so "1/255 in 8-bit units" can be read as
**one grey level** (1.0 DN, i.e. 1/255 of full scale) or as **one 255th of a grey level**
(0.003922 DN). The two readings disagree about fp16 and agree about fp32.

This amendment does **not** choose the reading that would change a verdict. Under
standing practice 6 the stricter reading — the literal one, `<= 0.003922 DN` — remains the
bound, and fp16 remains **failed**. Both readings are now reported side by side, together
with a unit-free measurement (how many pixels of the final uint8 image actually differ)
so the decision does not rest on a textual reading at all. The generator ends in `Tanh`,
so the output tensor is in **[-1, 1]** and `DN = |delta| * 127.5`; `1 DN = 2/255 tensor
units = 1/255 of full scale`.

**On failure or export failure:** report and **stop**. Do not fall back to a PyTorch
dependency inside QGIS — that changes the deployment story and is the institution's
decision, not ours.

**Also reported:** on-disk size of the fp32 and fp16 ONNX files.

---

## Gate D — determinism (Step 3)

**Prediction, registered before the run:** deterministic (dropout-off) inference is
expected to leave the KARIOS residual **statistically unchanged**, i.e. within the
project's standing 0.05 px "indistinguishable" band. Reason: dropout at test time is
pix2pix's noise source in place of a z vector; averaged over a chip it perturbs texture
rather than geometry, and the geolocation residual is driven by the position of structural
edges, which are determined by the input render. A *directional* prediction is also
registered: if anything, dropout-off should be very slightly **better**, because disabling
the noise source suppresses invented structure that has no counterpart in the reference.

**Prior result, and why this gate is not simply re-run.** This exact comparison was already
registered and measured as Registration A ([tool-registrations-3.md](tool-registrations-3.md),
results in [tool-results.md](tool-results.md)): paired (deterministic − seeded) over 30
production-input Ankara chips, all four arms, all four within the 0.05 px band, with the
stated precision limit that n = 30 and SE ≈ 0.077 px rules out shifts above roughly 0.15 px
and not all shifts. **That result stands and is reported, not re-derived.**

**What this gate adds.** The prior measurement disabled dropout *only* (`--no_dropout`) and
deliberately did **not** pass `--eval`. The work package asks for "eval-mode, dropout off".
These are **not the same thing here**: the generator is built with `--norm batch`, so
`model.eval()` switches BatchNorm from batch statistics to running statistics — a real,
output-shifting change that the prior registration explicitly refused to conflate with
dropout. This gate therefore measures the **third arm the prior work did not**: `--eval`
plus dropout off.

**Invariances — assumed identical across all three arms:** inputs (the same production
renders already on disk), render path (nothing re-rendered), checkpoint, KARIOS config,
references, warp geometry, analysis code path. The only degree of freedom is the
inference-time module mode.

**Arms:** (1) stochastic seeded (the evaluated path, seed 42) — the baseline every previous
number used; (2) dropout-off, BatchNorm in batch-statistics mode — the current tool default;
(3) dropout-off **and** `--eval`, BatchNorm in running-statistics mode — what the work
package asks for.

**Bands (the project's standing ones, unchanged):** |paired mean Δ| <= **0.05 px** →
indistinguishable; > **0.15 px** → materially different. Convention: **Δ = candidate −
baseline, negative = candidate better**. Inference path is stated for every number.

**Decision rule:** if arm 3 is not worse than arm 1, the plugin is deterministic in the
eval-mode sense the work package asked for. **If arm 3 is meaningfully worse, that is
reported and the choice between a fixed seed and accepting the penalty is the
institution's, not ours** — per the work package, we do not choose.

---

## Gate G — georeferencing contract (Step 5)

**Why this is a contract and not a nicety:** a separate application consumes our GeoTIFF and
extracts GCPs from it. A half-pixel offset is invisible to us and becomes wrong GCPs
downstream.

**Snapping rule, stated explicitly here before the gate runs.** The output grid is defined
by the reference extent and the nominal 10 m GSD:
- `xmin_out = xmin_ref`, `ymax_out = ymax_ref` (the NW corner is taken from the reference
  extent exactly, not snapped to a multiple of the GSD);
- `width  = ceil((xmax_ref - xmin_ref) / 10.0)`, `height = ceil((ymax_ref - ymin_ref) / 10.0)`;
- transform = `(10.0, 0, xmin_out, 0, -10.0, ymax_out)`.

So the grid is anchored at the reference's **north-west corner** and grows east and south in
whole 10 m pixels; the east and south edges may therefore extend up to one pixel beyond the
reference extent. This is the rule the mosaic already implements; it is written down here so
the downstream consumer can rely on it.

**Assertions, each reported with its actual number, not "passed":**
1. output CRS == reference CRS (authority code equality);
2. output pixel size == 10.0 m exactly, both axes (exact float equality, not approximate);
3. output corner coordinates == the reference extent under the snapping rule above (exact);
4. zero sub-pixel shift against the reference: normalised cross-correlation of the output
   against the reference over the shared footprint peaks at integer lag **(0, 0)**, and the
   sub-pixel refined peak lies within **0.05 px** of the origin in both axes.

**On failure:** report the measured offset and stop; do not adjust the transform to make the
correlation peak move.

---

## Gate S — size table (Step 5)

Measured, real, on-disk sizes; no estimates. Rows: ONNX model fp32; ONNX model fp16;
`onnxruntime` installed footprint; OSM subset for a defined test area **in the format the
plugin actually consumes**; CLC+ clip for the same area. The two data rows are normalised to
**MB per 1000 km2** so the figure scales to any coverage area. The test area is defined and
its area in km2 stated alongside, so the normalisation is checkable.
