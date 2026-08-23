# GenCP synthetic reference — ODTÜ campus and surroundings

A synthetic 10 m reference image generated from OpenStreetMap + CLC+ land cover, for use as
reference data in georeferencing software (e.g. GeoRef). **Read the accuracy section before
using it: for this area, a real Sentinel-2 scene is the better reference.** This package is
supplied so you can evaluate the synthetic option against the alternatives yourself.

## What is in this package

| file | what it is |
|---|---|
| `ODTU_gencp_reference_10m.tif` | the reference image. 771 × 771 px, 3-band RGB, 8-bit |
| `ODTU_reliability.tif` | per-tile reliability score, same grid, 1-band float |
| `ODTU_reliability.csv` | the same scores as a ranked table (best tile first) |
| `PROVENANCE.txt` | exactly how this file was produced (also embedded in the GeoTIFF tags) |

## Coordinate system and pixel size — please read

- **CRS: EPSG:32636** (WGS 84 / UTM zone 36N).
- **Extent:** E 477593 – 485303, N 4411827 – 4419537 (7.71 × 7.71 km).
- **The mosaic is written on a 10.0 m grid.** But the underlying network produces 256 × 256
  px tiles whose true ground coverage is 2570 m, i.e. **10.0390625 m/px** (= 257 × 10 / 256).
  The original GenCP pipeline wrote 10.0 m into the file while the content covered 2570 m —
  a +0.39 % scale error reaching **14.1 m at the far corner of each tile**. We found and
  corrected this; each tile is placed using 10.0390625 m before being resampled onto the
  regular 10 m output grid. **You do not need to apply any correction.** The number is given
  so that, if you compare against the original GenCP outputs, you know why they differ.

## How accurate is it — the one number

**Against a real Sentinel-2 image, the median matching residual is ≈ 0.59 px (≈ 5.9 m)** on
built-up areas — measured on 20 urban chips, production path, 8-draw average
(0.593 ± 0.041 px). Over all terrain types the median is ≈ 0.93 px (≈ 9.3 m).

Measured directly on **this file**: 0.656 px median over 3,017 matched points against the
real 2026-04-30 Sentinel-2 scene (0.468 px in the single-band/panchromatic-equivalent test).
That number is flattering and we say so: part of this area was in the model's fine-tuning
data, so treat the 0.59 px urban figure above — measured on chips that were not — as the
representative one.

**Honest comparison, measured by us on independent sites.** In a known-shift recovery test —
distort a real image by a known amount, see which reference recovers it — a **real Sentinel-2
scene from a different date recovered a 1 px shift to within 0.03 px, and this synthetic
reference to within 0.54 px.** Free EOX cloudless and standard basemaps performed like the
real Sentinel-2.

We then tested the two reasons you might still prefer a synthetic reference, and **neither
held up**:

- *Availability.* Across 24 stratified extents in Turkey, there was **no** case without a
  cloud-free Sentinel-2 scene: the median extent had one from **2 days** earlier, the worst
  from 17 days. The free EOX cloudless mosaic covered **every** extent.
- *Currency.* At a rapidly developing area of Istanbul, a **five-year-old** Sentinel-2 image
  still registered a 2026 target better than this synthetic reference — including in the
  tiles that had changed the most.

**Our recommendation is therefore to use real imagery wherever it exists for your area, which
in Turkey appears to be essentially everywhere.** This synthetic reference is worth using when
imagery genuinely is not available to you, when licensing prevents using what exists, or when
you specifically want to match against *mapped features* rather than observed ground.

If you are georeferencing 0.5–1 m imagery, note that **any** 10 m reference — ours, Sentinel-2,
or EOX — leaves metre-scale residuals, because the reference's resolution sets the limit.
Choose on availability, not on the source's identity.

**Known cosmetic artefact:** 5 pixels in the extreme north-west corner (rows 0–2, cols 0–2)
are nodata (value 0) — an edge effect of resampling the outermost tile onto the output grid.
That is 0.0008 % of the image and is not near any content; it is stated here so it does not
look like data corruption if your software flags it.

## The reliability layer and how to mask with it

`ODTU_reliability.csv` ranks the 16 generation tiles by a score computed **only from the input
map data** — road/building density, class-boundary length, and a penalty for forest and open
water (the classes you mentioned wanting to mask). Higher = more trustworthy.

Measured effect: **keeping the best-ranked 75 % of tiles and discarding the rest improves the
median residual by 0.21 px (Ankara) and 0.42 px (Cappadocia)**. Recommended use: sort by
`score`, drop the lowest-ranked tiles for the coverage you can afford to lose. Do **not** use
a fixed numeric cut-off — a threshold tuned on one area does not transfer to another (we
measured this failing). Use the ranking.

## Licence and attribution

| component | licence | attribution required |
|---|---|---|
| GenCP model weights (base) | CC-BY 4.0 | GenCP / Telespazio, ESA-supported |
| OpenStreetMap data | ODbL 1.0 | © OpenStreetMap contributors |
| CLC+ Backbone 2021 | Copernicus | © European Union, Copernicus Land Monitoring Service |
| Sentinel-2 (validation only) | Copernicus open | Contains modified Copernicus Sentinel data 2026 |

This output is a derived product of ODbL-licensed OpenStreetMap data. It is supplied to you
for internal evaluation and use. **Public redistribution needs a separate licence decision**
we have not made: whether ODbL's share-alike obligation extends to imagery generated from
ODbL-derived renders is unsettled.

## Reproducing this file

Every parameter is in `PROVENANCE.txt` and in the GeoTIFF tags (`GENCP_*`): tool version, model
arm and checkpoint SHA-256, random seed, inference path, OSM snapshot, CLC+ version, repo
commit, tile count, overlap, and the measured seam ratio. The same command with the same
inputs reproduces the file byte-for-byte.

---
*This is the recipient-facing README shipped inside the ODTÜ package. The package itself
(`tubitak/outputs/odtu_package/`: reference GeoTIFF, reliability tif+csv, provenance, visual)
is deliberately outside version control — `tubitak/outputs/` is gitignored, and the artifacts
are reproducible byte-for-byte from the provenance record.*
