# gencp-ref tool package — results, scored against the registrations

**Date:** 2026-08-21, branch `tubitak-tool`. Registrations:
[tool-gate-registration-2.md](tool-gate-registration-2.md) (commit `c4f8804`) and
[tool-registrations-3.md](tool-registrations-3.md) (commit `b80f384`) — all committed before
their numbers existed. The first gate registration stands as FAILED-as-designed
([tool-gate-registration.md](tool-gate-registration.md)); its failure produced corrections-log
entries 13–15 and the invariance rule in [standing-practices.md](standing-practices.md).

## Correctness gate (re-registered) — criteria 2 & 3 PASS; criterion 1 byte-exact where the archive is sound

- **Criterion 1 (tile space):** the full production path (country snapshot → `-s smart`
  extent extract → CLC+ render → bicubic 256) reproduces the verified corpus inputs
  **byte-exactly** on 30TXQ_0830_00 and 30TXQ_0934_00. The third chip (30TXQ_0879_00)
  failed because its archived input is itself a stale pre-fix render (entry 15's census
  later put the corpora at two-thirds stale). The fake layer of this criterion is
  unsatisfiable across processes (test-time dropout, entry 14) and was recorded as such,
  not scored.
- **Criterion 2 (mosaic space): PASS** — interior pixels equal the independent
  corrected-affine warp exactly; all ±1 differences lie inside the registered blend zone.
- **Criterion 3 (georeferencing): PASS** — transform exact, embedded GSD 10.0390625,
  cross-correlation lag (0,0) against the verified evaluation warps, all chips.

## Seam experiment — blending adequate; 640 m default

| overlap m | seam ratio | points obs/exp near seams (p) | duplicated generation |
|---|---|---|---|
| 0 (baseline, not quotable as a result) | 1.234 | 1.12 (0.12) | — |
| 160 | 0.958 | 1.12 (0.029) | 12% |
| 320 | 0.970 | 1.17 (0.003) | 23% |
| **640 (default)** | **1.008** | **1.01 (0.46)** | 44% |
| 960 | 0.996 | 1.00 (0.52) | 61% |

No blended configuration triggers the registered inadequacy criteria (ratio > 1.10;
clustering obs/exp > 1.25 at p < 0.05), but seam attraction is *statistically detectable* at
160/320 m and vanishes at 640 m. Default 640 m: we take the safe side of our own threshold
and pay 44% duplicate generation — the same reasoning that discarded the warm-up run. 160 m
is the documented economy setting.

## Registration A — determinism: dropout-off is score-indistinguishable

Paired (deterministic − seeded), 30 production-input chips, all four arms: pretrained
−0.004 ± 0.089, C1 −0.040 ± 0.077, C2 −0.021 ± 0.092, C3 −0.028 ± 0.070 px — **all in the
registered ≤ 0.05 px "indistinguishable" band**, with the no-op guard confirming the images
genuinely differ (70–90% of pixels). Report-back per the registration: `--deterministic`
could become the default at zero measured cost; the seeded evaluated path remains default
until that decision is taken deliberately.

## Registration B — acceptance gate re-run: PASS on the registered estimator, and the original figure is retired

Same claim, same 0.15 px bound, corrected input path, mean-of-8 estimator (small-n standing
rule), 25 held-out chips, harness replicated from the original (verified: 17/25 regenerated
inputs differ from the stale corpus — exactly entry 15's census count).

| estimator | paired Δ (ours − corpus refs) | verdict at 0.15 px |
|---|---|---|
| **mean-of-8 (registered)** | **+0.119 ± 0.138 px** (t = 0.86) | **PASS** |
| single draw (seed 42) | +0.1495 ± 0.143 px | PASS by 0.0005 px |
| original (stale corpus, single draw) | +0.012 ± 0.132 px | retired — not quotable |

The corrected central value is an order of magnitude larger than the stale figure but
statistically indistinguishable from zero. **The shift is carried almost entirely by the
five German-zone chips** (+0.61 px mean vs **−0.004 px** on the 20 non-German chips) whose
registered snapshot-drift caveat applies (the `germany-latest` re-download; content drift,
not render path — the registration's attribution, not established by this run). Quotable
sentence from here on: *held-out acceptance +0.119 ± 0.138 px, PASS; statistically zero
outside the drift-caveated German chips.* The PENDING flags on +0.012 stay, now pointing
here.

## Registration C — K-draw averaging: marginal; variance map real but sub-bar

- **Mean-of-8 vs single draw:** ≈ 0 on all Overpass-input cells (+0.002…+0.014 px) and EU
  C1; EU C2 +0.046 ± 0.031; **production-input C2 +0.131 ± 0.078** (n = 30, ~1.7 SE) — the
  only cell crossing the registered ≥ 0.10 px worth-it line, weakly supported, and on the
  production-relevant configuration.
- **Variance map:** the registered usability bar (rho ≥ +0.15, p < 0.01, both arms at one
  site) is **not met**; the signal is nonetheless replicated and highly significant
  everywhere it matters: production-Ankara C1 +0.122 / C2 +0.142, EU C1 +0.118 /
  C2 +0.112 (all p < 1e-7). Per the registration it is not adopted; recorded as a
  sub-threshold, replicated signal — follow-up candidates: higher K, different local
  window. The reliability sidecar therefore **stays input-heuristic for now**.
- Cost realism: 6,240 inferences + 1,560 KARIOS runs in 20.6 min wall at 64-wide
  parallelism — K = 8 is far cheaper than budgeted.
- Pattern worth stating: averaging helps, and variance predicts residual, **precisely where
  inputs are production-provenance** — consistent with model uncertainty concentrating on
  the (forest-bearing) content the train/serve skew under-represents.
- All numbers here are KLT-conditional, as registered: the institution's matcher is not
  KLT, and no gain is assumed to transfer.

## Standing state

Production tool: seeded (byte-exact reruns), 640 m overlap, corrected transform mandatory,
provenance embeds seed/torch/dropout/snapshot/checkpoint-hash/commit. `--deterministic`
available, non-default. `--bands single` still refuses pending Package A. Branch isolated
from `tubitak-tr` until Package A is scored.
