# Registration — a per-pixel confidence score, and whether it predicts matching error

**Registered 2026-08-27, before any correlation, discard curve or band boundary below is
computed.** Nothing in this file was written after seeing an outcome. The signals, their
combination, the aggregation, the test statistic, the pass criterion, the baseline it must
beat, and the rule for deriving band boundaries are all fixed here.

**Sign convention, used everywhere and never flipped: higher confidence = better = lower
expected matching error.** Every signal below is oriented to that convention at the point
it is defined, so a *negative* correlation between confidence and error is the result that
supports the score.

## Why this needs registering rather than just building

A confidence layer that does not predict error is worse than no layer, because it
manufactures trust exactly where the user cannot check. That is the same failure mode as
the preview bug in the previous package: a control that looks like a safeguard and is not
one. Choosing the signal after seeing which one correlates would be curve-fitting on
n = 150, and the resulting layer would carry a validation number that means nothing.

---

## Corpus and reference, named exactly

**Chips.** The 150 unique stems with `sitevar == "eu"` in
`tubitak/docs/evidence/regD/regD_per_chip.csv`. These are held out: they are the European
generalisation set, not the Ankara corpus the C-phase was tuned and reported on.

**Input renders.** `tubitak/data/eu_holdout/inputs/<stem>.png`, 257 x 257 px at 10 m.
Every one of the 150 stems is present there (verified: 150/150) and in
`tubitak/data/eu_holdout/eu_inventory.csv` (150/150).

**Error variable.** `med_mean32` — the KARIOS median radial residual in pixels — for
**arm C2**, from the same `regD_per_chip.csv`, 150 rows. `n_mean32` is that chip's matched
point count and is used only for the confound check below, never to select chips.

**Secondary arm.** Arm `C1`, same file, same 150 stems, reported alongside. It is a
replication check, not a second chance: C2 is the primary and its result stands whatever
C1 does.

### The arm mismatch, stated now rather than discovered later

`regD_per_chip.csv` has held-out EU errors for `pretrained`, `C1` and `C2` only. **It has
none for C3, which is what the plugin currently pre-fills.** So this validation is
performed on C2 end to end — the stochastic passes use the C2 checkpoint and the
deterministic control uses `gencp_C2_fp32.onnx` — and any claim it supports is a claim
about C2. Transferring it to C3 would be an assumption, not a measurement. If the score
validates, the integration must either ship C2 or state the transfer explicitly; that
decision is deferred to the integration step and is not licensed by this registration.

---

## The signals

All three are computed per pixel from artifacts available at inference time, with no
ground truth.

Palette class assignment, used by D and B: each pixel is assigned to the nearest of the 22
GenCP palette colours in Euclidean RGB. The renders are supersampled, so a minority of
pixels are blends — but the **median nearest-palette distance is 0.0 DN** (measured on
three chips before registering; this is a property of the extractor, not an outcome), so
the assignment is near-exact for the bulk of every chip.

**CLC-base classes** are the seven values of `gencp_core.rasterize.CLC_MAP`:
`black, forest_green, gray, light_green, no_vegetation, snow, water`.
**OSM-only classes** are the remaining fifteen palette names:
`foot_path, light_gray, light_orange_road, light_purple, medium_orange_road, orange_road,
red_road, residential_road, rock, salt_pond, sand, tertiary_road, track,
unclassified_road, yellow_farm`.
`gray`, `water`, `forest_green` and `light_green` are reachable from either source and are
therefore **not** counted as OSM evidence. That is deliberately conservative: it can only
weaken B, never inflate it.

### D — input information density (the primary prior)

For each pixel, the Shannon entropy in bits of the palette-class histogram in a **33 x 33
window** (330 m at 10 m GSD), computed on the class-index map, edges reflected.

`conf_D = entropy`

Rationale: where a window is a single flat CLC+ class, the input carries no structure and
the model has nothing to condition on, so whatever texture appears in the output is
invention. Where classes meet — a road, a field boundary, a shoreline — the output is
constrained. The project has already measured that edge density rises in input-silent
regions, which is the same phenomenon seen from the output side.

### B — distance to nearest OSM feature (the baseline to beat)

Euclidean distance transform, in pixels, from the set of pixels assigned to an OSM-only
class. A chip with no such pixel is assigned the chip diagonal (363.4 px) everywhere.

`conf_B = -distance`

This is the cheap, obvious score. It is included so that the sophisticated one has
something to be better than.

### S — stochastic spread

The deployed generator is deterministic because `gencp_core/export.py` removes dropout.
The C2 checkpoint was **trained with dropout** (`no_dropout: False` in its `train_opt.txt`;
`nn.Dropout(0.5)` sits in the three innermost `UnetSkipConnectionBlock` up-paths), so
dropout can be switched back on for a confidence pass without retraining or reloading
anything.

N = 16 forward passes, torch seeds 0..15, generator built exactly as `export.py` builds it
**except** `use_dropout=True` and the dropout modules left in train mode. BatchNorm is
swapped for the exactly-equivalent InstanceNorm as `export.py` does, so the passes stay on
the evaluated inference path and the only source of variation is dropout.

Per-pixel standard deviation across the 16 passes, averaged over the three channels.

`conf_S = -spread`

