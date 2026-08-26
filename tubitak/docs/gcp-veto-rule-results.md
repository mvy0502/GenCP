# GCP veto rule — held-out result: FAIL (recorded as registered)

**Date:** 2026-08-20 · Experiment as registered in
[phase-d-checks-registration.md](phase-d-checks-registration.md) §"Veto rule". Fit set: Ankara
130 + Tuz 126 + Europe 568 = 824 chips (C2 arm; input-only predictors — Sobel density, palette
composition, class-boundary length). Held-out: Cappadocia 130, evaluated once.

**Frozen rule** (fixed criterion — among candidates with catch ≥ 2×loss on the fit set,
maximize catch): veto if **class-boundary length < 0.140**. Fit set: catch 0.872, loss 0.427.

**Held-out result:** catch 1.000, loss **0.919** → registered acceptance (catch ≥ 2×loss)
**FAILS**. On Cappadocia (base rate of high-residual chips 71.5%, generally sparse inputs) the
rule vetoes 127/130 chips — operationally it discards the site. The 3 kept chips have median
C2 residual 1.05 px vs 2.86 px for all chips, so the *direction* is right and the predictors
carry real signal (reference logistic AUC 0.843 on the held-out site), but the transparent
single-threshold rule is not usable.

**Why it failed, honestly:** the registered selection criterion rewarded raw catch, and the
fit set's density mix let a loose boundary threshold satisfy catch ≥ 2×loss there while
degenerating on a sparse site. The failure is in the rule form and selection criterion, not in
the feature set.

**Discipline:** per the standing rules this result stands as a FAIL; no threshold is adjusted
after seeing the held-out outcome. Any revised rule (e.g., a criterion that penalizes
site-conditional loss, or a probability-calibrated rule with a registered operating point) is
a **new registration** with a fresh held-out evaluation — Phase F work. Recorded so that the
next attempt inherits the failure mode instead of rediscovering it.

Features and script: `veto_features.csv`, `veto_rule.py` (session scratchpad; regenerable).
