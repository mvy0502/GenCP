# Phase D registration audit — the E3 test applied to the alternative-explanations package

Audited 2026-08-26 against
[phase-d-checks-registration.md](phase-d-checks-registration.md) (commit `8b360f8`,
2026-08-20 10:18), [phase-d-ratio-addendum.md](phase-d-ratio-addendum.md) (`3da4efd`),
[phase-d-results.md](phase-d-results.md) (`f836f84`), and
[gcp-veto-rule-results.md](gcp-veto-rule-results.md) (`d3e7e09`). Same legs as the B2/B3 and
Package A audits.

**Verdict in one line: the registration discipline in this package is the best in the project
— a held-out gate failed and was recorded as a failure with nothing adjusted, and two
registered fallback sentences were used exactly as written — but LEG C CANNOT BE RUN. Six of
the seven checks and the veto rule have NO surviving artifact of any kind, the per-chip files
the results documents name do not exist, and the claim that they are "regenerable end-to-end
from committed scripts" is false because those scripts are not committed either.**

**Both Table II rows that Phase D feeds — the blur row and the corrected-georeferencing row —
rest entirely on numbers that cannot be re-derived from anything in this repository.** That is
the finding, and it is an entry-22-shaped one.

---

## A. Timeline — PASS on what can be checked, UNVERIFIABLE for check 3

| event | time (2026-08-20) | commit |
|---|---|---|
| Checks 1–7 and the veto rule registered | **10:18** | `8b360f8` |
| DEM ruggedness labels committed **before scoring** | **10:24** | `c97dbae` |
| Europe + Phase D results | 10:47 | `f836f84` |
| Veto rule result | 10:48 | `d3e7e09` |

The ratio addendum (`3da4efd`, 2026-08-19 23:41) predates its own results, correctly.

**Check 2's discipline is verified and exemplary.** The registration required the label list to
be "computed and committed **before** any KARIOS number for those chips is looked at". The
labels were committed at 10:24, twenty-three minutes before the results commit, and the
committed `docs/dem-ruggedness-labels-36SXJ.csv` is **byte-identical** (5,074 bytes, same
mtime) to the working copy at `data/tiles36SXJ/dem_ruggedness_labels.csv`. The DEM tiles
themselves were fetched 10:22–10:23. **This is the one check in the package whose ordering is
provable from artifacts rather than asserted.**

**The underlying KARIOS runs predate the registration, correctly and by design.** The
Cappadocia and Tuz runs are dated 2026-08-19 13:17–13:21, the EU hold-out 2026-08-19
23:37–23:39, Ankara 2026-08-18/19. These are the pretrained-arm scorings the checks *re-score
against a common baseline*; the registration's own wording ("Ankara's pretrained results are
**now re-scored** per stratum against the SAME fresh baseline") declares the reuse. **This is
not a timeline violation**, on the same reasoning that permits Package A's reuse of the
regC/task3 RGB-KLT cache.

### The gap: 29 minutes, and one claim that cannot be checked

**Seven checks and a fit-plus-held-out veto experiment were registered at 10:18 and reported
at 10:47.** That window has to contain: a per-stratum re-scoring of Ankara against a 568-chip
baseline; a DEM fetch, slope computation and labelling (10:22–10:24, verified); a corpus
census over 5,577 training pairs; a four-level point-floor sweep across five result sets; a
two-band FFT analysis over both arms at four sites; a 10,000-draw stratified bootstrap; a
systematic/scatter decomposition of 568 chips; **a spectral sigma fit plus a full blur-control
re-render and re-score of 568 + 130 chips**; and a veto-rule fit with a held-out evaluation.

**The blur control is the item that does not obviously fit.** It requires blurring 568
pretrained outputs, re-warping and re-running KARIOS on them — on the order of the 1,860-run
Package A workload that took 11.5 minutes — plus the spectral fit, inside a 29-minute window
shared with everything above.

**I cannot resolve this, and the reason is the finding in §C: no artifact survives.**
[phase-c-europe-results.md](phase-c-europe-results.md) asserts that "the third (mechanical
blur) was added and registered **before its control ran**". **That assertion rests on nothing
this repository can check.** There is no blur output, no fitted-sigma record, no timestamped
intermediate, no script. Contrast B2, whose 26-minute window was *fully reconstructed* from
surviving artifacts, and Package A, whose window is monotone in the mtimes. **Here the claim
is credible and unverifiable, and it must be recorded as unverifiable rather than as
verified.**

