# WP3A registration — the Wald corpus and its bicubic control

**Registered:** 2026-08-30, Project 2 WP3A, **before a single chip was cut and before any
metric was computed.** Standing practice 4: predictions are registered before outcomes. The
only measurement that preceded this file is the D7 radiometry diagnostic, which is an
*input* measurement made to decide a conversion, and whose result is quoted in §2 below.

This file is never edited to match a result. The numbers it names live in
`tubitak/sr/sr_data/params.py` and are imported, never restated as literals, so that what
ran is what was registered.

---

## 1. Corpus and directories, named exactly

Standing practice 5. A wrong name in registration text has already caused a failed gate and
a sign flip in this project.

**Source reflectance:** `tubitak/data/s2_reflectance_l2a/<TILE>_<DATE>/{B02,B03,B04,SCL}.tif`
— the 20 files WP2A acquired and verified against their S3 ETags (02a §3, 20/20 matched).

| tile | directory | date | datatake | orbit | product ID |
|---|---|---|---|---|---|
| 36TVK | `36TVK_20260430` | 2026-04-30 | A008614 | R064 | `S2C_MSIL2A_20260430T083651_N0512_R064_T36TVK_20260430T140714.SAFE` |
| 36TUK | `36TUK_20260430` | 2026-04-30 | A008614 | R064 | `S2C_MSIL2A_20260430T083651_N0512_R064_T36TUK_20260430T140714.SAFE` |
| 36SVJ | `36SVJ_20260430` | 2026-04-30 | A008614 | R064 | `S2C_MSIL2A_20260430T083651_N0512_R064_T36SVJ_20260430T140714.SAFE` |
| 36SWJ | `36SWJ_20260430` | 2026-04-30 | A008614 | R064 | `S2C_MSIL2A_20260430T083651_N0512_R064_T36SWJ_20260430T140714.SAFE` |
| 36SXJ | `36SXJ_20260527` | 2026-05-27 | A009000 | R021 | `S2C_MSIL2A_20260527T082601_N0512_R021_T36SXJ_20260527T135213.SAFE` |

**Corpus written to:** `tubitak/data/sr_wald_corpus/` — gitignored by `.gitignore:54`.
**Bands stored, in this order:** B02, B03, B04 (blue, green, red).

## 2. Radiometry — D7, decided by measurement

`reflectance = DN / 10000`. **The BOA offset is not applied.**

Measured before this registration was written, over **every clear pixel of all five
granules, n = 554,534,176 per band**, from a full 65536-bin histogram so percentiles are
exact over the population rather than estimated from a subsample
(`tubitak/sr/sr_data/checks/d7_radiometry.py`):

| band | DN p1 / p50 / p99.9 | A = DN/10000: p50 | A frac < 0 | B = DN/10000 − 0.1: p50 | B frac < 0 |
|---|---|---|---|---|---|
| B02 | 76 / 644 / 4084 | **0.0644** | 0.0000 % | **−0.0356** | **74.7164 %** |
| B03 | 287 / 1006 / 4663 | **0.1006** | 0.0000 % | 0.0006 | 49.5167 % |
| B04 | 107 / 1094 / 5029 | **0.1094** | 0.0000 % | 0.0094 | 45.0807 % |

A puts every band median in an ordinary land-reflectance range. B puts the blue median below
zero and three quarters of blue pixels below zero, which is not a physical surface
reflectance. **A is used. B is not.** The dissenting STAC `raster:bands offset: −0.1` is
recorded as a known Element84 metadata inconsistency and is not applied.

These DN percentiles reproduce WP2A §6.1 exactly, by an independent implementation over the
same pixels. They are not independent evidence — the two read the same SCL bytes — and are
reported as a reimplementation check.

## 3. Clear masking

**Clear = SCL class in {2, 4, 5, 6, 7}**: dark area/cast shadow, vegetation, not vegetated,
water, unclassified. **Rejected: 0** (no data), **1** (saturated/defective), **3** (cloud
shadow), **8, 9** (cloud medium/high probability), **10** (thin cirrus), **11** (snow/ice).

