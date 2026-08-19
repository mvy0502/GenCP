# Phase C/D preparation — training data and the landform-ranked second site

**Date:** 2026-08-19 · Phase B closed (`turkey-results.md`).

## 1. Phase D: site selection by landform distance, not intuition

**Method.** Signature per site = CLC+ Backbone class-composition vector (13 classes) over a
~25.7 km box, plus class-boundary patchiness. Distance = Jensen–Shannon divergence to each of the
77 European corpus tiles' signatures; a candidate's score is its distance to the **nearest**
European tile.

| candidate | min JSD to EU | nearest EU tile | composition |
|---|---|---|---|
| **Tuz Gölü** | **0.467** | 30SVJ | bare 60 %, water 36 % — salt flat |
| Black Sea (inland Rize) | 0.169 | 31TFK | broadleaf 58 %, low-woody 24 % (tea) |
| Cappadocia | 0.116 | 30TVL | perm-herb 59 %, bare 18 % |
| Kars plateau | 0.086 | 31UCR | perm-herb 60 %, period-herb 36 % |
| Ankara (control) | 0.061 | 31UES | — |

**Validation of the measure, honestly:** Ankara — known to generalise — ranks closest ✓; Tuz Gölü
is extreme at 2.8× the runner-up ✓. Two defects stated: the Black Sea "near-in-distribution
control" ranks middle, not close (its tea terraces classify as low-woody, a class the corpus
barely contains); and the composition signature is **blind to relief**, so Cappadocia's tuff
badlands — novel as landform, ordinary as land cover — are under-ranked. A first placement of the
Black Sea box was 74 % open sea and was corrected before use.

**Selection: Tuz Gölü (granule 36SWJ)** — the strong test. Bare-60/water-36 salt flat has no
European analogue by a factor of 2.8 in signature space.

### Registered prediction (before any Tuz Gölü data is acquired)

> Generalisation holds inside Europe's landform vocabulary and degrades outside it. For Tuz Gölü
> chips dominated by the salt surface (bare+water > 30 % of chip): **matched gap > +0.8 px**
> against density-matched Europe (cf. Ankara's −0.25), with visible semantic failure of the crust
> rendering in imagery. Non-salt chips of the same granule (dry farmland fringe) behave like
> Ankara (matched gap within ±0.3 px) — the degradation is landform-local, not site-wide.
>
> **Falsified if:** salt-surface chips show matched gap ≤ +0.15 px (the model is
> landform-robust and the vocabulary theory is wrong), or if fringe chips degrade as much as salt
> chips (the effect would be site-generic, not landform-specific).

**Spring availability (query only, nothing downloaded):** 36SWJ — 37 scenes, best 1.2 % cloud on
**2026-04-30, the same date as the Ankara acquisition**; Cappadocia 36SXJ 0.2 % (05-27);
Kars 38TLL 0.5 % (04-28); Black Sea 37TFF 0.1 % (04-16). All viable.

## 2. Phase C: training data prepared and leakage-verified

**Leakage check, by explicit set difference (not assertion):**

```
valid candidates : 1564
evaluation set   :  130     eval ∩ valid = 130 ✓
TRAINING pool    : 1434     train ∩ eval = 0 ✓
```

**Pairs built:** 1434 × 514×257 `[satellite | OSM+CLC+ render]` GeoTIFFs (LZW, 396 MB), corpus
convention, from the fixed snapshots (S2 2026-04-30, OSM 2026-08-18, CLC+ 2021 V1_1) —
`tubitak/data/ankara/train_pairs/`.

**Expansion options (scouted, not downloaded)** — each ≈ 1.4–1.6 k additional pairs after
screening, ~350 MB TCI + 5 MB SCL:

| tile | position | spring scenes | best cloud |
|---|---|---|---|
| 36SVJ | S | 39 | **0.0 % (2026-04-30 — same date)** |
| 36TUK | W | 37 | 2.5 % (2026-04-30 — same date) |
| 36SWJ | SE | 37 | 1.2 % (2026-04-30 — same date; also the Tuz Gölü granule) |
| 36TWK | E | 38 | 0.1 % (2026-04-07) |
| 36TVL | N | 18 | 7.6 % (2026-04-15) |

Three adjacent tiles have near-zero-cloud scenes from the **same acquisition date** as the Ankara
scene — an expansion can hold phenology constant, which the corpus itself never managed.

**Deferred decision, noted:** whether to mix European corpus pairs into Phase C training against
catastrophic forgetting. Data already local; a decision, not an acquisition.
