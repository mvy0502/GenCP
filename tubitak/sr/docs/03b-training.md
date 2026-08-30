# Project 2, WP3B — corrected split, training, evaluation, ONNX export

**Run:** 2026-08-30. **Repository:** `mvy0502/GenCP`, branch `tubitak-tr`, clean at `ba80f3f`
when this started. **No git command was run.**

**Registration:** [`03b-registration.md`](03b-registration.md), written **15:07:41**, before
the corrected split was built, before the control was recomputed, before any model existed.
Amendment 1 (D20/D21) appended **17:12:38**, before the test sets were opened. Neither file
has been edited to match a result.

**The boundary was respected.** `tubitak/qgis_plugin/` — symlinked into the live QGIS profile
and demonstrated on Friday — was not touched. Neither was `tubitak/sr/sr_plugin/`,
`tubitak/gencp_core/`, or the upstream tree. `git status --porcelain` restricted to each is
empty. All new code is in `tubitak/sr/sr_train/`; `sr_data` and `sr_core` are imported
read-only and are byte-identical to their committed state.

---

## 0. The headline, with its scope attached

**On the held-out granule 36SXJ, the model beats the registered bicubic control by
+5.574 dB PSNR (paired, per chip), and is worse on 0 of 1332 chips.**

> **SCOPE OF THIS NUMBER.** The model inverts a degradation we constructed and know exactly:
> a Gaussian low-pass at MTF 0.3 followed by decimation by two. Beating bicubic at that task
> is partly a statement about how well the model inverts a **known synthetic blur** — not
> about how well it super-resolves real imagery at 5 m, where there is no ground truth and
> the true 10 m → 5 m relationship is not that blur.

That sentence appears beside every occurrence of the margin in this document, per **D21**. It
is a reporting rule, not a limitations paragraph, because a caveat filed at the end is a
caveat that gets separated from its number the first time the number is copied into a slide.

**Every number from this model carries its step count.** Registered schedule **20,000 steps**;
the run **stopped at 16,306** on its wall-clock budget; the shipped checkpoint is **step
16,000**, the best by validation loss. A model stopped early is a **different model**, not a
noisier version of the same one.

---

## 1. Where the compute happened, stated plainly

**Training ran on this Mac's own GPU (Apple MPS). It did NOT run on Kaggle.** Nothing was
uploaded to Kaggle, no kernel was submitted, and no Kaggle quota was consumed — which is why
the Kaggle "Active Events" panel shows nothing.

This is a **deviation from the brief**, which specified a Kaggle T4, and it was taken on the
measurement the brief itself demanded. The probe (§5.1) put the full schedule at ~75 minutes
locally. Kaggle would have meant a 2.4 GB dataset upload plus kernel orchestration to produce
the same model more slowly and with less of it observable from here. The Kaggle path is not
commissioned and remains available: the corpus and the training script are unchanged, so it
is an upload and one command.

**It is fair to say the deviation cost something.** §5.2 records that the local GPU was
contended by this session's own verification work, the run missed its registered schedule,
and the shipped model is a 16,000-step model rather than a 20,000-step one. On an uncontended
T4 that would probably not have happened.

---

## 2. Part A — the corrected split

### 2.1 Input measurements, taken before the rule was chosen

Standing practice 4 permits a registration revision when an input measurement improves and no
outcome has been seen. These are those measurements.

**Chip grids of different granules do not align.** NW corner modulo the 2560 m chip:

| granule | easting mod 2560 | northing mod 2560 |
|---|---|---|
| 36TVK | 600.0 | 2080.0 |
| 36TUK | 480.0 | 2080.0 |
| 36SVJ | 600.0 | 1960.0 |
| 36SWJ | 780.0 | 1960.0 |
| 36SXJ | 960.0 | 1960.0 |

**Zero exact-corner matches** between any two granules. "The same ground in two granules" is
therefore always a **partial footprint overlap**, never a duplicated chip — so a rule based
on chip equality would have removed nothing, and the overlap predicate had to be geometric.

**Cross-granule overlap among accepted chips**, 428 ordered pairs:

