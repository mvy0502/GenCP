# WP8 — does super-resolution actually help matching?

**Registered before any arm was run.** Sections 1–8 are the registration. Results begin at §9.
Standing practice 4: predictions before outcomes. Nothing in §1–8 was revised after a result
was seen; if it had been, this document would say so and keep the earlier version.

---

## 1. Why this work package exists

Every super-resolution number this project has produced — WP3B's +5.574 dB, WP7's +2.971 dB,
every SSIM and MAE — is a **pixel-fidelity** number. None of them measures what the tool is
for. A sharper reference image is supposed to give keypoint matching more to lock onto, so
that georeferencing gets more control points and better-localised ones. **Whether
super-resolution delivers that is unmeasured, for our model and for wsx4 alike.**

## 2. The asymmetry, stated here and not saved for the conclusion

> **Our model was trained on exactly the transformation being measured: 40 m → 10 m, by the
> registered Wald degradation, on this corpus. wsx4 was trained for 10 m → 2.5 m on different
> imagery and is being run outside its domain.**
>
> **This favours our model.** It is unavoidable if the ground truth is to be real Sentinel-2
> rather than something we invented, and real ground truth is worth more than a symmetric
> comparison. Any reading of arm 2 against arm 3 must carry this sentence. It is not a caveat
> discovered at the end; it is a property of the design, fixed before the design was run.

A second asymmetry, smaller and also unavoidable: WP6 established that wsx4 requires a **crop
margin** to suppress border artefacts. The corpus stores 256 × 256 target chips with no
surrounding context, so the 64 × 64 degraded input has no margin available — **for any arm**.
Every arm is handicapped identically at the border, but a GAN's border artefacts are likely to
be worse than a bicubic kernel's, so this too leans against arm 3.

## 3. Design

Ground truth is the **real Sentinel-2 at 10 m**, the finest thing in this repository. The
experiment therefore runs at matching scale, not at native scale:

1. Take a real 10 m chip, 256 × 256.
2. Degrade it to 40 m (64 × 64) with **the registered degradation function**,
   `sr_data.degrade.degrade(x, scale=4)` — imported, never reimplemented, the same code
   `sr_data` and WP7 use, including the scale-4 kernel fix of `07-x4-registration.md` §11.1.
3. Bring it back to 256 × 256 by four arms.
4. Match each arm's output against the real 10 m chip.

| arm | what it is | role |
|---|---|---|
| **0** | the real 10 m, matched against itself | **the ceiling.** Without it the other three have no scale |
| **1** | bicubic ×4, `sr_core.upsample.BicubicUpsampler(scale=4)` | **the control.** All paired differences are against this arm |
| **2** | our WP7 x4 model, `gencp_sr_x4_b4.onnx` | the L1/Charbonnier model |
| **3** | wsx4, `wsx4_spatrad.onnx` | the reference GAN |

Arm 0 is degenerate by construction — an image matched to itself — and that is the point: it
measures the maximum keypoint count and the zero-residual floor this detector can achieve on
this imagery, which is the only honest denominator for the other three.

## 4. Corpus

**All 1332 chips of the held-out granule 36SXJ**, from
`tubitak/data/sr_wald_corpus_x4/chips_heldout.npy`, shape `(1332, 4, 256, 256)`, uint16 DN.

**Why all of them, and not a sample:** 36SXJ is the granule no model in this project was
trained on, in any form — it is held out in WP3A's corpus, in WP3B's corrected split and in
WP7. Using every chip removes the selection question entirely. Any subset would need a
selection rule, and a selection rule chosen by someone who has seen the imagery is a place for
a result to hide. **The same 1332 chips are used for every arm**, in the same order.

Chips with too little texture to detect keypoints are expected (water, uniform field) and are
reported as such rather than silently dropped.

## 5. The measurement — one detector, one matcher, one set of parameters

**Detector and matcher: the KARIOS KLT pipeline**, imported from
`/Users/vedat/tools/karios` — Laplacian, then Shi-Tomasi corners
(`cv2.goodFeaturesToTrack`), then pyramidal Lucas-Kanade (`cv2.calcOpticalFlowPyrLK`) with a
forward-backward consistency check at 0.1 px.

