# phase-c and phase-c-lpips registration audit — both halves of the letter's Table I

Date: 2026-08-24. Work item 1 of [paper-roadmap.md](paper-roadmap.md), continuing after
[T1-audit.md](T1-audit.md) and [B2-B3-audit.md](B2-B3-audit.md). Method and structure are
theirs: commit timestamps against artifact mtimes, run configuration diffed against the
registration *text*, and a full recomputation of every reported cell from raw outputs.

Two registrations, audited together because the letter's primary table needs both:

- **[phase-c-lpips-registration.md](phase-c-lpips-registration.md)** (`b07e719`) — the 2×2
  loss factorial, behind the paper's primary result C5 − C4 = −0.487 ± 0.053 px.
- **[phase-c-registration.md](phase-c-registration.md)** (`d621549`) — the C1/C2 arms, whose
  C2 − C1 = −0.638 ± 0.054 px is the Gate-1 comparison target the whole C4/C5 package is
  registered against.

The C4/C5 harness is committed (`tubitak/scripts/c45_eval/`, `40cde9b`), so B3's entry-22
failure mode cannot apply to it. That was the reason to expect a clean result — and it is
why the deviations found below carry more weight than B3's did.

**Verdict in one line: phase-c-lpips passes legs A and B and fails leg C on one registered
stop rule; phase-c passes leg A, fails leg B for the C1/C2 arms because their raw layer no
longer exists, and passes leg C.** Neither failure changes a conclusion. Details in the
per-registration verdicts.

## A. Timeline

### A.1 phase-c-lpips — PASS

Claim audited: "**Status: REGISTERED before any run. Committed before any number exists.**"

| event | time (UTC+03) | evidence |
|---|---|---|
| **registration commit `b07e719`** | **2026-08-23 22:47:35** | git (author = committer) |
| Kaggle arm definitions pushed (`2f2db7f`) | 2026-08-23 22:49:22 | git |
| C4 preflight — first line of the C4 run | 2026-08-23 22:51:31 | `[preflight] arm=C4 seed=42 utc=2026-08-23T19:51:31.700283+00:00` |
| C5 preflight | 2026-08-23 22:51:33 | `[preflight] arm=C5 seed=42 utc=2026-08-23T19:51:33.285450+00:00` |
| C4 training ends (+3 h 28 m) | ≈ 2026-08-24 02:19 | log span 6.7 s → 12,486.8 s |
| C5 training ends (+3 h 33 m) | ≈ 2026-08-24 02:24 | log span 6.5 s → 12,835.9 s |
| C4 checkpoints on disk locally | 2026-08-24 02:41:37 | mtime |
| C5 checkpoints on disk locally | 2026-08-24 02:52:02 | mtime |
| C45 evaluation begins (`C45/ck`, staging) | 2026-08-24 02:35:57 | mtime |
| eval harness committed (`40cde9b`) | 2026-08-24 02:44:06 | git |
| C45 inference (2,610 files) | 02:52:34 → 03:00:23 | mtime |
| C45 warps (1,430 files) | 02:52:40 → 03:00:26 | mtime |
| C45 KARIOS (14,740 files, 1,300 runs) | 02:52:49 → 03:05:03 | mtime |
| **first derived number — `C45_per_chip.csv`, `C45_summary.json`, edge-ratio pair** | **02:54:10** | mtime |
| `C45_b2_per_chip.csv` / `_summary.json` (secondary row) | 02:57:10 | mtime |
| `C45_e1_per_chip.csv` / `_summary.json` | 02:58:48 | mtime |
| `C45_sweep_per_chip.csv` / `_summary.json` | **03:05:04** | mtime |
| **results commit `6560c8b`** | **2026-08-24 03:05:33** | git (author = committer) |

**Classification: zero files predate the registration commit.** All 18,819 files under
`tool_runs/C45/` were written between 2026-08-24 02:35:57 and 03:05:04 — that is, between
3 h 48 m and 4 h 18 m *after* `b07e719`. There is no input, no checkpoint and no computed
score in the package that predates registration. Nothing postdates the results commit
either.

**Elapsed wall time, so no window is asserted rather than explained.** Training: C4
**3 h 28 m** (12,486.8 s), C5 **3 h 33 m** (12,835.9 s), measured from the Kaggle log's own
elapsed-time field, against the ≈ 3 h 25 m / ≈ 3 h 40 m documented in
[phase-c-lpips-results.md](phase-c-lpips-results.md) — C4 agrees to 3 minutes, C5 is 7
minutes shorter than stated. Both figures are written with "≈"; the exact values are
recorded here so the approximation is not the only record. The two arms ran **concurrently**
in separate Kaggle sessions (preflights 2 s apart), which is why ~3.5 h of training fits
between 22:51 and 02:24. Local evaluation: **29 min 07 s** end to end (02:35:57 → 03:05:04),
of which the five-arm panel took 18 min and the epoch sweep the remaining 11. The tightest
interval in the chain is `C45_sweep_summary.json` at 03:05:04 against the results commit at
03:05:33 — **29 seconds** — correctly ordered, and the sweep is the last thing the results
document needed.

