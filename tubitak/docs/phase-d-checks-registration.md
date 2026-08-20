# Phase D verification checks — registrations (committed before the numbers they judge)

**Registered 2026-08-20, before any check below has been computed.** Seven checks precede the
Europe/Phase D results documents. Checks 1–3 can change what those documents are allowed to say;
4–7 change how confident they may sound. Standing rules apply (epoch 20 only; nothing tuned;
labels/thresholds/bands committed first; earlier registrations never deleted).

Carried correction: the C3 work-package line "same lr_policy step / lr_decay_iters 50" was the
author's error (that flag belonged to the discarded C1 warm-up). C3 uses C2's exact schedule
(linear, 10 flat + 10 decay). Nothing changes except the data mix.

## Check 1 — Ankara re-scored against the fresh 568-chip European baseline

Phase B reported Ankara's density-matched gap as −0.247 px against its 44-chip arm-B European
baseline. Phase D scored Cappadocia (+0.446) and Tuz Gölü (+0.513) against the fresh 568-chip
baseline. The three numbers were produced against two different baselines and have not yet been
made comparable. Ankara's pretrained results are now re-scored per stratum against the SAME
fresh baseline with the SAME procedure (Ankara fixed density cut points 0.09904/0.1588/0.2241/
0.33222 on the canonical sobel measure recomputed from input renders; matched gap per stratum =
Ankara stratum median − EU stratum median; site figure = mean over supported strata).

Registered meanings, fixed before computing:

- **Ankara gap ≈ +0.4…+0.5 px (like the Phase D sites):** explanation (b) — the baselines were
  never comparable and the cross-site comparison should not have been made in that form. The
  "uniform site-level penalty" wording survives, but the Phase B headline "no measurable
  geographic penalty" becomes **baseline-dependent** and must be corrected in the corrections
  log and flagged to the coordinator: correct statement = "no penalty against the Phase B
  44-chip matched baseline; ≈ +X px against the better-supported 568-chip baseline."
- **Ankara gap ≈ 0 or negative on the fresh baseline too:** explanation (a) — the penalty is
  site-specific, "uniform" was the wrong word, the regional/phenological-radiometry story is
  broken (it does not explain Ankara), and the Phase B headline stands unchanged.
- **Intermediate/mixed strata:** reported per stratum; no single-word summary is permitted.

Sensitivity: computed for both the published Phase B per-chip medians and the same-environment
regenerated ones (they differ by +0.034 ± 0.045, previously shown statistically zero).

## Check 2 — badlands selection rule replaced (measurement failure recorded)

The committed composition rule (`no_veg ≥ 25%` of the input render) selected 5/130 Cappadocia
chips. A rule that finds 5 chips at the site defined by that terrain is not measuring the
landform; additionally the composition raster is the model's own input, so defining terrain
from it is near-circular. **Status of the registered landform row is restated as "not
measurable with the committed rule"; no verdict is scored against n = 5.**

Replacement rule, registered before any label is computed:

- Elevation source: **Copernicus DEM GLO-30** (open), covering tile 36SXJ.
- Per-chip measure: **standard deviation of slope** within the chip footprint (slope from the
  DEM via Horn's method on the native ~30 m grid, reprojected to the chip UTM footprint).
- Label: **badlands = chips in the top quartile (≥ 75th percentile) of the site's ruggedness
  distribution**; flat = bottom half (< 50th percentile). The middle quartile is unlabeled
  (buffer), so the contrast is not diluted by boundary chips.
- Discipline: the label list is computed and committed **before** any KARIOS number for those
  chips is looked at in this analysis; expected n(badlands) ≈ 32. If the rule still yields
  < 25 labeled badlands chips, the test is reported as **underpowered**, not scored.
- The original rule's failure goes to the corrections log regardless of outcome.

## Check 3 — restraint vs mechanical blur

Third candidate for C2's European gain, previously unstated: L1-only output is blurrier, and
KLT may simply match smoother imagery more reliably — a mechanical effect, not learned
restraint. Control: low-pass the PRETRAINED outputs to match C2's spatial-frequency content,
then identical georeferencing and KARIOS.

- Sigma fit: a single global Gaussian sigma fitted so the radially-averaged power spectrum of
  blurred-pretrained matches C2's median profile over the same chip set (fit on the European
  set; report fitted sigma and match quality). If no single sigma matches the profile shape,
  that is reported as a finding, and the closest-fit sigma is still run as the control.