| pair | chips of the first overlapping some chip of the second | datatake |
|---|---|---|
| 36SVJ × 36SWJ | 114 | same (A008614) |
| 36SVJ × 36TVK | 96 | same |
| 36TUK × 36TVK | 47 | same |
| 36SWJ × 36TVK | 9 | same |
| 36SVJ × 36TUK | 3 | same |
| **36SXJ × anything** | **0** | — |

**Per-block accepted chips (196 candidates per block), before dedup:**

| granule | the nine 14 × 14 blocks | min | blocks ≥ 50 |
|---|---|---|---|
| 36TVK | 77, 151, 130, 173, 160, 154, 105, 107, 138 | 77 | 9/9 |
| 36TUK | 68, 64, 103, 127, 99, 109, 149, 117, 84 | 64 | 9/9 |
| 36SVJ | 168, 178, 166, 110, 176, 169, 176, 195, 189 | 110 | 9/9 |
| 36SWJ | 184, 175, 64, 186, 162, **47**, 123, 141, **0** | 0 | **7/9** |
| 36SXJ | 185, 154, 151, 176, 156, 84, 159, 160, 107 | 84 | 9/9 |

`MIN_BLOCK_CHIPS_FOR_EVAL = 50` was chosen with these in front of it and is satisfiable
everywhere with room to spare — 7 eligible blocks in the worst granule against the 2 needed
for val + test.

### 2.2 D13 step one — deduplication across granules

Rule as registered: granules in **ascending accepted-chip count** (36TUK 1036, 36SWJ 1122,
36TVK 1283, 36SXJ 1332, 36SVJ 1659), keeping a chip unless its footprint overlaps one already
kept from an earlier granule.

| granule | chips in | dropped | dropped against |
|---|---|---|---|
| 36TUK | 920 | **0** | — |
| 36SWJ | 1082 | **0** | — |
| 36TVK | 1195 | **59** | 36TUK 72, 36SWJ 25 |
| 36SXJ | 1332 | **0** | — |
| 36SVJ | 1527 | **201** | 36TVK 122, 36SWJ 188, 36TUK 3 |
| **total** | 6056 | **260** | |

**The registered prediction held: 0 chips were removed from 36SXJ**, and every removal fell
inside datatake A008614. The ascending-count order did what it was chosen to do — the two
scarcest granules lost nothing and 36SVJ, with the largest surplus, paid.

### 2.3 D13 step two — yield-aware blocks and a corpus-wide buffer

Block yields after dedup, with `*` marking blocks eligible for val/test (≥ 50) and the
assignment that followed:

| granule | blocks (yield, eligibility, assignment) |
|---|---|
| 36TVK | 64\*tr 151\*va 130\*tr 152\*tr 160\*tr 154\*te 89\*tr 107\*tr 129\*tr |
| 36TUK | 68\*te 64\*va 103\*tr 127\*tr 99\*tr 109\*tr 149\*tr 117\*tr 84\*tr |
| 36SVJ | 143\*va 145\*tr 99\*tr 110\*tr 176\*tr 133\*tr 176\*te 195\*tr 149\*tr |
| 36SWJ | 184\*tr 175\*tr 64\*tr 186\*tr 162\*tr **47 tr** 123\*te 141\*va **(2,2) absent, 0 chips** |
| 36SXJ | held out whole |

36SWJ's two ineligible blocks — (1,2) at 47 chips and (2,2) at 0 — are now **train**, and its
eval blocks are drawn from the seven that can actually carry an evaluation.

The corpus-wide buffer then dropped **265** further chips.

### 2.4 The corrected split, beside WP3A's

| | WP3A (leaked) | WP3B (corrected) |
|---|---|---|
| train | 3846 | **3320** |
| val | 475 | **422** |
| test | 403 | **457** |
| heldout | 1332 | **1332** |
| removed | buffer 376 | dedup **260** + buffer **265** |
| total kept | 6056 | **5531** |

Per granule × split:

| granule | train | val | test | heldout |
|---|---|---|---|---|
| 36TVK | 771 | 114 | 138 | — |
| 36TUK | 771 | 53 | 54 | — |
| 36SVJ | 968 | 114 | 164 | — |
| 36SWJ | 810 | 141 | **101** | — |
| 36SXJ | — | — | — | 1332 |