**One item the timeline places precisely.** The eval harness was committed at 02:44:06,
which is *after* the C45 staging directory appears (02:35:57) but *before* every inference,
warp, KARIOS run and derived number (02:52:34 onward). The harness that produced every
reported cell was therefore in version control before it produced any of them.

### A.2 phase-c — PASS

Claim audited: "**registered 2026-08-19 09:29:03 UTC … Registered before any training run
exists, on any hardware.**"

| event | time (UTC+03) | evidence |
|---|---|---|
| pretrained baseline scored — `ankara/turkey_karios.csv` | 2026-08-19 11:52:20 | mtime |
| `ankara/clc_scores.csv` (stratum labels) | 2026-08-19 11:54:50 | mtime |
| `ankara/run/inputs`, `ref`, `arms`, pretrained `out` | 2026-08-19 12:05:36 → 12:06:38 | mtime |
| **registration commit `d621549`** | **2026-08-19 12:29:03** (= 09:29:03 UTC) | git |
| C1 preflight — first line of the C1 run | 2026-08-19 15:48:06 | `utc=2026-08-19T12:48:06.953928+00:00` |
| C2 preflight | 2026-08-19 16:18:57 | `utc=2026-08-19T13:18:57.760390+00:00` |
| C1 training ends (+1 h 15 m) | ≈ 2026-08-19 17:03 | log span → 4,528.4 s |
| C2 training ends (+1 h 16 m) | ≈ 2026-08-19 17:35 | log span → 4,573.1 s |
| C1 checkpoints on disk locally | 2026-08-19 22:54:28 | mtime |
| C2 checkpoints on disk locally | 2026-08-19 23:13:20 | mtime |
| **results commit `9e38075`** | **2026-08-19 23:46:44** | git |

**Classification.** Five artifacts predate the registration commit, all of them
**inputs or baseline**: `turkey_karios.csv` (the published Phase B pretrained per-chip
medians, which the registration treats as the baseline to beat), `clc_scores.csv` (the
stratum labels), and the `ankara/run/` input/reference/pretrained-output tree. **No C1 or C2
artifact of any kind predates the registration** — neither arm had been trained; the first
line of C1's run is 3 h 19 m after the registration commit. The claim holds.

Elapsed: C1 **1 h 15 m**, C2 **1 h 16 m**, concurrent (preflights 31 min apart, both
finished by ~17:35). Local scoring occupied the evening; the results commit is 6 h 11 m
after the last training run ended. The window is comfortable and needs no further
explanation — unlike the headline package's 26 minutes.

## B. Reported cells versus raw outputs

### B.1 phase-c-lpips — PASS on every cell that has an artifact, with three transcription
defects and one unreproducible column

**Five-arm ank130 panel** (`C45_per_chip.csv` rebuilt from the 260 raw KARIOS KLT files for
C4/C5 plus `B1_per_chip.csv` for pretrained/C1/C2, under the harness's documented formula:
per-chip statistic = median `hypot(dx, dy)`; per-arm = mean/median of the 130 per-chip
medians):

- **1,300/1,300 per-chip cells reproduce exactly** against the committed
  `C45_per_chip.csv`. Zero mismatches.
- **25/25 per-arm summary cells reproduce** against `C45_summary.json` (5 arms ×
  {mean, SE, median, points-median, zero-point count}).
- **30/30 paired cells reproduce** (6 deltas × {mean, SE, t, n, chips-first-better}):
  C5 − C4 **−0.4871 ± 0.0531**, t = −9.18, 113/130; C2 − C1 −0.6995 ± 0.0592, 116/130;
  C4 − C1 −0.1098 ± 0.0580; C5 − C2 +0.1025 ± 0.0416; C4 − pre −0.5972 ± 0.0606;
  C5 − pre −1.0844 ± 0.0714.
- **Interaction reproduces**: D_L1 = +0.6995 ± 0.0592, D_LPIPS = +0.4871 ± 0.0531,
  I = **−0.2123 ± 0.0691, t = −3.07**. Band: I negative at ≥ 2 SE with D_LPIPS positive at
  ≥ 2 SE → *substitutes*, as reported.
- **Dose-response sweep reproduces, 25/25 cells** (5 epochs × {C4 mean, C5 mean, penalty,
  SE, t}), including the endpoint claims: C5 improves e1 → e20 at **4.25 SE**, C4 flat at
  **0.24 SE**. Both match to two decimals.
- **Edge-ratio table reproduces, 20/20 cells** including the q25–q75 columns
  (pretrained 0.943–1.121, C1 0.959–1.174, C2 0.120–0.382, C4 0.997–1.204, C5 1.032–1.271).
