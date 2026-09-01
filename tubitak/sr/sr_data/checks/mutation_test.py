#!/usr/bin/env python
"""Prove the corpus checks' known-false arms can fail, by breaking the checks on purpose.

A known-false arm that reports "correctly rejected" tells you nothing unless it would have
reported otherwise had the check been blind. Four of the arms in `corpus_checks.py` could
not: they re-implemented the predicate, or compared a function to itself, so no defect in
the production code could have moved them.

This harness mutates one predicate at a time — replacing it with a blind version — and
requires the arm that guards it to turn FAIL. An arm that stays PASS under its own mutation
is still a tautology and is reported as such.

    python tubitak/sr/sr_data/checks/mutation_test.py

Exit 0 only if EVERY mutation is caught by the arm that is supposed to catch it.
"""
from __future__ import annotations

import io
import sys
from contextlib import redirect_stdout
from pathlib import Path

sys.argv = [sys.argv[0]]                    # corpus_checks runs strict_argv at import
sys.path.insert(0, str(Path(__file__).resolve().parent))
import corpus_checks as K                                              # noqa: E402
import numpy as np                                                     # noqa: E402


def run(fn, arm, mutate=None):
    """Run check `fn` under `mutate`, and return the ok flag of case `arm`."""
    saved = {}
    if mutate:
        for name, repl in mutate.items():
            saved[name] = getattr(K, name)
            setattr(K, name, repl)
    K.RESULTS.clear()
    try:
        with redirect_stdout(io.StringIO()):
            fn(K.CORPUS)
    finally:
        for name, orig in saved.items():
            setattr(K, name, orig)
    hits = [r for r in K.RESULTS if r["case"] == arm]
    return hits[0]["ok"] if hits else None


# --- the blind versions, one per predicate ------------------------------------------
def blind_geometry_ok(lo, hi, scale, n_bands):
    return True                                    # accepts any pair


def blind_c2_scan(rows, scl_by_tile, n_scl, stride_half, clear_classes):
    return len(rows), {4: 1}, [], []               # never reports a violation


def unshaped_c2_scan(rows, scl_by_tile, n_scl, stride_half, clear_classes):
    """The pre-WP15 body: no shape assertion, so an off-raster window passes vacuously."""
    bad, census, checked = [], {}, 0
    for tile, scl in scl_by_tile.items():
        for r in rows:
            if r["granule"] != tile:
                continue
            r0 = int(r["chip_row"]) * stride_half
            c0 = int(r["chip_col"]) * stride_half
            sub = scl[r0:r0 + n_scl, c0:c0 + n_scl]
            v, n = np.unique(sub, return_counts=True)
            for a, b in zip(v, n):
                census[int(a)] = census.get(int(a), 0) + int(b)
            checked += 1
            if not np.isin(sub, list(clear_classes)).all():
                bad.append((tile, r["chip_row"], r["chip_col"], []))
    return checked, census, bad, []                # off_raster always empty


def blind_differs(worst):
    return True                                    # everything "differs"


def closed_form_mtf(scale, sigma=None):
    """The pre-WP15 arm: sigma_for_mtf composed with mtf_at, an algebraic identity that
    returns the target whatever kernel is actually built."""
    from sr_data.degrade import mtf_at
    # `sigma` is IGNORED on purpose - that is the defect. The old arm had no kernel to ask
    # about; mtf_at re-derived sigma from the registered constant, so it returned the target
    # whatever the kernel did. Forwarding sigma here would make the mutation faithful to a
    # bug that never existed, and the arm would appear to catch it.
    return mtf_at(1.0 / (2 * scale), scale=scale), 0.0, 0


def blind_buffer_violations(records, *a, **k):
    return set()                                   # never finds a violation


CASES = [
    ("C1 known-false", K.c1, "known-false", {"c1_geometry_ok": blind_geometry_ok},
     "geometry predicate accepts any pair"),
    ("C2 known-false", K.c2, "known-false", {"c2_scan": blind_c2_scan},
     "SCL scan never reports a class violation"),
    ("C2 known-false-2", K.c2, "known-false-2", {"c2_scan": unshaped_c2_scan},
     "SCL scan drops the window-shape assertion (the pre-WP15 body)"),
    ("C3 known-false", K.c3, "known-false", None,
     "buffer_violations never finds a violation"),
    ("C4 known-false", K.c4, "known-false", {"c4_differs": blind_differs},
     "difference predicate says everything differs"),
    ("C4 value-false", K.c4, "value-false", {"discrete_mtf_at_nyquist": closed_form_mtf},
     "MTF read from the closed form instead of the kernel (the pre-WP15 arm)"),
]


def main():
    print("=" * 88)
    print("mutation test - each arm must FAIL when the predicate it guards is made blind")
    print("=" * 88)
    allok = True
    for label, fn, arm, mut, why in CASES:
        if label == "C3 known-false":                       # patch the module it calls
            saved = K.S.buffer_violations
            K.S.buffer_violations = blind_buffer_violations
            try:
                got = run(fn, arm)
            finally:
                K.S.buffer_violations = saved
        else:
            got = run(fn, arm, mut)
        base = run(fn, arm)
        ok = (base is True) and (got is False)
        allok &= ok
        print(f"  [{'PASS' if ok else 'FAIL'}] {label:18s} unmutated {base}, mutated {got}")
        print(f"         mutation: {why}")
        if not ok:
            print(f"         *** the arm did not move - IT IS STILL A TAUTOLOGY")
    print("=" * 88)
    print("EVERY ARM MOVED UNDER ITS OWN MUTATION" if allok else
          "AN ARM DID NOT MOVE - IT CANNOT FAIL")
    print("=" * 88)
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
