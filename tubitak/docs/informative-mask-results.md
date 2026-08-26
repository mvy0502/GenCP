# Informative-mask edge ratio — results

Written 2026-08-26 immediately after
[informative-mask-registration.md](informative-mask-registration.md) was committed and pushed
(`c158a7b`). Re-scoring of committed rasters; no training, no inference, no GPU.

**BRANCH 1 FIRES. The blur objection is refuted by a positive test at six seeds.**

## The result

Per-arm mean edge ratio on the **informative** mask (Sobel(input) > 20), beside the
registered **silent**-mask reading (Sobel(input) ≤ 20). 127 of 130 chips per seed; 3 skipped
where the mask or the real-chip edge fraction was empty, identically in every seed.

| seed | **C2 informative** | C2 silent | C1 inf. | C4 inf. | C5 inf. |
|---|---|---|---|---|---|
| 45 | **0.9882** | 0.2791 | 1.0242 | 1.0387 | 1.0515 |
| 46 | **0.9800** | 0.2713 | 1.0364 | 1.0316 | 1.0512 |
| 47 | **0.9885** | 0.2844 | 1.0282 | 1.0367 | 1.0518 |
| 48 | **0.9849** | 0.2727 | 1.0338 | 1.0375 | 1.0526 |
| 49 | **0.9858** | 0.2765 | 1.0288 | 1.0338 | 1.0505 |
| 50 | **0.9859** | 0.2790 | 1.0295 | 1.0382 | 1.0511 |

**Sign tallies against the pre-committed thresholds:**

- **C2 ≥ 0.80 on the informative mask: 6/6.** Mean 0.9856, range 0.9800–0.9885.
- **C2 ≤ 0.50 on the silent mask: 6/6.** Mean 0.2772.
- Both conditions of branch 1 hold in every seed. **P = 1/64 on the informative reading with
  the direction fixed in advance.**

## What it establishes

**C2 reproduces the real image's edge density where the input asserts structure — 0.986, within
1.5% of reality — and suppresses it to 0.277 where the input says nothing.** That is a factor
of **3.6** between the two masks, in the same arm, on the same chips, with the same operator.

**Blur cannot do that.** A Gaussian suppresses edges wherever they are, so a smoothing
explanation predicts C2 below 1.0 on *both* masks. It is below on one and at unity on the
other. **The suppression is conditional on what the input knows, which is what "restraint"
names.**

The other three arms sit at 1.03–1.05 on the informative mask: slightly *above* reality,
consistent with their behaviour on the silent mask, where they run 1.07–1.16. **Every arm
except C2 adds edges everywhere; C2 adds them only where the input warrants it.**

## Scope

**n = 6 seeds, mechanism reading, not positional.** It enters no registered positional
contrast and modifies no published number. The silent-mask reading is unchanged and remains
the registered one; both masks are reported side by side.

The 3 skipped chips per seed are identical across seeds and were skipped by the same rule the
registered measurement uses (empty mask or zero real-chip edge fraction).

**This is not a corrections-log entry.** A registered test returning its registered branch is
the system working.

## Artifacts

Per standing practice 10: six per-chip CSVs and `informative_mask.json` under
`tubitak/docs/evidence/informative_mask/`, and the script at
`tubitak/scripts/informative_mask/informative_mask_ratio.py`.
