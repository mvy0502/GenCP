# Registration 3 — do the European confidence bands transfer to Turkey?

**Registered 2026-08-27, before the transfer is computed.** Extends
[`confidence-registration.md`](confidence-registration.md) and
[`confidence-registration-2.md`](confidence-registration-2.md); neither is deleted and both
results stand.

**Sign convention, unchanged: higher confidence = better = lower expected matching error.**

## The problem this tests

The band boundaries were derived on 150 held-out **European** chips. The tool will be used
over **Turkey**. The dialog currently tells a user that a red-band tile had a median
matching error of **3.3 px** — a number measured in Europe, presented without saying where
it came from. Either that number transfers, or the wording is wrong.

## What is already known, and must not be mistaken for the answer

Two facts about the Ankara corpus are in hand before this registration, from
`confidence-registration-2.md`'s run, and both are stated here so they cannot later look
like findings:

- **Ankara's overall median matching error is 0.9418 px against Europe's 1.9802 px.** The
  Turkish corpus is roughly twice as easy in absolute terms.
- Ankara chips are far denser in OSM (European chips run 0.02%-0.2% OSM-class pixels).

Because `conf_D` is z-scored against **European** statistics and the boundaries are
absolute cut points on that z-scale, a denser corpus will push chips towards green
mechanically. That is expected. It is not, by itself, either transfer or failure — which is
why the criteria below separate *ordering* from *absolute level*.

What has **not** been computed, and is what this registration is for: the European
boundaries applied unchanged to Ankara.

---

## Method — the one thing that must not happen

**The boundaries are applied exactly as they stand and are not re-derived.** From
`gencp_core/confidence.py CALIBRATION`:

| | value |
|---|---|
| `conf_D_mean` (European) | 0.716106 |
| `conf_D_std` (European) | 0.514109 |
| `red_hi` | -0.982375 |
| `green_lo` | -0.245312 |

Re-deriving them on Ankara would guarantee a monotone, well-separated result and would
measure nothing. If they do not transfer, that is the finding.

**Corpus.** The 130 chips with `sitevar == "ank_overpass"`, arm `C2`, in
`tubitak/docs/evidence/regD/regD_per_chip.csv`; scores from
`tubitak/docs/evidence/confidence/per_chip_onnx_ankara.csv`, already computed under
registration 2. Nothing is re-inferred.

**Inference path.** Identical to registration 2: `conf_D` from the rasterised input,
`med_mean32` from the committed KARIOS results, arm C2 throughout.

---

## The three questions, and the criteria, fixed here

### 1. Ordinal transfer — does the ranking survive?

**Prediction: `median(red) > median(amber) > median(green)` on Ankara.**

This is the claim the coloured layer actually makes to a user: red areas are worse than
green ones. If this fails, the layer is misleading in Turkey and must not ship for Turkish
use in its present form.

### 2. Separation — is the ranking useful, not merely correct?

**Prediction: `median(red) / median(green) >= 1.5` on Ankara.** Europe gives
3.3093 / 1.3310 = **2.49**.

A monotone ordering with a ratio of 1.05 would be technically transferring and
operationally worthless.

### 3. Absolute transfer — may the dialog keep quoting the European numbers?

**Prediction: for each band, `|median_ankara - median_europe| / median_europe <= 0.50`.**

This is the criterion the UI wording depends on, and it is the one I expect to fail: the
Ankara corpus median is already 52% below Europe's before any banding. It is registered as
a prediction anyway, because writing down the expected failure and then observing it is
worth more than not testing it.

**If 3 fails, the dialog must name the corpus for every per-band figure it shows.** The
replacement wording is reported, not applied, and the decision is the reader's.

### Also reported, whatever the criteria say

- **n per band on Ankara**, against Europe's 19 / 55 / 76. A corpus that lands almost
  nothing in red would tell us the boundaries are mis-scaled for Turkey even if the three
  criteria pass.
- The two corpora's per-band medians and IQRs side by side.
- Spearman rho of `conf_D` against error on each corpus, for context (-0.755 Europe,
  -0.768 Ankara, both already reported).

---

## Invariances

- **Boundaries, normalisation constants, score definition and window: unchanged.** The only
  thing that changes between the European and Ankara columns is which chips are scored.
- **Arm C2 on both sides**, error column `med_mean32` on both sides.
- Nothing is re-rendered or re-inferred; both score files are already committed.
- Numerics per standing practice 9: numpy 2.4.6, onnxruntime 1.29.0.

## What this cannot settle

Ankara is one city. "Transfers to Turkey" is not established by 130 chips from a single
site, whatever the numbers say, and the report must not claim it.
