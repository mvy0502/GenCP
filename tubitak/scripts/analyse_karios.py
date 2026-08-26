#!/usr/bin/env python
"""Analyse the KARIOS arm results against the pre-registered predictions.

Per arm: mean error, RMSE, surviving point count, and — the primary discriminator —
the SLOPE of residual against position, which is what a georeferencing scale error
produces and a constant offset does not.

Also correlates per-chip KARIOS outcome against the three OSM information-content
scores, replacing the proxy metric of hallucinated-structure.md with the real tool.

Usage
-----
    python tubitak/scripts/analyse_karios.py --figure tubitak/docs/figures/karios-residuals.png
"""
from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
KDIR = ROOT / "tubitak" / "data" / "karios"
PIXEL = 10.0
GRID_N = 228
INSET_M = 145.0

# predicted slope from the scale error: (10.0390625 - 10.0) / 10.0390625 per px of ground
PRED_SLOPE = (257 / 256 - 1) / (257 / 256)


def osm_scores(path):
    import rasterio
    from rasterio.errors import NotGeoreferencedWarning
    from scipy.ndimage import sobel
    warnings.filterwarnings("ignore", category=NotGeoreferencedWarning)
    with rasterio.open(path) as s:
        a = np.transpose(s.read(), (1, 2, 0)).astype(float)
    g = a.mean(axis=2)
    edge = float((np.hypot(sobel(g, 0), sobel(g, 1)) > 20).mean())
    px = a.reshape(-1, 3).astype(np.uint8)
    _, cnt = np.unique(px, axis=0, return_counts=True)
    share = cnt / cnt.sum()
    return dict(edge_density=edge, class_count=int((share >= 0.001).sum()),
                non_dominant=float(1 - share.max()))


def spearman(x, y):
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = np.asarray(x)[ok], np.asarray(y)[ok]
    if len(x) < 5:
        return np.nan, len(x)
    rx = np.argsort(np.argsort(x)).astype(float)
    ry = np.argsort(np.argsort(y)).astype(float)
    return float(np.corrcoef(rx, ry)[0, 1]), len(x)


