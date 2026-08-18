#!/usr/bin/env python
"""Measure a local shift field between two rasters on an N x N grid of windows.

Takes an arbitrary pair of rasters, so it can be pointed at any dataset (the
GenCP demo, Turkish AOIs, KARIOS inputs) rather than hardcoded paths.

Each window is registered independently with the estimator in
``shift_estimator.py``. The resulting field distinguishes the cases that matter:

* all shifts ~zero                  -> the two grids are geometrically identical
* shifts ramp linearly to ~1 px     -> a full-extent resample; the ramp's zero
                                       end is the fixed point of the resampling
* large uniform offset              -> a translation / crop origin displacement
* anything else                     -> reported as-is, not forced into a category

If the rasters differ in size (e.g. 257x257 vs 256x256), windows are taken from
the same pixel indices in both, over the overlapping top-left region. That is
deliberate: it is exactly the comparison that reveals a scale ramp.

Examples
--------
    # OSM input raster vs the network's own input, with a figure
    python tubitak/scripts/shift_field.py \\
        GenCP_HR_demo/data/dataset/test/31TEJ_0704_00.tif \\
        GenCP_HR_demo/data/fake_images/.../31TEJ_0704_00_real.png \\
        --figure tubitak/docs/figures/geometric-shift-field.png

    # cross-modal (generated vs input): correlate on edges, not intensities
    python tubitak/scripts/shift_field.py A.png B.png --mode gradient
"""
from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from shift_estimator import phase_shift, prepare  # noqa: E402


def read_raster(path):
    """Read a raster as (H, W, bands) uint-ish array. Works for GeoTIFF and PNG."""
    import rasterio
    from rasterio.errors import NotGeoreferencedWarning
    warnings.filterwarnings("ignore", category=NotGeoreferencedWarning)
    with rasterio.open(path) as src:
        arr = src.read()
        res = src.res
    return np.transpose(arr, (1, 2, 0)), res


def measure(ref_img, mov_img, grid=4, window=64, mode="intensity", sigma=1.0):
    """Return a list of per-window records over an ``grid`` x ``grid`` layout."""
    ref = prepare(ref_img, mode, sigma)
    mov = prepare(mov_img, mode, sigma)
    h = min(ref.shape[0], mov.shape[0])
    w = min(ref.shape[1], mov.shape[1])
    step_y, step_x = h // grid, w // grid
    if window > min(step_y, step_x):
        window = min(step_y, step_x)

    out = []
    for i in range(grid):
        for j in range(grid):
            r0 = i * step_y + (step_y - window) // 2
            c0 = j * step_x + (step_x - window) // 2
            a = ref[r0:r0 + window, c0:c0 + window]
            b = mov[r0:r0 + window, c0:c0 + window]
            dy, dx, conf = phase_shift(a, b)
            out.append(dict(i=i, j=j, dy=dy, dx=dx, conf=conf,
                            yc=r0 + window / 2 - 0.5, xc=c0 + window / 2 - 0.5))
    return out, window


def fit_slope(rows, min_conf=8.0):
    """Least-squares slope through the origin: dy = s*yc, dx = s*xc."""
    v = [r for r in rows if np.isfinite(r["dy"]) and r["conf"] >= min_conf]
    if len(v) < 4:
        return np.nan, np.nan, len(v)
    yc = np.array([r["yc"] for r in v]); dy = np.array([r["dy"] for r in v])
    xc = np.array([r["xc"] for r in v]); dx = np.array([r["dx"] for r in v])
    return float((yc @ dy) / (yc @ yc)), float((xc @ dx) / (xc @ xc)), len(v)


def make_figure(mov_img, rows, path, pixel_size, title, exaggeration=40.0, grid=4):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    n = min(mov_img.shape[0], mov_img.shape[1])
    X = np.array([r["xc"] for r in rows]) * pixel_size
    Y = np.array([r["yc"] for r in rows]) * pixel_size
    U = np.array([r["dx"] for r in rows]) * pixel_size
    V = np.array([r["dy"] for r in rows]) * pixel_size
    M = np.hypot(U, V)

    fig, ax = plt.subplots(figsize=(9.2, 8.2))
    extent = (0, n * pixel_size, n * pixel_size, 0)
    disp = mov_img[..., :3] if mov_img.shape[2] >= 3 else mov_img[..., 0]
    ax.imshow(disp, extent=extent, interpolation="nearest",
              cmap=None if disp.ndim == 3 else "gray")

    q = ax.quiver(X, Y, U * exaggeration, V * exaggeration, M, angles="xy",
                  scale_units="xy", scale=1.0, cmap="autumn_r",
                  width=0.006, edgecolor="k", linewidth=0.5)
    cb = fig.colorbar(q, ax=ax, fraction=0.046, pad=0.03)
    cb.set_label("Shift magnitude (m)", fontsize=10)

    ax.add_patch(Rectangle((0.025, 0.018), 0.615, 0.082, transform=ax.transAxes,
                           fc="white", ec="0.3", alpha=0.88, zorder=5))
    ax.quiverkey(q, X=0.215, Y=0.059, U=pixel_size * exaggeration, labelpos="E",
                 coordinates="axes", zorder=6,
                 label=f"{pixel_size:g} m = 1 pixel   (arrows exaggerated x{exaggeration:g})",
                 fontproperties={"size": 9.5})
    ax.plot(0, 0, marker="o", ms=11, mfc="none", mec="lime", mew=2.5, clip_on=False)
    ax.annotate("fixed point\n(chip origin, NW)", xy=(0, 0),
                xytext=(0.06 * n * pixel_size, 0.082 * n * pixel_size), color="lime",
                fontsize=9, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color="lime", lw=1.6))

    ax.set_xlabel("Easting offset from chip origin (m)", fontsize=11)
    ax.set_ylabel("Southing offset from chip origin (m)", fontsize=11)
    ax.set_title(title, fontsize=12.5, pad=12)
    ax.grid(alpha=0.25, ls=":", color="w")
    fig.tight_layout()
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=170, bbox_inches="tight")
    plt.close(fig)


