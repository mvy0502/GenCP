# E1–E3 results and the positioning statement

> **Conventions:** Δ = candidate − baseline; negative = candidate better. Registration:
> [positioning-registrations.md](positioning-registrations.md), commit `122a7db`
> (E3 amended `89df56a`; E3-b is a **retrospective** disclosure — E3 is exploratory, see
> corrections-log entry 16). GenCP numbers **[DET path, POST inputs]**;
> real-imagery candidates carry their own provenance below.

Three premises decided what the final report may claim. All three were tested. **All three
came back negative for our product**, and the last section is written accordingly.

---

## E1 — how often is a real reference actually available? **It essentially always is.**

24 stratified extents (12/12 coastal/interior, 12/12 urban/rural, all 7 regions, ≤ 6 per
region — list committed at `122a7db` before sampling), 365-day window, registered thresholds
(usable = < 10 % cloud, current = ≤ 90 days).

| measure | result |
|---|---|
| extents with **no** usable scene in 365 days | **0 / 24 (0 %)** |
| extents with no usable scene **newer than 90 days** | **0 / 24 (0 %)** |
| EOX cloudless 2025 coverage | **24 / 24 (100 %)** |
| days since most recent usable scene | min 0, **median 2**, p90 3, **max 17** |
| usable scenes per year | 16 – 94 (median 41) |

Coastal vs interior and urban vs rural are indistinguishable (median 1–2 days either way).

**This is the registered prediction, met.** The registration stated in advance that if EOX
covered everything the availability argument would collapse and only currency would remain.
EOX covers everything — and free Sentinel-2 alone already closes it, with a median extent
having a cloud-free scene from **two days ago**. The claim "always available, cloud-free, any
extent" is **not a differentiator in Turkey at 10 m**.

*Limitation:* the archive query capped at 100 scenes and every extent hit the cap, so
"usable scenes per year" is a lower bound. The decisive figures (0 % gaps, median 2 days,
max 17) depend only on the most recent usable scene and are unaffected.

---

## E2 — does current OSM beat a stale real image where the ground changed? **No.**

Clean high-change site: **Istanbul 35TPF** (not a training tile), same-season pair
2026-04-26 (target, 0.0 % cloud) vs **2021-05-19** (old reference, 0.01 % cloud) — 23 days
apart in day-of-year, five years apart in time. 25 tiles of 2.57 km. Change defined **from
imagery** (gradient-structure difference), not from OSM.

**Mean recovery error over the 1/2/5 px displacement set:**

| reference | mean error (px) | tiles with enough points |
|---|---|---|
| EOX cloudless 2025 | **0.033** | 25 |
| real Sentinel-2 **from 2021** | **0.057** | 25 |
| GenCP C2 (current OSM) | 0.120 | 19 |

**The registered interaction — the result that mattered — is null:**

| split | high-change Δ | low-change Δ | difference | verdict |
|---|---|---|---|---|
| raw change (median 0.230) | +0.097 px | +0.089 px | **+0.008 ± 0.031 (0.26 SE)** | **ABSENT** |
| non-vegetation change (median 0.135) | +0.085 px | +0.100 px | **−0.015 ± 0.031 (0.48 SE)** | **ABSENT** |

Δ = GenCP − best real reference; the registered band for a demonstrated currency advantage
was ≤ −0.30 px at ≥ 2 SE. Neither split comes close. **A five-year-old real image of a
rapidly developing area still registers a 2026 target better than our synthetic reference
built from today's OSM** — and it does so just as well in the tiles that changed most.

The seasonal control worked and is worth recording: raw change (0.230 median) drops to 0.154
once vegetation-dominated pixels are excluded, i.e. **a third of apparent "change" was
phenology**; the verdict is ABSENT under both definitions.

**Registered caveat, applied:** OSM is not automatically current either. Its lag is unknown
and variable, and this null is equally consistent with "OSM had not yet recorded the change"
as with "currency does not help". Separating them needs OSM edit-history analysis — recorded
as future work, not claimed here.

---

## E3 — does the ranking survive the operational 0.5 m target? **Direction yes; but the
resolution gap dominates everything.**

Target: ESRI World Imagery z18 (**0.46 m/px**, 529/529 tiles) over the clean Cappadocia
sub-extent. References upsampled once onto that grid. **Basemap excluded as a candidate
because it is the target** — stated per the registration; its absence is a recorded gap, not
a judgement, since it was a strong candidate at 10 m.

**E3 is exploratory, not confirmatory** (corrections-log entry 16; AMENDMENT E3-b in the
registrations). Three configurations ran; only the first two were registered. Provenance
reconstructed from the run artifacts (`tool_runs/E3/` — every KARIOS output carries its
config JSON):

