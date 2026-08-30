# WP7 — the scale-4 four-band model

Registered before any outcome in [`07-x4-registration.md`](07-x4-registration.md), including
the amendment in its §11. Every number below states the path it came from.

**Status: training in progress.** This document currently carries the control and the metric
finding. The model results are added when the run completes.

---

## 1. The bicubic control at scale 4

Path: `sr_train/control_v2.py` under `GENCP_SR_VARIANT=x4`, on corpus `sr_wald_corpus_x4`,
against the **corrected** degradation (registration §11.1). Per chip, unweighted mean over
chips, never pooled. Normalised reflectance `DN / 10000`, `PSNR_DATA_RANGE = 1.0`.

| set | n | PSNR (dB) | SSIM | MAE |
|---|---|---|---|---|
| test | 457 | 33.9788 ± 2.810 | 0.847306 ± 0.0534 | 0.01374579 ± 0.003862 |
| heldout | 1332 | 33.9533 ± 2.141 | 0.845512 ± 0.0446 | 0.01382531 ± 0.003477 |
| val | 422 | 34.4114 ± 2.846 | 0.854300 ± 0.0549 | 0.01312892 ± 0.004551 |

> **The scale-4 control reads higher than the scale-2 control (33.9533 against 33.0050 on the
> same held-out granule) only because the normalisation divisor doubled; on the like-for-like
> cell — three bands, divisor 5000 — scale 4 scores 28.5221 dB, which is 4.48 dB *below*
> scale 2, so the harder task does score worse and the apparent gain is an artefact of the
> metric, not a property of the imagery.**

### 1.1 How that was decided — measurement, not argument

Two candidates were proposed: the divisor change, or B08 being smoother than the visible
bands and raising the pooled mean. They were separated by a 2 x 2 over the same chips and the
same code path (`degrade_chip` -> `BicubicUpsampler` -> the same metric functions), varying
only the band subset and the divisor. The scale-2 control is three bands at divisor 5000, so
that cell is the like-for-like one.

Path: `scratchpad/norm_probe.py`, written for this question; artefact
`tubitak/data/sr_wald_corpus_x4/norm_probe.json`. The upsampler's `n_clipped` was asserted to
be 0 in every cell, so the path is linear and the comparison is not distorted by clipping.

**heldout, n = 1332**

| bands | divisor | PSNR (dB) | SSIM | MAE |
|---|---|---|---|---|
| 3 (B02,B03,B04) | 5000 | **28.5221** | 0.738086 | 0.02610835 |
| 3 (B02,B03,B04) | 10000 | 34.5427 | 0.857638 | 0.01305417 |
| 4 (+B08) | 5000 | 27.9327 | 0.719549 | 0.02765062 |
| 4 (+B08) | 10000 | **33.9533** | 0.845512 | 0.01382531 |

**test, n = 457**

| bands | divisor | PSNR (dB) | SSIM | MAE |
|---|---|---|---|---|
| 3 | 5000 | **28.7903** | 0.738544 | 0.02499569 |
| 3 | 10000 | 34.8109 | 0.859884 | 0.01249785 |
| 4 | 5000 | 27.9582 | 0.723412 | 0.02749158 |
| 4 | 10000 | **33.9788** | 0.847306 | 0.01374579 |

### 1.2 The decomposition closes exactly

On `heldout`, from the scale-2 control to the scale-4 control, one factor at a time:

| step | PSNR (dB) | change | what it is |
|---|---|---|---|
| scale 2, 3 bands, divisor 5000 | 33.0050 | — | the WP3B registered bar |
| scale 4, 3 bands, divisor 5000 | 28.5221 | **−4.4829** | the task getting harder |
| scale 4, 4 bands, divisor 5000 | 27.9327 | **−0.5894** | adding B08 |
| scale 4, 4 bands, divisor 10000 | 33.9533 | **+6.0206** | the divisor, and nothing else |
| | | **+0.9483** | and 33.9533 − 33.0050 = **0.9483** |