def interpret(sy, sx, rows, extent, min_conf=8.0):
    """Plain-language reading of the field. Deliberately refuses to over-claim."""
    v = [r for r in rows if np.isfinite(r["dy"]) and r["conf"] >= min_conf]
    if not v:
        return "UNRESOLVABLE — no window had enough texture to register."
    mags = [np.hypot(r["dy"], r["dx"]) for r in v]
    mean_mag, max_mag = float(np.mean(mags)), float(np.max(mags))
    slope = float(np.nanmean([abs(sy), abs(sx)]))
    ramp_px = slope * extent          # displacement across the full chip

    if max_mag < 0.15:
        return (f"ALL SHIFTS ~ZERO (max {max_mag:.3f} px) — the two grids are "
                f"geometrically identical within the estimator's noise floor.")
    if abs(ramp_px) > 0.4 and slope > 5e-4:
        return (f"LINEAR RAMP — slope {slope:+.6f} px/px, reaching ~{abs(ramp_px):.2f} px "
                f"across the chip; consistent with a full-extent resample, fixed point "
                f"at the low-index (NW) corner.")
    dys = [r["dy"] for r in v]; dxs = [r["dx"] for r in v]
    if np.std(dys) < 0.15 and np.std(dxs) < 0.15 and mean_mag > 0.2:
        return (f"UNIFORM OFFSET — mean ({np.mean(dys):+.3f}, {np.mean(dxs):+.3f}) px, "
                f"spread <0.15 px; consistent with a translation, not a scale change.")
    return (f"NO CLEAN CATEGORY — mean magnitude {mean_mag:.3f} px, max {max_mag:.3f} px, "
            f"scatter dy {np.std(dys):.3f} / dx {np.std(dxs):.3f} px. Reported as measured.")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("reference", help="reference raster")
    p.add_argument("moving", help="moving raster (shifts are reported relative to reference)")
    p.add_argument("--grid", type=int, default=4, help="grid is GRID x GRID windows (default 4)")
    p.add_argument("--window", type=int, default=64, help="window size in px (default 64)")
    p.add_argument("--mode", default="intensity", choices=["intensity", "gradient"],
                   help="'gradient' for cross-modal pairs (default intensity)")
    p.add_argument("--sigma", type=float, default=1.0, help="smoothing before Sobel, gradient mode")
    p.add_argument("--min-conf", type=float, default=8.0, help="confidence floor for a usable window")
    p.add_argument("--pixel-size", type=float, default=None,
                   help="metres per pixel for the figure (default: from the moving raster)")
    p.add_argument("--figure", default=None, help="write a quiver figure here")
    p.add_argument("--title", default=None, help="figure title")
    p.add_argument("--quiet", action="store_true", help="summary only")
    a = p.parse_args()

    ref_img, _ = read_raster(a.reference)
    mov_img, mov_res = read_raster(a.moving)
    rows, win = measure(ref_img, mov_img, a.grid, a.window, a.mode, a.sigma)

    px = a.pixel_size if a.pixel_size else (mov_res[0] if mov_res and mov_res[0] else 1.0)

    print(f"reference : {a.reference}  {ref_img.shape[1]}x{ref_img.shape[0]}")
    print(f"moving    : {a.moving}  {mov_img.shape[1]}x{mov_img.shape[0]}")
    print(f"mode={a.mode}  grid={a.grid}x{a.grid}  window={win}px  pixel_size={px:g} m\n")

    if not a.quiet:
        print(f"{'win':<6}{'centre(y,x)':<18}{'dy (px)':>10}{'dx (px)':>10}"
              f"{'|d| (px)':>10}{'|d| (m)':>10}{'conf':>9}")
        print("-" * 73)
        for r in rows:
            mag = np.hypot(r["dy"], r["dx"])
            flag = "" if r["conf"] >= a.min_conf else "  <- low texture"
            print(f"{r['i']},{r['j']:<4}({r['yc']:6.1f},{r['xc']:6.1f})  "
                  f"{r['dy']:>10.3f}{r['dx']:>10.3f}{mag:>10.3f}{mag * px:>10.2f}{r['conf']:>9.1f}{flag}")
        print("-" * 73)

    sy, sx, nv = fit_slope(rows, a.min_conf)
    print(f"\nusable windows : {nv}/{len(rows)}")
    print(f"fitted slope   : dy/y={sy:+.6f}  dx/x={sx:+.6f} px per px")
    print(f"across chip    : {sy * mov_img.shape[0]:+.3f} px (y), {sx * mov_img.shape[1]:+.3f} px (x)")
    print(f"\nINTERPRETATION: {interpret(sy, sx, rows, mov_img.shape[0], a.min_conf)}")

    if a.figure:
        title = a.title or (f"Shift field: {Path(a.reference).name} vs {Path(a.moving).name}")
        make_figure(mov_img, rows, a.figure, px, title, grid=a.grid)
        print(f"\nfigure -> {a.figure}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
