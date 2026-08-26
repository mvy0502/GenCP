# Package A registration audit — the E3 test applied to the matcher-independence package

Audited 2026-08-26, against
[packageA-registration.md](packageA-registration.md) (commit `18904f0`) and
[packageA-results.md](packageA-results.md) (commit `bab6193`), using the committed artifacts
under `tubitak/data/tool_runs/pkgA/`. Same three legs as the B2/B3 audit: timeline,
reported-versus-raw, registered-versus-executed — plus gates and a verdict.

**Verdict in one line: the timeline is clean and fully reconstructed, every headline number
reproduces from raw to within 0.0008 px, the registered prediction band was applied honestly
against itself — but the results document's cell count "48 of 49" is not reproducible from
the artifact under any counting scheme, and it reports ONE exception where the artifact
contains TWO. Quotable with caveats, and the letter's Table II row needs a correction that is
larger than the count error.**

**The finding that matters most is not about Package A's numbers at all: Package A does not
supply the ORB/AKAZE/MI figures the letter attributes to it.** See §E.

---

## A. Timeline — PASS, fully reconstructed, no gaps

**No computed score predates the registration commit.** The window is reconstructed
end-to-end from filesystem mtimes and commit timestamps, with no unexplained interval.

| event | time (2026-08-21) | evidence |
|---|---|---|
| Registration committed, **with the urban chip lists in the same commit** | **10:44** | `18904f0`; `git show --name-only` confirms `packageA-registration.md` **and** `packageA-urban-chips.csv` |
| Gray conversions written (6 dirs) | 10:51:12 – 10:51:14 | `pkgA/gray/*` mtimes |
| First KARIOS run | **10:52:50** | `karios/ank130/pretrained/bt601/ank_0_10/…KLT_matcher…csv` |
| NCC/phase cells written (26 files) | 10:52:41 – 10:56 | `pkgA/nccphase/*.csv` mtimes |
| Last KARIOS run | 11:04:22 | `karios/eu150/C2/mean/34TCT_1134_00/…csv` |
| Scores, summary, report written | 11:04:38 | `pkgA_scores.csv`, `pkgA_summary.json`, `pkgA_report.txt` |
| Results committed | **11:05** | `bab6193` |

**Every artifact postdates the registration commit by at least seven minutes.** The KARIOS
work is **1,860 output CSVs in 11 min 32 s**, which the results document claims verbatim
("1,860 fresh gray-pair KARIOS runs") and which the artifact count confirms exactly:
`find karios -name "*.csv" | wc -l` = **1860**. That rate (≈2.7 runs/s) is consistent with the
independently measured KARIOS throughput elsewhere in this project (520 runs in 170 s during
the seed-block evaluations, ≈3.1/s on an idle machine).

