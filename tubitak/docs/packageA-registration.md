# Package A registration — does the arm ordering survive a change of measurement condition?
**Registered 2026-08-21, branch `tubitak-tool`, before any number below exists. Convention:
Δ = candidate − baseline; negative = candidate better; "gain" defined at point of use as −Δ.
Inference path: every input image was generated on the stochastic (dropout-active) path and
is used AS-IS — nothing generated, nothing downloaded, no institutional data. Registration A
bounded the deterministic/stochastic gap (|Δ| ≤ 0.05 px at n = 30 resolution); path is a
label here, not an axis.**

**The question is not "which arm is best" but: does our arm ordering survive a change of
matcher, band, and subset?** Every number is a proxy — we cannot run Georef, ever; the value
of the decision table is that it bounds how much the choice of proxy matters.

## Inventory contradiction, reported before design

The work package states all four arms' outputs are on disk. **Partially false after the
scratchpad purge** (corrections-log entry 13 addendum): surviving coverage is —
Ankara-30 (task3): all 4 arms × both input sources ✓; Ankara-130: pretrained/C1/C2 (regC
seed-42 draws) — **no C3**; EU-150: C1/C2 only. Per "no new generation", the missing cells
are **not regenerated**: the 4-arm table rides on Ankara-30, the 3-arm table on Ankara-130,
the 2-arm table on EU-150, each labeled with its n. (The purge is precisely why standing
practice 7 exists; the fakes that survive are those written to `tool_runs/`.)

## Invariances — what every comparison below assumes identical on both sides

Data source: the archived fakes and the project's own Sentinel-2 reference warps (`run/ref`,
`eu_holdout/ref_warp`), unchanged. Render path: none re-run. Code path: one scoring engine
per matcher applied to all arms; **the SAME band conversion applied to monitored AND
reference sides** — a per-side conversion difference would itself be a radiometric effect
and would be read as an arm result; this is the explicit invariance of task A1. Determinism:
scoring is deterministic; the images carry common dropout noise, which is **common to all
matchers on a given image** (they score the same pixels) and therefore does not bias the
cross-matcher comparison. Warp geometry: the existing 228-px/10 m corrected-affine warps.

## A1 — band conversions (registered before scoring)

- **Primary: BT.601 luminance** (0.299 R + 0.587 G + 0.114 B) — the standard broadcast
  luminance for 8-bit imagery of this kind; chosen over BT.709 because the products are
  plain 8-bit RGB visual composites, not linear-light HD video primaries.
- **Secondary: unweighted mean** of the three bands.
- **No third "pan-like" weighting.** Sentinel-2 carries no panchromatic band, our products
  are TCI-style RGB (B04/B03/B02), and a defensible pan response (~0.48–0.82 µm) would need
  B08, which these products do not contain. Rather than invent a weighting, this is stated
  as a limitation.
- KARIOS accepts single-band rasters (probed: 1-band run returns points normally).

## A2 — matchers and the cross-matcher comparison (registered before scoring)

| matcher | statistic per chip |
|---|---|
| KLT (KARIOS, config unchanged) | median over matched points of hypot(dx,dy), px |
| NCC template grid | 32×32 templates, 16-px grid, ±8 px search, subpixel parabola fit, acceptance peak r ≥ 0.5; median over accepted points of displacement magnitude, px |
| Phase correlation | ONE global shift magnitude per chip (Hann-windowed, subpixel) — a different quantity, reported in its own column, never mixed |

- **Primary readout: the RANK of the arms under each matcher**, plus the paired Δ between
  the top two arms with SE.
- **Ordering preserved** = identical rank of the available arms. **Ordering changed** is
  claimed only when a flipped pair's paired Δ under the new condition is nonzero at ≥ 2 SE;
  anything weaker is "rank unstable within noise" and reported as such.
- **Registered prediction:** NCC rewards sharpness and a well-localised correlation peak, so
  C2's blur should cost it more than under KLT; C1 should close the gap and may overtake.
  Bands (on the same chips, same conversion): **"closes"** = paired Δ(C1 − C2) under NCC
  shrinks to ≤ 50% of its KLT value; **"overtakes"** = Δ(C1 − C2) ≤ −0.10 px under NCC at
  ≥ 1 SE. If C2 still wins under NCC at ≥ 75% of its KLT margin, the restraint result is
  materially STRONGER than currently claimed — it stops being conditioned on one matcher.

## A3 — urban subset (chip lists committed with this registration)

Urban = built-up/gray fraction of the INPUT render ≥ **0.05** (canonical palette
classifier). Lists in [packageA-urban-chips.csv](packageA-urban-chips.csv), committed
before any of those chips is scored: **Ankara-130: n = 20; EU-150: n = 26; Ankara-30
subset: n = 2 — too small, reported without verdict.** Urban results quoted in RGB and the
primary grayscale, beside the production-path restatement (C2 − pretrained ≈ −0.97 px on
production inputs, not −1.167).

## Deliverable

One results document ending in the decision table:
**condition (matcher × band × subset) → which arm we would hand over** — with the standing
limitation stated: Georef is unmeasurable from here; if one answer fills the table we
recommend one arm and supply the other; if cells disagree, that disagreement IS the result
and defines the two-arm hand-over conditions. Report back before any merge to `tubitak-tr`.
