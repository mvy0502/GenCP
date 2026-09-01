# WP15 — making the corpus checks able to fail

**Repository** `mvy0502/GenCP`, branch `tubitak-tr`. **Date** 1 September 2026.
**Code** `tubitak/sr/sr_data/checks/corpus_checks.py`,
`tubitak/sr/sr_data/checks/mutation_test.py`.
**Evidence** `tubitak/docs/evidence/wp15/corpus_checks.json`.
**Registration amended** `03a-corpus-registration.md` §12.1.

An independent audit found that three of the four corpus checks had known-false arms that
could not fail. This package rewrote them so that each arm calls the same code the known-true
calls, added the measurement C4 was supposed to be making and was not, corrected what C3
claims, and then tested the arms themselves by breaking the checks on purpose.

Headline: **six of the eleven cases could not have failed before; all eleven can now.** Nothing
failed on the real corpus. No registered number changes.

---

## 1. What each old known-false actually tested

| check | the old arm, in one line | what it could detect |
|---|---|---|
| C1 | built `fake_hi` in memory, then re-evaluated the geometry predicate inline (`fake_hi.shape[-2] == lo.shape[-2] * C.SCALE and ...`) | nothing about `c1`'s own predicate — a defect there would have appeared in both arms and cancelled |
| C2 | `forged = np.full((128,128), 4); forged[7,11] = 9; np.isin(forged, CLEAR).all()` | that `np.isin` works. It never opened the manifest, never read an SCL raster, never computed a footprint |
| C3 | relabelled a real chip and called the real `S.buffer_violations` | genuinely worked — this arm was sound and was left alone |
| C4 | `identical = abs(area_average(t) - area_average(t)).max() == 0.0` | nothing. Unconditionally true for any deterministic function. No area average was ever substituted for the degradation |
| C4 (MTF) | `mtf_at(1/(2*scale), scale=scale)` compared with `MTF_AT_NYQUIST` | nothing. `mtf_at` re-derives σ from `MTF_AT_NYQUIST` via `sigma_for_mtf`, its own inverse, so it returns the target by construction whatever kernel is built |

A fifth defect, not an arm: **C2 passed vacuously on a chip whose footprint fell off the
raster.** `scl[r0:r0+n, c0:c0+n]` past the array bound yields an empty array, and
`np.isin(empty, CLEAR).all()` is `True`. The window was certified clear without being read.

---

## 2. What the new arms do

| check | new known-false | routed through |
|---|---|---|
| C1 | substitutes `_wrong_factor_degrade`, a real degradation decimating by `SCALE+1`, and asks `c1_geometry_ok` — the same predicate the known-true calls | `c1_geometry_ok` |
| C2 | plants a class-9 pixel **in the source SCL array** under a real chip footprint named by the real manifest, and re-runs the real scan | `c2_scan` |
| C2 (second) | plants a manifest row whose footprint runs past the raster edge; the scan must report an off-raster window rather than an empty pass | `c2_scan` |
| C3 | unchanged — it already called `S.buffer_violations` | `splits.buffer_violations` |
| C4 | substitutes `area_average` **for** the degradation and requires the measurement to report no difference | `c4_worst_difference` + `c4_differs` |
| C4 (MTF) | rebuilds the kernel from a σ derived for MTF 0.4 and requires rejection | `discrete_mtf_at_nyquist` |

`SCALE+1` rather than a literal 3: a hard-coded 3 rejects correctly at s=2 and s=4 and is blind
at s=3, which is how D27's known-false decayed.

---

## 3. Outcomes — every case, on the real corpus

`python tubitak/sr/sr_data/checks/corpus_checks.py`, corpus `sr_wald_corpus`, 6056 chips.
**Exit 0, 11 of 11 cases behaved as registered**, wall clock 1.8 s.

| check | case | outcome |
|---|---|---|
| C1 | known-true | **PASS** input (3, 128, 128) → target (3, 256, 256), ratio 2 both axes |
| C1 | known-false | **PASS** degradation decimating 3× → input (3, 85, 85) against target (3, 256, 256), correctly rejected |
| C2 | known-true | **PASS** 6056 chips re-read from source SCL; classes present [2, 4, 5, 6, 7]; 0 class violations, **0 off-raster footprints** |
| C2 | known-false | **PASS** class-9 planted in source SCL under real chip 36TVK (0,5) → 1 violation reported |
| C2 | known-false-2 | **PASS** chip planted at (47,47) past the (5490, 5490) raster → window (0, 0), 1 off-raster reported. *The pre-WP15 predicate returned clear=True for this same window* |
| C3 | known-true | **PASS** 6056 chips, 0 in two splits, 0 within 2560 m of a different split of the same granule |
| C3 | known-false | **PASS** one train chip relabelled 'test' at 36TVK (0,5) → 2 buffer violations detected |
| C4 | known-true | **PASS** over 64 chips, max \|MTF-degraded − area-average\| = 1.21124339 normalised (6056.2170 DN) |
| C4 | known-false | **PASS** degradation replaced by the 2×2 mean, run through the same measurement → max difference 0.00000000, correctly identified as a no-op |
| C4 | value | **PASS** discrete MTF of the 8-tap kernel as built = **0.299970210** (registered 0.3, deviation −2.98e−05, tolerance 1e−04); Im(H) = +0.0e+00 |
| C4 | value-false | **PASS** kernel rebuilt from σ for MTF 0.4 → discrete 0.399663252, 0.100 from target, correctly rejected |

