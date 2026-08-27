# Registration 2 — should the confidence score drop its stochastic term?

**Registered 2026-08-27, before any Ankara number below is computed.** Extends
[`confidence-registration.md`](confidence-registration.md); that registration is not
deleted and its result stands.

**Sign convention, unchanged: higher confidence = better = lower expected error.** A more
negative Spearman rho is better.

## Why this is being asked, and why the answer is not "whichever correlates best"

`confidence-results.md` reported that `conf_D` alone scored rho **-0.755** on the European
held-out set against **-0.747** for the registered combination `conf_COMB`. That is not a
reason to switch. It is one number on the corpus that produced it, the gap is far inside
the bootstrap width, and switching on it would be selecting a model on its test set.

**The reason to consider switching is simplification, and it is worth stating in full**,
because it — not the correlation — is what this test is for:

- 16 ONNX passes per tile disappear.
- A second 208 MB model file disappears from what has to be shipped, requested, stored and
  kept beside the first.
- `export_stochastic`, `StochasticOnnxGenerator`, the explicit-noise-mask graph surgery and
  their controls all disappear.
- The awkward sentence disappears: *the image is deterministic but the confidence map is
  stochastic*. Every place that has to be explained is a place someone inheriting this can
  misread.

So the question is **not** "is `conf_D` better?" but "**is `conf_D` not meaningfully
worse?**" — and the test is registered as a non-inferiority test accordingly. A test framed
as superiority would be the wrong test for the decision being made.

---

## Corpus — deliberately not the one that raised the question

| | |
|---|---|
| Chips | 130, `sitevar == "ank_overpass"`, arm `C2`, in `tubitak/docs/evidence/regD/regD_per_chip.csv` |
| Error | `med_mean32` — the same column, same units (px), as registration 1 |
| Point count | `n_mean32`, for the confound check only |
| Inputs | `tubitak/data/ankara/run/inputs/<stem>.png` — the 130 Overpass renders |
| Overlap with the European corpus | **zero stems**, verified before registering (130 unique stems, 0 shared) |

These are the unregenerable Overpass renders. They are Ankara, they were the C-phase's
reporting corpus, and they are **not** the 150 European chips the first registration used.
That is the point: the observation being tested came from the European set, so the test
runs somewhere else.

Both scores are computed with the calibration constants **already fixed** in
`gencp_core/confidence.py` from the European corpus. Nothing is re-fitted to Ankara.

---

## The three scores, all already defined

| score | definition | cost |
|---|---|---|
| `conf_D` | `z(input density)`, z from the European corpus (mean 0.716106, std 0.514109) | no inference |
| `conf_COMB` | `(z(conf_D) + z(conf_S)) / 2`, the registered incumbent | 16 ONNX passes/tile |
| `conf_B` | `-distance to nearest OSM feature`, the baseline both must beat | no inference |

Chip aggregation is the unweighted mean over the chip's pixels, exactly as registered.
`conf_S` comes from `gencp_C2_stochastic_fp32.onnx`, 16 draws, seed 0 — the deployed path.

---

## The decision rule — fixed here, before the numbers exist

Spearman rho against `med_mean32` over the 130 chips; 95% CIs from 10,000 chip bootstraps;
paired differences bootstrapped on the same resamples.

**Switch to `conf_D` alone if and only if ALL THREE hold:**

1. **Non-inferiority.** The upper bound of the 95% CI of `rho(conf_D) - rho(conf_COMB)` is
   **below +0.05**. In words: we are confident `conf_D` is not worse than the combination
   by more than 0.05 in rho. 0.05 is set here, before seeing anything, as the largest
   degradation worth accepting for the simplification above.
2. **It stands on its own.** `rho(conf_D) <= -0.25` and its own 95% CI excludes 0 — the
   same bar registration 1 set for the incumbent.
3. **It still beats the baseline.** The 95% CI of `rho(conf_D) - rho(conf_B)` excludes 0.

**If any of the three fails, the registered combination stays** and the stochastic path
ships as it does today. That is a real possible outcome and it is not a failure of this
package.

### Reported whatever the decision

- The same table for `conf_COMB` and `conf_B`, so all three are visible side by side.
- Discard curves at 10 / 25 / 50% for all three, plus a 1,000-draw random-discard control.
- Partial rho given `n_mean32` for every score — the confound that ate half the European
  association is expected to be present here too, and hiding it on the second corpus
  because it was disclosed on the first would be worse, not better.
- Both corpora side by side in the results, European and Ankara.

---

## If the switch happens: which numbers move, and which corpus re-derives them

**Bands must be re-derived, because the band boundaries live on the `conf_COMB` scale and
`conf_D` is a different scale.** They are re-derived by the rule already registered —
sliding conditional median over 30 chips, red where that median is `>= 1.5 * M`, green
where it is `<= 1.0 * M`, `M` the corpus median — and they are re-derived **on the EUROPEAN
corpus**, not on Ankara.

That split is deliberate and is registered here so it cannot be rearranged later:

- **Ankara decides** whether to switch. It is untouched by the observation that prompted
  the question.
- **Europe calibrates** the bands, exactly as it calibrated the incumbent's. Deriving
  boundaries on the same 130 chips that just chose the score would put the decision and the
  calibration on one corpus.

The `gencp_core.confidence.CALIBRATION` block is updated in one commit with the new score
name, the new boundaries, the new per-band medians, and the corpus each came from.

---

## Invariances — what must not change for this to mean what it claims

- **Arm C2 throughout**: the error column, the stochastic export, the deterministic control.
- **The calibration constants stay European.** `conf_D` is z-scored against the European
  mean and std even when evaluated on Ankara. Re-standardising per corpus would make the
  two corpora incomparable and would quietly fit the score to its test set.
- **The renders are the committed Overpass ones.** Nothing is re-rendered; that source is
  not replayable.
- **Window 33, N = 16, seeds 0..15, equal weights** as before.
- **Numerics recorded** per standing practice 9: torch 2.13.0, numpy 2.4.6,
  onnxruntime 1.29.0.

## One thing this test cannot settle

Ankara is a single city and its 130 chips are far denser in OSM than the European set
(European chips run 0.02%-0.2% OSM-class pixels). A score built on input density is being
asked to work across both regimes, and two corpora do not establish that it does. Whatever
this returns, the honest scope remains "measured on two corpora, both C2".
