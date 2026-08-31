# WP12 — a three-band 8-bit model at scale 4, for the data the institute holds

> **Numbering.** `12-qt5-uyumluluk.md` was written for later-commissioned work while this
> package was outstanding. This document keeps the name the brief asked for.

**Sections 1–8 are the registration and were written before any corpus was cut, any control
computed or any step trained.** Standing practice 4. Nothing below was revised after an
outcome was seen; if it had been, this document would say so and keep the earlier text.

## 1. Why this model exists

Mustafa Teke has confirmed the institute currently holds **8-bit RGB EOX imagery**, has no
four-band product, and will acquire 16-bit later. WP7's scale-4 four-band model already
matches that 16-bit tier when it arrives. **Nothing we hold matches the three-band 8-bit
product they have today** — `11-eox.md` §5 found only bicubic in domain, and the one model
that ran did so silently and wrongly.

## 2. D30 — the corpus is TCI, the scale is 4, the bands are three

TCI is Sentinel-2's own 8-bit three-band product on the same 10 m grid, it is on disk, and
**WP11 §3.4 measured it to be linear against reflectance at R² 0.9968 / 0.9991 / 0.9982** with
a fitted exponent indistinguishable from 1. Scale 4 because the institute's target is
10 m → 2.5 m.

## 3. D31 — the normalisation divisor is 255

`NORM_DIVISOR_DN = 255.0`, so normalised = the product's full scale. It is **a constant of the
format, not a value fitted to this corpus** — the same reasoning that put 10000 in the
four-band model (`07-x4-registration.md` §3), where 10000 is the L2A quantisation value.
`PSNR_DATA_RANGE = 1.0` accompanies it and **the two are meaningless apart**
(`07-x4-registration.md` §11.4, invariance item 8).

**A PSNR from this corpus may not be compared with any PSNR from the reflectance corpora.**
The divisor differs, and an absolute PSNR is not comparable across divisors; only a paired
margin is, and even then only when the task is the same. It is not.

## 4. D32 — chips cut fresh, split logic reused

WP0 counted TCI chips and never cut them. They are cut now with `sr_data.build_corpus`,
extended to read a single three-band TCI raster instead of three single-band files, and with
**no other change**: the same chip grid, the same SCL screening, the same clear classes.

Screening is provably identical: `tiles36SXJ/SCL.tif` and
`s2_reflectance_l2a/36SXJ_20260527/SCL.tif` are **byte-identical (sha256 equal)**, so the
clear mask cannot differ.

Then the **same two-step separation D13 established**: deduplicate across granules in map
coordinates, then buffer corpus-wide — by running `split_fix`, not by writing new code, and
scored by the existing leakage gate with its known-false.

**36TVK had no TCI on disk.** Four of the five granules did. Rather than build a corpus over
four granules and make it incomparable, 36TVK's TCI was fetched from the same public
`sentinel-cogs` route WP2A documented, item `S2C_36TVK_20260430_0_L2A`, 357,158,743 bytes.

### 4.1 Registered prediction — the chip counts

> **The split will be identical to the reflectance corpus's corrected v2 split:
> train 3320 / val 422 / test 457 / heldout 1332.**
>
> The reasoning is that the chip grid, the granules and the SCL screening are all identical,
> and only the pixel source differs. **Falsified by any different count.** If the counts
> differ, something other than the pixel source changed and the corpus is not what this
> registration describes.

> **The leakage gate will report 0 violations, and its known-false will reproduce WP3A's 47.**

## 5. D33 — the residual domain gap, stated and not closed

TCI is linear. The EOX product the institute holds is, on WP11's evidence, most likely the
**Viewing tier**, which EOX's own documentation calls *tonemapped* — "scaled to 0-255, color
corrected and contrast adjusted (and even sharpened)".

> **A TCI-trained model is much closer to that than anything we hold, and it is still not in
> domain.** It is trained on a linear product and would be applied to a non-linear one.

