# WP2A — Reflectance corpus acquisition

Project 2, Work Package 2A. Acquisition and measurement only: no training, no model code, no
chip cutting, no normalisation decision.

**Date of work:** 2026-08-30. **Branch:** `tubitak-tr`. **Repository:** `mvy0502/GenCP`.

**Purpose.** The five Sentinel-2 scenes inventoried in [`00-recon.md`](00-recon.md) are TCI —
an 8-bit, gamma-stretched RGB visual composite. The SR model will be applied to real
Sentinel-2 imagery and so must be trained on sensor reflectance. This package acquires the
reflectance bands for exactly the same five granules and the same acquisition dates, so that
the reflectance corpus and the TCI corpus cover the same ground and differ in one variable
only.

**Headline results.**

| question | answer |
|---|---|
| All five granules arrived complete? | **Yes.** 20/20 assets, 3,303,042,660 bytes, zero retries, zero failures, every checksum matched. |
| Reflectance 10 m grid identical to the TCI grid? | **Yes**, all five granules, all three bands — same CRS, same affine, same dimensions. WP0 chip indexing transfers directly. |
| Product IDs for the four "not determined" granules? | **Resolved, and proved byte-identical to what is on disk.** Risk R4 of `00-recon.md` is closed. |
| Chip recount | **7593 raw / 6990 distinct**, identical to WP0 — and identical *by construction*, see §5. |
| Single number WP3 most needs | **p99.9 of clear-pixel DN, pooled: 4084 (B02), 4663 (B03), 5029 (B04)** — against a maximum of 20703. See §6 and the offset contradiction in §7. |

---

## 1. The five products

Queried Element84 Earth Search v1 (`https://earth-search.aws.element84.com/v1/search`), one
POST per tile per collection, filtered by `grid:code = MGRS-<tile>` and a one-day `datetime`
window on the acquisition date recorded in `00-recon.md`.

**Every date returned exactly one L2A candidate.** No date was ambiguous, so no arbitration
was needed and none was made silently. Earth Search served L2A for all five dates; the
Copernicus Data Space Ecosystem alternative was not needed and was not used.

Each product is served by Earth Search under **two collections** —
`sentinel-2-l2a` and `sentinel-2-c1-l2a` — which are two STAC views of *the same underlying
SAFE product* (identical `s2:product_uri`, identical `datetime`, identical cloud cover). This
is not two candidate products; it is one product with two item IDs. **`sentinel-2-l2a` was
used**, because that is the collection the Ankara product ID already recorded in
`tubitak/docs/data-sources.md:20` (`S2C_36TVK_20260430_0_L2A`) comes from. The alternate item
ID is recorded below so the record is not silent about it.

| tile | product ID (`s2:product_uri`) | STAC item ID (`sentinel-2-l2a`) | alternate item ID (`sentinel-2-c1-l2a`) |
|---|---|---|---|
| 36TVK | `S2C_MSIL2A_20260430T083651_N0512_R064_T36TVK_20260430T140714.SAFE` | `S2C_36TVK_20260430_0_L2A` | `S2C_T36TVK_20260430T084301_L2A` |
| 36TUK | `S2C_MSIL2A_20260430T083651_N0512_R064_T36TUK_20260430T140714.SAFE` | `S2C_36TUK_20260430_0_L2A` | `S2C_T36TUK_20260430T084301_L2A` |
| 36SVJ | `S2C_MSIL2A_20260430T083651_N0512_R064_T36SVJ_20260430T140714.SAFE` | `S2C_36SVJ_20260430_0_L2A` | `S2C_T36SVJ_20260430T084301_L2A` |
| 36SWJ | `S2C_MSIL2A_20260430T083651_N0512_R064_T36SWJ_20260430T140714.SAFE` | `S2C_36SWJ_20260430_0_L2A` | `S2C_T36SWJ_20260430T084301_L2A` |
| 36SXJ | `S2C_MSIL2A_20260527T082601_N0512_R021_T36SXJ_20260527T135213.SAFE` | `S2C_36SXJ_20260527_0_L2A` | `S2C_T36SXJ_20260527T083324_L2A` |

| tile | granule / tile ID | acquisition datetime (UTC) | baseline | platform | orbit | cloud cover (API) | nodata % | snow/ice % |
|---|---|---|---|---|---|---|---|---|
| 36TVK | `S2C_OPER_MSI_L2A_TL_2CPS_20260430T140714_A008614_T36TVK_N05.12` | 2026-04-30T08:49:07.064Z | 05.12 | sentinel-2c | R064 | 2.040338 % | 0.0000 | 0.5255 |
| 36TUK | `S2C_OPER_MSI_L2A_TL_2CPS_20260430T140714_A008614_T36TUK_N05.12` | 2026-04-30T08:49:10.810Z | 05.12 | sentinel-2c | R064 | 2.472755 % | 5.7086 | 0.5684 |
| 36SVJ | `S2C_OPER_MSI_L2A_TL_2CPS_20260430T140714_A008614_T36SVJ_N05.12` | 2026-04-30T08:49:21.471Z | 05.12 | sentinel-2c | R064 | 0.001908 % | 0.0000 | 0.0006 |
| 36SWJ | `S2C_OPER_MSI_L2A_TL_2CPS_20260430T140714_A008614_T36SWJ_N05.12` | 2026-04-30T08:49:17.275Z | 05.12 | sentinel-2c | R064 | 1.192487 % | 25.4153 | 1.5163 |
| 36SXJ | `S2C_OPER_MSI_L2A_TL_2CPS_20260527T135213_A009000_T36SXJ_N05.12` | 2026-05-27T08:39:14.264Z | 05.12 | sentinel-2c | R021 | 0.201565 % | 0.0000 | 0.0030 |

All five are `sentinel-2c` — resolving the platform question `00-recon.md` left open. The
four April granules share one datatake (`A008614`, orbit R064, 14 seconds apart across the
five-granule strip); 36SXJ is a separate May datatake on orbit R021.

### 1.1 Cloud cover agrees with the record

