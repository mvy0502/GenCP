#!/usr/bin/env python
"""OSM-only information scores for every valid Ankara candidate chip.

Pipeline per chip: mini-PBF cut from the Turkey snapshot (batched osmium passes,
150 bboxes each, to respect open-file limits) -> OSM-only render (identical
rasteriser path, WorldCover off) -> edge density + non-dominant fraction.
Resumable; class count is excluded (proxy validation: rho 0.315, unusable).
"""
from __future__ import annotations
import csv, json, subprocess, sys, warnings
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
GRID = ROOT/"tubitak/data/ankara/chip_grid.csv"
MINI = ROOT/"tubitak/data/geofabrik/ankara_chips"
REND = ROOT/"tubitak/data/ankara/osm_renders"
OUTC = ROOT/"tubitak/data/ankara/osm_scores.csv"
PBF  = ROOT/"tubitak/data/geofabrik/turkey-latest.osm.pbf"
N, GSD = 257, 10.0
CRS = "EPSG:32636"

def valid_rows():
    rows=[r for r in csv.DictReader(open(GRID))
          if float(r["nodata"])<=0.005 and float(r["cloud_scl"])<=0.01
          and float(r["snow"])<=0.02]
    return rows

def cut(rows):
    from pyproj import Transformer
    tr=Transformer.from_crs(CRS,"EPSG:4326",always_xy=True)
    MINI.mkdir(parents=True, exist_ok=True)
    todo=[r for r in rows if not (MINI/f"ank_{r['gx']}_{r['gy']}.osm.pbf").exists()]
    print(f"cutting {len(todo)} mini-extracts in batches of 150", flush=True)
    for i in range(0,len(todo),150):
        batch=todo[i:i+150]; ex=[]
        for r in batch:
            x0=float(r["easting"]); y1=float(r["northing"])
            x1=x0+N*GSD; y0=y1-N*GSD
            pts=[tr.transform(x,y) for x,y in ((x0-300,y0-300),(x1+300,y0-300),
                                               (x1+300,y1+300),(x0-300,y1+300))]
            W=min(p[0] for p in pts); S=min(p[1] for p in pts)
            E=max(p[0] for p in pts); Nn=max(p[1] for p in pts)
            ex.append({"output":f"ank_{r['gx']}_{r['gy']}.osm.pbf",
                       "bbox":[round(W,6),round(S,6),round(E,6),round(Nn,6)]})
        cfg=MINI/"_cfg.json"
        cfg.write_text(json.dumps({"directory":str(MINI),"extracts":ex}))
        rr=subprocess.run(["osmium","extract","-c",str(cfg),"--overwrite",str(PBF)],
                          capture_output=True,text=True)
        if rr.returncode: print(f"  batch {i//150}: osmium failed {rr.stderr[:200]}", flush=True)
        else: print(f"  batch {i//150+1}/{(len(todo)+149)//150} done", flush=True)

def render_and_score(rows):
    sys.path.insert(0,str(ROOT/"tubitak/scripts")); sys.path.insert(0,str(ROOT/"GenCP_HR_demo"))
    import osm_to_raster as OTR
    import rasterio
    from scipy.ndimage import sobel
    REND.mkdir(parents=True, exist_ok=True)
    done={}
    if OUTC.exists():
        done={(r["gx"],r["gy"]):r for r in csv.DictReader(open(OUTC))}
    out=open(OUTC,"a",newline=""); w=csv.writer(out)
    if not done: w.writerow(["gx","gy","edge_density","non_dominant"])
    n_ok=0
    for i,r in enumerate(rows):
        key=(r["gx"],r["gy"])
        if key in done: n_ok+=1; continue
        mini=MINI/f"ank_{r['gx']}_{r['gy']}.osm.pbf"
        if not mini.exists(): continue
        x0=float(r["easting"]); y1=float(r["northing"])
        bounds=(x0, y1-N*GSD, x0+N*GSD, y1)
        chip=REND/f"ank_{r['gx']}_{r['gy']}.tif"
        try:
            OTR.make_chip(bounds, CRS, chip, pbf=mini, use_worldcover=False)
        except Exception as e:
            print(f"  ank_{key}: {type(e).__name__}: {str(e)[:60]}", flush=True); continue
        with rasterio.open(chip) as s: a=np.transpose(s.read(),(1,2,0)).astype(float)
        g=a.mean(axis=2)
        edge=float((np.hypot(sobel(g,0),sobel(g,1))>20).mean())
        px=a.reshape(-1,3).astype(np.uint8)
        _,cnt=np.unique(px,axis=0,return_counts=True)
        nd=float(1-cnt.max()/cnt.sum())
        w.writerow([r["gx"],r["gy"],round(edge,5),round(nd,5)]); out.flush()
        n_ok+=1
        if (i+1)%50==0: print(f"  scored {n_ok}/{len(rows)}", flush=True)
    out.close()
    print(f"SCORED {n_ok}/{len(rows)}", flush=True)

if __name__=="__main__":
    warnings.filterwarnings("ignore")
    rows=valid_rows()
    print(f"valid candidates: {len(rows)}", flush=True)
    cut(rows)
    render_and_score(rows)
    print("ANKARA SCORES DONE", flush=True)