---

## B. Registered versus executed

| # | check | ran? | reported? | where |
|---|---|---|---|---|
| 1 | Ankara re-scored vs the 568-chip baseline | yes | yes | phase-d-results.md:32–44 |
| 2 | DEM-ruggedness badlands rule | yes | yes | phase-d-results.md:48–60 |
| 3 | Restraint vs mechanical blur | asserted | yes, **elsewhere** | **phase-c-europe-results.md:33–39** |
| 4 | Salt in the fine-tuning corpus | yes | yes | phase-d-results.md:67–71 |
| 5 | Minimum-point-count floors | yes | **partially** | phase-d-results.md:19–20, 72–75 |
| 6 | Periodicity, both arms | yes | yes | phase-d-results.md:98–105 |
| 7a | Bootstrap CI on R | yes | **partially** | phase-d-results.md:24–30 |
| 7b | Systematic vs scatter decomposition | asserted | yes, **elsewhere** | **phase-c-europe-results.md:28–32** |
| — | GCP veto rule | yes | yes, in full | gcp-veto-rule-results.md |

### B-1 (minor) — two checks are reported outside the package that registered them

Checks **3** and **7b** have **no reported outcome anywhere in `phase-d-results.md`,
`phase-d-ratio-addendum.md` or `gcp-veto-rule-results.md`.** The words "blur", "sigma",
"systematic", "scatter" and "decompos" do not occur in any of the three. Both outcomes are
reported in [phase-c-europe-results.md](phase-c-europe-results.md), which is a different
document committed in the same commit.

Meanwhile `phase-d-results.md:9` describes the registration as "(verification checks 1–7,
**run and reported** before this document was written)" without saying that two of the seven
are reported elsewhere. **Nothing is hidden and both outcomes are genuinely published**, but a
reader auditing checks 1–7 against the document that claims them will find five, and the two
missing ones are the two that feed Table II. Cross-references should be added.

### B-2 (LOAD-BEARING) — two registered reporting requirements were not met

**Check 5's Ankara arm is missing.** The registration names the sets explicitly: "Every
headline paired difference in this package (**Europe, Ankara, Cappadocia, Tuz Gölü**, and the
salt/non-salt splits) is recomputed under minimum point-count floors of 0, 10, 20, 30 …
reported side by side." Floor sensitivity is reported for Europe (`phase-c-europe-results.md`
20–21), and for Cappadocia/Tuz/salt (`phase-d-results.md` 19–20, 72–75). **No floor-sensitivity
line for Ankara exists in any document.** Either it ran and was not reported, or it did not
run; **with no artifact, the audit cannot say which**, and that is itself the entry-19 shape in
its unresolvable form.

**Check 7a's per-stratum gains are missing.** The ratio addendum requires the per-stratum gains
to be "reported alongside R **so the aggregation hides nothing**". Only the aggregate
(1.188 / 1.258 = 0.945) is published. The stated purpose of the requirement is defeated by
its omission.

### B-3 — one registered conditional was never explicitly discharged

Check 7b's registration says: "If the improvement is mostly scatter, the georeferencing
candidate is not doing the work and **restraint/blur (check 3) carries the burden**." The
improvement *was* mostly scatter (~86%). `phase-c-europe-results.md:40` then asserts restraint
SUPPORTED — but never states that it is now carrying a burden transferred from a refuted
candidate. **The conclusion is the registered one; the reasoning step the registration
required to be made explicit was not made explicit.** Minor, but it matters here because
check 3 is the check whose evidence has vanished: the burden was transferred onto the least
verifiable result in the package.

### B-4 — nothing ran that was not registered

No unregistered analysis is reported. The veto rule, checks 1–7 and the ratio are all
registered in advance. **No reverse-direction finding.**

---

## C. Reproduction — CANNOT BE RUN. This is the package's central defect.

**Standing instruction followed: where an artifact is missing I say so rather than
reconstructing it.** Nothing below was regenerated.

### C-1 — no artifact exists for six of seven checks or the veto rule

