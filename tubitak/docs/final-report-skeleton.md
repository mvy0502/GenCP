# Final report skeleton — the working document (from tag `v0-deliverable`)

> **Conventions:** Δ = candidate − baseline, negative = candidate better. Every number below
> carries: **[path]** = inference path (STOCH = stochastic/dropout-active, DET =
> deterministic) and **[prov]** = input OSM provenance (OVP = Overpass, PRE = pre-fix
> Geofabrik, POST = post-fix Geofabrik). **CBQ** = CANNOT BE QUOTED (superseded/off-path).
> Every experiment from here fills a named hole in this document; none opens a new one.

## 1. The tool (gencp-ref)

Extent → georeferenced 10 m synthetic reference GeoTIFF + ranked reliability sidecar +
embedded provenance. Deterministic by default (`--stochastic` preserves the evaluated path);
640 m feather overlap (seam clustering statistically zero: obs/exp 1.01, p = 0.46
[STOCH, POST]); corrected transform (TRUE_GSD 10.0390625) mandatory; `-s smart` extraction;
`--bands single` refuses pending the panchromatic conversion decision. Gate: render layer
byte-exact vs sound archive [DET-equivalent, POST]; mosaic interior exact; georef lag (0,0).
**HOLE: none — tool is delivery-shaped.**

## 2. Input/output contract

Input: bbox/GeoJSON + CRS + arm + bands. Output: reference.tif (10 m, requested CRS, tags:
tool version, arm, checkpoint sha256, seed, inference path, torch, OSM snapshots, CLC+
version, repo commit, seam ratio) + reliability.{tif,csv} + provenance sidecar + optional S2
QA preview (never an input). **HOLE: single-band output contract (B-package pending).**

## 3. The arms

| arm | config | status |
|---|---|---|
| pretrained | Zenodo release | baseline |
| C1 | GAN+L1 fine-tune, cold-start D, warm-up amendment | **HOLE B1: cold-D artefact vs loss-function effect — unresolved; the "adversarial liability" claim is conditional on it** |
| C2 | L1-only fine-tune | recommended hand-over arm (Package A) |
| C3 | C2 + 17.7% EU mix | recommended training config; indistinguishable from C2 at n=30 |

## 4. The decomposed answer (all [STOCH] unless marked)

- Ankara 130, RGB KLT: pre 2.588 → C1 1.869 → C2 0.929 px; C2−pre −1.167 ± 0.074 [OVP]
  → **CBQ as headline: off production path.** Production restatement [POST, n=30]:
  C2−pre ≈ −0.84…−0.97 px.
- Europe 568: C2−pre −0.364 ± 0.024 [OVP-analogue corpus renders] — no forgetting.
- Cappadocia transfer R = 0.945, CI [0.73, 1.18] [PRE inputs] — adaptation, not scene
  memorisation.
- Restraint mechanism: blur control recovers −6.1%/+1.7% [OVP]; EU gain 86% scatter;
  matcher sweep: C2 margin grows under NCC (ank130 −0.70 → −1.01) [OVP] —
  **HOLE B3: "matcher-independent" tested only within the area-matcher family; descriptor
  matcher + mediation + direct restraint measurement outstanding.**
- Urban operational headline: **0.591 px (BT.601 KLT, n=20) [STOCH, OVP] — CBQ until B2:
  off production path**; B2 re-measures on POST inputs, K=8, all arms.
- Salt/water rare class: unresolved (C2 salt gain statistically zero; water-dominant class
  absent from training).

## 5. Positioning

Reference-generation for their Georef (extent in → raster out), not GCP lists; two-arm
hand-over (C2 primary, C1 supplied) with the condition table from Package A; reliability
sidecar = their forest-mask request, input-heuristic (variance map measured real but
sub-bar at converged K).

## 6. Honest record

15 corrections entries; 8 standing practices; every gate scored against pre-committed text;
FAILED gates on the record (veto rule; gate-1 FAILED-as-designed); registered predictions
that failed are quoted as failed (R2 scope, NCC prediction, attenuation story).

## 7. Limitations

Georef unmeasurable (all numbers proxy; Package A bounds proxy-sensitivity); train/serve
skew (training PRE, production POST; ~0.6 px forest-heavy cost, lands on the maskable
class — fortunate, not designed); Ankara evaluation inputs OVP (unregenerable — backed up,
manifest committed); scene-date confounds as registered; KLT noise floor ~2 px context.

## 8. Future work

Phase F backlog: veto re-registration; regenerable-label audit; retraining on POST inputs;
variance map (closed: sub-bar at converged K); sparse-EU regression under C3; single-band
package; **B1 confirmatory run if cold-D damage confirmed (one D-only warm-up run — not
launched without report-first).**
