# Positioning registrations E1–E3 — availability, currency, operational resolution
**Registered 2026-08-23, branch `tubitak-tr`, before any number below exists. Convention:
Δ = candidate − baseline; negative = candidate better. Every number states inference path
(STOCH/DET) and input provenance (OVP/PRE/POST). Standing practices 1–8 apply.**

The T1 benchmark came out against our product: where a cloud-free real 10 m image exists,
real imagery registers a target far better than our synthetic reference (0.033 vs 0.541 px at
1 px displacement, clean site). These three measurements decide what the final report's
positioning section may claim, because the conclusion rests on three untested premises:
how often a real reference actually exists (E1), whether current OSM beats a stale image
where the ground changed (E2), and whether the ranking survives the institution's actual
0.5–1 m target resolution (E3).

**Input measurement correction, recorded before it can flatter us.** The T1 benchmark used
the **s2cloudless-2020** EOX layer. The service publishes vintages through **2025**. T1
therefore benchmarked EOX at a six-year-old vintage and it still beat our product; using
2025 would have made the competitor *stronger*, not weaker. The error was conservative
against the competitor — i.e. favourable to us — and the competitor still won, so T1's
conclusion stands and is if anything understated. E1–E3 use the 2025 vintage.

---

## E1 — how often is a real reference actually available?

**Stratification (fixed before sampling).** 24 extents of 7.71 × 7.71 km across Turkey,
crossed over two axes and balanced across regions:
- **Coastal vs interior** (12/12): coastal = centre within 25 km of the coastline; interior
  otherwise.
- **Urban vs rural** (12/12): urban = the extent contains a place with population ≥ 100 k
  (selected from a fixed list of Turkish cities); rural otherwise.
- **Regional spread:** at least 4 of Turkey's 7 statistical regions represented, with no
  region contributing more than 6 extents. Coordinates are drawn from a fixed, committed
  list — not sampled after seeing any result.

**Registered thresholds — fixed now, not after seeing the distribution:**
- **Usable scene** = cloud fraction **< 10 %** *over that extent* (not the scene-level figure
  the archive reports: the extent-level number is computed from the scene's SCL band where
  available, else from the scene cloud value with that substitution stated per row).
- **Current** = acquired within **90 days** of the query date.
- **Window:** the 365 days preceding 2026-08-23.

**Measured per extent:** days since the most recent usable scene; cloud-free fraction of the
extent in the best single recent scene; count of usable scenes in the window; EOX coverage
and **vintage** (the year the layer represents).

**REGISTERED PREDICTION — the outcome that hurts, written down now so it cannot be reframed
afterwards:** EOX cloudless is a global, gap-filled product. If it covers all 24 extents,
then *"no real 10 m reference is available"* is essentially never true, **the availability
argument collapses entirely**, and the only remaining niche for the synthetic reference is
currency (E2). We expect this to happen. If it does, it is reported as a predicted outcome,
not as a disappointment reframed after the fact.

**Reporting rule:** the distribution, never an average. The sentence that creates or closes
a niche has the form *"in X % of sampled extents there is no usable scene newer than N days"*.

**Invariances:** identical query window, thresholds, extent size and cloud definition for
every extent; the same archive endpoint; EOX coverage tested by the same tile request for
every extent.

---

## E2 — currency: does current OSM beat a stale real image where the ground changed?

**Design.** Change is defined **from imagery, not from OSM** — defining it from OSM would
bias toward the very source the synthetic reference consumes.

- **Change detection:** an old Sentinel-2 scene vs a recent one over the same extent,
  compared per 2.57 km tile. Structural-change score = fraction of pixels whose **gradient
  structure** changes (Sobel-magnitude binary maps, |Δ| over a fixed threshold), not raw
  brightness difference.
