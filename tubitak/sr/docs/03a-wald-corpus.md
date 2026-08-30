# Project 2, WP3A — the Wald training corpus and its registered control

**Run:** 2026-08-30. **Repository:** `mvy0502/GenCP`, branch `tubitak-tr`, HEAD `33d8da1`.
**No training was run. Nothing was uploaded to Kaggle. No package was installed. No imagery
was downloaded.** What this work package produced is a registered corpus and a registered
control baseline, both of which exist before any model does.

**Concurrency.** A second session was building the QGIS plugin under `tubitak/sr/sr_plugin/`
throughout. This work package wrote only under `tubitak/sr/sr_data/`, `tubitak/sr/docs/` and
`tubitak/data/`. `tubitak/sr/sr_core/` was imported and never modified; nothing under
`tubitak/sr/sr_plugin/` was read for modification or written. No `git add`, `git commit`,
`git checkout` or `git stash` was run.

**Machine and environment.** MacBook Pro, Apple M4 Max, 14 cores, 36 GB. Python 3.11.15
(`/opt/homebrew/Caskroom/miniforge/base/envs/gencp/bin/python`).

**Library versions that affect numerics** — recorded per standing practice 9 and embedded in
`corpus.json` and both evidence JSONs:

| library | version | what it does here |
|---|---|---|
| numpy | 2.4.6 | all array arithmetic, the degradation kernel |
| scipy | 1.17.1 | `gaussian_filter`, inside SSIM only |
| rasterio | 1.4.4 | raster IO |
| GDAL | 3.12.3 | via rasterio |
| Pillow | 12.3.0 | **the bicubic resampling in the control baseline** |
| scikit-image | **absent** | not installed; SSIM is implemented locally, see §4 |

**Random seed: 20260830.** It is used in exactly two places: the block-to-split assignment
(`params.SPLIT_SEED`) and the RNG of the SSIM validation cases. The corpus cutting, the
degradation and the metrics contain no stochastic step.

**Wall clock**, per stage, each measured with `time.perf_counter` inside the script:

| stage | wall clock | peak RSS |
|---|---|---|
| D7 radiometry diagnostic (all 5 granules, full histograms) | 14.3 s | not measured |
| corpus cut and write (6056 chips, 2.2 GB) | 10.8 s | 5.673 GB |
| bicubic control (2210 chips, 3 metrics each) | 24.2 s | not measured |
| the four corpus checks | 0.9 s | not measured |

---

## 1. The registration, exactly as registered

Written to `tubitak/sr/docs/03a-corpus-registration.md` at **13:39:33**, before a single chip was cut and before any metric was computed. Reproduced here verbatim, quoted:

