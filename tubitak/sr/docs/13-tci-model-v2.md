# WP13 — the nodata test corrected, corpus rebuilt, model retrained

> **Numbering.** `13-cevrimdisi-kurulum.md` was written for later-commissioned work while this
> package was outstanding. This document keeps the name the brief asked for.

**This is a registered revision of WP12, not a replacement.** Nothing from WP12 is deleted,
withdrawn or overwritten. Both corpora and both models are on disk and are reported side by
side below. §11 states which is carried forward and why.

## 1. D35 — the nodata test, and why it was wrong

WP3A's rule rejects a chip if **any** band equals 0. For uint16 reflectance that is right: 0 is
a rare sentinel. For 8-bit TCI it is wrong, because quantisation to 256 levels puts genuinely
dark **land** — deep shadow, water — at 0 in one band while the others still carry signal. The
rule was rejecting dark terrain, not nodata.

**It is the sixth instance of the shape WP7 catalogued: code written for one parameter, met by
another.** Standing practice 4 permits the revision — the input measurement improved and no
model outcome had been seen when the defect was identified (WP12 §9 recorded it as a
falsified prediction at the time).

The corrected test requires **all three bands zero simultaneously**, which is how nodata is
written in this product. `sr_data.build_corpus._is_nodata()` branches on the source, so the
reflectance rule is **untouched** and WP3A, WP3B and WP7 stay reproducible.

### 1.1 Verified against a known-true and a known-false — at the second attempt

**The first known-true was wrong and is recorded rather than quietly replaced.** I nominated
36SXJ chip (0,17) and asserted it showed a contiguous nodata region. It does not: it has
**one** all-bands-zero pixel, longest contiguous run **1 px**. Checking the granules properly:

| granule | all-bands-zero, whole granule |
|---|---|
| 36SWJ | **25.36 %** |
| 36TUK | 5.65 % |
| 36TVK, 36SVJ, 36SXJ | **0.00 %** |

**Three of the five granules contain no nodata at all**, so no chip in them could have served
as a known-true. The cases come from 36SWJ:

| case | chip | measurement | old rule | corrected rule |
|---|---|---|---|---|
| **known-true** | 36SWJ (41,41) | **100 %** all-bands-zero — unambiguous nodata | rejects | **rejects** |
| **known-false** | 36SWJ (10,13) | 0 % all-bands-zero, some band at 0; band means 120.3 / 106.6 / 71.1 — valid dark land | **rejects** | **keeps** |

### 1.2 What the correction recovered

On 36SXJ alone, the old rule rejected **1008** chips and the corrected one rejects **54** —
**954 recovered**, and those 54 are isolated single black pixels rather than nodata.

| granule | nodata rejections WP12 → WP13 | accepted WP12 → WP13 |
|---|---|---|
| 36SXJ | 902 → **14** | 740 → **1628** |
| 36TVK | 723 → **10** | 758 → **1471** |
| 36TUK | 594 → **57** | 729 → **1266** |
| 36SVJ | 362 → **0** | 1384 → **1746** |
| 36SWJ | 4 → **0** | 1118 → **1122** |

Accepted before deduplication and buffering: **7233** against WP12's 4729.

## 2. The two corpora, side by side

Same D13 two-step separation both times — deduplicate across granules in map coordinates, then
buffer corpus-wide — by running `split_fix` unchanged.

| split | WP12 | **WP13** | change |
|---|---|---|---|
| train | 2656 | **3704** | +1048 |
| val | 377 | **426** | +49 |
| test | 380 | **467** | +87 |
| **heldout (36SXJ)** | 740 | **1628** | **+888** |
| total | 4153 | **6225** | +2072 |

**The held-out granule is now larger than the reflectance corpus's 1332**, because TCI carries
fewer nodata pixels than the three reflectance bands do.

**Per granule after correction (WP13):**

| granule | train | val | test | heldout |
|---|---|---|---|---|
| 36SVJ | 1020 | 117 | 168 | — |
| 36SWJ | 810 | 141 | 101 | — |
| 36TUK | 980 | 53 | 54 | — |
| 36TVK | 894 | 115 | 144 | — |
| 36SXJ | — | — | — | **1628** |

