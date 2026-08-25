# Launch record — AMENDMENT SEED-c seed block + warm-up de-confound, one wave

Launched 2026-08-25 ~21:38 +03, detached. App `ap-FmfGHSbLiIJJG7LotSbiSP`, 14 tasks at
launch (7 CPU drivers + 7 GPU containers — all seven GPU slots concurrent, within the
workspace limit of 10). Driver/registration code at `8d8dd66`; replication arms pinned to
`f2dc962`; warm-up arms pinned to `a782aa5`. Registrations committed and pushed before
launch: AMENDMENT SEED-c (`9ab599e`), warmup-deconfound-registration.md (`8d8dd66`).

## PRE-LAUNCH CORRECTION — arm order, caught before anything ran

The tasked order read `["C5", "C4", "C1", "C2"]`. Its own stated rationale — what survives
an early termination should be the arms of the primary contrast — contradicts placing C2
last: **C2 is a leg of C5 − C2, the contrast that carries the paper's "plausibility
pressure" claim and its title; C1 feeds only C1 − C2, a supporting sign reading.**
Corrected before launch to:

    ["C5", "C4", "C2", "C1"]

Cumulative per-seed times under the corrected order: C5 2.16 h, +C4 4.01 h, +C2 4.59 h,
+C1 5.17 h — a ceiling hit costs C1 first, with the title leg already complete. Recorded
here only: nothing was executed under the old order and nothing entered the record, so
this is not a corrections-log matter.

**Risk statement restated under the corrected order** (superseding the earlier "stops in
the cheap tail arms" phrasing, which was written under the old order): a ceiling hit near
$50 costs **C1 of the last seed or two, which feeds only C1 − C2.**

## ACCEPTED RISK — recorded before launch

- Remaining credit **$18.23**; headroom to the ceiling **$38.23**; estimated remaining
  work **~$39**. Over by roughly one arm, not mid-block.
- The **$50 stop is accepted** (Starter usage-limit ladder: $30 credits + $20, auto-charge
  $10 at $40 usage; the settable maximum — spend limit $20, budget $42.50 — is below the
  requested $60 backstop). skip-completed makes the **Sep 1 resume exact** (cycle resets
  Sep 1 with $30 fresh credits).
- The **$20 spend limit stays as set.** No further raise attempted, no support request.

## Billing at launch, read from the dashboard immediately before

Plan Starter, $30 credits/month. Cycle Aug 1 – Sep 1, 2026. **Total usage $11.77, credits
applied $11.77, charged $0.00** (read ~21:37 +03). Limits read from the workspace Limits
page, not assumed: GPU 10 concurrent, containers 100, sandbox 5/s + 150 burst.

## Expected wall clock (Modal-measured, not the Kaggle figures)

Measured on Modal A10G at seed 43: C4 1.85 h, C5 2.16 h, C2 0.42 h (C2_unsorted; sorted
C2 runs ~28% slower per image, so ~0.58 h). C1 was not timed directly, but its container
log shows 0.0285 s/img against sorted C2's 0.0282 s/img, so ~0.58 h. Four arms serial per
seed ≈ **5.2 h of compute; ~5.5 h per driver** with container start, clone, tar staging
and patch. Six drivers in parallel → **block wall clock ≈ 5.5 h, expected complete
~03:15 +03 (26 Aug)**. Warm-up driver (C5_warmup ~2.2 h + C2_warmup ~0.65 h + overhead)
≈ **2.9–3.0 h, expected complete ~00:35 +03**. To be confirmed against the first
completed arm; any drift reported here.

## Call ids

| driver | call id | arms |
|---|---|---|
| seed45 | `fc-01M0X3CXYXG7ERCZ5A738DM23D` | C5, C4, C2, C1 @ f2dc962 |
| seed46 | `fc-01M0X3CY53EVPM32PFB4GNGRKP` | C5, C4, C2, C1 @ f2dc962 |
| seed47 | `fc-01M0X3CYB3P7JAECXHQY1PYA3F` | C5, C4, C2, C1 @ f2dc962 |
| seed48 | `fc-01M0X3CYGVMPFDRA8CQN2FC3Q4` | C5, C4, C2, C1 @ f2dc962 |
| seed49 | `fc-01M0X3CYPKYR1ZDRQ54F4NJYGK` | C5, C4, C2, C1 @ f2dc962 |
| seed50 | `fc-01M0X3CYWCQTDPNNY9BJNDCSAR` | C5, C4, C2, C1 @ f2dc962 |
| warmup_s43 | `fc-01M0X3CZ2NHKXK7NW9F05NWYNH` | C5_warmup, C2_warmup @ a782aa5 |

## Standing notes for this log

- `A10G_USD_PER_HOUR = 1.10` is our hardcoded constant, not a Modal price; driver-computed
  costs inherit it. Reconcile against the dashboard after the first arm completes and
  record any discrepancy here.
- Dashboard balance to be recorded here again as each seed's driver completes.
- The local evaluation stage is to be **timed and recorded here per seed** — checkpoint
  download, inference, warp, KARIOS, edge ratio — no such timing exists in the repo (the
  seed-43 Modal evaluation ran without one), and the next block should be planned from a
  measurement instead of an estimate.
