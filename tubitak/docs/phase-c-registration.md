# Phase C pre-registration — fine-tuning arms (registered 2026-08-19 09:29:03 UTC)

Registered before any training run exists, on any hardware. Arms:

- **C1** adversarial (GAN + L1), Turkey-only pairs
- **C2** L1-only, Turkey-only pairs
- **C3** (sequential, after C1/C2 verdict): winning arm + ~20 % European corpus pairs

## R1 — which arm wins on KARIOS residual, and by how much

**Predicted winner: C2 (L1-only), by 0.15–0.40 px** on the 130-chip paired median residual.

Reasoning on the record: hallucinated high-frequency structure is an adversarial-loss product —
the discriminator demands realistic busyness, so the generator invents it (measured: busy ratio
~1.0 regardless of input information; edge density 2.1× the input's). For GCP matching, invented
edges are false control points (measured: local match failure rho −0.48 with input information;
ceiling control shows real imagery has no such accuracy dependence). L1-only output will look
blurrier and score worse on any perceptual metric, but blur costs KLT little (points drop, the
surviving ones stay honest) while invention costs accuracy. Hence: **C2 wins residual, C1 wins
points and appearance.**

## R2 — where fine-tuning helps

**Prediction: improvement over pretrained correlates POSITIVELY with OSM/CLC+ information
content** (rho ≥ +0.3 between chip density and improvement). Fine-tuning teaches the model to
render *Anatolian-looking* structure where the input specifies structure; it does not teach it to
stop inventing where the input specifies nothing. Q1 chips improve least or not at all; Q4–Q5
improve most.

## R3 — what falsifies the L1-only hypothesis

C1 beats C2 on paired KARIOS residual by ≥ 0.15 px, or C2's surviving-point count collapses so far
(> 50 % below C1) that accuracy gains are swamped for GCP-database purposes. Either way the
"hallucination is an adversarial liability" mechanism would be wrong or immaterial at this scale.

## R4 — what would mean fine-tuning is not worth doing

Neither arm improves on the pretrained baseline by more than **0.15 px** paired (the same
materiality band as every gate), or any arm *degrades* dense-stratum performance (Q5 worse by
> 0.15 px) while improving sparse strata — trading the model's best case for its worst.

## C3 risk statement (registered now, run later)

C3 tests over-fitting to Anatolian steppe: classes rare in Turkish training but present at test
time (water: 0.34 % of the Ankara scene; dense urban) may degrade under Turkey-only fine-tuning.
Per-class behaviour will be reported, not just aggregates. Prediction: Turkey-only arms lose water
and urban fidelity relative to pretrained; the 20 % EU mix recovers most of it at a small cost to
steppe performance.