Deduplication removed **319** cross-granule duplicates (36SVJ 221, 36TVK 98), against WP12's
157.

## 3. Leakage — GATE D18 PASS, and the gate now issues a verdict

| split | n | sharing ground with train | within 2560 m |
|---|---|---|---|
| test | 467 | **0 (0.00 %)** | **0** |
| val | 426 | **0 (0.00 %)** | **0** |
| heldout | 1628 | **0 (0.00 %)** | **0** |

> **GATE D18: PASS — zero residual leakage in test and heldout, at both radii.**

Training did not start until this was true.

**Known-false on this corpus:** the uncorrected split through the same implementation gives
**47** leaking test chips and val 35 (5.79 %). Non-zero before, zero after.

### 3.1 D36 — an expected value now travels with its corpus

WP12's gate refused a verdict on a clean split, because `KF2` expected the literal **47**
measured on the reflectance corpus and got 33 on the TCI one. **The number was not changed to
fit.** `KF2_EXPECTED` is now keyed by corpus identifier: a corpus with no independently
measured expectation reports **NOT APPLICABLE**, prints what it measured, and does not fail.

Verified: under `x2` the gate still reports **"KF2 PASS - reproduces 47 exactly"**; under `tci`
it reports NOT APPLICABLE and the gate proceeds to a verdict. The case also refuses to be
vacuous — if the uncorrected split showed no leakage it reports INCONCLUSIVE, because a
known-false that cannot fire demonstrates nothing.

> **The general form, recorded as an open item: an expected value written as a bare constant
> silently becomes untestable the moment the corpus changes.** It does not announce that it has
> stopped applying; it reports a failure, which is worse, because a check that cries wolf is a
> check people learn to skip.

## 4. The bicubic control — a third corpus, a third bar

`DN/255`, `PSNR_DATA_RANGE` 1.0, per chip, unweighted mean, never pooled.

| split | n | PSNR (dB) | SSIM | MAE |
|---|---|---|---|---|
| test | 467 | **23.4509 ± 2.725** | 0.616312 | 0.04761336 |
| heldout | 1628 | **22.7840 ± 2.379** | 0.612166 | 0.05179682 |
| val | 426 | 24.0821 ± 2.709 | 0.619686 | 0.04460675 |

**The bar fell** — WP12's test control was 24.8893 and heldout 23.8169. That is expected and is
the point: the recovered chips are the dark ones, and dark terrain with low contrast is harder
for bicubic. **This bar belongs to this corpus alone** and may not be set beside WP12's, the
reflectance corpora's, or anything else.

## 5. Training

| | WP12 | **WP13** |
|---|---|---|
| steps | 20,000 / 20,000, `stop_reason = steps` | **20,000 / 20,000, `steps`** |
| wall clock | 26.9 min | **28.5 min** (budget 60) |
| probe → sustained | 17.40 → 12.39 (**0.71**) | **18.43 → 11.70 (0.63)** |
| best validation | 0.029099 | **0.029682** |
| parameters | 509,552 | 509,552; seed 20260831 |

**The probe overstated sustained throughput for the fourth time**, and by the widest margin
yet (0.63). The 3.3× budget margin absorbed it; a 1.0× budget would have stopped this run at
roughly step 12,700.

X3 passed before training: known-true **0.000e+00**, known-false **1.171e+01**.

**The post-run hang recurred — fourth consecutive run, identical signature.** `last.pt`
truncated at **8192 bytes**, process at 0.1 % CPU, size unchanged across a 10-second sample.
**Checkpoint integrity confirmed: `best.pt` sha256
`75b12b1a96c445f7f182abb497108f0a571dc6f15b84a138158165ed84dd42f0` is unchanged by the kill**,
6,144,085 bytes, and `train_record.json` is complete. Fragment renamed `last.pt.TRUNCATED`.

## 6. Evaluation — paired, per set, never pooled

