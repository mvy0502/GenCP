# WP7 registration — scale 4, four bands

**Registered:** 2026-08-30, Project 2 WP7, **before B08 was joined to a single chip, before
the bicubic control was recomputed at scale 4, before any model existed and before any metric
was seen.** The only measurements that precede this file are *input* measurements, quoted in
§3 and §4: the B08 clear-pixel distribution and the B08 grid-identity check.

This file is never edited to match a result. The constants it names live in
`tubitak/sr/sr_data/params.py` and `tubitak/sr/sr_train/config.py` and are imported, never
restated as literals.

**Repository state.** Branch `tubitak-tr`, HEAD **`54bfd94`**. The brief names `6b09e92`; that
was HEAD when the brief was written and `54bfd94` is one commit later — the narrow-unfreeze
plugin text fixes. Nothing in that commit touches `sr_core`, `sr_data` or `sr_train`.

**The plugin is frozen and is not touched by this work package.** Everything here is in
`tubitak/sr/sr_data/` and `tubitak/sr/sr_train/`.

---

## 1. What is inherited unchanged, and the check that proves it

**D23. B08 is JOINED to the existing chips. `build_corpus.py` is NOT re-run.**

Re-running the screening over four bands would change the accepted chip set, and that would
invalidate three things at once: the v2 manifest, `config.DEDUP_ORDER_COUNTS`, and the
`== 47` anchor in `leakage.py` that is the **only independent arm** of the leakage gate — the
one number measured by a different implementation in a different work package. A corpus whose
leakage gate has lost its independent arm is not worth the bands it gained.

So the following carry over **untouched**, and §2 of the report shows the check that confirms
each is byte-identical to what WP3B used:

| carried over | artefact |
|---|---|
| accepted chip set | `tubitak/data/sr_wald_corpus/chips_{train,val,test,heldout}.npy` |
| the corrected split, dedup and buffer | `tubitak/data/sr_wald_split_v2/manifest_v2.csv`, `split_v2.json` |
| leakage verdict | `tubitak/data/sr_wald_split_v2/leakage.json` — 0/457 test, 0/1332 heldout |
| screening counts | `config.DEDUP_ORDER_COUNTS` |

**The new arrays are written to a NEW directory, `tubitak/data/sr_wald_corpus_x4/`.** The
WP3B corpus is not overwritten, so a WP3B number can still be reproduced after this.

---

## 2. D22 — scale 4 keeps the 256 px target; the input becomes 64 px

`256 / 4 = 64`, so the chip geometry is unchanged and nothing breaks arithmetically.

**The targets are NOT re-cut to 512 px.** That would need `BLOCK_CHIPS = 7`
(`splits.py:59-63` requires the 42-chip grid to divide exactly into 3 × 3 blocks), blocks
would then hold at most 49 chips, and `MIN_BLOCK_CHIPS_FOR_EVAL = 50` would make
`split_fix.py` raise. **Re-deriving that floor to make a split fit is how a leak gets in**, so
it is not touched.

### Receptive field, stated twice because it is two different distances

The architecture is unchanged from WP3B — `SRNet`, all 3 × 3 convolutions, `N = 6` residual
blocks — so the receptive field in **input pixels** is unchanged at **31** (`7 + 4N`,
measured by gradient support, not only derived). What changes is what an input pixel *is*:

| phase | input GSD | RF in input px | **RF in metres of ground** | input chip / tile |
|---|---|---|---|---|
| **training** (Wald, 40 m → 10 m) | **40 m** | 31 | **1240 m** | 64 px = 2560 m |
| **inference** (10 m → 2.5 m) | **10 m** | 31 | **310 m** | `INFER_TILE_SRC_PX` px |

**Is 64 px of context enough?** Yes, and the number is 31 < 64: the receptive field fits
inside the training chip with room, so only output pixels within 15 input px of the chip edge
see truncated context, and those are exactly the pixels the inference overlap covers. What 64
px does **not** give is more context than 31 px — the network cannot use it — so a claim that
the model "sees 2560 m of ground" would be false. It sees **1240 m at training and 310 m at
inference**, and those two numbers are not the same physical scale.

---

## 3. D24 — the normalisation constant, re-derived

