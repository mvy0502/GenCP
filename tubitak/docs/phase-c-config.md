# Phase C training configuration — chosen and documented, not swept

## Data

- Pairs: `[satellite | OSM+CLC+ render]`, 514×257, corpus convention → train with
  **`--direction BtoA`** (input = right half = rendered map, target = left half = satellite),
  exactly as the corpus pairs are consumed.
- Four tiles, all from the fixed snapshots; **three of four scenes share one acquisition date
  (2026-04-30)**, and 36SXJ is excluded from training (it is a Phase D evaluation site). Training
  therefore has **zero phenological variation** — a stated methodological advantage the European
  corpus (5 UTM zones, unknown mixed dates) never had.
- Evaluation leakage: the 130 Phase B chips are excluded by set difference (verified per tile;
  they all lie in T36TVK, which contributes only its non-eval valid chips).

## Preprocessing — keep `load_size 286 / crop 256`

Matching how the released weights were trained. Reasoning on the record: this preserves
random-crop augmentation, which matters for a long fine-tune on ~5.7 k pairs, and we **measured**
the train/inference scale mismatch to be immaterial for matching (arm C vs arm B: paired
t = +0.59; `train-test-scale-mismatch.md`). Removing the mismatch is not worth losing augmentation
for. `--no_flip` stays default-off (flips are valid augmentation for overhead imagery).

## Discriminator cold-start — the chosen protocol

No discriminator was released, so C1 begins with a random D against a fully trained G — the known
unstable configuration. **Chosen protocol: low-LR joint warm-up.**

> Stage 1 (warm-up): 2 epochs at `lr 2e-5` — D trains an order of magnitude faster than it damages
> G at this rate; G barely moves while D reaches useful discrimination.

**Correction, 19 Aug 2026 (configuration unchanged, justification replaced).** The original
wording above claimed that at `2e-5` "D trains an order of magnitude faster than it damages G".
That is not the mechanism. pix2pix exposes a **single** `--lr`, used to build both
`optimizer_G` and `optimizer_D`, so stage 1 scales D and G by exactly the same factor and the
G/D rate *ratio* is unchanged from the default. The protocol still works, for a different
reason: D's problem against a near-fixed G is easy and converges within a few hundred
iterations regardless of the absolute rate, while the low rate bounds how far G can be dragged
by a still-meaningless adversarial gradient in the meantime.

Recorded rather than quietly fixed, because a protocol that works for a reason we did not
understand is one we cannot adapt if it fails. If stage 1 turns out to be too short, the
lever is **epochs**, not `--lr`, and a genuine G/D rate split would require touching the
training loop, which this project does not do.

**AMENDMENT, 19 Aug 2026 ~12:47 UTC (stage-1 schedule corrected; one 25-minute run discarded).**
The first C1 run (Kaggle kernel version 2, launched 12:16:59 UTC) revealed that warm-up epoch 2
executed at **learning rate exactly 0**. Mechanism, confirmed against the code: `train.py` calls
`model.update_learning_rate()` at the **start** of every epoch, and the default `linear` policy's
`lambda_rule` is `1 - max(0, k + epoch_count - n_epochs)/(n_epochs_decay + 1)`; with
`n_epochs_decay=0` the denominator is 1, so the second step lands on zero. Half the registered
warm-up was dead. The lr log lines prove it: `0.0000200 -> 0.0000200` (epoch 1),
`0.0000200 -> 0.0000000` (epoch 2).

The same off-by-one costs **each main stage** its last flat epoch and terminates it on one lr=0
epoch — but that loss is **symmetric across arms** (upstream pix2pix behaviour; stock training
runs epoch 200/200 at lr 0 too) and is **accepted and disclosed, not corrected**. The dead
warm-up epoch is different: C1 has two stages and takes the termination twice, so the anomaly
falls on C1 alone, widening C2's summed-LR advantage from the designed 11.9% to 14.7% —
**in the direction of the registered R1 prediction (C2 wins)**. A bias against the prediction
would have been left standing as conservative; a bias toward it has to be removed. Decision
criterion and restart decision recorded in the corrections log
([corrections-log.md](corrections-log.md), entry 5).

Fix: stage 1 (and only stage 1) now runs with `--lr_policy step --lr_decay_iters 50` — stock CLI
flags; `StepLR(step_size=50)` cannot trigger inside a 2-epoch stage, so 2e-5 holds constant across
both warm-up epochs. Stage 2 and C2 keep the default linear policy and their symmetric losses.
The version-2 run was superseded at epoch 7/20 with **no C1 result in existence**; its partial
checkpoints are discarded. Restart verified live (kernel version 3): `0.0000200 -> 0.0000200`
at the start of **both** warm-up epochs.

Effective epochs after the fix: C1 = 2 warm-up + 17 main (epoch 20 at lr 0); C2 = 19 main
(epoch 20 at lr 0). The registration's original text above stands unedited.
> Stage 2 (main): continue at `lr 1e-4` (half the repo default — fine-tune regime), 8 epochs flat
> + 10 epochs linear decay.

Chosen over a frozen-G D-only phase because it needs no training-loop surgery (two stock CLI
invocations with `--continue_train`), and the effective outcome is the same: D catches up before G
receives large adversarial gradients. **Stop rule:** if G degrades early despite the warm-up
(L1 term rising over the first two main-stage epochs), the run stops and reports its curves —
no rescue by improvisation.

## Arms

