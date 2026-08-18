#!/usr/bin/env python
"""Measure the anti-aliasing edge profile of the reference OSM rasters.

The rasteriser must reproduce this profile (renderer-tolerance.md: the AA axes are
the only ones above the LOOSE bound). Rather than guessing the original renderer,
this measures the transition geometry so it can be fitted.

Method
------
Scan every row and column. A "transition" is a maximal run of non-palette pixels
flanked by exact-palette pixels. Two populations are kept separate:

* AREA-AREA: flanking colours differ. Each run pixel is projected onto the RGB
  segment between the flanks; the projection parameter t is the blend fraction.
  Runs whose pixels stray > 6 DN from the segment are discarded (junctions,
  three-colour corners).
* ROAD CROSSING: flanking colours are equal and the run's most extreme pixel is
  nearest a road-class colour. These are thin lines crossed transversely.

Perpendicular width: run length is corrected by the local edge obliquity,
w_perp = run * |cos phi|, where phi is the angle between the scan direction and
the edge normal (from a Sobel gradient of the smoothed luma at the run centre).
Isotropy is tested by binning corrected widths by edge orientation.
"""
from __future__ import annotations
import argparse, glob, sys, warnings
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "GenCP_HR_demo"))
from genCP_HR_osm_colors import color_dict  # noqa: E402

def hex2rgb(h):
    if h == "white": return (255,255,255)
    if h == "black": return (0,0,0)
    h = h.lstrip("#"); return tuple(int(h[i:i+2],16) for i in (0,2,4))

ROAD = ["residential_road","tertiary_road","unclassified_road","track","foot_path",
        "light_orange_road","medium_orange_road"]
NAMES = ["light_green","forest_green","water","light_purple","gray","no_vegetation",
         "sand","rock","light_gray","black","snow"] + ROAD + ["building"]
PAL = np.array([hex2rgb(color_dict[n]) if n != "building" else (165,42,42)
                for n in NAMES], dtype=np.int32)
ROAD_I = {NAMES.index(n) for n in ROAD}
KEY = (PAL[:,0].astype(np.int64)<<16)|(PAL[:,1]<<8)|PAL[:,2]
KEYSET = set(int(k) for k in KEY)

def scan(img, grad_ang, axis, res):
    """Collect transitions along rows (axis=1) or columns (axis=0)."""
    a = img if axis == 1 else img.transpose(1,0,2)
    ga = grad_ang if axis == 1 else grad_ang.T
    H, W, _ = a.shape
    key = (a[:,:,0].astype(np.int64)<<16)|(a[:,:,1].astype(np.int64)<<8)|a[:,:,2]
    exact = np.isin(key, list(KEYSET))
    for y in range(H):
        row, ex = a[y], exact[y]
        x = 1
        while x < W-1:
            if ex[x]: x += 1; continue
            s = x
            while x < W and not ex[x]: x += 1
            e = x                     # run [s, e)
            if s == 0 or e >= W: continue
            L, R = row[s-1].astype(float), row[e].astype(float)
            n = e - s
            cx = (s+e)//2
            # edge normal angle at run centre relative to scan direction
            phi = ga[y, cx] if axis == 1 else ga[y, cx]  # ga already transposed
            wperp = n * abs(np.cos(phi))
            seg = R - L; ss = seg @ seg
            if ss > 25:               # flanks differ: area-area candidate
                ts, resid = [], 0.0
                for px in row[s:e].astype(float):
                    t = float(np.clip((px-L)@seg/ss, 0, 1))
                    resid = max(resid, float(np.abs(L + t*seg - px).max()))
                    ts.append(t)
                if resid <= 6.0:
                    res["area"].append((n, wperp, phi, tuple(ts)))
                else:
                    res["complex"] += 1
            else:                     # flanks same: thin-feature crossing
                mid = row[s:e].astype(float)
                d = np.abs(mid[:,None,:]-PAL[None,:,:]).max(axis=2)
                nearest = d.argmin(axis=1)
                peak = int(np.abs(mid - L).sum(axis=1).argmax())
                if int(nearest[peak]) in ROAD_I:
                    res["road"].append((n, wperp, phi))
                else:
                    res["other_thin"] += 1

