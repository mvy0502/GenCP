#!/usr/bin/env python
"""Define the Ankara chip grid over T36TVK and screen every candidate.

Grid: 257x257 px at 10 m in EPSG:32636, anchored at the granule's NW corner —
the project-wide chip convention. For each candidate: nodata completeness, cloud
screening from the granule's own SCL band (a TCI brightness proxy is kept as a
reference column), and basic radiometry.

Cloud screening uses the scene's own SCL band (classes 3 cloud-shadow, 8/9
cloud, 10 thin cirrus), which the first attempt did not: a TCI-only brightness
proxy over-triggered on bright steppe fields, roofs and limestone (653 of 1764
chips flagged against a 2.04 % scene; visual calibration showed everything below
the extreme tail was cloud-free ground). SCL agrees with the scene metadata
(2.53 % vs 2.04 %). Snow (class 11) is recorded separately — real surface, but a
seasonal feature a GCP matcher should know about. The brightness proxy is kept
as a column for reference.
"""
from __future__ import annotations
import csv, sys, warnings
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
TCI  = ROOT/"tubitak/data/ankara/TCI_36TVK_20260430.tif"
OUT  = ROOT/"tubitak/data/ankara/chip_grid.csv"
N = 257

def main() -> int:
    import rasterio
    from rasterio.windows import Window
    warnings.filterwarnings("ignore")
    rows = []
    scl_src = rasterio.open(ROOT/"tubitak/data/ankara/SCL_36TVK_20260430.tif")
    scl = scl_src.read(1)                      # 5490x5490 @ 20 m, same footprint
    scl_src.close()
    with rasterio.open(TCI) as s:
        W, H, T = s.width, s.height, s.transform
        nx, ny = W//N, H//N
        print(f"granule {W}x{H} @ {s.res[0]:g} m -> grid {nx}x{ny} = {nx*ny} candidates "
              f"(margins {W-nx*N} px E, {H-ny*N} px S unused)")
        for gy in range(ny):
            for gx in range(nx):
                a = s.read(window=Window(gx*N, gy*N, N, N))
                R, G, B = a.astype(float)
                nodata = float(((a[0]==0)&(a[1]==0)&(a[2]==0)).mean())
                mx = np.maximum(np.maximum(R,G),B); mn = np.minimum(np.minimum(R,G),B)
                cloud = float(((mn>180)&((mx-mn)<40)).mean())
                gli = float(np.median((2*G-R-B)/(2*G+R+B+1e-6)))
                # SCL window: 257 px @10 m = 128.5 px @20 m; round outward
                sy0, sx0 = (gy*N)//2, (gx*N)//2
                sw = scl[sy0:sy0+129, sx0:sx0+129]
                cloud_scl = float(np.isin(sw,(3,8,9,10)).mean())
                snow_scl  = float((sw==11).mean())
                wt = rasterio.windows.transform(Window(gx*N,gy*N,N,N), T)
                rows.append(dict(gx=gx, gy=gy, easting=wt.c, northing=wt.f,
                                 nodata=round(nodata,5), cloud_scl=round(cloud_scl,5),
                                 snow=round(snow_scl,5), cloud_proxy=round(cloud,5),
                                 mean_R=round(R.mean(),1), mean_G=round(G.mean(),1),
                                 mean_B=round(B.mean(),1), std=round(a.std(),1),
                                 gli=round(gli,4)))
            if (gy+1)%10==0: print(f"  row {gy+1}/{ny}", flush=True)
    with open(OUT,"w",newline="") as f:
        w=csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    # granule carries 0 % nodata (SCL confirms); (0,0,0) TCI pixels are dark surface.
    # exclude only chips where they cluster (>0.5 %), plus any SCL cloud, plus snow >2 %.
    dark=[r for r in rows if r["nodata"]>0.005]
    cl=[r for r in rows if r["cloud_scl"]>0.01]
    sn=[r for r in rows if r["snow"]>0.02]
    valid=[r for r in rows if r["nodata"]<=0.005 and r["cloud_scl"]<=0.01 and r["snow"]<=0.02]
    print(f"\ncandidates            : {len(rows)}")
    print(f"  dark clusters >0.5% : {len(dark)}")
    print(f"  SCL cloud >1%       : {len(cl)}")
    print(f"  snow >2%            : {len(sn)}")
    print(f"  VALID               : {len(valid)}")
    c=np.array([r["cloud_scl"] for r in rows])
    print(f"SCL cloud: median {np.median(c)*100:.3f}%  p95 {np.percentile(c,95)*100:.3f}%  "
          f"max {c.max()*100:.1f}%")
    g=np.array([r["gli"] for r in valid])
    print(f"GLI over valid chips: median {np.median(g):+.4f}  p10 {np.percentile(g,10):+.4f}  "
          f"p90 {np.percentile(g,90):+.4f}")
    print(f"table -> {OUT}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
