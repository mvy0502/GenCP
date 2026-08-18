# Renderer tolerance — how faithfully must we reproduce the OSM rasteriser?

**Status:** pre-registered. Results below the line.
**Scored with KARIOS**, not pixel metrics — the question is whether a control point still lands in
the right place, and pixel metrics already gave contradictory answers on the scale question (SSIM
flipped sign between evaluation grids while the task metric was decisive).
**Companion:** [`osm-palette.md`](osm-palette.md) · [`karios-validation.md`](karios-validation.md)

---

## 1. PRE-REGISTRATION (registered 2026-08-18 15:59:49 UTC, before any perturbation was generated)

### 1.0 One code fact that drives these predictions

Inference runs with `norm: batch`, `batch_size: 1` and `eval: False` — `test.py` only calls
`model.eval()` when `--eval` is passed, and it was not. **BatchNorm therefore runs in training mode
on a single image, normalising each image by its own per-channel mean and variance.** That is
effectively instance normalisation at inference.

The consequence is specific and testable: **a constant additive shift applied to the whole image is
subtracted out by the first BatchNorm.** A global colour shift should be largely invisible to the
network, however large. A shift applied to *one class* changes the relative colour geometry and
survives normalisation.

This is where my expectation departs from the calibration guess offered. I do **not** expect colour
identity to dominate for *global* shifts; I expect it to dominate only for *per-class* shifts.

### 1.1 P1 — ranking of axes, most to least impactful

Ranked by **sensitivity per unit of plausible deviation**:

| rank | axis | reasoning |
|---|---|---|
| 1 | **D-single** — one class shifted | Not removed by normalisation; changes the relative colour geometry the network keys on. |
| 2 | **A** — anti-aliasing removed | Changes **45 % of all pixels**, and roads are ~100 % anti-aliased so every road in every chip changes. Largest pixel-count perturbation available. |
| 3 | **G** — building rendering | 3.7 % of pixels, but buildings are the highest-contrast feature and concentrate in exactly the dense chips where matching currently works best. |
| 4 | **B** — anti-aliasing increased | Same mechanism as A but milder: training data is already soft-edged, so blurring moves it less far than hardening does. |
| 5 | **C** — road width ±1 px | ~1-2 % of pixels. |
| 6 | **E** — draw order inverted | Affects overlap regions only. |
| 7 | **F** — black/snow class removed | **LEAST.** 0.10 % of pixels combined. |
| — | **D-global** — all classes shifted together | Predicted **no measurable effect at any swept magnitude**, per §1.0. Listed outside the ranking because I expect it to be null rather than small. |

**Note on practical risk, which is a different ordering.** The palette values are written down in
`genCP_HR_osm_colors.py`, so a re-implementer is unlikely to get colours wrong at all. Anti-aliasing,
draw order and building treatment are *not* written down anywhere, so those are what we will
actually get wrong. **A, E and G carry the highest practical risk even if D-single is the most
sensitive axis.**

### 1.2 P2 — colour-shift magnitude at which degradation begins

* **Global shift (all classes together): no measurable degradation at 2, 5, 10, 20 or 40 DN.**
  Predicted null across the whole sweep, because BatchNorm removes a constant offset (§1.0).
* **Single-class shift (dominant vegetation, `light_green`): onset at ~10 DN, clearly degraded by
  20 DN, badly degraded at 40 DN.** Below 10 DN the shift is comparable to the anti-aliasing spread
  already present in the training data, so the network should absorb it.

### 1.3 P3 — do sparse chips degrade more or less than dense ones?

**Prediction: sparse chips degrade LESS in measured terms — the correlation between OSM information
content and degradation magnitude will be POSITIVE (dense chips lose more).**

This is the opposite of the calibration guess, and the reasoning is a floor effect. Sparse chips
already sit near the matching ceiling: median residual is high and surviving points are few
(`karios-validation.md` §4.4, rho = −0.79 between OSM edge density and residual). A chip that is
already close to random has little further to fall. Dense chips hold most of the recoverable signal
and therefore have the most to lose.

I expect the *absolute quality* of sparse chips to remain worse throughout — this is a prediction
about the **change**, measured per chip against its own baseline, not about the level.

### 1.4 P4 — what would mean LOOSE (build the rasteriser now)

The natural yardstick is an effect we already know matters: correcting the georeferencing affine
(arm A → B) improved mean residual by **0.137 px**, and that was a real, worthwhile correction.

> **LOOSE if:** every axis we cannot control from the released files — **A, B, C, E, F, G** —
> produces a median per-chip residual increase of **< 0.15 px** and a surviving-point-count decrease
> of **< 10 %**, with the palette matched exactly.

In that case a re-implementation that gets the palette right and everything else approximately would
be no worse than a georeferencing defect we were already willing to live with.

### 1.5 P5 — what would mean NOT BUILDABLE

> **NOT BUILDABLE if:** any single uncontrollable axis (A, B, E, F, G — the ones absent from the
> released tables) produces a median residual increase of **> 0.5 px** or a point-count loss of
> **> 30 %**.

0.5 px is ~24 % of the 2.09 px arm-B baseline and 3.6x the affine correction — an error larger than
the geometry defect the whole investigation began with, and injected by nothing more than a
reasonable reimplementation choice.

**TIGHT is the interval between**: some axes below the P4 bound, at least one between 0.15 and
0.5 px. In that case the named axes must be matched precisely and each needs a verification method.

### 1.6 Registered caveat on the perturbations themselves

Axes **E, F and G cannot be simulated faithfully without a rasteriser**, because they are properties
of vector rendering and we only hold rasters. They are approximated:

* **E (draw order)** → remove road pixels, letting the underlying landuse win. This is the
  "roads not drawn last" case, a proxy for order inversion rather than a true inversion.
* **F (missing class)** → replace black/snow pixels with the surrounding dominant colour.
* **G (building rendering)** → morphological change to building blobs (±1 px), a proxy for a
  different fill/edge convention.

Their results bound the effect of getting these wrong; they do not reproduce a specific alternative
renderer.