- **Registered bands independently re-evaluated from raw:** primary fires at 9.18 SE; null 2
  fires at 2.46 SE; retraction condition not triggered — **5 of 6 fine-tuned pairs at
  ≥ 2 SE**, the exception being C1–C4 at 1.89 SE, exactly as the results document states.

**The "reproduces the committed headline figures to the fourth digit" claim — VERIFIED,
and it is true of the means only.** The four existing arms' 20-chip production means
recomputed through the C45 harness are pretrained 1.369802, C1 0.764049, C2 0.592721,
C3 0.610947, against `B2_summary.json`'s committed 1.3698 / 0.7640 / 0.5927 / 0.6109 —
**identical to four decimal places, 4/4**. The extension is validated as claimed.

**Defect 1 — the secondary table's SE column does not come from the artifact and cannot be
reproduced.** `C45_b2_summary.json` stores SEs of 0.1612 / 0.0712 / 0.0409 / 0.0375 /
0.0949 / 0.0660 for pretrained / C1 / C2 / C3 / C4 / C5, which is exactly what
`sd/√20` gives and exactly what B2 committed for the four existing arms. The results
document's secondary table prints **1.370 ± 0.108, 0.764 ± 0.043, 0.593 ± 0.041,
0.611 ± 0.043, 0.844 ± 0.054, 0.663 ± 0.045** — **five of six disagree with the artifact**,
only C2's 0.041 matching. The five values are not the SE of the mean, the SE of the median
(1.2533·sd/√n), a bootstrap median SE (4,000 resamples), a MAD-based SE, or an IQR-based
SE; they are not the RGB-band SEs either; and they appear nowhere else in the repository.
**They have no traceable origin.** → **corrections-log entry 24**.

The defect is confined to that column. Every mean, median, point count and paired delta in
the same table reproduces exactly, the ordering C2 < C3 < C5 < C1 < C4 < pretrained is
correct, and the paired C5 − C4 = −0.1817 ± 0.0541 (t = −3.36, 16/20) — the sentence the
row exists to support — is right. Because the row is explicitly secondary and carries no
registered band, no verdict depends on the wrong column.

**Defect 2 — two double-rounded cells in the primary tables.** Twenty reported 3-decimal
values were re-derived from raw and compared against correct half-up rounding:
**18/20 correct, 2 wrong by +0.001**, both from transcribing the artifact's 4-decimal value
and rounding a second time.

| cell | raw value | correct 3 dp | results document |
|---|---|---|---|
| C4 ank130 mean | 1.965452 | **1.965** | 1.966 |
| C1 edge-ratio mean | 1.096463 | **1.096** | 1.097 |

Both appear in tables destined for the letter. Neither changes a band: C4's mean is not a
band quantity, and C1's edge ratio clears the "near 1.0 ≥ 0.8" threshold either way.
→ folded into **entry 24**.

**Defect 3 — half-integer point-count medians printed as integers, in both packages.** With
an even number of chips the median point count can be a half-integer; the harness prints it
with `:.0f`, which rounds to even, and the documents carry the rounded value with no note.
Systematic and explicable. **Enumerated here and deliberately not corrected**, because how
they should be stated depends on a decision the audit should not make alone — see below.
→ folded into **entry 24**.

**Complete list of half-integer point-count medians, 2026-08-24.** Every point-count median
in every artifact behind a reported table was checked; ten are half-integers, six of them in
a printed table:

| document | table | arm | artifact value | as printed |
|---|---|---|---|---|
| phase-c-lpips-results.md | ank130 primary panel | C4 | **61.5** | 62 |
| phase-c-lpips-results.md | 20-chip secondary | C1 | **163.5** | 164 |
| phase-c-lpips-results.md | 20-chip secondary | C4 | **155.5** | 156 |
| phase-c-lpips-results.md | 20-chip secondary | C5 | **224.5** | **224** (down) |
| phase-c-results.md | pretrained per-stratum | Q2 | **37.5** | 38 |
| phase-c-results.md | pretrained per-stratum | Q3 | **51.5** | 52 |
| — artifact only, not printed anywhere — | | | | |
| headline-results.md B2 (BT.601) | — | C1 | 163.5 | not printed |
| headline-results.md B2 (RGB) | — | pretrained / C1 / C3 | 78.5 / 136.5 / 181.5 | not printed |
| B1 | — | C1_e10 / C2_e10 | 62.5 / 72.5 | not printed |

C5 rounds down while C1 and C4 round up because `:.0f` rounds half to even; it is consistent,
not erratic.

**The load-bearing argument is unaffected, and this is the reason not to touch these
blind.** The point-count claim the paper leans on — *"C5 produces more surviving matches than
C2 (median 88 vs 72) and still scores worse"*, the sentence that closes the fewer-but-better
reviewer objection — rests on the ank130 panel, where **both values are exact integers**
(C5 88.0, C2 72.0). No half-integer enters it. The same panel's C4 (61.5) is not part of that
comparison. So the decision about how to state half-integers is a presentational one that can
be taken deliberately — print one decimal, or note the convention once — without any risk to
the argument, which is why it is listed rather than silently rewritten.

