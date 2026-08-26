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

> **Status 2026-08-27: VERIFIED COMPLETE — counted, not merely seen.** Kaggle reports
> **13,732,977,835 bytes**. The 2026-08-26 check below established only that each archive
> was **present**; a half-uploaded tar extracts to a prefix that reads present exactly like
> a whole one. The listing has now been enumerated in full — **375 pages, 74,867 entries,
> no early exit, nothing unmatched** — and every archive matches its local tar exactly:
>
> | archive | local members | server entries | match | real payload |
> |---|---|---|---|---|
> | `checkpoints_C4/` | 2,108 | 2,108 | **yes** | 1,029 files (+50 dirs) |
> | `checkpoints_C5/` | 2,108 | 2,108 | **yes** | 1,029 files (+50 dirs) |
> | `checkpoints_C4_s43_modal/` | 7 | 7 | **yes** | 2 files (+3 dirs) |
> | `generated_fakes/` | 70,644 | 70,644 | **yes** | 35,322 `*_fake.png` |
>
> Run with `verify_kaggle_backup.py --full`. Kaggle lists **files only, never directories**
> — confirmed by the match, since the local side counts non-directory members.
>
> Verified with `tubitak/tests/verify_kaggle_backup.py`, **not** by trusting an exit code.
> The failures along the way are recorded because they are the procedure's real hazards:
>
> 1. **`kaggle datasets create` uploaded two of four archives and exited 0** — no error, and
>    no "Starting upload" line for the two it skipped. **A zero exit code from this tool
>    does not mean the upload completed.** A `datasets version` push with the same folder
>    then sent all four.
> 2. **A single page of `kaggle datasets files` proves nothing.** `checkpoints_C4` alone
>    fills many pages, so the other three read as absent whether they are there or not. The
>    check must page, and must match `prefix/` exactly so `checkpoints_C4` is not satisfied
>    by `checkpoints_C4_s43_modal`.
> 3. **Enumerating the whole listing risks a 429.** The fast mode stops as soon as every
>    prefix has been seen; `--full` pauses 2.5 s between pages and backs off on 429. The
>    full 375-page walk drew no 429 at that pace. It *did* die once on a bare
>    `ConnectionResetError` — a walk this long outlives the connection, and a handler that
>    catches only 429 loses the whole run to it. `--full` now retries any transport error
>    on the same page token.
> 4. **macOS `tar -tf` undercounts these archives by half, and that nearly produced a wrong
>    answer here.** macOS ships libarchive, whose reader silently merges an AppleDouble
>    `._x` member back into `x` as extended attributes, so `tar -tf` never prints them.
>    Kaggle extracts on Linux, which has no such reader, so **every `._` member becomes a
>    real file in the dataset** — one per real entry, directories included. The first
>    comparison used `tar -tf`, expected ~37 k entries, and read the perfectly healthy
>    74,867-entry listing as an endless pagination loop. The local side must be counted
>    with Python's `tarfile`, which merges nothing. **This also corrects the 2026-08-26 note
>    above, which put `checkpoints_C4` at 1,079 entries: that was the macOS-merged figure
>    (1,029 files + 50 dirs). The true stored count is 2,108.**
>
> The AppleDouble members are inert metadata, not corruption — the payload is intact and
> the `real payload` column is the number that matters. They cost roughly nothing in bytes.
> Future archives should be created with `COPYFILE_DISABLE=1` to avoid them.
>
> Kaggle reports `total_bytes = 0` until it has finished extracting the tars server-side —
> here for roughly three hours. **Size 0 means "still processing", not "empty".**

| item | size | why |
|---|---|---|
| `checkpoints_C4.tar` | 4.7 GB | **base C4 arm** — a cell of the 2×2 design we report directly. 21 per-epoch `net_G` |
| `checkpoints_C5.tar` | 4.7 GB | **base C5 arm** — the other reported cell. 21 per-epoch `net_G` |
| `evidence_inputs_corpora.tar.gz` | 129 MB | **the 130 Ankara Overpass renders, second copy.** Added 2026-08-27 so the project's least replaceable artifact is no longer in one place only. Same file as in Backup 1 |
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

1. **The Overpass renders were single-point-of-failure. RESOLVED 2026-08-27 — they are now
   in both backups.** They remain nowhere else reproducible: the Overpass query that
   produced them is not replayable against 2026 data, so the exposure was real and the
   asset is the least replaceable in the project while being one of the smallest (129 MB).
   `evidence_inputs_corpora.tar.gz` has been copied into Backup 2 as well, and verified
   there by enumeration rather than by an exit code:

   | | local tar | server-side | match |
   |---|---|---|---|
   | `evidence_inputs_corpora/` total file members | 3,739 | 3,739 | **yes** |
   | of which Ankara `run/inputs/*.png` — the renders themselves | **130** | **130** | **yes** |

   Counted with Python's `tarfile` on the local side, never macOS `tar -tf`, for the reason
   in hazard 4 above: 1,968 of those 3,739 members are AppleDouble `._` files that
   libarchive silently merges away and Kaggle's Linux extractor materialises as real files.
   Read at 2 s between pages, 41 pages, no 429.

   Kaggle still reported `total_bytes = 0` at verification time; per the note above that
   means "still extracting", not "empty", and the file listing is the reliable check.
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
# The kaggle module is NOT in the `gencp` env; use the miniforge base interpreter.
PY=/opt/homebrew/Caskroom/miniforge/base/bin/python

# presence only — fast, catches a wholly missing archive, ~22 pages
$PY tubitak/tests/verify_kaggle_backup.py

# completeness — counts every server entry and diffs it against the local tars.
# 375 pages at 2.5 s apart, so budget ~30 min. This is the only mode that can say
# "complete"; the fast mode can only say "present".
$PY tubitak/tests/verify_kaggle_backup.py --full
```

**Do not count the local side with `tar -tf` on macOS.** libarchive merges AppleDouble
`._x` members into `x` and never prints them, so `tar -tf` reports roughly half the
entries Kaggle actually stores. `--full` counts with Python's `tarfile`, which merges
nothing. Kaggle lists **files only, not directories**.

**Next review: at the next milestone, or whenever a new unregenerable artifact is produced.**
Standing practice 9 now requires every run to record its seed and its numerics-affecting
library versions, which should over time move artifacts out of the "unregenerable" column
entirely.
