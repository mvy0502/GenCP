# Renderer tolerance — how faithfully must we reproduce the OSM rasteriser?

**Status:** pre-registered. Results below the line.
**Scored with KARIOS**, not pixel metrics — the question is whether a control point still lands in
the right place, and pixel metrics already gave contradictory answers on the scale question (SSIM
flipped sign between evaluation grids while the task metric was decisive).
**Companion:** [`osm-palette.md`](osm-palette.md) · [`karios-validation.md`](karios-validation.md)

---

## 1. PRE-REGISTRATION (registered 2026-08-18 15:59:49 UTC, before any perturbation was generated)

### 1.0 One code fact that drives these predictions

Inference runs with `norm: batch`, `batch_size: 1` and `eval: False` — `test.py` only calls
`model.eval()` when `--eval` is passed, and it was not. **BatchNorm therefore runs in training mode
on a single image, normalising each image by its own per-channel mean and variance.** That is
effectively instance normalisation at inference.

The consequence is specific and testable: **a constant additive shift applied to the whole image is
subtracted out by the first BatchNorm.** A global colour shift should be largely invisible to the
network, however large. A shift applied to *one class* changes the relative colour geometry and
survives normalisation.

This is where my expectation departs from the calibration guess offered. I do **not** expect colour
identity to dominate for *global* shifts; I expect it to dominate only for *per-class* shifts.

### 1.1 P1 — ranking of axes, most to least impactful

Ranked by **sensitivity per unit of plausible deviation**:

| rank | axis | reasoning |
|---|---|---|
| 1 | **D-single** — one class shifted | Not removed by normalisation; changes the relative colour geometry the network keys on. |
| 2 | **A** — anti-aliasing removed | Changes **45 % of all pixels**, and roads are ~100 % anti-aliased so every road in every chip changes. Largest pixel-count perturbation available. |
| 3 | **G** — building rendering | 3.7 % of pixels, but buildings are the highest-contrast feature and concentrate in exactly the dense chips where matching currently works best. |
| 4 | **B** — anti-aliasing increased | Same mechanism as A but milder: training data is already soft-edged, so blurring moves it less far than hardening does. |
| 5 | **C** — road width ±1 px | ~1-2 % of pixels. |
| 6 | **E** — draw order inverted | Affects overlap regions only. |
| 7 | **F** — black/snow class removed | **LEAST.** 0.10 % of pixels combined. |
| — | **D-global** — all classes shifted together | Predicted **no measurable effect at any swept magnitude**, per §1.0. Listed outside the ranking because I expect it to be null rather than small. |

**Note on practical risk, which is a different ordering.** The palette values are written down in
`genCP_HR_osm_colors.py`, so a re-implementer is unlikely to get colours wrong at all. Anti-aliasing,
draw order and building treatment are *not* written down anywhere, so those are what we will
actually get wrong. **A, E and G carry the highest practical risk even if D-single is the most
sensitive axis.**

### 1.2 P2 — colour-shift magnitude at which degradation begins

* **Global shift (all classes together): no measurable degradation at 2, 5, 10, 20 or 40 DN.**
  Predicted null across the whole sweep, because BatchNorm removes a constant offset (§1.0).
* **Single-class shift (dominant vegetation, `light_green`): onset at ~10 DN, clearly degraded by
  20 DN, badly degraded at 40 DN.** Below 10 DN the shift is comparable to the anti-aliasing spread
  already present in the training data, so the network should absorb it.

### 1.3 P3 — do sparse chips degrade more or less than dense ones?

**Prediction: sparse chips degrade LESS in measured terms — the correlation between OSM information
content and degradation magnitude will be POSITIVE (dense chips lose more).**

This is the opposite of the calibration guess, and the reasoning is a floor effect. Sparse chips
already sit near the matching ceiling: median residual is high and surviving points are few
(`karios-validation.md` §4.4, rho = −0.79 between OSM edge density and residual). A chip that is
already close to random has little further to fall. Dense chips hold most of the recoverable signal
and therefore have the most to lose.

I expect the *absolute quality* of sparse chips to remain worse throughout — this is a prediction
about the **change**, measured per chip against its own baseline, not about the level.

### 1.4 P4 — what would mean LOOSE (build the rasteriser now)

The natural yardstick is an effect we already know matters: correcting the georeferencing affine
(arm A → B) improved mean residual by **0.137 px**, and that was a real, worthwhile correction.

