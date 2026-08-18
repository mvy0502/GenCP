# OSM raster palette — specification and open gaps

**Status:** PARTIAL. The area-class palette is established from data. The class mapping,
rendering order and line rendering are **not** established. **The rasteriser has not been built** —
see §7 for why, and what would close the gap.
**Date:** 2026-08-18

---

## 1. Does the repository already contain a rasteriser?

**No rasteriser. Yes, colour tables.**

| file | contents | status |
|---|---|---|
| `GenCP_HR_demo/genCP_HR_osm_colors.py` | `color_dict` (22 names → hex) plus `highway_colors`, `natural_colors`, `landuse_colors`, `CLC_color_mapping` tag→name tables | **referenced by nothing** — `grep` across all `.py` and notebook source finds zero imports |
| `GenCP_VHR_demo/genCP_VHR_osm_colors_and_width.py` | VHR palette, `default_highway_widths` (values 1-3 px), and a **`building_colors`** dict | VHR only; different colour convention |

No code anywhere renders OSM vectors: no `osmnx`, `geopandas`, `shapely`, `rasterio.features`
or `rasterize` import exists in the repository. The rasters were produced by tooling that was
**not released**.

**Consequence:** the HR colour table is unverified dead code. It cannot be trusted as a description
of what actually produced the rasters, and §3 shows it is in fact wrong in two ways.

---

## 2. The palette is closed — for area classes

Anti-aliasing makes a naive histogram useless: across all 630 demo rasters there are **907,645
distinct RGB values**, and only 54.8 % of pixels sit exactly on a declared colour.

The resolution is to look only at **flat-region interiors** — pixels whose eight neighbours are all
identical. Anti-aliased pixels lie at boundaries and are excluded by construction.

> 200 demo rasters, 13,209,800 px, of which 5,365,645 (40.6 %) are flat interior.
> **Distinct colours in those interiors: 11.** Ten of them account for **100.0000 %**.

| # | RGB | hex | class | interior share |
|---|---|---|---|---|
| 1 | (133, 224, 133) | `#85e085` | light_green | 58.68 % |
| 2 | (0, 153, 51) | `#009933` | forest_green | 25.72 % |
| 3 | (128, 204, 255) | `#80ccff` | water | 13.83 % |
| 4 | (204, 204, 204) | `#cccccc` | gray | 0.597 % |
| 5 | (195, 186, 141) | `#c3ba8d` | no_vegetation | 0.338 % |
| 6 | (255, 255, 204) | `#ffffcc` | sand | 0.330 % |
| 7 | (238, 204, 255) | `#eeccff` | light_purple | 0.309 % |
| 8 | **(165, 42, 42)** | **`#a52a2a`** | **buildings — NOT DECLARED** | 0.186 % |
| 9 | (230, 230, 230) | `#e6e6e6` | light_gray | 0.008 % |
| 10 | (255, 243, 230) | `#fff3e6` | residential_road | 0.002 % |

**The palette is closed.** The 45.2 % of pixels that are off-palette are boundary blends: 64.6 % of
them fit a two-colour convex blend of palette entries to within 3 DN, and the remainder are
near-palette values a few DN away. None occur in flat interiors.

---

## 3. Two errors in the declared table

### 3.1 Buildings are missing entirely

`#a52a2a` is the 8th most common interior colour and appears in **no** dict in
`genCP_HR_osm_colors.py`, which has no building mapping of any kind. Its morphology identifies it:

> 434 connected components measured — **median area 11 px, median bounding-box fill 0.60**.
> Compact blobs, not lines. The VHR sibling file *does* carry a `building_colors` dict.

**Evidence-based conclusion: `#a52a2a` = buildings.** The exact OSM tag scope (all `building=*`, or
a subset) is **not** established.

### 3.2 Three declared colours are never rendered

Across all 41,610,870 demo pixels, exact-match counts:

| declared colour | hex | exact pixels |
|---|---|---|
| yellow_farm | `#ecffb3` | **0** |
| red_road | `#ff5050` | **0** |
| orange_road | `#ff944d` | **0** |

`highway_colors` maps `motorway → red_road` and `trunk → orange_road`, yet neither colour occurs
anywhere. So either the renderer used a different highway table, or motorways/trunks are absent
from all 630 chips — the latter being implausible for 630 chips across four MGRS tiles.

**The declared table is not the table that produced these rasters.**

---

## 4. Roads are rendered almost entirely as blends

Exact-match pixel counts for the road colours, over 41.6 M pixels:

| class | exact px | class | exact px |
|---|---|---|---|
| residential_road | 561 | tertiary_road | 16 |
| track | 166 | light_orange_road | 10 |
| foot_path | 92 | medium_orange_road | 6 |
| unclassified_road | 21 | | |

Roads clearly exist in the imagery — after nearest-palette classification they occupy ~2.3 % of
pixels — but they almost never take their exact colour, because they are thin lines whose every
pixel is blended with the background.

Measured rendered width (distance transform over road-classified components, 1601 components):

> **median 2.00 px, p90 2.83 px** — 1091 components at 2 px, 411 at 3 px, 91 at 4 px.

This matches the VHR `default_highway_widths` table (values 1-3, most classes 2), which suggests
the HR renderer used the same width convention — **but that is an inference, not a verified fact.**

---

## 5. Nearest-palette class shares (all 630 demo rasters, blends assigned to nearest)

| class | share | class | share |
|---|---|---|---|
| light_green | 50.12 % | track | 0.85 % |
| forest_green | 17.26 % | light_gray | 0.84 % |
| water | 13.63 % | foot_path | 0.79 % |
| light_purple | 3.91 % | sand | 0.45 % |
| **buildings** | 3.69 % | residential_road | 0.45 % |
| no_vegetation | 3.40 % | snow | 0.34 % |
| gray | 2.66 % | unclassified_road | 0.11 % |
| rock | 1.24 % | black / tertiary / light_orange / medium_orange | < 0.1 % each |

---

## 6. What is NOT established

1. **Colour → OSM class mapping is declared, not verified.** No chip footprint has been queried
   against live OSM to confirm which features actually produce which colour. Given §3, the declared
   tag tables cannot be assumed correct.
2. **Rendering order is unknown.** Which class wins where features overlap has not been determined.
3. **Building tag scope is unknown** (§3.1).
4. **The anti-aliasing kernel and rendering engine are unknown.** 45 % of pixels are blends. A
   different engine produces different blends even with an identical palette and identical geometry.
5. **HR line widths are inferred from the VHR table**, not measured against a known input.
6. **`black` (`#000000`, 0.07 %) and `snow` (`#ffffff`, 0.03 %) are unexplained.** `CLC_color_mapping`
   maps CLC code 0 → black and 11 → snow, hinting the renderer also consumed CORINE Land Cover, not
   OSM alone — which would be a second data source we do not have.

---

## 7. Recommendation: do not build the rasteriser yet

The **palette** is pinned down. The **renderer** is not, and the two are not separable in practice:
45 % of every raster is anti-aliasing produced by unknown tooling, roads are ~100 % blended, and the
one released colour table is demonstrably not the one used.

Building a rasteriser now would produce plausible-looking rasters that differ from the training
distribution in ways that are invisible to inspection and would surface only as degraded model
output — precisely the failure mode this investigation exists to prevent.

**Three ways to close the gap, cheapest first:**

* **(a) Verify the class mapping against live OSM.** Query Overpass for a handful of chip footprints
  (each transform gives exact bounds) and check which features fall where each colour appears. This
  settles §6.1, §6.2 and §6.3 and needs no new data.
* **(b) Test the model's sensitivity to rendering differences before committing.** Take a demo chip,
  perturb it in ways a different renderer plausibly would (re-quantise the anti-aliasing, vary road
  width by ±1 px, shift a colour by a few DN), push it through the network and measure the change.
  If output is insensitive, exact AA reproduction does not matter and the risk collapses. **This is
  the highest-value single experiment** and it decides how much fidelity is actually required.
* **(c) Ask the authors** for the rasterisation script, alongside the `train_opt.txt` question
  already open in `train-test-scale-mismatch.md` §5.

Option (b) is worth running first: it converts an unbounded fidelity requirement into a measured
tolerance.

---

## 8. Edge profile — the measured anti-aliasing specification

Measured with `tubitak/scripts/edge_profile.py` over 100 demo + 100 corpus rasters: every row and
column is scanned for maximal runs of non-palette pixels flanked by exact-palette pixels, each run
pixel projected onto the RGB segment between the flanks (blend fraction *t*), runs off the segment
by >6 DN discarded as junctions. Perpendicular widths use the local edge normal from a Sobel field;
32k area-area transitions and 9k road crossings were kept.

### 8.1 Transition geometry

Raw run lengths look wide (median 5 px), but the **mean t-profiles** show what those runs contain
(near-perpendicular subset):

