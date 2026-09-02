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
2. `gencp-validation` is a **destination, never a source, for Project 1.** Never work in
   it on Project 1. Never merge a branch into it. It is refreshed at milestones by copying
   the curated `tubitak/` tree. Merging `tubitak-tr` into it would propagate deletions and
   destroy the research record — this has already nearly happened once.
   **Project 2 is the exception (WP17, 2 September 2026):** its canonical copy is
   `tubitak/sr/` in `gencp-validation`. `tubitak/sr/` in this repository is a **frozen
   mirror and must not be edited** — work done here on Project 2 is work that will be lost.
3. **The ownership boundary is a principle, not a list** — see below.
4. All data lives under gitignored `tubitak/data/`.
5. Institutional (TÜBİTAK) imagery must never enter the repository. Report summary
   results only.
6. Google Earth imagery is for internal visual verification only. It must not enter
   the repository, any dataset, or training.

### The ownership boundary

**Ours to change: anything this project created. Not ours: anything the upstream
pix2pix fork shipped.** That is the whole rule. If you did not write it and no work
package of ours did, treat it as upstream and leave it alone.

In practice ours means `tubitak/`, `.gitignore`, this `CLAUDE.md`, and any new root
file a work package explicitly authorises. Upstream means the pix2pix tree —
`models/`, `data/`, `options/`, `util/`, `scripts/` at the root, `test.py`, `train.py`,
`GenCP_HR_demo/`, `GenCP_VHR_demo/`. Read them freely; import from them freely; do not
edit them.

**This was an enumerated list twice, and it failed twice, the same way both times.**
`b815b46` enumerated what could leave the repository and missed
`tubitak/configs/karios_gencp.json` and `tubitak/docs/evidence/regA/regA_per_chip.csv`,
both of which an active harness was reading — the deletion landed and the harness broke
silently. The enumeration was not careless; the files simply were not thought of. That is
what enumerations do.

So the deletion rule is a principle too, and it is a question you ask of the file rather
than a set you check it against:

> **Before removing or relocating any file, ask: does anything in this repository read
> it?** Registrations a gate names, configs a harness passes, evidence a results document
> cites, fixtures a test opens. If yes, it stays — no matter which directory it lives in
> or which category it looks like it belongs to.

The check is mechanical and takes one command: grep the paths referenced by
`tubitak/tests/`, `tubitak/gencp_core/`, `tubitak/qgis_plugin/` and `tubitak/scripts/`,
and confirm every one still resolves. Run it **after** any deletion, relocation or
restore, and report the count.

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
9. Every run records its random seed and the versions of the libraries that affect
   numerics (at minimum: torch, numpy, and the ONNX runtime if used) in its option dump.
   Registration A's stochastic arm cannot be reproduced byte-for-byte because neither
   was recorded.
10. Every verifier is run against a known-true and a known-false case before its verdict
    is trusted — and also against its degenerate invocations: no arguments, empty input,
    a missing file, a path that does not exist. A tool that reports success when given
    nothing to check is not a check.

    The count, measured rather than estimated: an audit of all 23 verifiers under three
    degenerate invocations found **18 that exited 0**. One — the link checker — genuinely
    examined nothing and reported "0 dead". The other 17 ignored the argument entirely and
    re-ran their real work, which prints PASS for a configuration nobody asked for:
    `gate_g.py --overlp=2560` is a typo that passes at 0 m. Both are the same failure
    wearing different clothes, and neither was caught by the plant-a-dead-link discipline,
    which covered only the normal invocation. Verifiers now refuse arguments they do not
    understand (`tubitak/tests/_guard.py`).
11. A check is born with a failing case. Write the known-false input first, watch the
    check report it, and only then trust the check. Testing it afterwards is not the same
    thing: three of the last four checks added to this project could not have caught
    anything, and each was written by someone who believed it worked.

    The three: the link checker passed with no arguments; the dark-theme check asserted
    nothing; the coverage check computed a planet-sized box (300 m added to degrees) and
    was blind to every osmium-cut extract. All three were written last in their package,
    were small, and were assumed to work.

12. When code assumes a unit, it checks that unit where the assumption is made. Four bugs
    in this project are the same sentence — *code that assumes metres met a geographic
    CRS*: the fp16 parity bound, the extent display printing 0.46 degrees as 0 m, the
    EPSG:4258 output that became a 1x1 raster, and `_margin_bbox`'s 300 m margin becoming
    300 degrees. Every caller passing a projected CRS today is not enforcement; it was
    equally true the day before each of those shipped. See `vectors.require_metric`.

## Reporting format

For each gate: prediction, what was run, the numbers, pass or fail. Include the
inference path. Disclose errors you made and how they were caught.

## Concurrency and commit policy

Sessions may run in parallel **only on disjoint directories.** Two sessions writing into the
same directory is not a merge conflict waiting to happen — git never sees it, because both
writes land in the working tree and the first commit picks up whatever the other session
happened to have finished. Project 2 has already done this: WP1 and WP2A ran at the same
time, and both wrote into `tubitak/sr/docs/`. Nothing was lost, but the WP1 session found a
file it had not written sitting in its own output directory, and had to establish by mtime
and process inspection who had written it and whether that session was still running.

**No session runs `git add`, `git commit`, `git checkout` or `git stash` while another
session is working.** Each of these acts on the whole working tree, not on the directory the
session believes it owns. `git add` stages another session's half-finished files; `git
checkout` and `git stash` delete another session's uncommitted work outright, with no
warning and no reflog entry to recover it from.

**Commits happen between work packages, from a single session, once the others are idle.**
Not during a work package, and not from two sessions in turn. Before committing, confirm the
other sessions are idle rather than assuming it — a session is idle when its process has no
spawned work children and nothing in the repository has been written for some minutes. Both
are observable; neither is a matter of opinion.

The reporting rule that follows from this: a commit that includes another session's work
says so in its message, and says whether the committing session verified it. A commit
message is the only place that distinction survives.