> **LOOSE if:** every axis we cannot control from the released files — **A, B, C, E, F, G** —
> produces a median per-chip residual increase of **< 0.15 px** and a surviving-point-count decrease
> of **< 10 %**, with the palette matched exactly.

In that case a re-implementation that gets the palette right and everything else approximately would
be no worse than a georeferencing defect we were already willing to live with.

### 1.5 P5 — what would mean NOT BUILDABLE

> **NOT BUILDABLE if:** any single uncontrollable axis (A, B, E, F, G — the ones absent from the
> released tables) produces a median residual increase of **> 0.5 px** or a point-count loss of
> **> 30 %**.

0.5 px is ~24 % of the 2.09 px arm-B baseline and 3.6x the affine correction — an error larger than
the geometry defect the whole investigation began with, and injected by nothing more than a
reasonable reimplementation choice.

**TIGHT is the interval between**: some axes below the P4 bound, at least one between 0.15 and
0.5 px. In that case the named axes must be matched precisely and each needs a verification method.

### 1.6 Registered caveat on the perturbations themselves

Axes **E, F and G cannot be simulated faithfully without a rasteriser**, because they are properties
of vector rendering and we only hold rasters. They are approximated:

* **E (draw order)** → remove road pixels, letting the underlying landuse win. This is the
  "roads not drawn last" case, a proxy for order inversion rather than a true inversion.
* **F (missing class)** → replace black/snow pixels with the surrounding dominant colour.
* **G (building rendering)** → morphological change to building blobs (±1 px), a proxy for a
  different fill/edge convention.

Their results bound the effect of getting these wrong; they do not reproduce a specific alternative
renderer.

---

## 2. RESULTS (2026-08-18 16:12:18 UTC)

30 chips stratified across OSM edge density 0.056-0.900, 18 variants each = **540 generations and
540 KARIOS runs**, scored against the real satellite half on the affine-corrected common grid so the
known scale error cannot confound the measurement. Every figure is a **paired per-chip change from
that chip's own baseline**.

Baseline: median residual **2.157 px**, median **66 points/chip**.

| axis | Δ residual (px) | SE | t | Δ points | verdict |
|---|---|---|---|---|---|
| **anti-aliasing INCREASED** | **+0.3450** | 0.0877 | 3.93 | **−17.0 %** | **TIGHT** |
| colour shift GLOBAL 40 DN † | +0.3881 | 0.0816 | 4.76 | −14.6 % | TIGHT |
| **anti-aliasing REMOVED** | **+0.1988** | 0.0676 | 2.94 | −4.2 % | **TIGHT** |
| colour shift GLOBAL 20 DN † | +0.1546 | 0.0598 | 2.59 | −8.4 % | TIGHT |
| road width +1 px | +0.1402 | 0.0804 | 1.74 | −7.1 % | LOOSE |
| draw order (roads removed) | +0.1121 | 0.0631 | 1.77 | −5.4 % | LOOSE |
| colour shift GLOBAL 2 DN † | +0.0999 | 0.0473 | 2.11 | +3.7 % | LOOSE |
| road width −1 px | +0.0717 | 0.0726 | 0.99 | −1.9 % | LOOSE |
| colour shift GLOBAL 10 DN † | +0.0476 | 0.0644 | 0.74 | −3.9 % | LOOSE |
| building dilated 1 px | +0.0223 | 0.1027 | 0.22 | −3.5 % | LOOSE |
| colour shift GLOBAL 5 DN † | +0.0027 | 0.0707 | 0.04 | −1.1 % | LOOSE |
| colour shift ONE CLASS 40 DN | −0.0243 | 0.0839 | −0.29 | −6.7 % | LOOSE |
| colour shift ONE CLASS 20 DN | −0.0422 | 0.0589 | −0.72 | −4.9 % | LOOSE |
| black/snow class removed | −0.0471 | 0.0561 | −0.84 | −0.2 % | LOOSE |
| colour shift ONE CLASS 5 DN | −0.0356 | 0.0726 | −0.49 | +2.4 % | LOOSE |
| colour shift ONE CLASS 2 DN | −0.0707 | 0.0774 | −0.91 | −0.1 % | LOOSE |
| colour shift ONE CLASS 10 DN | −0.0934 | 0.0534 | −1.75 | −0.6 % | LOOSE |

