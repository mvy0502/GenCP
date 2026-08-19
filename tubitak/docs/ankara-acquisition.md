# Ankara Sentinel-2 acquisition — scouting and verification

**Date:** 2026-08-18 · **Site decision:** Ankara (user) · **Status:** TCI downloaded, verified
radiometrically consistent with the corpus. No chips generated yet — gated on the rasteriser
acceptance test.

## 1. Tile

**T36TVK (EPSG:32636, UTM 36N)** — a correction to the earlier scouting note, which said T36SVK
from pure MGRS geometry. Central Ankara (39.85–39.95°N) sits in MGRS band S, but the Sentinel-2
granule grid assigns the area to the band-T granule via its southward overlap: a STAC query for
scenes covering 32.80–32.95°E / 39.85–39.95°N returns **only MGRS-36TVK** (35 acquisitions
Mar–Jun 2025). This is the same granule-vs-square distinction found in the corpus chip naming.

The 110 km granule spans dense urban Ankara, Gölbaşı lakes, Kızılcahamam forest (N) and open
steppe (E/W) — the full OSM information-content range in one tile, as required.

## 2. Acquisition chosen

Spring candidates (T36TVK, April–May 2024–2026, sorted by cloud):

| cloud % | date | vegetation % | id |
|---|---|---|---|
| 0.00 | 2024-04-15 | 37.3 | S2B_36TVK_20240415_0_L2A |
| 0.00 | 2025-04-17 | 27.5 | S2A_36TVK_20250417_0_L2A |
| 1.30 | 2025-05-05 | 45.9 | S2C_36TVK_20250505_0_L2A |
| **2.04** | **2026-04-30** | **51.8** | **S2C_36TVK_20260430_0_L2A ← chosen** |
| 3.49 | 2026-04-25 | 49.1 | S2B_36TVK_20260425_0_L2A |

**Chosen: S2C_36TVK_20260430** — a stated deviation from strict lowest-cloud. Reasoning: 2 % cloud
over a 110 km tile is negligible, while its 51.8 % vegetation is the highest of any candidate
(the corpus sits at peak growing season, median GLI 0.126, so greenness matching is the point of
choosing spring), and the 2026 date minimises the OSM-vs-imagery temporal gap since Overpass
serves the current map.

Source: Element84 Earth Search STAC + the public `sentinel-cogs` S3 bucket — no registration, no
quota. TCI band only: `tubitak/data/ankara/TCI_36TVK_20260430.tif`, **341 MB**, 10980×10980 px,
10 m, uint8 RGB. (CDSE was scouted as the alternative: free registration, 12 TB/month quota —
not needed.)

## 3. Radiometric verification against the corpus

15.7 M Ankara pixels (60 random interior windows) vs 4.7 M corpus satellite-half pixels:

| band | Ankara mean/std | corpus mean/std | histogram overlap (Bhattacharyya) |
|---|---|---|---|
| R | 112.3 / 67.3 | 85.7 / 64.0 | **0.953** |
| G | 105.9 / 56.4 | 81.8 / 44.7 | **0.957** |
| B | 74.4 / 54.8 | 54.3 / 37.6 | **0.963** |

Same regime: uint8 with full dynamic range, sub-5 % saturation at 255, near-zero at 0, identical
product structure (10 m RGB COG). **Consistent with the corpus being L2A TCI, as assumed** — the
release itself carries no product metadata, so this indirect check is the strongest verification
available. Ankara is brighter overall (steppe/bare soil vs green Europe) and its GLI greenness
(+0.069) sits below the corpus median (+0.119) but inside the corpus per-zone range (0.004–0.175).
End-April is close to the Anatolian steppe's green peak; no better month exists for this match.

## 4. Chip grid and screening (2026-08-19)

Grid: 42×42 = **1764 candidates** (257×257 px @ 10 m, EPSG:32636, anchored at the granule NW
corner; 186 px margins east/south unused). Screening uses the scene's own **SCL band** — a
TCI-only brightness proxy was rejected after visual calibration showed it flagging cloud-free
bright steppe, roofs and limestone (653/1764 against a 2.04 % scene). SCL agrees with the scene
metadata (2.53 % cloud+shadow+cirrus vs 2.04 %).

| screen | chips |
|---|---|
| SCL cloud/shadow/cirrus > 1 % | 180 |
| snow > 2 % (April, NE mountains) | 38 |
| dark-pixel clusters > 0.5 % | 0 (the granule is complete; earlier "nodata" flags were dark surface) |
| **VALID** | **1564** |

## 5. OSM-only information scores and the provisional stratified selection

**Proxy validation first** (55 corpus chips, full reference raster vs OSM-only render of the same
footprint): Spearman rho — edge density **0.757**, non-dominant fraction 0.618, class count
**0.315 (unusable — the base layer supplies the class variety; dropped)**. Stratum stability by
edge-density quintile: **55 % exact, 89 % within ±1**, 6/55 move ≥2. Verdict: usable for a
provisional ranking; final scores wait for CLC+.

**Ankara distribution** (all 1564 valid candidates, OSM-only renders from the fixed
turkey-260818 snapshot): median edge density **0.072** vs corpus full-raster median 0.259 —
Turkish OSM is far sparser than the rendered European references, and **16 % of chips are
near-empty (< 0.02)**. p90 = 0.326, max 0.965 (central Ankara).

**Proposed selection** — `proposed_selection.csv`, 130 chips, 26 per edge-density quintile,
seed 42, **PROPOSAL ONLY**:

| stratum | edge range | pool | selected | median GLI | bright-chip share |
|---|---|---|---|---|---|
| Q1 | 0.000–0.025 | 313 | 26 | +0.071 | 42 % |
| Q2 | 0.025–0.052 | 313 | 26 | +0.083 | 31 % |
| Q3 | 0.052–0.090 | 312 | 26 | +0.064 | 31 % |
| Q4 | 0.090–0.167 | 313 | 26 | +0.080 | 31 % |
| Q5 | 0.168–0.965 | 313 | 26 | +0.063 | 65 % |

When CLC+ Backbone arrives: re-render the 1564 candidates with the real base layer, recompute the
scores, re-stratify, and report how far the proxy selection moved — that displacement is itself a
result (it measures how much the base layer reorders Turkish chips).