---

## 4. The discrete MTF measurement

C4 now computes the DTFT of the taps `gaussian_decimation_kernel` actually returns,

    H(f) = Σ_o w_o · exp(−2πi f (o − centre)),   f = 1/(2·scale),   centre = (scale−1)/2

and reads the modulation at the output grid's Nyquist frequency. This is not the closed form:
the kernel is truncated at `KERNEL_RADIUS_SIGMAS = 4.0` σ and the surviving taps renormalised,
so its response is a finite sum, not `exp(−2π²σ²f²)`.

| scale | σ | taps | offsets | discrete MTF | deviation from 0.3 | Im(H) | Gaussian mass outside the window |
|---|---|---|---|---|---|---|---|
| 2 | 0.987878331 | 8 | −3..+4 | **0.299970210** | −2.98e−05 | +0.0e+00 | 2.54e−05 |
| 4 | 1.975756662 | 16 | −6..+9 | **0.299975794** | −2.42e−05 | −1.4e−17 | 4.28e−05 |

**The value is 0.299970210 at scale 2, not scale 4.** The brief attributed it to WP7; it is
WP3A's, recorded in `03a-wald-corpus.md` §5.1 at "f = 0.250 (20 m Nyquist)", and this
measurement reproduces it digit for digit. The scale-4 value, 0.299975794, had never been
measured. Both were measured here; neither had ever been asserted by a check.

`Im(H)` is asserted `< 1e−12` in the same arm. A kernel not symmetric about the block centre
shifts the image, and that is not hypothetical: the scale-4 window was asymmetric until WP7 and
baked a −0.0011 px shift into every degraded input.

### The tolerance, and why it is 1e−4

`MTF_TOL = 1e-4`. It accommodates the truncation deliberately.

- The deviation is caused by cutting the Gaussian at 4 σ and renormalising, and is of the same
  order as the mass discarded (2.5e−05 and 4.3e−05 above). It is a property of the registered
  kernel, not an error.
- 1e−4 sits above both deviations with roughly 3× headroom.
- It sits three orders of magnitude below any error that would matter: a σ derived for a target
  of 0.4 instead of 0.3 lands **0.100** away, and a kernel with no low-pass at all lands 0.700
  away. Both are rejected.

The tolerance is not tuned to make anything pass. Widening the kernel would close the gap to
zero and would also change the corpus, so the truncation stays and the number is reported —
which is what WP3A decided and this package keeps.

---

## 5. Proving the arms can fail

An arm reporting "correctly rejected" means nothing unless it would have said otherwise had the
check been blind. `mutation_test.py` replaces one predicate at a time with a blind version and
requires the arm that guards it to turn FAIL. **Exit 0 — every arm moved.**

| arm | mutation | unmutated | mutated |
|---|---|---|---|
| C1 known-false | `c1_geometry_ok` accepts any pair | True | **False** |
| C2 known-false | `c2_scan` never reports a class violation | True | **False** |
| C2 known-false-2 | `c2_scan` reverted to the pre-WP15 body, no shape assertion | True | **False** |
| C3 known-false | `buffer_violations` never finds a violation | True | **False** |
| C4 known-false | `c4_differs` says everything differs | True | **False** |
| C4 value-false | MTF read from the closed form instead of the kernel (the pre-WP15 arm) | True | **False** |

### The same mutations put to the old code

The old file was restored from git and given the identical mutation:

| mutation | old arm | new arm |
|---|---|---|
| kernel replaced by a single delta tap — no low-pass at all, true MTF 1.0 at every frequency | **PASS**: still reports the registered 0.3 | **FAIL**: correctly rejected |
| production `degrade_chip` made to emit a 6.4× pair | known-true correctly FAILs; **known-false still PASSes** — it is insensitive to production | n/a, the arm now calls the predicate |
| every source SCL pixel forced to class 9 (cloud) | known-true correctly FAILs; **known-false still PASSes** | n/a, the arm now reads the source |

The first row is the sharpest: the pre-WP15 C4 certified a kernel that low-passes *nothing* as
having the registered modulation of 0.3.

### Two mutations of mine that were wrong, and how I found out

Reported because the harness caught them and because a mutation test is only as good as its
mutations.

1. My first `closed_form_mtf` mutation forwarded `sigma` to `mtf_at`, so it returned 0.4 for
   the wrong-σ kernel and the arm appeared to catch it. The pre-WP15 arm never had a σ to
   forward — it re-derived one from the registered constant. Corrected to ignore `sigma`, which
   is the actual defect; the arm then correctly turned FAIL.