**Why this one:** it is *this project's own matching side*, the pipeline Project 1's
georeferencing gates already run. Choosing a detector fresh for WP8 would make the answer a
statement about that choice; using the one the project already commits to makes it a statement
about super-resolution. It is also the reason this work package is possible here and not
elsewhere.

**Parameters: `tubitak/configs/karios_gencp.json`, unchanged.** They were chosen in Project 1,
for this imagery, before WP8 existed — so they cannot have been tuned to this experiment.

| minDistance | blocksize | maxCorners | matching_winsize | qualityLevel | laplacian_kernel_size |
|---|---|---|---|---|---|
| 1 | 5 | 20000 | 15 | 0.1 | 7 |

**Identical for all four arms. Not tuned per arm, not revisited after any result.**

### 5.1 Band

**B04 (red), plane index 2, everywhere.** A single band avoids introducing a band-weighting
choice that would itself need registering and defending. B04 is chosen over B08 because NIR
texture is dominated by vegetation state, and over a luminance combination because that is a
weighting. It is a visible band, present in every product, and the one the plugin's demo
displays. **Registered before measurement and not revisited.**

### 5.2 Two deliberate departures from KARIOS's defaults, both stated

**(a) Fixed radiometric window instead of per-image min/max.** KARIOS's `_to_uint8` normalises
each array by its own min/max. Across arms that is a confound: an arm whose output has a
different dynamic range gets a different stretch, so the Laplacian sees different contrast and
the detector a different image. **Both the arm output and the reference are converted to uint8
using one window taken from the reference chip**, so every arm's detector input is on the same
radiometric footing. This is a change to preprocessing, made for comparability, fixed before
any arm ran.

**(b) Detection runs on the ARM's output, tracked into the real 10 m.** KARIOS detects on its
reference. Here the super-resolved image is the thing whose usefulness is in question — the
brief's own framing is that a sharper *reference image* gives matching more to lock onto — so
the keypoints must be the ones the arm supplies. Detecting on the real 10 m instead would give
every arm an identical keypoint set and make the raw-keypoint half of §7's hypothesis
unmeasurable by construction.

### 5.3 RANSAC and the reported quantities

Correspondences surviving forward-backward are fitted with
`cv2.estimateAffinePartial2D(method=cv2.RANSAC, ransacReprojThreshold=3.0, maxIters=5000,
confidence=0.99, refineIters=10)`. `cv2.setRNGSeed(20260831)` before every call.

Per chip:

| quantity | definition |
|---|---|
| `n_keypoints` | corners returned by `goodFeaturesToTrack` on the **arm's** output |
| `n_tracked` | correspondences surviving the 0.1 px forward-backward check |
| `n_inliers` | RANSAC inliers |
| `inlier_ratio` | `n_inliers / n_keypoints` — **stated once, used throughout**; `n_inliers / n_tracked` is reported beside it and never substituted for it |
| `rmse_model` | RMSE of inlier residuals to the fitted RANSAC model — the standard quantity |
| `rmse_truth` | **RMSE of inlier displacements from zero.** The arm output is on the reference grid, so the true transform is the identity and any displacement is error |

`rmse_truth` is the one that measures georeferencing quality, because here — unlike in a real
georeferencing job — **the right answer is known**. `rmse_model` can be made small by a
consistent wrong answer; `rmse_truth` cannot. Both are reported; neither is dropped.

## 6. Sign convention, stated once

**`arm − bicubic`**, for every paired difference. For `n_keypoints`, `n_tracked`, `n_inliers`
and `inlier_ratio`, **positive = the arm is better**. For `rmse_model` and `rmse_truth`,
**negative = the arm is better** (smaller error). "Chips where the arm is worse" is counted in
the direction that metric's sign convention makes worse. Never pooled; per chip, then the mean
and standard deviation across chips.

## 7. Predictions, registered before measurement

**Arm 0, oracle.** Highest keypoint count of any arm, inlier ratio near 1, `rmse_truth`
essentially 0. It is an image matched to itself; anything else means the pipeline is broken,
which is why it doubles as a check.

**Arm 1, bicubic.** Fewest keypoints of the three real arms. Bicubic upsampling of a 40 m image
invents no detail, so the Laplacian has little to fire on and Shi-Tomasi finds few corners. But
the corners it does find should be well-localised, because bicubic introduces no structure that
is not in the 40 m data — so a **high inlier ratio on a small count**.