| check | artifact | status |
|---|---|---|
| 1 | Ankara per-stratum re-scoring | **NOT FOUND** |
| **2** | `dem_ruggedness_labels.csv` + DEM tiles | **FOUND, committed, byte-verified** |
| 3 | blur control / fitted sigma / `blur_control_per_chip.csv` | **NOT FOUND** |
| 4 | corpus census | **NOT FOUND** |
| 5 | point-floor sweep | **NOT FOUND** |
| 6 | FFT periodicity | **NOT FOUND** |
| 7a | bootstrap draws | **NOT FOUND** |
| 7b | `eu_decomposition_per_chip.csv` | **NOT FOUND** |
| veto | `veto_features.csv`, `veto_rule.py` | **NOT FOUND** |
| — | `eu_per_chip.csv` | **NOT FOUND** |

Verified by direct filesystem search: all five named files return zero hits repository-wide.

### C-2 — the "regenerable from committed scripts" claim is FALSE

The two documents justify the absence of the artifacts by asserting regenerability:

> `phase-c-europe-results.md:63–64` — "Per-chip data: `eu_per_chip.csv`,
> `blur_control_per_chip.csv`, `eu_decomposition_per_chip.csv` (session scratchpad;
> **regenerable end-to-end from committed scripts and registrations**)."

> `gcp-veto-rule-results.md:29` — "Features and script: `veto_features.csv`, `veto_rule.py`
> (session scratchpad; **regenerable**)."

**Neither is true as stated.** `git ls-files` finds **no committed script** for blur, low-pass,
sigma fitting, spectral matching, decomposition, bootstrap, periodicity/FFT, point-count
floors, or the veto rule. The only repository hit for any of those terms is the veto **results
prose** itself. The registrations describe the *procedures* in enough detail that someone could
write new code, but that is re-implementation, not regeneration, and it would not reproduce the
published numbers — it would produce new ones.

**This is corrections-log entry 22's failure mode (B3's harness deleted), recurring in a
package that had already learned the lesson**, and here it is worse in one respect: entry 22
cost four *parameters*; this costs the *numbers themselves*.

### C-3 — everything under `tubitak/data/` is untracked

`.gitignore:54` is `tubitak/data/*`, and `git ls-files tubitak/data` returns exactly one path,
`.gitkeep`. **No Phase D computation is under version control at all.** Package A's artifacts
survive only because they are on this machine's disk, not because the repository holds them —
the same is true of every `tool_runs/` directory in the project. This is a standing structural
exposure, not a Phase D defect, but Phase D is where it has already caused loss.

### C-4 — what DID reproduce, and one partial result worth recording

**Check 2 partially reproduces.** From the committed labels and the surviving 130 Cappadocia
KARIOS runs:

- Label counts reproduce **exactly**: 33 badlands, 65 flat, 32 buffer — matching the reported
  "33 badlands / 65 flat".
- 130 of 130 chips scored; no chip missing.
- The reported badlands SE of **±0.118 reproduces exactly** from the badlands chips' own
  residual spread (0.118).

**What does not reproduce, and is not reconstructed:** the matched-gap *means*
(badlands +0.436, flat +0.449) subtract a per-stratum EU baseline median that requires the
568-chip stratification and the canonical Sobel measure recomputed from input renders. The
intermediate is gone. **I did not rebuild it.**

**One partial finding, reported because it bears on the conclusion rather than against it.**
The *raw* pretrained residual difference between the two groups is **−0.522 ± 0.148 px**
(badlands better), against the reported matched-gap difference of −0.013 ± 0.141. The two are
different statistics and do not contradict each other — but the size of the collapse means
**essentially the entire raw badlands-versus-flat difference is attributable to the
information-density stratum mix, not to landform.** That strengthens the document's "no
morphological signature" conclusion and is worth stating in it, since a reader computing the
raw difference will find −0.52 and wonder.

---

## D. Gates — the strongest gate discipline in the project

**This is the leg where entries 26 and 27 came from. Phase D is the opposite case, and it
should be said plainly.**

**The veto rule failed its held-out acceptance gate and was recorded as a failure with nothing
adjusted.** Registered: "the rule is judged acceptable only if catch ≥ 2× loss on the held-out
site", threshold "fixed on the fit set before Cappadocia is touched". Fit set: catch 0.872,
loss 0.427 — passes. Held out: catch 1.000, **loss 0.919** — **FAILS**, and the rule vetoes
127 of 130 chips. The results document is titled "**held-out result: FAIL (recorded as
registered)**" and states: "per the standing rules this result stands as a FAIL; **no threshold
is adjusted after seeing the held-out outcome**". It then diagnoses the failure as being in the
rule form and the selection criterion, notes the predictors do carry signal (AUC 0.843), and
routes any revision to a **new registration with a fresh held-out evaluation**.