### 5.1 What is tested, and the registered expectation

WP11's regression of EOX against reflectance returned R² ≈ 0, because a 2024 annual mosaic and
a 2026-05-27 scene disagree about phenology, not about radiometry. A **rank-based** statistic
is therefore used instead of a regression on values:

- **Spearman rank correlation** between EOX and TCI over the same ground, and
- a **quantile–quantile comparison** of the two distributions over a large common footprint.

> **Registered expectation: the relationship is monotonic but not linear — a curved Q-Q,
> with Spearman materially above Pearson.** That is the signature of a tone curve.
>
> **Falsified** by a straight Q-Q line, which would mean EOX's tone curve equals TCI's, or by
> a Spearman no better than Pearson, which would mean the date mismatch dominates and the test
> settles nothing.

**The confound is registered with the test:** a seasonal difference changes the underlying
distribution of the landscape, so a curved Q-Q may be phenology rather than tone mapping.
**What would settle it: an EOX Exploitation tile over ground for which we hold Sentinel-2 of
the same date range.** That product is behind a 404 sample portal and a paid licence.

## 6. D34 — the rules from WP7 and WP8 carry over

1. **A parameter that can vary has no default.** `scale`, `bands` and the divisor are passed
   explicitly at every call. WP7 found seven defects of exactly this shape.
2. **Band order is written into the provenance and asserted wherever the model is loaded**, with
   a known-false that swaps two bands.
3. **Any caveat shipped with the model is derived from the configuration, never a literal.**
   WP7 shipped a scale-4 model carrying "20 m → 10 m" text because the caveat was hard-coded.
4. **Registration before outcomes; the two test sets are read once, at the end; selection on
   validation only.**
5. **The registered numbers come from the ONNX-on-CPU path**, the artefact that ships, once it
   agrees with PyTorch inside the registered tolerance.

## 7. Registered schedule and predictions

| | |
|---|---|
| variant name | `tci` — `GENCP_SR_VARIANT=tci` |
| scale | 4; input 64 px, target 256 px |
| bands | 3, **`B02,B03,B04`** in that order, matching TCI's own band order |
| divisor | **255.0**; `PSNR_DATA_RANGE` 1.0 |
| schedule | **20,000 steps**, batch 32, matching WP7 so optimisation effort is comparable |
| budget | set from a probe **with a margin of at least 3x**, because WP3B and WP7 both found a short probe overstates sustained throughput (`11-zamanlama.md` §5) |

**Predictions, before measurement:**

| # | prediction | falsified by |
|---|---|---|
| P1 | bicubic control PSNR on `test` lands in **22–30 dB** in `DN/255` units | anything outside |
| P2 | the model's paired margin over that control is **positive on both test sets**, in **+1 to +5 dB** | a negative or larger margin |
| P3 | ONNX-on-CPU agrees with PyTorch to **< 1e-4** normalised | anything larger |
| P4 | in the WP8 matching experiment the model yields **more RANSAC inliers and lower `rmse_truth`** than bicubic on the held-out granule | either reversed |
| P5 | the matching margin is **smaller than the four-band model's**, because 8-bit input carries less headroom than 16-bit reflectance | a larger margin |

## 8. Invariance — what must not change for these numbers to mean what they claim

1. `NORM_DIVISOR_DN = 255.0` **and** `PSNR_DATA_RANGE = 1.0`, quoted together, always.
2. `BANDS = ("B02","B03","B04")` in that order, in the stored array and in the provenance.
3. `SCALE = 4`, `CHIP_PX = 256`, input 64 px.
4. The corpus is TCI, screened by the same SCL, on the same chip grid, split by `split_fix`.
5. Test sets read once, at the end; selection on `val` only.
6. **No number here is compared with a number from the reflectance corpora.** Different
   product, different divisor, different task.
7. The matching experiment uses WP8's pipeline, detector and parameters unchanged, with the
   oracle and bicubic arms **recomputed on this corpus**.

