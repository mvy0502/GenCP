# Registration — the informative-mask edge ratio (blur versus restraint)

**Registered 2026-08-26, before the complementary-mask ratio is computed for any arm or seed.**
No number on the informative mask exists at the time of writing. Standing practice 4 governs.

## What it replaces and why

The blur objection — "L1-only just produces smoother output, and the matcher prefers smooth" —
was answered by a single-seed negative control whose artifacts did not survive
([phase-d-regeneration-STOP.md](phase-d-regeneration-STOP.md)). **This replaces it with a
six-seed positive test built from data that is committed and verified.**

## The quantity

The registered edge ratio is computed on **input-silent** pixels, Sobel(warped input render)
**≤ 20**. This computes the identical ratio on the **complementary mask, Sobel(input) > 20** —
the pixels where the input *does* assert structure. Everything else is unchanged:
`c45_edge_ratio.py`'s operator (scipy Sobel hypot on BT.601 gray), the same 130 Ankara chips,
the same real-chip denominator, per-chip ratio, per-arm mean over chips.

**The discrimination is exact.** Blur suppresses edges **uniformly**; restraint suppresses them
**conditionally**. C2 is at 0.28 on the silent mask. What it does on the informative mask
separates the two.

## Pre-committed threshold, fixed before any number is seen

- **"Near 1.0"** = per-arm mean informative-mask ratio **≥ 0.80**.
- **"Suppressed"** = **≤ 0.50**.
- Between 0.50 and 0.80 = **intermediate**, reported as intermediate, no stronger word.

These are not invented for this test: **0.80 and 0.50 are the bands already registered in
[phase-c-lpips-registration.md](phase-c-lpips-registration.md)** for the silent-mask reading
("near 1.0 = mean ratio ≥ 0.8; well below 1.0 = mean ratio ≤ 0.5"). Reusing them keeps the
threshold out of this session's hands.

## The two branches, both written now

**BRANCH 1 — RESTRAINT.** C2's informative-mask mean is **≥ 0.80** while its silent-mask mean
stays ≤ 0.50. Selective suppression. **The blur objection is refuted by a positive test**, at
six seeds, and Table II's blur row is replaced by a stronger one.

**BRANCH 2 — BLUR WINS, and this is what it costs.** C2's informative-mask mean is **≤ 0.50**
too. Uniform suppression, which is what blur looks like. Then:

- **The paper says so.** The blur row's verdict flips from *refuted* to *supported*, and the
  mechanism section states that C2's advantage is at least partly a smoothing effect rather
  than learned restraint.
- **"Restraint" leaves the manuscript** as a mechanism claim, in the same way "the same lever"
  did — the word is removed wherever it asserts a mechanism, and the disclosure that the test
  was registered and went against us stays.
- **The edge-ratio mechanism section is rewritten**, not deleted: C2 suppresses invented
  structure, and the honest reading becomes that it suppresses structure generally.
- **The positional results are untouched.** C5 − C4, C5 − C2, C1 − C2, C4 − C5 are
  measurements of residuals and do not depend on why C2 is smoother. **The design rule
  survives**: C2 is still the checkpoint to hand over.
- **What does not survive is the explanation**, which is the part the letter currently leads
  its mechanism section with.

**Intermediate** (0.50 < mean < 0.80): reported as partial, no stronger word, and the blur row
is reported as narrowed rather than refuted.

## Readings

Per-arm informative-mask mean per seed, all four arms, **six Modal seeds (45–50)**, with a
sign tally in the house style. The registered reading is on **C2**; the other three arms are
reported beside it because uniform-versus-conditional is only interpretable in contrast.

**Scope: n = 6 seeds.** This is a mechanism reading, not a positional one. It enters no
registered positional contrast and modifies no published number. Both mask results are
reported side by side; the silent-mask reading is unchanged and remains the registered one.

## Artifacts

Per standing practice 10, the per-chip informative-mask CSV and the script are committed under
`tubitak/docs/evidence/`, including if the result is branch 2.

Nothing is computed until this is committed and pushed.