**That is exactly what AMENDMENT C45-a was criticised for not being** (a threshold set after
seeing the arms). Recorded here as a pass, and as the model the project should cite when it
next needs one.

**Two registered fallback sentences were used as written, not improved upon:**

- **Check 7a.** Registered: "If the interval is wide, the committed sentence becomes 'above the
  registered 0.7 threshold', **not** 'about 95%'." The interval came out wide
  ([0.730, 1.184]) and R = 0.945 — the tempting sentence was available and was not used. The
  document says "above the registered 0.7 threshold … and is statistically indistinguishable
  from full transfer". **Correct.**
- **Check 1.** Registered three outcomes: ≈ +0.4…+0.5 → explanation (b); ≈ 0 or negative →
  explanation (a); **intermediate → "reported per stratum; no single-word summary is
  permitted."** Ankara came out at **+0.226**, squarely intermediate. The document reports a
  per-stratum gradient and explicitly refuses the single word: "A gradient, not a uniform
  level". **Correct.**

**Check 2's power condition was met, not waived.** Registered: "If the rule still yields < 25
labeled badlands chips, the test is reported as underpowered, not scored." It yielded 33.
Scored legitimately.

**Check 3's bands were applied as written.** Registered: ≥ 60% recovered kills the restraint
claim; ≤ 25% supports it. Measured −6.1% (Europe) and +1.7% (Cappadocia) → ≤ 25% → supported.
**The band was applied correctly; what cannot be checked is the number it was applied to.**

**No gate in this package fired and was ignored.** Nothing of the entry-26/27 shape is present.

---

## E. Verdict

**NOT QUOTABLE WITHOUT A PROVENANCE CAVEAT — and the caveat is larger than any this project
has yet attached to a live number.**

**What is quotable as registered and verified:**

- **Check 2 in full.** Labels committed before scoring, byte-verified, counts reproduce
  exactly, one SE reproduces exactly, the power condition was met. The "no morphological
  signature" conclusion stands and is the best-evidenced result in the package.
- **The veto-rule FAIL.** Fully reported, honestly diagnosed, nothing adjusted. Quotable as a
  negative result and as a methodological example.
- **Check 1 and check 7a's headline**, with the caveat that their intermediates are gone: the
  conclusions used the registered fallback wording correctly, which is checkable from the
  documents even though the numbers are not.

**What is NOT quotable without disclosure, and which Table II rows are affected:**

**The blur row** — *"It is blur, not restraint | low-pass the adversarial arm to match the
L1-only spectral profile (fitted σ = 0.45) | recovers −6.1% (Europe) / +1.7% (Cappadocia) of
the gain; support band was ≤ 25% | refuted"*. **Every number in this row is unreproducible.**
No blur output, no sigma record, no per-chip file, no script. The row's verdict may well be
right — the registered band was applied correctly to whatever was computed — but **nothing in
this repository can confirm what was computed.**

**The corrected-georeferencing row** — *"decompose the European gain | ~86% is scatter
reduction; the systematic component slightly worsened | refuted"*. Same position:
`eu_decomposition_per_chip.csv` does not exist and no decomposition script is committed.

**These two rows are half of Table II's four refuted candidates.** The row that survives
intact is the cold-discriminator sweep; the matcher row is Package A's and B3's (see
[packageA-audit.md](packageA-audit.md) §E); the mediation row is already marked "narrowed" and
carries entry 20.

**Recommendation, and it is cheap.** The registrations specify both procedures in full detail —
the sigma fit, the spectral matching, the recovered-fraction formula, the decomposition. **Re-run
them, commit the per-chip outputs and the scripts, and verify the published numbers.** If they
reproduce, the rows are quotable outright and the caveat disappears. If they do not, that is a
finding the paper needs before submission rather than after. **This is the only Table II row
pair whose evidence can be restored by re-running rather than by re-registering**, and until
it is done the standing rule — an unaudited number does not enter the letter — should be read
as: *an unreproducible number does not enter the letter without saying so in the letter.*

**Base rate.** Seven registrations audited; seven found something. Phase D's findings are the
most severe in kind (evidence loss) and the least severe in conduct (no gate ignored, no
threshold moved, two fallback sentences honoured, one held-out failure published as a
failure). **Those two facts belong in the same sentence whenever this package is described.**