> # WP3A registration — the Wald corpus and its bicubic control
>
> **Registered:** 2026-08-30, Project 2 WP3A, **before a single chip was cut and before any
> metric was computed.** Standing practice 4: predictions are registered before outcomes. The
> only measurement that preceded this file is the D7 radiometry diagnostic, which is an
> *input* measurement made to decide a conversion, and whose result is quoted in §2 below.
>
> This file is never edited to match a result. The numbers it names live in
> `tubitak/sr/sr_data/params.py` and are imported, never restated as literals, so that what
> ran is what was registered.
>
> ---
>
> ## 1. Corpus and directories, named exactly
>
> Standing practice 5. A wrong name in registration text has already caused a failed gate and
> a sign flip in this project.
>
> **Source reflectance:** `tubitak/data/s2_reflectance_l2a/<TILE>_<DATE>/{B02,B03,B04,SCL}.tif`
> — the 20 files WP2A acquired and verified against their S3 ETags (02a §3, 20/20 matched).
>
> | tile | directory | date | datatake | orbit | product ID |
> |---|---|---|---|---|---|
> | 36TVK | `36TVK_20260430` | 2026-04-30 | A008614 | R064 | `S2C_MSIL2A_20260430T083651_N0512_R064_T36TVK_20260430T140714.SAFE` |
> | 36TUK | `36TUK_20260430` | 2026-04-30 | A008614 | R064 | `S2C_MSIL2A_20260430T083651_N0512_R064_T36TUK_20260430T140714.SAFE` |
> | 36SVJ | `36SVJ_20260430` | 2026-04-30 | A008614 | R064 | `S2C_MSIL2A_20260430T083651_N0512_R064_T36SVJ_20260430T140714.SAFE` |
> | 36SWJ | `36SWJ_20260430` | 2026-04-30 | A008614 | R064 | `S2C_MSIL2A_20260430T083651_N0512_R064_T36SWJ_20260430T140714.SAFE` |
> | 36SXJ | `36SXJ_20260527` | 2026-05-27 | A009000 | R021 | `S2C_MSIL2A_20260527T082601_N0512_R021_T36SXJ_20260527T135213.SAFE` |
>
> **Corpus written to:** `tubitak/data/sr_wald_corpus/` — gitignored by `.gitignore:54`.
> **Bands stored, in this order:** B02, B03, B04 (blue, green, red).
>
> ## 2. Radiometry — D7, decided by measurement
>
> `reflectance = DN / 10000`. **The BOA offset is not applied.**
>
> Measured before this registration was written, over **every clear pixel of all five
> granules, n = 554,534,176 per band**, from a full 65536-bin histogram so percentiles are
> exact over the population rather than estimated from a subsample
> (`tubitak/sr/sr_data/checks/d7_radiometry.py`):
>
> | band | DN p1 / p50 / p99.9 | A = DN/10000: p50 | A frac < 0 | B = DN/10000 − 0.1: p50 | B frac < 0 |
> |---|---|---|---|---|---|
> | B02 | 76 / 644 / 4084 | **0.0644** | 0.0000 % | **−0.0356** | **74.7164 %** |
> | B03 | 287 / 1006 / 4663 | **0.1006** | 0.0000 % | 0.0006 | 49.5167 % |
> | B04 | 107 / 1094 / 5029 | **0.1094** | 0.0000 % | 0.0094 | 45.0807 % |
>
> A puts every band median in an ordinary land-reflectance range. B puts the blue median below
> zero and three quarters of blue pixels below zero, which is not a physical surface
> reflectance. **A is used. B is not.** The dissenting STAC `raster:bands offset: −0.1` is
> recorded as a known Element84 metadata inconsistency and is not applied.
>
> These DN percentiles reproduce WP2A §6.1 exactly, by an independent implementation over the
> same pixels. They are not independent evidence — the two read the same SCL bytes — and are
> reported as a reimplementation check.
>
> ## 3. Clear masking
>
> **Clear = SCL class in {2, 4, 5, 6, 7}**: dark area/cast shadow, vegetation, not vegetated,
> water, unclassified. **Rejected: 0** (no data), **1** (saturated/defective), **3** (cloud
> shadow), **8, 9** (cloud medium/high probability), **10** (thin cirrus), **11** (snow/ice).
>
> Why these. Cloud, cirrus, cloud shadow and snow are rejected because a super-resolution model
> should not be trained to reconstruct them, and because they are not the surface. Nodata is
> rejected because it is not data. Class 1 is rejected because a defective pixel is not a
> measurement — this differs from WP0/WP2A's screen, which rejected `{0,3,8,9,10,11}` and so
> retained class 1; WP2A measured class 1 at exactly **0 pixels** across all five granules, so
> the two definitions select identical pixels on this corpus and the difference is only that
> this one does not depend on that population staying empty. Class 2 and class 7 are retained
> because dark ground and ground the processor declined to label are still ground.
>
> **The 20 m SCL mask is expanded to 10 m by exact 2 × 2 replication.** This is lossless only
> because the grids nest exactly, so nesting is *checked* — CRS, origin exactly equal, pixel
> size exactly 2×, dimensions exactly half — at the point the assumption is made
> (`sr_data.clear.require_nested`), not assumed at the call site. WP2A open item 4 is the
> reason origin is compared and not only CRS and shape: all five granules share EPSG:32636 and
> 10980 × 10980, so a check omitting the transform would pass every wrong pairing.
>
> ## 4. Chip geometry — D8
>
> | | |
> |---|---|
> | target chip | **256 × 256 at 10 m** = 2560 m square |
> | Wald input | **128 × 128 at 20 m**, produced in the dataloader, never stored |
> | factor learned | **2** |
> | stride | **256 px** — chips are non-overlapping and share no pixel |
> | chips per granule | 10980 // 256 = 42, so **42 × 42 = 1764** candidates |
> | stored dtype | **uint16 DN**, shape (N, 3, 256, 256) |
>
> **Minimum clear fraction per chip: 1.0.** Every SCL pixel over the chip footprint must be
> clear. Not 0.99: the loss is computed per pixel, so a chip that is 99 % clear asks the
> network to reconstruct 1 % of pixels that are cloud or nodata, and requiring 1.0 removes the
> need for a per-pixel loss mask, which is one fewer thing to get wrong. With ~7000 candidates
> and no shortage, strictness is free.
>
> **A chip is additionally rejected if any B02/B03/B04 pixel equals 0.** This settles WP2A
> open item 2: DN 0 is simultaneously the declared nodata sentinel and a legal reflectance, and
> the encoding cannot distinguish them. WP2A measured 3,443 / 568 / 1,290 pixels per band that
> SCL calls clear yet store 0. Rejecting the chip removes the ambiguity from the corpus rather
> than carrying it into a loss function.
>
> **The WP4 inference tile contract, recorded so it is not rediscovered.** The trained network
> consumes 128 source pixels, because its input is the 20 m image; WP1's bicubic path tiles the
> source at 512. Overlap stays 32 source pixels. Computed with `sr_core.tiles.tile_grid` on a
> 10980² granule:
>
> | path | tile | overlap | stride | tiles |
> |---|---|---|---|---|
> | WP1 bicubic, `sr_core` default | 512 | 32 | 480 | 23 × 23 = **529** |
> | WP4 ONNX, D8 contract | **128** | 32 | 96 | 115 × 115 = **13,225** |
>
> **25.0× more tiles**, and each carries a network forward pass rather than a PIL resize. A
> note on the brief: it describes WP1's bicubic tile as 256; `sr_core.tiles.DEFAULT_TILE_PX` is
> 512, and 529 is the figure at 512. At 256 the count would be 49 × 49 = 2,401. The 529 the
> brief asks to compare against is the 512 figure, so 512 is what is compared.
>
> ## 5. Degradation — D9
>
> **MTF-matched Gaussian low-pass, then decimation by two.** Not a plain resize.
>
> **Target modulation at the 20 m Nyquist frequency: 0.3.** This is a stated *argument*
> (`params.MTF_AT_NYQUIST`), not a constant baked into code; changing it is a corpus
> regeneration.
>
> **Derivation of the sigma** — shown rather than copied:
>
> ```
> A Gaussian PSF of standard deviation s source pixels has, normalised to 1 at DC,
>     MTF(f) = exp(-2 * pi^2 * s^2 * f^2),     f in cycles per source pixel.
> The decimated grid samples every `scale` source pixels, so
>     f_nyq = 1 / (2 * scale) = 0.25 cycles/source px   (= 0.025 cycles/m at 10 m)
> Setting MTF(f_nyq) = m and solving:
>     s = sqrt( -ln(m) / (2 * pi^2 * f_nyq^2) )
> For m = 0.3, scale = 2:
>     s^2 = 1.2039728043259361 / (2 * 9.869604401089358 * 0.0625)
>         = 1.2039728043259361 / 1.2337005501361697 = 0.9759053...
>     s   = 0.987878331000285 source px = 9.8788 m
> Verification: exp(-2*pi^2*s^2*0.0625) evaluates to exactly 0.3.
> ```
>
> **Kernel and phase.** The kernel is truncated at 4 sigma (radius 4 source px, 8 taps) and
> renormalised to sum to 1. Decimation samples at the **centre of each 2 × 2 source block**, so
> the 20 m grid nests exactly inside the 10 m grid under the same half-pixel-centre convention
> WP1's Gate S asserts. Because a block centre falls at a half-integer source coordinate, the
> Gaussian is evaluated at half-integer offsets: output `j` is `sum_o k[o] * src[2j + o]` with
> `k[o] proportional to exp(-0.5 * ((o - 0.5) / s)^2)` over integer offsets
> `o in [-3, 4]`. The kernel is symmetric about `o = 0.5`, which *is* the block centre.
>
> ### What this makes the model learn, and the assumption underneath it
>
> The model learns to invert **a Gaussian blur of sigma 0.9879 pixels followed by 2×
> decimation, measured between a 20 m image and a 10 m image.** It is then applied between a
> 10 m image and a 5 m image.
>
> **The assumption, in words, because it must not be left implied by the code: the
> sensor's modulation transfer function is assumed to bear the same relationship to the
> sampling grid at 10 m → 5 m as it does at 20 m → 10 m — that is, the imaging system is
> assumed scale-invariant over a factor of two in ground sample distance.**
>
> This is false in general. A real instrument's MTF is fixed by its optics, detector pitch and
> platform motion; it does not rescale when you pretend the pixels are a different size. The
> 20 m image produced here is a *simulation* of a coarser Sentinel-2, not a real one, and the
> real 10 m Sentinel-2 image the model is applied to has its own, different MTF. **This
> assumption is unverifiable with the data in this project** — nothing on this machine is real
> imagery finer than 10 m over these footprints (`00-recon.md` §3.3) — and it is the standard
> and load-bearing core of the Wald protocol rather than a defect peculiar to this work.
>
> It is registered here so that no result from WP3B or WP4 can be presented as though the
> 5 m output had been validated. It has not been and, with this corpus, cannot be.
>
> **Only one corpus is built.** No second MTF value is produced now.
>
> ## 6. Storage — D10
>
> **Targets only. The degradation happens in the dataloader**
> (`sr_data.degrade.degrade_chip`), so training imports the same function the control baseline
> uses. This halves storage, removes any possibility of drift between a corpus-time and a
> train-time degradation, and guarantees one implementation of the thing the model is learning
> to invert.
>
> Chips are stored as one uncompressed `.npy` shard per split, `uint16`, shape
> `(N, 3, 256, 256)`, plus one manifest CSV per corpus carrying for every chip: granule, chip
> row and column, the UTM easting/northing of its north-west corner, its affine transform, its
> split, and its clear fraction.
>
> ## 7. Normalisation — D12
>
> **normalised = DN / 5000.0**, equivalently **reflectance / 0.5**. One constant, common to all
> three bands. Fixed corpus-wide, identical at training and at inference. No per-image
> percentile stretch of any kind.
>
> Justification. A model deployed offline on board cannot have its output depend on the
> statistics of the scene in front of it, so the constant must be chosen once from the corpus
> and then frozen. WP2A measured the pooled p99.9 of clear pixels at 4084 / 4663 / 5029 DN
> against a corpus maximum of 20703. Dividing by 5000 DN maps the brightest band's p99.9 to
> 1.006 — essentially unity — so about 99.9 % of clear-land signal lands in [0, 1] while the
> headroom above 1 remains real rather than clipped away, and the divisor is exactly
> reflectance / 0.5, a round physical number rather than a fitted one. **No clipping is applied
> anywhere in the corpus or the control**; whether a model clips its output is a WP3B decision.
>
> A single constant rather than one per band is deliberate: per-band scaling rescales the
> colour relationships between B02, B03 and B04, and those relationships are what the
> downstream matching stage keys on. The cost is that blue, whose p99.9 is 4084, uses less of
> the nominal range than red; that is accepted and stated rather than optimised away.
>
> WP2A §6.2 measured per-granule medians spreading by ~1.6× in every band. A global constant is
> therefore *not* centred on any individual granule, by construction. That is the intended
> behaviour: the alternative — per-granule normalisation — would make the model's output depend
> on which granule it was told it was looking at.
>
> ## 8. Splits — D11
>
> **Geographic, never random.**
>
> * Each granule's 42 × 42 chip grid is partitioned into **blocks of 14 × 14 chips**
>   (35,840 m square). 42 = 3 × 14 exactly, so a granule is **3 × 3 = 9 blocks** with no
>   ragged remainder.
> * Within each of the four training granules, the 9 blocks are assigned **7 train, 1 val,
>   1 test**, by a permutation seeded with `SPLIT_SEED = 20260830`. Four granules give
>   **28 train, 4 val, 4 test** blocks.
> * **Buffer: 2560 m** — one full chip width. Any chip lying within 2560 m of a chip assigned
>   to a *different* split is **dropped from the corpus entirely**, not reassigned. Chips do
>   not overlap, so this guards against spatial autocorrelation between neighbours rather than
>   against shared pixels.
> * **`36SXJ` is held out whole.** Every one of its accepted chips forms a second test set and
>   none of it enters train or val.
>
> **Why 36SXJ.** WP2A established that four of the five granules are one datatake — A008614,
> orbit R064, fourteen seconds apart — so this corpus contains **two acquisition conditions,
> not five**. 36SXJ is the only granule from the other one (2026-05-27, orbit R021, 27 days
> later). It is also the morphologically distinct site, Cappadocia tuff badlands.
>
> **What holding out 36SXJ tests:** transfer to an unseen acquisition — different date,
> different illumination geometry, different orbit — and simultaneously to an unseen landform.
> **What it does not test, and cannot:** those two factors are **confounded** and this corpus
> cannot separate them. A drop in performance on 36SXJ is not attributable to either one
> alone. It also does not test transfer to a different sensor, a different season beyond four
> weeks, a different climate zone, or a different atmospheric state. Holding out any of the
> other four granules would have tested *less*, because it would have left the model with three
> granules from the identical datatake and asked it to generalise fourteen seconds.
>
> **Reporting rule: the in-distribution test blocks and the held-out granule are reported
> ALWAYS SEPARATELY and NEVER POOLED**, in WP3A, WP3B and WP4. They measure different things
> and a pooled number would mean neither.
>
> ## 9. Metrics, and the one convention
>
> **Domain: normalised reflectance, `DN / 5000.0`, float32, dimensionless. Not DN. Not 8-bit.
> Not decibels of DN.** Every metric below is computed in that domain, on unclipped values.
>
> **Convention, stated once and never flipped: every metric is computed PER CHIP, and the
> reported figure is the UNWEIGHTED ARITHMETIC MEAN over the chips of that split.** Not pooled
> over all pixels of a split. A pooled MSE would let one large-error chip dominate; a per-chip
> mean weights every chip equally, which is what "how well does it do on a scene" means.
>
> | metric | definition |
> |---|---|
> | **PSNR** | per chip: `10 * log10(R^2 / MSE)` with `R = 1.0` (the nominal full scale of the normalised domain) and MSE taken over all 3 × 256 × 256 values of the chip; then the mean over chips. Reported in dB. |
> | **SSIM** | per chip: computed per band on the 256 × 256 plane with an 11 × 11 Gaussian window, sigma 1.5, `K1 = 0.01`, `K2 = 0.03`, data range 1.0 (Wang et al. 2004); the three per-band SSIMs averaged to give the chip's SSIM; then the mean over chips. |
> | **MAE** | per chip: mean `abs(pred - target)` over all 3 × 256 × 256 values, in normalised units; then the mean over chips. |
>
> `scikit-image` is not installed in this environment and no package was installed, so SSIM is
> implemented in `sr_data.metrics` and is validated against its own known-true and known-false
> cases rather than against a reference implementation. That is a weaker check than a
> cross-implementation comparison and is recorded as such.
>
> ## 10. The registered bicubic control
>
> Computed **before any model exists**, on both test sets separately:
>
> > degraded 128 × 128 input → `sr_core.upsample.BicubicUpsampler(scale=2)` → 256 × 256
> > prediction, compared against the 256 × 256 target.
>
> The upsampler is WP1's, imported read-only and unmodified. It runs on float32 normalised
> values, where it does not clip (`sr_core.upsample` clips integer dtypes only), so the control
> carries no clipping decision.
>
> **These three numbers per test set are the bar WP3B has to clear. They are registered now
> precisely so that the bar cannot move after a model's numbers are seen.** A trained model
> that does not beat bicubic on the in-distribution test set has not learned the task; one that
> beats it there and not on 36SXJ has learned the acquisition, not the physics.
>
> ## 11. Invariance — what must not change for this corpus to mean what we claim
>
> Standing practice 1.
>
> 1. **The five product IDs in §1.** They are the demonstrated source of the bytes, not a
>    plausible reconstruction (WP2A §1.2, byte-level ETag proof). A different processing
>    baseline would change the radiometry that D7 settles.
> 2. **`DN_TO_REFLECTANCE = 1/10000` with no offset.** If a future product has
>    `boa_offset_applied: false`, D7's conclusion does not transfer and the diagnostic must be
>    re-run, not assumed.
> 3. **`CLEAR_CLASSES = {2,4,5,6,7}` and `MIN_CLEAR_FRACTION = 1.0`.** Loosening either changes
>    what "clear" means in every count and every metric downstream.
> 4. **`MTF_AT_NYQUIST = 0.3` and the half-integer kernel phase.** The sigma follows from the
>    first; the second is what makes the 20 m grid nest inside the 10 m grid. Changing either
>    regenerates the corpus and invalidates every metric measured on the old one.
> 5. **`NORM_DIVISOR_DN = 5000.0`, one constant for three bands.** Every metric in §9 is in
>    these units; a different divisor rescales MAE linearly and moves PSNR by
>    `20*log10(ratio)`. Numbers from two divisors are not comparable.
> 6. **The split definition: 14 × 14 chip blocks, 7/1/1 per granule, seed 20260830, 2560 m
>    buffer, 36SXJ held out whole.** A rerun with a different seed produces a different corpus,
>    and its metrics may not be compared with these.
> 7. **Targets are stored; the degradation is applied at load time by
>    `sr_data.degrade.degrade_chip`.** If training ever copies that function instead of
>    importing it, the guarantee that the model inverts exactly what the control inverted is
>    gone.
> 8. **Test sets are never pooled.** In-distribution blocks and 36SXJ are separate numbers
>    wherever they appear.
>
> ## 12. Checks registered before they were run
>
> Each is stated with its predicted outcome, and each is run against a known-true and a
> known-false case. A check that passes on both is not a check.
>
> | # | check | known-true | known-false | predicted |
> |---|---|---|---|---|
> | C1 | target is exactly 2× the input in both dimensions | a real corpus pair | a pair built with a deliberately 3× target | **true passes, false is caught** |
> | C2 | no chip contains an SCL class declared not clear | a real accepted chip | a chip forced to include a class-9 (cloud) pixel | **true passes, false is caught** |
> | C3 | no chip is in more than one split, and no chip lies within 2560 m of a chip in a different split | the real manifest | a manifest with one chip's split relabelled | **true passes, false is caught** |
> | C4 | the degraded input is NOT byte-identical to a plain 2×2 area-average downsample | the real degradation | a degradation function replaced by a 2×2 mean | **true differs, false is identical and is caught** |
>
> C4 is the one that matters most: if the MTF filter did nothing, every number in this work
> package would still be produced, would still look reasonable, and would describe a corpus
> that is not the registered one.