The three terms sum to the observed difference exactly. **Both candidates were real and both
point downward**; the second one points the opposite way from the story proposed for it —
**B08 is harder than the visible bands, not smoother**, costing 0.59 dB on heldout and 0.98 dB
on test. The entire apparent improvement is the divisor, and it more than covers a genuine
4.48 dB loss to the harder task plus a 0.59 dB loss to the fourth band.

### 1.3 The divisor term is exactly analytic, and that is checkable

PSNR is `10 log10(range^2 / MSE)` with `range` pinned at 1.0 while the *signal* is divided by
the divisor, so MSE falls by the square of the divisor ratio and PSNR rises by a constant that
has nothing to do with the task:

    20 * log10(10000 / 5000) = 6.0205999133 dB

Measured per chip, not on the mean: the shift is **6.0205999133 dB on every one of the 1789
chips in both sets**, with a maximum deviation from the analytic value of **1.33e-14 dB**.
MAE's ratio is **2.0000000000** in all four cells, confirming the linearity the assertion on
`n_clipped` predicted.

**SSIM is not invariant either, and its shift is not a constant**: +0.119552 (heldout, 3
bands), +0.125963 (heldout, 4), +0.121339 (test, 3), +0.123894 (test, 4). SSIM's stabilising
constants are fixed against `range = 1.0`, so shrinking the signal moves SSIM toward 1 by an
amount that depends on the content. An SSIM compared across divisors is not comparable even
approximately.

### 1.4 What this permits and what it forbids

The constancy of the per-chip shift is what makes the consequence precise rather than a
caution:

- **A PSNR margin — `model − bicubic`, both at the same divisor — is exactly invariant to the
  divisor**, because a constant added to both cancels in the difference. This is verified, not
  assumed: the shift is constant to 1e-14 on every chip.
- **An absolute PSNR or SSIM is not comparable across divisors.** The scale-4 control may
  never be set beside the scale-2 control, and neither may the models' absolute scores.
- **An absolute MAE is not comparable across divisors either**; it scales by exactly the
  divisor ratio. A *relative* MAE margin would be invariant, an absolute one is not.
- **An SSIM margin is not invariant**, because SSIM's shift is content-dependent.

Registration §10.3 already required `NORM_DIVISOR_DN = 10000.0` and `PSNR_DATA_RANGE = 1.0` to
be quoted together, on the grounds that either alone is meaningless. This is the measurement
of how meaningless: **6.02 dB**, which is larger than the entire margin WP3B's model achieved
over its control (5.574 dB). A reader who took the two controls at face value would conclude
the scale-4 task is easier; it is 4.48 dB harder.

Registration §10.7 forbids comparing the scale-4 margin with the scale-2 margin. That
prohibition stands, but §1.4 above narrows *why*: the reason is not the divisor, which cancels
in a PSNR margin, but that the two margins are measured on different tasks.

---

## 2. The SSIM sweep — which existing comparisons the divisor affects

§1.4 established that a PSNR margin is invariant to the divisor and an SSIM margin is not.
Registration §10.7's rule was written for the *scale* difference, so it does not cover SSIM as
such. The documents were swept for SSIM values from different divisors quoted near each other.

**Swept:** `03a-wald-corpus.md`, `03a-corpus-registration.md`, `03b-registration.md`,
`03b-training.md`, `06-wsx4-eklentide.md`, `07-x4-registration.md`, and the Project 1
documents under `tubitak/docs/`.

**Result: no existing document places SSIM values from different divisors next to each
other.** In detail, so the negative result is checkable rather than asserted:

| document | divisor | SSIM content | verdict |
|---|---|---|---|
| `03a-wald-corpus.md`, `03a-corpus-registration.md` | 5000 | definition, validation cases, control table | internally consistent |
| `03b-registration.md` | 5000 | the parity tolerance `< 1e-4`, no reported score | not affected |
| `03b-training.md` | 5000 | model 0.964769, control 0.894263, margin +0.070506 | internally consistent |
| `06-wsx4-eklentide.md` | — | §7 states wsx4 quality is not measured at all: no PSNR, no SSIM | **nothing to compare** |
| `07-x4-registration.md` | 10000 | only the superseded control SSIM in §11.2; the WP3B figure quoted nearby (§3) is PSNR only | not affected |
| `tubitak/docs/*` (Project 1) | n/a | numeric near-matches are PSNRs and tolerance deltas, not our SSIMs; a different inference path entirely | not affected |

**The exposure is prospective, and it is specific.** `03b-training.md` §5 records an SSIM margin
of **+0.070506 ± 0.018698** (heldout) and **+0.070725 ± 0.021407** (test) at divisor 5000. This
report will record an SSIM margin at divisor 10000. Those are the two numbers a reader will put
side by side. Registration §10.7 happens to forbid it — but for the scale, and a rule that
fires for the right reason by accident is not a rule that will fire next time. Two models at
the *same* scale and different divisors would slip straight past it.

The measured size of what would slip past: the divisor alone moves the control's SSIM by
**+0.1196 to +0.1260** (§1.3), which is **1.7 times the entire +0.0705 margin** WP3B's model
earned. An SSIM comparison across divisors is not merely imprecise; the artefact is larger than
the effect.

### 2.1 A second finding from the same sweep: the SSIM definition is stated for three bands

`03a-wald-corpus.md` §D and `03a-corpus-registration.md` define the chip SSIM as *"the three
per-band SSIMs averaged to give the chip's SSIM"*. `sr_data.metrics.ssim_chip` in fact averages
over **all** planes (`for c in range(p.shape[0])`), so at scale 4 it averages **four**, B08
included. The code is right and the registered wording is now incomplete.

This matters beyond bookkeeping: §1.2 measured B08 to be the *hardest* band, so the fourth
plane pulls the chip SSIM down. Any reader applying the three-band definition to a scale-4 SSIM
would be reading a four-band number under a three-band description. WP7's SSIMs are stated as
**four-band means** wherever they appear in this report.

---

## 3. The probe finding, in its corrected form

`03b-training.md` §4.2 recorded the probe-versus-run gap and attributed it to GPU contention —
that run was contended, and the attribution was the available explanation. **This run shows the
same gap with no deliberate contention**, so the attribution does not survive and the general
statement has to be weaker and is:

> **A short probe measures burst throughput. It does not measure sustained throughput, and the
> two differ by roughly a factor of two in both runs measured so far.**

| run | probe | probe length | sustained rate in the run | achieved / probe |
|---|---|---|---|---|
| WP3B, scale 2 | 4.46 steps/s | 100 steps | 2.265 steps/s (contended) | **0.508** |
| WP7, scale 4 | 17.57 steps/s | 120 steps ≈ 6.8 s | ~10.6 steps/s (no deliberate contention) | **0.60** |

The trajectory shows where the probe's number comes from — instantaneous rate, 1000-step
windows:

| steps | rate | | steps | rate |
|---|---|---|---|---|
| 50 → 550 | **16.95** | | 4050 → 5050 | 10.6 |
| 550 → 1550 | 15.6 → 15.1 | | 7050 → 8050 | 10.8 → 10.1 |
| 1550 → 2550 | 14.4 → **9.0** | | 12050 → 13050 | 10.9 |
| 2550 → 3050 | **6.66** (minimum) | | 16050 → 17050 | 10.7 |
| 3050 → 4050 | 8.3 → 10.4 | | | stable to the end |

The first 500 steps run at 16.95 steps/s, which is the probe's 17.57 within the noise of a
different window. **The probe was not wrong about what it measured**; it measured the first
seven seconds. The rate then decays over about 2,000 steps, undershoots to 6.66, and settles at
a stable ~10.6 for the remaining 14,000 steps.