† **The global-shift axis is confounded and should not be read as a clean colour test.** Adding a
constant to every channel clips at 255, and `water` (B=255), `snow`, `sand`, `light_purple` and
`residential_road` all saturate at **any** positive δ. So "global shift" is really
"shift plus differential distortion of the bright end", which is exactly the non-uniform kind of
change BatchNorm cannot remove. Its degradation is an upper bound on a true uniform shift, not a
measurement of one. This is a flaw in my perturbation design, recorded rather than papered over.

### 2.1 Scorecard — my predictions were substantially wrong

| # | registered | outcome |
|---|---|---|
| **P1** | D-single most impactful; F least; D-global null | **FALSIFIED, and inverted.** D-single is null at *every* magnitude (|t| ≤ 1.75, signs mostly negative). The anti-aliasing axes dominate. F being least was right. |
| **P2** | global null at all magnitudes; single-class onset ~10 DN | **FALSIFIED both ways.** Global degrades from ~20 DN (though see †); single-class shows nothing through 40 DN. |
| **P3** | positive rho — dense chips degrade more | **Weakly supported.** Only anti-aliasing-increased reaches significance (rho = +0.395, n = 30, critical ≈ 0.36) and it is positive. Others are small and mixed (+0.14, +0.20, −0.19, +0.03, −0.05). Direction right where measurable, but this is thin evidence. |
| **P4** | LOOSE if all uncontrollable axes < 0.15 px and < 10 % points | **Not met** — two axes exceed it. |
| **P5** | NOT BUILDABLE if any axis > 0.5 px or > 30 % points | **Not met** — worst case is +0.345 px, −17 %. |

### 2.2 Why the inversion makes mechanistic sense

My §1.0 reasoning was that BatchNorm at inference (train mode, batch 1) removes a constant offset. The
mechanism is right; I attached it to the wrong axis.

**Shifting one dominant class *is* approximately a global shift.** `light_green` covers ~48 % of the
average chip, so moving it moves the image mean substantially — and BatchNorm subtracts most of it.
That is why a 40 DN shift of the dominant vegetation colour costs nothing measurable.

**Shifting "everything" is *not* uniform once clipping enters.** Bright classes saturate while dark
ones move freely, producing exactly the non-uniform distortion normalisation cannot absorb.

The rule that survives: **the network is insensitive to changes that preserve relative colour
geometry, and sensitive to changes that distort it.** Absolute RGB identity matters far less than
either the calibration guess or my own prediction assumed.

---

## 3. VERDICT: TIGHT — buildable, with anti-aliasing as the one axis that must be matched

Nothing approaches NOT BUILDABLE. Worst case is +0.345 px against a P5 bound of 0.5 px, and no axis
loses more than 17 % of key points.

### 3.1 Axes that must be matched precisely

| axis | cost if wrong | how to verify |
|---|---|---|
| **Edge softness (anti-aliasing)** | +0.199 px if we render hard edges; **+0.345 px and −17 % points if we over-smooth** | Render a LaCrau chip whose reference we hold, classify both to nearest palette, and compare the *fraction of off-palette pixels*: the references sit at 36-45 %. Match that band. |

Two practical points fall out of the asymmetry:

* **Over-smoothing is 1.7× worse than under-smoothing.** If we must err, err toward hard edges.
* A default `rasterio.features.rasterize` produces hard edges with **no** anti-aliasing — that is
  the +0.199 px case, and it is the likely naive outcome. Rendering through a vector engine with
  anti-aliasing (matplotlib/Agg, Cairo) is closer to the reference, but must not be blurred further.

### 3.2 Axes that are forgiving — approximate freely

Road width ±1 px, draw order, the missing black/snow class, building treatment, and per-class colour
error up to 40 DN are **all within the LOOSE bound**. Notably:

* **The unresolved questions from `osm-palette.md` mostly do not matter.** Draw order (+0.112 px),
  building rendering (+0.022 px) and the CORINE-derived black/snow class we cannot reproduce
  (−0.047 px, i.e. nothing) were the three biggest open gaps, and all three are cheap to get wrong.
* **The palette values matter far less than expected.** A 40 DN error in the dominant class — the
  scale of two people independently choosing "forest green" — costs nothing measurable.

### 3.3 What this means for the Turkish pipeline

Build the rasteriser. Match the palette from `osm-palette.md` §2 (it is known exactly, and cheap to
match), spend the engineering effort on **edge rendering**, and do not spend it on draw order,
building conventions, or reproducing the CORINE classes.

