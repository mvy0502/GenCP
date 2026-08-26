#!/usr/bin/env python
"""Build the three KARIOS arms on a common ground grid.

Why warping is necessary
------------------------
KARIOS requires the monitored and reference rasters to have identical pixel
dimensions - it matches on the shared pixel grid and uses the transform only to
convert the result to metres. Fed directly, arms A and B would therefore give
*identical* shift fields, because they contain the same pixels and differ only in
declared pixel size. The georeferencing would never be exercised.

So each arm is **reprojected onto a common ground grid using its own declared
transform**, which is exactly what a real GCP workflow does when it puts a chip
onto a target image's grid. A wrong transform then displaces the content, and
KARIOS sees it.

The arms
-------
A  stock          256 px, transform copied verbatim from the 257 px source
                  (pixel size 10.0 m) - the current pipeline
B  affine-fixed   identical pixels, pixel size 10.0390625 m = 2570/256
C  scale-matched  generated via 257->286 + centre crop 256; covers the central
                  2300.42 m at 2570/286 = 8.98601 m/px

Common grid: 228 x 228 at 10 m, inset 145 m from the chip origin. That lies
strictly inside every arm's footprint - including arm C's, which is the smallest -
so no arm contributes nodata and none is advantaged by edge padding.

Usage
-----
    python tubitak/scripts/build_karios_arms.py --limit 60
"""
from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
KDIR = ROOT / "tubitak" / "data" / "karios"

SRC_PX = 257
OUT_PX = 256
LOAD_B = 286
NOMINAL = 10.0
GRID_N = 228
INSET_M = 145.0


def main() -> int:
    import rasterio
    from rasterio.transform import Affine
    from rasterio.warp import Resampling, reproject
    from rasterio.errors import NotGeoreferencedWarning
    warnings.filterwarnings("ignore", category=NotGeoreferencedWarning)

    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gen-a", default=str(KDIR.parent / "scale_test/out_a/genCP_HR_RGB_model/test_latest/images"))
    ap.add_argument("--gen-c", default=str(KDIR.parent / "scale_test/out_b/genCP_HR_RGB_model/test_latest/images"))
    ap.add_argument("--reference", default=str(KDIR / "reference/satellite"))
    ap.add_argument("--out", default=str(KDIR / "arms"))
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()

    ga, gc, ref_dir, out = Path(a.gen_a), Path(a.gen_c), Path(a.reference), Path(a.out)
    stems = sorted(f.name[:-9] for f in ga.glob("*_fake.png")
                   if (gc / f.name).exists() and (ref_dir / f"{f.name[:-9]}.tif").exists())
    if a.limit:
        stems = stems[:a.limit]
    if not stems:
        sys.exit("no chips with generated output in both variants plus a reference")

    for d in ("A", "B", "C", "ref"):
        (out / d).mkdir(parents=True, exist_ok=True)

    gsd_b = SRC_PX * NOMINAL / OUT_PX               # 10.0390625
    gsd_c = SRC_PX * NOMINAL / LOAD_B               # 8.986013986...
    off_c = (SRC_PX * NOMINAL - OUT_PX * gsd_c) / 2  # centre-crop offset in metres
    print(f"arm B pixel size : {gsd_b:.7f} m")
    print(f"arm C pixel size : {gsd_c:.7f} m, centre offset {off_c:.3f} m")
    print(f"common grid      : {GRID_N}x{GRID_N} @ {NOMINAL} m, inset {INSET_M} m\n")

    n = 0
    for st in stems:
        with rasterio.open(ref_dir / f"{st}.tif") as s:
            crs, T = s.crs, s.transform
            ref = s.read()
        ox, oy = T.c, T.f
        target = Affine(NOMINAL, 0, ox + INSET_M, 0, -NOMINAL, oy - INSET_M)

        def load(p):
            with rasterio.open(p) as s:
                return s.read()

        srcs = {
            "A": (load(ga / f"{st}_fake.png"), Affine(NOMINAL, 0, ox, 0, -NOMINAL, oy)),
            "B": (load(ga / f"{st}_fake.png"), Affine(gsd_b, 0, ox, 0, -gsd_b, oy)),
            "C": (load(gc / f"{st}_fake.png"),
                  Affine(gsd_c, 0, ox + off_c, 0, -gsd_c, oy - off_c)),
            "ref": (ref, T),
        }
        prof = dict(driver="GTiff", height=GRID_N, width=GRID_N, count=3,
                    dtype="uint8", crs=crs, transform=target)
        for arm, (arr, src_T) in srcs.items():
            dst = np.zeros((3, GRID_N, GRID_N), dtype="uint8")
            for b in range(3):
                reproject(source=arr[b], destination=dst[b],
                          src_transform=src_T, src_crs=crs,
                          dst_transform=target, dst_crs=crs,
                          resampling=Resampling.bilinear)
            if (dst == 0).all():
                print(f"  {st} arm {arm}: EMPTY after warp — skipping chip")
                break
            with rasterio.open(out / arm / f"{st}.tif", "w", **prof) as d:
                d.write(dst)
        else:
            n += 1

    print(f"built {n} chips x 4 rasters (A, B, C, ref) -> {out}")
    print("\nsanity: arms A and B contain the SAME pixels before warping;")
    print("any difference after warping is caused solely by the declared pixel size.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
