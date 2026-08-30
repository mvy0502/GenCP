# WP3B registration — corrected split, model, training, evaluation

**Registered:** 2026-08-30, Project 2 WP3B, **before the corrected split was built, before the
control was recomputed on it, before any model existed and before any metric was seen.**

This file is never edited to match a result. The constants it names live in
`tubitak/sr/sr_train/config.py` and are imported, never restated as literals.

**Relationship to the WP3A registration.** This is a **revision of D11 (splits), not a
replacement of the WP3A registration.** `03a-corpus-registration.md` stays in the record
unedited. Standing practice 4 permits a revision only when an *input measurement* improves
and **no outcome has been seen**; both conditions hold. The input measurement that improved is
WP3A's own open item 8: 47 of 403 test chips (11.66 %) share ground with a training chip from
another granule. No model has been trained, and the only outcome in existence — WP3A's bicubic
control — is retained below, relabelled, not deleted.

**What is revised:** D11's split procedure only. Everything else in the WP3A registration —
D7 radiometry, clear masking, D8 chip geometry, D9 degradation, D10 storage, D12
normalisation, D-metrics conventions — is **unchanged and inherited**, and the corpus arrays
are not rebuilt. Only the `split` column of the manifest changes.

---

## 1. D13 — the corrected split

Two steps, in this order, both in map coordinates. All five granules are EPSG:32636, so map
coordinates are directly comparable without reprojection.

### 1.1 Step one: deduplicate across granules

**Measured input, before the rule was chosen** (`tubitak/sr/docs/03b-training.md` §2.1):
chip grids of different granules **do not align** — NW corners differ modulo the 2560 m chip
size (600 / 480 / 600 / 780 / 960 m easting). There are **zero exact-corner matches** between
any two granules. "The same ground in two granules" is therefore always a **partial footprint
overlap**, never a duplicated chip, and a rule based on equality would remove nothing.

**Overlap predicate.** Chips A and B overlap iff their 2560 m square footprints intersect in
positive area. Footprint of a chip with north-west corner `(e, n)` is
`[e, e+2560] x [n-2560, n]`.

**Deterministic keep rule, stated with its reason:**

> Granules are processed in **ascending order of accepted-chip count, ties broken by MGRS
> name ascending**. A chip is kept unless its footprint overlaps a chip already kept from an
> earlier granule in that order.

Order, from the WP3A screening counts (`03a-wald-corpus.md` §3.1) — an input measurement, not
an outcome:

| rank | granule | accepted chips |
|---|---|---|
| 1 | 36TUK | 1036 |
| 2 | 36SWJ | 1122 |
| 3 | 36TVK | 1283 |
| 4 | 36SXJ | 1332 |
| 5 | 36SVJ | 1659 |

**Why ascending count rather than alphabetical or WP0's order.** Dedup necessarily deletes
chips from one side of every overlap. Taking them from the granule that already contributes
fewest would strip the scarcest sites first — and 36SWJ (Tuz Gölü) is both the second
scarcest and the compositional outlier WP3A's open item 1 wants kept in the evaluation.
Ascending order protects the scarce granules and spends the surplus of 36SVJ, which has 1659
chips and the least to lose. The rule is stated before it is run and is not tuned afterwards.

**Scope.** The rule is applied **corpus-wide**, across all five granules, not only within
datatake A008614. The brief scopes deduplication to same-datatake pairs; corpus-wide is a
superset, and it is chosen because a same-datatake special case would need 36SXJ's zero
overlap to *stay* zero to be safe, which is exactly the "luck, not design" WP3A warned about.
**Prediction: every chip removed will in fact fall within datatake A008614**, because 36SXJ
was measured to overlap no accepted chip of any other granule. If any removal touches 36SXJ,
that is a finding to report, not a rule to adjust.

### 1.2 Step two: split with the buffer applied corpus-wide

**Block assignment, now yield-aware.** Unchanged from D11 except for eligibility: 14 x 14
chip blocks, 3 x 3 = 9 per granule, 7 train / 1 val / 1 test, seeded by
`splits.granule_seed(granule, SPLIT_SEED=20260830)` — the same seed and the same stable
SHA-256 derivation WP3A fixed.