| arm | loss | notes |
|---|---|---|
| C1 | GAN + L1 (repo defaults: lsgan, λ_L1 = 100) | warm-up protocol above |
| C2 | **L1 only** | 3-line patch applied to the *Kaggle copy* of the repo (zeroes the GAN term in G's loss); local pipeline files untouched; no warm-up needed (no adversarial gradient) |
| C3 | winner + ~20 % EU corpus pairs | sequential, after the C1/C2 verdict |

Batch 4, Adam β1 0.5 (defaults), `--norm batch`, `--netG unet_256`, seed 42, initialised from the
released `latest_net_G.pth`. Checkpoints saved every epoch to Kaggle persistent output so a
dropped session loses at most one epoch.

## Execution note

Kaggle runs require the user's account. The bundle under `tubitak/kaggle/` contains the dataset
packager, the CLI bootstrap, the kernel builder and the run script; evaluation (KARIOS, matched
comparison) runs locally on returned checkpoints.

| file | role |
|---|---|
| `prepare_dataset.sh` | packages `kaggle_gencp_tr.zip` |
| `dataset-metadata.json` | dataset id `vedatyildirim/gencp-tr`, for `kaggle datasets version` |
| `setup_kaggle_cli.sh` | Kaggle client in its own venv at `~/.venvs/kaggle`, token at `~/.kaggle/kaggle.json` mode 600 |
| `build_kernels.py` | generates the C1 and C2 kernel folders from the single run script |
| `train_c1_c2.py` | the run script itself |

Dataset: `vedatyildirim/gencp-tr`, private, Version 1, 2.04 GB, 6778 files, uploaded 19 Aug 2026.
Kaggle auto-extracts the uploaded zip, so it mounts as `/kaggle/input/gencp-tr/{pairs,eu_pairs,latest_net_G.pth}`.
Licence is recorded as `unknown`, which is correct while the dataset is private; **if it is ever
made public the licensing needs a real decision**, because it mixes OSM derivatives (ODbL, with
share-alike implications), Sentinel-2 (Copernicus open) and the GenCP weights (CC-BY 4.0).

## Kaggle bring-up: four things the plan did not survive contact with

Found 19 Aug 2026 by reading `train_c1_c2.py` against the fork at `f9d4952`. All four were
resolved on the Kaggle side; **no upstream file was touched and no hyperparameter changed.**

**1. `/kaggle/input` is built from attachments, not from account contents.** The first run failed
with `FileNotFoundError: '/kaggle/input/gencp-tr'` even though the dataset existed and its slug was
correct. Kaggle mounts only the data sources explicitly attached to *that notebook*. Fixed by
`dataset_sources` in `kernel-metadata.json`, and re-checked from inside the kernel by `preflight()`.

**2. `--seed 42` is not an option in this fork.** There is no `--seed` anywhere in `options/`, and
`BaseOptions.gather_options()` ends in `parser.parse_args()` (strict), so argparse would have
exited 2 on the first invocation of both arms. The seed was **not** dropped: `install_seed_hook()`
writes a `sitecustomize.py` onto the training subprocess's `PYTHONPATH`, which seeds
`random`/`numpy`/`torch` before `train.py` constructs anything, and prints a line proving it fired.

**3. `--continue_train` demands a discriminator checkpoint.** This falsifies the claim above that
the protocol "needs no training-loop surgery (two stock CLI invocations with `--continue_train`)".
`base_model.setup()` calls `load_networks('latest')` whenever `continue_train` is set;
`load_networks` iterates `model_names = ['G','D']` and calls `torch.load()` with no existence
check. Only `latest_net_G.pth` was ever released, so both arms would have died on
`latest_net_D.pth` before iteration 1. The CLI invocations are still stock; what was missing was a
**file**, not a code path.

Resolved by `make_cold_start_D()`, which builds D through the repository's own
`define_D -> init_net -> init_weights` path with the framework's own scheme, so it starts in the
distribution the training loop expects rather than introducing a second unknown on top of the
cold start:

```
define_D(input_nc=6, ndf=64, netD='basic', n_layers_D=3, norm='batch',
         init_type='normal', init_gain=0.02, gpu_ids=[0])     seeded with 42
```

Its provenance is written to `checkpoints/<ARM>/DISCRIMINATOR_PROVENANCE.txt` (seed, init scheme,
architecture, parameter count, sha256, creation date) and printed in full before every training
invocation that uses it. **A file named `latest_net_D.pth` sitting in a checkpoints directory looks
exactly like a released discriminator. It is not one, and the record must make that impossible to
misread.**

**4. `--print_freq` default 100 hides the signal the stop rule watches.** At 5577 pairs and batch 4
there are 1394 iterations per epoch, so the default yields 3 or 4 rows over the first few hundred
iterations. The stop rule's coarse half (L1 rising over the first two main-stage epochs) survives
that; its sharp half (a generator-loss spike in the first few hundred iterations, the actual
cold-D signature) does not. Set to `--print_freq 10`. Logging only, no effect on optimisation.

**Also noted, not blocking.** `models/pix2pix_model.py` imports `torchmetrics` at module level and
constructs `LearnedPerceptualImagePatchSimilarity(...).cuda()` in `__init__` **unconditionally**,
not only under `--LPIPS`, and `torchmetrics` is not in `requirements.txt`. This corrects the
project note that the LPIPS `.cuda()` "bites only during training with `--LPIPS`": it bites on any
CPU training run. On Kaggle it is harmless but it makes internet access mandatory (the VGG weights
are downloaded), and the run script checks the import and installs with `--no-deps` if needed.

## Sizing

20 epochs per arm (C1 = 2 warm-up + 18 main; C2 = 20), 1394 iterations per epoch, about 27,900
iterations per arm, roughly 2-3 h on a P100 and well inside the 12 h session cap. `--save_epoch_freq 1`
writes about 229 MB per epoch (G 218 MB + D 11 MB), roughly 4.6 GB per arm against the 20 GB
`/kaggle/working` budget, so the arms run in **separate sessions**.
