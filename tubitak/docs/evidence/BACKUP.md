# Evidence backup — what is protected, what is not, and what the gap would cost

**Date: 2026-08-26.** Supersedes nothing; complements
`tubitak/docs/evidence-backup-manifest.txt` (2026-08-21), which remains the manifest for the
first backup.

The principle: **back up what cannot be regenerated, not what is merely expensive.** Text
that the manuscript cites is in git and needs no separate backup. Weights matter only if we
want to re-run inference, which is unlikely. An accepted, written risk is fine; an unwritten
one is not.

---

## Backed up

### Backup 1 — Kaggle `vedatyildirim/gencp-evidence-backup` (2026-08-22, 13.7 GB)

| item | why |
|---|---|
| `evidence_inputs_corpora.tar.gz` | the **130 Ankara `run/inputs` Overpass renders — unregenerable.** Every C-phase paired number is measured against these exact files, and the Overpass source they came from is gone |
| `checkpoints_{pretrained,C1,C2,C3}.tar` | all per-epoch `*_net_G.pth`; B1 scores the epochs |

### Backup 2 — Kaggle `vedatyildirim/gencp-evidence-backup-2` (2026-08-26, 14 GB)

> **Status 2026-08-26: PARTIAL — two of four archives are on Kaggle; the other two are
> being re-pushed. Do not treat this backup as complete until the table below says so.**
>
> The four tars exist and are verified locally under `tubitak/data/evidence_backup_2/`
> (14 GB; entry counts checked: `checkpoints_C4.tar` 1,079 entries,
> `generated_fakes.tar` 35,322 entries). They are pushed to Kaggle as a **second dataset**
> rather than a new version of the first, because `datasets version` on the first would
> re-upload its existing 13.7 GB for no benefit.
>
> **`kaggle datasets create` uploaded only `checkpoints_C4.tar` and
> `checkpoints_C4_s43_modal.tar`, then exited with status 0.** `checkpoints_C5.tar` and
> `generated_fakes.tar` were never attempted — they appear nowhere in the command's output,
> not even as a "Starting upload" line, and no error was printed. **A zero exit code from
> this tool does not mean the upload was complete.** That is now a known failure mode for
> this procedure and the reason the verification step below exists.
>
> A `datasets version` push with the full folder is in flight. **This block must be replaced
> with UPLOADED AND VERIFIED plus a per-file confirmation** once
> `kaggle datasets files vedatyildirim/gencp-evidence-backup-2` shows all four archive
> prefixes. Until then, the independent off-machine copy covers **Backup 1 in full and
> Backup 2 only in part**, and `generated_fakes.tar` — the row this document argues is the
> most valuable — is **not yet protected off-machine**.

| item | size | why |
|---|---|---|
| `checkpoints_C4.tar` | 4.7 GB | **base C4 arm** — a cell of the 2×2 design we report directly. 21 per-epoch `net_G` |
| `checkpoints_C5.tar` | 4.7 GB | **base C5 arm** — the other reported cell. 21 per-epoch `net_G` |
| `checkpoints_C4_s43_modal.tar` | 208 MB | **one representative seed-replication arm**, stated: C4 at seed 43, the first seed of the C4 arm. Enough to re-run inference for one seed and confirm the seed pipeline behaves |
| `generated_fakes.tar` | 4.0 GB | **35,322 generated `*_fake.png` across all `tool_runs` packages** |

**The fakes are the important row, and they were not on the original list.** They rank
**above** the checkpoints on unregenerability, and they are cheap:

- Checkpoints **can** be regenerated — expensively, and not byte-identically (see below).
- The stochastic fakes **cannot be regenerated at all.** pix2pix runs dropout at test time,
  and neither the seed nor the torch version was recorded in any run's option dump
  (Item D3; now forbidden by standing practice 9). Registration A's stochastic arm is the
  proven case: re-scoring the **archived** fake reproduces its recorded number exactly
  (2.276977 px, n = 29), while re-generating it cannot.
- They are the audit trail for every number in the record. 4 GB to keep every scored image
  re-auditable is the best ratio in this table.

---