The API cloud cover reproduces the figures `00-recon.md` recovered from project documentation,
which were recorded at acquisition time and had never been re-checked against the source:

| tile | `00-recon.md` (from project docs) | Earth Search API (this work) | agree |
|---|---|---|---|
| 36TVK | 2.04 % | 2.040338 % | yes |
| 36TUK | 2.5 % | 2.472755 % | yes |
| 36SVJ | 0.0 % | 0.001908 % | yes |
| 36SWJ | 1.19 % | 1.192487 % | yes |
| 36SXJ | 0.20 % | 0.201565 % | yes |

### 1.2 Risk R4 is closed, with byte-level proof

`00-recon.md` §2.2 and risk R4 recorded that the four expansion granules (36TUK, 36SVJ,
36SWJ, 36SXJ) "cannot be re-fetched byte-identically from the record as it stands" — no
product ID, no platform, no md5, no download script.

Matching cloud percentages (§1.1) would only be *consistent* with these being the right
products. Two stronger checks were run, and both are byte-level:

**Check 1 — the SCL files already on disk are byte-identical to the SCL assets of these five
STAC items.** Local md5 of the newly downloaded SCL versus local md5 of the pre-existing
file, both computed here with `hashlib`:

| tile | new SCL md5 | on-disk SCL md5 | identical | bytes (both) |
|---|---|---|---|---|
| 36TVK | `e6706fd2d8cec2e737678e3cba2480d9` | `e6706fd2d8cec2e737678e3cba2480d9` | **YES** | 4,710,392 |
| 36TUK | `8e9ee579dc22e7fda2d1076c598c63ff` | `8e9ee579dc22e7fda2d1076c598c63ff` | **YES** | 4,320,024 |
| 36SVJ | `202eaf9efb53ad0404f2f51aec2cb893` | `202eaf9efb53ad0404f2f51aec2cb893` | **YES** | 3,794,300 |
| 36SWJ | `d9e7c19b18fdb2830ab8165b31e3d530` | `d9e7c19b18fdb2830ab8165b31e3d530` | **YES** | 2,784,869 |
| 36SXJ | `47cb7af7da6962cdd253841b86a2dad5` | `47cb7af7da6962cdd253841b86a2dad5` | **YES** | 4,133,443 |

**Check 2 — the TCI files already on disk are byte-identical to the `visual` assets of these
same five items.** The `visual` asset was not downloaded (§2 — it is not in scope). Instead
its S3 multipart ETag was read from the API and *recomputed locally* from the file already on
disk, using the 8 MiB part size inferred from the part count:

| tile | on-disk TCI, locally recomputed S3 ETag | API ETag of the item's `visual` asset | match | on-disk TCI whole-file md5 |
|---|---|---|---|---|
| 36TVK | `6ded197c20c6792765561bc917000dbc-43` | `6ded197c20c6792765561bc917000dbc-43` | **YES** | `b163f09ceb6ff435846ea61a20b8b7b0` |
| 36TUK | `3c35a41d1fe42c292047caebdb018fe6-41` | `3c35a41d1fe42c292047caebdb018fe6-41` | **YES** | `df14a13fa888c92ab112665b3917ea41` |
| 36SVJ | `a5e4868047bdb02d3b911c7e1a4a6c8e-43` | `a5e4868047bdb02d3b911c7e1a4a6c8e-43` | **YES** | `64b82b7b48a6f03e0c33535995a3762b` |
| 36SWJ | `5e1bf51af1ffef37b0ad43bbf58c4299-30` | `5e1bf51af1ffef37b0ad43bbf58c4299-30` | **YES** | `c991f76dfb735558b7e80d0836710b27` |
| 36SXJ | `60f67792380621a2b95ee20ac5c22e63-44` | `60f67792380621a2b95ee20ac5c22e63-44` | **YES** | `d3c3bd876694db42a0025ea95b813018` |

**Inference path, stated.** The API ETag is computed by S3 over the object as stored in
`sentinel-cogs`. The local ETag is computed here from the bytes on disk by the same
algorithm (md5 per 8 MiB part, then md5 of the concatenated part digests, then `-<n>`). A
match of a 128-bit digest over 350 MB is not a coincidence. **The five product IDs in §1 are
therefore not a plausible reconstruction; they are the demonstrated source of every TCI and
SCL file in `tubitak/data/`.** R4 is closed, and the whole-file md5 column above is the
missing checksum the record needed for the four expansion granules.

---

## 2. What was downloaded, and what was not

**Downloaded:** B02, B03, B04 (10 m reflectance) and SCL (20 m) — 4 assets × 5 granules = 20
files.

**Not downloaded, deliberately:** B08 (NIR 10 m), the 20 m spectral bands (B05, B06, B07,
B8A, B11, B12), the 60 m bands (B01, B09), AOT, WVP, the `cloud`/`snow` probability rasters,
`visual` (TCI — already on disk and unchanged), the JP2 variants of every asset, the
thumbnail, and the granule/product/tileinfo metadata assets. The Wald protocol builds its
20 m input by degrading real 10 m, so real 20 m spectral bands would not be used; holding the
channel count at three keeps this corpus comparable with the TCI corpus.

**Location.** `tubitak/data/s2_reflectance_l2a/<TILE>_<YYYYMMDD>/{B02,B03,B04,SCL}.tif` —
gitignored, and named so the distinction from the TCI corpus (`tubitak/data/ankara/`,
`tubitak/data/tiles36*/`) is obvious at a glance. **No TCI scene was deleted, moved or
modified.**

**Atomicity.** Each transfer streamed to `.<band>.tif.part` in the destination directory,
was `fsync`ed, had its byte count checked against the API `Content-Length`, and only then was
`os.replace`d onto its final name. An interrupted transfer leaves a dotfile that no reader
will mistake for a complete band. Zero `.part` files remain.