| run | mean t per pixel | erf fit σ |
|---|---|---|
| 4 px | 0.035 · 0.377 · 0.627 · 0.976 | 1.05 px |
| 5 px | 0.014 · 0.023 · **0.541** · 0.988 · 0.988 | 0.48 px |
| 6 px | 0.011 · 0.026 · **0.21 · 0.81** · 0.980 · 0.986 | 0.61 px |

The genuine blend is **1–2 intermediate pixels** (an erf step, weighted mean **σ = 0.68 px**);
the remaining run pixels sit within a few DN of the flanking colours — real but tiny deviations
that keep them off-palette without being visible blends.

**Interpretation:** a sharp antialiased core plus low-amplitude tails extending ±2 px is the
signature of resampling with a kernel that has negative lobes (bicubic/Lanczos) — consistent with a
hard-edged render at higher resolution followed by a bicubic-style downsample, and *inconsistent*
with either plain supersampling (σ ≈ 0.29, single intermediate pixel, no tails) or a wide Gaussian
(no tails, σ ≫ 1 would be needed to explain the run lengths, contradicting the profiles).

### 8.2 Consistency and isotropy

* **Demo vs corpus agree**: σ = 0.677 vs 0.684 px — one renderer produced both.
* **Isotropic**: perpendicular-corrected width varies only 4.1–4.8 px across orientation bins
  0–15°/15–30°/30–45°, with no near-axis staircase signature. Filter-like, not supersampling-like.

### 8.3 Roads

Transverse road crossings (flanks equal, interior nearest a road colour): **median full width 6 px**
— a ~2 px core (matching the earlier distance-transform measurement and the VHR width table) plus
~2 px of AA tail each side. Road pixels almost never reach their exact palette colour because a
2 px line under a σ≈0.7 kernel never fully saturates: this is why roads are ~100 % off-palette.

### 8.4 The specification the rasteriser must hit

1. Interiors byte-exact on the 11-colour palette.
2. Area-area boundaries: erf-like transition, **σ = 0.68 ± 0.15 px**, isotropic.
3. Roads: 2 px core width before smoothing.
4. If the target cannot be hit exactly, err toward **harder** edges (renderer-tolerance.md: over-smoothing measured 1.7× worse).

---

## 9. WorldCover → palette class mapping, derived from evidence

The base layer requires a mapping from ESA WorldCover v200 classes to the 11-colour palette. It is
written down nowhere (`CLC_color_mapping` maps CORINE codes, a different scheme), and an initial
mapping chosen by inspection proved wrong in two places when checked — the confusion below is the
authority.

**Method:** 40 fitting chips **disjoint from every scored set** (not in the 30 sensitivity chips,
not in the 116 arm chips). Per pixel: reference raster colour (nearest-palette) × WorldCover class
at the same location. OSM overlay features contaminate the matrix from above (roads, buildings,
mapped landuse), which is why plurality rather than purity is the read-out.

| WC class | pixels | reference distribution (top 3) | mapping | status |
|---|---|---|---|---|
| 10 tree | 979,638 | forest_green 69.8 · light_green 17.0 · light_purple 6.3 | **forest_green** | confirmed |
| 20 shrub | 44,625 | light_green 54.5 · forest_green 39.1 · no_veg 2.1 | **light_green** | confirmed (noisy) |
| 30 grass | 554,275 | light_green 76.0 · forest_green 5.8 | **light_green** | confirmed |
| 40 crop | 819,976 | light_green 89.9 · water 3.8 | **light_green** | confirmed |
| 50 built | 166,029 | light_purple 29.2 · building 24.5 · gray 13.3 | **light_purple** | **AMBIGUOUS** — plurality; inspected guess (gray) was 3rd |
| 60 bare | 13,625 | light_green 44.7 · no_veg 41.2 | **no_vegetation** | **AMBIGUOUS** — near-tie, kept on semantics |
| 70 snow | 0 | absent from fitting chips | snow | unverified default |
| 80 water | 58,077 | water 94.6 | **water** | confirmed |
| 90 wetland | 5,715 | **water 85.4** · light_green 11.3 | **water** | **corrected** — inspected guess (light_green) was wrong |
| 95/100 | 0 | absent | forest_green / light_green | unverified defaults |

Two corrections against inspection (50, 90) on 4 % of pixels — exactly the "looks obvious and is
wrong" failure the evidence check exists to catch. WorldCover vintage is 2021; reference imagery
vintage is unknown; class drift between them is a residual, unquantified error source.