> **`MIN_BLOCK_CHIPS_FOR_EVAL = 50`.** A block may be assigned to `val` or `test` only if it
> retains at least 50 chips **after deduplication**. Ineligible blocks are assigned `train`.
> The seeded permutation is drawn over the eligible blocks only.

**Why 50, and why it is satisfiable.** 50 is a quarter of a block's 196 candidates. It is
set so that each granule's contribution to a split is large enough for a per-chip mean to
mean something: with four training granules and one eval block each, 50 is the floor at which
a granule contributes a non-trivial share of a ~400-chip test set. Measured per-block yields
before dedup (`03b-training.md` §2.1) show minimum yields of 77 / 64 / 110 / 0 / 84 for
36TVK / 36TUK / 36SVJ / 36SWJ / 36SXJ, with **7 of 9 blocks eligible in the worst granule
(36SWJ) and 9 of 9 in every other**, so the rule is satisfiable everywhere with room to
spare. This directly addresses WP3A open item 1: 36SWJ's block (2,2) yielded 0 chips because
it is 94.81 % nodata, and it was nevertheless assigned `test`, which is why 36SWJ contributed
zero test chips.

**Buffer, now corpus-wide and in map coordinates.**

> A chip is **dropped from the corpus** if the separation between its footprint and the
> footprint of any chip in a **different split** is less than `SPLIT_BUFFER_M = 2560 m`,
> **regardless of which granule either chip belongs to.** Separation is the Chebyshev gap
> between the two footprint rectangles: `max(0, gap_x, gap_y)`, which is 0 for overlapping or
> touching footprints.

This generalises WP3A's rule rather than replacing it: for two aligned, non-overlapping chips
in one granule, a Chebyshev distance of one chip gives a gap of 0 m — dropped, as before —
and of two chips gives exactly 2560 m — kept, as before. The change is that the comparison is
no longer restricted to chips of the same granule, and no longer assumes a common grid.

**36SXJ remains held out whole** and never enters train or val. Unchanged.

---

## 2. D18 — the fifth registered check: cross-granule leakage

**This check gates Part B. Training does not start unless it reports zero residual leakage.**

> **D18.** No chip in `test`, and no chip in `heldout`, has a footprint that overlaps or lies
> within `SPLIT_BUFFER_M` of the footprint of any chip in `train`, in any granule.

Reported separately for `test` and for `heldout`, and separately at two radii — overlap
(separation 0) and buffer (separation < 2560 m) — because they are different failures: the
first is shared ground, the second is spatial autocorrelation.

| case | input | predicted |
|---|---|---|
| **KT** known-true | the corrected manifest | **0 leaking chips in `test`, 0 in `heldout`, at both radii** |
| **KF1** known-false, shared ground | the corrected manifest with one `train` chip of 36SVJ relabelled `test` while a genuinely overlapping 36SWJ train chip is left in `train` | **the relabelled chip is reported as leaking** |
| **KF2** known-false, the original split | the **WP3A** manifest, unmodified | **47 leaking `test` chips are reported**, reproducing WP3A open item 8 |
| **DG** degenerate | an empty manifest | **refuses to emit a verdict** |

KF2 is the case that matters: it is a known-false input whose expected answer was measured
independently, by a different implementation, in a different work package. A leakage checker
that cannot reproduce 47 on the split that is known to contain 47 is not a leakage checker.

---

## 3. The control, recomputed on the corrected split

Recomputed with **exactly the conventions of the WP3A registration §9**, unchanged and
restated here only so that no reader has to assume them:

* domain **normalised reflectance, `DN / 5000.0`**, float32, unclipped;
* PSNR data range **1.0**;
* **every metric computed PER CHIP; the reported figure is the UNWEIGHTED ARITHMETIC MEAN
  over the chips of that split. Never pooled over pixels.**
* the upsampler is `sr_core.upsample.BicubicUpsampler(scale=2)`, WP1's code, imported
  read-only;
* the degradation is `sr_data.degrade.degrade_chip`, imported, never reimplemented, with the
  normalisation divisor asserted against `sr_data.params.NORM_DIVISOR_DN` at run time rather
  than written again as a literal;
* **the two test sets are reported separately and never pooled.**

**The WP3A control numbers are retained, not replaced.** They are relabelled *measured on the
leaked split* and stay in the record:

| split | WP3A PSNR (dB) | status |
|---|---|---|
| test | 31.9420 | **superseded as a bar; retained as the measurement on the leaked split** |
| heldout | 33.0050 | **retained; the held-out set was measured clean (0 of 1332) and may be unchanged** |