1. **Pass 1 (registered, `122a7db`):** `matching_winsize` 15, nine displacement cases
   (0.5/1/2.5/5 m sub-window + 10–100 m). The 10–100 m cases recovered nothing — KLT is a
   local tracker and 20–200 px exceeds its range at any window size (KARIOS's own
   `mean_x/mean_y` confirm ≈ 0). **The sub-window cases did recover.** The E3-a amendment's
   description of this pass ("nothing was recovered and no ranking existed") is wrong for
   them: `E3_summary.json`, containing the sub-window ordering, was written 69 s before the
   amendment commit.
2. **Pass 2 = E3-a (registered, `89df56a`):** `matching_winsize` 64, displacements
   5/10/20 m. **Recovered nothing at any magnitude for any candidate** — the registered fix
   failed. The E3-a diagnosis ("capture range vs resolvable scale") was **partly wrong**:
   enlarging the window did not extend KLT's usable range here.
3. **Pass 3 — the reported table, NOT registered:** back to `matching_winsize` 15,
   displacement set 0.5/1/2/3/5 m. The 0.5/1/5 m cells are pass-1 cells (bit-identical
   recovery rows — deterministic same-config rerun); 2 and 3 m are new targets run after
   E3-a failed. This contradicts E3-a's "no other parameter changes" on both window and
   displacement set. Disclosed retrospectively as AMENDMENT E3-b; the section is downgraded
   to an exploratory consistency check accordingly.

Reported pass (exploratory; `matching_winsize` 15):

| reference | 0.5 m | 1 m | 2 m | 3 m | 5 m | mean | KLT pts |
|---|---|---|---|---|---|---|---|
| EOX 2025 | **0.438** | **0.747** | **1.750** | 2.814 | **4.561** | **2.062 m** | 210 |
| real S2 (other date) | 0.523 | 1.112 | 2.173 | 2.803 | 4.984 | 2.319 m | 320 |
| GenCP C2 | 0.994 | 0.986 | 2.543 | **2.529** | 4.844 | 2.379 m | 71 |

**Ordering matches T1 in direction** (EOX ≥ real S2 > GenCP) — read as an exploratory
consistency check per the label above, not as confirmation that the T1 conclusion transfers.
**The magnitudes carry the more important message:** every candidate's error is comparable
to the displacement applied — i.e. at a 0.5 m target, a 10 m reference recovers almost
nothing below a few metres, *whichever* 10 m reference you use. The gap between candidates
(2.06 vs 2.38 m) is small against their absolute errors, **and no dispersion is reported
yet**: these are means only, on 71 KLT points for the GenCP arm against 210/320 for the
others. Until the bootstrap CIs registered in E3-b are computed, the 0.32 m gap between
candidate means is not distinguishable from noise and no cross-candidate statement beyond
"direction is consistent with T1" may be quoted from this table.

**The operational consequence, which is useful to the institution regardless of our product:**
when georeferencing 0.5–1 m imagery against any 10 m reference, expect metre-scale residuals
set by the reference's resolution; the choice among 10 m references matters far less than the
resolution gap itself. *Caveat:* this is measured with KLT. Georef's own cross-resolution
strategy may do better, and we cannot measure it — every number here remains a proxy.

---

## POSITIONING STATEMENT (written to be lifted verbatim into the final report and the recipient README)

**When to use a real reference: essentially always, at 10 m.** Across 24 stratified extents
in Turkey there was no case where a cloud-free Sentinel-2 scene was unavailable — the median
extent had one from two days earlier, the worst from 17 days earlier — and the free EOX
cloudless mosaic covered every extent. Where a real 10 m reference exists it also registers
better: at a site with no training overlap it recovered a 1 px displacement to 0.03 px
against our synthetic reference's 0.54 px, and a five-year-old real image still beat our
current-OSM synthetic even in the areas that had changed most.

**When to use a synthetic reference: only where no imagery of the area exists at all, or
where the map, not the image, is the thing you need to match.** We looked for a niche in
availability (E1) and in currency (E2) and did not find one in Turkey. A synthetic reference
remains meaningful where imagery archives genuinely do not reach, where licensing forbids
using existing imagery, or where the intended match is against mapped features rather than
observed ground — none of which we were able to demonstrate as an advantage with the data
available to us.

**How to tell which case you are in.** Query the Sentinel-2 archive for your extent and
window; if a scene under ~10 % cloud exists within your currency tolerance, use it. If not,
check the EOX cloudless mosaic, which is global and free. Only if both fail does a synthetic
reference become the better option. If you are georeferencing 0.5–1 m imagery, expect
metre-scale residuals from any 10 m reference and choose based on availability rather than
on the source's identity.

**What this project delivers, stated honestly.** Not a more accurate reference. It delivers
a working extent-to-reference generator with a corrected georeferencing path (a real +0.39 %
scale error found, measured at 14.1 m in the far corner, and fixed), a reliability layer that
demonstrably improves delivered accuracy when used as a ranking (−0.21 px at Ankara, −0.42 px
at Cappadocia for 25 % of coverage given up), and — most durably — a measured account of when
this method's premise holds and when it does not. The negative results above are the
project's most reusable output: they tell the institution where not to spend effort.