**Measured first, over the same clear-pixel sample WP2A used** — every clear pixel of all five
granules, `n = 554,534,176` per band, exact 16-bit histogram, not a subsample. The three
visible bands reproduce WP2A §6.1 exactly, which is the check that the sample is the same one:

| band | min | p1 | p50 | p99 | **p99.9** | p99.99 | max | mean | ≥ 5000 DN |
|---|---|---|---|---|---|---|---|---|---|
| B02 | 0 | 76 | 644 | 2676 | 4084 | 6299 | 20703 | 765.1 | 234,027 |
| B03 | 0 | 287 | 1006 | 3181 | 4663 | 6602 | 18975 | 1146.3 | 385,031 |
| B04 | 0 | 107 | 1094 | 3608 | 5029 | 6709 | 17891 | 1249.1 | 576,342 |
| **B08** | 0 | **507** | **3055** | **5654** | **6650** | **7388** | **16465** | **3120.6** | **17,838,150** |

**B08 is a different animal.** Its median (3055) is three to five times the visible bands',
and **17.8 million clear pixels — 3.2 % — sit at or above 5000 DN**, against 0.04–0.10 % for
the visible bands. Under WP3B's `NORM_DIVISOR_DN = 5000` its p99.9 would normalise to
**1.330**, well outside a nominal full scale of 1.

> ### **`NORM_DIVISOR_DN = 10000.0`, that is: normalised = surface reflectance.**

`10000` is `1 / DN_TO_REFLECTANCE`, so the normalised value **is** the reflectance the
product encodes. Chosen for three reasons, in order:

1. **It is a physical constant, not a fitted one.** WP3A picked 5000 because it mapped the
   brightest visible band's p99.9 to ≈ 1.006 — a corpus-derived number that stops being right
   the moment the band set changes, which is exactly what has happened. 10000 does not depend
   on which bands are in the corpus.
2. **`PSNR_DATA_RANGE = 1.0` becomes a physical claim**: full scale is 100 % reflectance.
   Under it every band's p99.9 is ≤ **0.665** (B08) and the corpus maximum is 1.65, so nothing
   is clipped and the headroom is real.
3. **It makes our input domain identical to the reference model's.** wsx4's graph divides by
   10000 internally (`05-referans-arac.md` §3). Two models that disagree about what "1.0"
   means cannot be compared even qualitatively.

**The cost, stated:** the data occupies about two thirds of the nominal range rather than
filling it. That is accepted.

> **Why the new metrics are not comparable with the +5.574 dB recorded in `03b-training.md`:
> that number was measured at scale 2, on three bands, in a domain where full scale was
> DN/5000; this one is scale 4, four bands, DN/10000, against a different bicubic control on a
> harder task — four of the five things a PSNR depends on have changed.**

A note on which parts of the metric move with the divisor, because it matters for reading the
report: **the paired PSNR difference in dB is invariant** to it — `10·log10(MSE_b/MSE_m)`
cancels the scale — while **MAE scales linearly** with `1/divisor` and **SSIM changes**,
because its stabilising constants are defined against the data range.

---

## 4. D23 — the B08 join, and its grid check

B08 is on the same 10 m grid as B02/B03/B04. **Asserted, per granule, before the join**, and
the transform is compared, not only CRS and shape:

| granule | B08 vs that granule's B02 |
|---|---|
| 36TVK, 36TUK, 36SVJ, 36SWJ, 36SXJ | **IDENTICAL** — 10980 × 10980, uint16, EPSG:32636, same affine |

**Known-false, registered with it:** B08 of one granule against a *different* granule's B02
must be rejected. All five granules share EPSG:32636 and 10980 × 10980, so **only the
transform separates them**, and a check comparing CRS and shape alone would pass every wrong
pairing. Measured: **3 of 3 pairs rejected, each differing in `transform`.**

**Band order in the stored array: `B02, B03, B04, B08`** — the three existing planes in their
existing order, with B08 appended as plane 4. `params.BANDS` becomes that tuple and is the one
definition.

---

## 5. D25 — the degradation at scale 4 is a different physical claim

`sigma_for_mtf` is general in `scale`; `s = 4` is a parameter change and not a redesign. The
sigma follows from the same derivation:

```
f_nyq = 1/(2*scale) = 0.125 cycles per source pixel
s^2   = -ln(0.3) / (2*pi^2*f_nyq^2) = 1.2039728 / 0.30842514 = 3.9036...
sigma = 1.97575666 source px  =  19.7576 m at a 10 m GSD
```

> **STATED ASSUMPTION, and it is weaker than the one at scale 2.** MTF 0.3 at the **40 m**
> Nyquist frequency **is not the Sentinel-2 sensor MTF**, because **no Sentinel-2 band samples
> at 40 m**. At scale 2 the corresponding claim at least named a sampling the instrument
> really has (20 m, the B05–B12 grid); at scale 4 it names one it does not have at all. The
> 40 m image this corpus contains is a **construction**, not a coarser real product, and the
> model learns to invert **that construction**.
>
> **The phrase "MTF 0.3" therefore does not carry over from WP3B as though it meant the same
> thing.** It named a plausible sensor-like blur there; here it names a chosen blur with no
> instrument behind it.

`MTF_AT_NYQUIST` stays 0.3 so that the two corpora differ in one variable, not two.

---

## 6. D26 — the bicubic control, recomputed, and how it must be read

Recomputed on the corrected split **before training**, in the new domain, with the WP3A
conventions restated once and unchanged: **normalised reflectance `DN / 10000`, float32,
unclipped; PSNR data range 1.0; every metric PER CHIP and reported as the UNWEIGHTED MEAN
over the chips of that split; the two test sets separate and never pooled**; upsampler
`sr_core.upsample.BicubicUpsampler(scale=4)`, imported read-only; degradation
`sr_data.degrade.degrade_chip`, imported, never reimplemented.

> **A larger margin at scale 4 is the TASK BECOMING EASIER TO BEAT, not the model improving.**
> Bicubic loses far more at 4× than at 2×, so the bar is lower and any model clears it by
> more. **The scale-4 margin is never to be compared with the scale-2 margin.** This sentence
> travels next to every occurrence of the margin, as D21 requires of the scope caveat.

---

## 7. D27 — the commutation known-false must test the phase that matters

`train.py` guards the pre-degraded cache with a check that the degradation commutes with the
8 dihedral transforms, whose known-false arm was `t[:, ::2, ::2]` — a phase-0 decimation by
**two**. At `s = 4` that still returns a differing array, so the gate would report success
while **no longer testing the s = 4 phase at all**: a known-false that has decayed into a
no-op, which is worse than none because it looks like coverage.

> **The known-false becomes a phase-0 decimation by the CONFIGURED scale, `t[:, ::s, ::s]`,
> with no filter.** Predicted: it does **not** commute with the dihedral group, and the check
> reports it. The check is not trusted unless that failure is observed at the scale actually
> configured.

---

## 8. D28 — band order asserted, not assumed

**New, and it closes a trap that is already live.** `onnx_upsample.validate_input` checks
**channel count only**. Once our model is also four bands, `DEMO_INPUT_WSX4_*.tif` satisfies
its guard and would run in whatever order its bands happen to be, producing a plausible image
from the wrong bands — the dominant failure class in this project.

> **The band order is written into the model's ONNX `metadata_props` as `band_order`, and is
> asserted wherever the model is loaded in `sr_train`.** Known-false: an input whose band
> order is a swap of two planes must be **refused**, not run.

Measured in WP6 on the reference model: swapping two bands changed pixels by **max 1328 DN,
median 36 DN** and the result still looked like an image. That is why this is an assertion and
not a comment.

**The plugin is frozen, so its copy of the guard is NOT changed this week.** That is recorded
as an open item, not fixed here.

---

## 9. Registered before they were run: the checks

| # | check | known-true | known-false | predicted |
|---|---|---|---|---|
| X1 | B08 on the same grid as B02 | each granule | B08 vs another granule's B02 | true passes, false caught |
| X2 | the split carries over unchanged | v2 manifest hashes | — | byte-identical to WP3B |
| X3 | degradation commutes with the dihedral group **at s = 4** | the real degradation | phase-0 decimation by **4** | true 0.0, false non-zero |
| X4 | target is exactly 4 × the input | a real corpus pair | a deliberately 2× target | true passes, false caught |
| X5 | band order asserted | correct order | two planes swapped | true passes, **false refused** |
| X6 | ONNX-on-CPU equals PyTorch | the exported graph | — | max abs diff < 1e-4 normalised |

