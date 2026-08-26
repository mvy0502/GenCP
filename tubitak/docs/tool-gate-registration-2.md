# gencp-ref gate re-registration, seam thresholds, and the source-difference experiment
**Registered 2026-08-21, branch `tubitak-tool`, before any number below exists.**

## Why re-targeting the gate is not weakening it

Changing a gate because you dislike the result is forbidden. Changing a gate because the
test turned out not to ask the question is required. The first gate compared the tool's
PBF-rendered output against **Overpass-era** reference outputs: the two sides were not
rendering from the same OSM data, so a mismatch was guaranteed regardless of whether the
tool was correct — the test was not well-posed, and this could only be learned by running
it. The original registration ([tool-gate-registration.md](tool-gate-registration.md))
stays in the repo, marked **FAILED-as-designed**, and is never deleted.

## Task 1 — re-registered correctness gate

**Reference chips:** the `acc_clcgate` acceptance corpus (30 chips, e.g. `30TXQ_*`), whose
renders (~~`tubitak/data/rasteriser/chips/`~~ **`tubitak/data/rasteriser/chips_clc/<stem>.tif`**, 257 px, CLC+ base — see the correction note at the foot of this file) were produced from
the **dated Geofabrik snapshots with post-fix `-s smart` extracts**, and whose fakes
(`acc_clcgate/out/genCP_HR_RGB_model`) went through the byte-verified inference path and
KARIOS. Gate subset: **30TXQ_0830_00, 30TXQ_0879_00, and one further corpus chip**, each as
a single-tile extent with `--align-origin` at the chip's NW corner (origins from
`tubitak/data/karios/reference/satellite/<stem>.tif`), arm `pretrained`, `--osm-pbf`
pointing at the same country snapshot files the corpus used. **The Ankara evaluation inputs
are ineligible as references**: they predate the Geofabrik switch and were rendered from
Overpass (corrections-log entry 13), so no PBF-rendering tool can or should reproduce them.

Criteria (same reasoning as the first registration):
1. **Tile space:** the tool's 257-px render must be **bit-exact** against the corpus render
   tif; the tool's fake must be **bit-exact** against the eval-path fake regenerated from
   the corpus input. Any mismatch is a bug to report, not absorb. (Known allowed step: the
   corpus inference consumed a pre-resized 256 input; the tool feeds 257 and lets test.py
   resize — the earlier decomposition showed this path reproduces the prep resize; if it
   does not on these chips, that is itself a reportable finding.)
2. **Mosaic space:** outside blend zones the mosaic must equal, exactly, the independent
   single-tile bilinear warp with the corrected affine onto the same 10 m grid; inside a
   blend zone (production overlap run), each pixel within **[min−1, max+1]** of the
   contributing tiles' warped values (uint8 rounding only).
3. **Georeferencing:** mosaic transform (10.0, 0, xmin, 0, −10.0, ymax); per-tile GSD
   exactly 10.0390625 read back from provenance; content placement within one output pixel
   of the validated per-chip corrected warp (cross-correlation peak at lag 0 against the
   corpus `arms/` raster over its footprint).

A failure is reported, never tuned away.

## Task 2 — seam energy with blending active: registered thresholds

Extent: ≥ 3×3 nominal tiles (~7.7 km square) inside the 36TVK Ankara scene; arm C3;
overlap widths **0 (baseline only), 160, 320, 640, 960 m**; KARIOS reference = the real
TCI_36TVK_20260430 window on the same 10 m grid; KARIOS config unchanged.

- **Seam-energy criterion:** ratio of mean gradient magnitude in ±2-px seam-line buffers to
  background. Registered reading: ratio ≤ **1.05** acceptable; **> 1.10 at the recommended
  overlap ⇒ blending inadequate**. (The overlap-0 figure 1.124 is the no-blending baseline
  and is not quotable as a result.)
- **Point-clustering criterion:** from the KARIOS KLT points on the mosaic, the fraction
  landing within 30 m of a seam line, compared to the areal fraction of that buffer;
  binomial test. **Observed/expected > 1.25 with p < 0.05 ⇒ blending inadequate** (the tool
  would be manufacturing control points at tile boundaries). Also reported: within-stratum
  correlation of local seam proximity with residual, mirroring the checkerboard machinery.
