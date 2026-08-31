# WP10 — what the EOX product is, and a first super-resolution pass

> **Numbering.** `11-zamanlama.md`, `12-…` and `13-…` were written for later-commissioned
> work while this package was outstanding. This document keeps the name the brief asked for.

## 1. How the sample was obtained

**The sample link in the brief is dead.** The share token `jvu06wnt` on host
`cloudlessdownloads.eox.at` (path `/share/`) returns **HTTP 404**, as does the host root. The documentation page describing it renders, and
names three sample formats (STACTA TileDirectory, GeoPackage, SQLite mapcache) — but the share
token no longer resolves. Nothing was downloaded from it.

**What was used instead: EOX's public WMTS**, which serves the same Viewing product and is
live. This is reproducible:

```
capabilities  https://tiles.maps.eox.at/wmts/1.0.0/WMTSCapabilities.xml
layer         s2cloudless-2024_3857     (also 2017–2025, and EPSG:4326 variants)
matrix set    GoogleMapsCompatible, urn:ogc:def:crs:EPSG:6.3:3857, 22 levels
tile (REST)   host  tiles.maps.eox.at
              path  /wmts/1.0.0/s2cloudless-2024_3857/default/GoogleMapsCompatible/
                    {TileMatrix}/{TileRow}/{TileCol}.jpg
              (written as host + path template: it is a pattern, not a link, and the
               link checker cannot tell one from the other)
```

A GeoTIFF is obtained by fetching tiles and georeferencing them. Matrix 14 is 16384 × 16384
tiles of 256 px at **9.5546 m/px** in EPSG:3857 (`ScaleDenominator` 34123.673, top-left corner
−20037508.342789, 20037508.342789), which is the closest level to Sentinel-2's 10 m.

For a like-for-like comparison the footprint chosen was **the exact chip used in WP10/WP11**:
granule 36SXJ, `Window(5000, 5000, 256, 256)`, EPSG:32636 bounds
`(650000.0, 4347480.0, 652560.0, 4350040.0)`, 2560 × 2560 m near 34.75 °E, 39.27 °N. That
needed **9 tiles** (cols 9772–9774, rows 6244–6246), fetched in **2.0 s**, assembled into a
768 × 768 EPSG:3857 mosaic and reprojected onto the Sentinel-2 grid at 10 m.

Artefacts (all under gitignored `tubitak/data/eox/`): `eox_s2cloudless2024_z14_3857.tif`,
`eox_s2cloudless2024_36SXJ_chip_10m.tif`, `eox_bicubic_x2.tif`, `eox_comparison.png`.

**Opening the WMTS through GDAL's driver directly and warping was abandoned**: GDAL exposes
the pyramid down to 0.0746 m/px and drove an enormous number of tile requests. Computing the
tiles explicitly took 2 seconds.

## 2. Measured characterisation

From the pixels, not the prose. Percentiles use WP2A's convention.

| | measured |
|---|---|
| bands | **3**, RGB, in that order |
| dtype | **uint8** |
| served as | **`image/jpeg`** — lossy, chroma-subsampled |
| CRS (as served) | EPSG:3857; reprojected here to EPSG:32636 |
| pixel size | 9.5546 m at matrix 14 (10.0 m after reprojection) |
| nodata | **none declared** |
| extent used | 650000, 4347480 → 652560, 4350040 (EPSG:32636) |

| band | min | p1 | p50 | p99.9 | max |
|---|---|---|---|---|---|
| R | 29 | 98 | **155** | 253 | 255 |
| G | 38 | 72 | **122** | 223 | 251 |
| B | 8 | 43 | **85** | 177 | 208 |

For the same ground, our Sentinel-2 L2A reflectance (2026-05-27) has p50 **0.140 / 0.115 /
0.080** for B04/B03/B02, and Sentinel-2's own TCI has p50 **143 / 118 / 82**.

## 3. Linear, or a rendered composite? — **rendered, and the vendor says so**

