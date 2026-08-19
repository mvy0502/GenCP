#!/usr/bin/env python
"""Option A: correct the affine of GeoTIFFs produced by gencp_georeferencing.py.

The upstream script copies the 257-px source raster's transform (10.0 m pixels)
onto 256-px generated content, declaring a 2560 m footprint for 2570 m of
content — a +0.390625 % scale error reaching 14.1 m at the SE corner
(geometry-finding.md §5). KARIOS measured the correction to reduce the
systematic global shift by 40 % (karios-validation.md §8).

This rewrites the pixel size to 2570/256 = 10.0390625 m, keeping the same NW
origin. **Pixels are untouched** — metadata only. Upstream files are not
modified; this is a separate post-processing step.

Usage
-----
    python tubitak/scripts/fix_georeferencing.py CHIP.tif [CHIP2.tif ...]
    python tubitak/scripts/fix_georeferencing.py --dir data/GenCP_DB --out-dir corrected/
    python tubitak/scripts/fix_georeferencing.py --in-place --dir corrected_copies/
"""
from __future__ import annotations
import argparse, glob, sys, warnings
from pathlib import Path

SRC_PX, OUT_PX, NOMINAL = 257, 256, 10.0
TRUE_GSD = SRC_PX * NOMINAL / OUT_PX          # 10.0390625, exact in binary

def fix_one(src, dst, in_place=False):
    import rasterio
    from rasterio.transform import Affine
    with rasterio.open(src) as s:
        t = s.transform
        if s.width != OUT_PX or s.height != OUT_PX:
            return f"SKIP {src}: {s.width}x{s.height}, expected {OUT_PX}"
        if abs(t.a - TRUE_GSD) < 1e-9 and abs(t.e + TRUE_GSD) < 1e-9:
            return f"SKIP {src}: already corrected"
        if abs(t.a - NOMINAL) > 1e-9 or abs(t.e + NOMINAL) > 1e-9:
            return f"SKIP {src}: unexpected pixel size ({t.a}, {t.e})"
        arr = s.read()
        prof = s.profile.copy()
    prof["transform"] = Affine(TRUE_GSD, 0.0, t.c, 0.0, -TRUE_GSD, t.f)  # same NW origin
    out = src if in_place else dst
    with rasterio.open(out, "w", **prof) as d:
        d.write(arr)
    return None

def main() -> int:
    warnings.filterwarnings("ignore")
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="*", help="GeoTIFFs to correct")
    ap.add_argument("--dir", help="correct every *.tif in this directory")
    ap.add_argument("--out-dir", help="write corrected copies here (default: alongside, .fixed.tif)")
    ap.add_argument("--in-place", action="store_true")
    a = ap.parse_args()
    files = list(a.files) + (sorted(glob.glob(str(Path(a.dir)/"*.tif"))) if a.dir else [])
    if not files:
        ap.error("no input files")
    if a.out_dir:
        Path(a.out_dir).mkdir(parents=True, exist_ok=True)
    n_ok = 0
    for f in files:
        dst = (Path(a.out_dir)/Path(f).name if a.out_dir
               else Path(f).with_suffix(".fixed.tif"))
        msg = fix_one(f, dst, in_place=a.in_place)
        if msg: print(f"  {msg}")
        else: n_ok += 1
    print(f"corrected {n_ok}/{len(files)}  (pixel size {NOMINAL} -> {TRUE_GSD})")
    return 0

if __name__ == "__main__":
    sys.exit(main())