**Arm 2, our x4 model.** More keypoints than bicubic, because it restores edge energy bicubic
cannot. Inlier ratio comparable to or better than bicubic. `rmse_truth` lower than bicubic.
This is the arm the experiment is set up to favour (§2).

**Arm 3, wsx4.** See §7.1.

### 7.1 The hypothesis this work package exists to test

> **A GAN's invented texture produces keypoints with no counterpart on the ground.** So wsx4
> should show a **higher raw keypoint count** than the L1 model, together with a **worse inlier
> ratio** and a **larger residual**, while an L1 model produces **fewer but better-localised**
> correspondences.

Falsifiable in three independent ways, each recorded whether it holds or not:

| | prediction | falsified if |
|---|---|---|
| H1 | `n_keypoints`: arm 3 > arm 2 | arm 3 ≤ arm 2 |
| H2 | `inlier_ratio`: arm 3 < arm 2 | arm 3 ≥ arm 2 |
| H3 | `rmse_truth`: arm 3 > arm 2 | arm 3 ≤ arm 2 |

**If the measurement contradicts any of these, the contradiction is reported and the hypothesis
is not adjusted afterwards.** A finding that super-resolution does not help matching at all is
the more interesting outcome and would be reported as the result, not as a failure.

## 8. Checks — the pipeline must be shown to work before its numbers mean anything

| # | check | known-true | known-false |
|---|---|---|---|
| M1 | recovers a planted shift | a known integer + sub-pixel translation | — |
| M2 | rejects unrelated ground | — | two chips of different ground; inliers must collapse |
| M3 | empty image | — | all-zero input |
| M4 | single-colour image | — | constant-valued input |
| M5 | missing file | — | a path that does not exist |

**M1 tolerance, registered before running: the recovered translation must be within 0.25 px of
the planted one in both axes.** A pipeline that cannot recover an answer that was planted
cannot be trusted with one that was not.

M3–M5 are the degenerate invocations standing practice 10 requires: an audit of this project's
verifiers found 18 of 23 exiting 0 when handed nothing to check.

### 8.1 Invariance — what must not change for these numbers to mean what they claim

1. The KLT parameters of `karios_gencp.json`, identical across arms.
2. Band B04, and the fixed reference-derived uint8 window.
3. Detection on the arm output, tracking into the real 10 m.
4. The same 1332 chips, in the same order, for every arm.
5. The degradation is `sr_data.degrade` at `scale=4`, imported.
6. `cv2.setRNGSeed(20260831)` before every RANSAC call.
7. **Seed 20260831. numpy 1.26.4, cv2 4.8.1, scipy 1.17.1, onnxruntime 1.29.0, python 3.12.12**
   (the `karios` environment — the only one on this machine with a detector; nothing was
   installed for this work package).
8. `rmse_truth` and `rmse_model` are never substituted for one another.

---

# Results

Path for every number below: `tubitak/sr/sr_match/run_arms.py` in the `karios` environment,
over `tubitak/data/sr_wald_corpus_x4/chips_heldout.npy`, artefact
`tubitak/data/sr_match/wp8_arms.json`. 1332 chips, 129 s, seed 20260831.

## 9. Pipeline validation — reported before any arm's result

`tubitak/sr/sr_match/checks_match.py`. **11 of 11 cases behaved as registered.**

**M1, the planted shift.** A translation of `(dy, dx) = (+3.25, −2.75)` px — integer part plus
a sub-pixel part — applied with `scipy.ndimage.shift(order=3)`, on four chips:

| chip | recovered (dy, dx) | error | inliers |
|---|---|---|---|
| 0 | (+3.2594, −2.7368) | (0.0094, 0.0132) | 2089 |
| 17 | (+3.2603, −2.7446) | (0.0103, 0.0054) | 2584 |
| 101 | (+3.2470, −2.7358) | (0.0030, 0.0142) | 2397 |
| 500 | (+3.2639, −2.7394) | (0.0139, 0.0106) | 2320 |

**Worst error 0.0142 px against a registered tolerance of 0.25 px** — inside it by a factor of
about 18. The pipeline recovers an answer that was planted, so it may be trusted with one that
was not.