**Prediction, registered before the recomputation:** the `heldout` control will be
**unchanged to within floating-point reproducibility**, because 36SXJ was measured to have
zero cross-granule overlap and is held out whole, so neither dedup nor the corpus-wide buffer
can touch it — unless the corpus-wide buffer now drops 36SXJ chips near a *train* chip of
another granule, which the overlap measurement says does not exist. If `heldout` changes, the
reason must be found and reported before Part B. The `test` control is expected to change,
and its direction is **not** predicted.

---

## 4. D14 — the loss is L1-family only

**Charbonnier**, `sqrt((pred - target)^2 + eps^2) - eps`, with **`eps = 1e-3` in normalised
units** (= 5 DN). No adversarial term. No perceptual term. No feature-matching term.

**Why Charbonnier rather than plain L1:** it is L1 everywhere except within `eps` of zero,
where it becomes quadratic, which removes the gradient discontinuity at exactly zero error.
At `eps = 1e-3` normalised the quadratic region is far below the sensor noise floor, so on
every error magnitude that occurs in practice it *is* L1. The `- eps` term makes the loss zero
at zero error so its value is directly comparable with an L1 number.

**Why no adversarial or perceptual term at all, stated as the application requirement it is:**
this model feeds keypoint matching for georeferencing. Invented texture that looks sharp
produces keypoints that correspond to nothing on the ground, which is strictly worse than a
blurred output producing fewer but honest ones. The dominant failure class in this project is
output that is wrong and plausible; a GAN is a machine for producing exactly that. Fidelity
beats apparent sharpness here, and the metric that will be reported (PSNR/SSIM/MAE against a
real target) is the one the application actually cares about.

## 5. D15 — no BatchNorm, no dropout, and the export trap it removes

**No normalisation layer of any kind. No dropout.** The model therefore has **no
mode-dependent operation**, so `model.train()` and `model.eval()` are the same function.

This is not a style preference. `torch.onnx.export` calls `.eval()` by default; Project 1 paid
for a BatchNorm graph whose exported behaviour differed from what was trained. Removing every
mode-dependent layer removes the class of bug rather than managing it.

**Registered check D15-C, with its outcome predicted:** one fixed input tensor, forward pass
in `train()` mode and in `eval()` mode. **Prediction: bit-identical outputs, max absolute
difference exactly 0.0.** A non-zero difference means a mode-dependent layer is present and is
a finding, not a tolerance to widen.

## 6. D16 — receptive field consistent with the tiling overlap

**Architecture, fixed here before it is built.** Residual convolutional network, no
normalisation, all convolutions 3 x 3 stride 1, upsampling by a single `PixelShuffle(2)` at
the end. No resize of the input anywhere.

```
  x (B,3,128,128) normalised
    -> conv3x3(3 -> C), ReLU                                    head
    -> [ conv3x3(C->C), ReLU, conv3x3(C->C), + skip ] x N       N residual blocks
    -> conv3x3(C -> C)                                          fusion
    -> conv3x3(C -> 3*4)                                        to shuffle channels
    -> PixelShuffle(2)                             (B,3,256,256)
    +  PixelShuffle(2)( x.repeat_interleave(4, dim=1) )         global nearest skip
```

`C = 64`, `N = 6`.

**The global skip is a nearest-neighbour 2x upsample implemented with `repeat_interleave`
plus the same `PixelShuffle`, so it is a shuffle and not a resize**, consistent with the
constraint. The network therefore learns the *residual over nearest-neighbour upsampling*,
which starts training near a sensible baseline instead of from noise.

**Receptive field, in INPUT (20 m) pixels.** Every 3 x 3 stride-1 convolution adds 2. The
`PixelShuffle` and the global skip add nothing.

```
  head                      3
  6 residual blocks, 2 convs each:  + 6*2*2 = 24        -> 27
  fusion                    + 2                          -> 29
  to-shuffle conv           + 2                          -> 31
  PixelShuffle              + 0                          -> 31
  RECEPTIVE FIELD = 31 input pixels
```

**31 <= 32.** The tiling overlap `INFER_OVERLAP_SRC_PX = 32` is retained unchanged, and `N`
was chosen as the largest depth that fits it: `N = 7` gives RF 35 and would not.