**The reused cache is declared, not hidden.** The RGB-KLT column is not fresh: it re-uses
regC/task3 KARIOS output that predates this registration. The registration declares this in
advance ("the archived fakes and the project's own Sentinel-2 reference warps … unchanged;
Render path: none re-run"), and the results document states the verification
("every reused RGB-KLT per-chip median re-derives exactly from the KARIOS CSVs on disk").
**This is the one place where scored numbers predate the registration, and it is registered
as reuse rather than presented as new work.** Correct handling.

**No gaps.** Unlike B2's 26-minute window, this one needed no reconstruction: the mtimes are
monotone and continuous from 10:51 to 11:04.

---

## B. Reported tables vs raw outputs — PASS, max |diff| = 0.0008 px

Every headline number in [packageA-results.md](packageA-results.md) was **recomputed from
`pkgA_scores.csv` (6,510 per-chip rows)**, not read back from `pkgA_report.txt`. Paired
per-chip differences, SE = sd/√n, exactly as the registration specifies.

| document claim | recomputed from raw | Δ |
|---|---|---|
| Ankara-130 Δ(C2−C1) **−0.70 ± 0.06** (RGB KLT) | −0.6995 ± 0.0592, n = 130 | 0.0005 |
| Ankara-130 (BT.601 KLT) | −0.7023 ± 0.0622, n = 130 | 0.0003 |
| Ankara-130 **−1.01 ± 0.17** (BT.601 NCC) | −1.0075 ± 0.1709, n = 130 | 0.0005 |
| EU-150 **−0.47 ± 0.05** (RGB KLT) | −0.4679 ± 0.0539, n = 150 | 0.0001 |
| EU-150 **−1.15 ± 0.15** (BT.601 NCC) | −1.1494 ± 0.1483, n = 150 | 0.0004 |
| Phase corr. **−5.27 ± 1.00** (ank130 BT.601) | −5.2682 ± 0.9962, n = 130 | 0.0002 |
| Phase corr. **−2.95 ± 1.04** (eu150 BT.601) | −2.9462 ± 1.0440, n = 150 | 0.0002 |
| Ankara-30 prod C3−C2 **−0.02 ± 0.09** (RGB KLT) | −0.0187 ± 0.0888, n = 30 | 0.0003 |
| Ankara-30 ovp **−2.20 ± 1.43** (BT.601 phase) | −2.2038 ± 1.4250, n = 30 | 0.0002 |
| Ankara-30 prod C2−pretrained **−0.84** (RGB KLT) | −0.8418 ± 0.2144, n = 30 | 0.0008 |
| Urban Ankara-130 BT.601 KLT **C2 0.591 / C1 0.764 / pre 1.349** | 0.591 / 0.764 / 1.349 | exact |

**max |diff| across all columns: 0.0008 px**, entirely attributable to rounding at the
printed precision. **Leg B passes.**

**The apparent 0.47-versus-0.43 discrepancy in the document is not a defect.** The results
text quotes EU-150's KLT margin as −0.47 in one sentence and +0.43 in another. These are two
different conditions: **−0.4679 is RGB KLT** and **+0.4341 is BT.601 KLT**, and the second is
the correct one for the prediction band, which the registration requires to be judged "on the
same chips, same conversion" as the NCC cell. The arithmetic is right. **The wording does not
say which conversion each belongs to**, and a reader comparing the two sentences will read a
contradiction. Minor, recorded as §C-3.

---

## C. Registered protocol vs what ran

### C-1 — the registered secondary band ran, and its one adverse cell was not reported

**Registered (A1):** primary = BT.601 luminance; **secondary = unweighted mean of the three
bands.** Both ran. The artifact carries all seven conditions per set — `rgb|klt`,
`bt601|klt`, `mean|klt`, `bt601|ncc`, `mean|ncc`, `bt601|phase`, `mean|phase` — and the
`mean` band is present in every one of the 1,860 KARIOS runs and 26 NCC/phase cells.

**Reported:** the results document folds the secondary into aggregate phrasing ("all 7",
"two band conversions") and never breaks it out. That is acceptable on its own.

**What is not acceptable:** the single place where the secondary band produces an adverse
cell is the one place the document does not carry it. See §C-2 — **the unreported exception
is a `mean` band cell.** This is the same shape as B2's corrections-log **entry 19** (the
registered RGB half ran and was never reported), in the milder form where the half was
summarised rather than omitted, but the adverse cell within it was dropped.

### C-2 (LOAD-BEARING) — one exception is reported; the artifact contains two

**The results document says, twice:**

> "48 of 49 condition cells rank C2 first or tie it with C3 within noise"

> "the single exception (EU-150 urban, phase corr.) | C1 by −0.03 ± 0.21 — noise, no verdict"

**The artifact contains two cells in which C1 — not C3 — ranks ahead of C2**, both at EU-150
urban, both phase correlation, one per band:

| set | scope | condition | winner | Δ(winner − C2) | n | ≥ 2 SE? | reported? |
|---|---|---|---|---|---|---|---|
| eu150 | urban | **BT.601 \| phase** | C1 | −0.0246 ± 0.2080 | 26 | **No** | **yes** — this is the "−0.03 ± 0.21" |
| eu150 | urban | **mean \| phase** | C1 | −0.0092 ± 0.2168 | 26 | **No** | **NO — unreported** |

Confirmed independently in `pkgA_report.txt`, which prints both:
`bt601|phase … rank C1>C2 D=-0.025+-0.208` and `mean|phase … rank C1>C2 D=-0.009+-0.217`.

**Neither reaches 2 SE, so under the registered rule neither is a claimed ordering change,
and the package's conclusion is unaffected.** What is wrong is the word "single" and the
count. The correct statement is **two exceptions, both at EU-150 urban under phase
correlation, one in each band, both far below the 2 SE threshold.**

**Why this is load-bearing rather than cosmetic:** "48 of 49" is quoted **verbatim in the
letter's Table II** as the evidence that the matcher choice does not drive the result. A
reviewer who recomputes it will not get 48, will not get 49, and will find a second exception
the paper did not mention. The number is doing rhetorical work in the manuscript that the
artifact does not support.

### C-3 — the denominator "49" is not reproducible under any counting scheme