**Training-curve prose, checked against the per-epoch log means:** C4's main stage
54.37 → 55.73 = **+2.50%** ✓, 54.37 **is** the run minimum ✓, warm-up epoch 1 = 56.24 ✓,
C1's G_L1 wiggle band 32.82–34.33 ✓ ("32.8–34.3"). One inaccuracy: C5's G_LPIPS is
described as a "**monotone decrease** 53.0 → 49.0"; the endpoints are right (53.01 → 49.01)
but the series is **not monotone** — it rises at five epoch transitions (e11→12, e12→13,
e14→15, e16→17, e17→18), each by ≤ 0.22. The contrast being drawn (C5 falls, C4 drifts up)
survives; the word does not. Disclosed here, not corrected.

**Available but unscored, no deviation:** the C4/C5 KARIOS runs also produced the **RGB**
band on the 20-chip subset (40 runs, `B2/karios/rgb/C{4,5}/`), which no summary scores.
The registration fixes BT.601 for this row in its invariance section, so RGB is unregistered
and its absence is *not* the entry-19 pattern. Recorded here because the data exists and
corroborates: C4 0.9768 ± 0.1351, C5 0.6606 ± 0.0566, **C5 − C4 = −0.3161 ± 0.1044
(t = −3.03, 20/20 chips)** — a larger and cleaner main effect than BT.601's, same ordering.

### B.2 phase-c — FAIL for the C1/C2 arms: the raw layer no longer exists

**The pretrained row reproduces.** `ankara/turkey_karios.csv` (mtime 2026-08-19 11:52:20)
carries the per-chip median and point count for all 130 chips plus the stratum label.
Recomputed against the reported table: **10/12 cells exact** (5 strata + ALL, × {median,
points}), the two exceptions being the Q2/Q3 half-integer point counts of Defect 3. Medians
Q1 3.4798, Q2 3.1060, Q3 2.4922, Q4 2.0843, Q5 1.2404, ALL 2.5877 — all correct to the
reported 3 decimals.

**The C1 and C2 rows cannot be recomputed at all.** No per-chip artifact from the
2026-08-19/20 phase-C scoring run survives anywhere: the earliest directory under
`tool_runs/` is dated 2026-08-20 19:32, the `ankara/run/` tree holds only the pretrained
arm's outputs (`out/genCP_HR_RGB_model`), and `turkey_karios.csv` has no C1 or C2 column.
Every reported C1/C2 cell — the ten per-stratum values, the two ALL values, all three paired
deltas including **C2 − C1 = −0.638 ± 0.054**, and R2's correlations rho +0.232 / +0.032 —
rests on numbers with no surviving raw layer. **This is the entry-22 pattern in the phase-C
package**, and it lands on the number the entire C4/C5 registration nominates as its Gate-1
comparison target. → **corrections-log entry 25**.

**What can be said instead, labelled as the cross-check it is.** The Aug-21 B1 sweep
regenerated C1 and C2 at epoch 20 on the same chips, same inputs, same KARIOS config, seed
42 — a *different draw* from the same stochastic path, not a reproduction:

| quantity | phase-c-results.md (2026-08-19) | Aug-21 seed-42 redraw | gap |
|---|---|---|---|
| C1 ALL median | 1.869 | 1.7939 | −0.075 |
| C2 ALL median | 0.929 | 0.9744 | +0.045 |
| C1 − pretrained | −0.530 ± 0.070 (32/130 worse) | −0.4874 ± 0.0753 (35/130) | +0.043 |
| C2 − pretrained | −1.167 ± 0.074 (8/130 worse) | −1.1869 ± 0.0654 (4/130) | −0.020 |
| **C2 − C1** | **−0.638 ± 0.054 (9/130 worse)** | **−0.6995 ± 0.0592 (14/130)** | **−0.062** |

Every gap is well inside the test-time-dropout redraw noise the project has already measured
(0.1–0.4 px per chip median, corrections-log entry 14), every sign and every verdict is
unchanged, and the C4/C5 results document **already discloses both values side by side**
("C2 − C1 (same draw family) −0.700 ± 0.059" against "C2 − C1 (committed target,
phase-c-results.md) −0.638 ± 0.054"). The reported numbers are corroborated. They are not
verified, and the difference matters: a reader who asks for the C2 − C1 raw layer cannot be
given one.

## C. Registered protocol versus what ran

### C.1 phase-c-lpips