- Also reported: compute cost per overlap (tiles generated, fraction of extent generated
  more than once), and a recommended overlap chosen on these numbers.

## Task 3 — Overpass→Geofabrik input difference, effect on C-phase numbers

**Design:** 30 Ankara evaluation chips — per density stratum, 4 by seeded random draw
(seed 42) + the 2 with the highest forest fraction (forest fraction computed from the
existing Overpass inputs with the canonical palette classifier; the selection rule is
fixed here before any score exists). Inputs regenerated from the **fixed Geofabrik
snapshots** with post-fix `-s smart` extraction and the CLC+ base; all four arms run
through the byte-verified inference path; scored with the unchanged KARIOS config against
the existing `run/ref` warps. **Namespace isolation:** every artifact under
`tubitak/data/tool_runs/task3/` — nothing Package A reads is touched; `run/inputs` and all
existing fakes are read-only to this task.

Reported: per-arm paired difference PBF-inputs vs Overpass-inputs (absolute effect); the
change in **between-arm** paired differences (C1−pre, C2−pre, C3−C2 — the quantities the
conclusions rest on); both repeated for the forest-heavy subset (chips at or above the
130-chip forest-fraction 90th percentile).

**Registered restatement criterion:** the C-phase numbers must be restated if any
between-arm paired difference on the 30-chip subset moves by **more than 0.15 px** (the
project's standing materiality band) between input sources, **or** any headline sign flips
(C2 beats C1; both beat pretrained; C3−C2 null on Ankara). Absolute per-arm shifts alone —
however large — do not trigger restatement; they are the common-mode term the pairing is
designed to cancel, and they are reported as the measured size of that term.

## Task 4 note (procedure, no threshold needed)

Training-input provenance is established from repository records (commit timestamps,
packaging times, extract mtimes, document statements), not memory; if the records are
insufficient the answer is recorded as "unknown", not guessed.


---

## Correction note — 2026-08-26: the reference directory was named wrongly in this text

**What was wrong.** Task 1 above named the reference renders as
`tubitak/data/rasteriser/chips/<stem>.tif`. That directory holds the **WorldCover-era**
corpus, rendered before the CLC+ base layer was introduced in commit `e15f5a9`
(2026-08-19 11:48); its files are dated 2026-08-18 19:43. The CLC+ renders this gate
actually used are in **`tubitak/data/rasteriser/chips_clc/`** (55 files, dated
2026-08-19 11:46). The original wording is struck through above rather than deleted.

**How it was found.** Gate R of the QGIS plugin work package
([plugin-gate-registrations.md](plugin-gate-registrations.md)) inherited this path verbatim
from this registration. Its first run failed **0/3** with a dominant
`light_green -> forest_green` class flow — the signature of comparing a CLC+ render against
a WorldCover render, not of a broken renderer. The failure is recorded in that package's
amendment 1 and in [plugin-results.md](plugin-results.md).

**Evidence that the numbers here are unaffected.** This is a text defect, not a data
defect, and the distinction is measurable rather than argued. The current renderer's output
is byte-identical to `chips_clc/` and **differs** from `chips/` for every stem the committed
census `tool_runs/task4/acc_census.csv` marks `byte_exact = 1`:

| stem | census `byte_exact` | vs `chips/` | vs `chips_clc/` |
|---|---|---|---|
| 30TXQ_0830_00 | 1 | differs | **identical** |
| 30TXQ_0934_00 | 1 | differs | **identical** |
| 30UYD_0907_00 | 1 | differs | **identical** |

A census recording `byte_exact = 1` therefore cannot have been comparing against `chips/`,
because nothing the renderer produces matches `chips/`. Two further confirmations: the
census has **55 rows** and `chips_clc/` holds **55 files**; and this registration's own
sentence already reads "257 px, **CLC+ base**" — the description was correct and only the
path string was wrong.

**Status.** Text corrected; **no result is retracted and no number changes.** Standing
practice 5 — *registration text must name the exact corpus and the exact reference
directory* — was added to `CLAUDE.md` because of this defect and the reference-directory
error it later contributed to in Gate D.
