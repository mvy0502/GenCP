# Corrections log

Every case where what was registered, claimed, or assumed diverged from what actually happened.
Kept in one place so the pattern is visible: the run is corrected or the record is corrected,
never neither. Companion to the withdrawn-claims list in [../README.md](../README.md).

The test applied throughout, stated once here:

> Would a reader who knew about this discrepancy interpret any result differently?

If no — correct the record, prominently, with the evidence. If yes, or if the discrepancy is
biased **toward** a registered prediction — correct the run. A bias against our own prediction
strengthens the result and may stand (disclosed); a bias toward it must be eliminated even when
probably immaterial, because "probably immaterial and pointing at our prediction" is exactly the
configuration a skeptical reader is entitled to reject.

| # | date | what was claimed/registered | what was actually true | resolution | where |
|---|---|---|---|---|---|
| 1 | 18 Aug | "We are 3× worse than upstream on KARIOS" | Compared two different quantities; on upstream's own statistic we are 4.5× better | claim withdrawn | [README](../README.md), [karios-validation.md](karios-validation.md) |
| 2 | 19 Aug | "11 gate chips fail with zero key points; water loss causes it" | Harness bug: references missing for 11 chips, errors silenced by `>/dev/null`; the chips were never evaluated | attribution withdrawn; harness fixed; erratum §6.1 | [renderer-tolerance.md](renderer-tolerance.md) |
| 3 | 19 Aug | Warm-up works because "D trains an order of magnitude faster than it damages G" at 2e-5 | pix2pix has a single `--lr`; the G/D ratio is unchanged. It works because D's task vs a near-fixed G is easy at any rate | justification replaced, config unchanged | [phase-c-config.md](phase-c-config.md) |
| 4 | 19 Aug | Phase C/D scene dates assumed interchangeable | Cappadocia has no usable 04-30 scene; four-week phenology deviation, direction of bias ambiguous | registered as confound before data prepared | [phase-cd-preparation.md](phase-cd-preparation.md) §3 |
| 5 | 19 Aug | "Warm-up = 2 epochs at 2e-5"; then, during triage: "both arms lose one trailing epoch identically — symmetric, therefore neutral" | Warm-up epoch 2 ran at lr = 0 (scheduler off-by-one with `n_epochs_decay=0`). The symmetry claim was **wrong**: main-stage losses are symmetric, but the dead warm-up epoch falls on C1 alone — widening C2's step-budget advantage from 11.9% to 14.7%, toward the registered R1 prediction | **run corrected**: C1 restarted with `--lr_policy step` (stage 1 only), 25-min partial run discarded before any result existed. Symmetric losses kept and disclosed (stock pix2pix behaviour) | [phase-c-config.md](phase-c-config.md) amendment |
| 6 | 19 Aug | Geofabrik chip extracts assumed equivalent to Overpass renders (first fix: a per-extract `strategy` config key) | osmium's default `simple` strategy drops boundary-crossing multipolygons (3:1 forest→background flow, worst chip 84% wrong); the config-key fix was a **no-op** — the key is silently ignored | `-s smart` on the command line; transparency gate re-run to 99.91% class agreement | [renderer-tolerance.md](renderer-tolerance.md) |
| 7 | 19 Aug | Kaggle mount failure "fixed by `dataset_sources` in kernel-metadata.json" | The attachment was never broken; the hard-coded path `/kaggle/input/gencp-tr` was wrong (private datasets can mount under `/kaggle/input/datasets/<owner>/<slug>`, and the layout differs per node) | mount discovery in `train_c1_c2.py`; both layouts observed across the C1/C2 nodes | [phase-c-config.md](phase-c-config.md) |
| 8 | 19 Aug | Kernel identity assumed = metadata `id` | `kernels push` derives the slug from the **title** and only warns; `status` on the requested id returns a permission error that reads like a privacy problem | ids derived from titles in `build_kernels.py` so they cannot disagree | [build_kernels.py](../kaggle/build_kernels.py) |
| 9 | 19 Aug | `torch.cuda.is_available()` accepted as proof the GPU is usable | True on a P100 (sm_60) that torch 2.10+cu128 cannot emit code for; every kernel launch would have failed after preflight passed | preflight asserts `sm_XX ∈ torch.cuda.get_arch_list()`; T4 pinned in metadata | [phase-c-config.md](phase-c-config.md) |
| 10 | 19 Aug | (record damage, disclosed) Phase B's `test_opt.txt` options record assumed safe during inference replication | `test.py` writes its options file into the checkpoints directory; the replication run overwrote the untracked original | disclosed; the original run's options survive in prose in geometry-finding.md §"saved options file" | this file |

Entry 5 is the only one so far where the run was corrected rather than the record. What forced
the restart was not magnitude (1.49% of C1's step budget, at the schedule's lowest rate, in a
stage whose purpose the D_real trace shows was already met inside epoch 1) but **direction**: the
initial let-it-run decision was made on the symmetry claim, and when that claim fell, the
criterion had to be re-applied rather than defended. The evidence that the warm-up's purpose was
met — D_real 0.307→0.156 across epoch 1, G_L1 flat at ~32-34, zero spike events against a 20-row
running median — is an empirical claim that the risk did not materialise, not a structural
guarantee, and the two must not be conflated when deciding whether a bias can stand.

## What would have caught each sooner

1. Reading KARIOS's own definition of `mean_x`/`mean_y` before comparing to it.
2. Not silencing stderr in a harness, ever; an assertion that every gate chip has a reference file.
3. Reading the optimizer construction (`optimizer_G`/`optimizer_D` share one `--lr`) before writing a rate-ratio justification.
4. Checking scene availability for all sites at registration time, not at preparation time.
5. Printing the effective LR per epoch in the training log (one line: `lambda_rule`'s output); any glance at it shows a zero. The symmetry claim would have been caught by writing the per-arm schedule out epoch by epoch — five minutes of arithmetic — before using it in a decision.
6. Byte-level comparison gates on ANY substituted data source, run before adoption (this is now the standing "transparency gate" pattern); reading osmium's docs on extract strategies rather than assuming config keys are honored.
7. Preflight from inside the running kernel (which is what caught it); sooner: never hard-coding a mount path the platform does not document as a contract.
8. Reading the CLI's slug-derivation warning as an error, not a suggestion.
9. A one-line CUDA smoke test (`torch.randn(2,2,device='cuda') @ ...`) in preflight instead of trusting `is_available()`; capability-vs-arch-list assertion now standard.
10. Copying any about-to-be-touched untracked file aside before running a tool that writes into its directory.