**WP3A open item 1 is closed. 36SWJ contributed 0 test chips before and contributes 101 now**,
so the in-distribution test set covers all four training granules including Tuz Gölü, the
compositional-outlier site. 36TUK's 54 test chips sit just above the 50 floor, which is the
rule biting rather than a coincidence.

### 2.5 D18 — the leakage gate

`tubitak/sr/sr_train/leakage.py`, exit 0. Known-false cases first.

| case | result |
|---|---|
| **KF2** WP3A's own manifest | **47 leaking test chips — reproduces WP3A open item 8 exactly.** Also 67 within the 2560 m buffer (16.63 %), and val 27 / 33, heldout 0 / 0 |
| **KF1** a planted train→test relabel | **detected**, 47 → 48. It could not be planted on the corrected split — after dedup no 36SVJ train chip overlaps a 36SWJ train chip at all — so it was planted on the WP3A manifest instead. That failure to plant is itself the fix working |
| **DG** empty manifest | **refused** to emit a verdict |
| **KT** the corrected manifest | **test 0/457, heldout 0/1332, val 0/422 — zero at both radii** |

**GATE D18: PASS.** KF2 is the case that matters: an independent implementation in a
different work package measured 47, and this checker reproduces 47 on the same input. A
leakage checker that cannot find 47 where 47 is known to be is not a checker.

### 2.6 The control, recomputed — old numbers retained, not replaced

Same conventions, same imported upsampler and degradation; only chip membership differs.

| split | n | PSNR (dB) | SSIM | MAE | status |
|---|---|---|---|---|---|
| test (WP3A) | 403 | 31.9420 | 0.863073 | 0.01798890 | **retained, relabelled: measured on the leaked split** |
| **test (WP3B)** | **457** | **33.1621** | **0.894002** | **0.01457318** | **the registered bar** |
| heldout (WP3A) | 1332 | 33.0050 | 0.894263 | 0.01506987 | retained |
| **heldout (WP3B)** | **1332** | **33.0050** | **0.894263** | **0.01506987** | **the registered bar** |
| val (WP3A) | 475 | 32.2923 | 0.880694 | 0.01704687 | supplementary |
| val (WP3B) | 422 | 33.7517 | 0.897450 | 0.01379849 | supplementary |

**The registered prediction held exactly.** `heldout` is **33.0050029565 dB under both
splits — identical to ten decimal places** — confirming that neither dedup nor the
corpus-wide buffer touched 36SXJ, as predicted from its measured zero overlap. Had it moved,
the reason would have had to be found before Part B.

`test` rose 1.22 dB. **That is not the leak being removed; it is a different set of ground.**
The block assignment changed wholesale, because the seeded permutation is now drawn over
eligible blocks only. The two `test` numbers are measurements of two different chip sets and
neither is a correction of the other.

---

## 3. Part B — the model

### 3.1 Architecture, and the two structural decisions

`tubitak/sr/sr_train/model.py`. Residual CNN, `C = 64`, `N = 6`, all convolutions 3 × 3, one
`PixelShuffle(2)`, global nearest-neighbour skip built from `repeat_interleave` + the same
shuffle — a shuffle, not a resize. **488,780 parameters.**

**D15 — no mode-dependent operation.**

| check | result |
|---|---|
| modules that behave differently in train/eval | **NONE** (no BatchNorm, no InstanceNorm, no dropout) |
| max abs difference, `train()` vs `eval()`, fixed input | **exactly 0.0**, as predicted |

`torch.onnx.export` calls `.eval()` by default; with no mode-dependent layer that call cannot
change behaviour. Project 1 paid for that trap once; this removes the class of bug.

**D16 — receptive field measured, not only derived.** By gradient support: place a unit
gradient on one output pixel, count input pixels with non-zero gradient.

| depth | derived (7 + 4N) | **measured** |
|---|---|---|
| N = 2 | 15 | **15** |
| **N = 6 (chosen)** | **31** | **31 × 31** |
| N = 7 | 35 | **35** — exceeds 32, refused |