Sign `model − bicubic`. Figures are ONNX-on-CPU. Path agreement: test **3.457e-06**, heldout
**3.934e-06**, both inside the registered 1e-4.

**test, n = 467**

| metric | model | bicubic | **paired** | worse |
|---|---|---|---|---|
| PSNR (dB) | 26.7244 | 23.4509 | **+3.273420 ± 1.214722** | 2 / 467 |
| SSIM | 0.772573 | 0.616312 | +0.156261 ± 0.032881 | 2 / 467 |
| MAE | 0.03194276 | 0.04761336 | −0.015671 ± 0.006209 | 2 / 467 |

**heldout, n = 1628**

| metric | model | bicubic | **paired** | worse |
|---|---|---|---|---|
| PSNR (dB) | 26.3035 | 22.7840 | **+3.519577 ± 1.110923** | **0 / 1628** |
| SSIM | 0.774090 | 0.612166 | +0.161924 ± 0.032881 | **0 / 1628** |
| MAE | 0.03346571 | 0.05179682 | −0.018331 ± 0.007881 | **0 / 1628** |

| | WP12 | **WP13** |
|---|---|---|
| paired PSNR, test | +3.158 (n=380) | **+3.273 (n=467)** |
| paired PSNR, heldout | +3.293 (n=740) | **+3.520 (n=1628)** |
| chips worse, heldout | 0 / 740 | **0 / 1628** |

**These two columns are not a controlled comparison.** The metrics are identical and the
corpora are not: WP13's includes 2072 chips WP12's excluded, and they are systematically the
darker ones. The margin grew, and part of that is that bicubic does worse on dark low-contrast
terrain — not only that the model does better.

## 7. The shipped artefact

`tubitak/data/plugin_models/gencp_sr_tci_x4_b3_v2.onnx`, **2,047,228 bytes**, opset 17,
sha256 `01496736913ac257f8f57ccb26e1c4220e903b6c309712ebcc48e0b834485920`, input
`['batch', 3, 'height', 'width']`, `work_package P2-WP13`.

**X6, ONNX against PyTorch:** 64 → **2.205e-06**, 96 → **2.384e-06**, 100 → **2.503e-06**
(the last deliberately not a multiple of 8), against a registered 1e-4.

WP12's `gencp_sr_tci_x4_b3.onnx` is **kept, not deleted**.

## 8. Matching — the reason this revision exists

WP8's pipeline, detector, parameters and RANSAC settings, imported unchanged. Oracle and
bicubic recomputed on this corpus. **1628 chips of 36SXJ**, 32.5 s.

| arm | keypoints | tracked | inliers | inlier ratio | rmse_truth |
|---|---|---|---|---|---|
| oracle | 2473.6 | 2473.6 | 2473.6 | 1.0000 | 0.0000 |
| bicubic | 1528.6 | 127.2 | **124.6** | 0.0813 | **0.9835** |
| **model** | 1775.8 | 492.7 | **491.3** | **0.2774** | **0.5917** |

Fraction of the oracle: bicubic **0.050**, model **0.199**.

**Paired, model − bicubic:**

| | mean ± sd | worse |
|---|---|---|
| keypoints | +247.20 ± 83.41 | 4 / 1628 |
| **inliers** | **+366.68 ± 86.54** | **0 / 1628** |
| **inlier ratio** | **+0.1961 ± 0.0505** | **0 / 1628** |
| **rmse_truth** | **−0.3918 ± 0.0919** | **0 / 1628** |

> **The model yields 3.94 times bicubic's usable control points and cuts correspondence error
> by 40 %, and it is better on every one of the 1628 held-out chips.**

Systematic shift is negligible for both arms — model `dx +0.0029, dy −0.0061` px, bicubic
`dx +0.0025, dy −0.0057`.

### 8.1 Beside WP12, and what may be compared

| | WP12 (740 chips) | **WP13 (1628 chips)** |
|---|---|---|
| model inliers | 465.03 | **491.29** |
| model inlier ratio | 0.2628 | **0.2774** |
| model rmse_truth | 0.6100 | **0.5917** |
| bicubic inliers | 122.72 | 124.61 |
| bicubic rmse_truth | 0.9908 | 0.9835 |
| **model / bicubic** | **3.79×** | **3.94×** |

