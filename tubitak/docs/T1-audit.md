# T1 registration audit — the E3 test applied to the paper's load-bearing table

Date: 2026-08-23. Trigger: corrections-log entry 16 showed that a registration-integrity
claim of the same form as T1's ("amended … before any number existed") failed against run
artifacts in E3. T1 carries the paper's central table, so its claim gets the identical
audit before any manuscript text is written. Method is the one entry 16's postscript
prescribes: commit timestamps vs artifact mtimes, run-config JSON diffed against the
registration text, and a full recomputation of the reported table from the raw CSV.

## A. Timeline claim — PASS

Claim audited: "Registration: delivery-registrations.md §T1, commit `7e581b2`, amended
`e175c57` **before any number existed**."

| event | time (UTC) |
|---|---|
| registration commit `7e581b2` | 2026-08-22 10:31:57 |
| data preparation begins (`T1_odtu/cand_s2_alt.tif`, earliest artifact) | 10:34:57 |
| amendment commit `e175c57` (ODTÜ contamination; Cappadocia → primary) | **10:37:26** |
| first file after amendment (`T1_capp` matcher outputs onward) | 10:37:29+ |
| results CSV `T1_recovery_klt.csv` | 10:47:33 |

Only four files predate the amendment, all of them **input rasters/metadata**
(`T1_odtu/cand_s2_alt.tif` 10:34:57, `T1_odtu/cand_basemap.tif` + `candidates_meta.json`
10:35:23, `T1_capp/real_s2_target.tif` 10:37:03). No matcher output and no derived number
exists before 10:37:26. **The claim holds** — unlike E3's, which entry 16 falsified.

## B. Reported table vs raw CSV — PASS, 70/70 cells

Both tables in [T1-benchmark-results.md](T1-benchmark-results.md) were recomputed from
`tool_runs/T1_recovery_klt.csv` under the documented formula
(recovery error = ‖(d_case − d_t0) − applied‖; intrinsic = ‖d_t0‖; applied vector
= k·(cos 30°, sin 30°) px; sim case k = 2). All 70 reported cells (2 sites × 5 candidates
× [intrinsic, KLT pts, t1, t2, t5, t10, sim]) match to reported precision
(tolerance 0.0016 for rounding). Zero mismatches.

## C. Registered protocol vs what ran

| registered | ran | status |
|---|---|---|
| 5 candidates (C2, C1, real S2, EOX, basemap) | 5/5 present | ✓ |
| distortions t1/t2/t5/t10 + similarity, registered before running | t0 + t1/t2/t5/t10 + sim (t0 is the baseline the formula requires) | ✓ |
| "same matcher configuration (KARIOS `karios_gencp.json` unchanged)" | `matching_winsize` 15 in every run config, both sites | ✓ |
| both extents, reported together | T1_capp + T1_odtu, 60 rows | ✓ |
| < 10 usable points → failure-to-register, counted | min n across all 60 runs = 282; rule never triggered | ✓ |
| **secondary matcher ORB+RANSAC (B3 harness)** | **no ORB artifact exists; never run** | **✗ — deviation, entry 17** |

**Deviation 1 (real): the registered secondary matcher was never run**, and
T1-benchmark-results.md did not disclose the omission — it reports KLT-only results without
saying the ORB half of the registered protocol is missing. Recorded as corrections-log
entry 17; a disclosure line is added to the results document in the same commit as this
audit. The omission does not touch the numbers above (they are primary-matcher numbers,
verified in §B), but "registered protocol executed in full" was not true until disclosed.

**Deviation 2 (immaterial, disclosed here):** the registration says "bearing 30°"; the
implementation applied k·(cos 30°, sin 30°) — 30° from grid-east, not a compass bearing
from north. Identical for every candidate, so no effect on any comparison; noted so the
wording and the implementation can't be played against each other later.

## D. Evidence layer

`tubitak/data/*` is gitignored, so mtimes and raw CSVs live outside version control.
Pinned here:

```
sha256  T1_recovery_klt.csv        4f384da5e4a3788a1a12574ca058eb13be8e9c812e47efe88801f7cee0b66ad4
sha256  T1_capp/candidates_meta.json  3579209ee3383c13dddd66fe77a878851ec31374eee2b0a2882a8069e919c0de
sha256  T1_odtu/candidates_meta.json  5e429d64854f425a29b8b21f507abe7d9c76dde5d228fbb1e5967438658c4e80
```

Off-machine copy: the Kaggle evidence backup
([evidence-backup-manifest.txt](evidence-backup-manifest.txt)).

## Verdict

**T1 survives the audit that E3 failed.** The timeline claim is true, the table reproduces
from raw data cell-for-cell, and the executed protocol matches the registration on every
parameter except the secondary matcher, which was registered, not run, and is now disclosed
(entry 17). The paper may cite T1 as pre-registered **with** the entry-17 caveat; the
manuscript wording rule stands: "experiments were pre-registered where stated; deviations
from the registered protocol are documented in a public corrections log."

Audited but out of scope here: the remaining registrations (B1–B3, phase-c/-d, packageA,
tool gates) get the same treatment next — tracked in [paper-roadmap.md](paper-roadmap.md).