| registered | ran | status |
|---|---|---|
| C4 = C1's schedule exactly: 2-epoch warm-up 2e-5, `--lr_policy step --lr_decay_iters 50`, then linear 10+10 at 1e-4, `epoch_count 3` | log: stage 1 `lr 2e-05, n_epochs 2, n_epochs_decay 0, lr_policy step, lr_decay_iters 50, epoch_count 1`; stage 2 `lr 0.0001, 10+10, linear, epoch_count 3`; effective LR printed 2.0e-5 then 1.0e-4 | ✓ |
| C5 = C2's schedule exactly: linear 10+10 at 1e-4, `epoch_count 1` | log: single stage, `lr 0.0001, n_epochs 10, n_epochs_decay 10, linear, epoch_count 1` | ✓ |
| λ = 100, `gan_mode vanilla` (BCE) where a D exists, batch 4, load 286 / crop 256, BtoA, unet_256, norm batch, `save_epoch_freq 1` | all present and identical in both arms' logs | ✓ |
| `--LPIPS` on both new arms (stock CLI flag) | `LPIPS: True [default: False]` in both | ✓ |
| C5's GAN-zeroing patch retargeted to the LPIPS branch | `[C5] adversarial term zeroed in the Kaggle copy of pix2pix_model.py`; epoch-20 rows show `D_real: 0.000 D_fake: 0.000` | ✓ |
| seed 42 via the sitecustomize hook, both stages | `[preflight] arm=C4 seed=42` / `arm=C5 seed=42` | ✓ |
| same training data, 5,577 Turkish pairs, zero EU mix | `[preflight] training pairs: 5577` in both, and in C1/C2 | ✓ |
| torchmetrics version recorded from the log and reported | log `torchmetrics 1.9.0`; results document reports 1.9.0 against the paper's 0.11.0 | ✓ |
| checkpoints every epoch; epoch 20 is the evaluated one | 20/20 per-epoch `*_net_G.pth` for both arms; **`latest_net_G.pth` tensor-equal to `20_net_G.pth`, 82/82 tensors, both arms** (asserted here, not taken from the document) | ✓ |
| KARIOS config unchanged across every cell | **1,214 per-run config copies under `C45/karios/**`, all one sha256 `8eaa5bd8…`, equal to the committed master** | ✓ |
| ank130 primary, all 10 cells × 130 chips | 130 KLT CSVs in each of C4, C5, C4_e{1,2,5,10}, C5_e{1,2,5,10} — 1,300, none missing | ✓ |
| PRIMARY band (C5 − C4 negative at ≥ 2 SE) | scored, reported, fired at 9.18 SE | ✓ |
| SECONDARY edge-density bands — four predictions (C1 near 1.0, C4 near 1.0, C2 well below, **C5 near 1.0**) | all four scored and reported; all four fired | ✓ |
| INTERACTION bands (additive / substitutes / super-additive / degenerate) | scored, reported as substitutes with the D_LPIPS > 0 precondition checked | ✓ |
| NULL 2 (C5 − C2 positive at ≥ 2 SE) | scored, reported as fired (+0.1025 ± 0.0416, 2.46 SE) | ✓ |
| RETRACTION condition (all four fine-tuned arms within noise) | scored, reported as not triggered, with the 5-of-6 count correct | ✓ |
| NULL 1 (primary does not fire → claim narrows to GAN+L1) | not applicable once the primary fired; the document does not say so explicitly | ⚠ trivial |
| epoch sweep run **only if** the primary band fires | primary fired; sweep run, endpoints first as registered | ✓ |
| 20-chip production subset evaluated as secondary, no registered band | run and reported, labelled secondary | ✓ (but see Defect 1) |
| Cappadocia known-displacement recovery, "**if cheap**" | **not run — and disclosed in its own section** of the results document, with the reason (the T1 harness was not preserved) and an open-items entry | ✓ **this is the anti-entry-19 behaviour** |
| **C4's stop rule = C1's, term renamed: "G_LPIPS rising over the first two main-stage epochs" ⇒ the run stops** | **the condition was met and the run continued to epoch 20; the document declares it "not triggered" using a different test** | **✗ — deviation, entry 26** |
| edge-ratio recompute uses "the committed B3 definition" | operator and threshold verified identical to `hallucination_analysis.py` (scipy `sobel` hypot, threshold 20.0); **the B3 mask recipe itself cannot be verified — B3's harness was deleted (entry 22)** | ⚠ see C.3 |

#### C.2 The stop rule — the one real deviation, and it is inherited

The registration says: *"C4's stop rule is C1's with the term renamed — if G degrades early
despite the warm-up (**G_LPIPS rising over the first two main-stage epochs**), the run stops
and reports its curves, no rescue by improvisation."* The referenced C1 rule is stated in
[phase-c-config.md](phase-c-config.md) as having two halves: a **coarse half** — "L1 rising
over the first two main-stage epochs" — and a **sharp half** — "a generator-loss spike in
the first few hundred iterations, the actual cold-D signature".

C4's per-epoch G_LPIPS means, computed here from the 5,580 logged iterations:

| epoch | 1 (warm-up) | 2 (warm-up) | **3** | **4** | **5** | … | 20 |
|---|---|---|---|---|---|---|---|
| G_LPIPS | 56.24 | 55.48 | **54.37** | **54.65** | **55.02** | … | 55.73 |