- Sites: the European held-out set (568) and Cappadocia (130).
- Metric: fraction of C2's paired gain recovered by blur = (paired blur-pre gain) / (paired C2
  gain), on the same chips.

Registered reading bands: **≥ 60% recovered → the learned-restraint claim does not survive**;
honest statement becomes "KLT prefers smoother inputs". **≤ 25% → restraint is supported** by
something other than consistency for the first time. **In between → partial; reported as
partial, no stronger word.** Registered caveat: flat-sparse chips (empty input) cannot
discriminate — on a blank input both arms' outputs are unconstrained — so the bands are judged
on the full set and, as a secondary cut, excluding the empty-input stratum.

## Check 4 — was salt ever in the fine-tuning corpus

The "missing class knowledge, not missing scene familiarity" reading of the Tuz salt result
requires that the fine-tuning corpus actually contained salt-like pairs. Count first: CLC+
class composition of every fine-tuning input half (5,577 pairs); distribution of water/bare
fractions; number of pairs whose composition matches the Tuz salt-chip inputs (thresholds taken
from the salt chips' own input compositions, stated in the result). Near-zero count → the
sentence is rewritten to "a class absent from training was not learned" and the
knowledge-vs-familiarity claim is withdrawn. Substantial count → the claim stands, stronger.

## Check 5 — minimum-point-count sensitivity

Every headline paired difference in this package (Europe, Ankara, Cappadocia, Tuz Gölü, and
the salt/non-salt splits) is recomputed under minimum point-count floors of **0, 10, 20, 30**
(chip enters only if BOTH arms meet the floor), reported side by side. Stable conclusions →
one-line reassurance. Any flip → the floor becomes a registered part of the metric, justified
on KARIOS grounds, not chosen post hoc.

## Check 6 — periodicity scrutiny applied to both arms

The pretrained outputs show a periodic quilt/diamond mosaic on empty inputs; the checkerboard-
tuned detector may not register it. General measure, both arms, all sites: 2D FFT off-DC peak
energy reported in two bands — **high-frequency band** (period ≤ 4 px: the transpose-conv
checkerboard) and **low-frequency quilt band** (period 8–64 px) — each as fraction of non-DC
energy in the top-k off-DC peaks of that band. Correlations with point count and residual are
computed **within information-density stratum** for both arms (the sparsity confound fix
applied symmetrically). Decision: if the pretrained quilt band correlates with its point count
or residual, the C2-minus-pretrained gap is measured against a contaminated reference and the
gap's SIZE (not direction) carries a caveat in the documents.

## Check 7 — CI on R; separating the two European explanations

- **R interval:** stratified bootstrap (resample chips within strata, 10,000 draws) of
  R = mean-gain(Cappadocia)/mean-gain(Ankara) over the 4 supported strata; percentile 95% CI.
  If the interval is wide, the committed sentence becomes "above the registered 0.7 threshold",
  not "about 95%".
- **Systematic vs scatter decomposition (Europe):** from each chip's KARIOS output, the global
  systematic shift (mean_x/mean_y) and the residual scatter about it, both arms. Registered
  prediction of the corrected-georeferencing candidate: the C2 improvement concentrates in the
  **systematic** component. If the improvement is mostly scatter, the georeferencing candidate
  is not doing the work and restraint/blur (check 3) carries the burden.

## Veto rule — registered before any fitting (Phase F embryo)

Operational case 36SWJ_12_30: C2 renders the input's class boundaries faithfully; the
boundaries do not exist in reality; the chip degrades (3.87 → 5.82 px) while still emitting
points. For georeferencing, a wrong control point is worse than no control point. Registered
experiment, not a post-hoc filter:

- **Goal:** a chip-level veto predicting, from INPUT PROPERTIES ONLY (no output, no ground
  truth), whether a chip should emit GCPs.
- **Candidate predictors (all input-side):** OSM information density (canonical sobel
  measure); CLC+ class composition (water, bare, rare-class fractions); class-boundary length
  per unit area.
- **Fit set:** Ankara + Tuz Gölü + Europe chips (C2 arm). **Held-out test site: Cappadocia** —
  the only clean site.
- **Registered target variable:** high-residual chip = C2 median residual > 2.0 px (the
  project's KLT noise-floor scale).
- **Registered metric:** at the chosen threshold, report (a) fraction of high-residual chips
  vetoed (catch rate) and (b) fraction of good chips lost (false-veto rate); the rule is
  judged acceptable only if catch ≥ 2× loss on the held-out site.
- **Decision threshold:** fixed on the fit set before Cappadocia is touched; reported with
  both rates on fit and test.