**The delivered image never comes from this path.** It comes from the deterministic ONNX.
The stochastic path is used only to estimate spread. Every place this number is reported
must say so.

### Combined score — fixed here, not chosen later

`conf_COMB = mean( z(conf_D), z(conf_S) )`

where `z` is a z-score taken **across the 150 chips after chip-level aggregation**, not
per pixel and not per chip. Equal weights. No tuning, no third term, no per-signal
transform. If a weighted combination would have done better, that is not a result this
package is permitted to report.

### Chip-level aggregation

**Unweighted mean of the per-pixel value over all 257 x 257 pixels of the chip.** Chosen
because it is the simplest defensible rule and because it commits before the fact; a
percentile or a masked mean might be better and will not be substituted.

---

## The tests, and what would falsify them

### Primary — rank correlation

Spearman rho between `conf_COMB` and `med_mean32` (arm C2) across the 150 chips, with a
95% confidence interval from 10,000 bootstrap resamples of chips.

**Prediction: rho <= -0.25, and the 95% CI excludes 0.**

**Falsified if** rho > -0.25, or the CI contains 0, or the sign is positive.

### Must beat the baseline

`conf_COMB` must be more negative than `conf_B` on the same chips, with the 95% bootstrap
CI of the paired difference `rho(COMB) - rho(B)` excluding 0.

**If it does not, the finding is that the cheap baseline is as good or better, and that is
what gets reported and, if it validates on its own, shipped.** A more elaborate score that
does not beat distance-to-feature has earned nothing.

### Operational — the discard curve

Chips ranked by confidence descending. For X in {10, 25, 50}%, discard the lowest-X%
chips and report the **median** of `med_mean32` over those retained, against the median
over all 150. Reported for `conf_COMB` and for `conf_B`, and for a **random-discard
control** (mean over 1,000 random discards of the same size), because discarding any 50%
of a skewed distribution moves the median a little for free and that amount must be
visible.

### The confound that has already bitten this project once

`n_mean32` — matched point count — plausibly depends on input density in the same
direction as the error does. The equal-point-count hazard is documented in
`common-support-registration.md` and it produced a false result once already.

Registered checks, reported whatever they show:

1. Spearman rho between `conf_COMB` and `n_mean32`.
2. Partial Spearman of `conf_COMB` vs `med_mean32` controlling for `n_mean32`.
3. The primary correlation recomputed on the subset with `n_mean32 >= 10`, and the count
   dropped.

**If the association vanishes under (2), the score is measuring how many points KARIOS
found, not how wrong they were, and that is a negative result.**

### Control, run before any of the above

The mean of the 16 stochastic passes must be close to the deterministic ONNX output on the
same chip. Reported as max and mean absolute difference in DN over five chips. If the
stochastic passes are not a perturbation *around* the delivered image, their spread does
not describe the delivered image and signal S is void. This control is run first and its
result is reported even if it passes.

---

## Band derivation rule — registered before the boundaries are computed

Bands are derived from the held-out error distribution conditional on the score, never by
eye.

1. Sort the 150 chips by `conf_COMB` ascending.
2. Sliding window of 30 chips, step 1, giving the conditional median of `med_mean32` as a
   function of confidence rank.
3. Let `M` be the median of `med_mean32` over all 150 chips.
4. **Red** = the lowest-confidence contiguous run whose conditional median is `>= 1.5 * M`.
   **Green** = the highest-confidence contiguous run whose conditional median is `<= 1.0 * M`.
   **Amber** = everything between.
5. Boundaries are the confidence values at those run edges, reported together with the
   count and the median, IQR and n of `med_mean32` inside each band.

**Degeneracy rules, fixed now:**

- If the primary test is falsified, **no bands are produced at all** and no confidence
  layer ships.
- If the primary passes but `|rho| < 0.35`, **no red band is drawn.** Two bands only, and
  the amber label must say the evidence is weak.
- If no contiguous run reaches `1.5 * M`, there is no red band. A red line is not drawn to
  fill the table.

---

## Invariances — what must not change for these numbers to mean what they claim

- **The same 150 chips** on both sides. Confidence is computed from
  `eu_holdout/inputs/<stem>.png`; error is read from `regD_per_chip.csv`. Nothing is
  re-inferred by KARIOS and no chip is added, dropped or re-scored.
- **Arm held fixed at C2** for the error column, the stochastic checkpoint and the
  deterministic control. Mixing arms across those three would make the correlation
  meaningless.
- **The renders are the committed ones.** No chip is re-rendered; the OSM source for this
  corpus is not replayable.
- **Window size 33, N = 16, seeds 0..15, equal weights** are as written here. Changing any
  of them after seeing a result requires a new registration, and this one is not deleted.
- **Numerics recorded** with the run, per standing practice 9: torch 2.13.0, numpy 2.4.6,
  onnxruntime 1.29.0, and the torch seeds above.

## What ships under which outcome

| Outcome | What ships |
|---|---|
| Primary passes and beats baseline | The combined score, three bands, styled layer |
| Primary passes, baseline as good or better | The **baseline** score, same treatment, and the combined score is reported as not worth its cost |
| Primary passes but `\|rho\| < 0.35` | Two bands, no red line, weakness stated in the UI |
| Primary falsified | **No confidence layer.** The input-density raster ships instead, labelled *input density — not a reliability estimate*, with this file cited for why |
