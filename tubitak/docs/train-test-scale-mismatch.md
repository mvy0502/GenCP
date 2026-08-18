# Train/inference scale mismatch — the principal open technical question

**Status:** investigation only. No pipeline file modified, no existing output regenerated,
none of Options A-E implemented.
**Date:** 2026-08-18
**Companion document:** [`geometry-finding.md`](geometry-finding.md) (georeferencing scale error)

> **Why this is a separate document.** This began as §6.1 of the geometry finding, but it is a
> different question with a larger effect. The georeferencing error is a 0.39 % metadata defect
> with a known fix; this is an **11.72 % domain shift between training and inference** that affects
> what the model actually generates. It is recorded here as the principal open technical question,
> above the georeferencing arithmetic.

---

## 1. The mismatch

Read from the executed code path, not from a saved options file:

| | training | inference |
|---|---|---|
| `preprocess` | `resize_and_crop` | `resize_and_crop` |
| `load_size` | **286** (`base_options.py` default) | **256** (set by `test_options.py`) |
| `crop_size` | 256 | 256 |
| effective transform | 257 -> 286, random 256 crop | 257 -> 256, no crop |
| GSD the model sees | **8.986 m** | **10.039 m** |
| ground covered by the 256 grid | 2300.5 m | 2570.0 m |

`options/test_options.py` contains
`parser.set_defaults(load_size=parser.get_default('crop_size'))`, commented *"To avoid cropping,
the load_size should be the same as crop_size"*. Neither `train_options.py` nor `train.py`
contains any such override, so training keeps the 286 default.

Ratio 286/256 = **1.1172**: at inference the network is shown content **11.72 % coarser** than
anything it saw during training.

**This has an independently observed signature.** In the demo imagery, small structures degraded —
narrow rivers vanished, small villages rendered as noise — while large structures were fine. That
is the expected symptom of a scale mismatch: features near the network's learned size limit fall
below it when everything is presented 11.7 % smaller.

**The caveat that keeps this open:** `GenCP_HR_Model_Weights.zip` contains only two
`latest_net_G.pth` files and no `train_opt.txt`. The authors' actual `load_size` is therefore
**not recoverable** from the released artefacts. If they passed `--load_size 256`, no mismatch
exists. Since the command cannot be recovered, §4 tests the *consequence* instead.

---

## 2. Is the demo site in the training set?

This determines how every demo result so far should be read, so it was checked first.

The corpus spans **77 MGRS tiles** across 5 UTM zones. Distribution is uneven — the largest tile
(34TCT) holds 7.5 % of chips, and 40 tiles hold under 1 % each.

| | chips |
|---|---|
| `image_pairs/train` | 5,131 |
| `image_pairs/test` | 577 |
| distinct MGRS tiles | 77 |

**The demo folder contains four tiles:**

| tile | chips in demo folder | in DB train | in DB test | exact-name overlap |
|---|---|---|---|---|
| 31TFJ | 522 | 20 | 1 | 21 |
| 31TFK | 50 | 2 | 0 | 2 |
| **31TEJ** | **54** | **0** | **0** | **0** |
| 31TFH | 4 | 2 | 0 | 2 |

**The 50 chips actually processed in every result so far are all 31TEJ, and none of them appear
anywhere in the corpus** — zero overlap with train, zero with the DB test split.

**Verdict: the demo results are out-of-distribution / held out.** The observed degradation is
genuine generalisation behaviour, not memorisation. Note the nuance: 31TEJ is adjacent to 31TFJ,
which *is* represented in training, so the general region is in-distribution even though the
specific 100 km square and every specific chip are not.

Two incidental findings worth recording:

* Across the demo folder as a whole, **25 of 630 chips (4 %)** do appear in the training corpus
  (almost all 31TFJ). Anyone processing the full demo folder rather than the 31TEJ subset is
  mixing seen and unseen data.
* **The corpus's own splits overlap:** 9 of the 577 `image_pairs/test` chips also appear in
  `image_pairs/train`. Small (1.6 %), but it means the published test split is not strictly held
  out. Those 9 were excluded from every measurement in this document.