**What is not claimed.** No cause is asserted. Thermal behaviour, memory pressure, an allocator
warming up and a scheduler settling would all produce a curve of this shape, and none of them
was measured. The observation is the curve and the two ratios; the cause is an open item.

**One thing that *was* measured, because it would otherwise be a confound.** The §1 divisor
measurement ran on the CPU during roughly steps 4900–6500 of this run. The windows inside that
interval read 10.71, 10.46, 10.87, 10.35, 10.71 steps/s against a whole-run steady state of
~10.6 — indistinguishable. The cumulative rate moved from 10.85 to 10.79 across it. **My own
contention is bounded at ≤ 0.06 steps/s and is not what produced the gap**, which had already
appeared 2,000 steps before that job started.

**Consequence for the budget rule.** WP3B set its budget at 1.0x the probe extrapolation and
lost 3,694 steps of its registered schedule. This run set it at 3.2x (registration §11.3) and
completes the full 20,000 steps despite the identical factor-of-two shortfall. The correction
to the finding does not change the mitigation: the mitigation never depended on knowing the
cause, only on not trusting the estimate.

---

## 4. The divisor and the reference model are on the same footing — by choice, not by luck

Verified against the graph itself (`tubitak/data/wp5_reference/models/wsx4_spatrad.onnx`, 379
nodes), not against the WP5 write-up:

| position in the graph | op | constant |
|---|---|---|
| first op consuming the graph input | `Div(input, 10000.0)` | `/0/Constant_output_0 = [10000.]` |
| last op producing the graph output | `Mul(..., 10000.0) -> output` | `/2/Constant_output_0 = [10000.]` |

wsx4 takes uint16 DN in and returns DN out, and works internally in reflectance. Its input is
`(N, 4, H, W)` and its output `(N, 4, H, W)` — the same four-band shape as ours.

**So the two models' boundaries agree on what 1.0 means: 100 % surface reflectance.** A raster
can be fed to either without a conversion, and their outputs are in the same physical units.
That is what makes them directly comparable.

**Stated precisely, because "same footing" would otherwise overclaim.** wsx4 applies a further
per-band standardisation *inside* the graph, `(DN/10000 − mean) / std`, undone at the output:

| | B02 | B03 | B04 | B08 |
|---|---|---|---|---|
| `0.mean` | 0.1072 | 0.1367 | 0.1559 | **0.2781** |
| `0.std` | 0.1442 | 0.1412 | 0.1514 | 0.1341 |

Ours does not standardise. **The agreement is at the interface, not in the internal domain**,
and the interface is the part that matters for feeding both the same input and comparing
outputs without a conversion.

**Consequence of the choice, not coincidence — but it was the third reason of three.**
Registration §3 lists the grounds for `NORM_DIVISOR_DN = 10000` in order: (1) it is a physical
constant rather than a corpus-derived one, (2) it makes `PSNR_DATA_RANGE = 1.0` a physical
claim, (3) it makes our input domain identical to the reference model's. Reason 3 names this
explicitly and it was written before training. Being honest about its weight: **reasons 1 and 2
would have selected 10000 on their own**, and the project had already adopted
`reflectance = DN / 10000` in WP3A's D7 radiometry decision, well before wsx4 was looked at.

The deeper reason the two agree is not that either copied the other: **10000 is the Sentinel-2
L2A BOA quantification value**, so any model working in reflectance on this product converges
on it. WP3A's 5000 was the departure from that convention, chosen to map the brightest visible
band's p99.9 near 1.0 — a corpus-derived number that stopped being right the moment B08 was
added, which is exactly what happened.

**An incidental cross-check.** wsx4's `0.mean` puts B08 at 0.2781 against 0.107–0.156 for the
visible bands — NIR roughly twice as bright. Our D24 measurement of B08's distribution over
554.5 M clear pixels found the same 2–4x relationship. That is independent third-party
corroboration of our band statistics, from a model trained on different imagery.