## Deliberately NOT backed up — accepted risk

| item | size | why not |
|---|---|---|
| Seed-replication checkpoints for C1/C2/C4/C5 at seeds 43–50, `_modal` and `_modalwarmup` variants (minus the one representative kept) | **~54 GB** | Their **results are archived as text** — 70 per-chip CSVs under `tubitak/docs/evidence/`, tracked in git, and that is what the manuscript cites. The weights matter only for re-running inference |
| KARIOS output trees under `tool_runs/**/karios/` | ~large | Regenerable from the fakes (which **are** backed up) plus the config, in minutes |
| Warped rasters `tool_runs/**/warp/*.tif` | 0.04 GB | Regenerable from the fakes by an affine warp |
| CLC+ Backbone source raster | 8.2 GB | Third-party CLMS product, re-downloadable |
| Geofabrik `.osm.pbf` snapshots | 18 GB | Third-party, dated, re-downloadable — though **the dated snapshot matters**: see the risk below |

---

## What re-creating the unbacked material would cost

**Compute.** Training runs on Modal A10G. The driver's timeouts are set at roughly twice
expected wall time — `C1`/`C2` 2 h, `C4`/`C5` 4 h — so expected is about **1 GPU-hour per
C1/C2 arm and 2 per C4/C5 arm**. The unbacked set is 6 seeds × 4 arms ≈ **36 GPU-hours**, on
the order of **$40** at A10G rates, plus orchestration time.

**But money is not the real cost, and this is the part to read.** The hardware gate found the
arms are **NOT POOLED** across hardware (`edge_C1` 4.2×): a re-run on different hardware does
not reproduce the same numbers. So re-creating these checkpoints would produce *new* weights
that do not reproduce the recorded seed-replication numbers byte-for-byte. **The 54 GB is not
recoverable at any price — only replaceable.** What protects the conclusions is that the
numbers are in git, not that the weights could be remade.

**Accepted, in writing:** if the 54 GB is lost, the six-seed sign tallies remain fully
defensible from the committed CSVs, and the loss is the ability to re-run inference on those
specific weights. We accept that.

---

## Known risks, stated

1. **The Overpass renders are single-point-of-failure by nature.** They are in Backup 1 and
   nowhere else reproducible — the Overpass query that produced them is not replayable
   against 2026 data. Verified present at backup time: 130/130.
2. **The dated Geofabrik snapshots are treated as re-downloadable, which is only half true.**
   Geofabrik keeps a rolling window; `turkey-latest.osm.pbf` as of 2026-08-19 will not be
   retrievable indefinitely. The renders made *from* them are backed up, so this affects
   re-rendering from source, not any recorded number.
3. **iCloud Drive is a synced copy, not a backup** — a local deletion propagates to it. It is
   retained for convenience only. Kaggle is the independent copy: server-side, not
   sync-coupled to this machine.
4. **No public release.** The generator weights derive from GenCP's CC-BY 4.0 weights
   (redistributable with attribution), but the fine-tuning inputs were rendered from
   OpenStreetMap under ODbL, and whether ODbL's share-alike obligation reaches weights trained
   on ODbL-derived renders is unsettled. Private backup and direct institutional handover need
   no such decision; public release would.

---

## Verifying a backup

```bash
# backup 1
cd tubitak/data/evidence_backup && shasum -a 256 -c ../../docs/evidence-backup-manifest.txt
# backup 2 — Kaggle auto-extracts tars server-side, so archives appear as directories.
# Check all four prefixes explicitly: a zero exit code from `datasets create` has already
# once meant "two of four uploaded".
for f in checkpoints_C4 checkpoints_C5 checkpoints_C4_s43_modal generated_fakes; do
  echo -n "$f: "
  kaggle datasets files vedatyildirim/gencp-evidence-backup-2 --page-size 200 \
    | grep -c "^$f/" || echo 0
done
```

**Next review: at the next milestone, or whenever a new unregenerable artifact is produced.**
Standing practice 9 now requires every run to record its seed and its numerics-affecting
library versions, which should over time move artifacts out of the "unregenerable" column
entirely.