---

## 2. D7 — both conversions, measured

Path: `tubitak/sr/sr_data/checks/d7_radiometry.py`, evidence
`tubitak/data/sr_wald_corpus/evidence/d7_radiometry.json`. Run at 13:37:14, before the
registration was written at 13:39:33 — it is an *input* measurement made to decide a
conversion, which standing practice 4 permits ahead of registration precisely because no
outcome depended on it.

**Sample, stated exactly.** Every clear pixel of all five granules, where clear means the
pixel's own SCL class is in {2, 4, 5, 6, 7}, expanded from 20 m to 10 m by exact 2 × 2
replication. **n = 554,534,176 per band.** Statistics come from a full 65536-bin histogram of
the whole population, so the percentiles are exact integers over every pixel rather than
estimates from a subsample.

| granule | clear 10 m pixels |
|---|---|
| 36TVK | 116,870,656 |
| 36TUK | 109,505,980 |
| 36SVJ | 120,557,412 |
| 36SWJ | 87,483,140 |
| 36SXJ | 120,116,988 |
| **total** | **554,534,176** |

### Both conversions on the same pixels

| band | DN p1 | DN p50 | DN p99.9 | **A** p1 | **A** p50 | **A** p99.9 | **A** frac < 0 | **B** p1 | **B** p50 | **B** p99.9 | **B** frac < 0 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| B02 | 76 | 644 | 4084 | 0.0076 | **0.0644** | 0.4084 | **0.0000 %** | −0.0924 | **−0.0356** | 0.3084 | **74.7164 %** |
| B03 | 287 | 1006 | 4663 | 0.0287 | **0.1006** | 0.4663 | **0.0000 %** | −0.0713 | 0.0006 | 0.3663 | **49.5167 %** |
| B04 | 107 | 1094 | 5029 | 0.0107 | **0.1094** | 0.5029 | **0.0000 %** | −0.0893 | 0.0094 | 0.4029 | **45.0807 %** |

