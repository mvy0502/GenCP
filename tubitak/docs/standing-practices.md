# Standing practices

Rules of general force, collected where future work will see them. Each carries its origin.

1. **Invariance section in every gate registration** (2026-08-21). Three ill-posed gate
   elements failed the same way — an unstated invariance assumption (same OSM source: false;
   same render path: false; deterministic inference: false). Every gate registration now
   lists explicitly what it assumes identical on both sides: data source, render path, code
   path, determinism. A gate that does not state its invariances does not know what it is
   measuring. Origin: [tool-gate-registration-2.md](tool-gate-registration-2.md) family,
   corrections-log entries 13–15.

2. **K-draw averaging on small subsets** (2026-08-21). Any comparison on roughly n < 60
   chips generates K seeded dropout draws and averages before scoring. Test-time dropout
   noise (~0.1–0.4 px per chip median) is a large relative contributor at small n — it sits
   inside the CI on R, the salt and badlands subsets, and the Cappadocia per-stratum
   numbers. It is removable noise and unaveraged small-n results have been paying it.
   Origin: corrections-log entry 14; Task-3 determinism probe.

3. **No retraining on production-provenance inputs for now** (2026-08-21). The train/serve
   skew is real (training = pre-fix simple-strategy extracts; production = post-fix smart),
   its cost is measured (~0.6 px on forest-heavy chips), and it lands on precisely the class
   the institution intends to mask out — which is fortunate, not designed. Mitigation: the
   reliability layer is weighted against forest; retraining on post-fix inputs is Phase F
   future work, not undertaken now. Origin: phase-c-results Limitations;
   [phase-f-backlog.md](phase-f-backlog.md).

4. **Registrations before numbers; failed gates reported, never adjusted; mis-specified
   gates re-registered with the original preserved** (standing since Phase B, restated here
   for completeness).

5. **Every reported number states its inference path** (2026-08-21). All C-phase and tool
   evaluation numbers were measured on the stochastic (dropout-active) path; the delivered
   tool defaults to the deterministic path (measured agreement |Δ| ≤ 0.05 px at n = 30
   resolution). The invariance rule applied to our own reporting: a reader must see the
   gap, not discover it. Origin: tool-results.md §A; Task 1 decision.

6. **One sign convention, document-wide** (2026-08-21). Δ = candidate − baseline; negative
   = candidate better. "Gain" is defined at point of use as −Δ. Stated at the top of each
   results document. Origin: the regC/+phase-D sign divergence.

7. **Long detached runs checkpoint intermediate results** (2026-08-21). Any run expected to
   outlive a session writes per-item artifacts so a respawn resumes rather than restarts
   (registration B had to be respawned from zero after a session limit). Origin: regB.

8. **Review the open items; do not only append to them** (2026-08-21). At the end of every
   package, [open-items.md](open-items.md) is read from the top; each item is closed or
   explicitly deferred with a written reason. Origin: three headline-deciding findings (the
   cold-D risk, the small-n rule lapse, the unexplained baseline shift) were all items we
   wrote down ourselves and stopped watching. The corrections log records what went wrong;
   nothing before this rule forced revisiting what we flagged as pending.

9. **Registration audits get a fourth leg: does the design support the inference?**
   (2026-08-24). The audit method used on T1, B2/B3 and the phase-C pair has three legs —
   timeline (commit times vs artifact mtimes), recomputation (every reported cell rebuilt from
   raw), and configuration (run configs diffed against the registration text). All three ask
   **whether the numbers are what we say they are**. None asks **what the numbers are evidence
   about**. The fourth leg does: *at what level was the treatment applied, at what level is the
   error bar computed, and are they the same level?* — and, more generally, whether the design
   can support the claim the document draws from it. Origin: the C4/C5 package passed all three
   existing legs on 2026-08-24 and was found the same day, by an adversarial review pass and
   not by us, to rest on a treatment applied once per cell with every standard error computed
   at chip level — 130 chips replicating the evaluation, not the intervention, and an
   interaction term with no run-level error bar at all. The audit that had just cleared it
   would never have caught that, because no leg was pointed at it.
   [seed-replication-registration.md](seed-replication-registration.md) is the correction; this
   practice is so the class is caught next time rather than the instance.

10. **Numerical artifacts that a published number depends on live under `docs/` and are
    tracked** (2026-08-26). `.gitignore` excludes `tubitak/data/*` and `tubitak/outputs/*`
    wholesale, so **no per-chip CSV, summary JSON or analysis script under those paths has
    ever been under version control**. Any such file that a published number rests on is
    committed to `tubitak/docs/evidence/`, with its sha256 recorded in
    [evidence/MANIFEST.md](evidence/MANIFEST.md) and verified against any value already
    published for it. **The scripts that produce those files are committed too** — an output
    without its producer is not reproducible, only re-implementable, and re-implementation
    yields new numbers rather than the published ones. Origin: **Phase D**
    ([phase-d-audit.md](phase-d-audit.md) §C). Six of its seven registered checks and its veto
    rule have no surviving artifact of any kind; `eu_per_chip.csv`,
    `blur_control_per_chip.csv`, `eu_decomposition_per_chip.csv`, `veto_features.csv` and
    `veto_rule.py` do not exist anywhere in the repository; and the sentence that justified not
    committing them — "regenerable end-to-end from committed scripts and registrations" — was
    **false**, because none of those scripts was committed either. Two Table II rows rest on
    numbers nothing in this repository can re-derive. **The rule is not "hash your artifacts".
    A hash proves identity if the file survives; it does not preserve the file.** At the moment
    the Phase D audit was written, the six-seed Modal block — 26 arm-units, one night, $23 of
    GPU — was protected by nothing but sha256 strings in a markdown file. The corrective is
    this practice, and entry 22 (B3's harness deleted, four registered matcher parameters
    permanently unverifiable) is the earlier instance of the same class that this practice
    exists to stop recurring for a third time.
