# Paper handoff context

What an agent working on the manuscript needs to know before it writes a number down.

## Where things live

Three repositories exist for this project. They are not copies of each other.

| Repository | Role | Who writes |
|---|---|---|
| `mvy0502/GenCP`, branch `tubitak-tr` | **Working repository.** Research record, gate registrations, results, code, QGIS plugin | All agent work happens here |
| `mvy0502/gencp-validation` | **Handover copy** for whoever takes the project over | Destination only — never a source, never merged into |
| `mvy0502/gencp-letter` | Paper (TeX) | Paper work only |

The manuscript is written in `gencp-letter`. Every number in it comes from `tubitak/` in
the **working repository** — not from `gencp-validation`, which is a snapshot and may lag.
Never re-derive a number in the paper repository. Every number must cite the gate or
registration it came from, and must state its inference path.

## Rules that bind the manuscript

1. State the inference path for every number. Two numbers from different paths are not
   comparable.
2. One sign convention, stated: **Δ = candidate − baseline; negative = candidate better.**
   Never flip it mid-report.
3. A number whose registration was revised after the outcome was seen is not quotable.
4. Institutional (TÜBİTAK) imagery must never enter the repository or the manuscript's
   source tree. Google Earth imagery is for internal visual verification only.

## Method-section facts that must be stated

These are properties of the published GenCP pipeline that the manuscript cannot omit
without misdescribing what was measured.
