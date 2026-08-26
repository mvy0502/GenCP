#!/usr/bin/env python
"""Measure whether the generator preserves spatial alignment input -> output.

Every other measurement in the geometry investigation compares ``_real.png``
(the network's INPUT) against the source raster. The georeferenced GeoTIFFs
however contain ``_fake`` (the network's OUTPUT). The bridge between the two —
"a U-Net preserves pixel alignment" — is true by architecture but had not been
measured. Any misalignment the network introduces adds to the KARIOS error
budget and would be confounded with the 257->256 scale ramp.

Method
------
``_real.png`` and ``_fake.png`` are both 256x256 on the same grid, so any shift
between them is attributable to the network alone.

They are *different modalities*: categorical OSM colours vs continuous satellite
texture. Raw intensities are essentially uncorrelated between them (a green OSM
polygon and the generated field it produces share no grey level), so correlating
on intensity is meaningless. We correlate on **Sobel gradient magnitude of a
lightly smoothed image** instead: edges — roads, field boundaries, water margins —
occupy the same positions in both modalities even though their intensities do not
correspond. Both modes are reported so the choice is visible rather than asserted.

Validation before measurement
-----------------------------
A cross-modal estimator that cannot recover a *known* displacement cannot be
trusted to report an unknown one. So ``_fake`` is deliberately displaced by known
amounts and the estimator must recover them, measured as the change relative to
the (unknown) baseline offset:

    recovery_error = (shift[real, displaced_fake] - shift[real, fake]) - injected

If recovery fails, this script says the measurement is not possible with this
method rather than reporting unreliable numbers.

Usage
-----
    python tubitak/scripts/network_alignment.py --tiles 6
"""
from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from shift_estimator import ncc_shift, phase_shift, prepare  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
HR = REPO_ROOT / "GenCP_HR_demo"
DEF_PNG = HR / "data" / "fake_images" / "genCP_HR_RGB_model" / "test_latest" / "images"
DEF_DB = HR / "data" / "GenCP_DB"

INJECTED = [(0.0, 0.0), (0.5, 0.0), (0.0, 0.5), (1.0, 1.0), (-1.5, 2.0), (2.0, -1.0)]


def read_png(path):
    import rasterio
    from rasterio.errors import NotGeoreferencedWarning
    warnings.filterwarnings("ignore", category=NotGeoreferencedWarning)
    with rasterio.open(path) as s:
        return np.transpose(s.read(), (1, 2, 0)).astype(float)


def windows(shape, grid, win):
    h, w = shape[:2]
    sy, sx = h // grid, w // grid
    for i in range(grid):
        for j in range(grid):
            r0 = i * sy + (sy - win) // 2
            c0 = j * sx + (sx - win) // 2
            yield i, j, r0, c0


def field(real, fake, grid, win, mode, sigma, min_conf, estimator="ncc", max_shift=8):
    R, F = prepare(real, mode, sigma), prepare(fake, mode, sigma)
    est = (lambda a, b: ncc_shift(a, b, max_shift=max_shift)) if estimator == "ncc" else phase_shift
    out = []
    for i, j, r0, c0 in windows(real.shape, grid, win):
        dy, dx, conf = est(R[r0:r0 + win, c0:c0 + win],
                           F[r0:r0 + win, c0:c0 + win])
        out.append(dict(i=i, j=j, dy=dy, dx=dx, conf=conf,
                        yc=r0 + win / 2 - 0.5, xc=c0 + win / 2 - 0.5,
                        ok=np.isfinite(dy) and conf >= min_conf))
    return out