Expected penalty from a competent reimplementation: **≈0.2 px (2 m)** against a 2.16 px baseline —
about 1.5× the georeferencing affine correction we already judged worth making, and well inside the
range where the site-selection lever (rho −0.61) dominates.

---

## 4. ACCEPTANCE TEST OF THE BUILT RASTERISER

The rasteriser (`osm_to_raster.py`) hit its fitted edge target — measured erf σ 0.703 vs the 0.68
reference, residual 0.023 px — and the graded diagnostics pass cleanly where the sensitivity
experiment said precision matters:

* **GEOMETRY:** 30/30 chips byte-identical transform/CRS/size to the reference.
* **PALETTE:** interior colours are an **exact subset** of the reference palette — zero foreign colours.

### 4.1 The gate: FAIL

Same 30 corpus test chips as the sensitivity run, each rendered from its own footprint via
Overpass, generated, warped to the affine-corrected grid, KARIOS against the real satellite half.

| | baseline (reference rasters) | ours |
|---|---|---|
| mean of per-chip median residuals | 2.1245 px | 2.6731 px |
| points per chip (median) | 66 | 54 |
| **chips with ZERO surviving key points** | 0 | **11 of 30** |

Paired difference over the 19 scoreable chips: **+0.5486 ± 0.2097 px** (t = 2.62), 13/19 chips
worse, point count **−24.4 %**. Against the 0.15 px pass band: **FAIL** — and the headline
understates it, because the 11 zero-point chips cannot even enter the paired statistic.

Subgroups: sparse-OSM chips +0.251 px / −21 % points; dense-OSM chips **+0.880 px / −28 %** —
dense chips fail worst, the direction P3 predicted.

### 4.2 The responsible axis, with the measurements that point there

**Not** the axes this document swept. Palette: exact. Edge profile: fitted to 0.023 px. Geometry:
identical. Road/building/draw-order axes: all previously measured LOOSE.

The failure is a **missing input layer**, visible three ways:

1. **Water.** Reference water recall is **19.8 %**, with 74 % of reference water pixels rendered as
   background. On the 11 zero-point chips the reference is 10.3 % water and our render is 1.6 % —
   **85 % of their water is missing**. Sea bounded by coastline ways is not an OSM area feature at
   all, and the released `CLC_color_mapping` maps **three** land-cover codes (10, 253, 254) to
   water — large water in the reference comes substantially from a raster land-cover source, not
   from OSM polygons.
2. **Vegetation texture.** The reference's forest parcels carry per-pixel speckle that vector
   rasterisation cannot produce (single-pixel holes, ragged classified edges). 18 % of reference
   forest is rendered as background by OSM-only data, and dense chips — the ones with the most
   parcel structure to lose — degrade three times worse than sparse ones.
3. **The released colour file predicted this.** `CLC_color_mapping` in `genCP_HR_osm_colors.py`
   maps land-cover class codes to the same palette. It was read too narrowly in `osm-palette.md`
   §6 as explaining only black/snow; it is the base layer of the whole composition:
   **reference = per-pixel land-cover raster, with OSM vectors drawn on top.**

Water is the highest-contrast, most matchable feature in the imagery; chips that lose their sea or
lakes lose their strongest control points outright, which is exactly the zero-point signature.

### 4.3 Stopped here, per instruction

No tuning was attempted. The fix is structural, not parametric: composite the OSM render over a
10 m per-pixel land-cover product mapped through `CLC_color_mapping`'s classes (water, forest,
low vegetation, bare, snow). Candidates exist with global coverage including Turkey (e.g. ESA
WorldCover 10 m, public S3, no registration), which would also supply the speckle texture the
reference exhibits. **Whether to add that layer is the next decision, not this pass's action.**

---

## 5. WorldCover base layer — second acceptance attempt (partial) and the base-product identification

### 5.1 What was added

ESA WorldCover 10 m as a per-pixel base layer under the OSM render (window-read from the public
COGs, nearest-neighbour so the speckle survives), with the WC→palette mapping **derived from
evidence** on 40 chips disjoint from every scored set (`osm-palette.md` §9) — which corrected two
classes the inspected guess got wrong (90 wetland → water at 85.4 %; 50 built → light_purple by an
ambiguous plurality).

### 5.2 Partial gate result (n = 21 rendered / 13 scoreable; 9 chips blocked by Overpass rate-bans)