**Transfers.** 20 of 20 succeeded on the first attempt. **Zero retries, zero failures.**
Wall time for the transfers was 4 minutes 45 seconds (sum of per-file times: 285.2 s;
slowest single file 33.9 s). The whole work package — STAC query through final measurement —
ran well inside the 60-minute box, so no interim progress report was due.

| tile | band | bytes | local md5 (computed here from the bytes on disk) | seconds |
|---|---|---|---|---|
| 36TVK | B02 | 230,199,685 | `8d66a68ac00848caa1b6016941d3d8ec` | 16.8 |
| 36TVK | B03 | 233,373,867 | `a9e429b0e29b47e2a2e409c6051039d2` | 16.2 |
| 36TVK | B04 | 239,373,725 | `1f8760a6ae7bdc20a46ade27d2abf3a5` | 17.4 |
| 36TVK | SCL | 4,710,392 | `e6706fd2d8cec2e737678e3cba2480d9` | 2.4 |
| 36TUK | B02 | 217,655,063 | `dd1cde22c7b546d313c88367ae773bad` | 16.1 |
| 36TUK | B03 | 221,496,078 | `23e14a5951950b2af2824068f21ab398` | 16.6 |
| 36TUK | B04 | 225,691,619 | `ed5c92911e98dcee8f86e56f4d5b40e9` | 16.3 |
| 36TUK | SCL | 4,320,024 | `8e9ee579dc22e7fda2d1076c598c63ff` | 2.4 |
| 36SVJ | B02 | 229,856,354 | `ebe66d1d00bee5551867fd45d76c18cb` | 14.6 |
| 36SVJ | B03 | 233,694,818 | `c483c9091e647b6c7594cf99abaa73c7` | 17.2 |
| 36SVJ | B04 | 240,226,172 | `e02ea84b5715e1f47bbefc206740e0b1` | 16.8 |
| 36SVJ | SCL | 3,794,300 | `202eaf9efb53ad0404f2f51aec2cb893` | 2.4 |
| 36SWJ | B02 | 164,315,443 | `aa05209bd66ab747b520ffa08d9419b1` | 12.5 |
| 36SWJ | B03 | 168,154,464 | `669a26f972452df9587fa539adf59f28` | 29.8 |
| 36SWJ | B04 | 173,379,335 | `1e87cfad36842302eac68aa6fe8c1712` | 13.6 |
| 36SWJ | SCL | 2,784,869 | `d9e7c19b18fdb2830ab8165b31e3d530` | 2.8 |
| 36SXJ | B02 | 229,844,125 | `0ac526752f6a8b09969652476200c18f` | 33.9 |
| 36SXJ | B03 | 234,434,749 | `08a31a6ece1105d08676f1f5a90a4d01` | 17.2 |
| 36SXJ | B04 | 241,604,135 | `563a30ef7f6c6131b19acc44a7b6dd56` | 17.8 |
| 36SXJ | SCL | 4,133,443 | `47cb7af7da6962cdd253841b86a2dad5` | 2.4 |

**Total: 3,303,042,660 bytes = 3.303 GB** (3.2 GiB on disk; per granule 696 / 664 / 695 /
502 / 695 MiB for 36TVK / 36TUK / 36SVJ / 36SWJ / 36SXJ).

This is **roughly half the ≈ 6 GB that `00-recon.md` §4 estimated**, because that estimate
covered ten bands (B02, B03, B04, B08 at 10 m plus six 20 m bands) and this package took
three 10 m bands plus SCL. Per 10 m band the estimate of ~241 MB raw compressing to ~1.2 GB
per granule for ten bands implied ~120 MB per band; the observed 10 m bands are 164–242 MB,
so the true per-band size is larger than that estimate, and the smaller total here is
entirely due to the smaller band list.

### 2.1 Source and licence

`https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/36/<band>/<square>/<year>/<month>/<item-id>/<BAND>.tif`,
the public `sentinel-cogs` bucket indexed by Element84 Earth Search — the same route already
documented for Ankara at `tubitak/docs/ankara-acquisition.md:36`. No registration, no
credentials, no quota. Copernicus Sentinel-2, public. **No institutional imagery is involved
in this package, and none entered the repository.** No raster of uncertain provenance was
touched.

---

## 3. What arrived — per-file verification

Read with `rasterio` 1.4.4 / GDAL 3.12.3. Every one of the 20 files opened, reported the
properties below, and matched its checksum.

**Which number came from where.** The **API ETag** column is the `ETag` header returned by
`HEAD` on the S3 object, i.e. the checksum S3 reports for the object as stored. The **local
ETag** column was recomputed here from the bytes as they were written to disk, by the same
S3 multipart algorithm (md5 per 8 MiB part, md5 of the concatenated part digests, `-<n>`
suffix). Earth Search's STAC items carry **no** `file:checksum` field — the ETag is the only
checksum the API reports, which is why it is the one compared. For the SCL assets, which S3
stored as a single part, the ETag *is* the whole-file md5 and the comparison is a direct md5
comparison; for the 10 m bands, which S3 stored in 20–29 parts, the ETag is a digest-of-
digests and was reproduced exactly.