**RF 31 ≤ the 32 px tiling overlap**, so `INFER_OVERLAP_SRC_PX = 32` is retained unchanged and
depth was chosen to fit it. The measurement tracks depth in both directions, so it is a
measurement and not a constant. **What the other choice would have cost:** raising the overlap
to 48 for two more blocks drops the inference stride from 96 to 80 and takes a granule from
115 × 115 = 13,225 tiles to 138 × 138 = 19,044 — **+43.9 % forward passes.** Depth was the
cheaper thing to give up.

### 3.2 The loss — D14

**Charbonnier**, `sqrt((pred − target)² + eps²) − eps`, `eps = 1e-3` normalised (= 5 DN). L1
everywhere except within eps of zero, where it is quadratic, removing the gradient
discontinuity at exactly zero; at 5 DN the quadratic region is far below the noise floor, so
on every error magnitude that occurs it *is* L1. **No adversarial term. No perceptual term.**
The reason is the application: this model feeds keypoint matching, and invented texture that
looks sharp produces keypoints corresponding to nothing on the ground.

### 3.3 A check the pre-degraded cache depended on

Degrading once and augmenting afterwards is only valid if the degradation **commutes** with
the 8 dihedral transforms. Not assumed — checked, and the run refuses to start if it fails:

* real degradation: max |diff| **0.000e+00** across all 8 transforms;
* known-false (phase-0 decimation, no filter): **5.996e-01** — the check can fail.

---

## 4. Part B — the training run

### 4.1 The schedule, stated twice

| | |
|---|---|
| **registered schedule** | **20,000 steps** |
| **run stopped at** | **16,306 steps** — `stop_reason = budget` |
| **shipped checkpoint** | **step 16,000**, best by validation loss |
| wall clock | 7200.2 s = **120.0 min**, exactly the registered budget |
| rate achieved | **2.265 steps/s** |
| best val Charbonnier | **0.006934** |
| device | **MPS**, Apple M4 Max |
| seed | `TRAIN_SEED = 20260831` |
| versions | torch 2.13.0, numpy 2.4.6, Python 3.11.15, onnxruntime 1.29.0 |

**The stated stop rule was honoured and the budget was not extended to chase a number.** The
model is 81.5 % of the registered schedule. Validation was still improving when it stopped
(0.006975 → 0.006939 → 0.006934 over the last three checks), so a completed run would
probably be slightly better — that is a reason to rerun, not a reason to quote a number the
run did not produce.

Validation curve, every 3000 steps: 500 → 0.008131, 3500 → 0.007268, 6500 → 0.007106,
9500 → 0.007018, 12500 → 0.006975, 15500 → 0.006939, best 16000 → **0.006934**.

**These three numbers are written into the ONNX `metadata_props`** —
`registered_schedule_steps=20000`, `completed_steps=16306`, `stop_reason=budget`,
`checkpoint_step=16000` — so the step count travels with the weights and not only with this
report.

### 4.2 The probe missed by 2×, and the general form of why

| | steps/s | 20,000 steps |
|---|---|---|
| probe, uncontended GPU, 100 steps | **4.46** | 74.7 min |
| the actual run | **2.265** | 147 min (would have been) |
| ratio | **1.97× slower** | |

The probe was not wrong about the machine; it was a measurement of a **different machine
state** than the one that was later spent. During the run this session was also computing the
val-only read, the ONNX export drill and the recomputed control — all on the same GPU.

> **A resource budget measured under conditions that do not match the spending conditions is
> an estimate, not a measurement.**

This is recorded as a finding, not as an excuse for the shortfall. It is mine: the budget
check asked exactly the right question and I ran it under conditions I then failed to
reproduce. Two consequences compound in the same direction — the model is short of its
schedule, **and** the cause is a measurement error rather than a property of the hardware or
the task. The cheap fix is to probe under the load the run will actually experience, or to
leave the device idle for the run.

### 4.3 Checkpointing and resume — exercised, not asserted

Checkpoints every 500 steps to the run directory. **The resume path was run before the full
run, not believed:** a 600-step leg wrote `last.pt`; a second invocation resumed from it,
reported `resumed ... at step 600, best val 0.008453`, and continued to 700 with the optimiser
state restored.

