# Paper roadmap — GRSL letter + arXiv long version

Decided 2026-08-23 (session record; supersedes the earlier "4.1 main + 4.3 supporting"
split). Owner of open items: see the work list at the bottom. Registration discipline
applies to this document too: structural decisions recorded here before drafting.

> **AMENDED 2026-08-24 — read the amendment block at the bottom before using anything
> below.** The scope was narrowed to the loss-function paper after the C4/C5 factorial
> landed; the three-leg narrative and the work list below are the 2026-08-23 text,
> preserved as the record of what was decided then, and are superseded in emphasis (not
> withdrawn as false) by the amendment. The manuscript wording rule and the venue
> sequence are untouched by it.

## The paper is one three-leg narrative, not a main result with supporting evidence

1. **Scope** — at 10 m the premise for synthetic references fails: no availability gap
   (E1: 0/24 extents without a usable scene, median freshness 2 days — scene-per-year
   figures are right-censored lower bounds, query capped at 100 and every extent hit the
   cap; the censoring does not touch the gap rate or freshness, which depend only on the
   most recent scene) and no currency advantage (E2: ABSENT, +0.008 ± 0.031 px). E1/E2
   are **scope-setting, not results**: two-three sentences plus a footnote in the letter.
2. **Where it does bind** — sub-metre resolution is where licensing actually constrains
   reference choice. The T1→operational transfer question is treated honestly: E3 is
   **exploratory only** (corrections-log entry 16) and does not appear in the letter.
3. **Design rule** — if you generate a reference, do not train it with an adversarial
   loss. Grounded in **three independent 10 m measurements, all shown**: T1's C1 row
   (clean site: C1 1.119 px vs C2 0.541 px at t1, near-equal point counts 405/388 — a
   quality difference, not matchability), B2's production-path ablation, and B3's direct
   mechanism measurement (edge-density ratio; mediation 0%). In the mechanism section
   **B3 leads** (direct measurement, registered retraction condition untriggered) and
   **B1 follows** as dose-response support — B1 is post-hoc (registered bands did not
   cover the observed shape; the document says so) and must not be the spine.

3.1 (the 1/256 scale bug): one paragraph in methods + repo pointer. Four alternative
explanations for the mechanism: summary table in the letter, full protocol in the arXiv
version. Seed defence: one sentence combining the pre-registered n ≥ 60 single-draw rule,
the regA det/stoch bound (≤ 0.05 px), and the measured effect sizes (0.38–0.70 px) —
currently scattered across three documents.

**The ODTÜ contamination pair is an independent methods contribution:** same tool, same
matcher, same distortions — contaminated site 0.008–0.11 px vs clean site 0.54–3.97 px
(20–130×). A direct measurement of train-on-target overlap. Letter: one paragraph + the
two tables side by side. arXiv: its own section.

**E3 and its follow-ups (bootstrap CIs, C1 at 0.5 m) move to the second paper**, where
the operational-resolution protocol is the main material. In the arXiv long version E3
may appear in the discussion, exploratory label attached, never in a results table.
Verified 2026-08-23: **no leg of the argument depends on E3** — leg 1 = E1/E2, leg 2 =
T1 clean site + intrinsic column, leg 3 = T1-C1/B2/B3.

## Manuscript wording rule (binding)

Never: "All experiments were pre-registered."
Always: **"Experiments were pre-registered where stated; deviations from the registered
protocol are documented in a public corrections log."**
The first sentence is falsified by corrections-log entries 16–17; the second is evidenced
by them.

## Venues and sequence

arXiv preprint **first** (citable ID within days, what application forms cite), then:
1. **IEEE GRSL** — primary; 5-page letter, ~30-day handling; submit target end of
   October 2026; verify GRSL's current preprint + supplementary policy before submission.
2. **IGARSS 2027** (deadline 11 Jan 2027, notification 12 Mar 2027) — second slice.
3. TGRS/JSTARS — only if the three contributions are merged into one long paper.
4. ISPRS Journal — the expanded second paper (operational-resolution protocol).
5. Not MDPI Remote Sensing — GRSL is comparably fast and better regarded.

## Work list, in order

