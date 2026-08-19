#!/usr/bin/env python
"""Pairwise graded comparison of two render sets of the SAME chips.

Used to prove the Overpass -> PBF source switch is transparent: palette subset,
per-class confusion between the two renders, geometry, and agreement split by
stable vs volatile classes. Expected outcome for a transparent switch:
agreement in the high 90s with residuals that are individual features present or
absent (snapshot date drift), NOT systematic colour/boundary/class errors.
"""
from __future__ import annotations
import argparse, glob, sys, warnings
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/"GenCP_HR_demo"))

def main() -> int:
    import rasterio
    from genCP_HR_osm_colors import color_dict
    warnings.filterwarnings("ignore")
    def h2r(h):
        if h=="white": return (255,255,255)
        if h=="black": return (0,0,0)
        h=h.lstrip("#"); return tuple(int(h[i:i+2],16) for i in (0,2,4))
    NAMES=["light_green","forest_green","water","light_purple","gray","no_vegetation","sand",
           "rock","light_gray","black","snow","residential_road","tertiary_road",
           "unclassified_road","track","foot_path","light_orange_road","medium_orange_road","building"]
    PAL=np.array([h2r(color_dict[n]) if n!="building" else (165,42,42) for n in NAMES],float)
    STABLE={"water","building","residential_road","tertiary_road","unclassified_road",
            "track","foot_path","light_orange_road","medium_orange_road"}
    def cls(img): return np.linalg.norm(img[:,:,None,:]-PAL[None,None,:,:],axis=3).argmin(axis=2)

    ap=argparse.ArgumentParser()
    ap.add_argument("--a", required=True, help="render set A (e.g. Overpass)")
    ap.add_argument("--b", required=True, help="render set B (e.g. PBF)")
    args=ap.parse_args()
    A,B=Path(args.a),Path(args.b)
    stems=sorted(set(p.stem for p in A.glob("*.tif")) & set(p.stem for p in B.glob("*.tif")))
    if not stems: sys.exit("no common chips")
    conf=np.zeros((len(NAMES),len(NAMES)),np.int64); geom_ok=0; exact_px=0; tot_px=0
    per=[]
    for st in stems:
        with rasterio.open(A/f"{st}.tif") as s:
            ia=np.transpose(s.read(),(1,2,0)).astype(float); ta,ca=(s.transform,s.crs)
        with rasterio.open(B/f"{st}.tif") as s:
            ib=np.transpose(s.read(),(1,2,0)).astype(float)
            geom_ok+=int(s.transform==ta and s.crs==ca)
        exact_px+=int((ia==ib).all(axis=2).sum()); tot_px+=ia.shape[0]*ia.shape[1]
        c1,c2=cls(ia),cls(ib)
        per.append((st,float((c1==c2).mean())))
        conf+=np.bincount(c1.ravel()*len(NAMES)+c2.ravel(),
                          minlength=len(NAMES)**2).reshape(len(NAMES),len(NAMES))
    tot=conf.sum(); agree=np.trace(conf)
    si=[i for i,n in enumerate(NAMES) if n in STABLE]
    vi=[i for i,n in enumerate(NAMES) if n not in STABLE]
    s_tot=conf[si,:].sum(); s_ok=sum(conf[i,i] for i in si)
    v_tot=conf[vi,:].sum(); v_ok=sum(conf[i,i] for i in vi)
    print(f"chips compared      : {len(stems)}")
    print(f"GEOMETRY            : {geom_ok}/{len(stems)} identical transform/CRS/size")
    print(f"byte-identical px   : {100*exact_px/tot_px:.2f}%")
    print(f"class agreement     : overall {100*agree/tot:.2f}%  |  stable {100*s_ok/max(s_tot,1):.2f}%"
          f"  |  volatile {100*v_ok/max(v_tot,1):.2f}%")
    per.sort(key=lambda x:x[1])
    print("\nworst 5 chips by class agreement:")
    for st,a_ in per[:5]: print(f"  {st}: {100*a_:.2f}%")
    print("\nlargest off-diagonal flows (A-class -> B-class):")
    off=[(conf[i,j],i,j) for i in range(len(NAMES)) for j in range(len(NAMES)) if i!=j]
    off.sort(reverse=True)
    for n,i,j in off[:6]:
        if n==0: break
        print(f"  {NAMES[i]:<18} -> {NAMES[j]:<18} {n:>9,} px ({100*n/tot:.3f}%)")
    return 0

if __name__=="__main__":
    sys.exit(main())