The harness emits **no cell count**. `pkgA_summary.json` contains per-condition statistics and
per-condition ordering verdicts, but no total and no "48/49". The figure is a hand-count in
the prose, and it cannot be reconstructed. Schemes tried, exhaustively:

| counting scheme | total | C2-not-top | result |
|---|---|---|---|
| 4 sets × 2 scopes (full + urban) × 7 conditions | **56** | 6 (4 are C3 ties) | 50/56, or 54/56 counting C3 ties as passes |
| the same, excluding the 14 Ankara-30 urban cells (n = 2, pre-declared no-verdict) | 42 | 2 | 40/42 |
| ordering verdicts vs the RGB\|KLT baseline only (6 conditions × 4 full sets) | 24 | 0 | 24/24 |
| 7 conditions × 7 "groups" (treating the two Ankara-30 urban sets as one) | 49 | 2 | **47/49** |

**The last scheme is the only one that yields a denominator of 49**, and under it the numerator
is **47, not 48** — precisely because of the unreported second exception in §C-2. That is the
most probable origin of the figure: the author counted 49 groups correctly and missed one
adverse cell. **No scheme produces 48 of 49.**

### C-4 — minor precision items, no number changes

- **The 0.47/0.43 labelling** (§B): both values are correct; neither sentence names its band
  conversion. Wording should carry the conversion, as binding sentence 12 already requires for
  n.
- **Urban n labelling.** The registration pre-declared Ankara-130 urban n = 20, EU-150 n = 26,
  Ankara-30 n = 2. The artifact gives exactly 20, 26 and 2. **Verified against the committed
  chip list**, whose `urban` flag column yields 20 of 130 Ankara chips and 26 of 150 EU chips.
  No drift.
- **The −0.97 versus −0.84 production restatement.** The registration anticipated
  "C2 − pretrained ≈ −0.97 px on production inputs"; this package measures −0.84 on its own
  Ankara-30 production sample and points at −0.97 as the Task-3 sample's figure. Both are
  disclosed in the same sentence and neither is presented as the other. **No defect** — but a
  paper quoting either must name which sample it is.

---

## D. Gates and registered bands — applied literally, and against the author's own prediction

**This is the leg where entries 26 and 27 came from elsewhere in the project. Nothing of that
shape is present here.**

**The registered prediction failed, and the failure is reported in the direction that
strengthens the result rather than being quietly re-read.** Registered in advance: NCC rewards
sharpness, so C2's blur should cost it more than under KLT; **"closes"** = Δ(C1−C2) under NCC
shrinks to ≤ 50% of its KLT value; **"overtakes"** = ≤ −0.10 px at ≥ 1 SE; **C2 holding ≥ 75%
of its KLT margin** = the restraint result is materially stronger.

Measured, all eight set × band combinations:

| set | band | KLT margin | NCC margin | band triggered |
|---|---|---|---|---|
| ank130 | BT.601 | +0.702 ± 0.062 | +1.008 ± 0.171 | ≥ 75% (STRENGTHENED) |
| ank130 | mean | +0.688 ± 0.052 | +0.994 ± 0.168 | ≥ 75% (STRENGTHENED) |
| ank30_prod | BT.601 | +0.720 ± 0.163 | +0.944 ± 0.343 | ≥ 75% (STRENGTHENED) |
| ank30_prod | mean | +0.585 ± 0.139 | +1.013 ± 0.376 | ≥ 75% (STRENGTHENED) |
| ank30_ovp | BT.601 | +0.818 ± 0.111 | +0.916 ± 0.393 | ≥ 75% (STRENGTHENED) |
| ank30_ovp | mean | +0.797 ± 0.150 | +0.993 ± 0.408 | ≥ 75% (STRENGTHENED) |
| eu150 | BT.601 | +0.434 ± 0.046 | +1.149 ± 0.148 | ≥ 75% (STRENGTHENED) |
| eu150 | mean | +0.477 ± 0.053 | +1.170 ± 0.151 | ≥ 75% (STRENGTHENED) |

**8 of 8 in the strengthening band, on the registered comparison (same set, same
conversion).** The prediction was wrong in every cell and the document says so plainly
("The sharpness-helps-NCC intuition was wrong"). **A registered prediction that failed, was
reported as failed, and whose pre-committed band was then applied unchanged — this is the
behaviour the registration apparatus exists to produce, and it is worth recording as a pass
rather than passing over in silence.**

**The 2 SE ordering rule was applied literally, including where it cost the author a cleaner
story.** Every flip is reported as "rank unstable within noise" with its Δ and SE, and none is
claimed as an ordering change. The four C3-ahead-of-C2 cells at Ankara-30 are handled exactly
as the registration's tie language requires.