---

# Results

## 9. The corpus — and a registered prediction that failed

**§4.1 predicted the split would be identical to the reflectance corpus's. It is not.**

| | train | val | test | heldout | total |
|---|---|---|---|---|---|
| **TCI (this corpus)** | **2656** | **377** | **380** | **740** | **4153** |
| reflectance v2, predicted | 3320 | 422 | 457 | 1332 | 5531 |

**The mechanism, reported rather than tuned away.** Screening has two rules and the
registration reasoned about only one. The SCL clear-mask *is* byte-identical, as claimed. The
second rule — reject any chip containing a pixel equal to the nodata sentinel **0** — does not
transfer between products. In uint16 reflectance 0 is a rare sentinel; in 8-bit TCI,
quantisation puts genuinely dark pixels (deep shadow, water) at 0 far more often. Rejections
rose accordingly: 36SXJ 902, 36TVK 723, 36TUK 594, 36SVJ 362.

**Nothing was retuned to recover the prediction.** The rule is the one WP3A registered and it
stayed. The consequence is a smaller corpus, and in particular **a held-out granule of 740
chips instead of 1332**, which makes §13's matching result less precise than WP8's.

36TVK had no TCI on disk; it was fetched from the public `sentinel-cogs` route WP2A
documented, item `S2C_36TVK_20260430_0_L2A`, **357,158,743 bytes**, so the corpus spans the
same five granules.

**Per granule after the D13 correction:**

| granule | train | val | test | heldout |
|---|---|---|---|---|
| 36SVJ | 863 | 93 | 140 | — |
| 36SWJ | 806 | 141 | 101 | — |
| 36TUK | 523 | 47 | 54 | — |
| 36TVK | 464 | 96 | 85 | — |
| 36SXJ | — | — | — | **740** |

Cross-granule deduplication removed **157** chips (36SVJ 133, 36TVK 24).

### 9.1 Leakage — clean, with a known-false that fires on this corpus

| split | n | sharing ground with train | within 2560 m |
|---|---|---|---|
| val | 377 | **0 (0.00 %)** | **0** |
| test | 380 | **0 (0.00 %)** | **0** |
| heldout | 740 | **0 (0.00 %)** | **0** |

**Known-false on this same corpus**, the uncorrected manifest through the same implementation:
val **7 (2.41 %)**, test **33 (11.74 %)**. Non-zero before, zero after — the zero distinguishes
something.

**A defect in the gate, of the shape WP7 catalogued.** Run under this variant the gate refuses
a verdict, because its `KF2` case expects to reproduce WP3A's **47** and gets 33: `KF2`'s
expectation is a **literal tied to the reflectance corpus** and cannot hold on a different one.
The gate itself is healthy — run unchanged under `x2` it reproduces 47 exactly and KF1 and DG
pass. The measurement above uses the gate's own `load`/`leakage` functions, with the v2 `kept`
column honoured as `main()` honours it.

> **A near-miss worth recording.** My first call omitted `kept_col`, so dropped chips were
> counted and the corrected split appeared to leak *worse* than the uncorrected one (test
> 25.15 %). The figure was absurd, which is the only reason it was caught.

## 10. The bicubic control — a different corpus, so a different bar

`DN/255`, `PSNR_DATA_RANGE` 1.0, per chip, unweighted mean, never pooled.

| split | n | PSNR (dB) | SSIM | MAE |
|---|---|---|---|---|
| test | 380 | **24.8893 ± 3.056** | 0.646131 | 0.04011773 |
| heldout | 740 | **23.8169 ± 2.330** | 0.624241 | 0.04554655 |
| val | 377 | 24.2510 ± 2.658 | 0.623776 | 0.04366470 |

**This bar belongs to this corpus alone.** It may not be set beside the reflectance corpora's
controls: different product, different divisor, different chips. **P1 (22–30 dB) holds.**

