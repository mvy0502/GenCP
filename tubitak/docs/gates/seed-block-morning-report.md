# Morning report — SEED-c six-seed block + warm-up de-confound (overnight 25→26 Aug 2026)

Assembled 04:05, from the launch record (`seed-block-wave-launch.md`), the overnight log
(`seed-block-overnight.log`), driver FunctionCall results, verify_latest outputs, and the
frozen local evaluations. **Numbers and tables only; no reading is applied and no verdict
appears here** — interpretation is the morning's work, per the overnight mandate.

## 1. Completion matrix

| seed | C5 | C4 | C2 | C1 | driver | driver-computed |
|---|---|---|---|---|---|---|
| 45 | ✔ 7,783 s | ✔ 6,839 s | ✔ 1,833 s | ✔ 1,821 s | DONE, 0 failures | $5.58 |
| 46 | ✔ 7,743 s | ✔ 6,698 s | ✔ 1,854 s | ✔ 1,895 s | DONE, 0 failures | $5.56 |
| 47 | ✔ 7,732 s | ✔ 6,742 s | ✔ 1,830 s | ✔ 1,852 s | DONE, 0 failures | $5.55 |
| 48 | ✔ 7,449 s | ✔ 7,711 s | ✔ 1,832 s | ✔ 1,835 s | DONE, 0 failures | $5.75 |
| 49 | ✔ 7,674 s | ✔ 6,765 s | ✔ 1,825 s | ✔ 1,767 s | DONE, 0 failures | $5.51 |
| 50 | ✔ 7,653 s | ✔ 6,913 s | ✔ 1,827 s | ✔ 1,863 s | DONE, 0 failures | $5.58 |
| warm-up (s43) | C5_warmup ✔ 7,307 s | — | C2_warmup ✔ 1,865 s | — | DONE, 0 failures | $2.80 |

**26 of 26 arm-units complete. Zero failures, zero retries, zero partial directories, no
ceiling stop.** Every arm: pinned checkout (f2dc962 replication / a782aa5 warm-up),
ordered-list hash `4b5f2320…` asserted, patched `image_folder.py` `fef294b8…`, TF32 off.
verify_latest: **28/28 tags** (6×4 block + 2 warm-up + the pre-existing seed-43 set
re-checked in passing) latest==20 tensor-equal, and every downloaded file's local sha256
matches the Modal-side value (all listed in the overnight log and eval logs).

## 2. Failures

None. One anomaly, not a failure: **seed 46's chain ran ~50 min behind** its siblings.
Its per-arm GPU seconds are indistinguishable from the others (table above) — the lag was
container scheduling/queueing between arms, not slow compute. The 00:52 dashboard print
of $49.88 later revised to $42.56; noted in the log as estimator noise, no action taken.

## 3. Balance and reconciliation against the $1.10/h constant

- Launch (21:37): usage **$11.77**, charged $0.00.
- Final read (04:01): usage **$61.96**, credits applied $30.00, **charged $31.96**.
- Wave cost on the dashboard: 61.96 − 11.77 = **$50.19** (includes the overnight
  verify_latest CPU runs, ~cents each).
- Driver-computed total (GPU-hours × $1.10): **$36.33**.
- **Reconciliation: dashboard / driver-computed = 1.38.** The effective all-in rate is
  ≈ **$1.52 per GPU-container-hour**, not $1.10 — Modal bills CPU cores and memory on top
  of the GPU rate, and the driver containers themselves accrue while sequencing. Every
  driver-computed `usd` figure in the records carries this known ~38% understatement.
- Billing ladder, as observed: no stop occurred at any point; the usage limit auto-raised
  ($20 → $100 card) after successful charges; next step text at the final read: "at $60
  you'll be charged $20" (crossed; limit $100 stands).

## 4. Wall clock against the 5.5 h/seed estimate

Launch 21:38. Driver completions (observed at ticks): s47 and s49 by 02:48, s45/s48/s50
by 03:22, s46 ≈ 03:50. Per-seed serial GPU time 18,031–18,827 s = **5.01–5.23 h** against
the 5.17 h estimate — **on estimate, drift < 4%**. Wall per driver ≈ 5.2–5.7 h including
staging; block wall ≈ **6.2 h** end-to-end (vs ≈ 5.5 h expected), the excess being
seed 46's queueing lag, not compute. Warm-up driver: 9,172 GPU-s = 2.55 h, done by 00:19
(≈ 2.7 h wall vs ~2.9 estimated).

## 5. Local evaluation timing, measured per stage (first measurements in the repo)

All six evals: frozen code (48ced64 pins), `--variant modal`, sequential, idle machine.