**The main stage begins at epoch 3, and G_LPIPS rises at each of the next two epochs.** The
coarse half of the registered stop rule, read literally, was met, and the run continued to
epoch 20. [phase-c-lpips-results.md](phase-c-lpips-results.md) records the rule as "**not
triggered**", justifying it as *"G_LPIPS at main-stage start (54.4) is the run minimum,
below warm-up (56.2) — no cold-D spike"* — which is the **sharp** half. Both statements in
that sentence are true (54.37 is the run minimum; it is below the warm-up level); they are
just not the test the registration names, and the substitution is not disclosed as one.

**Three things keep this from being worse than it is, and all three are load-bearing.**

1. **It is inherited, not invented for C4.** C1's own G_L1 rose at the first of its two
   main-stage transitions too — 33.582 → **34.224** → 33.858, a **rise then a fall**, not
   C4's rise at both — and C1 was likewise not stopped. The coarse half was never applied
   literally in phase C either. C4/C5 inherited an ambiguous rule and resolved it the same
   way the original run had.

   *Revised 2026-08-24, second pass:* the window these numbers come from is **confounded**
   and is recorded as the description of what the registered rule measured, not as evidence
   for why it is mis-specified. Warm-up presence is perfectly collinear with discriminator
   presence (C1 and C4 have the 2-epoch 2e-5 warm-up; C2 and C5 do not), so the first two
   main-stage transitions are exactly where the learning rate jumps 2e-5 → 1e-4. The
   mis-specification argument rests instead on the **sustained main-stage trend** — neither
   adversarial arm reduces its reconstruction loss (C1 +1.16%, flat; C4 +2.50%, rising) while
   both non-adversarial arms reduce it by ~8% (C2 −7.90%, C5 −7.54%) — and, for C4 alone, on
   the fact that its main-stage start is the run minimum with **0 of 18 main-stage epochs
   below it**, which an LR transient would not produce. **C1 does recover below its start**
   (first at epoch 7, deepest 33.118 at epoch 16, −0.46), so that half of the argument is
   C4's alone. Full statement: AMENDMENT C45-a in
   [phase-c-lpips-registration.md](phase-c-lpips-registration.md).
2. **The rule as written has no threshold.** "Rising" is unquantified; C4's rise over those
   two epochs is +0.28 then +0.37, i.e. 0.5% and 0.7%, against a series whose full-run
   spread is 54.37–56.24. A rule that fires on any positive difference would have stopped
   C1 as well, which the project plainly did not intend.
3. **The conclusion does not depend on it.** Had the run stopped at epoch 5, the registered
   primary comparison would still have fired: the dose-response sweep gives C4 − C5 =
   **+0.441 ± 0.039 (11.3 SE) at epoch 5** and **+0.254 ± 0.040 (6.4 SE) at epoch 2**. The
   effect is present at every epoch measured, at ≥ 6 SE throughout.

The deviation is therefore in the *record*, not in the science: a registered stop condition
was met on its literal reading, the run continued, and the results document reported the
rule as untriggered by applying a different test without saying so. → **entry 26**.

#### C.3 The edge-ratio mask recipe — the disclosure is accurate, the attribution is not verifiable

The registration defines input-silent as "canonical Sobel ≤ 20 on the input render", and the
results document says the five-arm recompute used "the committed B3 definition (mask = input
PNG warped to the 228 grid, BT.601, Sobel ≤ 20; validated against the committed values
before use)".

What is verifiable, and checks out: the edge operator is exactly
`hallucination_analysis.py`'s (`scipy.ndimage.sobel`, `hypot`, threshold 20.0); the mask
source is `C45/warp/input/<stem>.tif`, a 3-band 228×228 uint8 raster, one per chip, 130 of
them; the ratio is `edge_fraction(fake)/edge_fraction(real)` on the same masked pixels;
`skipped_zero_ref` is empty, so all 130 chips contributed.