def validate(stems, png_dir, grid, win, mode, sigma, min_conf, estimator='ncc', max_shift=8):
    """Inject known shifts into _fake and check they are recovered."""
    from scipy.ndimage import shift as ndshift

    print("=" * 78)
    print(f"VALIDATION — can the cross-modal estimator recover a KNOWN shift? (mode={mode})")
    print("=" * 78)
    print("Measured as change relative to the unknown baseline offset, so the")
    print("baseline itself does not contaminate the test.\n")
    print(f"{'injected dy,dx':<18}{'recovered dy':>14}{'recovered dx':>14}"
          f"{'err dy':>10}{'err dx':>10}")
    print("-" * 78)

    errs = []
    for stem in stems[:3]:
        real = read_png(png_dir / f"{stem}_real.png")
        fake = read_png(png_dir / f"{stem}_fake.png")
        base = field(real, fake, grid, win, mode, sigma, min_conf, estimator, max_shift)
        b_ok = [r for r in base if r["ok"]]
        if not b_ok:
            continue
        b_dy = float(np.median([r["dy"] for r in b_ok]))
        b_dx = float(np.median([r["dx"] for r in b_ok]))
        for tdy, tdx in INJECTED:
            if tdy == 0 and tdx == 0:
                continue
            moved = np.stack([ndshift(fake[..., k], (tdy, tdx), order=3, mode="reflect")
                              for k in range(fake.shape[2])], axis=-1)
            f2 = field(real, moved, grid, win, mode, sigma, min_conf, estimator, max_shift)
            ok = [r for r in f2 if r["ok"]]
            if not ok:
                continue
            rdy = float(np.median([r["dy"] for r in ok])) - b_dy
            rdx = float(np.median([r["dx"] for r in ok])) - b_dx
            errs.append((rdy - tdy, rdx - tdx))
            print(f"{f'{tdy:+.1f}, {tdx:+.1f}':<18}{rdy:>14.3f}{rdx:>14.3f}"
                  f"{rdy - tdy:>10.3f}{rdx - tdx:>10.3f}")
    if not errs:
        print("  no usable windows — validation could not run")
        return False, np.nan
    e = np.abs(np.array(errs))
    rms = float(np.sqrt((e ** 2).mean()))
    p90 = float(np.percentile(e, 90))
    print("-" * 78)
    print(f"n={len(errs)}  median |err|={np.median(e):.3f}  RMS={rms:.3f}  "
          f"p90={p90:.3f}  max={e.max():.3f} px")
    # The honest question is not pass/fail but: below what magnitude is a measured
    # offset indistinguishable from estimator noise? That is the resolution limit.
    limit = max(rms, p90)
    if e.max() < 0.5:
        print(f"VERDICT: reliable to sub-pixel; resolution limit ~{limit:.2f} px")
    elif limit < 1.5:
        print(f"VERDICT: NOT reliable sub-pixel, but usable as a BOUND.")
        print(f"         Resolution limit ~{limit:.2f} px: offsets below this cannot be")
        print(f"         distinguished from noise; offsets above it would be detected.")
    else:
        print(f"VERDICT: unusable — noise ({limit:.2f} px) exceeds any plausible signal.")
    return limit < 1.5, limit


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--tiles", type=int, default=6)
    p.add_argument("--png-dir", default=str(DEF_PNG))
    p.add_argument("--list-from", default=str(DEF_DB))
    p.add_argument("--grid", type=int, default=4)
    p.add_argument("--window", type=int, default=64)
    p.add_argument("--mode", default="gradient", choices=["gradient", "intensity", "both"])
    p.add_argument("--sigma", type=float, default=1.0)
    p.add_argument("--min-conf", type=float, default=None,
                   help="confidence floor; default depends on estimator "
                        "(ncc 1.2, phase 8.0) since the two scales differ")
    p.add_argument("--estimator", default="ncc", choices=["ncc", "phase"],
                   help="ncc is robust cross-modally; phase is sharper but same-modality only")
    p.add_argument("--max-shift", type=int, default=8,
                   help="bounded search radius in px for the ncc estimator")
    a = p.parse_args()
    if a.min_conf is None:
        # The two estimators produce confidences on different scales: phase
        # correlation peaks stand far above a whitened surface (median ~10),
        # NCC peaks sit on a smooth surface (median ~2.3). Measured, not guessed.
        a.min_conf = 1.2 if a.estimator == "ncc" else 8.0

    png_dir = Path(a.png_dir)
    stems = sorted(q.stem for q in Path(a.list_from).glob("*.tif"))[:a.tiles]
    if not stems:
        sys.exit("no tiles found")

    modes = ["gradient", "intensity"] if a.mode == "both" else [a.mode]
    for mode in modes:
        passed, val_rms = validate(stems, png_dir, a.grid, a.window, mode, a.sigma, a.min_conf,
                                   a.estimator, a.max_shift)
        print()
        if not passed:
            print(f"[{mode}] MEASUREMENT NOT POSSIBLE with this method — the estimator failed")
            print(f"[{mode}] validation, so any shift field it produced would be unreliable.\n")
            continue

        print("=" * 78)
        print(f"MEASUREMENT — shift field between _real (input) and _fake (output), mode={mode}")
        print("=" * 78)
        print(f"{'tile':<16}{'n_ok':>6}{'median dy':>11}{'median dx':>11}"
              f"{'std dy':>9}{'std dx':>9}{'max|d|':>9}")
        print("-" * 78)
        all_dy, all_dx = [], []
        for stem in stems:
            real = read_png(png_dir / f"{stem}_real.png")
            fake = read_png(png_dir / f"{stem}_fake.png")
            rows = field(real, fake, a.grid, a.window, mode, a.sigma, a.min_conf, a.estimator, a.max_shift)
            ok = [r for r in rows if r["ok"]]
            if not ok:
                print(f"{stem:<16}{0:>6}{'--':>11}{'--':>11}{'--':>9}{'--':>9}{'--':>9}")
                continue
            dy = np.array([r["dy"] for r in ok]); dx = np.array([r["dx"] for r in ok])
            all_dy += list(dy); all_dx += list(dx)
            mag = np.hypot(dy, dx)
            print(f"{stem:<16}{len(ok):>6}{np.median(dy):>11.3f}{np.median(dx):>11.3f}"
                  f"{dy.std():>9.3f}{dx.std():>9.3f}{mag.max():>9.3f}")
        print("-" * 78)
        if not all_dy:
            print("no usable windows across any tile\n")
            continue
        ady, adx = np.array(all_dy), np.array(all_dx)
        amag = np.hypot(ady, adx)
        print(f"{'POOLED':<16}{len(ady):>6}{np.median(ady):>11.3f}{np.median(adx):>11.3f}"
              f"{ady.std():>9.3f}{adx.std():>9.3f}{amag.max():>9.3f}")
        print(f"\nnoise floor from validation : {val_rms:.3f} px RMS")
        print(f"pooled |median| offset      : dy {abs(np.median(ady)):.3f} px, "
              f"dx {abs(np.median(adx)):.3f} px")
        print(f"pooled scatter (1 sigma)    : dy {ady.std():.3f} px, dx {adx.std():.3f} px")

        med = max(abs(np.median(ady)), abs(np.median(adx)))
        print("\nCONCLUSION:", end=" ")
        if med < val_rms:
            print(f"NO MEASURABLE MISALIGNMENT. The pooled median offset is {med:.3f} px,")
            print(f"  below the estimator's own resolution limit of {val_rms:.3f} px. The")
            print(f"  alignment assumption HOLDS at this precision: any systematic")
            print(f"  input->output displacement is smaller than ~{val_rms:.2f} px (~{val_rms*10:.1f} m).")
            print(f"  Sub-pixel misalignment below that bound is UNRESOLVABLE by this method")
            print(f"  and is neither confirmed nor excluded.")
        else:
            print(f"POSSIBLE SYSTEMATIC OFFSET: pooled median {med:.3f} px exceeds the")
            print(f"  resolution limit {val_rms:.3f} px. Would add to the KARIOS error budget.")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
