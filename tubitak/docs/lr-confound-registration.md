# Registration — the learning-rate confound at the positional outcome

**Registered 2026-08-26, BEFORE any warm-up checkpoint is downloaded or scored through the
chip pipeline.** No positional number for `C2_warmup` or `C5_warmup` exists anywhere at the
time of writing: the warm-up de-confound package
([warmup-deconfound-registration.md](warmup-deconfound-registration.md)) deliberately excluded
these checkpoints from the chip-evaluation pipeline, and that exclusion has held. **The only
`C2_warmup` / `C5_warmup` numbers in existence are loss-curve reads**
([warmup-deconfound-results.md](warmup-deconfound-results.md)); nothing positional has been
looked at. Standing practice 4 governs; standing practice 10 governs the artifacts.

## The confound, stated with its arithmetic

The adversarial arms and the non-adversarial arms **do not receive the same amount of
training on the reconstruction objective.**

| arm | schedule | integrated LR (units of 1e-4 × epochs) |
|---|---|---|
| **C1, C4** | 2 warm-up epochs at 2e-5, then 18 main epochs (`epoch_count 3`, `n_epochs 10`, `n_epochs_decay 10`) → 8 at full LR + 10 decaying | **13.40** (0.40 warm-up + 13.00 main) |
| **C2, C5** | 20 main epochs (`epoch_count 1`, same policy) → 10 at full LR + 10 decaying | **15.00** |
| **C2_warmup, C5_warmup** | C1's ladder mirrored exactly | **13.40** |

Computed from pix2pix's own `lambda_rule`
(`lr_l = 1 − max(0, epoch + epoch_count − n_epochs) / (n_epochs_decay + 1)`), summed over each
arm's epochs. **The adversarial arms receive 1.60 less, a deficit of 10.67%**, and the deficit
runs **in the direction of the headline result**: the arms that get less cumulative learning
rate are the arms that score worse.

**So "adversarial ON" and "trained ~11% less on the reconstruction objective" are currently
the same variable.** This is a second collinearity in the same design as the warm-up
confound — and it is the more dangerous one, because the warm-up de-confound tested only the
loss curves. That test was scoped to curves by instruction, which protected the registered
contrasts and left the confound untested **at the outcome the paper's claim is made on.**

## Which contrasts are confounded, derived before any number is seen

This falls straight out of the table above and is recorded now, because it determines what
each branch costs.

| contrast | integrated LR | status |
|---|---|---|
| **PRIMARY C5 − C4** | 15.00 vs 13.40 | **CONFOUNDED** |
| main effect C1 − C2 | 13.40 vs 15.00 | **CONFOUNDED** |
| main effect C4 − C5 | 13.40 vs 15.00 | **CONFOUNDED** |
| **SECONDARY C5 − C2** | 15.00 vs 15.00 | **CLEAN — identical integrated LR** |
| C4 − C1 (unregistered) | 13.40 vs 13.40 | **CLEAN — identical integrated LR** |
| edge-ratio mechanism (four arms) | mixed | partly confounded |

**The secondary is structurally immune.** C5 and C2 are both un-warmed 20-epoch arms and
receive exactly the same integrated learning rate, so **no outcome of this probe can touch
C5 − C2** — the contrast that fired 6/6, that carries the LPIPS-alone penalty, and whose
registered consequence controls the title. That is stated here, before scoring, so it cannot
later look like a consolation found after a bad result.

## The design

No training. The checkpoints exist on the `gencp-out` Volume at `seed43/C2_warmup/` and
`seed43/C5_warmup/`, trained at `a782aa5` with C1's exact ladder, and their un-warmed
counterparts `seed43/C2` and `seed43/C5` are already scored
([hardware-gate-results.md](hardware-gate-results.md), `C45_s43_modal/`). **Volume read plus
local scoring only; zero GPU training.**

**Scored through the frozen pipeline, unchanged.** `seed_eval_run.py` (commit `6418febc`,
frozen) carries `--variant` and `--arms` flags documented in its own source as **"ROUTING
ONLY … numeric logic unchanged"**. The run is:

```
seed_eval_run.py --seed 43 --variant modalwarmup --arms C2,C5
```

reading `tubitak/outputs/c{2,5}_checkpoints_s43_modalwarmup/checkpoints/` and writing
`tubitak/data/tool_runs/C45_s43_modalwarmup/`. **No frozen file is edited.**

**One routing rename, disclosed in advance.** The Volume stores these arms as
`seed43/C2_warmup/C2_warmup/latest_net_G.pth`; the runner expects
`c2_checkpoints_s43_modalwarmup/checkpoints/C2/latest_net_G.pth`. The checkpoint file is
**copied, not modified**, and its sha256 is recorded on both sides and must match. The rename
is of directories only, so that the frozen runner's arm routing resolves; **it does not make
the warm-up arm into arm C2**, and every reported number names the arm as `C2_warmup`.

Same 130 Ankara chips, same warps, same KARIOS configuration, same estimator as every other
arm in the block. `verify_latest`-equivalent check applied: `latest_net_G.pth` must be
tensor-equal to `20_net_G.pth` before scoring.

## REGISTERED READINGS — committed before any positional number exists

**Quantity.** Per-arm mean over the 130 chips of the per-chip median KARIOS residual, in px —
the same statistic as every other positional number in this package. Comparisons are **paired
per-chip differences** with SE = sd/√130.

**Movement**, per family, with the sign fixed so that positive = toward the adversarial arm
(worse):

