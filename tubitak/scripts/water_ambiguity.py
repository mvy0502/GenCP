#!/usr/bin/env python
"""Water-ambiguity fraction: the measured signature of the WorldCover base failure.

A chip fails the gate where the reference says WATER but WorldCover says CROPLAND
(flooded rice/marsh systems). ambiguity = fraction of chip pixels with
(reference == water) AND (WC == 40 crop). Also records the broader variant
(WC in {30 grass, 40 crop}) as a sensitivity check.

Modes:
  corpus  -> distribution over all corpus reference chips
  ankara  -> the same quantity for the Ankara T36TVK scene, on a 257-px chip grid,
             with water identified from the Sentinel-2 TCI itself
"""
from __future__ import annotations
import argparse, glob, sys, warnings
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/"tubitak/scripts")); sys.path.insert(0, str(ROOT/"GenCP_HR_demo"))

def corpus():
    import rasterio, osm_to_raster as OTR
    from genCP_HR_osm_colors import color_dict
    def h2r(h):
        if h=="white": return (255,255,255)
        if h=="black": return (0,0,0)
        h=h.lstrip("#"); return tuple(int(h[i:i+2],16) for i in (0,2,4))
    NAMES=["light_green","forest_green","water","light_purple","gray","no_vegetation","sand",
           "rock","light_gray","black","snow","residential_road","tertiary_road",
           "unclassified_road","track","foot_path","light_orange_road","medium_orange_road","building"]
    PAL=np.array([h2r(color_dict[n]) if n!="building" else (165,42,42) for n in NAMES],float)
    iw=NAMES.index("water")
    rows=[]
    files=sorted(glob.glob(str(ROOT/"tubitak/data/karios/reference/osm/*.tif")))
    for i,f in enumerate(files):
        st=Path(f).stem
        with rasterio.open(f) as s:
            b=s.bounds; crs=s.crs
            a=np.transpose(s.read(),(1,2,0)).astype(float)
        ref=np.linalg.norm(a[:,:,None,:]-PAL[None,None,:,:],axis=3).argmin(axis=2)
        wm=(ref==iw)
        try:
            wc=OTR.fetch_worldcover((b.left,b.bottom,b.right,b.top),crs)
            wc=wc.reshape(257,4,257,4)[:,0,:,0]
        except Exception as e:
            print(f"  {st}: WC fetch failed {type(e).__name__}", flush=True); continue
        amb=float((wm&(wc==40)).mean())
        amb2=float((wm&np.isin(wc,(30,40))).mean())
        rows.append((st,float(wm.mean()),amb,amb2))
        if (i+1)%50==0: print(f"  {i+1}/{len(files)}", flush=True)
    import csv
    with open(ROOT/"tubitak/data/water_ambiguity_corpus.csv","w",newline="") as fh:
        w=csv.writer(fh); w.writerow(["stem","water_frac","amb_crop","amb_cropgrass"])
        w.writerows(rows)
    a=np.array([r[2] for r in rows])
    print(f"\ncorpus chips: {len(rows)}")
    print(f"ambiguity (ref-water & WC-crop) fraction of chip:")
    for q in (50,75,90,95,99):
        print(f"  p{q}: {np.percentile(a,q)*100:.3f}%")
    print(f"  mean {a.mean()*100:.3f}%   chips with amb>0.1%: {(a>0.001).sum()} "
          f"({100*(a>0.001).mean():.0f}%)   amb>1%: {(a>0.01).sum()}")

def ankara():
    import rasterio, osm_to_raster as OTR
    from rasterio.windows import Window
    tci=ROOT/"tubitak/data/ankara/TCI_36TVK_20260430.tif"
    N=257; rows=[]; skipped=0
    with rasterio.open(tci) as s:
        W,H=s.width,s.height; T=s.transform; crs=s.crs
        nx,ny=W//N,H//N
        for gy in range(ny):
            for gx in range(nx):
                win=Window(gx*N,gy*N,N,N)
                a=s.read(window=win).astype(float)
                R,G,B=a
                # conservative RGB water test: dark and blue-dominant
                wm=(R+G+B<210)&(B>R)&(B>=G-5)
                if wm.mean()<1e-4:
                    rows.append((gx,gy,float(wm.mean()),0.0,0.0)); continue
                wt=rasterio.windows.transform(win,T)
                bx=(wt.c, wt.f+N*wt.e, wt.c+N*wt.a, wt.f)
                try:
                    wc=OTR.fetch_worldcover(bx,crs).reshape(257,4,257,4)[:,0,:,0]
                except Exception as e:
                    print(f"  chip ({gx},{gy}): WC fetch failed {type(e).__name__}", flush=True)
                    skipped+=1; continue
                amb=float((wm&(wc==40)).mean())
                amb2=float((wm&np.isin(wc,(30,40))).mean())
                rows.append((gx,gy,float(wm.mean()),amb,amb2))
            print(f"  row {gy+1}/{ny}", flush=True)
    import csv
    with open(ROOT/"tubitak/data/water_ambiguity_ankara.csv","w",newline="") as fh:
        w=csv.writer(fh); w.writerow(["gx","gy","water_frac","amb_crop","amb_cropgrass"])
        w.writerows(rows)
    a=np.array([r[3] for r in rows])
    print(f"\nAnkara chips: {len(rows)}")
    if skipped: print(f"  skipped {skipped} chips (WC fetch errors)")
    for q in (50,75,90,95,99):
        print(f"  p{q}: {np.percentile(a,q)*100:.4f}%")
    print(f"  mean {a.mean()*100:.4f}%  chips amb>0.1%: {(a>0.001).sum()} ({100*(a>0.001).mean():.1f}%)")

if __name__=="__main__":
    warnings.filterwarnings("ignore")
    ap=argparse.ArgumentParser(); ap.add_argument("--mode",choices=["corpus","ankara"],required=True)
    a=ap.parse_args()
    corpus() if a.mode=="corpus" else ankara()