| tile | band | dtype | dimensions | CRS | affine (a, b, c, d, e, f) | nodata | bytes | API ETag | local ETag | match |
|---|---|---|---|---|---|---|---|---|---|---|
| 36TVK | B02 | uint16 | 10980 x 10980 | EPSG:32636 | 10.0, 0.0, 399960.0, 0.0, -10.0, 4500000.0 | 0.0 | 230,199,685 | `08622937c011495846ab6e861cb14ebf-28` | `08622937c011495846ab6e861cb14ebf-28` | **YES** |
| 36TVK | B03 | uint16 | 10980 x 10980 | EPSG:32636 | 10.0, 0.0, 399960.0, 0.0, -10.0, 4500000.0 | 0.0 | 233,373,867 | `00544aa7aaf0a61ec7dbcfdb0c30a9cf-28` | `00544aa7aaf0a61ec7dbcfdb0c30a9cf-28` | **YES** |
| 36TVK | B04 | uint16 | 10980 x 10980 | EPSG:32636 | 10.0, 0.0, 399960.0, 0.0, -10.0, 4500000.0 | 0.0 | 239,373,725 | `30780335a6fe87e85a024d681f827343-29` | `30780335a6fe87e85a024d681f827343-29` | **YES** |
| 36TVK | SCL | uint8 | 5490 x 5490 | EPSG:32636 | 20.0, 0.0, 399960.0, 0.0, -20.0, 4500000.0 | 0.0 | 4,710,392 | `e6706fd2d8cec2e737678e3cba2480d9` | `e6706fd2d8cec2e737678e3cba2480d9` | **YES** |
| 36TUK | B02 | uint16 | 10980 x 10980 | EPSG:32636 | 10.0, 0.0, 300000.0, 0.0, -10.0, 4500000.0 | 0.0 | 217,655,063 | `5c65c135be09abbde1c9512029c162ae-26` | `5c65c135be09abbde1c9512029c162ae-26` | **YES** |
| 36TUK | B03 | uint16 | 10980 x 10980 | EPSG:32636 | 10.0, 0.0, 300000.0, 0.0, -10.0, 4500000.0 | 0.0 | 221,496,078 | `3baee72a57de735aafe9332e9f5dad79-27` | `3baee72a57de735aafe9332e9f5dad79-27` | **YES** |
| 36TUK | B04 | uint16 | 10980 x 10980 | EPSG:32636 | 10.0, 0.0, 300000.0, 0.0, -10.0, 4500000.0 | 0.0 | 225,691,619 | `cd4da7373ba22f9ff35e43ecf0186128-27` | `cd4da7373ba22f9ff35e43ecf0186128-27` | **YES** |
| 36TUK | SCL | uint8 | 5490 x 5490 | EPSG:32636 | 20.0, 0.0, 300000.0, 0.0, -20.0, 4500000.0 | 0.0 | 4,320,024 | `8e9ee579dc22e7fda2d1076c598c63ff` | `8e9ee579dc22e7fda2d1076c598c63ff` | **YES** |
| 36SVJ | B02 | uint16 | 10980 x 10980 | EPSG:32636 | 10.0, 0.0, 399960.0, 0.0, -10.0, 4400040.0 | 0.0 | 229,856,354 | `b91f8e44d15f769987557a3fe3b85ba2-28` | `b91f8e44d15f769987557a3fe3b85ba2-28` | **YES** |
| 36SVJ | B03 | uint16 | 10980 x 10980 | EPSG:32636 | 10.0, 0.0, 399960.0, 0.0, -10.0, 4400040.0 | 0.0 | 233,694,818 | `da36498f8400c2128f98ef8e21036545-28` | `da36498f8400c2128f98ef8e21036545-28` | **YES** |
| 36SVJ | B04 | uint16 | 10980 x 10980 | EPSG:32636 | 10.0, 0.0, 399960.0, 0.0, -10.0, 4400040.0 | 0.0 | 240,226,172 | `a3e52f1b6fe53be8748aaeb870896929-29` | `a3e52f1b6fe53be8748aaeb870896929-29` | **YES** |
| 36SVJ | SCL | uint8 | 5490 x 5490 | EPSG:32636 | 20.0, 0.0, 399960.0, 0.0, -20.0, 4400040.0 | 0.0 | 3,794,300 | `202eaf9efb53ad0404f2f51aec2cb893` | `202eaf9efb53ad0404f2f51aec2cb893` | **YES** |
| 36SWJ | B02 | uint16 | 10980 x 10980 | EPSG:32636 | 10.0, 0.0, 499980.0, 0.0, -10.0, 4400040.0 | 0.0 | 164,315,443 | `56da663a1fd2cc192fb7979e0afdee2c-20` | `56da663a1fd2cc192fb7979e0afdee2c-20` | **YES** |
| 36SWJ | B03 | uint16 | 10980 x 10980 | EPSG:32636 | 10.0, 0.0, 499980.0, 0.0, -10.0, 4400040.0 | 0.0 | 168,154,464 | `66fc55a3e352db60a4566f48f6bfb651-21` | `66fc55a3e352db60a4566f48f6bfb651-21` | **YES** |
| 36SWJ | B04 | uint16 | 10980 x 10980 | EPSG:32636 | 10.0, 0.0, 499980.0, 0.0, -10.0, 4400040.0 | 0.0 | 173,379,335 | `312d8ded5a6670b910edcf87f552277c-21` | `312d8ded5a6670b910edcf87f552277c-21` | **YES** |
| 36SWJ | SCL | uint8 | 5490 x 5490 | EPSG:32636 | 20.0, 0.0, 499980.0, 0.0, -20.0, 4400040.0 | 0.0 | 2,784,869 | `d9e7c19b18fdb2830ab8165b31e3d530` | `d9e7c19b18fdb2830ab8165b31e3d530` | **YES** |
| 36SXJ | B02 | uint16 | 10980 x 10980 | EPSG:32636 | 10.0, 0.0, 600000.0, 0.0, -10.0, 4400040.0 | 0.0 | 229,844,125 | `273f5c5af9f9342f93a6c1519f1b5c3d-28` | `273f5c5af9f9342f93a6c1519f1b5c3d-28` | **YES** |
| 36SXJ | B03 | uint16 | 10980 x 10980 | EPSG:32636 | 10.0, 0.0, 600000.0, 0.0, -10.0, 4400040.0 | 0.0 | 234,434,749 | `b52ef589e5a22bb5178b64821607dff0-28` | `b52ef589e5a22bb5178b64821607dff0-28` | **YES** |
| 36SXJ | B04 | uint16 | 10980 x 10980 | EPSG:32636 | 10.0, 0.0, 600000.0, 0.0, -10.0, 4400040.0 | 0.0 | 241,604,135 | `610f31339adbf9f26a7fd8adbe82d867-29` | `610f31339adbf9f26a7fd8adbe82d867-29` | **YES** |
| 36SXJ | SCL | uint8 | 5490 x 5490 | EPSG:32636 | 20.0, 0.0, 600000.0, 0.0, -20.0, 4400040.0 | 0.0 | 4,133,443 | `47cb7af7da6962cdd253841b86a2dad5` | `47cb7af7da6962cdd253841b86a2dad5` | **YES** |