`A = DN / 10000` · `B = DN / 10000 − 0.1` (the STAC `raster:bands` offset).

**Verdict: D7 confirmed, and the work proceeded on A.** Under A every band median lands
between 0.064 and 0.109 — ordinary visible-band land reflectance. Under B the blue median is
**−0.0356**, and **74.7 % of blue pixels are negative**, which is not a physical surface
reflectance. `frac < 0` under A is not merely zero but *undefined*: the dtype is uint16, so a
negative value cannot be stored.

**These DN percentiles reproduce WP2A §6.1 digit for digit**, by an independent
implementation over the same pixels — 76/644/4084, 287/1006/4663, 107/1094/5029, and the same
554,534,176 count. **This is a reimplementation check, not independent corroboration**: both
read the same SCL bytes and the same band files, so it could not have come out differently
unless one of the two had a bug. WP2A open item 3 makes the same point about its own chip
recount, and it applies here. No WP2A number is withdrawn or overwritten; both agree.

---

## 3. The corpus

Path: `tubitak/sr/sr_data/build_corpus.py`. Written to `tubitak/data/sr_wald_corpus/`.

### 3.1 Screening, per granule

A chip is accepted iff **every** SCL pixel over its footprint is clear **and** no B02/B03/B04
pixel equals 0.