## 10. Invariance — what must not change for these numbers to mean what they claim

1. **The chip arrays and the v2 split.** Only the band dimension grows, 3 → 4.
2. **`BANDS = ("B02","B03","B04","B08")`** in that order, in the stored array and in the model
   provenance.
3. **`NORM_DIVISOR_DN = 10000.0`** and **`PSNR_DATA_RANGE = 1.0`** together. Either alone is
   meaningless.
4. **`SCALE = 4`, `CHIP_PX = 256`, input 64 px.**
5. **`MTF_AT_NYQUIST = 0.3`**, with §5's assumption attached to it wherever it is quoted.
6. **Test sets read once, at the end.** Model selection on `val` only.
7. **The scale-4 margin is never compared with the scale-2 margin.**

---

## 11. Amendment, 30 August 2026 — before any training outcome was seen

Standing practice 4 permits a registration to be revised when an *input measurement* improves
and no outcome has been seen. Both conditions hold: the degradation was found to be wrong at
scale 4, and no model had been trained. Sections 1–10 above are unchanged and are the earlier
version; this section records what changed and why.

### 11.1 D29 — the decimation kernel was asymmetric at scale 4

Check **X3** (degradation commutes with the dihedral group at s = 4) failed on its first real
invocation: `max |diff| = 4.032e-05` where an exact commutation is required, with the
known-false correctly at `2.985e-01`.

The cause was in `gaussian_decimation_kernel`. The kernel samples the block centre, which sits
at `(scale - 1) / 2` source pixels — `0.5` at scale 2, `1.5` at scale 4. The candidate window
was built as `arange(-r, r+1)`, centred on **zero**, and only afterwards filtered by distance
from the block centre. At scale 4 that truncates one side: offset `+9` lies within the radius
of the centre (`|9 - 1.5| = 7.5 < 7.903`) but was never a candidate, so the kernel ran `-6..8`
instead of `-6..9`.

| scale | centre | offsets before | offsets after | first moment about the centre, before |
|---|---|---|---|---|
| 2 | 0.5 | −3..4 | −3..4 (**identical**) | 0.0 |
| 4 | 1.5 | −6..8 | −6..9 | **−1.125e-03 source px** |

A non-zero first moment is a translation. The scale-4 degradation was shifting every input by
about a thousandth of a pixel — the exact property `degrade`'s own docstring promises does not
exist ("the filter introduces no shift"). Scale 2 was symmetric only because
`ceil(4 sigma) = 4` and the filter happened to keep `−3..4`; that is arithmetic coincidence,
not a property anyone chose.

**The window is now built around the centre**: integers in `[ceil(c − R), floor(c + R)]`.
After the fix both scales have a first moment of exactly 0.0, and X3 reports `0.000e+00`
known-true against `2.985e-01` known-false.

**Scale 2 is byte-identical.** The offsets are unchanged, verified by direct comparison of the
old and new offset sets. WP3B's corpus, control and model are unaffected and are not restated.

This is the fifth instance of this project's recurring defect shape, and the second in this
work package: **code that assumes a parameter, met by a different one.** D27 was written for
the same shape (a known-false hard-coded to `::2`). The other two found here were
`degrade_chip` called without `scale` in `train.py` and `evaluate.py`, and `mtf_at` called
without `scale` in `corpus_checks.c4` — which evaluated the scale-2 filter at the scale-4
Nyquist frequency and reported 0.7401 against a registered 0.3. In every case a module-level
default derived from `params.SCALE = 2` silently stood in for the variant's scale.

**What the checks are worth.** Three of the four were caught by a registered check firing, not
by reading the code: X3 found the kernel, C4's value case found `mtf_at`, and the loss shape
found the dataloader. The one that review would have had to catch — the kernel — is the one
that would have been invisible in every output.

### 11.2 The bicubic control at scale 4 is recomputed

The control figures computed before the kernel fix (test PSNR 33.9800 / SSIM 0.847327 /
MAE 0.01374359; heldout 33.9545 / 0.845535 / 0.01382300; val 34.4125 / 0.854320 / 0.01312691)
were produced against the shifted degradation. They are **superseded, not deleted**: they are
recorded here so the two are never confused, and no number in the report is taken from them.
D26's control is recomputed against the corrected degradation before training begins, and the
model is compared only with that recomputation.