**What the other choice would have cost.** Raising the overlap to accommodate a deeper
network is not free at this tile size. WP3A recorded the WP4 inference contract as a 128 px
tile with 32 px overlap, giving stride 96 and 115 x 115 = 13,225 tiles per granule. At
overlap 48 the stride falls to 80 and the count rises to 138 x 138 = 19,044 tiles, **+43.9 %
forward passes** for two more residual blocks. Depth was the cheaper thing to give up, and
D16 is satisfied by construction rather than by a tolerance.

**Registered check D16-C:** the receptive field is **measured**, not only derived — by
gradient support, feeding a unit gradient at one output pixel and counting the input pixels
with non-zero gradient. **Prediction: exactly 31 x 31 input pixels.**

## 7. D17 — ONNX export with dynamic spatial axes

Exported with `dynamic_axes` on height and width. WP1 open item 2 measured that a static-shape
graph rejects a source smaller than one tile in an axis.

**Registered check D17-C:** the exported graph runs at **128** (the training size), at **96**,
and at **100** (not a multiple of eight), and its output is compared against PyTorch on the
same inputs. **Prediction: all three shapes execute, and the maximum absolute difference is
below 1e-4 in normalised units (= 0.5 DN)**, that bound being set by float32 accumulation
order differing between the two runtimes rather than by any modelling choice.

## 8. D19 — training discipline

* **Optimiser** Adam, `lr = 2e-4`, betas (0.9, 0.999), cosine decay to `2e-5`.
* **Batch** 32 chips. **Augmentation:** the 8 dihedral transforms, uniformly sampled. **No
  photometric augmentation of any kind** — it would break the fixed normalisation D12 exists
  to guarantee.
* **Degradation** is `sr_data.degrade.degrade_chip`, imported. The normalisation divisor is
  **asserted** against `sr_data.params.NORM_DIVISOR_DN`, not hard-coded a second time.
* **Seed** `TRAIN_SEED = 20260831`, recorded with every library version that affects numerics.
* **Checkpoint every 500 steps** to the run directory, keeping `last` and `best`. **Resuming
  from the latest checkpoint is exercised once, deliberately, before the full run** — a
  resume path that has never been run is not a resume path.
* **Model selection uses the `val` split only.**
* **THE TWO TEST SETS ARE READ EXACTLY ONCE, AT THE END OF PART C.** Not during training, not
  between epochs, not out of curiosity. The report states plainly whether this held.
* **Stop rule, before the run:** a wall-clock budget is stated before training starts; on
  reaching it, training stops and the best checkpoint by validation loss is the model that is
  evaluated. The budget is not extended to chase a number.

## 9. Evaluation — registered quantity and sign convention

**The registered quantity is the paired per-chip difference, `model - bicubic`, on the
identical chips**, reported per test set:

* its **mean**, its **standard deviation across chips**, and the **number of chips where the
  model is worse than bicubic**.

**Sign convention, stated once and never flipped: `model - bicubic`. For PSNR and SSIM,
positive means the model is BETTER. For MAE, negative means the model is BETTER.** Every
number in the report carries the metric's name beside it so the direction is never ambiguous.

Paired, because it removes chip difficulty from the comparison. A difference of two means
does not.

**The two test sets are never pooled and their absolute PSNRs are never compared with each
other.** WP3A §4.3 established the reason: 36SXJ has the lowest p99.9 in every band, so
bicubic loses less there for reasons that have nothing to do with the model.

**Edge density is reported as a diagnostic and is not a gate and not a claim.** Mean gradient
magnitude of model output, bicubic output and target, per test set.

**If the model does not beat the registered control on the held-out set, that is reported as
the result.** Nothing is tuned, training is not extended, the split is not redrawn.

## 10. Invariance — what must not change for these numbers to mean what they claim

1. **Everything in the WP3A registration §11 that is not D11.** The corpus arrays are not
   rebuilt; only the manifest's `split` column changes.
2. **The dedup keep rule and its granule order** (§1.1). A different order deletes different
   chips and produces a different corpus.
3. **`MIN_BLOCK_CHIPS_FOR_EVAL = 50`** (§1.2). It changes which blocks can be eval blocks.
4. **`SPLIT_BUFFER_M = 2560 m`, now applied corpus-wide** (§1.2).
5. **`SPLIT_SEED = 20260830`** and the stable SHA-256 per-granule derivation, unchanged from
   WP3A. The permutation is now drawn over *eligible* blocks, so the same seed does not
   reproduce the WP3A assignment, and is not expected to.
