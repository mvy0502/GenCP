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

Kaggle runs require the user's account (no CLI configured on this machine). The bundle under
`tubitak/kaggle/` contains the dataset packager and the ready-to-run notebook; evaluation (KARIOS,
matched comparison) runs locally on returned checkpoints.
