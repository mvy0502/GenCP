# Confidence score — validation results

Executes [`confidence-registration.md`](confidence-registration.md), which was committed
(`613530b`) before any number below existed. Nothing was re-chosen after seeing an outcome.

**Sign convention: higher confidence = better = lower expected error.** A negative rho is
the result that supports the score.

**Verdict: the registered score PASSES, and the margin over the cheap baseline is thin
enough that the honest summary is "input density predicts matching error, and the two
elaborations on top of it add very little".**

---

## Corpus and inference path

| | |
|---|---|
| Chips | 150, `sitevar == "eu"` in `tubitak/docs/evidence/regD/regD_per_chip.csv` — the held-out European set, not Ankara |
| Error | `med_mean32`, KARIOS median radial residual in px, **arm C2** |
| Inputs | `tubitak/data/eu_holdout/inputs/<stem>.png`, 150/150 present |
| Deterministic path | `gencp_C2_fp32.onnx` |
| Stochastic path | `gencp_C2_stochastic_fp32.onnx`, 16 draws, seed 0 |
| Versions | torch 2.13.0, numpy 2.4.6, onnxruntime 1.29.0 |

Both spread paths were run. The registered one (torch) gives rho **-0.7466**; the deployed
one (ONNX) gives **-0.7466**. Every number below is from the **deployed** path, so what is
reported is what the plugin will actually compute.

### Controls, run before anything else

| control | result |
|---|---|
| Stochastic mean sits around the deterministic image | worst chip mean \|diff\| **0.51 DN**, max 18.5 DN |
| Stochastic graph with all masks = 1 == deterministic export | **0.0000 DN mean, 0.0000 DN max** — bit for bit |
| ONNX spread vs torch spread, same chip | chip means 1.743 vs 1.672 DN, spatial correlation **0.860** |
| Cost of 16 ONNX draws | **0.27 s** per tile |

The second is the one that matters: the stochastic graph is provably the same network as
the deployed one, with the dropout multiplies restored.

---

## 1. Does the score predict error?

Spearman rho against `med_mean32`, 150 chips, 95% CI from 10,000 chip bootstraps.

| signal | rho | 95% CI | |
|---|---|---|---|
| `conf_D` input density | **-0.755** | [-0.830, -0.659] | excludes 0 |
| `conf_B` distance to nearest OSM feature (baseline) | -0.647 | [-0.745, -0.533] | excludes 0 |
| `conf_S` stochastic spread | -0.455 | [-0.577, -0.313] | excludes 0 |
| **`conf_COMB` registered score** | **-0.747** | [-0.823, -0.647] | excludes 0 |

**Registered primary test — rho <= -0.25 and CI excluding 0: PASS.**

Replication on the secondary arm C1, same chips: `conf_COMB` -0.754, `conf_B` -0.702. Same
picture.

### Beating the baseline — technically yes, meaningfully barely

`rho(COMB) - rho(B) = -0.099`, 95% CI **[-0.195, -0.005]**. The interval excludes zero, so
by the registered criterion the combined score beats distance-to-nearest-feature. But the
upper bound is -0.005. That is as marginal as a pass can be, and Section 2 shows it does
not survive contact with the operational question.

### The thing the registration will not let me do, stated plainly

**`conf_D` alone (-0.755) scores better than the combined score (-0.747).** The stochastic
term, which costs a second model and 16 extra forward passes, very slightly *drags the
combination down*.

Substituting `conf_D` for `conf_COMB` now would be exactly the curve-fitting the
registration exists to prevent: the choice would be made on the same 150 chips that
produced the numbers. So the registered score ships, and "drop the stochastic term" is
recorded as an open item needing its own registration and, ideally, a different corpus.

---

## 2. The operational question — discard the worst X%, what improves?

Median `med_mean32` over the retained chips.

| discard | kept | `conf_COMB` | `conf_B` baseline | random control |
|---|---|---|---|---|
| — | 150 | 1.9802 | 1.9802 | 1.9802 |
| 10% | 135 | 1.8708 | **1.8209** | 1.9746 |
| 25% | 112 | 1.6086 | 1.6086 | 1.9632 |
| 50% | 75 | **1.2970** | 1.3457 | 1.9513 |

Random discard is the mean over 1,000 random subsets of the same size, and it barely moves
the median at all — so the improvement is real selection, not an artefact of trimming a
skewed distribution.

