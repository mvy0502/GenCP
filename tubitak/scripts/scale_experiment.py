#!/usr/bin/env python
"""Does feeding at the training-matched scale improve output quality?

The released code trains with ``load_size=286`` (resize 257->286, random 256 crop)
but infers with ``load_size=crop_size=256`` (resize 257->256, no crop). The network
is therefore shown content 11.7 % coarser at inference than in training. We cannot
recover the authors' actual training command, so this tests the *consequence*.

Two generations from the same OSM input:

(a) current inference path   257 -> 256                     GSD 10.039 m, covers 2570.0 m
(b) training-matched path    257 -> 286, centre-crop 256    GSD  8.986 m, covers 2300.5 m

A centre crop is used rather than the random crop training would apply, so the
comparison is deterministic.

Because the two cover different ground, both are evaluated over the **common
central 2300.5 m**. Two evaluation grids are reported, because neither is neutral:
at 229 px variant (b) must be downsampled (both its output and its reference,
equally), at 256 px variant (a) must be upsampled. If the same variant wins on
both grids the conclusion is robust to that choice.

Metrics, and why each
---------------------
gradient correlation   Pearson r of Sobel gradient magnitude. The question is about
                       texture and small-feature rendering, not colour, so this is
                       the primary metric.
SSIM                   Structural similarity - luminance, contrast and structure
                       jointly; the standard reference metric.
high-freq energy ratio Output high-frequency power / reference high-frequency power.
                       Directly tests the observed symptom (narrow rivers vanishing,
                       villages rendered as noise). 1.0 = detail matched, <1 = too
                       smooth, >1 = spurious detail.
RMSE                   Intensity error. A weak proxy - a GAN is not required to match
                       pixel values - included only as a sanity baseline.

Usage
-----
    python tubitak/scripts/scale_experiment.py --figure tubitak/docs/figures/scale-comparison.png
"""
from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "tubitak" / "data" / "scale_test"


def read(path):
    import rasterio
    from rasterio.errors import NotGeoreferencedWarning
    warnings.filterwarnings("ignore", category=NotGeoreferencedWarning)
    with rasterio.open(path) as s:
        return np.transpose(s.read(), (1, 2, 0)).astype(float)


def to_size(img, n):
    """Resample to n x n with a single consistent kernel (identity if already n)."""
    if img.shape[0] == n:
        return img
    from PIL import Image
    from torchvision import transforms
    pil = Image.fromarray(np.clip(img, 0, 255).astype("uint8"))
    return np.array(transforms.Resize([n, n], transforms.InterpolationMode.BICUBIC)(pil)).astype(float)


def gray(a):
    return a.mean(axis=2) if a.ndim == 3 else a


def grad_corr(x, y):
    from scipy.ndimage import sobel
    gx = lambda a: np.hypot(sobel(gray(a), 0), sobel(gray(a), 1))
    A, B = gx(x).ravel(), gx(y).ravel()
    if A.std() < 1e-9 or B.std() < 1e-9:
        return np.nan
    return float(np.corrcoef(A, B)[0, 1])


def ssim(x, y, sigma=1.5, L=255.0):
    """Gaussian-weighted SSIM (Wang et al. 2004), implemented locally."""
    from scipy.ndimage import gaussian_filter
    a, b = gray(x), gray(y)
    C1, C2 = (0.01 * L) ** 2, (0.03 * L) ** 2
    mu_a = gaussian_filter(a, sigma); mu_b = gaussian_filter(b, sigma)
    saa = gaussian_filter(a * a, sigma) - mu_a ** 2
    sbb = gaussian_filter(b * b, sigma) - mu_b ** 2
    sab = gaussian_filter(a * b, sigma) - mu_a * mu_b
    s = ((2 * mu_a * mu_b + C1) * (2 * sab + C2)) / ((mu_a ** 2 + mu_b ** 2 + C1) * (saa + sbb + C2))
    return float(s.mean())


def hf_ratio(x, y, cutoff=0.25):
    """Ratio of high-frequency power, output vs reference."""
    def hf(a):
        A = np.fft.fftshift(np.abs(np.fft.fft2(gray(a) - gray(a).mean())) ** 2)
        n = A.shape[0]
        yy, xx = np.mgrid[0:n, 0:n] - n / 2
        r = np.hypot(yy, xx) / (n / 2)
        return A[r > cutoff].sum()
    d = hf(y)
    return float(hf(x) / d) if d > 0 else np.nan


def rmse(x, y):
    return float(np.sqrt(((gray(x) - gray(y)) ** 2).mean()))


def common_area(out_a, ref_a, out_b, ref_b, grid):
    """Restrict both variants to the central 2300.5 m and resample to `grid`."""
    n = out_a.shape[0]
    keep = int(round(n * (256 / 286)))          # 229 px of a's 256 covers 2300.5 m
    off = (n - keep) // 2
    ca, ra = out_a[off:off + keep, off:off + keep], ref_a[off:off + keep, off:off + keep]
    cb, rb = out_b, ref_b                        # b already covers exactly that ground
    return (to_size(ca, grid), to_size(ra, grid), to_size(cb, grid), to_size(rb, grid))


