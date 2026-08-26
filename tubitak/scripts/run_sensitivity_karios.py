#!/usr/bin/env python
"""Warp each perturbation variant onto the common grid and score it with KARIOS.

Uses the affine-CORRECTED georeferencing (10.0390625 m, arm B) so the known scale
error is not confounded with the perturbation being measured. Reference is the real
satellite half on the same common grid.

Two phases so the KARIOS work can be parallelised:
    --phase warp   build the georeferenced rasters
    --phase list   emit "variant stem" pairs for xargs -P
"""
from __future__ import annotations
import argparse, glob, sys, warnings
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SENS = ROOT / "tubitak" / "data" / "sensitivity"
REF  = ROOT / "tubitak" / "data" / "karios" / "reference" / "satellite"
GRID_N, INSET, PX = 228, 145.0, 10.0
GSD_B = 257 * 10.0 / 256          # affine-corrected

def main() -> int:
    import rasterio
    from rasterio.transform import Affine
    from rasterio.warp import reproject, Resampling
    from rasterio.errors import NotGeoreferencedWarning
    warnings.filterwarnings("ignore", category=NotGeoreferencedWarning)

    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--phase", choices=["warp","list"], required=True)
    a = ap.parse_args()

    variants = sorted(p.name for p in (SENS/"out").iterdir() if p.is_dir())
    stems = sorted(Path(p).stem for p in glob.glob(str(SENS/"inputs/base/*.png")))

    if a.phase == "list":
        for v in variants:
            for st in stems:
                if (SENS/"arms"/v/f"{st}.tif").exists(): print(f"{v} {st}")
        return 0

    (SENS/"arms"/"ref").mkdir(parents=True, exist_ok=True)
    n=0
    for v in variants:
        (SENS/"arms"/v).mkdir(parents=True, exist_ok=True)
        gd = SENS/"out"/v/"genCP_HR_RGB_model/test_latest/images"
        for st in stems:
            g = gd/f"{st}_fake.png"
            r = REF/f"{st}.tif"
            if not (g.exists() and r.exists()): continue
            with rasterio.open(r) as s:
                crs, T, ref = s.crs, s.transform, s.read()
            ox, oy = T.c, T.f
            tgt = Affine(PX,0,ox+INSET,0,-PX,oy-INSET)
            prof = dict(driver="GTiff",height=GRID_N,width=GRID_N,count=3,
                        dtype="uint8",crs=crs,transform=tgt)
            with rasterio.open(g) as s: gen = s.read()
            for arr, srcT, dest in ((gen, Affine(GSD_B,0,ox,0,-GSD_B,oy), SENS/"arms"/v/f"{st}.tif"),
                                    (ref, T, SENS/"arms"/"ref"/f"{st}.tif")):
                if dest.exists() and dest.parent.name=="ref": continue
                dst = np.zeros((3,GRID_N,GRID_N),dtype="uint8")
                for b in range(3):
                    reproject(source=arr[b],destination=dst[b],src_transform=srcT,src_crs=crs,
                              dst_transform=tgt,dst_crs=crs,resampling=Resampling.bilinear)
                with rasterio.open(dest,"w",**prof) as d: d.write(dst)
            n+=1
    print(f"warped {n} variant rasters across {len(variants)} variants")
    return 0

if __name__ == "__main__":
    sys.exit(main())