**Read the middle columns honestly.** At 10% the cheap baseline is *better*. At 25% they
are identical. Only at 50% does the combined score win, and by 0.05 px. The rank
correlation says COMB is better; the operational curve says the two are interchangeable up
to a 25% discard budget. **A user choosing between them should choose the cheap one**, and
the only reason this package ships the combined score is that it is what was registered.

Discarding half the output improves the median residual from **1.98 px to 1.30 px, a 34%
reduction** — that part is unambiguous and is the layer's actual value.

---

## 3. The confound, which is half the story

Matched-point count `n_mean32` is entangled with both sides. This exact mechanism produced
a false result in this project once before, which is why it was registered as a mandatory
check rather than left to discretion.

| | rho |
|---|---|
| `conf_COMB` vs `n_mean32` | **+0.743** |
| `n_mean32` vs error | **-0.798** |
| `conf_COMB` vs error, **partialling out `n_mean32`** | **-0.381** |
| unadjusted, for comparison | -0.747 |

**About half the association runs through matched-point count.** Restricting to
`n_mean32 >= 10` changes nothing because every chip already clears it (0 dropped).

Two readings, and the honest position is that this measurement does not separate them:

- **Nuisance.** Where the input is silent KARIOS finds fewer keypoints, and a median over
  few points is noisy; the score is partly predicting noisiness rather than error.
- **Mechanism.** Where the input is silent the model invents, so there is genuinely less
  matchable structure *and* what matches is worse. Point count is then a step in the causal
  chain, not a confounder to be removed.

What can be said without choosing: **controlling for point count, the score still predicts
error at rho = -0.38 with the correct sign.** The layer is not merely a point-count proxy,
and it is also not as strong as -0.75 makes it look. The UI text is written against -0.38,
not -0.75.

---

## 4. Bands

Derived by the registered rule — sliding conditional median over 30 chips, red where that
median reaches 1.5x the corpus median, green where it is at or below it. Corpus median
M = 1.9802 px, so red requires a conditional median >= 2.9703 px. `|rho| >= 0.35` permits a
red band to be drawn.

| band | boundary on `conf_COMB` | n | median residual | IQR |
|---|---|---|---|---|
| **Red** — do not use | `<= -0.7288` | 23 | **3.133 px** | 0.576 |
| **Amber** — use with care | -0.7288 to -0.1050 | 43 | **2.705 px** | 0.884 |
| **Green** — usable | `>= -0.1050` | 84 | **1.380 px** | 1.030 |

Monotone, and the ends are well separated: green chips match **2.3x better** than red ones.
Amber sits closer to red than to green, which is worth knowing — "use with care" here means
closer to unusable than to usable.

### Normalisation constants the plugin must use

`conf_COMB = (z(conf_D) + z(conf_S)) / 2` where z uses the **held-out corpus** statistics,
not the statistics of whatever the user is generating. A run over a single flat tile would
otherwise z-score itself to the middle of the scale and report green.

| | mean | std |
|---|---|---|
| `conf_D` | 0.716106 | 0.514109 |
| `conf_S` | -1.807605 | 0.805370 |

---

## 5. Scope — what this result does and does not license

- **Arm C2 only.** `regD_per_chip.csv` has held-out EU errors for `pretrained`, `C1` and
  `C2`, and none for C3. The plugin previously pre-filled C3; the confidence layer is
  therefore only offered with a validated model, and the plugin says so rather than
  silently extrapolating.
- **Chip-level only.** Everything above validates a **chip-mean** score against a
  **chip-median** error. The per-pixel raster is the same quantity at finer granularity and
  is useful for seeing *where* the input was silent, but its per-pixel calibration is not
  separately validated. The run-level verdict is the validated claim; the map is a
  visualisation of it.
- **This corpus.** 150 European chips, and they are unusually OSM-sparse (0.02%-0.2% of
  pixels carry an OSM-only class). That is the regime the layer is for, but it is one
  regime.

## 6. What shipped, and the decisions taken at integration

Per the registration's outcome table, the primary test passed and beat the baseline, so
the combined score ships with three bands and an auto-styled layer.

