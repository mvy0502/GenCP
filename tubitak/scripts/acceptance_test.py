#!/usr/bin/env python
"""Acceptance gate for the rasteriser (renderer-tolerance.md pass mark).

Phases:
  prep     resize rendered 257 chips to the 256 PNG the network consumes
  warp     put generated output on the affine-corrected common grid
  list     emit stems for the parallel KARIOS runner
  score    paired comparison against the sensitivity-run baseline
  graded   palette / confusion / geometry / agreement vs the reference rasters
"""
from __future__ import annotations
import argparse, glob, sys, warnings
from pathlib import Path
import numpy as np

import os
ROOT = Path(__file__).resolve().parents[2]
_TAG = os.environ.get("ACC_TAG", "")
CH   = ROOT/f"tubitak/data/rasteriser/chips{_TAG}"
SENS = ROOT/"tubitak/data/sensitivity"
ACC  = ROOT/f"tubitak/data/rasteriser/acc{_TAG}"
REFS = ROOT/"tubitak/data/karios/reference"
GRID_N, INSET, PX = 228, 145.0, 10.0
GSD_B = 257*10.0/256
PASS_BAND = 0.15

def stems():
    return sorted(Path(p).stem for p in glob.glob(str(CH/"*.tif")))

def prep():
    import rasterio
    from PIL import Image
    from torchvision import transforms
    r256 = transforms.Resize([256,256], transforms.InterpolationMode.BICUBIC)
    (ACC/"inputs").mkdir(parents=True, exist_ok=True)
    for st in stems():
        with rasterio.open(CH/f"{st}.tif") as s:
            img = Image.fromarray(np.transpose(s.read(),(1,2,0)))
        r256(img).save(ACC/"inputs"/f"{st}.png")
    print(f"prepped {len(stems())} inputs")

def warp():
    import rasterio
    from rasterio.transform import Affine
    from rasterio.warp import reproject, Resampling
    gd = ACC/"out/genCP_HR_RGB_model/test_latest/images"
    (ACC/"arms").mkdir(parents=True, exist_ok=True)
    n=0
    for st in stems():
        g = gd/f"{st}_fake.png"
        r = REFS/"satellite"/f"{st}.tif"
        if not g.exists(): continue
        with rasterio.open(r) as s: crs, T = s.crs, s.transform
        ox, oy = T.c, T.f
        tgt = Affine(PX,0,ox+INSET,0,-PX,oy-INSET)
        with rasterio.open(g) as s: arr = s.read()
        dst = np.zeros((3,GRID_N,GRID_N),"uint8")
        for b in range(3):
            reproject(source=arr[b],destination=dst[b],
                      src_transform=Affine(GSD_B,0,ox,0,-GSD_B,oy),src_crs=crs,
                      dst_transform=tgt,dst_crs=crs,resampling=Resampling.bilinear)
        prof=dict(driver="GTiff",height=GRID_N,width=GRID_N,count=3,dtype="uint8",
                  crs=crs,transform=tgt)
        with rasterio.open(ACC/"arms"/f"{st}.tif","w",**prof) as d: d.write(dst)
        n+=1
    print(f"warped {n}")

def score():
    import pandas as pd
    rows=[]
    for f in glob.glob(str(ACC/"results/*/*/KLT_matcher_*.csv")):
        st=f.split("/")[-3]
        try: d=pd.read_csv(f,sep=None,engine="python")
        except Exception: continue
        if len(d): rows.append(dict(stem=st,n=len(d),
                                    med=float(np.median(np.hypot(d.dx,d.dy)))))
    ours=pd.DataFrame(rows).set_index("stem")
    if os.environ.get("ACC_BASE") == "armB":
        ap_=pd.read_csv(ROOT/"tubitak/data/karios/results/all_points.csv")
        ap_=ap_[ap_.arm=="B"]; ap_["r"]=np.hypot(ap_.dx,ap_.dy)
        base=ap_.groupby("stem").agg(n=("dx","size"),med=("r","median"))
    else:
        base_rows=[]
        for f in glob.glob(str(SENS/"results/base/*/*/KLT_matcher_*.csv")):
            st=f.split("/")[-3]
            try: d=pd.read_csv(f,sep=None,engine="python")
            except Exception: continue
            if len(d): base_rows.append(dict(stem=st,n=len(d),
                                             med=float(np.median(np.hypot(d.dx,d.dy)))))
        base=pd.DataFrame(base_rows).set_index("stem")
    common=ours.index.intersection(base.index)
    o,b=ours.loc[common],base.loc[common]
    d=o.med-b.med
    se=d.std(ddof=1)/np.sqrt(len(d))
    print(f"chips scored: {len(common)}")
    print(f"baseline (reference rasters) : mean of per-chip medians {b.med.mean():.4f} px, "
          f"points/chip median {b.n.median():.0f}")
    print(f"OURS (rasteriser)            : mean of per-chip medians {o.med.mean():.4f} px, "
          f"points/chip median {o.n.median():.0f}")
    print(f"\npaired difference : {d.mean():+.4f} +/- {se:.4f} px  "
          f"(t={d.mean()/se:.2f}); chips worse: {(d>0).sum()}/{len(d)}")
    print(f"point-count change: {100*(o.n.sum()-b.n.sum())/b.n.sum():+.1f}%")
    verdict = "PASS" if abs(d.mean()) < PASS_BAND else "FAIL"
    print(f"\nACCEPTANCE ({PASS_BAND} px band): {verdict}   (measured {d.mean():+.4f} px)")
    # subgroup: sparse vs dense OSM
    import rasterio
    from scipy.ndimage import sobel
    ed={}
    for st in common:
        with rasterio.open(REFS/"osm"/f"{st}.tif") as s:
            a=np.transpose(s.read(),(1,2,0)).astype(float)
        g=a.mean(axis=2); ed[st]=float((np.hypot(sobel(g,0),sobel(g,1))>20).mean())
    med_ed=float(np.median(list(ed.values())))
    lo=[st for st in common if ed[st]<=med_ed]; hi=[st for st in common if ed[st]>med_ed]
    for lab,grp in (("sparse OSM",lo),("dense OSM",hi)):
        dd=(o.loc[grp].med-b.loc[grp].med)
        print(f"  {lab:<11} n={len(grp):>2}  d={dd.mean():+.4f} px  "
              f"points {100*(o.loc[grp].n.sum()-b.loc[grp].n.sum())/b.loc[grp].n.sum():+.1f}%")
    d.to_csv(ACC/"paired_diff.csv")