*A wording slip in the tool's own output, noted not fixed: `control_v2.py` prints "normalised
reflectance DN/255". TCI is not reflectance. The number is right; the label is inherited.*

## 11. Training

| | |
|---|---|
| steps | **20,000 / 20,000**, `stop_reason = steps` |
| wall clock | 1613.6 s = **26.9 min** against a 60-minute budget |
| sustained rate | **12.39 steps/s**, against the probe's **17.40** — ratio **0.71** |
| best validation | **0.029099** Charbonnier, at step 20,000 |
| parameters | 509,552; seed 20260831; device mps |

The probe overstated throughput again, a third time, by the same factor the earlier packages
found. **The 3.1× margin absorbed it**; a 1.0× budget would have stopped this run short.

X3, the dihedral commutation check, passed before training: known-true **0.000e+00**,
known-false **1.171e+01**.

**The post-run hang recurred for the third time**, with the identical signature: `last.pt`
truncated at **8192 bytes**, process at 0.1 % CPU, size unchanged across an 8-second sample.
`best.pt` (6,144,085 bytes) and `train_record.json` were complete. Killed, fragment renamed
`last.pt.TRUNCATED`. **Three runs, three identical hangs.**

## 12. Evaluation — paired, per set, never pooled

Sign: `model − bicubic`; PSNR/SSIM positive = better, MAE negative = better. Figures are
**ONNX-on-CPU**, the artefact that ships.

**Path agreement**: test raw **2.503e-06**, heldout **2.682e-06**, both inside the registered
1e-4. **P3 holds.**

**test, n = 380**

| metric | model | bicubic | **paired** | chips worse |
|---|---|---|---|---|
| PSNR (dB) | 28.0474 | 24.8893 | **+3.158100 ± 1.178588** | 2 / 380 |
| SSIM | 0.783565 | 0.646131 | **+0.137435 ± 0.035881** | 2 / 380 |
| MAE | 0.02735957 | 0.04011773 | **−0.012758 ± 0.006076** | 2 / 380 |

**heldout, n = 740** (36SXJ, never seen in any form)

| metric | model | bicubic | **paired** | chips worse |
|---|---|---|---|---|
| PSNR (dB) | 27.1101 | 23.8169 | **+3.293153 ± 1.097909** | **0 / 740** |
| SSIM | 0.773013 | 0.624241 | **+0.148772 ± 0.029977** | **0 / 740** |
| MAE | 0.03060316 | 0.04554655 | **−0.014943 ± 0.006435** | **0 / 740** |

**P2 (+1 to +5 dB, positive on both) holds.** Edge density, diagnostic only: model 0.0194
against bicubic 0.0113 and a target of 0.0330 on test — about 59 % of the target's edge
energy where bicubic reaches 34 %.

## 13. Matching — the number that says whether the model helps

WP8's pipeline, detector, parameters, band and RANSAC settings, imported unchanged. Oracle and
bicubic arms recomputed on this corpus. 740 chips of 36SXJ, 14.8 s.

| arm | keypoints | tracked | inliers | inlier ratio | rmse_truth |
|---|---|---|---|---|---|
| oracle | 2528.9 | 2528.9 | 2528.9 | 1.0000 | 0.0000 |
| bicubic | 1538.6 | 125.4 | **122.7** | 0.0796 | **0.9908** |
| **TCI model** | 1775.4 | 466.3 | **465.0** | **0.2628** | **0.6100** |

Usable correspondences as a fraction of the oracle: bicubic **0.049**, model **0.184**.

**Paired, model − bicubic:**

| | mean ± sd | chips worse |
|---|---|---|
| keypoints | +236.81 ± 80.66 | 2 / 740 |
| **inliers** | **+342.31 ± 82.51** | **0 / 740** |
| **inlier ratio** | **+0.1832 ± 0.0489** | **0 / 740** |
| **rmse_truth** | **−0.3807 ± 0.0975** | **0 / 740** |

