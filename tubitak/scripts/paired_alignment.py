#!/usr/bin/env python
"""Certify the generator's spatial alignment using paired satellite ground truth.

The earlier cross-modal attempt (``network_alignment.py``) compared the network's
OSM *input* against its generated output. Those are different modalities, which
forced a gradient proxy and bounded alignment only to ~0.9 px — too loose to be
useful for KARIOS.

The GenCP_HR_DB pairs are ``[satellite | OSM]``, so feeding the OSM half through
the network yields a generated image that can be compared against the **real
satellite half**. Both are satellite-modality, so plain phase correlation applies
and its 0.076 px accuracy (see ``shift_estimator.py --self-test``) is available.

Validation first, as always: a known displacement is injected into the generated
image and must be recovered before any zero-shift reading is trusted.

Usage
-----
    python tubitak/scripts/paired_alignment.py \\
        --generated tubitak/data/scale_test/out_a/genCP_HR_RGB_model/test_latest/images \\
        --reference tubitak/data/scale_test/refs_a
"""
from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from shift_estimator import ncc_shift, phase_shift, prepare  # noqa: E402

INJECTED = [(0.25, 0.0), (0.0, 0.25), (0.5, 0.5), (-1.0, 1.5), (2.0, -1.25)]


def read(path):
    import rasterio
    from rasterio.errors import NotGeoreferencedWarning
    warnings.filterwarnings("ignore", category=NotGeoreferencedWarning)
    with rasterio.open(path) as s:
        return np.transpose(s.read(), (1, 2, 0)).astype(float)


def field(ref, mov, grid, win, min_conf, estimator="ncc", smooth=4.0, max_shift=8):
    """Shift field over a grid x grid layout.

    Defaults chosen by measured sweep, not assumption: generated imagery shares
    only OSM-driven STRUCTURE with the real satellite half - its fine texture is
    hallucinated and uncorrelated. Phase correlation weights all frequencies
    equally after whitening and therefore locks onto that uncorrelated texture
    (measured resolution limit 0.92-8.5 px). Un-whitened NCC on a Gaussian-smoothed
    full chip keeps only the shared structure and reaches 0.307 px.
    """
    from scipy.ndimage import gaussian_filter
    R, M = prepare(ref, "intensity"), prepare(mov, "intensity")
    if smooth > 0:
        R, M = gaussian_filter(R, smooth), gaussian_filter(M, smooth)
    est = (lambda x, y: ncc_shift(x, y, max_shift=max_shift)) if estimator == "ncc" else phase_shift
    h, w = min(R.shape[0], M.shape[0]), min(R.shape[1], M.shape[1])
    sy, sx = h // grid, w // grid
    rows = []
    for i in range(grid):
        for j in range(grid):
            r0 = i * sy + (sy - win) // 2
            c0 = j * sx + (sx - win) // 2
            dy, dx, conf = est(R[r0:r0 + win, c0:c0 + win],
                               M[r0:r0 + win, c0:c0 + win])
            if np.isfinite(dy) and conf >= min_conf:
                rows.append(dict(dy=dy, dx=dx, conf=conf,
                                 yc=r0 + win / 2 - 0.5, xc=c0 + win / 2 - 0.5))
    return rows


