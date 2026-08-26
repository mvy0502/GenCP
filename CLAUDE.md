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

## Reporting format

For each gate: prediction, what was run, the numbers, pass or fail. Include the
inference path. Disclose errors you made and how they were caught.