- **Δ_L1 = mean(C2_warmup) − mean(C2)**, against the L1-family adversarial gap
  **D_L1 = mean(C1) − mean(C2)**.
- **Δ_LPIPS = mean(C5_warmup) − mean(C5)**, against the LPIPS-family adversarial gap
  **D_LPIPS = mean(C4) − mean(C5)**.

Both gaps are already published for seed 43 Modal: **D_L1 = +0.6473 px**,
**D_LPIPS = +0.5292 px**.

### The materiality threshold, in px, fixed now

**A family shows MATERIAL movement if BOTH hold:**

1. **|Δ| ≥ 0.10 px** in the positive (toward-adversarial) direction, **and**
2. **|Δ| ≥ 2 SE** of that paired per-chip difference.

**Why 0.10 px, and not a number chosen to be safe.** It is the size of the **entire secondary
effect** — C5 − C2 = +0.1086 px at this very seed, +0.063 px as the six-seed mean. A schedule
difference that moves an arm by 0.10 px can account for the whole of the smallest positional
claim this package makes. Anything that large is material by construction, and the threshold
is therefore anchored to a published quantity in the same units at the same seed rather than
picked. The 2 SE condition is the same evidential bar the ordering rule in
[packageA-registration.md](packageA-registration.md) uses.

**The fraction f = Δ / D is REPORTED, NOT REQUIRED**, for both families. It is the natural
thing for the manuscript to quote and it is not a gate; no band is attached to it, because a
second threshold on a derived ratio would be a second gate smuggled in as a description.

### The two branches, both written now

**BRANCH 1 — LIVE.** *Either* family shows material movement by the test above.

> **The LR schedule is a live alternative explanation for the adversarial main effect, and
> the manuscript must say so.**

**What branch 1 costs, written before the answer is known:**

- **The primary (C5 − C4) and both main effects (C1 − C2, C4 − C5) can no longer be
  attributed to the adversarial term alone.** They must be stated as the effect of *the
  adversarial configuration, which also trains ~11% less on the reconstruction objective*,
  with the confound named in the same sentence as the number. The six-seed sign replications
  stand as replications — they do not become wrong — but what they replicate is a
  two-factor contrast, not a one-factor one.
- **The claim sentence narrows.** "Plausibility pressure degrades generated reference
  imagery" survives for the LPIPS half (see below) but the adversarial half acquires a stated
  alternative.
- **The edge-ratio mechanism readings carry the caveat too**, since three of the four arms
  differ in schedule as well as in objective.
- **The secondary and the title are untouched**, for the structural reason given above.
- **The design rule survives intact.** It says which checkpoint to hand over, and C2 is still
  the better checkpoint whatever explains why.
- **The fix is one more package, not a re-planning:** `C1_nowarmup` / `C4_nowarmup` at six
  seeds, ≈ $21, which breaks the collinearity in the other direction. **Whether to run it is
  the supervising session's call and is explicitly not decided here.**

**BRANCH 2 — ANSWERED.** *Neither* family shows material movement.

> **The confound is answered at the positional outcome.** Giving a non-adversarial arm the
> adversarial arm's exact learning-rate schedule does not move its positional residual
> materially toward the adversarial arm, so the ~11% integrated-LR deficit does not account
> for the main effect. The manuscript states the deficit as a disclosed design asymmetry, with
> this probe cited as the test that bounded it, and the adversarial attribution stands.

**Under either branch, nothing already disclosed is withdrawn.** The 14.7% summed-LR
asymmetry is already listed among the "known asymmetries, inherited and disclosed rather than
removed" in [seed-replication-registration.md](seed-replication-registration.md); this probe
measures its consequence rather than revealing it.

### A third possibility, registered so it is not read as either branch

**Movement in the NEGATIVE direction** — a warmed non-adversarial arm scoring *better* than
its un-warmed counterpart — is neither branch. It would mean the shorter schedule helps,
which cannot explain why the adversarial arms lose. It is **reported as its own outcome**,
counted as branch 2 for the confound question (the LR deficit does not explain the main
effect), and flagged as an unexplained observation rather than being folded into a story.

## Scope — this cannot become a confirmatory estimate

**n = 1 seed. A mechanism probe, not a confirmatory estimate.** It enters **no registered
contrast**. It does not join the six-seed Modal block, it does not modify any published
number, and it cannot repair or strengthen the failed interaction reading. Its result is
reported beside the block with the seed count attached wherever it appears, exactly as the
warm-up de-confound's loss-curve reads are.

**The comparison is within platform and within seed** — Modal, seed 43, both sides — which is
the control the warm-up package's first attempt lacked and had to correct
([warmup-deconfound-results.md](warmup-deconfound-results.md) §4a).

**Registered limitation: this probe tests the schedule's effect on the NON-adversarial arms
only.** It asks whether the schedule alone can produce an adversarial-sized penalty. It cannot
establish that the adversarial arms would be unaffected by the reverse manipulation; only
`C1_nowarmup` / `C4_nowarmup` can do that, and that is the follow-up named above.

## Artifacts

Per standing practice 10: the per-chip CSV, the edge-ratio CSV and the summary JSON produced
by this run are committed to `tubitak/docs/evidence/`, with sha256 recorded in the manifest,
**including if the result is inconvenient.**

## The stop condition

**If branch 1 fires, execution stops and the result is reported before anything else is
done.** The follow-up package is not launched, no document is edited beyond recording the
result, and the decision is the supervising session's.

Nothing is downloaded or scored until this registration is committed and pushed.