What is **not** verifiable: whether that mask recipe is what B3 actually did. **B3's harness
was deleted** (corrections-log entry 22), so the committed B3 definition survives only as
prose plus three output numbers. The harness's own docstring is honest about this — it
describes the mask source as "validated against the committed B3 numbers: C2 0.2177 vs
0.218" — but the results document's phrase "the committed B3 definition" states as fact
something that rests on **agreement with one arm out of three**. The other two disagree:
pretrained 1.016 → 1.0195 (+0.0035) and C1 1.023 → 1.0457 (**+0.023**, a 2.2% shift). The
document does disclose this ("the small recompute-vs-committed offsets on pretrained/C1 are
mask-recipe sensitivity … all cross-arm comparisons here use the one-pass recompute"), which
is the right disposition and puts every five-arm comparison on one internally consistent
run. The attribution to a specific cause is a plausible hypothesis that cannot be tested
while B3's harness is gone. Recorded, not corrected; no band depends on it, since C1 clears
"near 1.0" under both values.

### C.4 phase-c

| registered | ran | status |
|---|---|---|
| C1 = adversarial (GAN + L1), Turkey-only pairs | log: `gan_mode vanilla`, `LPIPS False`, 5,577 Turkish pairs | ✓ |
| C2 = L1-only, Turkey-only pairs | log: `[C2] adversarial term zeroed`, `LPIPS False`, 5,577 pairs | ✓ |
| C3 sequential, after the C1/C2 verdict, winning arm + ~20% EU corpus | run and reported separately ([phase-c3-results.md](phase-c3-results.md)); applied to C2, per the registration's sequential design | ✓ |
| R1 — predicted winner C2 by 0.15–0.40 px | scored **and reported as partly falsified**: winner held, magnitude exceeded the band (~1.5×), and the points half explicitly recorded as FALSIFIED | ✓ |
| R2 — improvement correlates with information content, rho ≥ +0.3 | scored and reported; the document goes further and records that R1 and R2 were **mutually inconsistent as registered**, which it caught itself | ✓ |
| R3 — falsifiers of the L1-only hypothesis | scored, reported as not triggered, with the sign of the second falsifier noted as reversed | ✓ |
| R4 — fine-tuning not worth doing | scored, reported as not triggered | ✓ |
| checkpoint discipline: epoch 20 only, `latest_net_G.pth` tensor-equal to `20_net_G.pth` for both arms | **verified here: 20/20 per-epoch checkpoints and 82/82 tensors equal for C1, C2 and C3** | ✓ |
| seed 42, same schedule family, same KARIOS config | preflight lines confirm seed 42 both arms; KARIOS config identity confirmed via the `8eaa5bd8…` hash shared by every downstream package | ✓ |
| C1's stop rule, coarse half: "L1 rising over the first two main-stage epochs" | **G_L1 rose 33.582 → 34.224 at the first of those transitions and the run continued** — the same deviation as C4, in its original instance. C1 then *falls* to 33.858 (rise-then-fall, unlike C4's rise at both), and over the main stage C1 is flat (+1.16%, slope −0.001/epoch) rather than rising, recovering below its start at epoch 7 and reaching 33.118 at epoch 16 | **✗ — entry 26** |

**No registered band in phase-c went scored-but-unreported.** Every one of R1–R4 appears in
the results document with an explicit verdict, including the two that went against the
registration. That is the opposite of the entry-19 failure mode, and it is worth recording
as such: phase-c-results.md reports its own falsifications in the same prominence as its
confirmations.

## D. Evidence layer

`tubitak/data/*` and `tubitak/outputs/*` are gitignored. Pinned here (sha256, 2026-08-24):

```
fede1c5080ed91392c82aa394d9a98fc8764c3925b8d61b9d1bfd808236ab945  C45/C45_per_chip.csv
2a31f70b8e46b3890419adb88f4df699dfd02aab3269060020f6593d4b12eea1  C45/C45_summary.json
0a7525a9082079a74cf4af6e044a02c01eeda278f77cb544d8c8cc488f238a59  C45/C45_edge_ratio.csv
a06f94f37b762c391ebfd41350487784c9553548f32ec46c577e6a70d59c7972  C45/C45_edge_summary.json
45dc469a4284b14eec47351ee8a0392a01598306a8209b90959a8bf70068125a  C45/C45_sweep_per_chip.csv
b57f3844f602b0c7a0d0b47d83ad89d5b206f93856eb97d19ac1215205165ec5  C45/C45_sweep_summary.json
97be08b82678d0985884008cb1e892ae9ed5cc383370e5bf41b425b69f918a99  C45/C45_b2_per_chip.csv
fa1a1b9648491483f9a7a16d9582af30c1e912b262acc161c11d7bd1eb595a4c  C45/C45_b2_summary.json
fb4703b23914dcbc384f491896a4c175d1413760e3ef5428f689d1c1644243a2  B1/B1_per_chip.csv
f407326169ce0679135c6bcc915d50b5846ed71c0f71179be20be058377dcc90  ankara/turkey_karios.csv
44cde1336738c36806c1951568a28b2cbc196ed1deac78f9d6aad0e19988eb8e  outputs/c4_checkpoints/gencp-phase-c-arm-c4-gan-lpips.log
7683ce5527707060736a839f6f683d7475a0a4d3f736173287460a9ca0582d85  outputs/c5_checkpoints/gencp-phase-c-arm-c5-lpips-only.log
c725619eb5acfd6e7586e45dd6b3b3164b7a86785068d6c77e03b4ff6bd49b7f  outputs/c1_checkpoints/gencp-phase-c-arm-c1-gan-l1.log
90e14957add58932fe50bd5b206958175d0d30fd1e22d4cb19229c27fd4c912b  outputs/c2_checkpoints/gencp-phase-c-arm-c2-l1-only.log
```

Evaluated generator weights, pinned so the audited arms cannot be confused with any other
checkpoint:

```
4f06a88edc20a55e3dea5ebf68d63750668848090bdbbb41896b71210903d5f1  c4_checkpoints/checkpoints/C4/latest_net_G.pth
dc190b410621bb59845ea3f9eaa0ddef7d27bd2a5bf0d0a76d25b48810bb8738  c5_checkpoints/checkpoints/C5/latest_net_G.pth
```