### 3.1 What the documentation states

EOX splits the catalogue in two, and the distinction is exactly this question
(`/documentation/product-list`):

| product line | bands | bit depth | radiometry |
|---|---|---|---|
| **Viewing Basic** | RGB | 8-bit | **Tonemapped** |
| **Viewing Ready** | RGB | 8-bit (sRGB), **JPEG lossy** | **Tonemapped** |
| **Exploitation Starter** | B04, B03, B02, **B08** | **uint8, 8-bit scaled reflectance, 0–1000 → 0–255** | linear |
| **Exploitation Ready** | B04, B03, B02, **B08** | **uint16, 12-bit surface reflectance** | linear, atmospherically corrected |

Their own footnote defines the term: *"Tonemapped here means that the visible rendered bands
are scaled to 0-255, color corrected and contrast adjusted (and even sharpened)."*

**"And even sharpened" is the sentence that matters most to this project.** A super-resolution
model applied to a Viewing product operates on imagery that has already had an undisclosed
sharpening kernel applied.

**Mustafa Teke's "8 or 16 bit, normalisation applied upstream" maps exactly onto the two
Exploitation tiers** — Starter is the 8-bit 0–1000→0–255 scaling, Ready is the 16-bit
reflectance. So which product the institute receives decides everything below.

### 3.2 What the pixels show

**The public WMTS serves a Viewing product**, and the measurement is consistent with
tonemapping: a linear reflectance-to-8-bit map of the kind Sentinel-2 TCI uses would put this
scene's medians near 102 / 84 / 58; EOX's are **155 / 122 / 85**, markedly brighter and
mid-tone weighted. It is also delivered as JPEG, which alone disqualifies it as a linear
carrier of reflectance.

### 3.3 What could NOT be settled this way, and why

**A per-pixel regression of EOX against our reflectance is meaningless here, and the number
proves it rather than hiding it.** Fitted on all 65 536 pixels, EOX against B04/B03/B02:

| pairing | linear R² | power-law R² | fitted gamma |
|---|---|---|---|
| B04 → R | **0.051** | 0.104 | −0.085 |
| B03 → G | **0.000** | 0.002 | −0.057 |
| B02 → B | 0.005 | −0.013 | −0.028 |

R² ≈ 0 is not evidence of a stretch; it is evidence that **the two images are not of the same
moment**. `s2cloudless-2024` is an annual cloud-free composite; our scene is 2026-05-27. A
shift search over ±24 px found no offset that improves the correlation (best 0.0, r = −0.086),
and the rendered comparison shows **identical field boundaries, roads and village geometry** —
the same ground with opposite phenology, bare brown soil against green crop. Fields that are
darkest in one are brightest in the other, so the correlation is genuinely near zero.

**What would settle linearity by measurement:** an EOX **Exploitation** tile over ground for
which we hold Sentinel-2 L2A of the **same date range**, regressed band by band. The
Exploitation products are behind the sample portal that is 404, and behind a paid licence for
commercial use.

### 3.4 A correction to this project's own prose, found while doing this

`02a-reflectance-corpus.md:9` describes Sentinel-2 TCI as *"an 8-bit, gamma-stretched RGB
visual composite"*. **Measured on this chip, TCI is linear, not gamma-stretched**: against
reflectance it fits with **R² 0.9968 / 0.9991 / 0.9982** and a fitted exponent of **0.989 /
0.994 / 0.982** — indistinguishable from 1.0. TCI is a linear scaling with clipping. The
corpus is unaffected; the wording is wrong and is corrected here.

## 4. What a cloudless mosaic implies that a single scene does not

- **Composed from many dates.** Each pixel is selected from a time series, so a scene has no
  single acquisition date and no single sun geometry. EOX applies **BRDF normalisation** to
  a standard geometry (nadir view, 45° solar zenith) with MODIS MCD43 kernel weights, which is
  a further departure from any one observation.