---

## Corrections-log entries DRAFTED FOR REVIEW — not applied

`corrections-log.md` is untouched. Proposed as entries **32**, **33** and **34**.

> **| 32 | 26 Aug | [phase-c-europe-results.md](phase-c-europe-results.md) §63–64 and
> [gcp-veto-rule-results.md](gcp-veto-rule-results.md) §29: the per-chip artifacts are declared
> "session scratchpad; **regenerable end-to-end from committed scripts and registrations**" |
> **The artifacts are gone and the scripts were never committed, so the regenerability claim
> that justified not committing them is false.** `eu_per_chip.csv`, `blur_control_per_chip.csv`,
> `eu_decomposition_per_chip.csv`, `veto_features.csv` and `veto_rule.py` return zero hits
> repository-wide; `git ls-files` finds no committed script for blur, sigma fitting, spectral
> matching, decomposition, bootstrap, FFT periodicity, point-count floors or the veto rule.
> Six of seven Phase D checks and the veto rule therefore have **no artifact of any kind** and
> leg C of the audit could not be run for them. The registrations describe the procedures well
> enough to re-implement, but re-implementation produces new numbers, not the published ones.
> Same class as entry 22 (B3's harness deleted), recurring after that lesson, and worse in one
> respect: entry 22 cost four parameters, this costs the numbers. Affects Table II's blur row
> (σ = 0.45, −6.1%/+1.7%) and corrected-georeferencing row (~86% scatter) in full | Re-run both
> procedures from their registrations, commit the per-chip outputs **and the scripts**, and
> verify the published values; until then neither row enters the letter without an explicit
> unreproducible-provenance caveat. Standing fix: `tubitak/data/*` is gitignored, so no
> `tool_runs/` artifact in this project is protected — analysis outputs that support a
> published number are committed outside `data/`, as the seed-block loss logs now are |
> [phase-d-audit.md](phase-d-audit.md) §C |**

> **| 33 | 26 Aug | [phase-d-checks-registration.md](phase-d-checks-registration.md) check 5
> ("Europe, **Ankara**, Cappadocia, Tuz Gölü, and the salt/non-salt splits" recomputed under
> floors 0/10/20/30) and the ratio addendum's requirement that per-stratum gains be "reported
> alongside R **so the aggregation hides nothing**" | **Two registered reporting requirements
> were not met.** No floor-sensitivity line for **Ankara** exists in any document; floors are
> reported for Europe, Cappadocia, Tuz and the salt splits only. Only the aggregate ratio
> (1.188/1.258 = 0.945) is published; the per-stratum gains are absent, defeating the stated
> purpose of the requirement. With no artifact surviving (entry 32) the audit **cannot
> determine whether the Ankara sweep ran and went unreported or never ran** — the entry-19
> shape in its unresolvable form. Additionally, check 7b's registered conditional ("if the
> improvement is mostly scatter … restraint/blur carries the burden") was triggered (~86%
> scatter) but never explicitly discharged, so the burden transferred onto check 3 — the least
> verifiable result in the package — without being stated | Both items reported when the
> procedures are re-run per entry 32; the burden-transfer sentence added to the restraint
> verdict | [phase-d-audit.md](phase-d-audit.md) §B-2, §B-3 |**

> **| 34 | 26 Aug | [phase-d-results.md](phase-d-results.md):9 describes the registration as
> "verification checks 1–7, **run and reported** before this document was written" | **Two of
> the seven are not reported in it, or in either of the other two Phase D documents.** Checks 3
> (blur) and 7b (systematic/scatter) appear only in
> [phase-c-europe-results.md](phase-c-europe-results.md); the words "blur", "sigma",
> "systematic", "scatter" and "decompos" occur nowhere in `phase-d-results.md`,
> `phase-d-ratio-addendum.md` or `gcp-veto-rule-results.md`. Nothing is concealed — both
> outcomes are published, in a document committed in the same commit — but a reader auditing
> checks 1–7 against the document that claims them finds five, and the two absent ones are
> precisely the two that feed Table II | Cross-references added from `phase-d-results.md` to
> the two outcomes; the "run and reported" clause amended to say where |
> [phase-d-audit.md](phase-d-audit.md) §B-1 |**