`8eaa5bd8cdae066d2580a4105169262f873523cadf0b450a8aa134a31ed4ca84` is the single KARIOS
configuration hash shared by all 1,214 C45 per-run copies and by the committed master
config — the config-identity invariance, pinned as one number, and the same hash the
[B2-B3-audit.md](B2-B3-audit.md) pinned for B1, B2 and pkgA.

The C4/C5 harness is in version control at `tubitak/scripts/c45_eval/` (commit `40cde9b`),
so unlike B3 it needs no hash here: git holds it.

## Verdict — phase-c-lpips

**Leg A PASS.** Zero artifacts predate the registration commit; the whole package —
7 h 03 m of training and 29 minutes of evaluation — sits entirely between `b07e719` and
`6560c8b`, and the eval harness was committed before it produced any number. The documented
wall times are confirmed (C4 3 h 28 m against "≈ 3 h 25 m"; C5 3 h 33 m against "≈ 3 h 40 m").

**Leg B PASS on every cell backed by an artifact:** 1,300 per-chip cells, 25 per-arm summary
cells, 30 paired cells, the interaction, 25 sweep cells and 20 edge-ratio cells all
reproduce from raw. The "fourth digit" claim that validates the extension is true, verified
independently. Three transcription defects (entry 24) and one column with no traceable
origin — the secondary table's SEs — none of which touches a registered band.

**Leg C FAIL on one item.** Every registered band was scored *and* reported, including the
ones that could have gone the other way, and the one registered element that was not run
(Cappadocia recovery) is disclosed in its own section — the entry-19 failure mode does not
recur here. The failure is the stop rule (entry 26): a registered stop condition was met on
its literal reading, the run continued, and the results document reported it as untriggered
by substituting a different test.

**Quotable as:** the primary result, the interaction, the dose-response and the edge-ratio
mechanism are all quotable as registered and reproduced from raw, with the stop-rule caveat
attached. The 20-chip secondary row is quotable for its means, medians, point counts and
paired deltas but **its ± values must not be quoted until they are recomputed** — the
artifact's values (pretrained ± 0.1612, C1 ± 0.0712, C2 ± 0.0409, C3 ± 0.0375, C4 ± 0.0949,
C5 ± 0.0660) are the correct ones.

## Verdict — phase-c

**Leg A PASS.** The registration precedes the first line of C1's training by 3 h 19 m. The
only pre-registration artifacts are the pretrained baseline and the input/stratum files,
which the registration itself names as the baseline to beat.

**Leg B FAIL for C1 and C2.** The pretrained row reproduces (10/12 exact, the two exceptions
being the half-integer point-count convention). Nothing else can be recomputed: no per-chip
C1/C2 artifact from the 2026-08-19/20 scoring run survives, so the ten per-stratum values,
both ALL values, all three paired deltas and R2's correlations have no raw layer. The
Aug-21 seed-42 redraw corroborates every one of them within dropout noise and changes no
verdict — but corroboration by a different draw is not recomputation, and the audit says so
(entry 25).

**Leg C PASS.** Every registered parameter matches the run logs, checkpoint discipline is
verified tensor-by-tensor, and all four registered predictions R1–R4 were scored and
reported with explicit verdicts, including R1's falsified half and R2's self-caught
inconsistency. The one blemish is the stop rule, which is the same inherited item as C4's
(entry 26) and originates here.

**Quotable as:** pre-registered, with the entry-25 caveat — the C1/C2 numbers are
corroborated by a later independent redraw but cannot be recomputed from their own outputs.
The Gate-1 target −0.638 ± 0.054 that the C4/C5 package registers against is one of those
numbers; the same-draw-family value −0.6995 ± 0.0592 **is** fully reproducible and the
results document already publishes both.

## Consequence for the letter

Both halves of Table I clear, with three things that must travel with them: the secondary
row's ± column is wrong and must be replaced from the artifact before any draft quotes it
(entry 24); the phase-C C1/C2 column has no raw layer and the letter should quote the
reproducible same-draw-family value alongside the committed one, as the C4/C5 results
document already does (entry 25); and the stop-rule reading must be stated once, plainly,
rather than left as a rule the record says was untriggered (entry 26).

Base rate after six audited registrations: **three timeline claims verified true** (T1, B2/B3,
phase-c-lpips) plus phase-c, **one falsified** (E3); **five registrations carrying disclosed
protocol deviations** (T1 entry 17, B2 entry 19, B3 entries 20–22, phase-c-lpips entries
24/26, phase-c entries 25/26). The manuscript wording rule is unchanged and further
evidenced.

Remaining in [paper-roadmap.md](paper-roadmap.md) item 1: `phase-c-europe-registration`,
`phase-d-checks-registration`, `packageA-registration`, the four `tool-*registration` files,
T3.