- **Seams are possible** wherever neighbouring pixels come from different dates. None was
  visible in this 2560 m chip; that is one chip and is not a survey.
- **Per-pixel acquisition dates are not exposed** in the WMTS product. The layer name carries
  the year and nothing finer. So a matching experiment of the kind in `08-eslestirme.md`
  cannot pair an EOX pixel with a dated reference.
- **Consequence for us:** the phenology mismatch in §3.3 is not an accident of this chip. Any
  comparison between an EOX mosaic and a dated Sentinel-2 scene inherits it.

## 5. Which of our upsamplers are in domain

The models' own `metadata_props` are the criteria, not preference.

| upsampler | declares | EOX Viewing (measured) | verdict |
|---|---|---|---|
| **bicubic** | nothing; parameter-free | any raster | **IN DOMAIN.** Always valid |
| **ours x2** | 3 bands `B02,B03,B04`; `DN/5000`; uint16 DN | 3 bands **R,G,B**; uint8 0–255; tonemapped | **OUT.** Band order reversed, normalisation absent, radiometry rendered |
| **ours x4** | 4 bands `B02,B03,B04,B08`; `DN/10000` | 3 bands, no NIR | **OUT.** Band count wrong |
| **wsx4** | 4 bands B2,B3,B4,B8; DN in, DN out | 3 bands, no NIR | **OUT.** Band count wrong |

**Only bicubic is in domain.** Note the band-order fault in the x2 row is independent of the
radiometry one: EOX serves **R,G,B**, our model declares **B02,B03,B04** — blue, green, red.
Feeding one to the other reverses the channels even before the normalisation is wrong.

## 6. The bicubic result

CLI, `sr_core.run.superresolve(scale=2, method="bicubic")`. **0.04 s** for 256 → 512.

| Gate S assertion | result |
|---|---|
| out CRS == src CRS | **True** (EPSG:32636) |
| out pixel == src / scale exactly | **True** (10.0 → 5.0) |
| out origin == src origin exactly | **True** |
| out size == scale × src exactly | **True** (256² → 512²) |
| no clipped / no uncovered values | **76 clipped**, 0 uncovered |

Extent unchanged at `650000, 4347480 → 652560, 4350040`; 2560 × 2560 m at 5.0 m/px.

**The 76 clipped values are the first concrete cost of an 8-bit input.** Bicubic overshoots at
sharp edges, and with the input already at 255 there is no headroom, so 76 of 786 432 output
values (0.0097 %) were clamped. On a 16-bit reflectance product they would not have been.

## 7. What the out-of-domain models did — the finding of this package

| model | what happened |
|---|---|
| **ours x4** | **Refused before running.** Needs 4 bands, got 3. No output |
| **wsx4** | **Refused before running.** Needs 4 bands, got 3. No output |
| **ours x2** | **It ran.** And it produced a plausible image |

The x2 model saw its input as **0.00160 – 0.05100** normalised, against training data whose
median was about **0.28** — roughly five times darker than anything it was trained on, with
the channels reversed. It emitted output of standard deviation **40.8** against the input's
**40.2**: structurally sensible, radiometrically meaningless.

`eox_comparison.png` — left EOX input (nearest ×2, **no stretch**, 0–255 as served), middle
bicubic ×2 (**no stretch**), right the x2 model (**linear 0.2 – 277.9 → 0 – 255**, its own
full range). **The right panel looks the sharpest of the three.** It is the one that is wrong.
The stretch that makes it presentable is stated precisely because without it the panel would
be near-black, and with it nobody could tell.

> **Two of the three models refused loudly and one failed silently. The silent one is the
> only one that produced a picture, and the picture is the most convincing of the three.**

## 8. Licence and attribution — and a correction to the brief

The brief says EOX Cloudless is "a public Sentinel-2 derived product". **It is Sentinel-2
derived and publicly documented, but it is not open data.** From
`https://cloudless.eox.at/documentation/license`:

- **Attribution is required for all uses**, in these words:
  > `EOxCloudless https://cloudless.eox.at by EOX IT Services GmbH (Contains modified Copernicus Sentinel data "year")`
  and it "must be clearly visible wherever the imagery is displayed".
- **Non-commercial use** is free under **CC BY-NC-SA 4.0**, explicitly including academic
  research and university projects.
- **Commercial use requires** an **EOX Commercial Attribution-RestrictedUse 1.2 License**,
  purchased from EOX.
- **Sub-licensing and resale are not permitted** by default; the imagery may not be sold or
  licensed as a standalone product without modification.
- You must not imply endorsement by the European Commission or ESA.

**Practical consequence.** Research use is permitted with attribution. But **ShareAlike and
NonCommercial attach to derivatives**, so a model trained on EOX imagery, or outputs
distributed from it, inherit obligations that our Sentinel-2-derived work does not. Sample
rasters may be downloaded and worked on, and live under gitignored `tubitak/data/` like
everything else.

## 9. Is a TCI-trained model the right next step? — **Yes, if the product is a Viewing one**

**The condition holds for what was measured.** The public product is 8-bit, three-band, RGB,
tonemapped — the same *kind* of thing as Sentinel-2 TCI, which is 8-bit three-band RGB on the
same 10 m grid. None of our four upsamplers except bicubic can touch it, and the reason is not
fixable by rescaling: no reflectance normalisation exists for a tonemapped product.

**Two honest qualifications.**

1. **It is the same kind, not the same thing.** TCI is a *linear* scaling of reflectance
   (§3.4, R² ≈ 0.998). EOX Viewing is *tonemapped* — colour corrected, contrast adjusted and
   **sharpened**. A TCI-trained model would be much closer to in-domain than anything we hold,
   but it would still be trained on a linear product and applied to a non-linear one. It is
   the right next step, not a finished answer.
2. **If the institute receives an Exploitation product instead**, this conclusion inverts: the
   16-bit Exploitation Ready tier is B04,B03,B02,**B08** surface reflectance at 10 m, which is
   what our **x4 four-band model was trained on**, and it would be in domain or close to it.
   **Establishing which tier the institute has is worth more than any training run**, and the
   diagnostic is one question to Fatih Gültekin.

### Cost, given that the corpus screening already exists

The 6990 distinct cloud-free chips are an *indexing* result shared by both corpora; the TCI
**chip arrays** are not cut yet, but the four TCI granules are on disk (`tiles36SVJ`,
`tiles36SWJ`, `tiles36SXJ`, `tiles36TUK`, 232–346 MB each, 3-band uint8, 10980², EPSG:32636)
and the reflectance corpus's manifest indexes the same footprints.

| step | estimate | basis |
|---|---|---|
| cut TCI chips with the existing manifest | **10–20 min** | one 3-band file per granule; cheaper than the reflectance cut, which read three separate band files |
| train 20 000 steps, scale 2, 3 bands | **~75 min** | WP3B measured 4.46 steps/s uncontended at this configuration; `11-zamanlama.md` warns that is a burst rate, so treat as a floor |
| evaluate, both test sets, dual path | **~2 min** | WP7 measured 110 s |
| export ONNX + checks | **~1 min** | WP7 |
| **total compute** | **≈ 1.5–2 hours** | plus writing the registration first |

**Not started, as instructed.**

## 10. Open items

1. **The sample portal is 404.** The Exploitation products could not be measured at all. Every
   statement here about them comes from EOX's product list, not from pixels.
2. **Linearity of the Exploitation tiers is unverified by measurement** (§3.3 names the test).
3. **Which tier the institute will receive is unknown** and decides the next work package (§9).
4. **Seams and per-pixel dates were not surveyed** — one chip, no seam seen, dates not exposed.
5. **The tonemap's sharpening is undisclosed and unmeasured.** Super-resolving an
   already-sharpened product is a different problem from super-resolving a linear one.