### 11.3 The schedule, registered before the run

Section 1–10 did not state one. It is registered here, before any training step is taken.

| | |
|---|---|
| registered schedule | **20,000 steps**, matching WP3B so the optimisation effort is comparable |
| wall-clock budget | **60 minutes**, whichever comes first |
| batch | 32 |
| checkpoints | every 500 steps |
| selection | validation loss only; the two test sets are opened once, at the end |
| probe | 120 steps at **17.57 steps/s** on an idle machine, extrapolating to 19.0 min |

The budget is deliberately **3.2x the probe's extrapolation** rather than the 1.0x WP3B chose.
WP3B's probe measured 4.46 steps/s idle and the run achieved 2.265 under contention, so the
budget bound first and the run stopped 3,694 steps short of its schedule. The finding recorded
there — *a resource budget measured under conditions that do not match the spending conditions
is an estimate, not a measurement* — is acted on here in the only way that does not require
trusting the estimate: the budget is set so that being wrong by a factor of three still lets
the schedule complete. The probe was run on an idle machine and the run will be too.

The scale-4 run is faster than scale 2 for a structural reason, not a mysterious one: the
trunk operates at input resolution, which is 64x64 here against 128x128 at scale 2, so it does
a quarter of the work per chip.

### 11.4 Invariance item 8 — SSIM and the normalisation divisor

§10's list is extended by one item. It is written separately from item 7 rather than folded
into it, because item 7 is a rule about the **scale** and this is a rule about the
**divisor**. Item 7 would forbid the specific comparison at issue today only by accident, and
would not fire at all for two models at the same scale under different divisors.

> **8. An SSIM is comparable only against another SSIM computed under the same normalisation
> divisor — including an SSIM *margin*.**
>
> SSIM's stabilising constants `C1 = (K1·L)²` and `C2 = (K2·L)²` are defined against the data
> range `L`, which is pinned at 1.0 while the signal is divided by the divisor. Changing the
> divisor therefore changes SSIM by an amount that **depends on the image content and does not
> cancel in a difference**. Measured on the scale-4 control: **+0.119552, +0.125963,
> +0.121339, +0.123894** across the four cells of the 2 x 2 in `07-x4-model.md` §1.2 — not a constant, and **1.7
> times the size of the entire +0.070506 SSIM margin** WP3B recorded.
>
> **PSNR is the exception and it is exact, not approximate.** The divisor adds a constant
> `20·log10(ratio)` to every chip's PSNR — verified as `6.0205999133 dB` on **all 1789 chips**
> of `test` and `heldout`, maximum deviation `1.33e-14 dB` — so it cancels exactly in a paired
> PSNR difference. **An absolute PSNR is still not comparable across divisors; only the
> margin is.**
>
> **MAE scales by exactly the divisor ratio** (measured: `2.0000000000` in all four cells), so
> an absolute MAE margin is not comparable across divisors either. A *relative* MAE margin
> would be.
>
> The practical form of this rule: **`03b-training.md`'s SSIM margin of +0.070506 (heldout)
> and +0.070725 (test), at divisor 5000, may never be set beside any SSIM margin in
> `07-x4-model.md`, which is at divisor 10000.** The PSNR margins may not be compared either,
> but for item 7's reason — different tasks — not for this one.

### 11.5 A correction to §3's wording: the chip SSIM is now a four-band mean

`03a-wald-corpus.md` and `03a-corpus-registration.md` define the chip SSIM as *"the three
per-band SSIMs averaged"*. `sr_data.metrics.ssim_chip` averages over **all** planes, so at
scale 4 it averages **four**, B08 included. The code was always general; the registered
wording was specific to the band set of the day and is now incomplete.

It is not cosmetic. B08 was measured to be the **hardest** of the four bands (`07-x4-model.md`
§1.2: adding it costs 0.589 dB on heldout and 0.982 dB on test), so the fourth plane pulls the
chip SSIM down. A reader applying the three-band definition to a scale-4 SSIM would be reading
a four-band number under a three-band description. **Every SSIM in WP7 is a four-band mean and
is labelled as one.**
