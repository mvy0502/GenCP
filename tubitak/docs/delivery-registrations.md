# Delivery package registrations — benchmark, ODTÜ package, reliability layer
**Registered 2026-08-22, branch `tubitak-tr`, before any number below exists. Convention:
Δ = candidate − baseline; negative = candidate better. Every reported number states inference
path (STOCH/DET) and input provenance (OVP/PRE/POST). Standing practices 1–8 apply.**

The question under all of this, never asked in five days of measuring accuracy: the
institution already has EOX mosaics and free Sentinel-2, and no licence problem at 10 m.
**When is a synthetic reference the better choice at all?** If real imagery wins outright,
that is the finding and it is reported plainly — the project's answer becomes "synthetic is
viable where real imagery is not available", which is still a real answer.

---

## T1 — Known-shift recovery benchmark

**Design:** ground truth is manufactured, not assumed. Take a real Sentinel-2 target scene,
apply a KNOWN distortion, and ask each candidate reference to recover it. The candidate whose
estimated transform is closest to the applied one is the better reference. Truth is exact by
construction.

**Why sources with unverifiable georeferencing may compete honestly (registered reasoning):**
an earlier objection — that we should exclude basemaps because we cannot verify their own
georeferencing — is void under this design. A source's own georeferencing error appears as
recovery error, which is precisely the quantity being measured. A misregistered basemap will
rank badly, for the right reason.

### Candidates

| # | candidate | source |
|---|---|---|
| 1 | **GenCP synthetic C2** (primary) | `gencp_ref.py`, DET path, POST inputs |
| 2 | **GenCP synthetic C1** (secondary) | same |
| 3 | **Real Sentinel-2, different date** | Earth Search STAC, cloud-minimal scene ≥ 60 days from target |
| 4 | **EOX Sentinel-2 cloudless** | public `tiles.maps.eox.at` WMTS. **Contradiction reported:** the package said to mark this NOT AVAILABLE if the institutional copy has not arrived; the *public* EOX cloudless product is reachable, so the row is filled from it and labelled as the public product, not the institutional copy. Attribution: Sentinel-2 cloudless by EOX (CC BY-NC-SA / CC BY depending on vintage) — measured against, never redistributed. |
| 5 | **Open basemap** | ESRI World Imagery tiles at native resolution, downsampled to the common grid |

### Invariances — identical for every candidate

Same target image; same distortion set applied once and reused for all candidates; same
common grid (EPSG:32636, 10 m, identical bounds and size); **one** bilinear resampling to
that grid per candidate; same band handling (BT.601 luminance of 8-bit RGB, both sides);
same matcher configuration (KARIOS `karios_gencp.json` unchanged; ORB+RANSAC exactly as in
B3); same acceptance rules and statistics.

**Asymmetries that cannot be removed — named, per the instruction:**
1. **C2/C1 were fine-tuned on tile 36TVK**, which contains the primary (Ankara/ODTÜ) extent:
   the synthetic candidate is *in-domain* there. Mitigation registered in advance: the whole
   benchmark is repeated at a **Cappadocia extent (36SXJ, not a training tile)**, and the
   in-domain/out-of-domain pair is reported together. Neither is reported alone.
2. **The basemap is natively ~0.5 m** and must be downsampled to 10 m. Justification: the
   institution's workflow consumes a *10 m* reference and upsamples it themselves
   ("10m'lik referansı, yeni görüntünün çözünürlüğüne çıkarıyor"), so comparing all
   candidates at 10 m is the operationally correct treatment, not a handicap.
3. **EOX cloudless is a multi-date composite**, not a single acquisition — different temporal
   semantics from every other candidate, and an inherent advantage in cloud terms which the
   availability column is designed to expose rather than hide.
4. **The real-S2 competitor differs in date from the target** (phenology). That is the
   operational reality, not an artefact.
5. The target is a real S2 scene that is **not** any candidate, so no candidate can win
   trivially by being the target.

### Distortions (magnitudes registered before running)

Applied to the target on the common grid, bearing 30°: translations of **1, 2, 5, 10 px**
(10, 20, 50, 100 m), plus one **similarity** case (rotation 0.3°, scale 1.002, translation
2 px). Five cases → the result is a curve, and where each source breaks down is the
informative part.

