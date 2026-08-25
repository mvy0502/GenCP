# Hardware gate results — seed 43 on Modal A10G vs Kaggle T4

Date: 2026-08-25. Registration: [seed-replication-registration.md](seed-replication-registration.md)
AMENDMENT SEED-b (acceptance rule committed before any run). Evaluation code frozen at
`48ced64` (sha256 table in the registration); every number below was produced by that code on
the registered local machine. Raw layers: `tool_runs/C45_s43_modal/` and
`tool_runs/C45_s43_modal_unsorted/` (untracked, sha256-pinned below), plus the committed
Kaggle `C45_s43/`, `C45_s44/`.

## Verdict under the registered rule, stated first

**NOT POOLED.** The registered acceptance rule reads: pool only if EVERY Modal-vs-Kaggle
difference at seed 43 is smaller than the corresponding s43-to-s44 spread. Ten of eleven
quantities pass; **edge_C1 fails** (|Modal−Kaggle| = 0.0177 against a seed spread of 0.0042,
4.2×). Under the pre-written second branch, **Modal runs are analysed as their own
homogeneous block and compared to the Kaggle block, never pooled; seed counts are reported
per block.** Both branches were committed before the gate ran; this is the branch the number
selected, not a judgment made after seeing it.

### Interpretation, beside the verdict, not instead of it

The failing quantity is the mechanism metric, and the difference is scientifically
immaterial: edge_C1 1.0827 vs 1.0650 is **1.6% relative**, and the arm ordering is untouched
on both platforms (C2 0.28 < pretrained 1.02 < C1 1.07 < C4 1.12 < C5 1.15). Why the rule
fired anyway: the edge ratio's seed-to-seed spread is **0.0042 — an order of magnitude
tighter than the positional quantities' 0.0232–0.0745**. A hardware difference of the same
absolute size clears every positional bar comfortably and fails the edge bar. **The rule
caught the tightness of the reference scale, not a material hardware effect.** The four
registered residual contrasts and the interaction sit at 27–92% of their spreads. All of
this is interpretation; the verdict above is not conditioned on any of it.

### A specification flaw in the rule, recorded and not repaired

The acceptance rule was written as a **single global verdict** while scaling each quantity
to **its own spread**. The consequence, visible now: the most reproducibly-measured quantity
governs the whole package — the tighter a quantity's seed spread, the lower its bar for
failing the gate, and one such quantity vetoes ten. A per-quantity verdict would have been
the better specification. **This flaw was noticed only after seeing which quantity failed —
precisely the moment at which fixing it is forbidden**: refining the rule now would be
indistinguishable from adjusting a gate to pass. So the flaw is recorded, the post-hoc
timing of noticing it is recorded, and **the verdict stands unchanged under the rule as
written.** For the future, registered in
[seed-replication-registration.md](seed-replication-registration.md): gates of this shape
return a verdict **per quantity**, not one for the package.

### The provenance gap is not connected to the failure

The failing quantity is edge_C1, and **C1 is the arm whose preflight block was fully
captured** — image id, environment, pip freeze, ordered-list hash, patched-file hash, all of
it. The arm with the provenance gap, C2, passes its quantities (edge 0.0015 vs spread
0.0064; arm mean inside spread). The gap and the failure touch different arms; a reader
should not link them.

## Four-arm results against the Kaggle values

Per-quantity: Kaggle T4 seed 43 (registration table, reproduced exactly from `C45_s43/`),
Modal A10G seed 43, the absolute difference, and the s43-to-s44 Kaggle seed spread that is
the registered yardstick.

