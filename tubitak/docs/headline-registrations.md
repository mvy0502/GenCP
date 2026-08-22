# Registrations B1–B3 — the three measurements that decide the headline
**Registered 2026-08-21, branch `tubitak-tool`, before any number exists. Convention:
Δ = candidate − baseline; negative = candidate better; "gain" defined at point of use as −Δ.
Every result states inference path and input provenance (standing practice 5).**

## B1 — C1's loss: loss-function effect or cold-discriminator artefact?

The most quotable claim ("for GCP generation the adversarial term is a liability") rests on
C1-vs-C2, and C1 was fine-tuned against a randomly initialised D — a risk we recorded
ourselves (B20: early D gradients can damage G silently) and never revisited. Direct
counter-evidence already in our numbers: the false-control-point mechanism predicts MORE
points landing wrong; observed is FEWER points (61 vs 75; Q5 120 vs 194) AND worse
residuals.

**Design:** score existing checkpoints — no GPU, no training. C1 epochs {1, 2, 5, 10, 20}
and C2 epochs {1, 2, 5, 10, 20} (control), standard Ankara-130 set, KARIOS config unchanged,
against the pretrained baseline (2.588 px median; paired per chip).
**Inference path: STOCHASTIC seed 42** — consistency with every C-phase number this is read
against (regA bounds the det/stoch gap at ≤0.05 px). **Input provenance: Overpass**
(`run/inputs`, the exact files the C-phase numbers used). n = 130 ≥ 60 → single draw per
standing practice 2.

**Invariances — identical across all 10 cells:** inputs, references, warp geometry, KARIOS
config, seed, code path. The ONLY varying element is the checkpoint (arm × epoch).

**Registered readings:**
- C1 dips BELOW pretrained at epoch 1–2 (paired C1(e)−pre > 0 at ≥2 SE) then recovers →
  **cold-D damage is real**; the claim is renamed to a warm-start-protocol statement and
  does not generalise to other GAN reference generators. The honest fix is ONE confirmatory
  run (D-only warm-up, G frozen ~200 iters, else identical to C2's schedule) — **reported
  first, not launched in this package.**
- C1 improves monotonically from epoch 1 and plateaus above C2 → the loss-function reading
  survives.
- Anything between: the shape is reported with which reading it supports and how strongly.

## B2 — the operational headline is off-path; re-measure it on the production path

0.591 px (urban, BT.601 KLT) was measured on Overpass inputs; the delivered tool renders
post-fix Geofabrik; the common-mode term is +0.33…+0.58 px/arm. Standing practice 5 was
violated at its first opportunity by quoting it as the headline — recorded, not excused.

**Contradiction reported, before design:** the committed urban list has 46 chips (Ankara 20
+ EU 26), but the EU corpus test chips carry **no real-world geolocation** (synthetic-origin
pairs) — their inputs CANNOT be regenerated from Geofabrik by anyone. **Scope = the 20
Ankara urban chips**; the EU-26 remain quotable only on their archived corpus renders, and
the document says so.

**Design:** render the 20 Ankara urban chips' inputs from post-fix Geofabrik (`-s smart`
extent extract, CLC+ base — the production render path); all four arms; **K = 8 seeded
draws (42…49), mean-of-8 estimator (standing practice 2, n = 20 < 60)**; score RGB KLT and
BT.601-gray KLT against the standard references. Report as **value ± SE (production path,
K = 8, n = 20)** per arm, plus paired C2 − pretrained and C2 − C1.
**Inference path: STOCHASTIC (mean-of-8). Input provenance: POST.**

**Invariances:** same chips, references, warp, KARIOS config as the Package A urban rows;
the ONLY changes are input provenance (OVP → POST) and the estimator (single → mean-of-8,
per the standing rule).

**Registered restatement criterion:** if the production-path urban C2 figure differs from
the quoted 0.591 px by **more than 0.15 px** (the standing materiality band), the headline
is restated — **and the restated number is the one that goes to the institution regardless
of which direction it moves.**

## B3 — earn "matcher-independent" or withdraw it

KLT, NCC and phase correlation are one family (intensity/gradient area matchers); C2 is
trained on pixel L1 — an approximation of that family's own criterion. The NCC margin
growth is exactly what the trained-on-the-metric explanation predicts. Three parts:

1. **Different-family matchers** (OpenCV 4.8.1, karios env; existing BT.601 warps from
   Package A; sets ank130 pre/C1/C2, eu150 C1/C2, ank30 both sources 4 arms):
   - **ORB + RANSAC:** ORB (nfeatures 2000) on monitored and reference grays; BFMatcher
     Hamming cross-check; RANSAC via `estimateAffinePartial2D` (threshold 3 px); per-chip
     statistic = **median displacement magnitude of RANSAC-inlier matches** (px); chips
     with < 10 inliers reported as unmatched, counted separately.
   - **AKAZE + RANSAC:** same harness, AKAZE defaults — the corroborating descriptor.
   - **Mutual information:** global MI shift per chip (grid search ±8 px, 64-bin joint
     histogram, parabola subpixel) — a global-shift quantity, own column, never mixed with
     per-point matchers (the phase-correlation rule).
2. **Mediation check (no new runs):** per chip, photometric similarity (Pearson r of gray
   fake vs gray real) and gradient similarity (Pearson r of Sobel magnitudes); test whether
   the per-chip C2 − C1 KLT residual difference survives conditioning on Δsimilarity
   (partial correlation / OLS with the similarity difference as covariate). **Fully
   mediated** (registered): the conditional C2 − C1 gap loses ≥ 80% of its magnitude AND
   significance at α = 0.01.
3. **Direct restraint measurement (flagged in the record, never run):** within input-silent
   pixels (canonical Sobel ≤ 20 on the input render), edge fraction (Sobel > 20) of each
   arm's output vs the real chip's edge fraction on the SAME pixels; per-chip ratio
   output/real. Pretrained's analogue measured 2.1× on the input side historically; here
   the registered read-out is the per-arm ratio distribution (C2 ≈ 1 = honest; ≫ 1 =
   invention), Ankara-130. Restraint is currently inferred by elimination; this measures it.

**Invariances:** same images, same gray conversion both sides, same warps; only the matcher
family varies. Dropout noise is common to all matchers per image.

**Registered withdrawal condition, stated in advance so it is not a judgement call:** if
the C2-first ordering flips under a descriptor-based matcher at ≥ 2 SE, **or** the C2 − C1
gap is fully mediated by photometric/gradient similarity (definition above), the phrase
"matcher-independent" is withdrawn from every document and replaced by: *"C2 wins under
area-correlation matchers (KLT, NCC, phase); descriptor/statistical matchers …"* with the
measured continuation. Partial mediation or a sub-2-SE flip = reported as measured, wording
narrowed proportionally.

**Inference path: STOCHASTIC (archived fakes as-is). Input provenance: OVP (ank130/eu150),
POST+OVP (ank30 pair).**