def main() -> int:
    from scipy.ndimage import shift as ndshift

    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--generated", required=True, help="dir of <stem>_fake.png")
    p.add_argument("--reference", required=True, help="dir of <stem>.png (real satellite)")
    p.add_argument("--grid", type=int, default=1, help="grid x grid windows (1 = whole chip)")
    p.add_argument("--window", type=int, default=256)
    p.add_argument("--min-conf", type=float, default=0.0,
                   help="confidence floor (NCC scale; 0 keeps all)")
    p.add_argument("--estimator", default="ncc", choices=["ncc", "phase"])
    p.add_argument("--smooth", type=float, default=4.0,
                   help="Gaussian sigma before correlation; keeps shared structure only")
    p.add_argument("--pixel-size", type=float, default=10.0)
    p.add_argument("--limit", type=int, default=0, help="cap pairs (0 = all)")
    a = p.parse_args()

    gen_dir, ref_dir = Path(a.generated), Path(a.reference)
    stems = sorted(f.name[:-9] for f in gen_dir.glob("*_fake.png"))
    stems = [s for s in stems if (ref_dir / f"{s}.png").exists()]
    if a.limit:
        stems = stems[:a.limit]
    if not stems:
        sys.exit("no matching generated/reference pairs found")
    print(f"pairs: {len(stems)}   grid {a.grid}x{a.grid}   window {a.window}px   "
          f"estimator={a.estimator}   smooth={a.smooth}\n")

    # ---------------- validation ----------------
    print("=" * 74)
    print("VALIDATION — recover a known shift injected into the generated image")
    print("=" * 74)
    print(f"{'injected dy,dx':<18}{'recovered dy':>14}{'recovered dx':>14}{'err dy':>10}{'err dx':>10}")
    print("-" * 74)
    errs = []
    for stem in stems[:8]:
        ref = read(ref_dir / f"{stem}.png")
        gen = read(gen_dir / f"{stem}_fake.png")
        base = field(ref, gen, a.grid, a.window, a.min_conf, a.estimator, a.smooth)
        if not base:
            continue
        b_dy = float(np.median([r["dy"] for r in base]))
        b_dx = float(np.median([r["dx"] for r in base]))
        for tdy, tdx in INJECTED:
            mv = np.stack([ndshift(gen[..., k], (tdy, tdx), order=3, mode="reflect")
                           for k in range(gen.shape[2])], axis=-1)
            f2 = field(ref, mv, a.grid, a.window, a.min_conf, a.estimator, a.smooth)
            if not f2:
                continue
            rdy = float(np.median([r["dy"] for r in f2])) - b_dy
            rdx = float(np.median([r["dx"] for r in f2])) - b_dx
            errs.append((rdy - tdy, rdx - tdx))
    if not errs:
        sys.exit("validation could not run — no usable windows")
    e = np.abs(np.array(errs))
    for (tdy, tdx), (ey, ex) in list(zip(INJECTED * 99, errs))[:10]:
        print(f"{f'{tdy:+.2f}, {tdx:+.2f}':<18}{tdy + ey:>14.3f}{tdx + ex:>14.3f}{ey:>10.3f}{ex:>10.3f}")
    rms = float(np.sqrt((e ** 2).mean()))
    p90 = float(np.percentile(e, 90))
    print("-" * 74)
    print(f"n={len(errs)}  median|err|={np.median(e):.4f}  RMS={rms:.4f}  "
          f"p90={p90:.4f}  max={e.max():.4f} px")
    limit = max(rms, p90)
    print(f"VERDICT: resolution limit ~{limit:.3f} px "
          f"({'sub-0.1 px capable' if limit < 0.1 else 'above 0.1 px'})")
    if limit > 1.0:
        print("Estimator too noisy on this data — measurement NOT possible. Stopping.")
        return 1

    # ---------------- measurement ----------------
    print("\n" + "=" * 74)
    print("MEASUREMENT — generated output vs REAL satellite half (same modality)")
    print("=" * 74)
    print(f"{'tile':<20}{'n':>5}{'median dy':>12}{'median dx':>12}{'std dy':>9}{'std dx':>9}")
    print("-" * 74)
    all_dy, all_dx, all_yc, all_xc = [], [], [], []
    for stem in stems:
        rows = field(read(ref_dir / f"{stem}.png"), read(gen_dir / f"{stem}_fake.png"),
                     a.grid, a.window, a.min_conf, a.estimator, a.smooth)
        if not rows:
            print(f"{stem:<20}{0:>5}{'--':>12}{'--':>12}{'--':>9}{'--':>9}")
            continue
        dy = np.array([r["dy"] for r in rows]); dx = np.array([r["dx"] for r in rows])
        all_dy += list(dy); all_dx += list(dx)
        all_yc += [r["yc"] for r in rows]; all_xc += [r["xc"] for r in rows]
        print(f"{stem:<20}{len(rows):>5}{np.median(dy):>12.3f}{np.median(dx):>12.3f}"
              f"{dy.std():>9.3f}{dx.std():>9.3f}")
    ady, adx = np.array(all_dy), np.array(all_dx)
    ayc, axc = np.array(all_yc), np.array(all_xc)
    n = len(ady)
    print("-" * 74)
    print(f"{'POOLED':<20}{n:>5}{np.median(ady):>12.3f}{np.median(adx):>12.3f}"
          f"{ady.std():>9.3f}{adx.std():>9.3f}")

    se_y = 1.253 * ady.std() / np.sqrt(n)
    se_x = 1.253 * adx.std() / np.sqrt(n)
    print(f"\npooled median offset : dy {np.median(ady):+.4f} +/- {se_y:.4f} px "
          f"({np.median(ady)*a.pixel_size:+.3f} m)")
    print(f"                       dx {np.median(adx):+.4f} +/- {se_x:.4f} px "
          f"({np.median(adx)*a.pixel_size:+.3f} m)")
    print(f"mean offset          : dy {ady.mean():+.4f}, dx {adx.mean():+.4f} px")
    print(f"validation limit     : {limit:.4f} px")

    # spatial structure: does the offset depend on position (a ramp)?
    sy = float((ayc @ ady) / (ayc @ ayc)); sx = float((axc @ adx) / (axc @ axc))
    print(f"\nstructure check (ramp): dy/y={sy:+.6f}, dx/x={sx:+.6f} px per px "
          f"-> {sy*256:+.3f}, {sx*256:+.3f} px across the chip")

    bound = max(abs(np.median(ady)) + 2 * se_y, abs(np.median(adx)) + 2 * se_x, limit)
    print("\n" + "=" * 74)
    print("CONCLUSION")
    print("=" * 74)
    certified = bound < 0.1
    print(f"Alignment is certified to better than {bound:.3f} px "
          f"({bound*a.pixel_size:.2f} m).")
    print(f"Better than 0.1 px? {'YES' if certified else 'NO'}")
    if not certified:
        print(f"  The achieved bound is {bound:.3f} px, set by "
              f"{'the estimator noise floor' if limit >= bound - 1e-9 else 'the measured offset itself'}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