> **The model yields 3.79 times bicubic's usable control points and cuts the correspondence
> error by 38 %, and it is better on every one of the 740 held-out chips.** **P4 holds.**

Systematic shift is negligible for both arms — model `dx +0.0002, dy +0.0019` px, bicubic
`dx −0.0007, dy −0.0047` — unlike wsx4's −0.25 px in `08-eslestirme.md` §16.

### 13.1 What may and may not be compared with WP8's four-band figures

| | WP8 four-band (n=1332) | WP12 TCI three-band (n=740) |
|---|---|---|
| inliers, model / bicubic | 478.6 / 126.9 = **3.77×** | 465.0 / 122.7 = **3.79×** |
| fraction of oracle | 0.198 | 0.184 |
| paired inliers | +351.81 | +342.31 |
| paired inlier ratio | +0.1885 | +0.1832 |
| paired rmse_truth | −0.3682 | **−0.3807** |

**These may be compared only in kind, not as a controlled experiment.** The matching metrics
are geometric — counts and pixel distances — so unlike PSNR they carry no radiometric unit and
are not invalidated by the different divisor. But **the corpora differ** (TCI against
reflectance), **the products differ** (8-bit tonemapped-linear against 16-bit reflectance), and
**the held-out sets differ in size and membership** (740 against 1332 chips of the same
granule, screened by a rule that rejects differently). Nothing here isolates band count or bit
depth.

**P5 is mixed, and is reported as such rather than read favourably.** It predicted a *smaller*
margin than the four-band model's. On counts it is smaller (+342.3 against +351.8 inliers,
+0.1832 against +0.1885 ratio). **On localisation it is larger** (−0.3807 against −0.3682), and
the ratio to bicubic is marginally higher (3.79× against 3.77×). The prediction's direction is
not consistently confirmed.

## 14. D33 — the monotonicity test, and the expectation it falsified

**Registered expectation: Spearman materially above Pearson. FALSIFIED.**

| band | Pearson r | Spearman rho | rho − r |
|---|---|---|---|
| R | −0.1474 | −0.1775 | **−0.0301** |
| G | +0.1416 | +0.0312 | **−0.1105** |
| B | +0.2466 | +0.1383 | **−0.1083** |
| grey | +0.0525 | −0.0269 | −0.0793 |

Spearman is **below** Pearson on every band. The date mismatch scrambles the *ranks* as well as
the values: a parcel that is bright bare soil in the 2024 mosaic is dark green crop in the
2026-05-27 scene, so its rank moves as much as its value. **A rank statistic does not rescue
this comparison, and the registration was wrong to expect it would.**

**The quantile–quantile comparison does carry evidence**, over 244,481 valid pixels of a
5120 m window:

| quantile | EOX | TCI | EOX/TCI |
|---|---|---|---|
| 1 % | 71.3 | 21.7 | **3.29** |
| 10 % | 93.0 | 30.3 | 3.07 |
| 50 % | 125.0 | 95.7 | 1.31 |
| 90 % | 162.0 | 165.7 | 0.98 |
| 99 % | 202.3 | 219.0 | **0.92** |

A straight line fits with slope 0.5715 and intercept 70.77, deviating by up to **13.0 DN**
(R² 0.973). **TCI's 1st percentile is 21.7; EOX's is 71.3 — EOX has essentially no dark
pixels.** A three-fold lift of the entire lower quartile with mild highlight compression is a
**black-point lift**, which is a tone-curve operation.

**Not settled, and the confound stands.** A seasonal difference changes which pixels are dark,
so part of the curve is phenology. What separates the two: **an EOX Exploitation tile over
ground for which we hold Sentinel-2 of the same date range** — behind a 404 sample portal and,
for commercial use, a paid licence.

## 15. The shipped artefact

`tubitak/data/plugin_models/gencp_sr_tci_x4_b3.onnx`, **2,047,228 bytes**, opset 17,
sha256 `e6fd9b6216461b4a268286e548a12d8202a34d523e7c02c4767db13af6afbbfe`, declared input
`['batch', 3, 'height', 'width']`.

