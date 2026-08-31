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

| 21 | E2's null is equally consistent with "currency does not help" and "OSM had not yet recorded the change" | positioning-results E2 | OPEN — separating them needs OSM edit-history analysis over the Istanbul tiles; recorded as future work, no claim rests on the distinction |
| 22 | E3 measured cross-resolution matching with KLT only; Georef's own strategy may differ | positioning-results E3 | OPEN — DEFERRED: unmeasurable from here (the standing Georef limitation); the resolution-gap conclusion is stated as KLT-conditional |
| 23 | E1's "usable scenes per year" is a lower bound (archive query capped at 100, every extent hit the cap) | positioning-results E1 | **CLOSED as immaterial**: the decisive figures (0% gaps, median 2 days, max 17) depend only on the most recent usable scene, not the count |
| 24 | E3 basemap excluded as candidate because it was the target | positioning-registrations E3 | OPEN — DEFERRED: a coverage gap by construction; closing it needs a fourth independent high-res source |

## Package review 2026-08-23 (standing practice 8, third pass)

Read top to bottom. **Closed this package:** 23. **Newly opened and triaged:** 21, 22, 24 —
all deferred with written reasons, none blocking the deliverable. **Materially reframed by
E1–E3:** items 6, 7 and 10 (rare-class learning, sparse-EU regression, retraining on post-fix
inputs) were already off the critical path after T1; E1 and E2 remove the last two arguments
that could have put them back on it. They stay open as research questions with no route to
the deliverable's value.

**Standing state of the ledger:** 24 items, 8 closed, 16 open — every open item carries a
written reason and none blocks the final report.

| 25 | Cappadocia known-displacement recovery for arms C4/C5 (entry into the paper's main table) | phase-c-lpips-registration evaluation panel ("if cheap") | OPEN — DEFERRED: the T1 harness script was not preserved (inputs/outputs only); adding arms requires reconstructing the distortion/recovery protocol from artifacts, which is not cheap and carries protocol-drift risk (the E3 lesson). Route if wanted: re-derive from `T1_capp/klt/` artifacts + `delivery-registrations.md` §T1, register the reconstruction first |

## Package review 2026-08-24 (standing practice 8, fourth pass — C4/C5 package)

Read top to bottom. **Closed this package:** none of the standing items (none were in this
package's scope). **Newly opened and triaged:** 25 — deferred with reason, not blocking.
**Materially affected by C4/C5:** the paper-facing claims widen (adversarial → plausibility
pressure; [phase-c-lpips-results.md](phase-c-lpips-results.md)); items 6/7/10 remain
research questions off the critical path — nothing in this package changes that. Item 4
(checkerboard) now has two more arms whose outputs could feed its within-stratum control if
it is ever run; still deferred, conclusion unaffected.

**Standing state of the ledger:** 25 items, 8 closed, 17 open — every open item carries a
written reason and none blocks the final report.


## Package review 2026-08-30 (standing practice 8, fifth pass — Project 2 WP2B verification)

This pass opened one item and closed none. It was not a Project 1 package: the item was
found while verifying that Project 2's new QGIS plugin had not disturbed Project 1, which
it had not (`plugin_e2e_run.py` 82/82, Gate G 12/12, sub-pixel offset +0.000181 px, both
plugins loaded in one process).

| # | item | origin | status 2026-08-30 |
|---|---|---|---|
| 26 | Three of twenty-five evidence screenshots differ between two runs of `plugin_e2e_run.py` on the same machine | Project 2 WP2B verification pass | OPEN — DEFERRED, not this week. Cause is identified and is not a rendering nondeterminism: the differing pixels are the dialog's **pre-filled output path**, restored by `dialog._prefill()` from `QgsSettings` (`out_dir`), so the screenshots record whatever directory the profile last wrote to. A small reproducibility question for the paper, since the evidence images are then a function of profile state rather than of the code. Closable by having the harness set the output path explicitly before shot 1, or by clearing that key; deliberately not chased further |

**Standing state of the ledger:** 26 items, 8 closed, 18 open — every open item carries a
written reason and none blocks the final report.

## Package review 2026-08-31 (Project 2 WP12/WP13 — QGIS 3.x compatibility)

| # | item | origin | status 2026-08-31 |
|---|---|---|---|
| 27 | **`tubitak/tests/coverage_block.py` cannot be run: the three OSM extracts it requires are named in no document.** It takes `--wrong=`, `--right=` and `--partial=` and, given none, raises `KeyError: 'wrong'` rather than refusing cleanly (a standing-practice-10 defect in the test itself). What is needed, specifically: an extract that does **not** cover the Istanbul test extent (`--wrong`), one that fully covers it (`--right`), and one that covers it only in part (`--partial`). No fixture in `tubitak/data/geofabrik/` is documented as any of these, and the smallest available non-covering candidate is 660 MB, which costs ~16 minutes to index (`sr/docs/11-zamanlama.md` §5). **Documentation debt, not a code defect: the gate is intact but unrunnable by anyone who did not write it.** Deliberately not constructed now — recorded so the gate does not rot silently | Project 2 WP12 suite run | OPEN — three fixtures to be built and named in the gate's own docstring |
| 28 | **Qt5 dark-capture failure in `plugin_e2e_run` (2 of 82 checks) is undiagnosed.** The harness cannot force a dark palette under Qt 5.15.18 on macOS; the check correctly refuses to assert anything about dark-mode styling on a capture that is not dark. The obvious hypothesis — that `QPalette.ColorRole.Window` does not resolve under PyQt5, leaving the palette empty — was **measured and disproved**: all eight roles resolve on Qt5 exactly as on Qt6. No cause is asserted | Project 2 WP12 | OPEN — plugin unaffected; harness-only |
| 29 | **`demo_dry_run`'s cross-version result is withdrawn, not resolved.** Its apparent Qt6 pass came from profile residue written by earlier runs in the same package via the dialog's `_remember`; the demo project carries no `<GenCP>` properties at all. Re-runs on genuinely fresh profiles hung QGIS 3.44 at startup | Project 2 WP12 | OPEN — needs a fresh-profile harness that does not hang |