| decision | why |
|---|---|
| The layer is offered **only** for `gencp_C2_fp32.onnx` | The bands are calibrated on C2. For any other model the dialog withholds the layer and says which model or which file is wrong, rather than drawing bands that mean nothing. |
| Section 6 quotes **both** rho figures | -0.75 alone oversells it. The UI text carries -0.38, the point-count-adjusted figure, in the same sentence. |
| The **run-level verdict** is the headline, the per-pixel map is context | The validation tested a chip-mean score against a chip-median error. That is the run-level quantity. The map shows *where* the input went silent; its per-pixel calibration is not separately validated, and `band_map`'s docstring says so. |
| Both inference paths are stated on the raster | `GENCP_PROVENANCE` on the confidence layer records that the image came from the deterministic path and the confidence from 16 stochastic draws at a recorded seed. |
| Band colours match band names | A first pass drew the green band blue on colour-blind grounds, producing a legend that read "Yeşil" beside a blue swatch - which moves the burden onto the reader. Red/amber/green are drawn as named, separated by lightness instead (measured relative luminance 0.13 / 0.48 / 0.22). |
| Missing stochastic export **raises** rather than degrading | A one-term score is not the score the bands were calibrated on. `pipeline.generate` refuses it explicitly. |

Cost, measured: 16 draws take **0.27 s per tile** through the deployed ONNX, against
roughly 5 s to rasterise the same tile. The layer is opt-out in section 6 anyway.

### A crash found while integrating, worth reading even if you skip the rest

Building a **pyproj CRS on a QgsTask worker thread segfaults QGIS 4.2.1** - if and only if
the main thread has already built one. Probed in isolation, both orders: worker-first is
fine, main-thread-first then worker is an immediate SIGSEGV.

This was not introduced by the confidence work. `vectors._margin_bbox` has called pyproj
on the worker since the beginning and only escaped because the preview warms the render
cache, so the worker usually hits the cache instead of re-rendering. A multi-tile run in
which the preview covered tile 0 and the worker had to render the rest would have crashed
in any earlier build. `gencp_core` now uses rasterio's PROJ binding throughout, with the
four-corner arithmetic unchanged; Gate R still renders byte-identically.

## 7. Registration 2 — the stochastic term is dropped

Executes [`confidence-registration-2.md`](confidence-registration-2.md), committed
(`4019717`) before any Ankara number existed. Decision corpus: the **130 Ankara Overpass
chips**, arm C2, `med_mean32`. Zero stem overlap with the 150 European chips that raised
the question.

| signal | Ankara rho | 95% CI | Europe rho |
|---|---|---|---|
| `conf_D` input density | **-0.768** | [-0.831, -0.676] | -0.755 |
| `conf_COMB` incumbent | -0.645 | — | -0.747 |
| `conf_B` baseline | -0.387 | — | -0.647 |
| `conf_S` stochastic spread | -0.327 | — | -0.455 |

| registered condition | result |
|---|---|
| 1. Non-inferiority: upper CI of `rho(D) - rho(COMB)` below +0.05 | **-0.035** — PASS |
| 2. Stands alone: `rho <= -0.25`, CI excludes 0 | PASS |
| 3. Beats the baseline: upper CI of `rho(D) - rho(B)` below 0 | **-0.245** — PASS |

**Registered decision: SWITCH to `conf_D` alone.** It was framed as non-inferiority and it
cleared superiority: `rho(D) - rho(COMB) = -0.123`, CI [-0.219, -0.035], excluding zero.

### The number that actually settles it

Partial rho on Ankara, with matched-point count held constant:

| score | raw | partial given `n_mean32` |
|---|---|---|
| `conf_D` | -0.768 | **-0.287** |
| `conf_COMB` | -0.645 | **+0.012** |
| `conf_B` | -0.387 | -0.045 |
| `conf_S` | -0.327 | +0.079 |

**On Ankara, once point count is held constant, only `conf_D` retains any association at
all.** The combination's entire Ankara correlation ran through how many points KARIOS
matched; `conf_D`'s did not. The confound check was registered as mandatory because this
mechanism produced a false result in this project once before, and here it is what
distinguishes the two candidates rather than merely qualifying them.

Discard curves agree, though less sharply — at every level `conf_D` is at or ahead of the
combination (50%: 0.601 vs 0.627 px, against 0.947 for random discard).

### What changed as a result

- **No stochastic pass.** No 16 ONNX draws, no second 208 MB model to ship or request, no
  explicit-noise graph surgery, and no need to explain that the image is deterministic
  while its confidence map is not. The confidence layer is now computed from the rasterised
  **input** alone and adds no measurable time.