**No stop rule exists in this registration**, so there is no entry-26-shaped gate to check.

---

## E. THE FINDING THAT REACHES THE LETTER — Package A does not supply Table II's numbers

**This is the most consequential item in the audit and it is not a defect in Package A.** It
is a mis-attribution in the letter skeleton.

The letter's Table II row reads:

> | Optimising the evaluation metric | matchers from three families | **ORB −0.613 ± 0.135
> (n = 29 intersection), AKAZE, MI −1.260 ± 0.261 (lower bound); ordering preserved in 48 of
> 49 cells** | refuted |

**Package A's registered matchers are KLT, NCC template grid, and phase correlation.** It
never ran ORB, AKAZE or mutual information, and no such number exists anywhere in
`pkgA_scores.csv`, `pkgA_summary.json` or `pkgA_report.txt`.

**The ORB/AKAZE/MI figures are B3's**, from the descriptor-family package, verified in
[B2-B3-audit.md](B2-B3-audit.md) (leg-B reproduction at −0.6130 ± 0.1350, −0.1483 ± 0.0484,
−1.2600 ± 0.2613) and reported in [headline-results.md](headline-results.md). **The
"48 of 49" is Package A's.** The row therefore fuses two registrations — different matchers,
different chip sets, different n, different audits — into one apparent test, and the phrase
"matchers from three families" is ambiguous between B3's three descriptor families and Package
A's three matcher families.

**The three caveats the row already carries are B3's, and all three check out**, but they must
travel with B3's half and not be read as qualifying Package A's:

1. **ORB Δ rests on a 29-chip intersection.** Confirmed — B2-B3 audit finding **m1**: the Δ is
   paired over the 29 chips where both C2 and C1 matched, while headline-results prints
   "C2 53/130" two clauses later, and "a reader will read 53 as the support for −0.613".
   AKAZE ank130 rests on **11** paired chips and eu150 AKAZE on **3**. **Binding sentence 12
   exists for exactly this and must be applied to this row.**
2. **MI is a lower bound.** Confirmed — corrections-log **entry 21**: the registered parabola
   subpixel refinement never ran, and the ±8 px grid censors 15.8% at the bound. The censoring
   is heavier for the worse arms (pretrained 27.7%, C1 17.7%, C2 8.5%), so it **compresses**
   the margin toward zero. −1.260 ± 0.261 is a floor, not an estimate.
3. **Delta-versus-matched-count n labelling.** Confirmed as a live requirement, unmet in the
   current row wording.

**Recommended correction to the row (for review, not applied):** split it into two rows, or
state both provenances in the cell — B3 supplies the descriptor-family deltas with their
paired n and the MI lower-bound caveat; Package A supplies the KLT/NCC/phase ordering
stability with the corrected count. **And correct the count.**

---

## F. Evidence layer

| artifact | content | status |
|---|---|---|
| `pkgA_scores.csv` | 6,510 per-chip rows: set, arm, band, matcher, chip, med, n | present, complete, reproduces every headline |
| `pkgA_summary.json` | per-condition statistics and ordering verdicts | present; **contains no cell count** |
| `pkgA_report.txt` | human-readable full table, all 7 conditions × all sets, both exceptions printed | present |
| `karios/` | **1,860** KLT run directories | complete, count matches the claim exactly |
| `nccphase/` | 26 NCC/phase cells | complete |
| `gray/` | 6 conversion directories | complete |
| `packageA-urban-chips.csv` | 280 rows, `urban` flag → 20 Ankara + 26 EU | committed in the registration commit |

**Nothing is missing and nothing had to be reconstructed.** Contrast B3, whose harness was
lost (corrections-log entry 22): Package A's full evidence layer survives, and the audit
recomputed from raw rather than from the report at every step.

---

## Verdict

**QUOTABLE WITH CAVEATS.**

**What is quotable as registered and reproduced from raw:**

- Every Δ, SE and per-arm value in the results document — all reproduce to within 0.0008 px.
- The rank-stability conclusion: **the arm ordering never changes outside noise** across two
  matcher families, a third global-shift method, both registered band conversions, and the
  urban subset. This is the package's actual result and it survives the audit intact.
- The registered prediction outcome: C2 holds **more** than 100% of its KLT margin under NCC
  in all 8 set × band combinations, so the restraint result is not conditioned on the KLT
  matcher. Pre-committed band, applied unchanged.