| quantity | Kaggle s43 | Modal s43 | \|Modal−Kaggle\| | s43↔s44 spread | within spread? |
|---|---|---|---|---|---|
| C5−C4 (primary) | −0.5485 | −0.5292 | 0.0193 | 0.0362 | yes |
| C1−C2 | +0.6636 | +0.6473 | 0.0163 | 0.0232 | yes |
| C4−C5 | +0.5485 | +0.5292 | 0.0193 | 0.0362 | yes |
| C5−C2 | +0.1275 | +0.1086 | 0.0189 | 0.0745 | yes |
| I_raw | −0.1151 | −0.1181 | 0.0030 | 0.0594 | yes |
| edge mean pretrained | 1.0208 | 1.0208 | 0.0000 | 0.0000 | identical by construction¹ |
| edge mean C1 | 1.0827 | 1.0650 | **0.0177** | **0.0042** | **NO — 4.2×** |
| edge mean C2 | 0.2788 | 0.2803 | 0.0015 | 0.0064 | yes |
| edge mean C4 | 1.1206 | 1.1207 | 0.0001 | 0.0018 | yes |
| edge mean C5 | 1.1541 | 1.1584 | 0.0043 | 0.0100 | yes |

¹ Pretrained is training-independent: both sides read the same pkgA grays and B1 per-chip
values, so 0 = 0 carries no information about hardware and is excluded from the rule.

Every registered sign survives on Modal: C5−C4 negative, C1−C2 / C4−C5 / C5−C2 positive,
I_raw negative, C2's edge mean far below 0.5, C5's edge mean highest.

## C2 sorted vs unsorted — the order effect, beside the seed spread

Both arms trained tonight's pinned commit on Modal A10G at seed 43; the only difference is
`image_folder_sorted.patch` applied (sorted) or not (raw ext4 enumeration).

| quantity | C2 sorted | C2 unsorted | \|diff\| | s43↔s44 seed spread | larger |
|---|---|---|---|---|---|
| residual arm mean (C2_med over 130 chips) | 1.3699 | 1.3911 | 0.0212 | 0.0309 | **seed spread** |
| edge-ratio mean | 0.2803 | 0.2793 | 0.0010 | 0.0064 | **seed spread** |

The order effect is smaller than the seed-to-seed spread on both quantities (residual
0.0212 < 0.0309, edge 0.0010 < 0.0064; the residual difference is also within its own
per-chip paired SE of 0.0334, n=130). Per the registered reading: **the gate's
interpretation is clean whatever Kaggle's enumeration order was**, and the paper carries
these numbers instead of a "we cannot know".

## Checkpoint identity — five arms, latest_net_G.pth only

`gencp_modal.py::verify_latest` ran on the output Volume, where both files live: every arm's
`latest_net_G.pth` is tensor-equal to its `20_net_G.pth`, and every Modal-side sha256
matches the locally downloaded file byte-for-byte.

| arm | latest_net_G.pth sha256 (Modal-side = local) |
|---|---|
| C1 | `7b753e541ee5a7ffabd30b9cbb68d1fa1c278080ec9e32edaeb5731f14571d01` |
| C2 | `1ea1255d61400854ae7eb216689fa543140ec7950637be0394a99f97b78f6938` |
| C4 | `f46b3e356aaab0bf280f339a15f3e7a7ae869fb6234c4c91cd1260120fe15842` |
| C5 | `adae3edefdde1d633b790339fade6101b7516557b685922eed94666013ab28cf` |
| C2_unsorted | `cfbe50fb3ca51b271beb78dd3d12adf66cbc7df6cc1241c520f0a0f2997317ef` |

Evaluation outputs (frozen code, 130 chips each, zero skipped):
`C45_s43_modal/C45_per_chip.csv` `8e1db40d9a015eb3df74e4c46207de3960dd70adbe923e86b9a341990dac0eb9`,
`C45_s43_modal/C45_edge_ratio.csv` `ad1e1cdf18e75e19461e7b7f3714b175506be45fef67a101b06ca29cec4a917c`,
`C45_s43_modal_unsorted/C45_per_chip.csv` `40140b74c68c3ee5273780a11806749a7cba090ea6f89cc6ac1f159fa85f2c26`,
`C45_s43_modal_unsorted/C45_edge_ratio.csv` `76e2b4bceea78a135f202dd0beb111c5572d4461efcdc9a3ad28c9efc53dbd9d`.