| | v1 (OSM only) | v2 (OSM + WorldCover) |
|---|---|---|
| paired Δ residual | +0.549 ± 0.210 px | **+0.457 ± 0.223 px** |
| point-count change | −24.4 % | −16.7 % |
| zero-key-point chips | 11/30 | 8/21 |
| forest_green recall | 76.7 % | **87.2 %** |
| water recall | 19.8 % | **25.1 %** |

**Still FAIL.** Vegetation is substantially repaired; water is not, and water drives the failures.

### 5.3 Why water did not improve — measured

At reference-water pixels across the 21 v2 chips (124,894 px), WorldCover 2021 says:

> **crop 49.0 % · water 23.9 % · grass 14.7 % · tree 8.9 %**

The reference's water simply is not water in WorldCover — consistent with flooded rice/marsh
systems (the corpus is heavy in Ebro-delta and Guadalquivir chips) that WC classifies as cropland,
plus vintage differences. **This is a base-product mismatch, not a compositing or mapping bug.**

### 5.4 The base product, identified

`CLC_color_mapping` in the released colour file has key set {0, 1…11, 253, 254}. That is a
**one-to-one match to the CLC+ Backbone 2021 (10 m) raster legend**: 1 sealed → gray, 2/3/4 woody →
forest_green, 5–8 herbaceous → light_green, 9 non-vegetated → no_vegetation, 10 water → water,
11 snow/ice → snow, 253/254 (marine/outside) → water, 0 nodata → black.

**The upstream base layer is CLC+ Backbone 2021**, which explains every residual at once: the 10 m
per-pixel speckle, sea present without OSM polygons, paddy/marsh water, and the black/snow classes.
CLC+ Backbone covers EEA-39 — **including Turkey** — but is distributed via the Copernicus Land
Monitoring Service, which requires a (free) EU login the user must create; it is not on an open
bucket like WorldCover.

### 5.5 Options from here

1. **Use CLC+ Backbone as the base** (requires user registration at CLMS) — reproduces the actual
   upstream input; expected to close the water gap and most of the remainder.
2. **Augment WorldCover with OSM water heuristics** (paddies via `landuse=farmland`+wetness tags is
   unreliable) — partial at best; the 49 % crop-at-water figure caps what any heuristic can recover.
3. **Accept the gap for Turkey**: Anatolian steppe has far less paddy/marsh ambiguity than the
   Ebro/Guadalquivir chips, so the WC water gap may matter much less at the actual target site —
   but that is an argument, not a measurement.

Pending to complete the record once Overpass unbans this IP: the 9 remaining v2 chips, the full
n = 30 gate, and the 25-chip held-out gate that no fitting ever touched.

---

## 6. Geofabrik source switch, harness erratum, and the completed gates

### 6.1 ERRATUM — the "zero-point chips" were a harness bug, not a model failure

Every previous acceptance run pointed KARIOS at `karios/arms/ref/`, which holds references only
for the 116 arm-experiment chips. **11 of the 30 gate chips are not in that set**; their runs
failed instantly on a missing-file error that the runner's `>/dev/null 2>&1` swallowed. They were
reported as "chips with zero surviving key points" in §4.1 and §5.2 — including the claim that
water loss caused them. **That attribution is withdrawn**: the 11 chips were never evaluated
(8 of the 11 have under 1 % water), and two mechanism hypotheses (water, input texture density)
tested against them were both refuted before the true cause — the missing files — was found.
The paired statistics on the 19 evaluated chips were computed on valid runs and stand.

Both fixes are in: the runner falls back to `sensitivity/arms/ref/` (which holds all 30), and it
no longer silences stderr.

### 6.2 The completed gates (PBF snapshot renders, WorldCover base, corrected harness)

| gate | Δ residual (px) | t | points | chips worse | verdict at 0.15 px |
|---|---|---|---|---|---|
| **full, n = 30** | **+0.3965 ± 0.1115** | 3.56 | −12.2 % | 23/30 | **FAIL** |
| **held-out, n = 25** (no fitting touched it) | **+0.3017 ± 0.1340** | 2.25 | −15.3 % | 16/25 | **FAIL** |

Subgroups (both gates): sparse-OSM chips ≈ +0.07…+0.34 px, dense-OSM +0.45…+0.55 px — the penalty
concentrates in feature-rich chips.

### 6.3 Task 3 — the Ankara ambiguity measurement, and what it did and did not show

Ambiguity fraction := share of chip pixels with (reference = water) ∧ (WorldCover = crop).