- **Bands re-derived on the EUROPEAN corpus**, as registered — Ankara decided, Europe
  calibrated, so the decision and the calibration are not on one corpus.

| band | boundary on `z(conf_D)` | n | median residual | IQR |
|---|---|---|---|---|
| Red — do not use | `<= -0.9824` | 19 | **3.309 px** | 0.692 |
| Amber — use with care | -0.9824 to -0.2453 | 55 | **2.631 px** | 1.085 |
| Green — usable | `>= -0.2453` | 76 | **1.331 px** | 0.996 |

- `export_stochastic`, `StochasticOnnxGenerator` and `CALIBRATION_COMB_SUPERSEDED` are
  **kept**, because `confidence_validate.py` still reproduces both registrations and this
  document reports their numbers. They are simply no longer on the plugin's path.

### Scope, restated

Two corpora, both arm C2. Ankara is far denser in OSM than the European set (which runs
0.02%-0.2% OSM-class pixels), so the score has now been asked to work in two regimes rather
than one. That is better than one and it is not "general".

---

## 8. The four review decisions

| | decision | what was done |
|---|---|---|
| 1.1 | Separate "which model ships" from "which model the bands were calibrated on" | `CALIBRATION` now records `calibrated_model_file` **and its SHA-256**, and `model_is_validated` checks the hash rather than the file name — a renamed C3 can no longer be handed C2's bands. Section 4 states, at the point the model is chosen and independently of the confidence checkbox, whether the bands were measured on it. |
| 1.2 | Delete the hand-set 0.2% sparse-OSM threshold | Deleted, not re-tuned. The preview warning is computed from the **same registered score and the same band boundaries** the output layer uses, on the tile being shown, so the two cannot disagree by construction. Measured on the Ankara test tile: preview says 67.4% red, layer says 67.8% — the difference is only the 257 to 256 px alignment. Since the score is now `conf_D`, this costs no inference. |
| 1.3 | One registered test | Above. |
| 1.4 | Two interface corrections | The half-translated warning box is fixed at the source: `pipeline.coverage_warnings` returns **structured facts**, not English prose, and the dialog renders them in Turkish. The Spearman/partial-rho sentence moved behind a collapsible "Detaylar"; the band shares and the red-share warning stay prominent. |

### Which arm is pre-filled, and the choice that is yours

The plugin currently pre-fills **`gencp_C2_fp32.onnx`**, and it is worth being explicit
that this happened as a side effect: C2 was chosen as the *calibration* arm because it is
the only one with held-out European KARIOS errors, and the pre-fill followed. That is not a
reason to ship it. The options:

1. **Keep C2 as the default.** The confidence layer works out of the box. Whether C2 is the
   best generator is a separate question this package has not measured.
2. **Default to C3** (the previous default) and accept that the confidence layer is
   withheld until the user switches model — the dialog now says so clearly.
3. **Calibrate the bands for C3 as well.** This needs held-out European KARIOS errors for
   C3, which do not exist; producing them is a run, not a decision.

This is a product decision and it is left open deliberately.

## 9. Open items

1. **Drop the stochastic term?** `conf_D` alone scored better here, at a fraction of the
   cost and with no second model to ship. Needs its own registration on a different corpus.
2. **Separate nuisance from mechanism** in the point-count entanglement — would need an
   error measure that does not depend on how many points were matched.
3. **Per-pixel calibration** against per-pixel error, if a source of that ever exists.
4. **C3 and the pretrained arm** have no held-out EU KARIOS errors, so the layer cannot yet
   be offered for them. The plugin now pre-fills C2 rather than C3 for this reason, which
   changes the default model a user gets.
5. ~~The sparse-OSM warning and the confidence layer disagree.~~ **Closed by decision 1.2**
   — the threshold was deleted rather than tuned, and the warning now comes from the
   registered score.
7. **`conf_D` measures INPUT information, not OSM information.** A tile with zero OSM
   features can still land in the green band on CLC+ land-cover variety alone. Observed
   while wiring the preview warning, and handled by keeping the zero-OSM notice as a
   warning in its own right regardless of the band. Whether the score *should* weight OSM
   evidence more heavily than land-cover variety is unmeasured.
6. **Per-pixel bands are chip-level boundaries applied at pixel granularity.** Stated
   wherever they appear, but a per-pixel calibration would need a per-pixel error source.