- The urban headline C2 0.591 / C1 0.764 / pretrained 1.349 px (n = 20, BT.601 KLT), exact.

**What is NOT quotable without correction:**

- **"48 of 49" — not reproducible. Do not quote it.** The defensible restatements are
  "**47 of 49**" under the group counting that yields the 49, or "**two exceptions, both at
  EU-150 urban under phase correlation, both far below the 2 SE threshold**", which is what the
  data supports without needing a denominator at all. **The second phrasing is recommended:
  it is exactly true, and it does not rest on a counting convention the artifact never
  recorded.**
- **"the single exception" — false. There are two.**

**Which Table II row loses evidence, and how much:** the matcher-independence row does **not**
lose its verdict. The "refuted" verdict for "optimising the evaluation metric" stands on B3's
three descriptor families (with their caveats) **and** on Package A's ordering stability (with
the corrected count) — the two together are stronger evidence than the row currently claims,
not weaker, because they are two independent registrations rather than one. **What the row
loses is its current wording**, which mis-attributes half its numbers and quotes a count that
cannot be reproduced.

**Base rate note.** Five registrations audited before this one; every one found something.
This makes six. The findings here are a miscount and a dropped adverse cell rather than a
structural defect, which is the mildest outcome of the six — and the package's own gate
behaviour (§D) is the best of the six.

---

## Corrections-log entries DRAFTED FOR REVIEW — not applied

`corrections-log.md` is untouched. Proposed as entries **30** and **31**, in the log's
existing column format.

> **| 30 | 26 Aug | [packageA-results.md](packageA-results.md): "48 of 49 condition cells rank
> C2 first or tie it with C3 within noise" and "the single exception (EU-150 urban, phase
> corr.)" | **The count is not reproducible and the exception count is wrong.** The harness
> emits no cell total; `pkgA_summary.json` has none. Enumerating the artifact gives **56**
> condition cells (4 sets × 2 scopes × 7 conditions), or 42 excluding the pre-declared
> no-verdict Ankara-30 urban cells, or 24 counting only ordering verdicts against the RGB|KLT
> baseline. The only scheme yielding a denominator of 49 is 7 conditions × 7 groups, and under
> it the numerator is **47, not 48**. Separately, the artifact contains **two** cells where C1
> ranks ahead of C2, not one: EU-150 urban `bt601|phase` (C1 by 0.0246 ± 0.2080, reported as
> "−0.03 ± 0.21") and EU-150 urban `mean|phase` (C1 by 0.0092 ± 0.2168, **unreported**). Both
> are far below the registered 2 SE threshold, so **no registered ordering change is claimed
> either way and the package's conclusion is unaffected** — but "48 of 49" is quoted verbatim
> in the letter's Table II, where a reviewer recomputing it will find neither the count nor the
> single exception. The unreported cell is in the registered **secondary** band, the same shape
> as entry 19 in milder form | Results document to read "**two exceptions, both at EU-150 urban
> under phase correlation, one per band, both far below 2 SE**" and drop the unreproducible
> denominator; letter Table II corrected with it. Every other number in the package reproduces
> from raw to within 0.0008 px | [packageA-audit.md](packageA-audit.md) §C-2, §C-3 |**

> **| 31 | 26 Aug | [letter-skeleton.md](letter-skeleton.md) §3 Table II, matcher-independence
> row: "matchers from three families | ORB −0.613 ± 0.135 (n = 29 intersection), AKAZE, MI
> −1.260 ± 0.261 (lower bound); ordering preserved in 48 of 49 cells" | **The row fuses two
> different registrations into one apparent test.** Package A's registered matchers are KLT,
> NCC template grid and phase correlation; it never ran ORB, AKAZE or MI, and no such number
> exists in any Package A artifact. The ORB/AKAZE/MI deltas are **B3's** descriptor-family
> results ([B2-B3-audit.md](B2-B3-audit.md), [headline-results.md](headline-results.md)); only
> the ordering count is Package A's. "Matchers from three families" is ambiguous between B3's
> three descriptor families and Package A's three matcher families. The three caveats the row
> carries (ORB's 29-chip paired intersection, MI's lower bound from the never-run subpixel
> refinement, the delta-versus-matched-count n) are all **B3's** and all verified as still
> true, but they qualify only B3's half | Row split, or both provenances named in the cell,
> with each half carrying its own n and caveats. **The verdict "refuted" is unaffected and is
> in fact better supported than the row claims** — two independent registrations rather than
> one | [packageA-audit.md](packageA-audit.md) §E |**
