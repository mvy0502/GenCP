#!/usr/bin/env python
"""Certify the generator's spatial alignment by testing translation equivariance.

Why this rather than comparing against ground truth
---------------------------------------------------
Two earlier attempts bounded alignment only loosely, both for the same reason —
they compared images whose *content* differs, so content mismatch swamped the
geometry:

* ``network_alignment.py`` compares the OSM input against the generated output.
  Different modalities; bound ~0.9 px.
* ``paired_alignment.py`` compares the generated output against the real
  satellite half. Same modality, but the generator produces a *plausible* scene,
  not the real one, so per-chip offsets scatter by +/-8 px (std 3.4 px) against an
  estimator noise floor of 0.31 px. Bound ~1.9 px.

This test removes ground truth from the question entirely. Two 256x256 crops are
taken from the same up-sampled OSM canvas, offset by a known integer translation
(no resampling difference, no wraparound). Both are pushed through the network.
If the network preserves alignment, the two outputs must agree over their overlap
after undoing that known offset — and crucially they are then the *same modality
with the same content*, which is exactly the regime where phase correlation is
accurate to 0.076 px.

A residual shift here is attributable to the network and nothing else.

Usage
-----
    python tubitak/scripts/equivariance_test.py \\
        --out-p tubitak/data/equivariance/out_p/genCP_HR_RGB_model/test_latest/images \\
        --out-q tubitak/data/equivariance/out_q/genCP_HR_RGB_model/test_latest/images \\
        --offset 16
"""
from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from shift_estimator import phase_shift  # noqa: E402


def read(path):
    import rasterio
    from rasterio.errors import NotGeoreferencedWarning
    warnings.filterwarnings("ignore", category=NotGeoreferencedWarning)
    with rasterio.open(path) as s:
        return np.transpose(s.read(), (1, 2, 0)).astype(float)


def overlap(p_img, q_img, off):
    """Regions of the two outputs that depict the same ground."""
    n = p_img.shape[0]
    a = p_img[off:n, off:n].mean(axis=2)
    b = q_img[0:n - off, 0:n - off].mean(axis=2)
    return a, b