**What may be compared: the metrics.** They are geometric — counts and pixel distances — and
both runs used the same pipeline, detector, parameters, band and seed on the same granule.

**What may not: the two as a controlled experiment.** The held-out sets differ in size *and
membership* — WP13's 1628 chips are WP12's 740 plus 888 that the old rule wrongly excluded,
and those are systematically darker. Both arms shift slightly (bicubic 122.7 → 124.6), so the
change in the ratio is not attributable to the model alone. **The right reading is that
WP13's number is measured on the whole granule and WP12's on 45 % of it**, and the whole
granule is the one to quote.

## 9. EOX application — illustration, regenerated from the shipped artefact

> **There is no ground truth for an EOX mosaic. This is illustration, not measurement, and no
> quality is claimed from it.** The caveat travels with the figure.

`eox_tci_v2_model_x4.png` — left EOX input (nearest ×4), middle bicubic ×4, right the **WP13**
model ×4. **All three with no stretch, 0–255 as produced**; the model panel is clipped to
0–255 for display only.

Band order reversed on input, as in WP12: EOX serves **R,G,B**, the model declares
**B02,B03,B04**.

| | |
|---|---|
| EOX input, normalised median | **0.4706** |
| TCI training median | **0.4482** |
| model output range | 0.7 – 276.5 DN |
| difference from the WP12 model on the same input | mean **1.52 DN**, max 20.3 DN |

The two models disagree by about 1.5 DN on average on this image — visually indistinguishable,
which is worth stating plainly: **the corpus correction mattered for the measurement, not
visibly for this one picture.**

**Still not in domain.** EOX Viewing is tonemapped and, by EOX's own documentation, sharpened;
this model is trained on linear TCI. `11-eox.md` §14's quantile evidence stands.

## 10. What came out differently from expectation

1. **The margin grew rather than shrank.** Adding harder, darker chips might have been expected
   to reduce the model's advantage. It rose (+3.293 → +3.520 dB on heldout; 3.79× → 3.94×
   inliers), because bicubic degrades on dark low-contrast terrain faster than the model does.
2. **Three of five granules contain no nodata whatsoever**, which is why the first known-true
   attempt failed and why the correction's benefit is concentrated in 36SXJ and 36TVK.
3. **The probe's overstatement got worse, not better** (0.71 → 0.63), on a corpus 50 % larger.
4. **The corrected rule still rejects 54 chips on 36SXJ** for single isolated all-zero pixels
   that are almost certainly dark land rather than nodata. The registered rule was applied as
   registered; whether a minimum contiguous-area threshold would be better is a registration
   question and is not decided here.

## 11. Which model is carried forward

**`gencp_sr_tci_x4_b3_v2.onnx` (WP13).** It is trained on a corpus that includes the dark
terrain the old rule wrongly excluded, and it is evaluated and matched on the **whole** held-out
granule rather than 45 % of it. WP12's model and corpus remain on disk and its report stands
unaltered; nothing in it is withdrawn, and its numbers remain correct **for the corpus they
were measured on**.

## 12. Open items

1. **The post-run hang is four-for-four** and undiagnosed. `best.pt` has survived intact every
   time, verified by checksum across the kill.
2. **The probe has overstated sustained throughput on four consecutive runs**, ratios 0.51,
   0.60, 0.71, 0.63. The margin rule works; the cause is still unmeasured.
3. **An expected value as a bare constant becomes untestable when the corpus changes** (§3.1) —
   `KF2` is fixed, but the pattern may exist in other checks and has not been swept for.
4. **The corrected rule still rejects isolated single black pixels as nodata** (§10.4).
5. **The tone-curve question against EOX remains unsettled** (`11-eox.md` §14).
6. **`control_v2.py` and `evaluate.py` print "reflectance" for a product that is not
   reflectance.** Cosmetic, inherited, not fixed here.