| seed | wall | ckpt-hash | inference (4×130) | warp (650) | KARIOS (520) | edge (130) | score |
|---|---|---|---|---|---|---|---|
| 45 | 3 m 16 s | 4 s | 19 s | 4 s | 170 s | 2 s | <1 s |
| 47 | 3 m 17 s | ~4 s | ~20 s | ~4 s | ~170 s | ~2 s | <1 s |
| 49 | 3 m 05 s | ~4 s | ~20 s | ~4 s | ~160 s | ~2 s | <1 s |
| 48 | 3 m 37 s | ~4 s | ~19 s | ~4 s | ~190 s | ~2 s | <1 s |
| 50 | 3 m 33 s | ~4 s | ~19 s | ~4 s | ~185 s | ~2 s | <1 s |
| 46 | 3 m 23 s | ~4 s | ~19 s | ~4 s | ~180 s | ~2 s | <1 s |

≈ **3.4 min per seed, KARIOS-dominated (~85%)**; checkpoint download ≈ 6–36 s per batch
(recorded per batch in the overnight log). The earlier "~25 min" impression came from a
loaded machine; plan future blocks on ~4 min/seed local scoring plus downloads.

## 6. Per-seed contrast table (frozen evaluation outputs; signs stated, nothing applied)

| seed | C5−C4 | C1−C2 | C4−C5 | C5−C2 | I_raw | edge pre / C1 / C2 / C4 / C5 |
|---|---|---|---|---|---|---|
| 45 | −0.6153 | +0.6749 | +0.6153 | +0.0619 | −0.0597 | 1.0208 / 1.0845 / 0.2791 / 1.1173 / 1.1442 |
| 46 | −0.6462 | +0.5868 | +0.6462 | +0.0068 | **+0.0594** | 1.0208 / 1.0768 / 0.2713 / 1.1207 / 1.1511 |
| 47 | −0.6162 | +0.7010 | +0.6162 | +0.0665 | −0.0847 | 1.0208 / 1.0951 / 0.2844 / 1.1267 / 1.1484 |
| 48 | −0.5942 | +0.7544 | +0.5942 | +0.0799 | −0.1602 | 1.0208 / 1.0828 / 0.2727 / 1.1251 / 1.1607 |
| 49 | −0.6054 | +0.7024 | +0.6054 | +0.1085 | −0.0970 | 1.0208 / 1.1203 / 0.2765 / 1.1314 / 1.1557 |
| 50 | −0.5775 | +0.6444 | +0.5775 | +0.0519 | −0.0669 | 1.0208 / 1.0718 / 0.2790 / 1.1438 / 1.1504 |

Sign tallies, stated as counts only: C5−C4 negative **6/6**; C1−C2 positive **6/6**;
C4−C5 positive **6/6**; C5−C2 positive **6/6** (smallest +0.0068, seed 46);
**I_raw negative 5/6 — seed 46 is +0.0594**; edge C2 mean < 0.5 **6/6**; edge C5 highest
of the four fine-tuned arms **6/6**. The registered readings (including the interaction's
raw-AND-monotone requirement and the log/rank transforms), seed-43 range checks, seed-level
intervals, and every consequence are **not evaluated here**.

CSV sha256 (per_chip / edge_ratio):
s45 `ac400313…`/`3492d8d1…`, s46 `e1b83871…`/`d55a8164…`, s47 `3c091ad0…`/`e5cb5b21…`,
s48 `9dc33fab…`/`d0211337…`, s49 in `eval_s49.log`, s50 `505e8f94…`/`a5a8b14a…` — full
values in the eval logs and overnight log.

## 7. Warm-up de-confound package

Both arms complete at a782aa5, sorted order asserted, driver $2.80 (driver-computed).
`loss_log.txt` for C5_warmup and C2_warmup downloaded locally (5,582 lines each).
**No curve has been read**, per the registration: the epoch-mean computation and the
branch decision happen in the morning session.

## 8. Standing items for the morning

1. Apply the SEED-c registered readings to §6 and the warm-up registration's readings to
   §7 (curves untouched overnight).
2. seed-43 Modal values' position within the six-seed range (comparability rule).
3. The corrections-log/results documents remain untouched overnight, as mandated.
4. The $1.10 constant's ~38% understatement (§3) for the cost records.

---

**Correction, 05:03 (before hand-off; the 04:01 figures above were pre-settle):** the
dashboard settled to **usage $53.00 / charged $23.00** once all containers closed. Settled
wave cost 53.00 − 11.77 = **$41.23** against the driver-computed $36.33: **ratio 1.13**,
effective ≈ **$1.25 per GPU-container-hour**. The §3 figures ($61.96 / ×1.38) were the
live estimate at read time and are kept above rather than edited away; this note is the
settled reconciliation. Total out-of-pocket this cycle so far: **$23.00**.