6. **`NORM_DIVISOR_DN = 5000.0`.** Every metric is in these units.
7. **The loss is Charbonnier with no adversarial or perceptual term** (D14). A model trained
   with any such term is not this model and its numbers are not these numbers.
8. **No mode-dependent layer** (D15), which is what makes the ONNX graph and the trained
   network the same function.
9. **Test sets read once, at the end.** If that is ever violated the reported margin is no
   longer a held-out measurement and must be relabelled.

---

# AMENDMENT 1 — registered 2026-08-30, before Part C was run

**Status of this amendment.** Appended, not edited in. Nothing above this line is changed.
It is registered **before the two test sets were opened**: the chained job that would have
run Part C was stopped with the test sets still unread (`evaluate.py` had not started;
verified by process inspection, and the run log carries no Part C marker). Standing practice
4 is satisfied — no outcome has been seen on `test` or `heldout`.

## A1.1 — D20: the registered numbers come from the artifact that ships

A metric produced by a numeric path nobody runs is not a measurement of the tool. The model
trains on **MPS**; what a user executes is the **ONNX graph under onnxruntime on CPU**,
inside QGIS. Those are different numeric paths.

> **D20.** Part C computes every metric **twice on the identical chips**: once from the
> exported **ONNX graph on the CPU execution provider**, and once from the **PyTorch model**.
> Both are reported. The **maximum per-chip difference between the two paths** is reported
> for each metric and for the raw output.
>
> **If the two paths agree within the tolerance below, the ONNX-on-CPU figures are the
> registered ones.** If they do not, **that disagreement is the finding and it outranks the
> margin over bicubic** — the margin is then reported as provisional and the disagreement is
> the headline.

**Tolerance, registered before the comparison is run:**

| quantity | tolerance | basis |
|---|---|---|
| raw output, max abs per pixel | **< 1e-4 normalised** (= 0.5 DN) | the D17-C bound already registered; float32 accumulation order differs between runtimes |
| PSNR, max abs per chip | **< 0.01 dB** | far below the ~1 dB scale at which any claim here is made |
| SSIM, max abs per chip | **< 1e-4** | four orders below the reported margin |
| MAE, max abs per chip | **< 1e-6 normalised** (= 0.005 DN) | below the last significant digit reported |

**Prediction:** the two paths agree inside every tolerance, because the network contains no
mode-dependent layer (D15) and no operation whose CPU and MPS implementations are expected to
differ beyond float32 accumulation order. The D17-C drill on an interim checkpoint measured
**2.265e-06** normalised at 128 px, two orders inside the raw bound.

## A1.2 — provenance that must travel with the model

Recorded in the ONNX `metadata_props` **and** in the report, so that a future rerun on a
machine whose exporter default differs cannot switch silently:

* **training device: MPS** (Apple M4 Max), not CUDA and not CPU;
* **torch version**, exactly;
* **the export used the LEGACY TorchScript exporter, `dynamo=False`.** torch 2.13 defaults to
  the dynamo exporter, which requires `onnxscript`; that package is absent and this work
  package installs nothing. The TorchScript path supports `dynamic_axes`, which is what D17
  needs, so nothing was given up — but the default differs by torch version, and a silent
  switch would change the graph without changing the code.

## A1.3 — D21: the scope caveat travels with the number

The model learns to invert a degradation **we constructed and know exactly**: a Gaussian
low-pass at MTF 0.3 followed by decimation by two (D9). Beating bicubic at that task by a
wide margin is partly a statement about how well the model inverts a **known synthetic
blur** — not about how well it super-resolves real imagery at 5 m, where there is no ground
truth and the true 10 m -> 5 m relationship is not that blur.

> **D21.** That sentence is printed **next to the number, every time the number appears** —
> in the report at every occurrence of the margin, and in the evaluation tool's own stdout.
> Not in a limitations section at the end. **The number and its scope travel together, or the
> number gets quoted alone.**

This is registered as a reporting *rule*, not a caveat to be recorded once. A caveat filed
elsewhere is a caveat that will be separated from its number the first time someone copies
the number into a slide.