### Statistic and matchers

Recovery error = ‖estimated − applied‖ in px (translation cases); RMS corner-displacement
error (similarity case). Estimation: KLT/KARIOS point field → median translation, and
RANSAC partial-affine for the similarity case; **secondary matcher ORB+RANSAC** (B3 harness).
Primary readout = recovery-error curve per candidate; chips/patches with < 10 usable points
are reported as failures-to-register, counted, never silently dropped.

### Availability column — mandatory, reported beside accuracy

For each candidate: **cloud cover over the extent**, **date gap to target**, **coverage
completeness** (% valid pixels), **on-demand producibility for an arbitrary extent and date**
(yes/no). Rationale registered: the synthetic reference's claim was never "more accurate than
real imagery" — it is "always available, cloud-free, any extent, any date, no acquisition".
An accuracy table alone cannot show that, and an accuracy table alone would misrepresent this
project in either direction depending on the scene chosen.

### Registered decision rule

- **RECOMMEND synthetic**: its recovery error is within **0.5 px** of the best real-imagery
  candidate across the whole curve at BOTH extents, and it wins the availability column.
- **RECOMMEND AGAINST**: its recovery error exceeds the best real candidate by **> 2 px at
  the smallest (1 px) distortion** — i.e. it is simply worse on the easy case.
- **CONDITIONAL** otherwise, and the condition must be named explicitly in the results (the
  expected form: "use synthetic where cloud-free, near-date real imagery is unavailable").

---

## T2 — the ODTÜ reference package

**Extent (registered):** EPSG:32636, xmin 477593, ymin 4411827, xmax 485303, ymax 4419537 —
7.71 × 7.71 km centred on ODTÜ campus (39.891 N, 32.783 E), i.e. 3 × 3 nominal tiles, so the
mosaic and seam handling are exercised rather than a single-tile toy.

**Run:** `gencp_ref.py` end to end at the tool's delivered defaults (arm **C2**, DET path,
640 m overlap, corrected transform, POST inputs), producing reference GeoTIFF + reliability
sidecar + embedded provenance. **Accuracy** measured against the real Sentinel-2 over the same
extent, RGB and BT.601, production-path numbers, reported with SE.

**Recipient README (written for them, not us):** what the file is; CRS; **the actual pixel
size 10.0390625 m and why**; what the reliability layer means and how to use it as a mask;
the licence/attribution chain (GenCP CC-BY 4.0 weights; OSM ODbL; Copernicus Sentinel-2;
CLC+ Backbone); and **the one number** that says how accurate it is. Packaged to send as-is.

**Visual:** OSM input | generated reference | real Sentinel-2, side by side — deliverable and
demo material both, produced before the work is called done.

---

## T3 — is the reliability layer worth shipping?

Tested as what it operationally is: **a ranking under a budget**, not a threshold. (The failed
veto experiment already showed the features carry information — held-out AUC 0.843 — and that
a threshold calibrated on Ankara met a different base rate at Cappadocia.)

**Design:** order chips by the tool's input-only reliability score; keep the top N% at
N ∈ {100, 90, 75, 50}; report delivered accuracy (mean and median per-chip residual over kept
chips, C2 arm) against coverage given up. **Fit site: Ankara (130). Validation site:
Cappadocia (130)** — different sites by construction, because the base-rate shift between
them is exactly what broke the previous version.

**Invariances:** same scores already committed in the tool's sidecar formula (input-only, not
refitted here), same per-chip residuals from the existing archived runs, same arm, same
matcher config; only the retention budget varies.

**Registered decision rule:**
- **SHIP AS RECOMMENDATION**: at the 75% budget, delivered median residual improves by
  **≥ 0.15 px** versus the 100% budget on **both** sites.
- **SHIP AS INFORMATION ONLY**: improvement positive but < 0.15 px, or inconsistent across
  the two sites.
- **DO NOT SHIP**: no improvement at any budget on either site, or a perverse/non-monotone
  curve. *A layer that costs 25% of coverage to buy 0.05 px is not worth shipping and we
  will say so.*