def graded():
    import rasterio
    sys.path.insert(0, str(ROOT/"GenCP_HR_demo"))
    from genCP_HR_osm_colors import color_dict
    def h2r(h):
        if h=="white": return (255,255,255)
        if h=="black": return (0,0,0)
        h=h.lstrip("#"); return tuple(int(h[i:i+2],16) for i in (0,2,4))
    NAMES=["light_green","forest_green","water","light_purple","gray","no_vegetation",
           "sand","rock","light_gray","black","snow","residential_road","tertiary_road",
           "unclassified_road","track","foot_path","light_orange_road","medium_orange_road",
           "building"]
    PALX=np.array([h2r(color_dict[n]) if n!="building" else (165,42,42) for n in NAMES],float)
    STABLE={"water","building","residential_road","tertiary_road","unclassified_road",
            "track","foot_path","light_orange_road","medium_orange_road"}
    def cls(img): 
        return np.linalg.norm(img[:,:,None,:]-PALX[None,None,:,:],axis=3).argmin(axis=2)
    conf=np.zeros((len(NAMES),len(NAMES)),np.int64)
    extra=set(); geom_ok=0
    for st in stems():
        with rasterio.open(CH/f"{st}.tif") as s:
            ours=np.transpose(s.read(),(1,2,0)).astype(float)
            t1,c1,sz1=s.transform,s.crs,(s.width,s.height)
        with rasterio.open(REFS/"osm"/f"{st}.tif") as s:
            ref=np.transpose(s.read(),(1,2,0)).astype(float)
            geom_ok += int(s.transform==t1 and s.crs==c1 and (s.width,s.height)==sz1)
        # palette subset check on interiors (flat 3x3 neighbourhoods)
        o8=ours.astype(np.int32)
        key=(o8[:,:,0]<<16)|(o8[:,:,1]<<8)|o8[:,:,2]
        same=np.ones_like(key,bool)
        for dy in(-1,0,1):
            for dx in(-1,0,1):
                if dy==dx==0: continue
                same &= (np.roll(np.roll(key,dy,0),dx,1)==key)
        same[0,:]=same[-1,:]=same[:,0]=same[:,-1]=False
        pal_ok={(int(r),int(g),int(b)) for r,g,b in PALX}
        for k in np.unique(key[same]):
            rgb=((int(k)>>16)&255,(int(k)>>8)&255,int(k)&255)
            if rgb not in pal_ok: extra.add(rgb)
        conf += np.bincount(cls(ref).ravel()*len(NAMES)+cls(ours).ravel(),
                            minlength=len(NAMES)**2).reshape(len(NAMES),len(NAMES))
    print(f"GEOMETRY : {geom_ok}/{len(stems())} chips identical transform/CRS/size")
    print(f"PALETTE  : interior colours not in the reference palette: "
          f"{len(extra)} {'-> HARD FAIL '+str(sorted(extra)[:5]) if extra else '(exact subset - PASS)'}")
    tot=conf.sum()
    agree=np.trace(conf)
    stable_i=[i for i,n in enumerate(NAMES) if n in STABLE]
    s_tot=conf[stable_i,:].sum(); s_ok=sum(conf[i,i] for i in stable_i)
    v_i=[i for i,n in enumerate(NAMES) if n not in STABLE]
    v_tot=conf[v_i,:].sum(); v_ok=sum(conf[i,i] for i in v_i)
    print(f"AGREEMENT: overall {100*agree/tot:.1f}%  |  stable classes "
          f"{100*s_ok/max(s_tot,1):.1f}%  |  volatile (landuse) {100*v_ok/max(v_tot,1):.1f}%")
    print("\nper-class recall (reference px of class also rendered as class), classes >0.2%:")
    for i,n in enumerate(NAMES):
        row=conf[i].sum()
        if row < tot*0.002: continue
        top=np.argsort(conf[i])[::-1][:2]
        alt=", ".join(f"{NAMES[j]} {100*conf[i,j]/row:.0f}%" for j in top if j!=i and conf[i,j]>0.05*row)
        print(f"  {n:<18} {100*conf[i,i]/row:5.1f}%  of {100*row/tot:5.2f}% of px"
              + (f"   mostly -> {alt}" if alt else ""))

if __name__ == "__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--phase",choices=["prep","warp","list","score","graded"],required=True)
    a=ap.parse_args()
    warnings.filterwarnings("ignore")
    if a.phase=="list":
        for st in stems(): print(st)
    else: globals()[a.phase]()