Provenance, **derived from the configuration and not written as literals** (D34):
`band_order B02,B03,B04`, `norm_divisor_dn 255.0`, `scale_factor 4`, `output_layout … 4x
spatial`, `completed_steps 20000`, `stop_reason steps`, `train_seed 20260831`, and the caveat
*"Trained by the Wald protocol 40m->10m and applied 10m->2.5m …"* — the scale and both ground
distances derived, which is the WP7 defect that shipped inside a model.

**X6, ONNX against PyTorch**, three input sizes including one not a multiple of 8:

| input | output | max abs diff |
|---|---|---|
| 64 | 256² | 2.265e-06 |
| 96 | 384² | 2.384e-06 |
| 100 | 400² | 2.801e-06 |

## 16. Applied to the EOX sample — illustration, not measurement

> **There is no ground truth for an EOX mosaic. Nothing in this section is a measurement of
> quality, and no number is claimed from it.**

The EOX chip of `11-eox.md` was fed to this model. **The band order was reversed first**: EOX
serves **R,G,B** and the model declares **B02,B03,B04**, so feeding it directly would reverse
the channels — the fault WP11 caught in the x2 model.

The domain distance is the point:

| | normalised median |
|---|---|
| TCI training data | **0.4482** |
| EOX sample | **0.4706** |

**The same domain**, against WP11 where the x2 model saw input five times darker than anything
it trained on. Output ranged **−1.3 to 273.6** DN — a slight overshoot at both ends, consistent
with an unclipped model, and no stretch of any kind was needed to display it.

`eox_tci_model_x4.png` — left EOX input (nearest ×4), middle bicubic ×4, right the model ×4.
**All three with no stretch, 0–255 as produced**; the model panel is clipped to 0–255 for
display only. The model panel is visibly sharper at field boundaries and tracks, with natural
colour and no visible artefacts.

**What is still not claimed.** EOX Viewing is tonemapped and, by EOX's own documentation,
sharpened; this model is trained on linear TCI. It is much closer to in domain than anything
held before — §14's evidence says the tone curve differs — and it is **still not in domain**.
The figure shows what the model does to that imagery. It does not show that the result is
correct.

## 17. Predictions, scored

| # | prediction | outcome |
|---|---|---|
| §4.1 | split identical to the reflectance corpus | **FALSIFIED** — the nodata-DN rule does not transfer (§9) |
| §4.1 | leakage 0, known-false reproduces 47 | **half** — leakage 0 confirmed; KF2's 47 is a corpus-specific literal (§9.1) |
| P1 | control on test in 22–30 dB | **HOLDS** — 24.8893 |
| P2 | paired margin positive, +1 to +5 dB | **HOLDS** — +3.158 test, +3.293 heldout |
| P3 | ONNX agrees with PyTorch < 1e-4 | **HOLDS** — 2.5e-06 |
| P4 | more inliers and lower rmse than bicubic | **HOLDS** — 3.79×, 0/740 worse |
| P5 | margin smaller than the four-band model's | **MIXED** — smaller on counts, larger on localisation (§13.1) |

## 18. Open items

1. **The nodata-DN screening rule does not transfer between products** and cost this corpus
   1378 chips relative to the prediction. Whether an 8-bit product should use a different rule
   is a registration question, not a tuning one, and is not decided here.
2. **`leakage.py`'s KF2 expectation is a corpus-specific literal** and fires spuriously on any
   new corpus (§9.1).
3. **The post-run hang is now three-for-three** and remains undiagnosed.
4. **The probe overstated sustained throughput a third time**, ratio 0.71 here.
5. **The tone-curve question is unsettled** (§14) and needs a same-date Exploitation tile.
6. **`control_v2.py` prints "reflectance" for a product that is not reflectance** (§10).