---

## 3. Alignment is not the confound

Before attributing any quality difference to scale, the generator's own geometric fidelity was
certified: a translation-equivariance test bounds any systematic input->output shift at
**0.008 px (8 cm)** over 33 chips. See [`geometry-finding.md` §11](geometry-finding.md). The
network introduces no measurable displacement, so quality differences below are not alignment
artefacts.

---

## 4. Testing the consequence

### 4.1 Design

40 pairs from the corpus's **held-out test split**, spanning **26 MGRS tiles**, excluding the 9
leaked chips. Each OSM half was generated twice from identical weights:

* **(a) current inference path** — resize 257 -> 256. GSD 10.039 m, covers 2570.0 m.
* **(b) training-matched path** — resize 257 -> 286, **centre**-crop 256 (deterministic, unlike the
  random crop training uses). GSD 8.986 m, covers 2300.5 m.

Both variants were pre-transformed to 256x256 before inference, so `test.py`'s own
`Resize([256,256])` is a verified no-op and the pipeline was not modified.

> **Deviation from the brief, and why.** The task said to use training pairs and note that the
> model has seen them. Held-out test pairs were used instead: for §4 this is a *quality*
> comparison, and seen data would confound it with memorisation. The held-out split is strictly
> stronger for the question being asked. (For the §3 geometry measurement, seen-ness would not
> have mattered either way.)

Because the two variants cover different ground, both are scored over the **common central
2300.5 m**, on two evaluation grids — neither is neutral, so both are reported:

* **229 px** — variant (b) is downsampled 256 -> 229 (its output *and* its reference equally).
* **256 px** — variant (a) is upsampled 229 -> 256 (its output *and* its reference equally).

If a result holds on both grids it is robust to that choice; if it flips, it is an artefact of the
resampling, not of the scale.

### 4.2 Metrics and why each was chosen

| metric | rationale |
|---|---|
| **gradient correlation** | Pearson r of Sobel gradient magnitude. The question is about texture and small-feature rendering, not colour — this is the primary metric. |
| **SSIM** | Luminance, contrast and structure jointly; the standard reference metric. |
| **high-frequency energy ratio** | Output HF power / reference HF power above a radial cutoff. Directly tests the observed symptom: 1.0 = detail matched, <1 = output too smooth. |
| **RMSE** | Intensity error. A deliberately weak proxy — a GAN is not required to reproduce pixel values — included only as a sanity baseline. |

### 4.3 Results (40 pairs)

**Evaluation grid 229x229:**

| metric | (a) current | (b) train-matched | difference | pairs won by b | significant? |
|---|---|---|---|---|---|
| gradient correlation | 0.2577 | **0.2700** | +0.0124 | 28/40 | yes (2.9 SE) |
| SSIM | 0.4051 | 0.4053 | +0.0002 | 24/40 | **no** (0.1 SE) |
| HF energy ratio | 0.7202 | **0.8547** | +0.1345 | 26/40 | yes (5.0 SE) |
| RMSE (lower better) | 39.417 | 39.207 | −0.210 | 24/40 | **no** (0.6 SE) |

**Evaluation grid 256x256:**

| metric | (a) current | (b) train-matched | difference | pairs won by b | significant? |
|---|---|---|---|---|---|
| gradient correlation | 0.2568 | **0.2666** | +0.0097 | 27/40 | yes (2.4 SE) |
| SSIM | **0.4275** | 0.4079 | −0.0196 | 6/40 | yes (5.5 SE) — favours **(a)** |
| HF energy ratio | 0.7184 | **0.8610** | +0.1426 | 25/40 | yes (5.6 SE) |
| RMSE (lower better) | **39.197** | 39.490 | +0.293 | 19/40 | **no** (0.8 SE) |

Visual comparison for 4 pairs: [`figures/scale-comparison.png`](figures/scale-comparison.png)
(OSM input / real satellite / output (a) / output (b)).

### 4.4 Reading the results honestly

