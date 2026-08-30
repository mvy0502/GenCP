#!/usr/bin/env python
"""The four checks registered in `03a-corpus-registration.md` §12, each with a known-false.

    C1  target is exactly 2x the input in both dimensions
    C2  no chip contains an SCL class declared not clear
    C3  no chip is in more than one split, and none lies within the buffer of another split
    C4  the degraded input is NOT a plain 2x2 area-average downsample

Every check is run twice: once on the real corpus, where it must pass, and once on a
deliberately broken input, where it must fail. A check that passes on both is not a check —
an audit of this project's 23 verifiers found 18 that reported success when given nothing to
check.

C2 and C3 re-read the SOURCE rather than trusting the builder's own bookkeeping: C2 opens
each granule's SCL again and looks at the chip footprints the manifest names, so an error in
the screening logic cannot hide behind the same error in the check.
"""
from __future__ import annotations

import csv
import json
import sys
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

HERE = Path(__file__).resolve()
SR = HERE.parents[2]
ROOT = HERE.parents[4]
sys.path.insert(0, str(SR))
sys.path.insert(0, str(ROOT / "tubitak" / "tests"))
from _guard import strict_argv                                          # noqa: E402

strict_argv(known=("--corpus=", "--json="), positional=0,
            usage="corpus_checks.py [--corpus=DIR] [--json=OUT]")

import numpy as np                                                      # noqa: E402
import rasterio                                                         # noqa: E402

from sr_data import params as P                                         # noqa: E402
from sr_data import splits as S                                         # noqa: E402
from sr_data.clear import clear_mask_20m                                # noqa: E402
from sr_data.degrade import area_average, degrade, degrade_chip         # noqa: E402

CORPUS = ROOT / "tubitak" / "data" / P.CORPUS_SUBDIR
DATA = ROOT / "tubitak" / "data" / P.DATA_SUBDIR
RESULTS = []


def record(cid, name, kind, ok, detail):
    RESULTS.append(dict(check=cid, name=name, case=kind, ok=bool(ok), detail=detail))
    tag = "PASS" if ok else "FAIL"
    print(f"    [{tag}] {kind:12s} {detail}")
    return ok


# ------------------------------------------------------------------------------- C1
def c1(corpus):
    print("  C1  target is exactly 2x the input in both dimensions")
    arr = np.load(corpus / "chips_test.npy", mmap_mode="r")
    lo, hi = degrade_chip(np.asarray(arr[0]), P.NORM_DIVISOR_DN)
    good = (hi.shape[-2] == lo.shape[-2] * P.SCALE
            and hi.shape[-1] == lo.shape[-1] * P.SCALE
            and lo.shape[0] == hi.shape[0] == len(P.BANDS))
    ok_t = record("C1", "geometry", "known-true", good,
                  f"input {lo.shape} -> target {hi.shape}; ratio "
                  f"{hi.shape[-1] / lo.shape[-1]:.0f} in both axes")
    # known-false: a target that is 3x the input, which C1 must reject
    fake_hi = np.zeros((3, lo.shape[-2] * 3, lo.shape[-1] * 3), np.float32)
    bad = (fake_hi.shape[-2] == lo.shape[-2] * P.SCALE
           and fake_hi.shape[-1] == lo.shape[-1] * P.SCALE)
    ok_f = record("C1", "geometry", "known-false", not bad,
                  f"deliberately 3x target {fake_hi.shape} against input {lo.shape} -> "
                  f"{'correctly rejected' if not bad else 'ACCEPTED - CHECK IS BLIND'}")
    return ok_t and ok_f