---

## 5. The run, and the model

Registered schedule 20,000 steps with a 60-minute budget (registration §11.3).

| | |
|---|---|
| steps | **20,000 / 20,000**, `stop_reason = steps` |
| wall clock | 1883.5 s = **31.4 min** |
| sustained rate | 10.62 steps/s |
| best validation | **0.008439624** Charbonnier, at step 20,000 |
| seed | 20260831 |
| parameters | 519,360 in 30 tensors; receptive field 31 input px |
| device | mps; torch 2.13.0, onnx 1.22.0, onnxruntime 1.29.0 |

**The full registered schedule completed.** WP3B stopped 3,694 steps short on its budget; the
3.2x margin (§3) is what prevented a repeat, and it was needed — a 1.0x budget would have cut
this run off near step 12,700. The best checkpoint is the final one, so selection is
unambiguous, and selection used validation only.

### 5.1 The post-run hang reproduced exactly, which makes it deterministic

After the last step the process sat at **0.2 % CPU with `last.pt` truncated at 8192 bytes** —
the same file, the same size and the same signature as WP3B. `best.pt` (6,261,781 bytes) and
`train_record.json` were both complete. It was sampled twice five seconds apart to establish it
was stuck rather than writing slowly: size and CPU both unchanged. It had been blocked for
roughly an hour, so this is a hard block, not slowness.

`best.pt` was checksummed before and after the kill and is **unchanged** — the write that hangs
is the redundant one, and nothing that matters is lost. The fragment is retained as
`last.pt.TRUNCATED`. **Two runs, two identical hangs: this is reproducible and belongs in the
open items, not in the anecdotes.**

## 6. Results — the two test sets, read once, on both numeric paths

Sign convention: **`model − bicubic`**; PSNR and SSIM positive = model better, MAE negative =
model better. All figures **normalised reflectance `DN / 10000`, `PSNR_DATA_RANGE = 1.0`**, per
chip, unweighted mean over chips, **never pooled**. Every SSIM is a **four-band** mean (§2.1).

**D20 — the two paths agree, so the ONNX figures are the registered ones.**

| split | raw | PSNR | SSIM | MAE | verdict |
|---|---|---|---|---|---|
| test | 1.274e-06 | 1.328e-06 dB | 2.198e-08 | 1.291e-09 | within tolerance |
| heldout | 1.550e-06 | 1.436e-06 dB | 2.747e-08 | 1.846e-09 | within tolerance |

Registered tolerance: raw < 1e-4, PSNR < 0.01 dB, SSIM < 1e-4, MAE < 1e-6. The numbers below
are **ONNX-on-CPU** — produced by the artefact that ships, not by the training graph.

**test — n = 457** (36SVJ/36SWJ held-out chips)

| metric | model | bicubic | **paired margin** | chips model worse |
|---|---|---|---|---|
| PSNR (dB) | 37.1299 | 33.9788 | **+3.151101 ± 1.128928** | 2 / 457 |
| SSIM | 0.910003 | 0.847306 | **+0.062697 ± 0.021344** | 2 / 457 |
| MAE | 0.00948688 | 0.01374579 | **−0.004259 ± 0.001566** | 2 / 457 |

**heldout — n = 1332** (granule 36SXJ, never seen in any form)

| metric | model | bicubic | **paired margin** | chips model worse |
|---|---|---|---|---|
| PSNR (dB) | 36.9242 | 33.9533 | **+2.970930 ± 0.753976** | 1 / 1332 |
| SSIM | 0.907789 | 0.845512 | **+0.062277 ± 0.019554** | 2 / 1332 |
| MAE | 0.00963523 | 0.01382531 | **−0.004190 ± 0.001517** | 2 / 1332 |