**A defect found at teardown, reported rather than tidied away.** After the training loop
ended and `train_record.json` was written, the process **hung on its final redundant
`last.pt` write** — stuck at 8192 bytes, 0.2 % CPU, not progressing, and it had to be killed.
Nothing was lost: `best.pt` (5,894,549 B) and the run record were already complete on disk,
and `best.pt` was verified to load and forward correctly afterwards. **The 8192-byte partial
file was renamed `last.pt.TRUNCATED`** so that nothing can mistake it for a resumable
checkpoint — the same discipline `sr_core.mosaic.atomic_path` applies to rasters, which this
save path does not have. It also means the chained job waiting on the process's final log line
would have waited forever; it was stopped and the remaining stages were run directly. Cause
not diagnosed; it is an open item.

### 4.4 The discipline that makes the control mean something

**The two test sets were read exactly once, at the end, and this held.** `train.py` calls
`data.load_split` for `train` and `val` and for nothing else. Model selection used `val` only.
One `val`-only reading was taken mid-run (permitted, and reported: +4.66 dB at ~step 2000).

When Amendment 1 arrived, a chained job that would have run Part C automatically was **stopped
with the test sets still unread** — `evaluate.py` had not started, verified by process
inspection, and the run log carried no Part C marker. Part C then ran once, after the
amendment, on both numeric paths.

**Augmentation:** the 8 dihedral transforms only. **No photometric augmentation**, which would
have broken the fixed normalisation D12 exists to guarantee.

---

## 5. Part C — the two test sets, read once, on both numeric paths

`checkpoint best.pt step 16000` · ONNX `CPUExecutionProvider` · onnxruntime 1.29.0 ·
torch 2.13.0 · domain normalised reflectance DN/5000 · **per chip, unweighted mean over chips,
never pooled** · PSNR range 1.0.

### 5.1 D20 — do the shipped path and the training path agree?

| split | raw max | PSNR max/chip | SSIM max/chip | MAE max/chip | verdict |
|---|---|---|---|---|---|
| test | 1.907e-06 | 1.256e-06 dB | 6.527e-09 | 8.202e-10 | **within tolerance** |
| heldout | 1.907e-06 | 1.185e-06 dB | 6.353e-09 | 8.260e-10 | **within tolerance** |
| **registered tolerance** | < 1e-4 | < 0.01 dB | < 1e-4 | < 1e-6 | |

Every quantity is **two to four orders of magnitude inside** its registered bound. **Per D20
the ONNX-on-CPU figures below are the registered ones** — they are the numbers produced by
the artifact that actually ships and runs inside QGIS, not by a path nobody executes.

### 5.2 test — the in-distribution blocks (n = 457)

| metric | ONNX-CPU | PyTorch | bicubic control | **paired (model − bicubic)** | chips model worse |
|---|---|---|---|---|---|
| PSNR (dB) | **38.6629** | 38.6629 | 33.1621 | **+5.500852 ± 1.121333** | **0 / 457** |
| SSIM | **0.964727** | 0.964727 | 0.894002 | **+0.070725 ± 0.021407** | **0 / 457** |
| MAE | **0.00794012** | 0.00794012 | 0.01457318 | **−0.006633 ± 0.002241** | **0 / 457** |

Sign convention: `model − bicubic`; PSNR/SSIM positive = model better, MAE negative = model
better. ± is the standard deviation across chips.

> **SCOPE OF THIS NUMBER.** The model inverts a degradation we constructed and know exactly —
> a Gaussian low-pass at MTF 0.3 then decimation by two. Beating bicubic at that task is
> partly a statement about inverting a **known synthetic blur**, not about how well it
> super-resolves real imagery at 5 m, where there is no ground truth and the true 10 m → 5 m
> relationship is not that blur. **Model: 16,000 steps of a registered 20,000.**

### 5.3 heldout — 36SXJ, whole granule (n = 1332)