**M2, unrelated ground.** Chip 700 against chip 0: **15 inliers** where the same chip against
itself gives 2284 — **0.7 %**. Chip 1200: 24 inliers, **1.1 %**. The inlier count collapses.

**M3–M5, degenerate.** All-zero image → 0 keypoints, 0 inliers. Single-colour image → 0
keypoints. A real image against an all-zero reference → 0 inliers. A missing corpus file raises
`FileNotFoundError`; a missing ONNX model raises `NoSuchFile`. **Nothing reports success when
handed nothing to check.**

## 10. The four arms, absolute

Mean over 1332 chips, never pooled.

| arm | keypoints | tracked | inliers | inlier ratio | rmse_model | **rmse_truth** |
|---|---|---|---|---|---|---|
| **0 oracle** | 2415.2 | 2415.2 | 2415.2 | 1.0000 | 0.0000 | **0.0000** |
| **1 bicubic** | 1513.6 | 129.4 | 126.9 | 0.0836 | 0.9587 | **0.9731** |
| **2 ours (x4)** | 1766.4 | 480.0 | 478.7 | 0.2721 | 0.6012 | **0.6049** |
| **3 wsx4** | 2171.6 | 239.9 | 231.3 | 0.1070 | 1.0452 | **1.0917** |

Medians track the means closely (bicubic 1520/129/126, ours 1771/477/476, wsx4 2180/238/229),
so no arm's mean is being carried by a tail. **No chip in any arm failed to produce keypoints.**

### 10.1 As a fraction of the oracle

| | bicubic | ours | wsx4 |
|---|---|---|---|
| keypoints | 0.627 | 0.731 | **0.899** |
| tracked | 0.054 | **0.199** | 0.099 |
| **usable correspondences (inliers)** | **0.053** | **0.198** | **0.096** |

**This table is the work package's answer.** wsx4 recovers the most *keypoints* — 90 % of what
the oracle finds, far ahead of everything else. It converts almost none of them into *usable*
correspondences. Our model finds fewer keypoints than wsx4 and produces **twice as many usable
ones**, and **3.8 times as many as bicubic**.

The gap between the keypoint row and the inlier row is the whole story: **detecting a corner is
not the same as detecting a corner that is where it appears to be.**

## 11. Paired against arm 1, the bicubic control

Per chip, `arm − bicubic`; positive = better for counts and ratio, negative = better for RMSE
(§6).

| arm | keypoints | inliers | inlier ratio | **rmse_truth** | chips worse (rmse_truth) |
|---|---|---|---|---|---|
| oracle | +901.54 ± 152.14 | +2288.31 ± 188.49 | +0.9164 ± 0.0122 | −0.9731 ± 0.0817 | 0 / 1332 |
| **ours** | +252.77 ± 82.61 | **+351.81 ± 72.76** | **+0.1885 ± 0.0448** | **−0.3682 ± 0.0928** | **1 / 1332** |
| **wsx4** | +657.93 ± 143.31 | +104.43 ± 31.47 | +0.0234 ± 0.0171 | **+0.1186 ± 0.1227** | **1128 / 1332** |

> **Our model helps matching, and it helps almost everywhere: it beats bicubic on inliers on
> 1332 of 1332 chips and on localisation on 1331 of 1332.**

> **wsx4 supplies more correspondences than bicubic but localises them worse than bicubic —
> worse on 1128 of 1332 chips.** More control points that are further from the truth is not an
> improvement for georeferencing; it is a harder problem with a larger residual.

## 12. The hypothesis — all three limbs held

Registered in §7.1, before measurement.

| | prediction | ours | wsx4 | verdict |
|---|---|---|---|---|
| **H1** | wsx4 has more raw keypoints | 1766.40 | 2171.56 | **HOLDS** |
| **H2** | wsx4 has a worse inlier ratio | 0.2721 | 0.1070 | **HOLDS** |
| **H3** | wsx4 has a larger residual | 0.6049 | 1.0917 | **HOLDS** |

Paired per chip, `ours − wsx4`: wsx4 finds more keypoints on **1324 of 1332** chips
(−405.16 ± 143.43), while ours has the better inlier ratio on **1332 of 1332**
(+0.1651 ± 0.0387) and the better `rmse_truth` on **1332 of 1332** (−0.4868 ± 0.0786).

