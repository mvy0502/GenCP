#!/usr/bin/env python
"""Compare OSM raster inputs with the pix2pix-generated satellite imagery.

Picks N random generated tiles and writes a two-row figure:
  top row    = OSM vector raster fed into the generator
  bottom row = generated synthetic Sentinel-2 style image (georeferenced)

Usage:
    python tubitak/scripts/visualize.py [-n 4] [--seed 42]
"""
import argparse
import random
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import rasterio
from rasterio.plot import reshape_as_image

REPO_ROOT = Path(__file__).resolve().parents[2]
HR_DEMO = REPO_ROOT / "GenCP_HR_demo"
INPUT_DIR = HR_DEMO / "data" / "dataset" / "test"
GENERATED_DIR = HR_DEMO / "data" / "GenCP_DB"
OUTPUT_PATH = REPO_ROOT / "tubitak" / "outputs" / "sample_output.png"


def read_rgb(path):
    """Read a raster as an (H, W, 3) uint8 image."""
    with rasterio.open(path) as src:
        arr = src.read(indexes=[1, 2, 3][: src.count])
    return reshape_as_image(arr)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=4, help="number of tiles to show")
    parser.add_argument("--seed", type=int, default=None, help="RNG seed for reproducibility")
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    generated = sorted(GENERATED_DIR.glob("*.tif"))
    if not generated:
        raise SystemExit(f"No generated tiles found in {GENERATED_DIR}. Run the pipeline first.")

    # Only keep tiles whose OSM input is also present.
    pairs = [(INPUT_DIR / g.name, g) for g in generated if (INPUT_DIR / g.name).exists()]
    if not pairs:
        raise SystemExit(f"No matching OSM inputs found in {INPUT_DIR}.")

    n = min(args.n, len(pairs))
    sample = random.sample(pairs, n)

    fig, axes = plt.subplots(2, n, figsize=(3.2 * n, 6.8))
    if n == 1:
        axes = axes.reshape(2, 1)

    for col, (osm_path, gen_path) in enumerate(sample):
        axes[0, col].imshow(read_rgb(osm_path))
        axes[0, col].set_title(osm_path.stem, fontsize=9)
        axes[1, col].imshow(read_rgb(gen_path))
        for row in (0, 1):
            axes[row, col].set_xticks([])
            axes[row, col].set_yticks([])

    axes[0, 0].set_ylabel("OSM input", fontsize=11)
    axes[1, 0].set_ylabel("Generated", fontsize=11)
    fig.suptitle("GenCP HR — OpenStreetMap input vs. generated satellite imagery", fontsize=13)
    fig.tight_layout()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_PATH, dpi=150, bbox_inches="tight")
    print(f"Wrote {OUTPUT_PATH} ({n} tiles: {', '.join(p.stem for _, p in sample)})")


if __name__ == "__main__":
    main()