def make_figure(stems, path, n=4):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    sel = stems[:n]
    fig, axes = plt.subplots(4, len(sel), figsize=(3.1 * len(sel), 12.6))
    axes = np.atleast_2d(axes).reshape(4, len(sel))
    rows = ["OSM input (a)", "REAL satellite", "(a) 257->256", "(b) 257->286, crop"]
    for c, stem in enumerate(sel):
        imgs = [read(BASE / "inputs_a" / f"{stem}.png"),
                read(BASE / "refs_a" / f"{stem}.png"),
                read(BASE / "out_a/genCP_HR_RGB_model/test_latest/images" / f"{stem}_fake.png"),
                read(BASE / "out_b/genCP_HR_RGB_model/test_latest/images" / f"{stem}_fake.png")]
        for r, im in enumerate(imgs):
            axes[r, c].imshow(np.clip(im, 0, 255).astype("uint8"))
            axes[r, c].set_xticks([]); axes[r, c].set_yticks([])
        axes[0, c].set_title(stem, fontsize=8)
    for r, lab in enumerate(rows):
        axes[r, 0].set_ylabel(lab, fontsize=10)
    fig.suptitle("Inference scale comparison: current path (a) vs training-matched path (b)\n"
                 "row 3 covers 2570 m, row 4 covers the central 2300 m of the same chip",
                 fontsize=12)
    fig.tight_layout()
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    print(f"figure -> {path}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--grid", type=int, nargs="+", default=[229, 256])
    ap.add_argument("--figure", default=None)
    ap.add_argument("--per-pair", action="store_true")
    a = ap.parse_args()

    ga = BASE / "out_a/genCP_HR_RGB_model/test_latest/images"
    gb = BASE / "out_b/genCP_HR_RGB_model/test_latest/images"
    stems = sorted(f.name[:-9] for f in ga.glob("*_fake.png") if (gb / f.name).exists())
    if not stems:
        sys.exit("no generated pairs found - run the generation step first")
    print(f"pairs: {len(stems)}\n")

    METRICS = [("grad corr", grad_corr, "higher"), ("SSIM", ssim, "higher"),
               ("HF energy ratio", hf_ratio, "->1.0"), ("RMSE", rmse, "lower")]

    for grid in a.grid:
        print("=" * 78)
        print(f"EVALUATION GRID {grid}x{grid}   (common central 2300.5 m)")
        if grid == 229:
            print("  variant (b) downsampled 256->229 (output AND reference equally)")
        else:
            print("  variant (a) upsampled 229->256 (output AND reference equally)")
        print("=" * 78)
        res = {m[0]: ([], []) for m in METRICS}
        for stem in stems:
            ca, ra, cb, rb = common_area(
                read(ga / f"{stem}_fake.png"), read(BASE / "refs_a" / f"{stem}.png"),
                read(gb / f"{stem}_fake.png"), read(BASE / "refs_b" / f"{stem}.png"), grid)
            for name, fn, _ in METRICS:
                res[name][0].append(fn(ca, ra))
                res[name][1].append(fn(cb, rb))
            if a.per_pair:
                print(f"  {stem:<20} " + "  ".join(
                    f"{n}: a={res[n][0][-1]:.4f} b={res[n][1][-1]:.4f}" for n, _, _ in METRICS))

        print(f"\n{'metric':<18}{'(a) current':>14}{'(b) train-matched':>19}"
              f"{'diff':>10}{'wins (b/n)':>12}{'better':>9}")
        print("-" * 78)
        for name, _, direction in METRICS:
            A = np.array(res[name][0]); B = np.array(res[name][1])
            ok = np.isfinite(A) & np.isfinite(B)
            A, B = A[ok], B[ok]
            if direction == "higher":
                wins = int((B > A).sum()); better = "b" if B.mean() > A.mean() else "a"
            elif direction == "lower":
                wins = int((B < A).sum()); better = "b" if B.mean() < A.mean() else "a"
            else:
                wins = int((np.abs(B - 1) < np.abs(A - 1)).sum())
                better = "b" if abs(B.mean() - 1) < abs(A.mean() - 1) else "a"
            d = B.mean() - A.mean()
            se = (A - B).std(ddof=1) / np.sqrt(len(A))
            sig = "yes" if abs(d) > 2 * se else "NO (within noise)"
            print(f"{name:<18}{A.mean():>14.4f}{B.mean():>19.4f}{d:>+10.4f}"
                  f"{wins:>8}/{len(A):<4}{better:>9}   diff/2SE {abs(d)/(2*se+1e-12):.2f} -> {sig}")
        print()

    if a.figure:
        make_figure(stems, a.figure)
    return 0


if __name__ == "__main__":
    sys.exit(main())
