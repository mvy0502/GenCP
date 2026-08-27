#!/usr/bin/env python
"""Apply the EUROPEAN confidence band boundaries, unchanged, to the Ankara chips.

Executes tubitak/docs/confidence-registration-3.md. The boundaries are read from
gencp_core.confidence.CALIBRATION and are not recomputed here - re-deriving them on Ankara
would guarantee a monotone, well-separated result and would measure nothing.

    /opt/homebrew/Caskroom/miniforge/base/envs/gencp/bin/python \
        tubitak/scripts/confidence_transfer.py
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tubitak"))

import numpy as np

from gencp_core import confidence as C

OUT = ROOT / "tubitak/docs/evidence/confidence"
FILES = {"europe": OUT / "per_chip_onnx.csv", "ankara": OUT / "per_chip_onnx_ankara.csv"}
SEP_MIN = 1.5          # registered
ABS_TOL = 0.50         # registered
BOOT = 10_000
SEED = 20260827


def load(path):
    rows = list(csv.DictReader(open(path)))
    d = np.array([float(r["conf_D"]) for r in rows])
    e = np.array([float(r["err_C2"]) for r in rows])
    return d, e


def banded(conf_D, err):
    """Score and band with the CALIBRATION constants exactly as the plugin does."""
    z = C.deployed_score(conf_D)
    b = C.band_map(z)
    out = {}
    for v, name in ((C.BAND_RED, "red"), (C.BAND_AMBER, "amber"), (C.BAND_GREEN, "green")):
        m = b == v
        out[name] = dict(
            n=int(m.sum()),
            median=(float(np.median(err[m])) if m.any() else None),
            iqr=(float(np.subtract(*np.percentile(err[m], [75, 25]))) if m.any() else None))
    return out, z, b


def boot_median_ratio(err, b, reps=BOOT, seed=SEED):
    """95% CI for median(red)/median(green), resampling chips."""
    rng = np.random.default_rng(seed)
    r = err[b == C.BAND_RED]
    g = err[b == C.BAND_GREEN]
    if len(r) == 0 or len(g) == 0:
        return None
    vals = [np.median(rng.choice(r, len(r), True)) / np.median(rng.choice(g, len(g), True))
            for _ in range(reps)]
    return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


def main():
    cal = C.CALIBRATION
    print("=" * 78)
    print("REGISTRATION 3 - European bands applied UNCHANGED to Ankara")
    print("=" * 78)
    print(f"  score          : {C.ACTIVE_SCORE}")
    print(f"  normalisation  : mean {cal['conf_D_mean']}, std {cal['conf_D_std']}  (European)")
    print(f"  boundaries     : red <= {cal['red_hi']}, green >= {cal['green_lo']}")
    print("  neither is recomputed here\n")

    res = {}
    for corpus, path in FILES.items():
        d, e = load(path)
        bands, z, b = banded(d, e)
        res[corpus] = dict(n=len(d), corpus_median=float(np.median(e)), bands=bands,
                           ratio_ci=boot_median_ratio(e, b))
        print(f"  {corpus:6s}: {len(d)} chips, corpus median {np.median(e):.4f} px")
    print()

    def fmt(v, w, dec=4):
        return "—".rjust(w) if v is None else f"{v:>{w}.{dec}f}"

    print(f"  {'band':6s} {'n EU':>5} {'med EU':>9} {'IQR EU':>8} "
          f"{'n ANK':>6} {'med ANK':>9} {'IQR ANK':>8}  {'ANK vs EU':>10}")
    for band in ("red", "amber", "green"):
        eu = res["europe"]["bands"][band]
        an = res["ankara"]["bands"][band]
        rel = (None if (eu["median"] is None or an["median"] is None)
               else (an["median"] - eu["median"]) / eu["median"])
        rel_s = "—".rjust(10) if rel is None else f"{rel * 100:>+9.1f}%"
        print(f"  {band:6s} {eu['n']:>5} {fmt(eu['median'], 9)} {fmt(eu['iqr'], 8)} "
              f"{an['n']:>6} {fmt(an['median'], 9)} {fmt(an['iqr'], 8)}  {rel_s}")
    print()

    # --- registered criteria -----------------------------------------------------------
    a = res["ankara"]["bands"]
    have_all = all(a[k]["median"] is not None for k in ("red", "amber", "green"))
    c1 = have_all and a["red"]["median"] > a["amber"]["median"] > a["green"]["median"]
    ratio = (a["red"]["median"] / a["green"]["median"]) if have_all else None
    c2 = have_all and ratio >= SEP_MIN
    devs = {}
    for band in ("red", "amber", "green"):
        eu, an = res["europe"]["bands"][band]["median"], a[band]["median"]
        devs[band] = None if an is None else abs(an - eu) / eu
    c3 = all(v is not None and v <= ABS_TOL for v in devs.values())

    print("  REGISTERED CRITERIA")
    print(f"    1 ordinal   median(red) > median(amber) > median(green)      : "
          f"{'PASS' if c1 else 'FAIL'}")
    if have_all:
        print(f"                {a['red']['median']:.4f} > {a['amber']['median']:.4f} "
              f"> {a['green']['median']:.4f}")
    ci = res["ankara"]["ratio_ci"]
    print(f"    2 separation red/green >= {SEP_MIN}                              : "
          f"{'PASS' if c2 else 'FAIL'}")
    print(f"                Ankara {ratio:.2f}x"
          f"{'' if ci is None else f'  95% CI [{ci[0]:.2f}, {ci[1]:.2f}]'}"
          f"   (Europe 2.49x)")
    print(f"    3 absolute  |ANK - EU| / EU <= {ABS_TOL} for every band          : "
          f"{'PASS' if c3 else 'FAIL'}")
    for band, v in devs.items():
        print(f"                {band:6s} {'—' if v is None else f'{v*100:.1f}%'}")

    print()
    print(f"  VERDICT: ordinal {'transfers' if c1 else 'DOES NOT transfer'}; "
          f"separation {'holds' if c2 else 'does NOT hold'}; "
          f"absolute levels {'transfer' if c3 else 'DO NOT transfer'}")

    res["criteria"] = dict(ordinal=bool(c1), separation=bool(c2), absolute=bool(c3),
                           ratio_ankara=ratio, deviations=devs,
                           sep_min=SEP_MIN, abs_tol=ABS_TOL)
    (OUT / "transfer_results.json").write_text(json.dumps(res, indent=2))
    print(f"\nwrote {OUT/'transfer_results.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