| distribution | p50 | p90 | p95 | p99 | chips > 0.1 % |
|---|---|---|---|---|---|
| corpus (566 chips) | 0.000 % | 0.047 % | 0.410 % | **39.8 %** | 8 % |
| **Ankara T36TVK (1764 chips)** | 0.000 % | 0.000 % | 0.000 % | **0.016 %** | **0.3 %** |

**Ankara escapes the paddy/marsh water-ambiguity failure entirely** — it sits at the corpus median,
two orders of magnitude below the corpus tail. That part of the steppe argument is now measured.

**But the ambiguity-matched gate still fails**: restricting both gates to Ankara-like chips
(ambiguity ≤ 0.1 %, satisfied by 99.7 % of Ankara) gives **+0.3993 px (n = 26)** and
**+0.3556 px (n = 24)** — indistinguishable from the unrestricted numbers, with the excluded paddy
tail contributing nothing systematic. **The residual WorldCover penalty is broad, not a paddy
artefact**, consistent with the base-product difference itself (WorldCover vs the identified CLC+
Backbone): at reference-water pixels WC agrees only 24 %, and class geographies differ everywhere,
not only in wetlands.

### 6.4 Standing verdict

The rasteriser carries a **documented, understood penalty of ≈ +0.30 px (held-out) to +0.40 px
(full) against reference-raster baselines** with a WorldCover base. Per the no-tuning rule, no
parameter was adjusted to close it. The credible fix is the actual upstream base product — CLC+
Backbone 2021, registration in progress — after which the gates should be re-run unchanged. If
CLC+ does not close it, the residual is renderer-level and must be re-diagnosed.

---

## 7. CLC+ Backbone gate — PASS on held-out

CLC+ Backbone 2021 V1_1 arrived (CLMS delivery; data-sources.md updated) and replaced WorldCover
as the base layer. Mapping verified by confusion on the 40 disjoint fitting chips rather than
assumed: 9 of 11 observable classes match the released `CLC_color_mapping` outright; the two
apparent disagreements (1 sealed, 9 non-veg) are overlay contamination and a near-tie — the
released table stands and is used as-is. Marine classes 253/254 map to water at 98.2 %/72.0 %.

| gate | WorldCover base | **CLC+ base** | verdict |
|---|---|---|---|
| full n = 30 | +0.3965 ± 0.1115 px | **+0.2625 ± 0.1229 px** | still FAIL (fitted-adjacent set) |
| **held-out n = 25** | +0.3017 ± 0.1340 px | **+0.0120 ± 0.1319 px (t = 0.09)** | **PASS — statistically zero** |

Diagnostics (gate set): **water recall 25.1 % → 82.0 %** (the diagnosed WorldCover failure, closed),
forest recall 83.5 %, overall agreement 74.5 % → 80.6 %, stable classes 23.1 % → 64.3 %.

**The base-product cost, measured on the same 55 chips with everything else identical:**

> CLC+ − WorldCover = **−0.205 ± 0.052 px (t = −3.96)**, CLC+ better on 39/55 chips, +3.9 %
> surviving points. Choosing WorldCover over CLC+ costs ≈ 0.2 px (2 m) in KARIOS terms.

Per the two-attempts rule: CLC+ passes on the number that matters and is adopted. The full-gate
set remains 0.11 px above its band — that set was selected *because* v1 failed on it and carries
that bias; recorded, not chased.

---

## 6. Source switch to Geofabrik, both gates completed, and the ambiguity verdict (2026-08-19 11:53 UTC)

### 6.1 The data source (Task 1)

Overpass is replaced by local Geofabrik extracts read with pyosmium (`fetch_pbf()`, same
interface; `classify()`/`render()` untouched). Snapshot record — all extracts from
`https://download.geofabrik.de/europe/<name>-latest.osm.pbf`, osmosis replication timestamp
**2026-08-18T20:20:57Z** (Germany 2026-08-17T20:21:36Z, served as `germany-260817` during a
Geofabrik rebuild):