Why these. Cloud, cirrus, cloud shadow and snow are rejected because a super-resolution model
should not be trained to reconstruct them, and because they are not the surface. Nodata is
rejected because it is not data. Class 1 is rejected because a defective pixel is not a
measurement — this differs from WP0/WP2A's screen, which rejected `{0,3,8,9,10,11}` and so
retained class 1; WP2A measured class 1 at exactly **0 pixels** across all five granules, so
the two definitions select identical pixels on this corpus and the difference is only that
this one does not depend on that population staying empty. Class 2 and class 7 are retained
because dark ground and ground the processor declined to label are still ground.

**The 20 m SCL mask is expanded to 10 m by exact 2 × 2 replication.** This is lossless only
because the grids nest exactly, so nesting is *checked* — CRS, origin exactly equal, pixel
size exactly 2×, dimensions exactly half — at the point the assumption is made
(`sr_data.clear.require_nested`), not assumed at the call site. WP2A open item 4 is the
reason origin is compared and not only CRS and shape: all five granules share EPSG:32636 and
10980 × 10980, so a check omitting the transform would pass every wrong pairing.

## 4. Chip geometry — D8

| | |
|---|---|
| target chip | **256 × 256 at 10 m** = 2560 m square |
| Wald input | **128 × 128 at 20 m**, produced in the dataloader, never stored |
| factor learned | **2** |
| stride | **256 px** — chips are non-overlapping and share no pixel |
| chips per granule | 10980 // 256 = 42, so **42 × 42 = 1764** candidates |
| stored dtype | **uint16 DN**, shape (N, 3, 256, 256) |

**Minimum clear fraction per chip: 1.0.** Every SCL pixel over the chip footprint must be
clear. Not 0.99: the loss is computed per pixel, so a chip that is 99 % clear asks the
network to reconstruct 1 % of pixels that are cloud or nodata, and requiring 1.0 removes the
need for a per-pixel loss mask, which is one fewer thing to get wrong. With ~7000 candidates
and no shortage, strictness is free.

**A chip is additionally rejected if any B02/B03/B04 pixel equals 0.** This settles WP2A
open item 2: DN 0 is simultaneously the declared nodata sentinel and a legal reflectance, and
the encoding cannot distinguish them. WP2A measured 3,443 / 568 / 1,290 pixels per band that
SCL calls clear yet store 0. Rejecting the chip removes the ambiguity from the corpus rather
than carrying it into a loss function.

**The WP4 inference tile contract, recorded so it is not rediscovered.** The trained network
consumes 128 source pixels, because its input is the 20 m image; WP1's bicubic path tiles the
source at 512. Overlap stays 32 source pixels. Computed with `sr_core.tiles.tile_grid` on a
10980² granule:

| path | tile | overlap | stride | tiles |
|---|---|---|---|---|
| WP1 bicubic, `sr_core` default | 512 | 32 | 480 | 23 × 23 = **529** |
| WP4 ONNX, D8 contract | **128** | 32 | 96 | 115 × 115 = **13,225** |

**25.0× more tiles**, and each carries a network forward pass rather than a PIL resize. A
note on the brief: it describes WP1's bicubic tile as 256; `sr_core.tiles.DEFAULT_TILE_PX` is
512, and 529 is the figure at 512. At 256 the count would be 49 × 49 = 2,401. The 529 the
brief asks to compare against is the 512 figure, so 512 is what is compared.

## 5. Degradation — D9

**MTF-matched Gaussian low-pass, then decimation by two.** Not a plain resize.

**Target modulation at the 20 m Nyquist frequency: 0.3.** This is a stated *argument*
(`params.MTF_AT_NYQUIST`), not a constant baked into code; changing it is a corpus
regeneration.

**Derivation of the sigma** — shown rather than copied:

```
A Gaussian PSF of standard deviation s source pixels has, normalised to 1 at DC,
    MTF(f) = exp(-2 * pi^2 * s^2 * f^2),     f in cycles per source pixel.
The decimated grid samples every `scale` source pixels, so
    f_nyq = 1 / (2 * scale) = 0.25 cycles/source px   (= 0.025 cycles/m at 10 m)
Setting MTF(f_nyq) = m and solving:
    s = sqrt( -ln(m) / (2 * pi^2 * f_nyq^2) )
For m = 0.3, scale = 2:
    s^2 = 1.2039728043259361 / (2 * 9.869604401089358 * 0.0625)
        = 1.2039728043259361 / 1.2337005501361697 = 0.9759053...
    s   = 0.987878331000285 source px = 9.8788 m
Verification: exp(-2*pi^2*s^2*0.0625) evaluates to exactly 0.3.
```

**Kernel and phase.** The kernel is truncated at 4 sigma (radius 4 source px, 8 taps) and
renormalised to sum to 1. Decimation samples at the **centre of each 2 × 2 source block**, so
the 20 m grid nests exactly inside the 10 m grid under the same half-pixel-centre convention
WP1's Gate S asserts. Because a block centre falls at a half-integer source coordinate, the
Gaussian is evaluated at half-integer offsets: output `j` is `sum_o k[o] * src[2j + o]` with
`k[o] proportional to exp(-0.5 * ((o - 0.5) / s)^2)` over integer offsets
`o in [-3, 4]`. The kernel is symmetric about `o = 0.5`, which *is* the block centre.

### What this makes the model learn, and the assumption underneath it

The model learns to invert **a Gaussian blur of sigma 0.9879 pixels followed by 2×
decimation, measured between a 20 m image and a 10 m image.** It is then applied between a
10 m image and a 5 m image.

**The assumption, in words, because it must not be left implied by the code: the
sensor's modulation transfer function is assumed to bear the same relationship to the
sampling grid at 10 m → 5 m as it does at 20 m → 10 m — that is, the imaging system is
assumed scale-invariant over a factor of two in ground sample distance.**

This is false in general. A real instrument's MTF is fixed by its optics, detector pitch and
platform motion; it does not rescale when you pretend the pixels are a different size. The
20 m image produced here is a *simulation* of a coarser Sentinel-2, not a real one, and the
real 10 m Sentinel-2 image the model is applied to has its own, different MTF. **This
assumption is unverifiable with the data in this project** — nothing on this machine is real
imagery finer than 10 m over these footprints (`00-recon.md` §3.3) — and it is the standard
and load-bearing core of the Wald protocol rather than a defect peculiar to this work.

It is registered here so that no result from WP3B or WP4 can be presented as though the
5 m output had been validated. It has not been and, with this corpus, cannot be.

**Only one corpus is built.** No second MTF value is produced now.

## 6. Storage — D10

**Targets only. The degradation happens in the dataloader**
(`sr_data.degrade.degrade_chip`), so training imports the same function the control baseline
uses. This halves storage, removes any possibility of drift between a corpus-time and a
train-time degradation, and guarantees one implementation of the thing the model is learning
to invert.

Chips are stored as one uncompressed `.npy` shard per split, `uint16`, shape
`(N, 3, 256, 256)`, plus one manifest CSV per corpus carrying for every chip: granule, chip
row and column, the UTM easting/northing of its north-west corner, its affine transform, its
split, and its clear fraction.

## 7. Normalisation — D12

**normalised = DN / 5000.0**, equivalently **reflectance / 0.5**. One constant, common to all
three bands. Fixed corpus-wide, identical at training and at inference. No per-image
percentile stretch of any kind.

Justification. A model deployed offline on board cannot have its output depend on the
statistics of the scene in front of it, so the constant must be chosen once from the corpus
and then frozen. WP2A measured the pooled p99.9 of clear pixels at 4084 / 4663 / 5029 DN
against a corpus maximum of 20703. Dividing by 5000 DN maps the brightest band's p99.9 to
1.006 — essentially unity — so about 99.9 % of clear-land signal lands in [0, 1] while the
headroom above 1 remains real rather than clipped away, and the divisor is exactly
reflectance / 0.5, a round physical number rather than a fitted one. **No clipping is applied
anywhere in the corpus or the control**; whether a model clips its output is a WP3B decision.