2. An A/B mutation replaced `area_average` with random noise. That moved the old arm, but for
   the wrong reason: `|f(t) − f(t)|` is non-zero for a non-deterministic `f`. Re-run with a
   deterministic substitute, the old arm stayed PASS as expected. Patching `area_average` also
   moves C4's *yardstick* rather than the code under test, so it is not a valid mutation for
   either version and is not counted above.

---

## 6. Degenerate invocations

| invocation | exit | what is printed |
|---|---|---|
| no arguments | **0** | the real run, 11 of 11 |
| `--overlp=2560` (a typo) | **2** | `unrecognised argument(s): --overlp=2560` |
| a bare positional | **2** | `unrecognised argument(s): extra` |
| `--corpus=/nonexistent` (missing file) | **2** | `no manifest at /nonexistent` |
| `--corpus=<empty directory>` | **2** | `no manifest at ...` |
| `--corpus=<manifest with zero rows, chips present>` | **2** | `manifest ... has no rows - there is nothing to check, which is not the same as everything passing` |

The last row is new in WP15 and is the reason for it. Given the same input, the pre-WP15 code
printed:

```
  C2  no chip contains an SCL class declared not clear
    [PASS] known-true   0 chips re-read from source SCL; classes present [] ...; 0 violations
  C3  no chip in two splits, and none within the buffer of another split
    [PASS] known-true   0 chips, 0 appearing in more than one split, 0 within 2560 m ...
```

— three PASSes for a corpus that contains nothing. It then exited 1, but from a `TypeError` in
C3's known-false (`forged[None]`), not from a verdict. It was saved by an unrelated crash. This
is the failure the 23-verifier audit found eighteen times, and it was still here.

---

## 7. C3's claim, corrected

`splits.buffer_violations` groups records by granule and never compares across them. C3's
prose claimed the unqualified property. Corrected in the check's own output and in the
registration to:

> no chip is in more than one split, and none lies within `SPLIT_BUFFER_M` of a chip in a
> different split **of the same granule**.

The corpus-wide property — chips of different splits physically close across granule
boundaries, where granules overlap by about 9.8 km — is gate **D18**, the cross-granule leakage
check, `tubitak/sr/sr_train/leakage.py`. C3 is deliberately **not** extended to duplicate it.
That gap is what let 47 test chips leak in WP3A, and two checks asserting the same property is
how a gap gets missed twice rather than once.

---

## 8. Found on the way, not in the brief

**The checks could read one corpus with another's parameters.** `CORPUS` is built from
`params.CORPUS_SUBDIR` — always the scale-2 corpus — while `C.SCALE`, `C.N_BANDS` and
`C.NORM_DIVISOR_DN` come from `config`, which follows `GENCP_SR_VARIANT`. Under `x4` or `tci`
the two disagree, and the checks would have degraded scale-2 chips by 4 and reported a verdict
about a corpus nobody asked for — `strict_argv`'s own complaint, one level up.

Repointing `CORPUS` at `config.CORPUS_SUBDIR` is not the fix: `sr_wald_corpus_x4` has no
`manifest.csv` at all, so C2 and C3 cannot run on it. The script now **refuses**:

```
GENCP_SR_VARIANT=x4  -> exit 2, "Refusing rather than checking one corpus with another's parameters"
GENCP_SR_VARIANT=tci -> exit 2, same
GENCP_SR_VARIANT=x2  -> exit 0, 11 of 11
```

`--corpus=DIR` overrides it, so saying which corpus you mean is still possible. At the default
variant the behaviour is unchanged. Nothing else in the repository imports `corpus_checks`, so
no harness is affected.

---

## 9. Did anything fail once it could?

**No.** All eleven cases pass on the real 6056-chip corpus, and both new failure modes measure
zero on it: **0 off-raster footprints** out of 6056, and the discrete MTF within 3.0e−05 of the
registered target at both scales. No registered number changes and no corpus is rebuilt.

That is a real result and also a limited one. These checks were incapable of failing, so their
past PASSes were not evidence; what this package establishes is that the *present* state of the
corpus satisfies the properties, measured by checks that would have said so if it did not. It
does not retroactively validate the WP3A run, because the code that ran then could not have
reported a violation of C4 in any case.

---

## 10. Open items

1. The MTF arm asserts the kernel at `C.SCALE` only. The scale-4 kernel is measured here
   (0.299975794) but is not asserted by any check, because the checks refuse to run under the
   x4 variant for the corpus-mismatch reason in §8. Asserting both scales in one invocation
   would close this.
2. `sr_wald_corpus_x4` has no `manifest.csv`, so C2 and C3 have never run on the scale-4
   corpus. Its split separation rests on D18 alone.
3. `mutation_test.py` covers the six known-false arms. It does not cover the known-**true**
   arms, which could in principle be blind in the other direction.
4. `clear_mask_20m` is imported by `corpus_checks.py` and never used. Left alone: it is a
   one-line removal that touches a file this package rewrote, and removing it deserves the
   reference check CLAUDE.md requires rather than a drive-by deletion.
5. The evidence JSON is written to `tubitak/docs/evidence/wp15/`. WP3A's went to
   `tubitak/data/sr_wald_corpus/evidence/`, which is gitignored and therefore not a record.
