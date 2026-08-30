#!/usr/bin/env python
"""D7 diagnostic — which DN-to-reflectance conversion is physical?

Fixed decision D7 says the conversion is a division by 10000 with NO BOA offset, and tells
this work package to check it rather than trust it. So both candidate conversions are
implemented here and reported side by side:

    A  (chosen)       reflectance = DN / 10000
    B  (alternative)  reflectance = DN / 10000 + (-0.1)      == (DN - 1000) / 10000

B is what the STAC `raster:bands` block declares (`scale: 0.0001, offset: -0.1`). A is what
`boa_offset_applied: true` in the same STAC properties, and `scale 1.0 / offset 0.0` in the
GeoTIFF itself, both imply. WP2A §7 flagged the contradiction and declined to resolve it.

The test is physical, not stylistic: surface reflectance cannot be negative, and clear land
in the visible bands sits at a few per cent to a few tens of per cent. A conversion that puts
the MEDIAN of half a billion clear land pixels below zero is not a candidate.

Sample, stated exactly: every clear pixel of all five granules, where clear means the
pixel's own SCL class is in `params.CLEAR_CLASSES`, expanded from 20 m to 10 m by exact
2 x 2 replication. Statistics come from a full 65536-bin histogram of the whole population,
so percentiles are exact integers over every pixel rather than estimates from a subsample.
"""
from __future__ import annotations

import json
import sys
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

HERE = Path(__file__).resolve()
SR = HERE.parents[2]                     # tubitak/sr
ROOT = HERE.parents[4]                   # repository root
sys.path.insert(0, str(SR))
sys.path.insert(0, str(ROOT / "tubitak" / "tests"))
from _guard import strict_argv                                          # noqa: E402

strict_argv(known=("--json=",), positional=0, usage="d7_radiometry.py [--json=OUT]")

import numpy as np                                                      # noqa: E402
import rasterio                                                         # noqa: E402

from sr_data import params as P                                         # noqa: E402
from sr_data.clear import (clear_mask_20m, expand_to_10m,                # noqa: E402
                           require_nested)

DATA = ROOT / "tubitak" / "data" / P.DATA_SUBDIR
NBINS = 65536


def granule_hist(tile, meta):
    """65536-bin histogram of clear DN per band, for one granule."""
    d = DATA / meta["dirname"]
    with rasterio.open(d / "SCL.tif") as s:
        scl_prof, scl = s.profile, s.read(1)
    hists, n_clear = {}, None
    for band in P.BANDS:
        with rasterio.open(d / f"{band}.tif") as s:
            prof = s.profile
            require_nested(prof, scl_prof, who=f"{tile}/{band}")
            mask = expand_to_10m(clear_mask_20m(scl))
            h = np.zeros(NBINS, np.int64)
            for r0 in range(0, s.height, 1024):
                n = min(1024, s.height - r0)
                w = rasterio.windows.Window(0, r0, s.width, n)
                a = s.read(1, window=w)
                m = mask[r0:r0 + n]
                h += np.bincount(a[m].astype(np.int64), minlength=NBINS)
            hists[band] = h
            if n_clear is None:
                n_clear = int(mask.sum())
    return hists, n_clear


def pct_from_hist(h, q):
    """Exact q-quantile DN from a full histogram (q in [0, 1])."""
    c = np.cumsum(h)
    n = c[-1]
    return int(np.searchsorted(c, q * n, side="left"))