A single constant rather than one per band is deliberate: per-band scaling rescales the
colour relationships between B02, B03 and B04, and those relationships are what the
downstream matching stage keys on. The cost is that blue, whose p99.9 is 4084, uses less of
the nominal range than red; that is accepted and stated rather than optimised away.

WP2A §6.2 measured per-granule medians spreading by ~1.6× in every band. A global constant is
therefore *not* centred on any individual granule, by construction. That is the intended
behaviour: the alternative — per-granule normalisation — would make the model's output depend
on which granule it was told it was looking at.

## 8. Splits — D11

**Geographic, never random.**

* Each granule's 42 × 42 chip grid is partitioned into **blocks of 14 × 14 chips**
  (35,840 m square). 42 = 3 × 14 exactly, so a granule is **3 × 3 = 9 blocks** with no
  ragged remainder.
* Within each of the four training granules, the 9 blocks are assigned **7 train, 1 val,
  1 test**, by a permutation seeded with `SPLIT_SEED = 20260830`. Four granules give
  **28 train, 4 val, 4 test** blocks.
* **Buffer: 2560 m** — one full chip width. Any chip lying within 2560 m of a chip assigned
  to a *different* split is **dropped from the corpus entirely**, not reassigned. Chips do
  not overlap, so this guards against spatial autocorrelation between neighbours rather than
  against shared pixels.
* **`36SXJ` is held out whole.** Every one of its accepted chips forms a second test set and
  none of it enters train or val.

**Why 36SXJ.** WP2A established that four of the five granules are one datatake — A008614,
orbit R064, fourteen seconds apart — so this corpus contains **two acquisition conditions,
not five**. 36SXJ is the only granule from the other one (2026-05-27, orbit R021, 27 days
later). It is also the morphologically distinct site, Cappadocia tuff badlands.

**What holding out 36SXJ tests:** transfer to an unseen acquisition — different date,
different illumination geometry, different orbit — and simultaneously to an unseen landform.
**What it does not test, and cannot:** those two factors are **confounded** and this corpus
cannot separate them. A drop in performance on 36SXJ is not attributable to either one
alone. It also does not test transfer to a different sensor, a different season beyond four
weeks, a different climate zone, or a different atmospheric state. Holding out any of the
other four granules would have tested *less*, because it would have left the model with three
granules from the identical datatake and asked it to generalise fourteen seconds.

**Reporting rule: the in-distribution test blocks and the held-out granule are reported
ALWAYS SEPARATELY and NEVER POOLED**, in WP3A, WP3B and WP4. They measure different things
and a pooled number would mean neither.

## 9. Metrics, and the one convention

**Domain: normalised reflectance, `DN / 5000.0`, float32, dimensionless. Not DN. Not 8-bit.
Not decibels of DN.** Every metric below is computed in that domain, on unclipped values.

**Convention, stated once and never flipped: every metric is computed PER CHIP, and the
reported figure is the UNWEIGHTED ARITHMETIC MEAN over the chips of that split.** Not pooled
over all pixels of a split. A pooled MSE would let one large-error chip dominate; a per-chip
mean weights every chip equally, which is what "how well does it do on a scene" means.

| metric | definition |
|---|---|
| **PSNR** | per chip: `10 * log10(R^2 / MSE)` with `R = 1.0` (the nominal full scale of the normalised domain) and MSE taken over all 3 × 256 × 256 values of the chip; then the mean over chips. Reported in dB. |
| **SSIM** | per chip: computed per band on the 256 × 256 plane with an 11 × 11 Gaussian window, sigma 1.5, `K1 = 0.01`, `K2 = 0.03`, data range 1.0 (Wang et al. 2004); the three per-band SSIMs averaged to give the chip's SSIM; then the mean over chips. |
| **MAE** | per chip: mean `abs(pred - target)` over all 3 × 256 × 256 values, in normalised units; then the mean over chips. |

