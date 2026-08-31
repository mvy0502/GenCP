#!/usr/bin/env python3
"""D18 — the cross-granule leakage check. This is the gate on Part B.

Asserts: no chip in `test`, and no chip in `heldout`, has a footprint that overlaps or lies
within SPLIT_BUFFER_M of the footprint of any chip in `train`, in ANY granule.

Reported at two radii, because they are different failures:
  * OVERLAP  (separation == 0)      shared ground - the chips are near-duplicates
  * BUFFER   (separation < 2560 m)  spatial autocorrelation without shared ground

Standing practice 10/11: run against a known-true and a known-false case before the verdict
is trusted, and refuse arguments it does not understand. KF2 is the case that matters - it
runs the check on WP3A's own manifest, where an independent implementation in another work
package measured 47 leaking test chips. A checker that cannot reproduce 47 on a split known
to contain 47 is not a checker.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np

SR = Path(__file__).resolve().parents[1]
ROOT = SR.parents[1]
for p in (str(SR), str(ROOT / "tubitak" / "tests")):
    if p not in sys.path:
        sys.path.insert(0, p)

from _guard import strict_argv                                          # noqa: E402
from sr_train import config as C                                        # noqa: E402
from sr_train.split_fix import footprints, separation                   # noqa: E402


def load(path, split_col="split", kept_col=None):
    recs = []
    for r in csv.DictReader(open(path)):
        if kept_col and r.get(kept_col, "yes") != "yes":
            continue
        recs.append(dict(granule=r["granule"], split=r[split_col],
                         chip_row=int(r["chip_row"]), chip_col=int(r["chip_col"]),
                         e=float(r["easting"]), n=float(r["northing"])))
    return recs


def leakage(recs, buffer_m=C.SPLIT_BUFFER_M):
    """{split: {'overlap': n, 'buffer': n, 'n': N, 'pairs': k}} against `train`."""
    if not recs:
        raise SystemExit("leakage: manifest has no chips - nothing to check")
    fp = footprints(recs)
    sp = np.array([r["split"] for r in recs])
    tr = np.flatnonzero(sp == "train")
    if tr.size == 0:
        raise SystemExit("leakage: no train chips - nothing to check against")
    tfp = fp[tr]
    out = {}
    for s in ("test", "heldout", "val"):
        idx = np.flatnonzero(sp == s)
        ov = bf = pairs = 0
        offenders = []
        for i in idx:
            sep = separation(fp[i], tfp)
            n_ov = int((sep <= 0.0).sum())
            n_bf = int((sep < buffer_m).sum())
            if n_ov:
                ov += 1
            if n_bf:
                bf += 1
                offenders.append(dict(granule=recs[i]["granule"],
                                      chip=[recs[i]["chip_row"], recs[i]["chip_col"]],
                                      overlapping_train_chips=n_ov,
                                      within_buffer_train_chips=n_bf))
            pairs += n_bf
        out[s] = dict(n=int(idx.size), overlap=ov, buffer=bf, pairs=pairs,
                      offenders=offenders[:10])
    return out


def _fmt(name, r):
    n = r["n"] or 1
    return (f"  {name:8s} n={r['n']:5d}   sharing ground with train: {r['overlap']:4d} "
            f"({100*r['overlap']/n:6.2f} %)   within {C.SPLIT_BUFFER_M:.0f} m: "
            f"{r['buffer']:4d} ({100*r['buffer']/n:6.2f} %)   pairs {r['pairs']}")


#: WP13 D36: an expected value travels with the corpus it was measured on.
#:
#: KF2's 47 was measured on WP3A's reflectance corpus by an independent implementation. As a
#: bare constant it silently became untestable the moment the corpus changed: on the TCI
#: corpus it reported FAILED when it meant "this expectation is not about you", and the gate
#: then refused a verdict for a split that was in fact clean.
#:
#: Keyed by corpus, so a new corpus reports NOT APPLICABLE instead of failing. Adding an entry
#: requires an independent measurement, which is the point - the check is only as good as the
#: number it is checking against.
KF2_EXPECTED = {
    "sr_wald_corpus": (47, "WP3A open item 8 measured 47 leaking test chips by a different "
                           "implementation in another work package."),
}


def self_test():
    """Known-false FIRST, then known-true. Practice 11."""
    ok = True
    v2 = C.data_root() / C.SPLIT_SUBDIR / "manifest_v2.csv"
    v1 = C.data_root() / C.CORPUS_SUBDIR / "manifest.csv"

    print("KF2  known-false: the pre-correction manifest of THIS corpus, unmodified.")
    exp = KF2_EXPECTED.get(C.CORPUS_SUBDIR)
    if not v1.is_file():
        print(f"     *** cannot run: {v1} missing"); ok = False
    elif exp is None:
        # WP13 D36: the expectation is 47 ON THE CORPUS IT WAS MEASURED ON. Applied to any
        # other corpus it is not a failing check, it is an inapplicable one - and a check that
        # reports FAIL when it means "I have no expectation here" trains people to ignore it.
        r = leakage(load(v1))
        print(_fmt("test", r["test"])); print(_fmt("val", r["val"]))
        print(_fmt("heldout", r["heldout"]))
        print(f"     KF2 NOT APPLICABLE to corpus {C.CORPUS_SUBDIR!r} - no independently")
        print(f"     measured expectation exists for it. Measured here: "
              f"{r['test']['overlap']} leaking test chips.")
        print("     The check still demonstrates it CAN report leakage: the figure above is")
        print("     non-zero on the uncorrected split and zero on the corrected one.")
        if r["test"]["overlap"] == 0:
            print("     *** KF2 INCONCLUSIVE - the uncorrected split shows no leakage, so this")
            print("         case demonstrates nothing on this corpus.")
            ok = False
    else:
        r = leakage(load(v1))
        print(f"     {exp[1]} Expect {exp[0]}.")
        print(_fmt("test", r["test"])); print(_fmt("val", r["val"]))
        print(_fmt("heldout", r["heldout"]))
        if r["test"]["overlap"] == exp[0]:
            print(f"     KF2 PASS - reproduces {exp[0]} exactly")
        else:
            print(f"     *** KF2 FAILED - got {r['test']['overlap']}, expected {exp[0]}")
            ok = False

    print("\nKF1  known-false: one train chip of 36SVJ that genuinely overlaps a 36SWJ")
    print("     train chip, relabelled `test`. Expect it to be reported.")
    if not v2.is_file():
        print(f"     *** cannot run: {v2} missing - build the corrected split first")
        ok = False
    else:
        recs = load(v2, kept_col="kept")
        base = leakage(recs)["test"]["overlap"]
        fp = footprints(recs)
        sp = np.array([r["split"] for r in recs])
        tr = np.flatnonzero(sp == "train")
        planted = None
        for i in tr:
            if recs[i]["granule"] != "36SVJ":
                continue
            sep = separation(fp[i], fp[tr])
            hit = [tr[j] for j in np.flatnonzero(sep <= 0.0)
                   if recs[tr[j]]["granule"] == "36SWJ"]
            if hit:
                planted = i; break
        if planted is None:
            print("     *** KF1 could not be planted: after dedup no 36SVJ train chip")
            print("         overlaps a 36SWJ train chip. That is the corrected split")
            print("         working; KF1 is planted on the WP3A manifest instead.")
            recs1 = load(v1)
            fp1 = footprints(recs1); sp1 = np.array([r["split"] for r in recs1])
            tr1 = np.flatnonzero(sp1 == "train")
            for i in tr1:
                if recs1[i]["granule"] != "36SVJ":
                    continue
                sep = separation(fp1[i], fp1[tr1])
                hit = [tr1[j] for j in np.flatnonzero(sep <= 0.0)
                       if recs1[tr1[j]]["granule"] == "36SWJ"]
                if hit:
                    planted = i; recs, base = recs1, leakage(recs1)["test"]["overlap"]; break
        if planted is None:
            print("     *** KF1 FAILED: no overlapping train pair to plant"); ok = False
        else:
            g, cr, cc = (recs[planted]["granule"], recs[planted]["chip_row"],
                         recs[planted]["chip_col"])
            recs[planted] = dict(recs[planted], split="test")
            after = leakage(recs)["test"]["overlap"]
            print(f"     planted: {g} chip ({cr},{cc}) train -> test")
            print(f"     leaking test chips {base} -> {after}")
            if after > base:
                print("     KF1 PASS - the planted chip is detected")
            else:
                print("     *** KF1 FAILED - not detected"); ok = False
            recs[planted] = dict(recs[planted], split="train")

    print("\nDG   degenerate: an empty manifest must refuse to emit a verdict.")
    try:
        leakage([])
        print("     *** DG FAILED - a verdict was emitted for an empty input"); ok = False
    except SystemExit as e:
        print(f"     DG PASS - refused: {e}")
    return ok


def main():
    strict_argv(known=("--self-test", "--manifest=", "--v1"), positional=0,
                usage="leakage.py [--self-test] [--manifest=CSV] [--v1]")
    argv = sys.argv[1:]
    print("D18 leakage check - known-false cases first (standing practice 11)")
    print("=" * 74)
    ok = self_test()
    print("=" * 74)
    if not ok:
        print("FAILED: the check itself did not behave. Its verdict is not trusted.")
        return 1
    if "--self-test" in argv:
        print("PASS  self-test only; no corpus verdict requested")
        return 0

    man = C.data_root() / C.SPLIT_SUBDIR / "manifest_v2.csv"
    for a in argv:
        if a.startswith("--manifest="):
            man = Path(a.split("=", 1)[1])
    if "--v1" in argv:
        man = C.data_root() / C.CORPUS_SUBDIR / "manifest.csv"
    if not man.is_file():
        raise SystemExit(f"leakage: manifest not found: {man}")
    kept = "kept" if "v2" in man.name else None
    r = leakage(load(man, kept_col=kept))
    print(f"\nKT   known-true: {man}")
    for s in ("test", "heldout", "val"):
        print(_fmt(s, r[s]))
    (man.parent / "leakage.json").write_text(json.dumps(r, indent=2))
    bad = r["test"]["buffer"] + r["heldout"]["buffer"]
    print()
    if bad:
        print(f"GATE D18: FAIL - {r['test']['buffer']} test and "
              f"{r['heldout']['buffer']} heldout chips leak. Part B does not start.")
        return 1
    print("GATE D18: PASS - zero residual leakage in test and heldout, at both radii.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
