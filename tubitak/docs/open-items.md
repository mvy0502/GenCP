# Open items — read from the top at the end of every package (standing practice 8)

Each item is CLOSED or explicitly DEFERRED with a written reason, every package.

| # | item | origin | status 2026-08-21 |
|---|---|---|---|
| 1 | Cold-D risk on C1 | B20 note | **CLOSED 21 Aug: signature absent; deficit widens with adversarial training; loss-function reading confirmed (headline-results.md B1)** |
| 2 | K-draw small-n rule applied inconsistently: Package A urban rows (n=20/26) scored on single draws after the rule existed | standing practice 2 vs Package A | **CLOSED 21 Aug: B2 re-measured with mean-of-8 on POST inputs; headline 0.593 stands; violation recorded and corrected** |
| 3 | Mechanism of the 0.47 px baseline shift (Phase B −0.247 vs fresh +0.226 on the same Ankara results) | check 1 | OPEN — candidates: 44-chip support, arm-B reference provenance; DEFERRED: does not gate any current claim (both baselines documented; fresh baseline adopted) |
| 4 | Checkerboard-strength vs sparsity within-stratum control (confound flagged, never run) | phase-c-europe-results watch item | OPEN — DEFERRED: artefact shown to cost, not inflate, at every site; the confound affects interpretation of strength, not the no-inflation conclusion |
| 5 | German-chip drift attribution (snapshot re-download) asserted by registration, not established | regB / tool-results | OPEN — closable by re-cutting German extracts from `germany-260817` snapshot and re-scoring the 5 chips; DEFERRED pending institution relevance |
| 6 | Salt / water-dominant class not learned | phase-d/c3 results | OPEN — DEFERRED: superseded in priority by the T1 finding that real imagery is the better reference where it exists; the reliability layer (now shipping, T3) down-weights water |
| 7 | Sparse-Europe regression under C3 (+0.235 ± 0.105) | phase-c3-results | OPEN — DEFERRED unless EU deployment becomes a goal |
| 8 | Veto rule re-registration (held-out FAIL; failure mode documented) | gcp-veto-rule-results | OPEN — Phase F |
| 9 | Regenerable-label audit (scratch purge lesson) | corrections 13 addendum | PARTIALLY CLOSED (evidence backup + manifest, `ccbe41a`); full audit Phase F |
| 10 | Retraining on post-fix inputs (train/serve skew ~0.6 px forest) | phase-c-results limitations | OPEN — Phase F, deliberately not now (standing practice 3) |
| 11 | Variance map | regC/regD | **CLOSED — sub-bar at converged K (rho flat 8→32); sidecar stays input-heuristic** |
| 12 | Single-band output contract | Package A context | OPEN — B3/T1 both used BT.601 successfully end-to-end (KARIOS accepts 1-band; 0.468 px on the ODTU deliverable), so the conversion is now evidenced; `--bands single` still refuses pending an explicit institution decision on which conversion they want |
| 13 | "Matcher-independent" family scope | Package A results | **CLOSED 21 Aug: earned across descriptor+MI families; kept with boundaries (headline-results.md B3)** |
| 14 | Headline off production path | Package A results | **CLOSED 21 Aug: 0.593 px on-path (B2)** |
| 15 | Second off-machine backup location | A1 | **CLOSED 22 Aug: uploaded and verified** — private Kaggle dataset `vedatyildirim/gencp-evidence-backup`, 4,395 files, all five archives, 130/130 unregenerable Ankara inputs confirmed present by enumeration. iCloud remains a synced copy (not a backup); public GitHub release rejected on the unsettled ODbL-over-weights question |
| 16 | B1 confirmatory run | B1 registration | **CLOSED 21 Aug: not triggered (reading A did not obtain)** |

## Package review 2026-08-21 (standing practice 8, first pass)

Read top to bottom. Closed this package: 1, 2, 13, 14, 16 (and 11 previously). Remaining
open with reasons on file: 3 (deferred, gates nothing), 4 (deferred, conclusion unaffected),
5 (closable on demand), 6/8/10/12 (Phase F), 7 (deferred unless EU deployment), 9 (partial;
Phase F), 15 (needs user action - Kaggle upload command provided).

| 17 | T1: at 10 px displacement every candidate fails identically (KLT capture range at `matching_winsize 15`) | T1-benchmark-results | OPEN — DEFERRED: a matcher-configuration limit, not a product property; would need a coarse-to-fine or larger window to explore, and the institution's matcher is not KLT |
| 18 | T1 similarity case measures only the translation component, not full similarity recovery | T1-benchmark-results | OPEN — DEFERRED: no ranking was drawn from that column; closing it needs an affine fit from the KLT point field |
| 19 | ODTÜ extent is train-contaminated (14 chips) — every future benchmark must check train overlap first | T1 amendment | **CLOSED as a practice**: the check is now part of any site selection; the contamination itself is permanent and the site is marked |
| 20 | The secondary ECC/ORB full-scene harness failed comprehensively (ECC non-convergent, ORB ~150 px errors) | T1 execution | OPEN — DEFERRED: KLT (the registered primary) worked; the failure is informative about generic full-scene registration and is recorded, not fixed |

## Package review 2026-08-22 (standing practice 8, second pass)

Read top to bottom. **Closed this package:** 19 (as a practice). **Advanced:** 15 (approved,
uploading), 12 (conversion now evidenced), 2 (T3's Cappadocia arm regenerated, closing the
validation gap that had forced an information-only verdict). **Newly opened and immediately
triaged:** 17, 18, 20 — all deferred with reasons, none blocking. **Still open with reasons on
file:** 3, 4, 5, 6, 7, 8, 9, 10, 12, 17, 18, 20.

**One item is now materially reframed by T1:** items 6, 7 and 10 (rare-class learning,
sparse-EU regression, retraining on post-fix inputs) are all *accuracy-improvement* work on the
synthetic product. T1 found that real imagery outperforms the synthetic reference decisively
wherever it exists. Those items are therefore no longer on the critical path to the
deliverable; they remain open as research questions, and the honest ordering is that closing
them would narrow, not eliminate, a gap that the availability argument — not the accuracy
argument — has to justify.