| granule | candidates | accepted | rejected: not all clear | rejected: contains DN 0 |
|---|---|---|---|---|
| 36TVK | 1764 | 1283 | 283 | 198 |
| 36TUK | 1764 | 1036 | 441 | 287 |
| 36SVJ | 1764 | 1659 | 18 | 87 |
| 36SWJ | 1764 | 1122 | 642 | 0 |
| 36SXJ | 1764 | 1332 | 122 | 310 |
| **total** | **8820** | **6432** | **1506** | **882** |

The **DN-0 rejection is larger than WP2A's pixel counts would suggest** and is worth stating
plainly: WP2A measured only 3,443 / 568 / 1,290 *pixels* per band that SCL calls clear yet
store the nodata sentinel, but a single such pixel condemns an entire 65,536-pixel chip, so
882 chips — 13.7 % of all otherwise-acceptable chips — are lost to it. That is the price of
resolving WP2A open item 2 by rejection rather than by carrying the ambiguity forward, and it
is paid knowingly.

### 3.2 Splits

Definition as registered: 14 × 14 chip blocks (35,840 m), 3 × 3 = 9 blocks per granule,
**7 train / 1 val / 1 test** per granule by a seeded permutation, **2560 m buffer**,
**36SXJ held out whole**. The block assignment is recorded in `corpus.json`.