def main():
    t0 = time.perf_counter()
    out_json = None
    for a in sys.argv[1:]:
        if a.startswith("--json="):
            out_json = a.split("=", 1)[1]

    print("=" * 86)
    print("D7 — DN to reflectance: both conversions, measured on the same clear pixels")
    print("=" * 86)
    print(f"  sample     : every clear pixel of all five granules")
    print(f"  clear       : SCL class in {sorted(P.CLEAR_CLASSES)} "
          f"({', '.join(P.SCL_MEANING[c] for c in sorted(P.CLEAR_CLASSES))})")
    print(f"  source      : {DATA}")
    print(f"  A (chosen)  : reflectance = DN * {P.DN_TO_REFLECTANCE!r}")
    print(f"  B (alt)     : reflectance = DN * {P.DN_TO_REFLECTANCE!r} + (-0.1)")
    print(f"  numpy {np.__version__} · rasterio {rasterio.__version__} · "
          f"GDAL {rasterio.__gdal_version__}\n")

    total = {b: np.zeros(NBINS, np.int64) for b in P.BANDS}
    per_granule = {}
    for tile, meta in P.GRANULES.items():
        h, n_clear = granule_hist(tile, meta)
        per_granule[tile] = {b: int(h[b].sum()) for b in P.BANDS}
        for b in P.BANDS:
            total[b] += h[b]
        print(f"  {tile}: {n_clear:,} clear 10 m pixels")
    print()

    rows = []
    hdr = (f"  {'band':5s} {'n':>13s} {'p1':>7s} {'p50':>7s} {'p99.9':>7s} | "
           f"{'A p1':>9s} {'A p50':>9s} {'A p99.9':>9s} {'A frac<0':>9s} | "
           f"{'B p1':>9s} {'B p50':>9s} {'B p99.9':>9s} {'B frac<0':>9s}")
    print("  DN percentiles, then the same pixels under each conversion:")
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))
    for b in P.BANDS:
        h = total[b]
        n = int(h.sum())
        p1, p50, p999 = (pct_from_hist(h, q) for q in (0.01, 0.50, 0.999))
        # Fraction below zero. Under A that is DN < 0, impossible in uint16.
        # Under B it is DN < 1000.
        frac_a = 0.0
        frac_b = float(h[:1000].sum()) / n
        A = lambda dn: dn * P.DN_TO_REFLECTANCE                          # noqa: E731
        B = lambda dn: dn * P.DN_TO_REFLECTANCE - 0.1                    # noqa: E731
        print(f"  {b:5s} {n:13,d} {p1:7d} {p50:7d} {p999:7d} | "
              f"{A(p1):9.4f} {A(p50):9.4f} {A(p999):9.4f} {frac_a:9.4%} | "
              f"{B(p1):9.4f} {B(p50):9.4f} {B(p999):9.4f} {frac_b:9.4%}")
        rows.append(dict(band=b, n=n, dn_p1=p1, dn_p50=p50, dn_p999=p999,
                         A_p1=A(p1), A_p50=A(p50), A_p999=A(p999), A_frac_negative=frac_a,
                         B_p1=B(p1), B_p50=B(p50), B_p999=B(p999), B_frac_negative=frac_b))

    print()
    a_ok = all(r["A_p50"] > 0 and 0.01 <= r["A_p50"] <= 0.60 for r in rows)
    b_bad = any(r["B_p50"] < 0 for r in rows)
    print(f"  A: every band median in a physically ordinary range (0.01-0.60)   : "
          f"{'YES' if a_ok else 'NO'}")
    print(f"  B: at least one band median is NEGATIVE (impossible reflectance)  : "
          f"{'YES' if b_bad else 'NO'}")
    print()
    verdict = a_ok and b_bad
    print("=" * 86)
    if verdict:
        print("D7 CONFIRMED: A (divide by 10000, no offset) is physical; B is not.")
        print("              Proceeding on A, as fixed decision D7 specifies.")
    else:
        print("D7 NOT CONFIRMED: the observation does not match what D7 predicts.")
        print("                  STOP. Do not build the corpus on an unresolved conversion.")
    print("=" * 86)
    print(f"  wall clock {time.perf_counter() - t0:.1f} s")

    if out_json:
        Path(out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(out_json).write_text(json.dumps(
            dict(bands=rows, per_granule_clear_pixels=per_granule,
                 A_physical=a_ok, B_negative_median=b_bad, verdict=verdict), indent=2))
    return 0 if verdict else 1


if __name__ == "__main__":
    sys.exit(main())