**20 of 20 checksums matched.** All files are single-band GeoTIFF, deflate-compressed,
tiled (1024 px blocks for the 10 m bands, 512 px for SCL), `nodata = 0`.

**GDAL reports `scale = 1.0` and `offset = 0.0` on every band, and no band-level tags.** The
STAC metadata says something different, and that discrepancy is §7.

---

## 4. The grid-identity assertion

**Claim under test.** For each granule, the reflectance 10 m grid is identical to that
granule's TCI grid: same CRS, same affine transform, same dimensions. If true, the WP0 chip
indexing transfers to this corpus unchanged.

**TCI references used**, exactly as `00-recon.md` §2.2 lists them:
`tubitak/data/ankara/TCI_36TVK_20260430.tif`, `tubitak/data/tiles36TUK/TCI.tif`,
`tubitak/data/tiles36SVJ/TCI.tif`, `tubitak/data/tiles36SWJ/TCI.tif`,
`tubitak/data/tiles36SXJ/TCI.tif`.

### 4.1 Known-true case — 15 comparisons, all IDENTICAL

| granule | B02 vs TCI | B03 vs TCI | B04 vs TCI | the shared grid |
|---|---|---|---|---|
| 36TVK | IDENTICAL | IDENTICAL | IDENTICAL | EPSG:32636, 10980 x 10980, (10, 0, 399960, 0, -10, 4500000) |
| 36TUK | IDENTICAL | IDENTICAL | IDENTICAL | EPSG:32636, 10980 x 10980, (10, 0, 300000, 0, -10, 4500000) |
| 36SVJ | IDENTICAL | IDENTICAL | IDENTICAL | EPSG:32636, 10980 x 10980, (10, 0, 399960, 0, -10, 4400040) |
| 36SWJ | IDENTICAL | IDENTICAL | IDENTICAL | EPSG:32636, 10980 x 10980, (10, 0, 499980, 0, -10, 4400040) |
| 36SXJ | IDENTICAL | IDENTICAL | IDENTICAL | EPSG:32636, 10980 x 10980, (10, 0, 600000, 0, -10, 4400040) |

**Verdict: the reflectance 10 m grid is identical to the TCI grid for all five granules.
WP0 chip indexing transfers directly.** The chip grid, the per-chip `easting`/`northing` in
`chip_grid.csv`, and the minipbf/render footprints all address the same pixels in this corpus
as they do in the TCI corpus. No re-indexing is needed and no resampling is implied.

### 4.2 Known-false case — the comparison can report a mismatch

Standing practice 10 and 11: a comparison that cannot report a mismatch is not a comparison.
The same function was run against a *different* granule's TCI grid.

| comparison | verdict | field that differs |
|---|---|---|
| 36TVK B02 vs **36SVJ** TCI | **MISMATCH** | `transform` |
| 36SWJ B02 vs **36SXJ** TCI | **MISMATCH** | `transform` |
| 36TUK B02 vs **36TVK** TCI | **MISMATCH** | `transform` |

**The false case fires on all three pairs.** Note what it is sensitive to and what it is not:
all five granules share EPSG:32636 and 10980 x 10980, so CRS and dimensions alone would *not*
have separated them — only the affine origin does. A grid check on this corpus that compared
CRS and shape but not the transform would pass every wrong pairing above. That is worth
carrying into WP3.

### 4.3 SCL grids also agree with the corpus already on disk

| granule | new SCL grid vs on-disk SCL grid |
|---|---|
| 36TVK, 36TUK, 36SVJ, 36SWJ, 36SXJ | IDENTICAL (all five) |

Each SCL is 5490 x 5490 at 20 m with the same origin as its 10 m grid, so a 256 px chip at
10 m is exactly 128 px on SCL with no fractional offset — the arithmetic WP0 §3.1 Path B
relies on.

---

## 5. Chip recount on this corpus

**Method, stated so the inference path is explicit.** WP0 Path B was reimplemented here from
scratch against this corpus's SCL: 10980 // 256 = 42, so 42 x 42 = 1764 non-overlapping
256 x 256 windows per granule; each maps to a 128 x 128 window on the 20 m SCL.

**SCL classes treated as *not* clear, and why:**

| class | meaning | treated as | reason |
|---|---|---|---|
| 0 | no data | **nodata** | outside the granule's imaged area; nothing to learn from |
| 3 | cloud shadow | **cloud** | radiometry is not the surface's |
| 8 | cloud, medium probability | **cloud** | " |
| 9 | cloud, high probability | **cloud** | " |
| 10 | thin cirrus | **cloud** | attenuated and haze-contaminated |
| 11 | snow / ice | **snow** | a distinct surface state; WP0 screened it out, so this corpus must too |
| 1, 2, 4, 5, 6, 7 | saturated/defective, dark area, vegetation, not vegetated, water, unclassified | **clear** | everything else |

These are exactly the classes `00-recon.md` §3.1 Path B used, and the thresholds are exactly
those of `tubitak/scripts/tile_pipeline.py::valid()` — nodata fraction ≤ 0.005, cloud fraction
≤ 0.01, snow fraction ≤ 0.02. **They were chosen to match WP0, not re-derived**, because the
point of the recount is to be comparable with it.

### 5.1 The counter was calibrated before its output was used

Standing practice 11 — the known-false input first:

```
  all-nodata (class 0)   -> 1764 windows,    0 valid, rej n/c/s = 1764/0/0   (expected 0)     OK
  all-cloud  (class 9)   -> 1764 windows,    0 valid, rej n/c/s = 0/1764/0   (expected 0)     OK
  all-snow   (class 11)  -> 1764 windows,    0 valid, rej n/c/s = 0/0/1764   (expected 0)     OK
  all-clear  (class 4)   -> 1764 windows, 1764 valid, rej n/c/s = 0/0/0      (expected 1764)  OK
```

