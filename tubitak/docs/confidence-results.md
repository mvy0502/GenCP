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

## 6. Open items

1. **Drop the stochastic term?** `conf_D` alone scored better here, at a fraction of the
   cost and with no second model to ship. Needs its own registration on a different corpus.
2. **Separate nuisance from mechanism** in the point-count entanglement — would need an
   error measure that does not depend on how many points were matched.
3. **Per-pixel calibration** against per-pixel error, if a source of that ever exists.
4. **C3 and the pretrained arm** have no held-out EU KARIOS errors, so the layer cannot yet
   be offered for them.