def fit_slope(pos, resid):
    """Least-squares slope with standard error, through a free intercept."""
    ok = np.isfinite(pos) & np.isfinite(resid)
    x, y = np.asarray(pos)[ok], np.asarray(resid)[ok]
    if len(x) < 10:
        return np.nan, np.nan, len(x)
    A = np.vstack([x, np.ones_like(x)]).T
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    resid_v = y - A @ coef
    dof = max(1, len(x) - 2)
    s2 = (resid_v ** 2).sum() / dof
    cov = s2 * np.linalg.inv(A.T @ A)
    return float(coef[0]), float(np.sqrt(cov[0, 0])), len(x)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--results", default=str(KDIR / "results"))
    ap.add_argument("--osm", default=str(KDIR / "reference/osm"))
    ap.add_argument("--figure", default=None)
    a = ap.parse_args()

    res = Path(a.results)
    pts = pd.read_csv(res / "all_points.csv")
    summ = pd.read_csv(res / "per_chip_summary.csv")
    pts["radial"] = np.hypot(pts.dx, pts.dy)

    print("=" * 78)
    print("ARM COMPARISON")
    print("=" * 78)
    print(f"{'arm':<5}{'chips':>7}{'points':>9}{'mean|d| px':>12}{'mean|d| m':>11}"
          f"{'RMSE px':>10}{'RMSE m':>9}{'med dx':>9}{'med dy':>9}")
    print("-" * 78)
    for arm in sorted(pts.arm.unique()):
        d = pts[pts.arm == arm]
        rmse = float(np.sqrt((d.dx ** 2 + d.dy ** 2).mean()))
        nch = summ[(summ.arm == arm) & (summ.n_points > 0)].shape[0]
        print(f"{arm:<5}{nch:>7}{len(d):>9}{d.radial.mean():>12.4f}"
              f"{d.radial.mean()*PIXEL:>11.3f}{rmse:>10.4f}{rmse*PIXEL:>9.3f}"
              f"{d.dx.median():>9.4f}{d.dy.median():>9.4f}")

    print("\n" + "=" * 78)
    print("PRIMARY TEST — slope of residual against position")
    print("=" * 78)
    print(f"predicted slope for a stock (uncorrected) arm: {PRED_SLOPE:+.6f} px per px")
    print(f"{'arm':<5}{'dx vs column':>22}{'dy vs row':>22}{'n':>8}")
    print("-" * 78)
    slopes = {}
    for arm in sorted(pts.arm.unique()):
        d = pts[pts.arm == arm]
        sx, ex, n = fit_slope(d.x0.values, d.dx.values)
        sy, ey, _ = fit_slope(d.y0.values, d.dy.values)
        slopes[arm] = (sx, ex, sy, ey)
        print(f"{arm:<5}{f'{sx:+.6f} +/- {ex:.6f}':>22}"
              f"{f'{sy:+.6f} +/- {ey:.6f}':>22}{n:>8}")
    print("\n(a scale error produces a non-zero slope; a constant offset does not)")

    for arm, (sx, ex, sy, ey) in slopes.items():
        zx, zy = abs(sx) / (ex + 1e-12), abs(sy) / (ey + 1e-12)
        print(f"  arm {arm}: slope differs from zero by {zx:.1f} sigma (dx), {zy:.1f} sigma (dy)")

    # ---------------- per-chip vs OSM information ----------------
    print("\n" + "=" * 78)
    print("PER-CHIP OUTCOME vs OSM INFORMATION CONTENT (arm B)")
    print("=" * 78)
    b = pts[pts.arm == "B"]
    per = b.groupby("stem").agg(n_points=("dx", "size"),
                                med_radial=("radial", "median")).reset_index()
    sc = {s: osm_scores(Path(a.osm) / f"{s}.tif") for s in per.stem}
    for k in ("edge_density", "class_count", "non_dominant"):
        per[k] = [sc[s][k] for s in per.stem]
    print(f"chips: {len(per)}   median points/chip: {per.n_points.median():.0f}")
    print(f"\n{'OSM score':<18}{'rho vs n_points':>18}{'rho vs residual':>18}{'n':>5}")
    print("-" * 60)
    for k in ("edge_density", "class_count", "non_dominant"):
        r1, n1 = spearman(per[k].values, per.n_points.values)
        r2, _ = spearman(per[k].values, per.med_radial.values)
        print(f"{k:<18}{r1:>18.4f}{r2:>18.4f}{n1:>5}")
    print("\nP9 predicted rho(points) > 0 ; P10 predicted rho(residual) < 0 ;"
          " P11 predicted |rho| in 0.3-0.5")

    if a.figure:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(1, 2, figsize=(15.5, 7.2))
        for ax, arm in zip(axes, ["A", "B"]):
            d = pts[pts.arm == arm]
            if not len(d):
                continue
            # bin the key points onto a coarse grid and average the residual vectors
            nb = 9
            xb = np.clip((d.x0 / GRID_N * nb).astype(int), 0, nb - 1)
            yb = np.clip((d.y0 / GRID_N * nb).astype(int), 0, nb - 1)
            X, Y, U, V, M = [], [], [], [], []
            for i in range(nb):
                for j in range(nb):
                    m = (yb == i) & (xb == j)
                    if m.sum() < 3:
                        continue
                    X.append((j + .5) * GRID_N / nb * PIXEL)
                    Y.append((i + .5) * GRID_N / nb * PIXEL)
                    U.append(d.dx[m].median() * PIXEL)
                    V.append(d.dy[m].median() * PIXEL)
                    M.append(np.hypot(U[-1], V[-1]))
            X, Y, U, V, M = map(np.array, (X, Y, U, V, M))
            EX = 60
            q = ax.quiver(X, Y, U * EX, V * EX, M, angles="xy", scale_units="xy",
                          scale=1.0, cmap="autumn_r", width=0.006,
                          edgecolor="k", linewidth=0.5)
            ax.set_xlim(0, GRID_N * PIXEL); ax.set_ylim(GRID_N * PIXEL, 0)
            ax.set_aspect("equal")
            sx, ex, sy, ey = slopes.get(arm, (np.nan,) * 4)
            ax.set_title(f"Arm {arm} — {'stock transform (10.0 m)' if arm=='A' else 'affine-corrected (10.0390625 m)'}\n"
                         f"slope dx/col = {sx:+.5f} +/- {ex:.5f} px/px    "
                         f"mean |d| = {d.radial.mean()*PIXEL:.2f} m", fontsize=11)
            ax.set_xlabel("easting offset within common grid (m)")
            ax.set_ylabel("southing offset within common grid (m)")
            ax.grid(alpha=0.3, ls=":")
            fig.colorbar(q, ax=ax, fraction=0.046, pad=0.03).set_label("residual (m)")
            ax.plot(0, 0, marker="o", ms=10, mfc="none", mec="lime", mew=2.4, clip_on=False)
        fig.suptitle("KARIOS residual vectors — arrows exaggerated x60, median per bin\n"
                     "a scale error appears as a ramp growing away from the NW origin (green circle)",
                     fontsize=12.5)
        fig.tight_layout()
        Path(a.figure).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(a.figure, dpi=150, bbox_inches="tight")
        print(f"\nfigure -> {a.figure}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
