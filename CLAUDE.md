# Project rules — read before working

## Repository roles

Three repositories exist for this project. They are not copies of each other.

| Repository | Role | Who writes |
|---|---|---|
| `mvy0502/GenCP` (this one), branch `tubitak-tr` | **Working repository.** Research record, gate registrations, results, code, QGIS plugin | All agent work happens here |
| `mvy0502/gencp-validation` | **Handover copy** for whoever takes the project over | Destination only — see below |
| `mvy0502/gencp-letter` | Paper (TeX) | Paper work only |

### Rules

1. All work happens here, on `tubitak-tr`. This is where you push.
2. `gencp-validation` is a **destination, never a source.** Never work in it. Never
   merge a branch into it. It is refreshed at milestones by copying the curated
   `tubitak/` tree. Merging `tubitak-tr` into it would propagate deletions and destroy
   the research record — this has already nearly happened once.
3. Do not modify upstream files. Only `.gitignore`, this `CLAUDE.md`, and `tubitak/`
   are ours.
4. All data lives under gitignored `tubitak/data/`.
5. Institutional (TÜBİTAK) imagery must never enter the repository. Report summary
   results only.
6. Google Earth imagery is for internal visual verification only. It must not enter
   the repository, any dataset, or training.

## Standing practices — apply to every work package

1. Every gate registration includes an invariance section: what must not change for the
   result to mean what we claim.
2. State the inference path for every number. Two numbers from different paths are not
   comparable.
3. One sign convention, stated. Never flip it mid-report.
4. Register predictions before outcomes. A registration may be revised only when an
   *input measurement* improves and no outcome has been seen; the earlier version is
   never deleted.
5. Registration text must name the exact corpus and the exact reference directory. A
   wrong name in registration text has already caused a failed gate and a sign flip.
6. Failed gates are reported, not adjusted. Never tune a parameter to make a gate pass.
   A documented penalty we understand beats a passing number we cannot explain.
7. Long runs are checkpointed. Liveness is counted, not assumed.
8. At the end of every work package, review open items and report them.

## Reporting format

For each gate: prediction, what was run, the numbers, pass or fail. Include the
inference path. Disclose errors you made and how they were caught.