**The GAN produces keypoints with no counterpart on the ground, exactly as registered.** The
mechanism is visible in the `tracked` column of §10: wsx4 detects 2171 corners and only 240
survive a 0.1 px forward-backward check. Bicubic's corners survive at a similar rate because
it has few to begin with; ours survive at **27 %**, wsx4's at **11 %**.

**§2's asymmetry governs how far this generalises.** Our model was trained on precisely this
degradation; wsx4 was not, and had no crop margin. H1–H3 are confirmed *for this comparison*.
They are not a general result about GANs versus L1 losses, and this document does not claim one.

## 13. A finding that was not predicted: wsx4 carries a systematic quarter-pixel shift

Decomposing each chip's residual into a systematic part and a scatter, `rmse² = bias² +
scatter²` where bias is the mean displacement of that chip's inliers:

| arm | rmse_truth | \|bias\| | scatter | bias share |
|---|---|---|---|---|
| bicubic | 0.9731 | 0.1035 | 0.9660 | 1.4 % |
| ours | 0.6049 | 0.0418 | 0.6030 | 0.6 % |
| **wsx4** | 1.0917 | **0.2740** | 1.0532 | **6.8 %** |

The bias is almost entirely in one axis and one direction: **wsx4's mean `dy` is −0.2504 px,
median −0.2516, standard deviation 0.1025, and 1267 of 1332 chips have `dy < −0.1`.** Our
model's `dy` is −0.0093 and bicubic's −0.0056.

**A consistent quarter-pixel offset in a single axis is a grid-convention mismatch, not noise.**
It is the same class of defect as WP7's decimation-kernel asymmetry and as Gate S's half-pixel
centre contract: somewhere between wsx4's upsampling convention and ours, the output grid is
placed half a step differently. It is **systematic and therefore correctable** — which makes it
the most actionable result in this work package.

**It is not, however, the explanation for wsx4's poor showing.** With the bias removed entirely,
wsx4's scatter is **1.0532 px, still worse than bicubic's total error of 0.9731 px.** Correcting
the shift would leave the ranking unchanged.

## 14. Open items

1. **The asymmetry of §2 is unresolved and unresolvable with this data.** Measuring wsx4 in its
   own domain would need real 2.5 m ground truth, which this project does not have.
2. **No arm had a crop margin** (§2). WP6 measured wsx4's tiling error at 37 DN with feathering
   against 1 DN with a crop margin; the border of every 64 → 256 chip here is unmargined. This
   leans against wsx4 by an unmeasured amount.
3. **wsx4's −0.25 px `dy` bias is measured but not diagnosed.** Whether it originates in the
   model, in its expected input convention, or in how WP6's host feeds it is unknown.
4. **One band, one detector, one matcher.** B04 with KARIOS KLT. Whether the ranking holds for
   B08, or for SIFT or a learned matcher, is untested. The choices were registered before
   measurement and not revisited, which protects against tuning but does not establish
   generality.
5. **The oracle's ceiling is an identity match**, so its 1.0000 inlier ratio and 0.0000 residual
   are exact by construction rather than achievable. The "fraction of the oracle" column is a
   scale, not a target: no real arm can reach it.
6. **`rmse_truth` is available only because the true transform is known to be the identity.** In
   a real georeferencing job it is not, and only `rmse_model` would be available — which, on
   this data, ranks the arms the same way but understates wsx4's error (1.0452 against 1.0917)
   precisely because a consistent bias is invisible to a model-fit residual.

---

# Addendum — arm 3 with its declared margin, and the shift

Added after §9–14 were measured. **Nothing already registered or measured was changed**: the
other arms were not re-run, and the uncropped arm 3 numbers stay exactly as reported above.
Where a comparison needs a common chip set, existing per-chip values are *subset*, never
recomputed.

## 15. Arm 3, re-run with the crop margin wsx4 declares

The strongest objection to §12 is that the reference model was not run properly. It is a fair
objection and it is now removed.

### 15.1 Where the margin comes from, and what it costs to honour

`tubitak/data/wp5_reference/models/wsx4_spatrad.yaml` declares, in full:

```
bands: [B2, B3, B4, B8]     factor: 4.0     margin: 130     model: wsx4_spatrad.onnx
```

`run.py:326` — `margin_in_meters = target_resolution * model_parameters.margin` — fixes the
unit as **output pixels**: 130 output px = 32.5 source px = **325 m at the model's native
scale**. WP6 measured cropped tiling at **1 DN** against the single-tile reference where
feathering gave **37 DN**.

32.5 source pixels is not an integer, so the window is padded by **33 source px** per side and
the output cropped by **132 output px** — the smallest integer margin that satisfies the
declared 130:

| step | size |
|---|---|
| real 10 m window | 520 × 520 (256 target + 2 × 132 real context) |
| degrade ÷4 | 130 × 130 |
| wsx4 ×4 | 520 × 520 |
| crop 132 per side | **256 × 256** — exactly the chip, matched against the same reference |

**The context is real granule pixels, not padding.** Reflect-padding the margin would have
re-created the artefact the margin exists to remove. **76 of 1332 chips lie within 132 px of
the granule edge and are excluded** rather than given invented context. Every column in §15.2
is restricted to the same **1256** chips, including the arms carried over from §10, so the
comparison is like-for-like.

Verified before use: the manifest's heldout order matches the array order (4 of 4 spot chips
byte-identical to their raster window, with a neighbouring-window known-false correctly
rejected), and B02/B03/B04/B08 were re-checked as sharing one transform and shape at the point
where that is relied on.

### 15.2 Result, on the same 1256 chips

| arm | keypoints | tracked | inliers | inlier ratio | **rmse_truth** | mean dy |
|---|---|---|---|---|---|---|
| 0 oracle | 2412.5 | 2412.5 | 2412.5 | 1.0000 | 0.0000 | 0.0000 |
| 1 bicubic | 1512.9 | 129.4 | 126.9 | 0.0836 | 0.9719 | −0.0065 |
| 2 ours | 1764.5 | 479.9 | 478.6 | 0.2723 | **0.6041** | −0.0090 |
| 3 wsx4 **uncropped** | 2171.5 | 240.4 | 231.8 | 0.1072 | 1.0907 | −0.2508 |
| 3 wsx4 **cropped, m=132** | **2231.6** | 270.7 | 262.1 | 0.1181 | **1.0716** | −0.2500 |

**What the margin bought** (paired, cropped − uncropped, per chip):

| keypoints | inliers | inlier ratio | rmse_truth | dy |
|---|---|---|---|---|
| +60.15 ± 45.89 | +30.26 ± 18.60 | +0.0109 ± 0.0084 | **−0.0191 ± 0.0593** | +0.0007 ± 0.0734 |

**The margin helps, and it helps in the direction WP6 predicted — and it does not change the
conclusion.**

- Cropped wsx4 **still localises worse than bicubic**: +0.0997 ± 0.1208 px, worse on
  **1015 of 1256** chips (uncropped: worse on 1128 of 1332).
- Ours **still beats cropped wsx4** on inlier ratio on **1256 of 1256** chips
  (+0.1542 ± 0.0379) and on `rmse_truth` on **1256 of 1256** (−0.4675 ± 0.0773).
- The margin recovers **0.0191 px** of a **0.4675 px** gap — about **4 %** of it.

Stated plainly: **running the reference model properly improves it measurably and leaves every
ranking in §10–12 intact.** H1, H2 and H3 all still hold with the cropped arm substituted.

### 15.3 The remaining asymmetry, which the margin does not touch

wsx4 was trained for 10 m → 2.5 m and is being run 40 m → 10 m. **This cannot be removed,
because the only ground truth in this repository is real Sentinel-2 at 10 m** — measuring wsx4
in its own domain would require real 2.5 m imagery, which does not exist here, and substituting
synthetic ground truth would replace a measurement with an assumption. The asymmetry is
structural, it favours our model, and it stays stated (§2).

## 16. The −0.25 px shift: what it is, and what would settle it

### 16.1 What the measurement says

**wsx4's output sits a quarter of an output pixel off our grid convention, in the row axis.**

| arm | mean dx | mean dy | median dy | std dy | chips with dy < −0.1 |
|---|---|---|---|---|---|
| bicubic | +0.0020 | −0.0065 | −0.0080 | 0.0839 | — |
| ours | −0.0033 | −0.0090 | −0.0085 | 0.0328 | — |
| wsx4 uncropped | +0.0343 | −0.2508 | −0.2522 | 0.1025 | 1267/1332 |
| **wsx4 cropped** | +0.0322 | **−0.2500** | −0.2504 | 0.0954 | **1209/1256** |

**In ground units**, since a shift in pixels is illegible to most readers:

| | output pixel | shift |
|---|---|---|
| in this experiment (40 m → 10 m) | 10 m | **2.50 m** |
| at the model's native scale (10 m → 2.5 m) | 2.5 m | **0.63 m** |

At native scale that is roughly a quarter of a Sentinel-2 10 m pixel of georeferencing error,
applied uniformly — small per pixel, and systematic, which is the kind of error that does not
average out across control points.

### 16.2 Three things the evidence does and does not support

**It is not a border artefact.** Giving wsx4 its full declared margin with real context moved
the shift from −0.2508 to **−0.2500** — that is, not at all (+0.0007 ± 0.0734 paired). Whatever
produces it is in the model's interior behaviour, not its edges. This is new evidence from §15
and it is the strongest single fact about the shift.

**It is probably not our measurement path.** Bicubic and our model, through the identical
degradation, upsampling harness, uint8 window, Laplacian, detector, tracker and RANSAC, sit at
−0.0065 and −0.0090 px. A path that imposed a quarter-pixel bias would impose it on them too.

**But that evidence is not conclusive, and the reason is worth stating.** Our model was trained
on data produced by our own grid convention, so a zero for arm 2 is **partly by construction** —
it learned whatever alignment `sr_data.degrade` defines. Bicubic is the stronger witness of the
two, because `BicubicUpsampler` was never trained on anything; but it is also a different kind
of operator, and WP7 has already shown once that this project's own kernel carried a sub-pixel
shift nobody noticed for two work packages.

**One detail that argues against a simple convention mismatch:** the shift is in **y only**.
`dx` is +0.032 px, an order of magnitude smaller. A pixel-centre convention disagreement —
the `(s−1)/2s` family of offsets — would displace both axes equally. A single-axis offset is
more consistent with something in row handling than with a symmetric grid convention, and
that is a reason not to write "grid convention mismatch" as though it were established.

### 16.3 Verdict: **not attributed**

The finding is recorded as what it is — *wsx4's output sits a quarter output pixel off our grid
convention in y, and the cause is unknown* — and not as a defect attributed to either side.

**Two tests would settle whether the convention is theirs or the mismatch is ours.**

**Test A — run their own tool end to end on its demo product and measure the same quantity.**
**Not done.** WP5 (`05-referans-arac.md`) established that `sentinel2_superresolution` cannot
read Copernicus L2A COGs: it accepts THEIA/MAJA products or L1C SAFE, neither of which this
project holds. Running it end to end therefore needs a product we would have to acquire, plus
its own environment, and that is a work package rather than an addendum. It is the decisive
test and it remains open.

**Test B — look for an output-alignment declaration in `wsx4_spatrad.yaml`. Done, negative.**
The file's complete contents are the four keys quoted in §15.1: `bands`, `factor`, `margin`,
`model`. **There is no declaration of output alignment, pixel-centre convention, origin offset
or half-pixel handling of any kind.** The contract the model ships states what bands it wants,
what factor it applies and how much border to discard — and says nothing about where its output
grid sits. So the file does not settle the question, and it also cannot be cited as evidence
that wsx4 intends our convention.

Since the contract is silent, **neither side can claim conformance from the declaration**, and
the shift stays unattributed until Test A is run.

## 17. Open items, updated

Items 1–6 of §14 stand, with these changes and additions:

7. **Item 2 of §14 is discharged.** wsx4 has now been run with its declared margin (§15). The
   margin improves it by about 4 % of the gap to our model and changes no ranking.
8. **76 of 1332 chips are excluded from §15** as granule-edge chips that cannot be given real
   context. They are included in §10–13, which is why §15 restates every arm on its own 1256.
9. **Test A is the open question for the shift** (§16.3), and needs a THEIA/MAJA or L1C SAFE
   product this project does not have.
10. **The shift is in one axis only**, which the "grid convention" reading does not by itself
    explain (§16.2).
