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

---

## 3. Phase D amendment: Cappadocia added — overriding the metric, deliberately (2026-08-19 09:29:30 UTC)

Cappadocia is included **despite** its low JSD (0.116), and the reasoning is the point: the JSD
measure compares **class composition**. The observation that motivated this entire phase — white
badlands rendering as dark woodland with an incoherent blob — was a **morphological** failure:
ordinary classes, alien texture and relief. A composition metric cannot see that axis by
construction (§1 already flagged it as blind to relief). Deferring to a measure known to be blind
on the relevant axis would not be rigour; it would be laziness. The override is recorded as such.

Two distinct kinds of out-of-distribution, now separated by design:

| | site | JSD | mechanism probed |
|---|---|---|---|
| compositional | **Tuz Gölü** (36SWJ, 2026-04-30, cloud 1.19 %) | 0.467 | unusual class mix |
| morphological | **Cappadocia** (36SXJ, 2026-05-27, cloud 0.20 %) | 0.116 | ordinary classes, unfamiliar shape/texture |

Phenology note: three of four Phase C/D scenes are 2026-04-30; Cappadocia has no usable 04-30
scene (best that day > 20 % cloud) and takes 05-27 at 0.20 % — a stated four-week deviation.

### Registered Cappadocia prediction (before any Cappadocia data is prepared)

> Tuff-badlands chips (high relief texture, composition dominated by perm-herb/bare) degrade
> **morphologically**: generated imagery misrenders the eroded-valley texture (the badlands
> signature), with matched gap **> +0.5 px** against density-matched Europe on those chips, while
> flat agricultural chips in the same granule behave like Ankara (within ±0.3 px).

### Mechanism separation — the outcome table, registered in advance

| Tuz Gölü salt chips | Cappadocia badlands chips | conclusion |
|---|---|---|
| fail (> +0.8 px) | hold (≤ +0.3 px) | the limit is **composition** |
| fail | fail (> +0.5 px) | the limit is **morphology** — landform-vocabulary hypothesis confirmed in its strong form |
| hold | hold | the landform explanation is **wrong**; the badlands chip was an isolated anomaly |
| hold | fail | composition robust, morphology not — vocabulary hypothesis holds in texture space only |

Both sites are tested with the **pretrained weights** — the hypothesis concerns the original
training distribution; fine-tuned weights are a separate, subsequent question.

### 3b. Registered confound: Cappadocia's acquisition date (added before any Cappadocia result)

No usable 36SXJ scene exists near the common 2026-04-30 date (±2 weeks: best is 21.3 % cloud on
04-27; the 04-30 window is 25–100 % cloud). The 2026-05-27 scene (0.20 %) stands.

**The confound, registered with its ambiguous direction:** Cappadocia therefore differs from every
other site in phenology as well as landform — four weeks later, and Anatolian vegetation dries
measurably in that window (later ⇒ drier, browner). We also know the pretrained model's own output
prior trends brown (`turkey-results.md` §3.3). The mismatch could thus plausibly cut EITHER way:
a browner real scene may *reduce* the generated-vs-real radiometric gap (model prior closer to
reality) while simultaneously *degrading* vegetation-edge contrast that KLT matches on.
**No direction is claimed.** Any Cappadocia degradation must therefore exceed what phenology can
plausibly produce — i.e. the morphological claim rests on the badlands-vs-flat-agriculture
*within-site* contrast (both halves share the date), not on the site-level comparison against
Ankara. The within-site contrast is the registered discriminator; the cross-site number is
reported with this caveat attached.
