# Registration — warm-up de-confound: does the LR jump explain the two-epoch window without a discriminator?

Date: 2026-08-25, written and committed BEFORE the runs launch. Standing practice 4 governs:
no reading below is adjusted after any curve has been seen.

## The question, from corrections-log entry 26

Warm-up presence is perfectly collinear with discriminator presence. C1 and C4 carry a
2-epoch warm-up at lr 2e-5; C2 and C5 carry none. So the first two main-stage epochs are
exactly where the learning rate jumps 2e-5 → 1e-4, in precisely the two arms that rise and
neither of the two that do not. That window cannot separate "the adversarial term competes
with the reconstruction term" from "a 5× LR jump causes a transient".

## Design

Give C2 and C5 C1's exact warm-up schedule, at seed 43 on Modal, where the un-warmed
comparators already exist (seed43/C2, seed43/C5 on the gencp-out Volume, trained at
f2dc962).

- **Schedule mirrors C1 exactly**: stage 1 = 2 epochs at lr 2e-5 with `--lr_policy step
  --lr_decay_iters 50` (the phase-c-config.md fix that stopped warm-up epoch 2 running at
  lr 0), `--epoch_count 1`; stage 2 = `--lr 1e-4 --n_epochs 10 --n_epochs_decay 10
  --epoch_count 3`, default linear policy — main-stage epochs 3–20, i.e. 18 main epochs,
  20 total, matching C1's structure and the existing arms' totals.
- **Tags `C2_warmup` and `C5_warmup`** — outputs to `seed43/C2_warmup`, `seed43/C5_warmup`;
  nothing collides with seed43/C2 or seed43/C5.
- **One driver, two arms serial, C5_warmup first then C2_warmup** (longest and most
  load-bearing first, the same survival ordering as the seed block): 1 GPU container,
  ~2.9 h ≈ $3.2 at the $1.10/h constant.
- Everything else identical to every Modal arm: sorted enumeration (patch applied, ordered
  hash asserted), tar staging, TF32 off, seed hook, cold-start-D provenance file, C45-a
  sharp stop rule per stage.

## Code provenance, disclosed before the run

The arms exist at commit `a782aa5` (`WARMUP_COMMIT` in `gencp_modal.py`); the replication
arms never move off `f2dc962`. The `a782aa5` diff to `train_c1_c2.py` is
**membership-only**: the four ARM conditionals (L1 zero-patch, LPIPS zero-patch, `--LPIPS`
flag, warm-up branch) gain the new values, and the stage invocations, loss patches and
cold-D handling are shared verbatim with the existing arms — the schedule IS the
manipulation. One inherited difference, stated: the base script is the 96503b7 revision
(sha `878fa200…`), while the seed-43 comparators ran `839e1aad…` (f2dc962). That diff is
three `open()` → `with open()` conversions and nothing else (verified by reading it); no
schedule, loss or numeric path differs. This package reads curve shapes, not byte
equivalence, and the disclosure stands in place of an equivalence run.

## Registered readings — committed now, both branches written before any curve exists

**Quantity**: the per-epoch mean of the generator reconstruction loss as printed in
`loss_log.txt` — `G_L1` for C2_warmup, `G_LPIPS` for C5_warmup — with reference curves
from the existing seed-43 Modal loss logs (C1, C4: the risers; C2, C5: the non-risers).
"Main-stage epoch k" means the k-th epoch of that run's own main stage.

**PRIMARY — the window.** Rise = mean(main-stage epoch 2) > mean(main-stage epoch 1), the
same criterion as the coarse half of the stop rule ("rising over the first two main-stage
epochs").

- **IF C2_warmup and/or C5_warmup RISE** as C1 and C4 did: the window is explained by the
  LR jump alone, no discriminator required. Entry 26's revised argument is confirmed
  exactly as already written — the window is confounded; the sustained trend carries the
  claim. Nothing is withdrawn.
- **IF NEITHER RISES**: the rise requires the discriminator, and entry 26's revision was
  more conservative than it needed to be. The window becomes usable again and entry 26
  gains a paragraph saying so. Nothing is withdrawn.

**SECONDARY — the sustained trend.** The relative change from the first to the last
main-stage epoch mean, per arm. The un-warmed counterparts fall by roughly 8% over their
main stage. If C2_warmup and C5_warmup still fall by roughly that much, warm-up does not
touch the sustained trend — which is what the paper's claim actually rests on.

**The 18-vs-20 asymmetry, decided now and not revisited after the curves.** C2_warmup and
C5_warmup have 18 main-stage epochs (3–20, of which 8 at constant lr and 10 decaying);
the existing C2 and C5 have 20 (10 constant + 10 decaying). **Decision: state the
difference and read the SHAPE — each run's own main-stage window — rather than aligning
epoch indices or endpoints.** Reason: the warm-up variants inherit C1's LR ladder BY
DESIGN; that ladder is the manipulation, so no windowing can equalise the schedules
without deleting the thing being tested. The primary reading uses each run's own
main-stage epochs 1–2; the secondary uses each run's own first→last main-stage change,
with the epoch counts stated beside every number.

## What cannot be concluded

n = 1 seed. This is a **mechanism probe, not a confirmatory estimate**, and it is
reported as such wherever it appears. It cannot enter the Modal confirmatory block
(AMENDMENT SEED-c), touches no registered contrast, and its checkpoints are kept but not
scored through the chip-evaluation pipeline — the registered readings are the loss-curve
reads above and only those.