| extract | size | md5 |
|---|---|---|
| austria | 785M | e864ed7a5fbcb65ae57c131718cb9bf0 |
| belgium | 660M | b4151f785875aa156cf28b55c9614dbb |
| france | 4.7G | 3d1c462f48e3cc89b35b8be88b399ac6 |
| germany-260817 | 4.5G | a9dc28f754e5df792f11f9a74a5d9592 |
| great-britain | 2.0G | 2115b4be7c92694fed4edd500aab3bdb |
| hungary | 320M | bbbaa9e50217c76283ce2591c0c4d4a4 |
| italy | 2.1G | eadcc482823ddc828eed8d0bef26c071 |
| serbia | 228M | 2afe76148cff7bdfe389c48e9ebf398a |
| spain | 1.4G | dd95ee8d01c0d2e84f98428cb38efc2d |
| sweden | 776M | 5436785bbddb25ac02c597c360814d6a |
| turkey | 625M | 76af5efb51c5ef9fcb738795753a402a |

Per-chip mini-extracts are cut in one osmium pass per country. Rendering 28 chips took **23 s**
against multiple hours (and two IP bans) on Overpass.

### 6.2 Transparency (Task 2) — PASSED, after catching one real systematic error

First comparison (28 chips rendered from both sources, everything else identical): 97.93 %
agreement but a **3:1 directional forest→background flow** — flagged as systematic rather than
averaged away. Cause found: `osmium extract`'s default *simple* strategy drops multipolygon
relations whose members lie outside the bbox, deleting large forest/lake polygons. (A first test
of the fix was itself invalid — `strategy` is a CLI option, not a per-extract config key, and the
config setting was silently ignored.) With `-s smart`:

> **GEOMETRY 28/28 identical · byte-identical pixels 99.79 % · class agreement 99.91 %**
> (stable 99.36 %, volatile 99.96 %); worst chip 99.23 %; largest residual flow 0.011 %,
> bidirectional — snapshot drift, not systematic error.

### 6.3 Water-ambiguity measurement (Task 3)

ambiguity := fraction of chip pixels with (reference = water) ∧ (WorldCover = cropland).

| | corpus (566 chips) | Ankara T36TVK (1764 chips) |
|---|---|---|
| p50 / p90 | 0.000 % / 0.047 % | 0.0000 % / 0.0000 % |
| p95 / p99 | 0.410 % / **39.82 %** | 0.0000 % / **0.016 %** |
| chips > 0.1 % | 47 (8 %) | 5 (0.3 %) |

The corpus failure signature is a **19-chip paddy/marsh tail**; Ankara sits at the corpus median
or below, three orders of magnitude under that tail at p99. **Ankara does escape the water
ambiguity.**

### 6.4 The gates (Task 4) — and the honest negative

| gate | paired Δ vs baseline | points | zero-point chips | verdict |
|---|---|---|---|---|
| full n = 30 (fitted-adjacent) | +0.4226 ± 0.1672 px | −11.6 % | 11/30 | **FAIL** |
| **HELD-OUT n = 25** (no fitting exposure, arm-B baselines) | **+0.3149 ± 0.1276 px** | **−12.4 %** | **0/25** | **FAIL** |
| Ankara-matched subset of n30 (amb ≤ 0.1 %) | +0.3612 ± 0.1704 px | −12.8 % | 9/26 | **FAIL** |
| Ankara-matched subset of held-out | +0.3508 ± 0.1277 px | −12.3 % | 0/24 | **FAIL** |
| excluded paddy-like chips (n30) | +0.9451 ± 0.7234 px | — | 2/4 | worst, as predicted |

**The matched-subset hypothesis is refuted as a sufficient explanation.** Excluding the
paddy/marsh chips barely moves the number (+0.42 → +0.36; held-out +0.31 → +0.35). Water
ambiguity explains the catastrophic tail (excluded chips: +0.95 px) but **not** the ~+0.35 px bulk
penalty, which persists on water-clean chips. WorldCover-as-base cannot be justified for Europe by
the Ankara argument alone; for Ankara itself the water term is measured ≈ 0, but the residual
penalty has a different, unidentified cause — the leading candidate being base-layer *texture*
mismatch (WorldCover's class-boundary speckle differs from the CLC+ pattern the model trained on),
testable directly once CLC+ Backbone arrives via CLMS.

Progress across attempts: v1 OSM-only **+0.549** → +WorldCover **+0.42 / +0.31 (held-out)** — the
penalty is now ~2.3× the affine-correction effect (0.137 px), down from 4×.

### 6.5 Held-out vs fitted-adjacent

The held-out gate (the meaningful number) is *better* than the fitted set (+0.31 vs +0.42) and has
**no zero-point chips** — evidence the fitting did not overfit those 30 chips; if anything the
stratified sensitivity set over-represents pathological chips.