- **Seasonal control (registered, because seasonal difference would otherwise masquerade as
  structural change):** old and recent scenes are chosen in the **same seasonal window
  (±30 days of the same day-of-year)**, and the change score is additionally reported after
  excluding vegetation-dominated pixels (CLC+ vegetation classes) so that phenology cannot
  drive the ranking. If a same-season pair is unavailable at the chosen site, the site is
  reported as seasonally-confounded and the limitation stated rather than silently accepted.
- **Target:** the recent Sentinel-2 scene. **References:** (a) the old real Sentinel-2 scene,
  (b) EOX at its own (2025) vintage, (c) GenCP C2 rendered from current OSM
  [DET path, POST inputs].
- Same known displacements (1/2/5 px, bearing 30°), same estimator and statistic as T1, so
  the tables read side by side.

**The result that matters is the INTERACTION, not the main effect:** does the
synthetic-versus-real gap depend on how much the tile changed? Tiles are split at the
**median structural-change score** into high-change and low-change halves.

**Registered reading bands for the interaction** (Δ = GenCP − best real reference, per tile,
recovery error; negative = GenCP better):
- **Currency advantage demonstrated:** Δ in high-change tiles is better than Δ in low-change
  tiles by **≥ 0.30 px**, and the difference is ≥ 2 SE.
- **Currency advantage absent:** the difference between the two halves is **< 0.10 px**, or
  its sign favours low-change tiles.
- **Partial/inconclusive** in between — reported as such, with the number, and no positioning
  claim built on it.

**Registered caveat, in advance:** OSM is not automatically current either; it lags reality
by an unknown, variable amount. If the synthetic does not win even in high-change tiles,
**OSM lag is a candidate explanation and is reported as such**, not as a refutation of the
method's premise. Distinguishing the two would need OSM edit-history analysis, which is out
of scope here and is recorded as future work.

---

## E3 — does the ranking survive a 0.5–1 m target? (the operational setup)

**The gap this closes:** T1 used a 10 m Sentinel-2 target. The institution's target is a
0.5–1 m image, and Georef upsamples our 10 m reference to that resolution. The conclusion
probably transfers — but "probably" is not a measurement.

- **Target:** ESRI World Imagery at zoom 18 (**≈ 0.46 m/px**, probed) over the clean
  Cappadocia site.
- **References:** GenCP C2 [DET, POST], real Sentinel-2, EOX 2025 — each **upsampled to the
  target's grid the way Georef would** (bilinear, single resampling per candidate).
- **The basemap is EXCLUDED as a candidate in this run because it is the target.** Stated
  explicitly: scoring a source against itself would be meaningless and would look rigged even
  though it was an oversight in the candidate list. **Resulting limitation, recorded:** the
  basemap was a strong candidate at 10 m (0.028–0.13 px) and its absence from E3 is a gap in
  coverage, not a judgement on it.
- Same known displacements and statistic as T1, **expressed in metres as well as pixels**,
  since a pixel means something different at 0.46 m than at 10 m.

**Why this design is valid despite the target's unknown absolute accuracy (registered):** we
apply a displacement to the target and measure recovery *of that displacement*. Any absolute
georeferencing error in the target is common to all candidates and cancels in the comparison.

**Registered question:** does the ordering match the 10 m-target benchmark? If yes, the T1
conclusion transfers to the operational setup and we say so with evidence rather than
assumption. If no, that is a significant finding and the positioning section is rewritten
around it.

**Invariances:** identical target, identical displacement set, one resampling per candidate
onto the identical target grid, same band handling (BT.601 both sides), same estimator and
acceptance rules.

---

## Deliverable

One document ending in a **positioning statement written to be lifted verbatim** into the
final report and the recipient README: when a real reference should be used, when a synthetic
one should be used *if ever*, and how a user determines which case they are in — each with
its measured evidence. **If the honest answer is "real imagery in essentially all cases",
that sentence is written plainly**, and the tool's remaining value is allowed to stand on
what it is: a working reference generator, a corrected georeferencing path, and a measured
account of where the approach's premise does and does not hold.