`scikit-image` is not installed in this environment and no package was installed, so SSIM is
implemented in `sr_data.metrics` and is validated against its own known-true and known-false
cases rather than against a reference implementation. That is a weaker check than a
cross-implementation comparison and is recorded as such.

## 10. The registered bicubic control

Computed **before any model exists**, on both test sets separately:

> degraded 128 × 128 input → `sr_core.upsample.BicubicUpsampler(scale=2)` → 256 × 256
> prediction, compared against the 256 × 256 target.

The upsampler is WP1's, imported read-only and unmodified. It runs on float32 normalised
values, where it does not clip (`sr_core.upsample` clips integer dtypes only), so the control
carries no clipping decision.

**These three numbers per test set are the bar WP3B has to clear. They are registered now
precisely so that the bar cannot move after a model's numbers are seen.** A trained model
that does not beat bicubic on the in-distribution test set has not learned the task; one that
beats it there and not on 36SXJ has learned the acquisition, not the physics.

## 11. Invariance — what must not change for this corpus to mean what we claim

Standing practice 1.

1. **The five product IDs in §1.** They are the demonstrated source of the bytes, not a
   plausible reconstruction (WP2A §1.2, byte-level ETag proof). A different processing
   baseline would change the radiometry that D7 settles.
2. **`DN_TO_REFLECTANCE = 1/10000` with no offset.** If a future product has
   `boa_offset_applied: false`, D7's conclusion does not transfer and the diagnostic must be
   re-run, not assumed.
3. **`CLEAR_CLASSES = {2,4,5,6,7}` and `MIN_CLEAR_FRACTION = 1.0`.** Loosening either changes
   what "clear" means in every count and every metric downstream.
4. **`MTF_AT_NYQUIST = 0.3` and the half-integer kernel phase.** The sigma follows from the
   first; the second is what makes the 20 m grid nest inside the 10 m grid. Changing either
   regenerates the corpus and invalidates every metric measured on the old one.
5. **`NORM_DIVISOR_DN = 5000.0`, one constant for three bands.** Every metric in §9 is in
   these units; a different divisor rescales MAE linearly and moves PSNR by
   `20*log10(ratio)`. Numbers from two divisors are not comparable.
6. **The split definition: 14 × 14 chip blocks, 7/1/1 per granule, seed 20260830, 2560 m
   buffer, 36SXJ held out whole.** A rerun with a different seed produces a different corpus,
   and its metrics may not be compared with these.
7. **Targets are stored; the degradation is applied at load time by
   `sr_data.degrade.degrade_chip`.** If training ever copies that function instead of
   importing it, the guarantee that the model inverts exactly what the control inverted is
   gone.
8. **Test sets are never pooled.** In-distribution blocks and 36SXJ are separate numbers
   wherever they appear.

## 12. Checks registered before they were run

Each is stated with its predicted outcome, and each is run against a known-true and a
known-false case. A check that passes on both is not a check.

| # | check | known-true | known-false | predicted |
|---|---|---|---|---|
| C1 | target is exactly 2× the input in both dimensions | a real corpus pair | a pair built with a deliberately 3× target | **true passes, false is caught** |
| C2 | no chip contains an SCL class declared not clear | a real accepted chip | a chip forced to include a class-9 (cloud) pixel | **true passes, false is caught** |
| C3 | no chip is in more than one split, and no chip lies within 2560 m of a chip in a different split | the real manifest | a manifest with one chip's split relabelled | **true passes, false is caught** |
| C4 | the degraded input is NOT byte-identical to a plain 2×2 area-average downsample | the real degradation | a degradation function replaced by a 2×2 mean | **true differs, false is identical and is caught** |

C4 is the one that matters most: if the MTF filter did nothing, every number in this work
package would still be produced, would still look reasonable, and would describe a corpus
that is not the registered one.