**The margin is positive on every metric and both sets, and the model is worse on 1 chip in
1332 on the unseen granule.** The two sets agree closely (+3.151 and +2.971), which is what a
model that generalises across granules should look like.

> **SCOPE (D21).** The model inverts a degradation we constructed and know exactly: a Gaussian
> low-pass at MTF 0.3 then decimation by 4, **40 m → 10 m**. Beating bicubic at that task is
> partly a statement about inverting a **known synthetic blur**, not about how well it
> super-resolves real imagery at **2.5 m**, where there is no ground truth and the true
> 10 m → 2.5 m relationship is not that blur.

**Edge density, diagnostic only, not a gate:** model 0.006726 against bicubic 0.003888 and a
target of 0.011261 (test); 0.006807 / 0.003950 / 0.011404 (heldout). The model recovers roughly
**60 % of the target's edge density** where bicubic reaches about 35 %. It is sharper than
bicubic and still visibly short of the truth, which is the honest reading.

### 6.1 D26's registered expectation did NOT hold, and it is reported rather than adjusted

Registration §6 stated: *"Bicubic loses far more at 4x than at 2x, so the bar is lower and any
model clears it by more,"* and warned that a larger scale-4 margin must not be read as the model
improving. **The margin did not get larger. It roughly halved.**

| | scale 2 (WP3B) | scale 4 (WP7) |
|---|---|---|
| paired PSNR margin, heldout | **+5.574459** | **+2.970930** |

This comparison is legitimate **in units**: §1.4 proved the paired PSNR margin is exactly
invariant to the divisor, so the two dB figures are on the same footing despite 5000 vs 10000.
It is still not a statement about which model is better — §10.7 forbids that, and the tasks
differ — but it is precisely the right comparison for testing D26's stated *mechanism*, and the
mechanism is falsified.

The half of D26 that was right: the bar **is** lower at scale 4 (§1.2 — bicubic loses 4.48 dB
going from scale 2 to scale 4 in like-for-like units). What D26 missed is that **the model
loses more than the bar does.** Scale 4 gives the network a quarter of the input pixels and asks
it to invent sixteen times as many outputs rather than four; that cost exceeded the gift of a
lower bar. Per standing practice 6, this is recorded as a registered prediction that failed. No
parameter was changed and no number was tuned in response.

## 7. Defects found while producing these numbers

Seven, all the same shape — **code or text that assumes a parameter, met by a different one** —
and the four in this section were found *after* the three in registration §11.1.

| # | where | what it did | how it was caught |
|---|---|---|---|
| 4 | `train.py`, `evaluate.py` | `degrade_chip` without `scale` → degraded at 2, fed 128 px to a scale-4 model | loss shape crash |
| 5 | `corpus_checks.c4` | `mtf_at` without `scale` → scale-2 filter at the scale-4 Nyquist, 0.7401 vs a registered 0.3 | check C4 fired |
| 6 | `gaussian_decimation_kernel` | window built around 0, not the block centre → −1.125e-03 px shift at scale 4 | check X3 fired |
| 7 | `evaluate.CAVEAT`, ONNX `caveat`, `output_layout` | printed "decimation by two", "at 5 m", "2x spatial" **from inside a scale-4 model** | read the output |

**Number 7 is the worst of them and it was mandated by D21.** The rule that the scope caveat
must travel with the number was honoured — and the caveat travelled **hard-coded**, so a
scale-4 model shipped provenance saying it was trained 20 m → 10 m and applied at 5 m. That text
lives in `metadata_props` inside the graph, which is what the QGIS plugin reads and displays.
**Provenance that lies is worse than provenance that is absent.** All three strings are now
derived from `C.SCALE` and render correctly at both variants; the scale-2 rendering is
semantically identical to WP3B's original wording, so no WP3B claim moved.