## Ordered-list hashes, patched-file sha256, and per-arm provenance

What each arm's container verifiably read and ran. CAPTURED = present in a retained log or a
driver-returned record; ASSERTED = the run could not have trained unless the in-code
assertion held (constants confirmed in `gencp_modal.py` at f2dc962:
`EXPECTED_ORDER_SHA256 = 4b5f2320…`, `EXPECTED_N_FILES = 5577`,
`EXPECTED_VGG_SHA256 = 397923af…`); INFERRED = follows from measured git history, not from
any record of the run itself.

| arm | ordered-list sha256 (n) | image_folder.py sha256 | VGG sha256 | image | commit / train-script sha |
|---|---|---|---|---|---|
| C1 | `4b5f2320…cad9` (5,577) — CAPTURED | `fef294b8…0a34` (patched) — CAPTURED | n/a (L1 arm; pre-bake image) | `im-a6ofKzN2gTc7VqJ4SNdJvk` — CAPTURED | commit not captured (pre-pin); train script `839e1aad…` INFERRED² |
| C2 | **not captured, not provably asserted** — see the gap below | not captured | n/a (L1 arm) | not captured | commit not captured; train script `839e1aad…` INFERRED² |
| C4 | `4b5f2320…cad9` (5,577) — ASSERTED (f2dc962 code) | `fef294b8…0a34` — CAPTURED | `397923af…5bf0` — CAPTURED (+ baked-image build check captured) | `im-CRd9BvZz8XvhZ4P73wkOWe` — CAPTURED | commit not captured (pre-pin); train script `839e1aad…` INFERRED² |
| C5 | `4b5f2320…cad9` (5,577) — ASSERTED | `fef294b8…0a34` — ASSERTED (git-apply against pinned pre-state) | `397923af…5bf0` — ASSERTED | same app image as C4 — CAPTURED at app level | commit not captured (pre-pin); train script `839e1aad…` INFERRED² |
| C2_unsorted | `f28d5215…9d2c` (5,577) — CAPTURED (driver-returned; raw ext4 order, not asserted BY DESIGN — it measures "an unsorted order") | `f47c3b60…b008` (UNPATCHED) — CAPTURED, byte-equal to `git show f2dc962:data/image_folder.py` | `397923af…5bf0` — ASSERTED | f2dc962-defined image (cached) | **pinned f2dc962 — checkout asserted in code**; train script `839e1aad…` |

² The train-script inference, measured not assumed: `tubitak/kaggle/train_c1_c2.py` hashes
to `839e1aad…` at EVERY commit from ea7d1f9 (10:43) through f2dc962 (13:40) — ea7d1f9,
cd2966c, 3622132, 4817b90, 6440f77, ed7245a, f2dc962 all verified — and first changes at
96503b7 (19:16). Every morning/afternoon container cloned within that window, so whichever
commit each bare branch clone took, the training script was byte-identical. This is exactly
the argument the f2dc962 pin exists to make unnecessary from now on.

The surviving raw evidence is committed beside the gate logs:
[gates/modal-seed43-C1-container.log](gates/modal-seed43-C1-container.log) (C1's full
container stream) and
[gates/modal-seed43-preflight-recovered.log](gates/modal-seed43-preflight-recovered.log)
(C4/C5 fragments, C2_unsorted driver record). The laptop-side captures these were recovered
from live in a session tmp directory and would not have survived a cleanup.

C1's full environment block is CAPTURED (gate3 stream): Python 3.12.13, torch 2.10.0+cu128
(CUDA 12.8, cudnn 91002), torchvision 0.25.0+cu128, torchmetrics 1.9.0, numpy 2.0.2, Pillow
11.3.0, scipy 1.16.3, pip freeze of all 52 packages, A10 smoke test passed, TF32 off,
pretrained initialisation `5938…a022` verified after staging, preflight stamp
`arm=C1 seed=43 utc=2026-08-25T08:45:55Z`, training pairs 5,577.