**Buffer: 376 of 6432 chips (5.8 %) were dropped** for lying within one chip of a chip in a
different split.

| granule | train | val | test | heldout | total |
|---|---|---|---|---|---|
| 36SVJ | 1251 | 110 | 166 | 0 | 1527 |
| 36SWJ | 941 | 141 | **0** | 0 | 1082 |
| 36TUK | 704 | 117 | 99 | 0 | 920 |
| 36TVK | 950 | 107 | 138 | 0 | 1195 |
| 36SXJ | 0 | 0 | 0 | 1332 | 1332 |
| **TOTAL** | **3846** | **475** | **403** | **1332** | **6056** |

### 3.3 Size and dtype

| split | chips | file | bytes | GB |
|---|---|---|---|---|
| train | 3846 | `chips_train.npy` | 1,512,308,864 | 1.512 |
| val | 475 | `chips_val.npy` | 186,777,728 | 0.187 |
| test | 403 | `chips_test.npy` | 158,466,176 | 0.158 |
| heldout | 1332 | `chips_heldout.npy` | 523,763,840 | 0.524 |
| | | `manifest.csv` | 576,519 | |
| | | `corpus.json` | 3,953 | |
| **total** | **6056** | | **2,381,897,080** | **2.382** |

**dtype `uint16`, shape `(N, 3, 256, 256)`, bands B02/B03/B04.** Under the 5 GB ceiling, so
no reduction was needed and none was chosen. The builder refuses to write above 5 GB rather
than deciding on its own what to cut.

### 3.4 A defect found, and how

**The split assignment was not deterministic, and the registration said it was.** The first
implementation seeded the per-granule RNG with `abs(hash((seed, granule)))`. Python salts
`hash()` of a `str` per process, so the assignment changed on every run. It was caught by
running `--dry-run` and the real build and comparing: **train 3747 against 3680**, from the
same code, the same data and the same registered seed, with nothing in either output saying
anything was wrong. `granule_seed` now derives the seed from SHA-256 of `"<seed>:<granule>"`,
which is stable across processes, machines and Python versions.

Verified after the fix: `assign_blocks` run in **five separate processes with
`PYTHONHASHSEED=random` produced 1 distinct assignment**, and the `--dry-run` counts now equal
the written counts exactly (3846 / 475 / 403 / 1332). The corpus reported here is from the
fixed code; the earlier arrays were deleted and rebuilt.

---

## 4. The registered bicubic control

Path: `tubitak/sr/sr_data/bicubic_control.py`, evidence
`tubitak/data/sr_wald_corpus/evidence/bicubic_control.json`. Computed at 13:44, **before any
model exists**.

**Domain: normalised reflectance, `DN / 5000.0`, float32, dimensionless.** Not DN, not 8-bit.
PSNR data range 1.0. **Convention: every metric is computed PER CHIP and reported as the
UNWEIGHTED ARITHMETIC MEAN over the chips of that split — never pooled over pixels.** Stated
once here and not varied anywhere.

The upsampler is `sr_core.upsample.BicubicUpsampler`, WP1's code, imported read-only. On
float32 input it does not clip, so the control carries no clipping decision.

### 4.1 SSIM implementation, validated before its numbers were used

`scikit-image` is absent and nothing was installed, so SSIM is implemented in
`sr_data/metrics.py` to Wang et al. (2004) — 11 × 11 Gaussian window, sigma 1.5, K1 = 0.01,
K2 = 0.03, per band then averaged over bands.

| case | SSIM | expected | |
|---|---|---|---|
| identical images | 1.000000 | exactly 1 | PASS |
| independent uniform noise | 0.007693 | near 0 | PASS |
| constant offset +0.1 | 0.982971 | < 1 | PASS |
| 4× block-replicated blur | 0.055187 | < 1 | PASS |

**This is weaker than a cross-implementation comparison and is reported as such.** It
establishes that the function is not a constant and behaves correctly at its extremes; it
does not establish agreement with `skimage.metrics.structural_similarity`.

### 4.2 The registered numbers — the bar WP3B has to clear

| split | n | PSNR (dB) | SSIM | MAE (normalised) |
|---|---|---|---|---|
| **test** (in-distribution blocks) | 403 | **31.9420** ± 3.606 | **0.863073** ± 0.0563 | **0.01798890** ± 0.009173 |
| **heldout** (36SXJ, whole granule) | 1332 | **33.0050** ± 2.614 | **0.894263** ± 0.0285 | **0.01506987** ± 0.004652 |
| val (supplementary, not a bar) | 475 | 32.2923 ± 3.333 | 0.880694 ± 0.0449 | 0.01704687 ± 0.007261 |

± is the standard deviation across chips, not a standard error. **The two test sets are
reported separately and are never pooled**, per D11.

MAE in normalised units × 5000 gives DN: **89.9 DN** on test and **75.3 DN** on the held-out
granule.

### 4.3 The held-out granule is EASIER for bicubic, not harder

36SXJ scores **1.06 dB better** in PSNR and **0.031 better** in SSIM than the in-distribution
test set. That is the opposite of the usual expectation for a held-out set and it must not be
read as evidence that generalisation is easy.

The likely cause is measurable in WP2A §6.2: 36SXJ has the **lowest p99.9 in every band** of
the five granules (B02 3279 against 36SVJ's 4136; B03 3879 against 4702; B04 4480 against
5205). Less dynamic range means less high-frequency energy, and bicubic interpolation's error
is dominated by exactly that. The held-out set is intrinsically a softer image, not a harder
task for an interpolator.

