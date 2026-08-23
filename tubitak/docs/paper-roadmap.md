# Paper roadmap — GRSL letter + arXiv long version

Decided 2026-08-23 (session record; supersedes the earlier "4.1 main + 4.3 supporting"
split). Owner of open items: see the work list at the bottom. Registration discipline
applies to this document too: structural decisions recorded here before drafting.

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
