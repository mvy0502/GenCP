# Registration C-common — Gate D on common support

**Registered 2026-08-26, branch `tubitak-tr`, before any number in this test exists.**
Convention: **Δ = candidate − baseline; negative = candidate better.** Inference path is
stated for every number.

## What is under test

Gate D reported eval-mode BatchNorm as slightly better — C3 **−0.056 px**, C2
**−0.259 px** — while the number of matched KLT points fell by about 20% (median 60→50 on
C3, 61→48 on C2).

There is a specific mechanism that produces exactly that joint pattern, and it is not an
accuracy gain:

> Eval-mode BatchNorm uses running statistics, which produces a **smoother** image.
> Smoother images yield fewer detectable corners. The corners that survive are the
> **strong, unambiguous** ones, which are also the ones that match well. The median error
> then improves by **survivorship** — the hard points were removed from the sample, not
> solved.

The Gate D numbers cannot distinguish that from a real gain, because each arm's median is
computed over **its own** point set. This test removes that confound by scoring both arms
on the **same points**.

## Invariances — what this test assumes identical on both sides

- **Inputs:** the same 30 task3 production-provenance renders, already on disk; nothing
  re-rendered.
- **Reference:** the same warped satellite reference, `plugin_gates/gate_d/ref/<stem>.tif`
  (228×228 at 10 m, inset 145 m) — the reference whose reconstruction was verified to
  reproduce Registration A exactly (1.940379 px, n = 19 on `ank_0_30`).
- **Warp geometry:** identical, asserted equal to Registration A's own artifact.
- **KARIOS config and version:** unchanged, `tubitak/configs/karios_gencp.json`.
- **Checkpoints:** the same C3 and C2 weights.
- **Analysis code path:** one script, both arms, same matching and same statistic.
- **The KLT point sets themselves are NOT assumed identical** — that they differ is the
  thing being controlled for.

The only degree of freedom is the inference-time normalisation mode.

## Matching rule — fixed here, before any number

Both arms' rasters live on the **same 228×228 pixel grid with the same transform**, so KLT
point coordinates `(x0, y0)` are directly comparable across arms without any reprojection.

- A point in arm A and a point in arm B are **the same point** when their Euclidean
  distance is **≤ 1.0 px** in that shared grid.
- Matching is **mutual nearest neighbour**, resolved greedily in ascending distance, so it
  is **one-to-one**: no point may be matched twice, and the pairing does not depend on
  which arm is processed first.
- The common set for a chip is the set of such pairs. Chips with **fewer than 5** common
  pairs are excluded from the paired statistic and their exclusion is reported.
- **Sensitivity:** the whole test is repeated at tolerance **0.5 px** and **2.0 px**. If
  the conclusion changes with tolerance, that is reported and no conclusion is drawn from
  the 1.0 px figure alone.

## Statistic

Per chip, per arm, on the common set only: **median radial error**
`median(hypot(dx, dy))` — the same statistic and the same definition as every previous
number in this project. Then the paired per-chip difference across the 30 chips, with SD,
SE and t.

## Registered predictions

**Primary prediction (the survivorship hypothesis).** If survivorship explains the Gate D
result, then on common support the eval-mode advantage **shrinks toward zero**:
`|Δ_common| < |Δ_full|` in both arms, and the C2 advantage in particular falls to within
the **0.05 px indistinguishable band**.

**Secondary prediction.** The points *dropped* by eval-mode (present in the batch-statistic
arm, absent from the eval-mode arm) have a **higher** median error, in the batch-statistic
arm, than the points that survive into the common set. That is the direct signature of the
mechanism, measured on one arm only, so it does not depend on the pairing.

**The alternative outcome, stated so it cannot be explained away afterwards.** If
`Δ_common` stays at or beyond the full-set value — that is, the advantage survives on
common support — then survivorship is **not** the explanation and eval-mode really is
better on these chips. That outcome would make eval-mode a genuine candidate for
deployment and is reported as such.

## Bands and decision

Standing bands, unchanged: |paired mean Δ| ≤ **0.05 px** indistinguishable; > **0.15 px**
materially different.

**This decides which model ships.** If the advantage does not survive on common support,
the plugin keeps **batch-statistic** normalisation — which additionally reproduces the
measured baseline — and eval-mode is not adopted. If it does survive, eval-mode becomes a
candidate and the decision is reported for the institution, not taken here.

No parameter is tuned to make either outcome appear. A failed prediction is reported.