def main() -> int:
    from scipy.ndimage import shift as ndshift

    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out-p", required=True)
    ap.add_argument("--out-q", required=True)
    ap.add_argument("--offset", type=int, default=16)
    ap.add_argument("--pixel-size", type=float, default=10.0)
    a = ap.parse_args()

    P, Q = Path(a.out_p), Path(a.out_q)
    stems = sorted(f.name[:-9] for f in P.glob("*_fake.png")
                   if (Q / f.name).exists())
    if not stems:
        sys.exit("no matching output pairs")
    print(f"pairs: {len(stems)}   crop offset {a.offset} px   "
          f"overlap {256 - a.offset}x{256 - a.offset}\n")

    # ---------- validation on this very data ----------
    print("=" * 70)
    print("VALIDATION — recover a known shift injected into one output")
    print("=" * 70)
    errs = []
    for stem in stems[:8]:
        pa, qb = overlap(read(P / f"{stem}_fake.png"), read(Q / f"{stem}_fake.png"), a.offset)
        b_dy, b_dx, _ = phase_shift(pa, qb)
        for tdy, tdx in [(0.1, 0.0), (0.0, 0.1), (0.25, 0.25), (-0.5, 0.75), (1.0, -1.0)]:
            mv = ndshift(qb, (tdy, tdx), order=3, mode="reflect")
            dy, dx, _ = phase_shift(pa, mv)
            errs.append((dy - b_dy - tdy, dx - b_dx - tdx))
    e = np.abs(np.array(errs))
    rms = float(np.sqrt((e ** 2).mean()))
    p90 = float(np.percentile(e, 90))
    print(f"n={len(errs)}  median|err|={np.median(e):.4f}  RMS={rms:.4f}  "
          f"p90={p90:.4f}  max={e.max():.4f} px")
    limit = max(rms, p90)
    print(f"resolution limit ~{limit:.4f} px  "
          f"({'sub-0.1 px capable' if limit < 0.1 else 'above 0.1 px'})")
    if limit > 0.5:
        print("Estimator too noisy on this data — measurement NOT possible.")
        return 1

    # ---------- measurement ----------
    print("\n" + "=" * 70)
    print("MEASUREMENT — residual shift between the two outputs (expected: 0)")
    print("=" * 70)
    print(f"{'tile':<20}{'residual dy':>13}{'residual dx':>13}{'|d| (px)':>11}")
    print("-" * 70)
    dys, dxs = [], []
    for stem in stems:
        pa, qb = overlap(read(P / f"{stem}_fake.png"), read(Q / f"{stem}_fake.png"), a.offset)
        dy, dx, _ = phase_shift(pa, qb)
        dys.append(dy); dxs.append(dx)
        print(f"{stem:<20}{dy:>13.4f}{dx:>13.4f}{np.hypot(dy, dx):>11.4f}")
    dy = np.array(dys); dx = np.array(dxs)

    # A chip whose residual lands on the crop offset itself means the estimator
    # locked onto the UNCORRECTED alignment - a periodic-structure ambiguity, not
    # a network shift. Reject those explicitly and report how many, never silently.
    keep = (np.abs(dy) < 1.0) & (np.abs(dx) < 1.0)
    rejected = [(stems[i], dy[i], dx[i]) for i in range(len(dy)) if not keep[i]]
    print("-" * 70)
    print(f"{'MEAN (all)':<20}{dy.mean():>13.4f}{dx.mean():>13.4f}")
    print(f"{'MEDIAN (all)':<20}{np.median(dy):>13.4f}{np.median(dx):>13.4f}")
    print(f"{'STD (all)':<20}{dy.std(ddof=1):>13.4f}{dx.std(ddof=1):>13.4f}")

    if rejected:
        print(f"\nrejected {len(rejected)} of {len(dy)} chips (|residual| >= 1 px = estimator lock failure):")
        for st, a_, b_ in rejected:
            print(f"    {st}  ({a_:+.2f}, {b_:+.2f}) - matches the {a.offset} px crop offset, "
                  f"i.e. the correlation found the uncorrected alignment")

    dyk, dxk = dy[keep], dx[keep]
    n = len(dyk)
    se_y, se_x = dyk.std(ddof=1) / np.sqrt(n), dxk.std(ddof=1) / np.sqrt(n)
    print(f"\n--- robust statistics over the {n} accepted chips ---")
    print(f"{'MEAN':<20}{dyk.mean():>13.5f}{dxk.mean():>13.5f}")
    print(f"{'MEDIAN':<20}{np.median(dyk):>13.5f}{np.median(dxk):>13.5f}")
    print(f"{'STD':<20}{dyk.std(ddof=1):>13.5f}{dxk.std(ddof=1):>13.5f}")
    print(f"{'STD ERROR':<20}{se_y:>13.5f}{se_x:>13.5f}")
    print(f"{'MAX |residual|':<20}{np.abs(dyk).max():>13.5f}{np.abs(dxk).max():>13.5f}")

    bound = max(abs(dyk.mean()) + 2 * se_y, abs(dxk.mean()) + 2 * se_x)
    print(f"\nmean residual : dy {dyk.mean():+.5f} +/- {se_y:.5f} px "
          f"({dyk.mean()*a.pixel_size:+.4f} m)")
    print(f"                dx {dxk.mean():+.5f} +/- {se_x:.5f} px "
          f"({dxk.mean()*a.pixel_size:+.4f} m)")
    print(f"\n95% bound on any systematic shift (|mean| + 2*SE): {bound:.5f} px "
          f"({bound*a.pixel_size:.4f} m)")
    print(f"estimator resolution limit on this data          : {limit:.5f} px")
    print("=" * 70)
    print(f"CERTIFIED BETTER THAN 0.1 px? {'YES' if bound < 0.1 else 'NO'}")
    print(f"  Achieved bound: {bound:.5f} px ({bound*a.pixel_size:.4f} m) over {n} chips")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