*(2026-08-23 text. Superseded 2026-08-24 — items 0–7 as they now stand are in the
amendment block below; this list is kept as the record of what was planned then.)*

- [x] **0. T1 registration audit** — DONE 2026-08-23, [T1-audit.md](T1-audit.md).
      Timeline claim TRUE (only input rasters predate the amendment; results CSV 10 min
      after). 70/70 table cells reproduce from the raw CSV. Configs match the
      registration. One real deviation: **registered ORB+RANSAC secondary matcher never
      ran, undisclosed until the audit** → corrections-log entry 17 + disclosure line in
      the results doc. One immaterial wording nit ("bearing 30°" implemented as 30° from
      grid-east; identical for all candidates; disclosed in the audit).
- [ ] **1. Repo-wide registration audit** (same three checks per registration):
      `headline-registrations.md` B2/B3 (B1 already self-reports its band failure),
      `phase-c-registration`, `phase-c-europe-registration`, `phase-d-checks-registration`,
      `packageA-registration`, the four `tool-*registration` files, T3. Until this is
      done the paper's discipline claim rests on a base rate of 1 clean / 1 failed / 1
      partial among audited registrations.
- [ ] 2. Run the T1 ORB+RANSAC half (closes entry 17's open work) — or record a reasoned
      decision not to, in the corrections log.
- [ ] 3. Bootstrap CIs on the existing E3 runs (E3-b step 1; per-point fields in
      `kp_delta.json`); interpretation rule pre-stated in E3-b.
- [ ] 4. C1 at 0.5 m under the disclosed protocol — only if step 3 separates the arms
      (E3-b step 2). Steps 3–4 feed the second paper, not the letter.
- [ ] 5. E1 re-query with pagination (replaces the censored lower bound with the true
      scene counts; half a day; kills one likely revision-round question).
- [ ] 6. Letter skeleton in Markdown → `latex-scaffold` route once the audits are green.
- [ ] 7. Figure plan: three-leg figure budget for 5 pages (contamination pair, mechanism
      B3, dose-response B1 inset).

The Teke one-pager waits on item 0's outcome by design — item 0 is done and T1 stands;
the one-pager can proceed against this roadmap.

---

# AMENDMENT — 2026-08-24: the letter is the loss-function paper

Recorded as an amendment, not an edit, for the same reason every registration in this
repository is: the 2026-08-23 text above is the record of a structural decision made
without a result that now sits at the centre of the paper, and a reader is entitled to
see both states. Nothing above is withdrawn as false. What changes is which leg carries
the paper.

## A. What this document did not know when it was written

| event | commit | time (UTC+03) |
|---|---|---|
| **roadmap above committed** | `014b308` | **2026-08-23 20:33:51** |
| C4/C5 registration (2×2 loss factorial), before any run | `b07e719` | 2026-08-23 22:47:35 |
| C4/C5 evaluation harness committed | `40cde9b` | 2026-08-24 02:44:06 |
| **C4/C5 results** | `6560c8b` | **2026-08-24 03:05:33** |

The roadmap above was written **2 h 14 m before the factorial was registered** and
**6 h 32 m before its results existed**. The 2×2 loss factorial appears nowhere in it —
not in the three-leg narrative, not in the figure budget, not in the work list. Its
design-rule leg (leg 3) rests instead on T1's C1 row, B2 and B3, and its mechanism
section is built around B3.

**Recorded plainly: the structure above predates the result that is now the paper's
spine.** This is exactly the failure mode the registration discipline exists to make
visible in our own planning documents, so it is stated rather than smoothed over by
rewriting leg 3 in place.

## B. Amended scope decision

**The GRSL letter is the loss-function paper.**

1. **Spine — the 2×2 loss factorial**, five arms (pretrained, C1, C2, C4, C5),
   [phase-c-lpips-results.md](phase-c-lpips-results.md). Primary: C5 − C4 =
   **−0.487 ± 0.053 px, t = −9.18** (ank130, n = 130). ~~Interaction: **−0.212 ± 0.069,
   t = −3.07**, the registered *substitutes* band.~~ Dose-response replicates under LPIPS
   at every epoch at ≥ 6 SE.

   **SUPERSEDED 2026-08-26** — the interaction sentence is struck, not deleted. The
   registered seed-level reading failed at 5/6 across six confirmatory seeds on all three
   registered scales and the pre-committed consequence fired, so the interaction is not spine
   content and is not quotable ([seed-block-results.md](seed-block-results.md) §4). **The
   spine gains the required interaction disclosure instead**
   ([paper-context-addendum.md](paper-context-addendum.md) §24), and the out-of-range result
   at [seed-block-results.md](seed-block-results.md) §5(c). B2's production path survives here as the secondary row,
   now extended to six arms (C5 − C4 = −0.182 ± 0.054, t = −3.36).
2. **Mechanism section leads with the edge-ratio measurement** (C2 0.28 vs C1 1.10 /
   C4 1.12 / C5 1.16; pretrained ≈ 1.02) — the direct measurement, all five arms in one
   pass — **and carries the section-22 non-monotonicity caveat**
   ([paper-context-addendum.md](paper-context-addendum.md) §22): the ratio separates the
   restrained arm from the unrestrained ones but **does not order the errors within the
   unrestrained group**. Invention is a necessary condition, not a complete explanation;
   the route-difference account is offered as the honest partial one.
3. **E1/E2 become two sentences of scope in the introduction, not results.**
4. **T1, the ODTÜ/Cappadocia contamination pair, and E3 move to the second paper** —
   with them, T1's C1 row, which leg 3 above used as its first independent measurement.

**Reason, stated so it can be checked later.** Two, and both matter:

- **The factorial replicates the main effect under both reconstruction terms and
  generalises the claim from "adversarial" to "plausibility pressure".** C5 — which has
  no discriminator anywhere in its objective — hallucinates hardest of all five arms
  (edge ratio 1.16) and pays for it positionally. That is a stronger and more general
  contribution than a critique of one paper's premise, which is what the 2026-08-23
  structure was: legs 1 and 2 argue that the published motivation does not hold at 10 m,
  and only leg 3 says anything a reader can carry to their own system.
- **It is also the material with the cleanest registration.** Registered `b07e719`
  before any run, harness committed (`40cde9b`), Gates 0/1 passed, every registered band
  fired, and the retraction condition not triggered — against B3's corrections-log
  entries 20–22 and E3's entry 16. A letter whose primary table rests on the
  best-registered package in the repository is the one we can defend line by line.

**Consequences for the legs above**, so the two texts cannot be played against each
other: leg 1 (E1/E2) survives, demoted from a leg to introduction scope. Leg 2 (where
the premise binds, sub-metre) moves to the second paper with T1 and E3. Leg 3's support
changes hands: the factorial replaces T1's C1 row as the primary measurement, B2 stays
as the production-path row, **B3 part 1 and part 3 stay as mechanism support with
corrections-log entries 20–22 attached, and B3 part 2 (mediation) does not appear at all
— it is void as stated** ([B2-B3-audit.md](B2-B3-audit.md), entry 20).

## C. Work list as it now stands

- [x] **0. T1 registration audit** — DONE 2026-08-23, [T1-audit.md](T1-audit.md).
      Unchanged by this amendment; T1's own material moves to the second paper.
- [ ] **1. Repo-wide registration audit** — in progress, per registration:
      - [x] **T1** — DONE 2026-08-23. Holds; one real deviation (entry 17, registered
            ORB+RANSAC half never run, now disclosed).
      - [x] **B2** — DONE 2026-08-24, [B2-B3-audit.md](B2-B3-audit.md). **Holds.**
            Timeline PASS (zero artifacts predate the registration commit), 384/384
            reported cells reproduce from raw KARIOS output, estimator and chip roster
            verified. One deviation: **entry 19** — the registered RGB half ran but was
            never reported; now published, and it is *more* favourable than the reported
            BT.601 half.
      - [x] **B3** — DONE 2026-08-24, same audit. **Part 1 holds** (every mean, SE,
            count, rank and Δ reproduces). **Part 2 is void as stated** — **entry 20**:
            the reported conditional is the OLS fitted value at the covariate means,
            algebraically the raw mean, so "loses 0% of its magnitude" could not have
            come out otherwise; the "trained-on-the-metric receives no support" sentence
            is withdrawn. Plus **entry 21** (MI parabola subpixel refinement registered,
            never applied) and **entry 22** (B3's harness and its part-2/part-3 per-chip
            artifacts not preserved).
      - [x] **E3** — **FAILED** (entry 16), reclassified exploratory. Recorded here so
            the base rate is read off one place.
      - [ ] **`phase-c-lpips-registration.md` (C4/C5) — NEW, and now the top priority.**
            It did not exist when the 2026-08-23 list was written (registered 22:47:35
            that evening, results 03:05:33 the next morning), so the list above does not
            name it. **It is the registration behind the letter's primary result, and
            under the amended scope the letter's primary table cannot be drafted before
            it is audited.** Same three checks: commit times vs artifact mtimes, run
            configs diffed against the registration text, full recomputation of every
            reported cell from the raw per-chip artifacts in `tool_runs/C45/`. Its
            harness is committed (`tubitak/scripts/c45_eval/`), so the entry-22 failure
            mode does not apply — which is precisely why it should audit cleanly, and
            precisely why an audit that does *not* come out clean matters most here.
      - [ ] Remaining, unchanged and lower priority now that the letter's spine has
            moved: `phase-c-registration`, `phase-c-europe-registration`,
            `phase-d-checks-registration`, `packageA-registration`, the four
            `tool-*registration` files, T3.
      - **Base rate after four audits:** two timeline claims verified true (T1, B2/B3),
        one falsified (E3); three registrations carrying disclosed protocol deviations
        (T1 entry 17, B2 entry 19, B3 entries 20–22). The discipline claim is evidenced
        by the corrections log, not by a clean sheet — which is what the wording rule
        below already says.
- [x] **1b. Related work — first pass DONE.** **Location correction: there is no
      `related-work.md` in this repository**; the first pass is
      [paper-context-addendum.md](paper-context-addendum.md) **§16**, which fixes the
      must-cite (Blau & Michaeli, *The Perception-Distortion Tradeoff*, CVPR 2018), the
      near-but-distinct set, and the gap confirmed against the upstream paper's own
      bibliography. **Remaining legs:** (a) a structured **Scopus / Web of Science**
      query; (b) a **manual Google Scholar citation check** on the upstream paper. Until
      both are done, novelty claims read "to our knowledge", never "first".
- [ ] 2. Run the T1 ORB+RANSAC half (closes entry 17's open work) — or record a reasoned
      decision not to, in the corrections log. **Now second-paper work**, with T1.
- [ ] 3. Bootstrap CIs on the existing E3 runs (E3-b step 1). Second paper, as before.
- [ ] 4. C1 at 0.5 m under the disclosed protocol, only if step 3 separates the arms.
      Second paper, as before.
- [ ] 5. E1 re-query with pagination. **Demoted**: E1 is now two sentences of
      introduction scope, so the censored lower bound no longer appears in a results
      table. Still worth half a day before submission; no longer gating.
- [ ] 6. Letter skeleton in Markdown → `latex-scaffold` route. **Gate changed:** it now
      waits specifically on the C4/C5 audit (item 1's new top entry), not on the whole
      repo-wide sweep.
- [ ] 7. **Figure plan — replaced.** The 2026-08-23 budget (contamination pair /
      mechanism B3 / dose-response B1 inset) no longer matches the legs: the
      contamination pair has moved to the second paper and B1 was never the spine. The
      5-page budget is now (i) the 2×2 factorial main effect, (ii) the five-arm
      edge-ratio mechanism figure carrying the §22 caveat, (iii) the C4/C5
      dose-response, with B1's L1-family curve as the replication it reproduces.
- [ ] 8. **Cappadocia known-displacement recovery for C4/C5** — open-items item 25,
      deferred: the T1 harness was not preserved, so adding arms means reconstructing the
      protocol from artifacts. Register the reconstruction first if it is ever attempted
      (the E3 lesson).

**Unchanged by this amendment:** the manuscript wording rule and the venue sequence,
both of which stand exactly as written above.