**The consequence for WP3B is concrete and needs saying now: the two bars are not
comparable to each other.** A model that beats bicubic by 2 dB on test and 1.5 dB on heldout
has not necessarily degraded — the baselines differ. Only the *margin over the bicubic
control on the same set* is meaningful, which is why the control is registered per set rather
than as a single number.

---

## 5. The four checks, each with its known-false case

Path: `tubitak/sr/sr_data/checks/corpus_checks.py`, evidence
`tubitak/data/sr_wald_corpus/evidence/corpus_checks.json`. Exit 0, **9 of 9 cases behaved as
registered.**

| check | case | outcome |
|---|---|---|
| **C1** target exactly 2× the input | known-true | **PASS** — input (3, 128, 128) → target (3, 256, 256), ratio 2 in both axes |
| | known-false | **PASS** — a deliberately 3× target (3, 384, 384) against the same input was **correctly rejected** |
| **C2** no chip contains a non-clear SCL class | known-true | **PASS** — all **6056** chips re-read from the source SCL rasters; classes present are exactly {2, 4, 5, 6, 7}; **0 violations** |
| | known-false | **PASS** — a chip footprint with one class-9 (cloud, high probability) pixel was **correctly rejected** |
| **C3** no chip in two splits, none within the buffer of another | known-true | **PASS** — 6056 chips, **0** in more than one split, **0** within 2560 m of a different split |
| | known-false | **PASS** — one train chip at 36TVK (0,5) relabelled `test` produced **2 buffer violations**, correctly detected |
| **C4** degraded input is not a plain 2 × 2 area average | known-true | **PASS** — over 64 chips, max abs difference **1.21124339** normalised = **6056 DN**; the filter does something |
| | known-false | **PASS** — with the degradation replaced by a 2 × 2 mean the difference is **exactly 0.0**, correctly identified as a no-op |
| | value | **PASS** — MTF at the 20 m Nyquist frequency evaluates to **0.3** as registered |

C2 deliberately re-reads the source SCL rasters and looks at the footprints the manifest
names, rather than trusting the builder's own bookkeeping, so an error in the screening logic
cannot hide behind the same error in the check.

### 5.1 The filter as built, not only as derived

C4's known-true establishes the filter is not a no-op; it does not establish that it is the
filter the registration names. That was measured separately:

```
kernel as built: 8 taps at integer offsets -3..+4, symmetric about offset +0.5
   -3: 0.000759423   -2: 0.016426195   -1: 0.127518320   +0: 0.355296062
   +1: 0.355296062   +2: 0.127518320   +3: 0.016426195   +4: 0.000759423
   sum = 1.0 exactly
DC gain          : degrade(constant 0.7) deviates by 2.220e-16
MTF, implemented vs analytic:
   f = 0.000  (DC)           1.000000000   vs   1.000000000
   f = 0.125  (half-Nyquist) 0.740124522   vs   0.740082804
   f = 0.250  (20 m Nyquist) 0.299970210   vs   0.300000000
   f = 0.500  (10 m Nyquist) 0.000000000   vs   0.008100000
```

**The MTF of the kernel actually in use is 0.299970210, not 0.3** — a deviation of 3.0e-5
caused by truncating the Gaussian at 4 sigma and renormalising. It is reported rather than
rounded away. The value is not tuned to hit 0.3; widening the kernel would close the gap and
would also change the corpus, so the truncation stays and the number is stated.

Context for C4's 6056 DN maximum, which is a tail rather than a typical value — the
distribution of `|MTF-degraded − area-average|` over 32 chips:

| percentile | difference (DN) |
|---|---|
| p50 | 58.09 |
| p90 | 202.79 |
| p99 | 465.92 |
| p99.9 | 914.47 |
| max | 6018.08 |
| mean | 88.71 |

---

## 6. Repository hygiene

`git status --untracked-files=all`, in full, at the end of this work package:

```
On branch tubitak-tr
Your branch is up to date with 'origin/tubitak-tr'.

Untracked files:
  (use "git add <file>..." to include in what will be committed)
	tubitak/sr/build_sr_plugin_zip.py
	tubitak/sr/docs/03a-corpus-registration.md
	tubitak/sr/sr_data/__init__.py
	tubitak/sr/sr_data/bicubic_control.py
	tubitak/sr/sr_data/build_corpus.py
	tubitak/sr/sr_data/checks/__init__.py
	tubitak/sr/sr_data/checks/corpus_checks.py
	tubitak/sr/sr_data/checks/d7_radiometry.py
	tubitak/sr/sr_data/clear.py
	tubitak/sr/sr_data/degrade.py
	tubitak/sr/sr_data/metrics.py
	tubitak/sr/sr_data/params.py
	tubitak/sr/sr_data/splits.py
	tubitak/sr/sr_plugin/__init__.py
	tubitak/sr/sr_plugin/dialog.py
	tubitak/sr/sr_plugin/metadata.txt
	tubitak/sr/sr_plugin/plugin.py
	tubitak/sr/sr_plugin/qtcompat.py
	tubitak/sr/sr_plugin/strings.py
	tubitak/sr/sr_plugin/task.py
	tubitak/sr/tests/plugin_guards.py

nothing added to commit but untracked files present (use "git add" to track)
```

**Not one path under `tubitak/data/` appears**, and that is the claim this output supports:

```
$ git status --porcelain --untracked-files=all -- tubitak/data | wc -l
       0
$ git check-ignore -v tubitak/data/sr_wald_corpus/chips_train.npy
.gitignore:54:tubitak/data/*	tubitak/data/sr_wald_corpus/chips_train.npy
$ git check-ignore -v tubitak/data/sr_wald_corpus/manifest.csv
.gitignore:54:tubitak/data/*	tubitak/data/sr_wald_corpus/manifest.csv
```

**2.382 GB of corpus is invisible to git.** No institutional imagery exists in this project
(`00-recon.md` §2.2: everything is public Copernicus, and
`tubitak/docs/paper-context-addendum.md:482` states no institutional imagery was used), and
no pixel value, thumbnail or chip appears in this report — only summary statistics.

The eight `sr_plugin/`, `build_sr_plugin_zip.py` and `tests/plugin_guards.py` entries are the
**concurrent session's work**, not this one's. They are listed because the command's full
output was requested; nothing under those paths was read for modification or written here.

---

## 7. Open items

1. **36SWJ contributes zero chips to the in-distribution test set.** Measured: its assigned
   test block (2,2) is **94.81 % SCL nodata** — the granule's south-east corner margin, part
   of the 25.4 % nodata WP2A recorded for 36SWJ. Only 6 of its 196 candidate chips are fully
   clear and all 6 fell inside the split buffer. **So the `test` set covers three of the four
   training granules and omits Tuz Gölü, the compositional-outlier site.** The split
   procedure assigns blocks without regard to how many chips survive in them; a
   yield-aware assignment, or simply re-drawing a block that yields under some minimum, would
   fix it. Not changed here because the split is registered and the corpus is built; it is a
   WP3B input and a candidate WP3A-revision if WP3B wants coverage of that site.
2. **The MTF assumption is unverifiable and load-bearing.** Registered in words in §5 of the
   registration: the model learns to invert a degradation measured between 20 m and 10 m and
   is applied between 10 m and 5 m, which assumes the imaging system is scale-invariant over
   a factor of two in GSD. It is not, in general. Nothing in this project can test it. Any
   presentation of a 5 m output must carry this.
3. **The held-out set is easier for bicubic than the in-distribution test set** (§4.3), so
   the two bars are not comparable to one another and only the margin over the control on the
   same set means anything. This is the most likely way a WP3B result gets misread.
4. **SSIM is validated only against its own extremes** (§4.1). Installing `scikit-image` and
   cross-checking `structural_similarity` on a sample of chips would upgrade this from a
   sanity check to a verification. It needs permission to install a package.
5. **882 chips (13.7 % of otherwise-acceptable chips) were lost to the DN-0 rule.** The rule
   resolves WP2A open item 2 correctly, but the cost is larger than the pixel counts implied
   and is concentrated in 36TUK (287) and 36SXJ (310). If the corpus ever needs to be larger,
   this is the cheapest place to find chips, at the price of reintroducing the
   nodata-versus-zero-reflectance ambiguity.
6. **Peak RSS during the build is 5.673 GB** because every accepted chip is held in memory
   before the per-split arrays are assembled. Fine on this machine, and it will not scale to a
   corpus twice this size. Streaming to a pre-sized memmap per split would fix it.
7. **The corpus is 2.382 GB as uncompressed `.npy`.** Kaggle upload is WP3B's problem, not
   this one's, but four files of this size are a different upload proposition from 6056 small
   ones, and that was part of why the shard format was chosen.
8. **MEASURED LEAKAGE: 47 of 403 test chips (11.66 %) share ground with a training chip
   from a different granule. The held-out granule is clean: 0 of 1332.**

   The split buffer is applied *within* a granule. `00-recon.md` measured ~9.8 km of
   footprint overlap between adjacent granules, so a train chip in one granule and a test
   chip in another can cover the same ground, and C3 does not look for it. I first wrote
   this open item as an unmeasured possibility; it is measured now, and it is real:

   | comparison | chips sharing ground with a train chip of another granule |
   |---|---|
   | `test` | **47 of 403 — 11.66 %** |
   | `val` | 27 of 475 — 5.68 % |
   | `heldout` | **0 of 1332 — 0.00 %** |

   131 overlapping chip pairs in total, between 36SWJ↔36SVJ, 36SWJ↔36TVK (train vs test) and
   36SVJ↔36TVK (train vs val). This is worse than ordinary spatial autocorrelation: the four
   April granules are **one datatake fourteen seconds apart**, so the overlapping ground is
   imaged essentially simultaneously and the two chips are near-duplicates of each other, not
   merely neighbours.

   **Consequence, stated plainly: the registered `test` bar of 31.9420 dB is measured on a
   set that is about 12 % contaminated, and a WP3B model's `test` score will be optimistic by
   an unknown amount for the same reason.** The comparison is at least like-for-like — both
   the control and any model are scored on the identical contaminated set — so the *margin*
   remains meaningful even though the absolute number is not clean.

   **The held-out granule is unaffected and is therefore the trustworthy set.** My earlier
   reasoning that 36SXJ overlaps 36SWJ by 1,074 km² is true of the granule *footprints* but
   has no chip-level consequence here, because 36SWJ's chips in that overlap strip were
   rejected by the clear screen — 36SWJ carries 25.4 % nodata concentrated at its margins.
   That is luck, not design, and it would not survive a different granule set.

   The fix is a cross-granule buffer applied in map coordinates rather than in chip indices,
   plus a fifth registered check that asserts it. Neither is done here: the corpus is
   registered and built, and changing the split now would invalidate the control numbers this
   work package exists to register. It is the first thing WP3B should decide about.