### The C2 provenance gap, stated rather than papered over

**C2 (sorted) has NO captured preflight record.** The laptop-side capture died at 12:06
during C1's run (the same client-disconnect that later hit C5), C2 trained after it, and
Modal's log retention has since discarded the container output. Not captured: its
environment block, image id, ordered-list hash print, patched-file print, preflight stamp —
and, unlike C4/C5, the ordered-list hash cannot be recovered by the ASSERTED route either,
because the assert was added at 6440f77 (11:58) and it cannot be established which driver
version C2's container ran under (the driver is mounted from the laptop's working copy at
app launch, which pre-pin sat between commits). What C2 still has: its checkpoint on the
Volume with `verify_latest` passing (latest tensor-equal to epoch 20, sha256 above), the
count guard (present from 4817b90) as a partial screen, the train-script window argument²,
and results coherent with every sibling. **One of the four gate arms therefore has no
captured record of what it read at training time. This is the class of gap the rest of this
package spent the day closing, present in the gate's own arms, and it is recorded here
before the verdict rather than discovered after.** C5 is only one step better: its
preflight survives as an unattributed fragment plus the task-level cost line; its hashes
rest on the f2dc962 asserts. C4 is partial (patch and VGG captured, environment lost).

## Throughput

Wall-clock GPU-seconds where captured; loss-log per-image times are the training loop's own
prints (async-sampled, indicative — they under/over-state true wall time).

| arm | wall (captured) | loss-log time/img | data/img |
|---|---|---|---|
| C1 | not captured | 0.0285 s (~35 img/s) | 0.0034 s |
| C2 | not captured | 0.0282 s (~35 img/s) | 0.0034 s |
| C4 | 6,647 s (1.85 h) | 0.0744 s (~13 img/s) | 0.0038 s |
| C5 | 7,770 s (2.16 h) | 0.0841 s (~12 img/s) | 0.0038 s |
| C2_unsorted | 1,517 s (0.42 h) | 0.0204 s (~49 img/s) | 0.0055 s |

Data-loading held at ~0.003–0.006 s/img on every arm — the Kaggle-steady value; the
0.120–0.491 s/img Volume stall AMENDMENT SEED-b records did not recur, i.e. the tar-staging
fix held across all five runs. C2_unsorted's per-image compute (0.0204 s) differs from
sorted C2's (0.0282 s) by ~28% on the same nominal GPU class — host-to-host variance,
disclosed; evaluation is local and unaffected.

## Credit accounting

| item | GPU-seconds | est. cost |
|---|---|---|
| balance through C5 (dashboard reading, 25 Aug ~19:58) | — | $8.79 of $30 |
| C2_unsorted (driver-computed, A10G @ $1.10/h) | 1,517 | $0.46 |
| verify_latest ×2, volume ops, log fetches (CPU) | — | ~$0.05 |
| **estimated standing** | | **~$9.30 of $30** |

The authoritative figure is the Modal dashboard; the driver-computed arm costs are the
per-run records ([cost] lines / returned `usd`). Remaining budget comfortably covers the
seed-44 Modal replication if the no-pooling branch makes one wanted.

## What happened tonight, in one paragraph

The seed-42 reproduction gate was re-run at HEAD before anything else and passed exactly
(all 17 columns max|diff| 0.0; `C45_per_chip.csv` byte-identical to the original gate run).
C2_unsorted was launched through the driver at the pinned f2dc962 — the same commit whose
training script every sibling ran — completed in 0.42 h, and was evaluated locally by the
frozen code, as were the four sorted arms from latest-only downloads verified Modal-side.
The gate verdict is the registered no-pooling branch on account of edge_C1; the order effect
is below seed noise on both registered quantities. corrections-log entry 29 (sixth instance)
records the 19:16–19:51 exposure window during which a bare branch clone would have given
C2_unsorted a different training script, closed by the pin only after the exposure existed.