| metric | ONNX-CPU | PyTorch | bicubic control | **paired (model − bicubic)** | chips model worse |
|---|---|---|---|---|---|
| PSNR (dB) | **38.5795** | 38.5795 | 33.0050 | **+5.574459 ± 1.055668** | **0 / 1332** |
| SSIM | **0.964769** | 0.964769 | 0.894263 | **+0.070506 ± 0.018698** | **0 / 1332** |
| MAE | **0.00810134** | 0.00810134 | 0.01506987 | **−0.006969 ± 0.002401** | **0 / 1332** |

> **SCOPE OF THIS NUMBER.** The model inverts a degradation we constructed and know exactly —
> a Gaussian low-pass at MTF 0.3 then decimation by two. Beating bicubic at that task is
> partly a statement about inverting a **known synthetic blur**, not about how well it
> super-resolves real imagery at 5 m, where there is no ground truth and the true 10 m → 5 m
> relationship is not that blur. **Model: 16,000 steps of a registered 20,000.**

**The two test sets are never pooled and their absolute PSNRs are never compared with each
other.** WP3A §4.3 established why: 36SXJ has the lowest p99.9 in every band, so bicubic loses
less there for reasons that have nothing to do with the model. Only the margin over the
control **on the same set** means anything. That both margins land near +5.5 dB is worth
noticing and is not evidence that the two sets are equally hard.

### 5.4 What the held-out granule does and does not test

**Does:** transfer to an unseen acquisition — 2026-05-27 against 2026-04-30, orbit R021
against R064, different illumination geometry — and simultaneously to an unseen landform,
Cappadocia tuff badlands. Zero of its chips share ground with any training chip, verified.

**Does not:** separate those two factors. They are **confounded** and this corpus cannot
disentangle them. It is one honest number about two things at once, not a clean
generalisation measurement. It also says nothing about a different sensor, a season beyond
four weeks, a different climate zone, or a different atmospheric state.

### 5.5 Edge density — diagnostic, not a gate, not a claim

Mean gradient magnitude:

| split | model | bicubic | **target** |
|---|---|---|---|
| test | 0.017335 | 0.011150 | **0.020504** |
| heldout | 0.018048 | 0.011802 | **0.021253** |

The model recovers edge energy bicubic loses (0.0111 → 0.0173 against a target of 0.0205) and
**sits below the target on both sets** — it under-sharpens rather than over-sharpens. Had it
exceeded the target that would have been a signal worth chasing, since inventing structure is
this project's dominant failure class. **This is a diagnostic. It is not turned into a claim,
and one summary statistic cannot distinguish recovered structure from plausible structure in
the right amount.**

---

## 6. Part D — the exported graph

| | |
|---|---|
| path | `tubitak/data/sr_models/gencp_sr_x2_v1.onnx` (**gitignored**) |
| size | **1,964,122 bytes** |
| sha256 | `3fcb34a2ff5e07f00aefe426f08e3f60243388270bbcbd8e11749f25b0375ef7` |
| opset | **17** |
| declared input | `['batch', 3, 'height', 'width']` — **spatial axes dynamic** |
| exporter | **legacy TorchScript, `dynamo=False`** |
| versions | torch 2.13.0, onnx 1.22.0, onnxruntime 1.29.0 |

**D17-C — the graph runs at three shapes and matches PyTorch:**

| input | output | max abs difference |
|---|---|---|
| 128 (training size) | 256 × 256 | 1.907e-06 normalised = **0.0095 DN** |
| 96 | 192 × 192 | 1.788e-06 = **0.0089 DN** |
| **100** (not a multiple of 8) | 200 × 200 | 1.907e-06 = **0.0095 DN** |

All three inside the registered 1e-4 bound by two orders of magnitude. This settles WP1 open
item 2 for this model: a source smaller than one tile in an axis is accepted.

**Why `dynamo=False` is pinned, and why it is recorded.** torch 2.13 defaults to the dynamo
exporter, which requires `onnxscript`; that package is absent and this work package installed
nothing. The TorchScript path supports `dynamic_axes`, which is what D17 needs, so nothing was
given up — but **the default differs by torch version, and a silent switch would change the
graph without changing the code.** It is therefore in the model's own metadata, not only here.