def main() -> int:
    import rasterio
    from rasterio.errors import NotGeoreferencedWarning
    from scipy.ndimage import gaussian_filter, sobel
    warnings.filterwarnings("ignore", category=NotGeoreferencedWarning)

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n-demo", type=int, default=100)
    ap.add_argument("--n-corpus", type=int, default=100)
    a = ap.parse_args()

    files = sorted(glob.glob(str(ROOT/"GenCP_HR_demo/data/dataset/test/*.tif")))[:a.n_demo] + \
            sorted(glob.glob(str(ROOT/"tubitak/data/GenCP_HR_DB/train/*.tif")))[::max(1,5131//a.n_corpus)][:a.n_corpus]
    res = {"area": [], "road": [], "complex": 0, "other_thin": 0}
    for f in files:
        with rasterio.open(f) as s:
            img = np.transpose(s.read(), (1,2,0)).astype(np.int32)
        g = gaussian_filter(img.mean(axis=2), 1.0)
        gy, gx = sobel(g, 0), sobel(g, 1)
        ang_x = np.arctan2(np.abs(gy), np.abs(gx))   # angle of normal vs x-axis (0..pi/2)
        scan(img, ang_x, 1, res)                      # row scan: phi vs x
        scan(img, (np.pi/2 - ang_x), 0, res)          # col scan: phi vs y
    print(f"rasters: {len(files)}   area-area transitions: {len(res['area']):,}   "
          f"road crossings: {len(res['road']):,}")
    print(f"discarded: {res['complex']:,} multi-colour junctions, "
          f"{res['other_thin']:,} thin non-road features\n")

    # ---- area-area ----
    A = res["area"]
    n = np.array([r[0] for r in A]); w = np.array([r[1] for r in A])
    phi = np.array([r[2] for r in A])
    print("=== AREA-AREA transitions ===")
    print("raw run length histogram (scan direction):")
    for k in range(1, 7):
        c = int((n == k).sum())
        print(f"  {k} px: {c:>8,}  ({100*c/len(n):5.1f}%)")
    print(f"  >6px: {int((n>6).sum()):,}  ({100*(n>6).mean():.1f}%)")
    # near-perpendicular subset: scan crosses the edge head-on
    perp = phi < np.deg2rad(15)
    print(f"\nnear-perpendicular subset (edge normal within 15 deg of scan, n={perp.sum():,}):")
    for k in range(1, 6):
        c = int((n[perp] == k).sum())
        print(f"  {k} px: {c:>8,}  ({100*c/perp.sum():5.1f}%)")
    # blend fractions for 1- and 2-pixel perpendicular transitions
    t1 = [r[3][0] for r in A if r[0]==1 and r[2]<np.deg2rad(15)]
    t2a = [r[3][0] for r in A if r[0]==2 and r[2]<np.deg2rad(15)]
    t2b = [r[3][1] for r in A if r[0]==2 and r[2]<np.deg2rad(15)]
    t1 = np.array(t1); t2a=np.array(t2a); t2b=np.array(t2b)
    print(f"\nblend fraction t, 1-px transitions (n={len(t1):,}):")
    hist,_ = np.histogram(t1, bins=10, range=(0,1))
    for i,h in enumerate(hist):
        print(f"  {i/10:.1f}-{(i+1)/10:.1f}: {'#'*int(60*h/max(hist.max(),1))} {h:,}")
    print(f"  mean {t1.mean():.3f}  std {t1.std():.3f}  (uniform(0,1) -> mean 0.5, std 0.289)")
    if len(t2a):
        print(f"\n2-px transitions (n={len(t2a):,}): first px t mean {t2a.mean():.3f}, "
              f"second px t mean {t2b.mean():.3f}")
        print(f"  pair sum mean {np.mean(t2a+t2b):.3f}  (area-average of a straight edge -> sum ~1.0)")
    # isotropy
    print("\nisotropy: perpendicular-corrected width by edge orientation:")
    for lo,hi in ((0,15),(15,30),(30,45)):
        m = (phi>=np.deg2rad(lo))&(phi<np.deg2rad(hi))
        if m.sum()<50: continue
        print(f"  {lo:>2}-{hi:<2} deg: mean w_perp {w[m].mean():.3f} px  "
              f"median {np.median(w[m]):.2f}  (n={m.sum():,})")

    # ---- roads ----
    R = res["road"]
    rn = np.array([r[0] for r in R]); rphi = np.array([r[2] for r in R])
    rperp = rphi < np.deg2rad(15)
    print(f"\n=== ROAD crossings (transverse) ===")
    print("full-width run length (both AA flanks + core), near-perpendicular:")
    for k in range(1, 9):
        c = int((rn[rperp]==k).sum())
        if c: print(f"  {k} px: {c:>7,}  ({100*c/max(rperp.sum(),1):5.1f}%)")
    print(f"  median full width: {np.median(rn[rperp]):.1f} px")
    return 0

if __name__ == "__main__":
    sys.exit(main())
