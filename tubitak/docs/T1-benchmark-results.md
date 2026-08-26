# T1 — known-shift recovery benchmark: when is a synthetic reference the better choice?

> **Conventions:** lower recovery error is better. Registration:
> [delivery-registrations.md](delivery-registrations.md) §T1, commit `7e581b2`, amended
> `e175c57` before any number existed — **that claim, and every cell of both tables, has
> been audited against the run artifacts and holds** ([T1-audit.md](T1-audit.md): timeline
> verified, 70/70 cells recomputed from `T1_recovery_klt.csv`, run configs match the
> registration). GenCP candidates: **[DET path, POST inputs]**; real-imagery candidates
> carry their own provenance below.
>
> **Disclosed deviation (corrections-log entry 17):** the registration also names a
> **secondary matcher, ORB+RANSAC (B3 harness). It was never run** — every number in this
> document is a primary-matcher (KLT/KARIOS) result. The omission was found by the audit,
> not disclosed at writing time. Running the ORB half remains open work; until then this
> document is quotable as a primary-matcher result, not as the full registered protocol.

**Design:** ground truth manufactured, not assumed — a known distortion is applied to a real
Sentinel-2 target, and each candidate reference is asked to recover it. Truth exact by
construction. **Recovery error = |(measured displacement − measured at zero distortion) −
applied|**, which isolates the applied shift; the candidate's *own* georeferencing offset is
reported separately as `intrinsic |d0|`, and is itself one of the more useful numbers here.

## Primary site — Cappadocia 36SXJ (clean: zero training pairs at this tile)

| candidate | intrinsic \|d0\| | KLT pts | t1 | t2 | t5 | t10 | sim |
|---|---|---|---|---|---|---|---|
| real S2, other date | 0.262 | 1524 | **0.033** | **0.003** | **0.243** | 9.553 | 1.722 |
| EOX cloudless | 0.329 | 1164 | **0.017** | 0.033 | **0.030** | 8.759 | 1.206 |
| ESRI basemap | 0.128 | 1738 | 0.034 | 0.028 | 0.131 | 10.203 | **1.000** |
| **GenCP C2** | 0.157 | 388 | 0.541 | 1.011 | 3.967 | 10.378 | 1.323 |
| GenCP C1 | 0.218 | 405 | 1.119 | 2.561 | 5.180 | 10.402 | 2.307 |

## Contaminated site — ODTÜ (14 training chips overlap; **not quotable as a ranking**)

| candidate | intrinsic \|d0\| | KLT pts | t1 | t2 | t5 | t10 | sim |
|---|---|---|---|---|---|---|---|
| real S2, other date | 0.073 | 16103 | 0.014 | 0.006 | 0.026 | 8.875 | 0.366 |
| EOX cloudless | 0.353 | 12407 | 0.031 | 0.022 | 0.085 | 9.496 | 0.322 |
| ESRI basemap | 0.648 | 15805 | 0.045 | 0.041 | 0.085 | 9.823 | 0.203 |
| **GenCP C2** | 0.468 | 3241 | 0.039 | 0.008 | 0.112 | 10.238 | 0.281 |
| GenCP C1 | 0.541 | 2248 | 0.027 | 0.025 | 0.131 | 9.816 | 0.067 |

**The two tables together are the measurement of the contamination.** At the site where 14
training chips overlap the target scene, GenCP recovers shifts as well as real imagery
(0.008–0.11 px). At the clean site it is 20–130× worse (0.54–3.97 px). Same tool, same
matcher, same distortions — the difference is train-on-target overlap. This is why the ODTÜ
row is published only as a contamination measurement and never as a capability claim.

**Two columns are uninformative and are reported as such:** at **t10** every candidate fails
identically (~9–10 px error = the displacement was not detected at all), because 10 px exceeds
the KLT capture range at `matching_winsize 15` — a matcher-configuration limit, not a property
of any reference. The **sim** column measures only the *translation* component recovered in
the presence of rotation+scale, not full similarity recovery; it is not a clean similarity
score and no ranking is drawn from it.

## Availability — the column that decides the actual question

| candidate | cloud over extent | date gap to target | coverage | producible on demand, arbitrary extent/date? |
|---|---|---|---|---|
| real S2, other date | 0.006–0.019% (chosen cloud-minimal) | 62–112 days | 100% | **No** — depends on acquisition and on a cloud-free pass existing |
| EOX cloudless | 0% by construction | multi-year composite (2020 vintage) | 100% | **No** — fixed published product, but globally pre-existing and free |
| ESRI basemap | 0% (mosaic) | undated mosaic | 100% | **No** — fixed product, globally pre-existing |
| **GenCP C2** | **0% by construction** | **0 — any date** | 100% | **Yes** — any extent, any time, no acquisition |

## Verdict against the registered decision rule

- **RECOMMEND synthetic** required recovery within **0.5 px of the best real candidate across
  the whole curve at BOTH extents.** At Cappadocia the gap is 0.52 px (t1), 1.01 px (t2) and
  3.94 px (t5). **Not met.**
- **RECOMMEND AGAINST** required exceeding the best real candidate by **> 2 px at the smallest
  distortion.** The t1 gap is 0.52 px. **Not met.**
- **→ CONDITIONAL**, and the registration requires the condition be named explicitly.

**The condition, stated plainly: for 10 m georeferencing reference over an area where any
real 10 m imagery exists — including free Sentinel-2 and the free EOX cloudless mosaic — real
imagery is the better reference, decisively, and we recommend it over our own product.**
Synthetic reference is the right choice only where the real options genuinely fail: an extent
with no usable cloud-free acquisition and no acceptable existing mosaic, or a use case that
requires the reference to reflect **current OSM map content** rather than historical imagery
(new construction, changed road network) — the one axis on which no imagery product can
compete.

**This is the finding the package was written to obtain, and it is negative for our product
in the accuracy dimension.** The honest summary: the institution already owns the better
answer for the common case. Our contribution is (a) a tool that produces a defensible
reference where imagery does not exist, (b) the measurement showing when that is and is not
worth doing, and (c) the discovery that **the fine-tuning gains measured all week — real and
carefully verified — do not close the gap to real imagery at this task.** GenCP C2 is
markedly better than C1 and than pretrained (consistent with every prior result), and still
an order of magnitude behind a free Sentinel-2 scene from two months away.

**One genuine strength survives the comparison, and it is visible in the intrinsic column:**
GenCP's own georeferencing offset (0.157 px at Cappadocia) is the *smallest of any candidate
except the basemap*, and better than the real S2 alternate date (0.262) and EOX (0.329) —
the corrected-transform work is real and the product is not internally misregistered. What
it lacks is matchable content: 388 KLT points against 1164–1738 for real imagery.

Artifacts: `tool_runs/T1_recovery_klt.csv`, `tool_runs/T1_{capp,odtu}/klt/`,
`candidates_meta*.json`. Secondary ECC/ORB harness (`T1_recovery.csv`) is retained but not
scored — see the results caveat in the package report.