**Provenance travels inside the file — 36 `metadata_props` entries**, including
`input_normalisation = normalised = DN / 5000.0`, `norm_divisor_dn`, `scale_factor = 2`,
`in_channels = 3`, `band_order = B02,B03,B04`, `infer_tile_src_px = 128`,
`infer_overlap_src_px = 32`, `receptive_field_input_px = 31`, `train_device = mps`,
`onnx_exporter = legacy TorchScript (dynamo=False)`, `registered_schedule_steps = 20000`,
`completed_steps = 16306`, `stop_reason = budget`, `checkpoint_step = 16000`, the corpus and
split registration paths, and the scale caveat. WP4 reads the normalisation from the model
rather than from anyone's memory.

---

## 7. Repository hygiene

`git status --porcelain --untracked-files=all` shows nothing outside `tubitak/sr/`, and
**zero entries under `tubitak/data/`** — the corpus, the run directory and the model file are
all gitignored. **No git command was run.** New files: `tubitak/sr/sr_train/` (config, data,
split_fix, leakage, control_v2, model, train, evaluate, export_onnx),
`tubitak/sr/docs/03b-registration.md`, and this report. No institutional imagery is involved:
the only rasters read are the five public Copernicus L2A granules.

---

## 8. Open items

1. **The run is 3,694 steps short of its registered schedule** (16,306 of 20,000), and
   validation was still improving. A rerun on an uncontended device would produce a different
   and probably slightly better model. Every number here is a 16,000-step number.
2. **The probe/run discrepancy is mine and will recur** (§4.2). A budget measured under
   conditions that do not match the spending conditions is an estimate, not a measurement.
   Nothing in the harness enforces that they match.
3. **`torch.save` hung at process teardown on MPS** (§4.3), leaving an 8,192-byte partial
   `last.pt`. Not diagnosed. The training save path has no atomic-write discipline, unlike
   `sr_core.mosaic.atomic_path`; a truncated checkpoint that a future run resumed from would
   fail confusingly. Cheapest fix: write checkpoints through a temp-and-rename.
4. **The MTF assumption remains unverifiable and load-bearing**, inherited from WP3A. It is
   the reason for D21 and for §9 below.
5. **Kaggle is uncommissioned** (§1). If the model is ever retrained for the paper, the
   compute question reopens, and the corpus upload has not been done.
6. **SSIM is validated only against its own extremes**, inherited from WP3A open item 4. Every
   SSIM in §5 carries that. Installing `scikit-image` and cross-checking would upgrade it;
   it needs permission to install a package.
7. **Both test margins land near +5.5 dB.** Not investigated. It could mean the task is
   equally hard on both sets, or that the model has saturated what this degradation permits;
   these are distinguishable with more work and were not distinguished here.
8. **Edge density is one summary statistic** (§5.5) and cannot separate recovered structure
   from plausible structure of the right magnitude. A spatial or spectral comparison would say
   more. Not done.
9. **`36TUK` contributes 54 test chips**, barely over the 50 floor. The floor is doing real
   work there, and a slightly different dedup outcome could have pushed it under.

---

## 9. What this work package proves about 10 m → 5 m

**Nothing.**

Every number in §5 is measured between a **simulated 20 m image and a real 10 m image**. The
20 m image was produced by a degradation this project defined: a Gaussian low-pass at
MTF 0.3, then decimation by two. The model learned to invert that specific, known operator,
and §5 measures how well it does so on ground it has not seen.

Applying it at 10 m → 5 m assumes the sensor's MTF bears the same relationship to the sampling
grid at 10 m → 5 m as it does at 20 m → 10 m — that the imaging system is **scale-invariant
over a factor of two in ground sample distance**. That is false in general: a real
instrument's MTF is fixed by its optics, detector pitch and platform motion, and does not
rescale because you relabel the pixels. **Nothing in this project can test it**, because
nothing on this machine is real imagery finer than 10 m over these footprints.

So the honest statement is: this work package establishes that the model inverts a **known
synthetic degradation** better than bicubic does, on held-out ground and on a held-out
acquisition, by a paired margin of about +5.5 dB with no chip worse. It establishes **no
evidence whatever** about the accuracy of a 5 m product. A 5 m output may be presented as
what the pipeline produces; it may not be presented as validated, and the two must not be
allowed to blur into each other in a slide.
