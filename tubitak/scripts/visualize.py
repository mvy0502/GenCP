#!/usr/bin/env python
"""Visualise GenCP HR results.

Two modes:

  default   two-row figure (OSM input / generated image) -> outputs/sample_output.png
  --verify  three-row figure adding the georeferenced GeoTIFF read back from
            data/GenCP_DB/ -> outputs/verification_grid.png

In --verify mode rows 2 and 3 must be pixel-identical: row 2 is the generated
PNG, row 3 is that same PNG after gencp_georeferencing.py wrapped it in a
GeoTIFF. The script compares the arrays exactly and reports any mismatch, so the
figure is a visual cross-check of tubitak/scripts/verify_georeferencing.py.

Usage:
    python tubitak/scripts/visualize.py [-n 4] [--seed 42]
    python tubitak/scripts/visualize.py --verify [-n 6] [--seed 42]
"""
import argparse
import random
import sys
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from rasterio.errors import NotGeoreferencedWarning
from rasterio.plot import reshape_as_image

REPO_ROOT = Path(__file__).resolve().parents[2]
HR_DEMO = REPO_ROOT / "GenCP_HR_demo"
INPUT_DIR = HR_DEMO / "data" / "dataset" / "test"
GENERATED_DIR = HR_DEMO / "data" / "GenCP_DB"
PNG_DIR = HR_DEMO / "data" / "fake_images" / "genCP_HR_RGB_model" / "test_latest" / "images"
OUT_DIR = REPO_ROOT / "tubitak" / "outputs"

# Generated PNGs legitimately carry no geotransform.
warnings.filterwarnings("ignore", category=NotGeoreferencedWarning)


def read_bands(path):
    """Read a raster as an (bands, H, W) array."""
    with rasterio.open(path) as src:
        return src.read(indexes=[1, 2, 3][: src.count])


def read_rgb(path):
    """Read a raster as an (H, W, 3) image for imshow."""
    return reshape_as_image(read_bands(path))


def pick_pairs(n, seed):
    if seed is not None:
        random.seed(seed)
    generated = sorted(GENERATED_DIR.glob("*.tif"))
    if not generated:
        raise SystemExit(f"No generated tiles found in {GENERATED_DIR}. Run the pipeline first.")
    pairs = [(INPUT_DIR / g.name, g) for g in generated if (INPUT_DIR / g.name).exists()]
    if not pairs:
        raise SystemExit(f"No matching OSM inputs found in {INPUT_DIR}.")
    return random.sample(pairs, min(n, len(pairs)))


def style(ax):
    ax.set_xticks([])
    ax.set_yticks([])


def make_sample(n, seed):
    sample = pick_pairs(n, seed)
    n = len(sample)
    fig, axes = plt.subplots(2, n, figsize=(3.2 * n, 6.8))
    axes = np.atleast_2d(axes).reshape(2, n)

    for col, (osm_path, gen_path) in enumerate(sample):
        axes[0, col].imshow(read_rgb(osm_path))
        axes[0, col].set_title(osm_path.stem, fontsize=9)
        axes[1, col].imshow(read_rgb(gen_path))
        style(axes[0, col])
        style(axes[1, col])

    axes[0, 0].set_ylabel("OSM input", fontsize=11)
    axes[1, 0].set_ylabel("Generated", fontsize=11)
    fig.suptitle("GenCP HR — OpenStreetMap input vs. generated satellite imagery", fontsize=13)
    fig.tight_layout()

    out = OUT_DIR / "sample_output.png"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150, bbox_inches="tight")
    print(f"Wrote {out} ({n} tiles: {', '.join(p.stem for _, p in sample)})")
    return 0


def make_verify(n, seed):
    sample = pick_pairs(n, seed)
    n = len(sample)
    fig, axes = plt.subplots(3, n, figsize=(3.0 * n, 9.6))
    axes = np.atleast_2d(axes).reshape(3, n)

    mismatches = []
    for col, (osm_path, geotiff_path) in enumerate(sample):
        stem = geotiff_path.stem
        fake_png = PNG_DIR / f"{stem}_fake.png"
        if not fake_png.exists():
            raise SystemExit(f"Missing generated PNG for {stem}: {fake_png}")

        gen_bands = read_bands(fake_png)
        tif_bands = read_bands(geotiff_path)
        identical = gen_bands.shape == tif_bands.shape and np.array_equal(gen_bands, tif_bands)
        if not identical:
            diff = (int(np.abs(gen_bands.astype(int) - tif_bands.astype(int)).max())
                    if gen_bands.shape == tif_bands.shape else None)
            mismatches.append((stem, diff))

        axes[0, col].imshow(read_rgb(osm_path))
        axes[1, col].imshow(reshape_as_image(gen_bands))
        axes[2, col].imshow(reshape_as_image(tif_bands))
        axes[0, col].set_title(stem, fontsize=8)
        for row in range(3):
            style(axes[row, col])

    axes[0, 0].set_ylabel("OSM input", fontsize=10)
    axes[1, 0].set_ylabel("Generated (_fake.png)", fontsize=10)
    axes[2, 0].set_ylabel("GeoTIFF (GenCP_DB)", fontsize=10)
    fig.suptitle(
        "GenCP HR verification grid — rows 2 and 3 must be pixel-identical", fontsize=13
    )
    fig.tight_layout()

    out = OUT_DIR / "verification_grid.png"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150, bbox_inches="tight")
    print(f"Wrote {out} ({n} tiles: {', '.join(p.stem for _, p in sample)})")

    print("\nRow 2 vs row 3 exact-equality check:")
    if mismatches:
        print(f"  MISMATCH in {len(mismatches)} of {n} tiles:")
        for stem, diff in mismatches:
            detail = f"max abs diff {diff}" if diff is not None else "shape mismatch"
            print(f"    {stem}: {detail}")
        return 1
    print(f"  all {n} tiles identical (exact, per band) — rows 2 and 3 agree")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-n", type=int, default=None, help="number of tiles (default 4, or 6 with --verify)")
    parser.add_argument("--seed", type=int, default=None, help="RNG seed for reproducibility")
    parser.add_argument("--verify", action="store_true",
                        help="three-row verification grid including the georeferenced GeoTIFF")
    args = parser.parse_args()

    if args.verify:
        return make_verify(args.n if args.n is not None else 6, args.seed)
    return make_sample(args.n if args.n is not None else 4, args.seed)


if __name__ == "__main__":
    sys.exit(main())