**SSIM flips between grids** — it favours (b) by +0.0002 at 229 px and (a) by −0.0196 at 256 px.
That is the resampling artefact the two-grid design was built to expose: whichever variant gets
upsampled has both its output *and* its reference smoothed, which inflates SSIM. **SSIM is
therefore uninformative here**, and would have produced a confident, wrong answer had only one
grid been evaluated.

**What survives on both grids:**

* **High-frequency energy ratio: 0.72 -> 0.86.** Consistent, large (5+ SE on both grids), and in
  the predicted direction. Variant (a) produces only 72 % of the reference's high-frequency
  energy — it is measurably too smooth — while (b) reaches 86 %, closing about **48 % of the gap
  to 1.0**. This is the metric that directly targets the observed symptom, and it supports the
  hypothesis.
* **Gradient correlation: +0.010 to +0.012 in favour of (b)**, 27-28 of 40 pairs, roughly 2.4-2.9
  SE. Consistent in direction but small in size.

**What does not survive:** SSIM (flips) and RMSE (within noise on both grids).

**Absolute agreement is poor for both variants** — gradient correlation ~0.26, SSIM ~0.41. Neither
variant reproduces the real scene closely, which is expected: the generator synthesises plausible
imagery from OSM, and the real satellite contains features OSM does not describe (quarries, bare
soil, seasonal state). The comparison is *relative*; neither number should be read as a quality
score in absolute terms.

### 4.5 Verdict

**Feeding at the training-matched scale produces a measurable but modest improvement, confined to
detail rendering.**

* The effect is **real, not noise**: the high-frequency deficit narrows from 28 % to 14 % below
  reference, consistently across both evaluation grids and in 25-26 of 40 pairs.
* The effect is **specific**: it appears in the two texture/detail metrics and is absent from SSIM
  and RMSE. Feeding at training scale does not make outputs globally more similar to reality — it
  makes them **less over-smoothed**.
* The effect is **modest in absolute terms**. It is not the difference between a broken and a
  working model. Overall similarity to the real scene is essentially unchanged.

This is neither a clean confirmation nor a null result. The scale mismatch is real and its
predicted signature is measurable, but correcting it recovers only part of the lost detail and
does not transform output quality. **It does not by itself justify changing the inference path**,
particularly since path (b) sacrifices 10 % of ground coverage (2300.5 m vs 2570.0 m) for that
gain.

---

## 5. What remains open

1. **The authors' actual `load_size` is still unknown and unrecoverable** from the released
   artefacts. Everything in §1 describes the released code under its defaults. The only way to
   settle it is to ask the authors — see Option E in `geometry-finding.md`.
2. **Only the centre crop was tested.** Training uses a *random* crop, so a trained model saw many
   crop positions; a deterministic centre crop is one sample of that distribution.
3. **A third path was not tested:** retraining or fine-tuning at `load_size=256` would remove the
   mismatch without sacrificing coverage. That is out of scope here and would need the full
   training corpus and a training run.
4. **40 pairs, 26 tiles.** Enough to establish the direction and significance of the HF effect,
   not enough to characterise how it varies by land-cover type. The symptom was described for
   small villages and narrow rivers specifically; a land-cover-stratified analysis would test that
   directly and has not been done.
5. **No perceptual or task-based metric was used.** FID, LPIPS or a downstream segmentation score
   would answer "is (b) better *for a purpose*", which the pixel metrics here cannot.

---

## 6. Reproducing

```bash
conda activate gencp

# section 2 - tile distribution and overlap
python tubitak/scripts/corpus_overlap.py

# section 3 - alignment certification
python tubitak/scripts/equivariance_test.py \
    --out-p tubitak/data/equivariance/out_p/genCP_HR_RGB_model/test_latest/images \
    --out-q tubitak/data/equivariance/out_q/genCP_HR_RGB_model/test_latest/images --offset 16

# section 4 - scale experiment (after generating both variants)
python tubitak/scripts/scale_experiment.py --figure tubitak/docs/figures/scale-comparison.png
```

The training corpus (1.71 GB) and all generated imagery live under `tubitak/data/`, which is
gitignored. Re-download from <https://zenodo.org/records/15044428>.