**X5 existed and was never called.** `assert_band_order` was defined in `data.py` and invoked
from nowhere in the training, export or evaluation path. That is this project's own standing
finding about its verifiers, recurring: a check nothing invokes is not a check. It is now
asserted at the export stamp and again before the ONNX session is built, and it was tested end
to end — the real graph is accepted, while **B08/B04 swapped, B08 dropped, and `band_order`
absent are each refused before any split is opened** (no output file is written in the false
cases, which is how "before" was verified rather than assumed).

**One further fix, worth recording for its irony.** `torch.load` refused our own checkpoint:
it stores `TorchVersion` objects because standing practice 9 requires library versions in the
option dump, and torch 2.6+ defaults `weights_only=True`. **The practice that exists to make
runs reproducible is what blocked reading the run back.** `weights_only=False` is now pinned
with the reason in a comment, in all three load sites.

### 7.1 The evaluation was run twice, and no number moved

Fixing the stale caveat meant re-running the evaluation, which reads the two test sets a second
time. That is disclosed rather than hidden, and it was made checkable: the first run's artefact
is retained as `eval_x4.FIRSTRUN.json`, and the two were compared field by field.

**25,202 numeric fields compared; exactly one differs — `wall_clock_s` (110.15 → 111.97 s).**
Every metric, every per-chip value and every path-agreement figure is identical. Nothing was
selected, tuned or chosen on the strength of a second look; the frozen checkpoint was pushed
through deterministic code twice and only a label changed.

The ONNX artefact is byte-stable across re-exports: the last two exports have the identical
sha256 `f3f2ffbde52c92eff81b0741b6c180e9d4a5a117fbd91ac5eaa77c789f0ad4ba`, and X6's three parity
figures were bit-identical across all three exports, so the weights never moved — only the
provenance strings, which was the intent.

## 8. The shipped artefact

`tubitak/data/plugin_models/gencp_sr_x4_b4.onnx`, 2,086,466 bytes, opset 17,
sha256 `f3f2ffbde52c92eff81b0741b6c180e9d4a5a117fbd91ac5eaa77c789f0ad4ba`, declared input
`['batch', 4, 'height', 'width']`, band order `B02,B03,B04,B08`, `norm_divisor_dn = 10000.0`,
`scale_factor = 4`, `completed_steps = 20000`, `stop_reason = steps`.

**X6 — ONNX-on-CPU equals PyTorch**, at three input sizes including one deliberately not a
multiple of 8:

| input px | output | max abs diff (normalised) | in DN |
|---|---|---|---|
| 64 | 256 × 256 | 3.070e-06 | 0.0307 |
| 96 | 384 × 384 | 3.576e-06 | 0.0358 |
| 100 | 400 × 400 | 3.099e-06 | 0.0310 |

Registered bound 1e-4, so about a factor of 30 clear, and dynamic spatial axes confirmed.

## 9. Open items

1. **The post-run `last.pt` hang is reproducible** — two runs, identical signature. Not
   diagnosed. Nothing of value is lost, but a training script that cannot exit is a script that
   cannot be run unattended.
2. **The probe/run gap has no measured cause** (§3). The observation and the two ratios are
   recorded; thermal behaviour, memory pressure and allocator warm-up are all untested.
3. **`bicubic_control.py` prints "at 20 m Nyquist" with a variable `{P.SCALE}`** — the same
   defect shape as numbers 4–7, currently harmless because it is only reached at scale 2.
4. **SSIM is validated only against its own extremes**, inherited from WP3A open item 4 and
   still true. Every SSIM here carries it.
5. **WP3B's `export_verification.json` was overwritten** by the first x4 export before the
   filename was made variant-aware. Nothing in the repository reads it and WP3B's parity numbers
   survive in `03b-training.md`, so no claim is lost — but the artefact is. Exports are now
   written to `export_verification_{variant}.json`.
6. **wsx4 is still not measured** (`06-wsx4-eklentide.md` §7). Both models now share an input
   domain (§4), so the comparison is finally possible; it has not been done.