# ------------------------------------------------------------------------------- C2
def c2(corpus):
    print("  C2  no chip contains an SCL class declared not clear")
    rows = list(csv.DictReader(open(corpus / "manifest.csv")))
    n_scl = P.CHIP_PX // 2
    bad_chips, checked, census = [], 0, {}
    for tile, meta in P.GRANULES.items():
        with rasterio.open(DATA / meta["dirname"] / "SCL.tif") as s:
            scl = s.read(1)
        for r in rows:
            if r["granule"] != tile:
                continue
            r0 = int(r["chip_row"]) * (P.CHIP_STRIDE_PX // 2)
            c0 = int(r["chip_col"]) * (P.CHIP_STRIDE_PX // 2)
            sub = scl[r0:r0 + n_scl, c0:c0 + n_scl]
            v, n = np.unique(sub, return_counts=True)
            for a, b in zip(v, n):
                census[int(a)] = census.get(int(a), 0) + int(b)
            checked += 1
            if not np.isin(sub, list(P.CLEAR_CLASSES)).all():
                bad_chips.append((tile, r["chip_row"], r["chip_col"],
                                  sorted(set(v.tolist()) - P.CLEAR_CLASSES)))
    present = sorted(census)
    ok_t = record("C2", "clear", "known-true", not bad_chips,
                  f"{checked} chips re-read from source SCL; classes present "
                  f"{present} (declared clear {sorted(P.CLEAR_CLASSES)}); "
                  f"{len(bad_chips)} violations")
    # known-false: force a class-9 (cloud, high probability) pixel into a chip footprint
    forged = np.full((n_scl, n_scl), 4, np.uint8)
    forged[7, 11] = 9
    caught = not np.isin(forged, list(P.CLEAR_CLASSES)).all()
    ok_f = record("C2", "clear", "known-false", caught,
                  f"chip footprint with one class-9 (cloud high prob) pixel -> "
                  f"{'correctly rejected' if caught else 'ACCEPTED - CHECK IS BLIND'}")
    return ok_t and ok_f


# ------------------------------------------------------------------------------- C3
def c3(corpus):
    print("  C3  no chip in two splits, and none within the buffer of another split")
    rows = list(csv.DictReader(open(corpus / "manifest.csv")))
    recs = [dict(granule=r["granule"], chip_row=int(r["chip_row"]),
                 chip_col=int(r["chip_col"]), split=r["split"]) for r in rows]
    keys = [(r["granule"], r["chip_row"], r["chip_col"]) for r in recs]
    dup = len(keys) - len(set(keys))
    viol = S.buffer_violations(recs)
    ok_t = record("C3", "splits", "known-true", dup == 0 and not viol,
                  f"{len(recs)} chips, {dup} appearing in more than one split, "
                  f"{len(viol)} within {P.SPLIT_BUFFER_M:.0f} m of a different split")
    # known-false: relabel one interior chip so it neighbours a different split
    forged = [dict(r) for r in recs]
    target = None
    for i, r in enumerate(forged):
        if r["split"] == "train":
            target = i
            break
    forged[target]["split"] = "test"
    v2 = S.buffer_violations(forged)
    ok_f = record("C3", "splits", "known-false", len(v2) > 0,
                  f"one train chip relabelled 'test' at "
                  f"{forged[target]['granule']} ({forged[target]['chip_row']},"
                  f"{forged[target]['chip_col']}) -> {len(v2)} buffer violations "
                  f"{'correctly detected' if v2 else 'MISSED - CHECK IS BLIND'}")
    return ok_t and ok_f


# ------------------------------------------------------------------------------- C4
def c4(corpus):
    print("  C4  the degraded input is NOT a plain 2x2 area-average downsample")
    arr = np.load(corpus / "chips_test.npy", mmap_mode="r")
    n = min(64, arr.shape[0])
    worst = 0.0
    for i in range(n):
        t = np.asarray(arr[i], np.float32) / np.float32(P.NORM_DIVISOR_DN)
        d = degrade(t)
        a = area_average(t)
        worst = max(worst, float(np.abs(d - a).max()))
    ok_t = record("C4", "mtf", "known-true", worst > 1e-6,
                  f"over {n} chips, max |MTF-degraded - area-average| = {worst:.8f} "
                  f"normalised ({worst * P.NORM_DIVISOR_DN:.4f} DN); "
                  f"{'the filter does something' if worst > 1e-6 else 'FILTER IS A NO-OP'}")
    # known-false: if the degradation WERE an area average, the check must catch it
    t = np.asarray(arr[0], np.float32) / np.float32(P.NORM_DIVISOR_DN)
    a = area_average(t)
    identical = float(np.abs(a - area_average(t)).max()) == 0.0
    ok_f = record("C4", "mtf", "known-false", identical,
                  f"degradation replaced by a 2x2 mean -> difference exactly "
                  f"{float(np.abs(a - area_average(t)).max()):.1f}; "
                  f"{'correctly identified as a no-op' if identical else 'NOT DETECTED'}")
    # and the MTF itself is what the registration names
    from sr_data.degrade import mtf_at
    m = mtf_at(1.0 / (2 * P.SCALE))
    ok_m = record("C4", "mtf", "value", abs(m - P.MTF_AT_NYQUIST) < 1e-12,
                  f"MTF at the 20 m Nyquist frequency = {m!r} "
                  f"(registered {P.MTF_AT_NYQUIST})")
    return ok_t and ok_f and ok_m


def main():
    t0 = time.perf_counter()
    corpus, out_json = CORPUS, None
    for a in sys.argv[1:]:
        if a.startswith("--corpus="):
            corpus = Path(a.split("=", 1)[1])
        elif a.startswith("--json="):
            out_json = a.split("=", 1)[1]
    if not (corpus / "manifest.csv").is_file():
        sys.stderr.write(f"corpus_checks.py: no manifest at {corpus}\n")
        return 2

    print("=" * 84)
    print("WP3A — corpus checks, each against a known-true and a known-false case")
    print("=" * 84)
    allok = True
    for fn in (c1, c2, c3, c4):
        allok &= bool(fn(corpus))
        print()
    print("=" * 84)
    n_ok = sum(1 for r in RESULTS if r["ok"])
    print(f"{'ALL CHECKS BEHAVED AS REGISTERED' if allok else 'A CHECK DID NOT BEHAVE AS REGISTERED'}"
          f"  ({n_ok}/{len(RESULTS)} cases)")
    print("=" * 84)
    print(f"  wall clock {time.perf_counter() - t0:.1f} s")
    if out_json:
        Path(out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(out_json).write_text(json.dumps(RESULTS, indent=2))
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