All three rejection reasons are individually reachable, and each is attributed to the right
cause. `00-recon.md` calibrated three cases; the fourth (all-snow) was added here because the
snow threshold is the one that differs from the other two and had never been exercised alone.

### 5.2 Result

| granule | windows | clear | rej nodata | rej cloud | rej snow | clear % |
|---|---|---|---|---|---|---|
| 36TVK | 1764 | 1568 | 0 | 177 | 19 | 88.9 |
| 36SVJ | 1764 | 1763 | 0 | 1 | 0 | 99.9 |
| 36SWJ | 1764 | 1177 | 440 | 110 | 37 | 66.7 |
| 36SXJ | 1764 | 1687 | 0 | 76 | 1 | 95.6 |
| 36TUK | 1764 | 1398 | 122 | 235 | 9 | 79.3 |
| **total** | **8820** | **7593** | | | | **86.1** |

Overlap removed, first-come rule, order 36TVK → 36SVJ → 36SWJ → 36SXJ → 36TUK (a clear chip
is dropped if its centre falls inside an earlier-listed granule's footprint):

```
  36TVK: 1568 clear -> keep 1568, drop   0
  36SVJ: 1763 clear -> keep 1595, drop 168
  36SWJ: 1177 clear -> keep 1009, drop 168
  36SXJ: 1687 clear -> keep 1519, drop 168
  36TUK: 1398 clear -> keep 1299, drop  99
  TOTAL distinct = 6990   (45,810 km2)
```

### 5.3 Both numbers, side by side, and why they are equal

| | corpus | mask | raw clear chips | distinct after overlap |
|---|---|---|---|---|
| **WP0** (`00-recon.md` §3.1–3.2, Path B) | TCI corpus (`tubitak/data/ankara/`, `tubitak/data/tiles36*/`) | that corpus's own `SCL.tif` | **7593** | **6990** |
| **WP2A** (this document) | reflectance corpus (`tubitak/data/s2_reflectance_l2a/`) | that corpus's own `SCL.tif` | **7593** | **6990** |

**The WP0 numbers are not replaced. They stand.** The recount agrees with them exactly.

**The difference to explain is that there is no difference, and that is not a coincidence —
it is entailed.** §1.2 established that the SCL files in the two corpora are byte-identical
(same md5, all five granules). The two counts are therefore two runs of equivalent code over
literally the same bytes, and any disagreement would have meant an error in one of the two
implementations, not a property of the corpora. Read that way this is a **useful independent
reimplementation check** — a second, separately written screener reproduced 7593 and 6990
from the same input — but it is **not independent evidence about the reflectance corpus's
cloud content.** Claiming "the reflectance corpus was independently recounted and agrees"
would overstate it.

What *is* new information about the reflectance corpus: its own SCL is the same SCL, so the
per-chip cloud screen already computed in `chip_grid.csv` applies to it unchanged, and (with
§4.1) so does the chip indexing. **The reflectance corpus inherits WP0's chip inventory
intact.**

**One caveat on the number itself, inherited from WP0 and not fixed here.** The clear-chip
count uses only SCL. The 36TUK TCI has a nodata corner that `00-recon.md` §2.2 noted; the SCL
nodata screen catches 122 of 36TUK's windows and 440 of 36SWJ's, and Path A (which read TCI
RGB == 0) and Path B disagreed by 9 chips in 7590. That disagreement is unchanged here.

---

## 6. Value distributions — measured, not decided

**No normalisation was chosen, and no scaling code was written.** These are raw stored DN.

**Sample, stated exactly.** Every clear pixel of all five granules. Clear is per-pixel, from
each granule's own SCL: class **not in {0, 3, 8, 9, 10, 11}** — the same class set the chip
screen rejects (§5), applied pixel-by-pixel rather than as a per-chip fraction. The 20 m SCL
mask was expanded to 10 m by exact 2 x 2 nearest-neighbour replication, which is lossless
because the grids nest exactly (§4.3). **n = 554,534,176 pixels per band** (116.9 M + 120.6 M
+ 87.5 M + 120.1 M + 109.5 M for 36TVK / 36SVJ / 36SWJ / 36SXJ / 36TUK), which is 92.0 % of
all 5 x 10980² pixels.

**These are exact, not sampled.** Statistics were computed from a full 65536-bin histogram of
every clear pixel, so min, max, percentiles and threshold counts are exact integers over the
whole population, not estimates from a subsample.

### 6.1 Pooled over all five granules

| band | n | min | p1 | p25 | p50 | p75 | p99 | p99.9 | max | mean | DN >= 10000 | DN = 0 | negatives |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **B02** (blue) | 554,534,176 | 0 | 76 | 387 | 644 | 1005 | 2676 | **4084** | 20703 | 765.1 | 2,352 (0.00042 %) | 3,443 | **impossible — uint16** |
| **B03** (green) | 554,534,176 | 0 | 287 | 711 | 1006 | 1449 | 3181 | **4663** | 18975 | 1146.3 | 3,393 (0.00061 %) | 568 | **impossible — uint16** |
| **B04** (red) | 554,534,176 | 0 | 107 | 637 | 1094 | 1721 | 3608 | **5029** | 17891 | 1249.1 | 4,124 (0.00074 %) | 1,290 | **impossible — uint16** |

**Negative values.** The dtype is `uint16` on all fifteen band files (§3), so negatives cannot
be stored and the count is not merely zero but undefined. This matters, because the STAC
metadata declares an offset that would make some of these values negative once applied — §7.

**DN = 0.** Zero is also the declared `nodata` value, yet 3,443 / 568 / 1,290 clear-masked
pixels carry it. That is at most 6 per million of the band (B02); they are pixels SCL calls clear where the band
stores its nodata sentinel. Small, but WP3 should decide whether they are excluded, because
"nodata" and "a reflectance of exactly zero" are indistinguishable in this encoding.

**Saturation.** No pixel reaches 65535. The largest value seen anywhere is 20703 (36TUK B02).
SCL class 1 (saturated / defective) has a population of **exactly zero** across all five
granules, so nothing was flagged as saturated by the processor either.

### 6.2 Per granule

| granule | band | n | min | p1 | p25 | p50 | p75 | p99 | p99.9 | max | DN >= 10000 | DN = 0 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 36TVK | B02 | 116,870,656 | 0 | 78 | 370 | 552 | 820 | 2751 | 4924 | 19717 | 911 | 702 |
| 36SVJ | B02 | 120,557,412 | 0 | 107 | 514 | 838 | 1170 | 2534 | 4136 | 19287 | 222 | 239 |
| 36SWJ | B02 | 87,483,140 | 1 | 160 | 490 | 738 | 1036 | 2859 | 3743 | 18232 | 276 | 0 |
| 36SXJ | B02 | 120,116,988 | 0 | 58 | 318 | 634 | 1005 | 2328 | 3279 | 19609 | 822 | 929 |
| 36TUK | B02 | 109,505,980 | 0 | 16 | 333 | 533 | 851 | 2791 | 4167 | 20703 | 121 | 1,573 |
| 36TVK | B03 | 116,870,656 | 0 | 285 | 669 | 856 | 1191 | 3311 | 5430 | 18252 | 1,392 | 14 |
| 36SVJ | B03 | 120,557,412 | 0 | 353 | 886 | 1255 | 1649 | 3120 | 4702 | 17920 | 229 | 1 |
| 36SWJ | B03 | 87,483,140 | 1 | 228 | 818 | 1115 | 1493 | 3176 | 3987 | 17139 | 313 | 0 |
| 36SXJ | B03 | 120,116,988 | 0 | 301 | 697 | 1046 | 1490 | 3003 | 3879 | 18125 | 884 | 24 |
| 36TUK | B03 | 109,505,980 | 0 | 174 | 616 | 847 | 1230 | 3359 | 4805 | 18975 | 575 | 529 |
| 36TVK | B04 | 116,870,656 | 0 | 124 | 593 | 903 | 1361 | 3667 | 5610 | 17295 | 1,835 | 125 |
| 36SVJ | B04 | 120,557,412 | 0 | 130 | 854 | 1442 | 1993 | 3618 | 5205 | 17051 | 226 | 33 |
| 36SWJ | B04 | 87,483,140 | 0 | 86 | 797 | 1276 | 1785 | 3291 | 4187 | 16445 | 339 | 1 |
| 36SXJ | B04 | 120,116,988 | 0 | 100 | 575 | 1131 | 1797 | 3662 | 4480 | 17207 | 833 | 252 |
| 36TUK | B04 | 109,505,980 | 0 | 64 | 542 | 893 | 1414 | 3701 | 5142 | 17891 | 891 | 879 |

Per-granule medians spread by a factor of about 1.6 in every band (B02: 533 to 838; B03: 847
to 1255; B04: 893 to 1442), with 36SVJ consistently brightest and 36TVK/36TUK darkest. A
normalisation fitted on one granule will not be centred on another. That is a WP3 input, not
a WP2A decision.

### 6.3 SCL class census (pooled, 20 m pixels, all five granules)

| class | meaning | pixels | share |
|---|---|---|---|
| 0 | no data | 9,380,775 | 6.225 % |
| 1 | saturated / defective | 0 | 0.000 % |
| 2 | dark area / cast shadow | 274,967 | 0.182 % |
| 3 | cloud shadow | 377,209 | 0.250 % |
| 4 | vegetation | 64,697,172 | 42.931 % |
| 5 | not vegetated | 71,114,030 | 47.189 % |
| 6 | water | 2,169,019 | 1.439 % |
| 7 | unclassified | 378,356 | 0.251 % |
| 8 | cloud, medium probability | 705,942 | 0.468 % |
| 9 | cloud, high probability | 470,700 | 0.312 % |
| 10 | thin cirrus | 470,460 | 0.312 % |
| 11 | snow / ice | 661,870 | 0.439 % |
| > 11 | (undefined) | 0 | 0.000 % |

Cloud in all forms (classes 3, 8, 9, 10) is 1.34 % of pixels; nodata (6.2 %, almost all of it 36SWJ's 25.4 % and
36TUK's 5.7 % granule-edge margin) is the larger loss. Water is 1.4 % — thin, and relevant if
WP3 wants a normalisation that behaves over water.

---

## 7. The offset contradiction — flagged, not resolved

This is the highest-priority item for WP3 and it is exactly the class of bug this project has
now hit four times (`CLAUDE.md`, standing practice 12: *code that assumes a unit met a
different unit*).

Three sources say three things about how a stored DN becomes a reflectance:

| source | says |
|---|---|
| STAC `raster:bands` on B02/B03/B04 | `"scale": 0.0001, "offset": -0.1` — i.e. reflectance = DN x 0.0001 - 0.1 |
| STAC property `earthsearch:boa_offset_applied` | `true` — i.e. the BOA offset has already been applied to the stored data |
| The GeoTIFF itself, as GDAL reads it | `scale = 1.0`, `offset = 0.0`, no band tags |

The first two cannot both be acted on. Processing baseline 05.12 is above 04.00, so the
product does carry a `BOA_ADD_OFFSET` of -1000 DN; the question is whether it is already
folded into these COGs.

**The measurement decides which reading is physically possible, and it is worth recording
even though the choice is WP3's.** Applying the declared offset to the pooled medians of
§6.1 gives:

| band | median DN | DN x 0.0001 (offset **not** applied again) | DN x 0.0001 - 0.1 (offset applied) |
|---|---|---|---|
| B02 | 644 | 0.0644 | **-0.0356** |
| B03 | 1006 | 0.1006 | 0.0006 |
| B04 | 1094 | 0.1094 | 0.0094 |

Applying the offset makes the **median** blue reflectance of 554 million clear land pixels
negative, and drives B03 and B04 to within a thousandth of zero. The p1 of B02 becomes
-0.0924. Not applying it gives 0.064 / 0.101 / 0.109 — ordinary values for blue, green and
red over semi-arid Anatolian land in spring. **The evidence is one-sided: `raster:bands.offset`
appears to be a declaration of the product's nominal offset rather than an instruction to
apply one to these bytes, consistent with `boa_offset_applied: true`.**

**This document does not decide it, and no scaling code was written.** WP3 owns the choice.
What WP2A asserts is narrower and is what the record needs: *the two pieces of STAC metadata
contradict each other, the contradiction is a 1000-DN shift — about 1.5 median blue
reflectances — and it must be resolved explicitly and written down before any pixel is
scaled.* A silent guess here would be the fifth instance of the same bug.

**Recommended for WP3 (a check, not a decision):** whatever convention is chosen, assert it at
the point of use — reject a band whose clear-pixel median maps to a negative reflectance —
and give that assertion a known-false case, per standing practices 11 and 12.

---

## 8. Environment and versions

Everything that read or checksummed the data:

| component | version |
|---|---|
| Python | 3.11.15 (conda env `gencp`, `/opt/homebrew/Caskroom/miniforge/base/envs/gencp`) |
| platform | macOS-26.5.1-arm64 |
| rasterio | 1.4.4 |
| GDAL (via rasterio) | 3.12.3 |
| numpy | 2.4.6 |
| requests | 2.34.2 |
| urllib3 | 2.7.0 |
| certifi | 2026.07.22 |
| hashlib / md5 | CPython stdlib, OpenSSL-backed |
| Earth Search STAC API | v1, `earth-search.aws.element84.com` |
| Earth Search item generator | `sentinel2-to-stac 2026.08.16` (from `processing:software`) |

No packages were installed. Nothing outside `tubitak/data/` and this file was created or
modified. No code was written into the repository — the acquisition and measurement scripts
ran from the session scratchpad, and their content is reproduced in method form above rather
than committed, since this package was scoped to acquisition and measurement only.

**Randomness:** none. No step in this package draws a random number. There is no seed to
record because there is no stochastic arm: the STAC query is deterministic, the transfers are
verified by checksum, and the statistics are exhaustive rather than sampled.

---

## 9. Repository hygiene

Everything written under `tubitak/data/s2_reflectance_l2a/` is gitignored:

```
$ git check-ignore -v tubitak/data/s2_reflectance_l2a/36TVK_20260430/B02.tif
.gitignore:54:tubitak/data/*	tubitak/data/s2_reflectance_l2a/36TVK_20260430/B02.tif
```

`git status` after all 20 transfers and all measurement:

```
$ git status
On branch tubitak-tr
Your branch is up to date with 'origin/tubitak-tr'.

Untracked files:
  (use "git add <file>..." to track)
	tubitak/sr/

nothing added to commit but untracked files present (use "git add" to track)
```

The only path git sees is `tubitak/sr/`, collapsed because the whole directory is untracked.
Expanded (`git status --porcelain --untracked-files=all tubitak/sr`) it holds twelve files:
`docs/00-recon.md` (WP0), `docs/02a-reflectance-corpus.md` (**this document — the only file
this work package created**), and ten files under `docs/`, `sr_core/` and `tests/` written by
the concurrent session. The same command against `tubitak/data` returns **zero lines**:
**3.3 GB of imagery is invisible to git.** No `git add`,
`git commit`, `git checkout` or `git stash` was run. No file outside `tubitak/data/` and this
document was created, modified, moved or deleted; in particular no TCI or SCL file of the
existing corpus was touched, and nothing under `tubitak/sr/sr_core/` was read for modification
or written.

---

## 10. Open items

1. **The offset contradiction (§7) is unresolved and is the blocking input to WP3.** STAC
   declares `offset: -0.1` and simultaneously `boa_offset_applied: true`; the GeoTIFF declares
   neither. The measurement points one way but the decision is WP3's, and it must be written
   down with an assertion at the point of use.
2. **DN = 0 inside the clear mask** (§6.1): 3,443 / 568 / 1,290 pixels per band carry the
   declared nodata sentinel while SCL calls them clear. WP3 must decide whether zero means
   nodata or a reflectance of zero — the encoding cannot distinguish them.
3. **The chip recount is a reimplementation check, not independent evidence** (§5.3). Because
   the two corpora share byte-identical SCL, 7593 / 6990 could not have come out differently.
   Anyone citing the recount as corroboration of the cloud screen should cite it as what it is.
4. **A grid check on this corpus must compare the affine transform, not just CRS and shape**
   (§4.2). All five granules share EPSG:32636 and 10980 x 10980; only the origin separates
   them. Any WP3 check that omits the transform will pass every wrong pairing.
5. **Per-granule brightness spreads by ~1.6x in every band** (§6.2). A normalisation fitted on
   one granule is not centred on another. WP3 should decide whether normalisation is global,
   per-granule, or per-chip, and state which.
6. **Path A / Path B still disagree by 9 chips in 7590**, inherited unchanged from WP0 §3.1.
   Not investigated here; it is a 0.12 % effect attributable to window size (257 vs 256) and
   nodata source (TCI RGB == 0 vs SCL class 0).
7. **Place names for 36TUK and 36SVJ remain not determined**, unchanged from `00-recon.md`
   open item 1. This package did not address them; the STAC metadata carries no toponym.
8. **B08 (NIR) was deliberately not fetched.** If WP3 or later work ever wants a 4-channel
   model or an NDVI-based screen, it is another ~230 MB per granule from the same five items,
   whose IDs are now recorded — the fetch is a 20-second job per granule and no longer a
   reproducibility question.
9. **Only the 10 m grid identity was asserted.** The SCL 20 m grids were checked against the
   on-disk SCL (§4.3) but not against a nested-grid assertion of the form "SCL origin equals
   B02 origin and SCL pixel is exactly 2 x B02 pixel". That relationship was verified by
   inspection of the transforms in §3 and is used by §5–6; WP3 should make it an assertion if
   it cuts chips from both grids.
