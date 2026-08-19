#!/usr/bin/env python
"""Generalised per-tile pipeline: grid -> SCL screen -> mini-extracts -> CLC+ renders
[-> training pairs]. Reproduces the Ankara/T36TVK flow for any granule directory
containing TCI.tif + SCL.tif from the fixed snapshots.

Usage:
    python tile_pipeline.py --tile-dir tubitak/data/tiles36SVJ --tag 36SVJ [--pairs]
"""
from __future__ import annotations
import argparse, csv, json, subprocess, sys, warnings
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/"tubitak/scripts")); sys.path.insert(0, str(ROOT/"GenCP_HR_demo"))
N, GSD = 257, 10.0
PBF = ROOT/"tubitak/data/geofabrik/turkey-latest.osm.pbf"

def grid_and_screen(td, tag):
    import rasterio
    from rasterio.windows import Window
    out = td/"chip_grid.csv"
    if out.exists():
        return [r for r in csv.DictReader(open(out))]
    scl_src = rasterio.open(td/"SCL.tif"); scl = scl_src.read(1); scl_src.close()
    rows = []
    with rasterio.open(td/"TCI.tif") as s:
        W,H,T = s.width, s.height, s.transform
        nx,ny = W//N, H//N
        for gy in range(ny):
            for gx in range(nx):
                a = s.read(window=Window(gx*N,gy*N,N,N))
                nod = float(((a[0]==0)&(a[1]==0)&(a[2]==0)).mean())
                sw = scl[(gy*N)//2:(gy*N)//2+129,(gx*N)//2:(gx*N)//2+129]
                cloud = float(np.isin(sw,(3,8,9,10)).mean())
                snow = float((sw==11).mean())
                wt = rasterio.windows.transform(Window(gx*N,gy*N,N,N),T)
                rows.append(dict(gx=gx,gy=gy,easting=wt.c,northing=wt.f,
                                 nodata=round(nod,5),cloud_scl=round(cloud,5),
                                 snow=round(snow,5)))
            if (gy+1)%10==0: print(f"  [{tag}] grid row {gy+1}/{ny}", flush=True)
    with open(out,"w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    return rows

def valid(rows):
    return [r for r in rows if float(r["nodata"])<=0.005
            and float(r["cloud_scl"])<=0.01 and float(r["snow"])<=0.02]

def cut_extracts(td, tag, rows, crs):
    from pyproj import Transformer
    tr = Transformer.from_crs(crs,"EPSG:4326",always_xy=True)
    mini = td/"minipbf"; mini.mkdir(exist_ok=True)
    todo=[r for r in rows if not (mini/f"{tag}_{r['gx']}_{r['gy']}.osm.pbf").exists()]
    for i in range(0,len(todo),150):
        ex=[]
        for r in todo[i:i+150]:
            x0=float(r["easting"]); y1=float(r["northing"])
            x1=x0+N*GSD; y0=y1-N*GSD
            pts=[tr.transform(x,y) for x,y in ((x0-300,y0-300),(x1+300,y0-300),
                                               (x1+300,y1+300),(x0-300,y1+300))]
            ex.append({"output":f"{tag}_{r['gx']}_{r['gy']}.osm.pbf",
                       "bbox":[round(min(p[0] for p in pts),6),round(min(p[1] for p in pts),6),
                               round(max(p[0] for p in pts),6),round(max(p[1] for p in pts),6)]})
        cfg=mini/"_cfg.json"; cfg.write_text(json.dumps({"directory":str(mini),"extracts":ex}))
        subprocess.run(["osmium","extract","-c",str(cfg),"--overwrite",str(PBF)],
                       capture_output=True)
        print(f"  [{tag}] extracts batch {i//150+1}", flush=True)

def render_all(td, tag, rows, crs):
    import osm_to_raster as OTR
    rend = td/"clc_renders"; rend.mkdir(exist_ok=True)
    ok=0
    for i,r in enumerate(rows):
        out=rend/f"{tag}_{r['gx']}_{r['gy']}.tif"
        if out.exists(): ok+=1; continue
        mini=td/"minipbf"/f"{tag}_{r['gx']}_{r['gy']}.osm.pbf"
        if not mini.exists(): continue
        x0=float(r["easting"]); y1=float(r["northing"])
        try:
            OTR.make_chip((x0,y1-N*GSD,x0+N*GSD,y1),crs,out,pbf=mini,base_product="clcplus")
            ok+=1
        except Exception as e:
            print(f"  [{tag}] {r['gx']},{r['gy']}: {type(e).__name__}",flush=True)
        if (i+1)%150==0: print(f"  [{tag}] rendered {ok}/{len(rows)}",flush=True)
    print(f"[{tag}] RENDERS {ok}/{len(rows)}",flush=True)

def build_pairs(td, tag, rows):
    import rasterio
    from rasterio.windows import Window
    pairs=td/"pairs"; pairs.mkdir(exist_ok=True)
    built=0
    with rasterio.open(td/"TCI.tif") as s:
        for r in rows:
            gx,gy=r["gx"],r["gy"]
            dst=pairs/f"{tag}_{gx}_{gy}.tif"
            if dst.exists(): built+=1; continue
            rend=td/"clc_renders"/f"{tag}_{gx}_{gy}.tif"
            if not rend.exists(): continue
            sat=s.read(window=Window(int(gx)*N,int(gy)*N,N,N))
            with rasterio.open(rend) as rr: osm=rr.read()
            pair=np.concatenate([sat,osm],axis=2)
            prof=dict(driver="GTiff",height=N,width=2*N,count=3,dtype="uint8",compress="lzw")
            with rasterio.open(dst,"w",**prof) as d: d.write(pair)
            built+=1
    print(f"[{tag}] PAIRS {built}",flush=True)

def main():
    import rasterio
    warnings.filterwarnings("ignore")
    ap=argparse.ArgumentParser()
    ap.add_argument("--tile-dir",required=True); ap.add_argument("--tag",required=True)
    ap.add_argument("--pairs",action="store_true")
    a=ap.parse_args()
    td=Path(a.tile_dir)
    with rasterio.open(td/"TCI.tif") as s: crs=str(s.crs)
    rows=grid_and_screen(td,a.tag)
    v=valid(rows)
    print(f"[{a.tag}] CRS {crs}; candidates {len(rows)}, VALID {len(v)}",flush=True)
    cut_extracts(td,a.tag,v,crs)
    render_all(td,a.tag,v,crs)
    if a.pairs: build_pairs(td,a.tag,v)
    print(f"[{a.tag}] TILE PIPELINE DONE",flush=True)

if __name__=="__main__":
    main()
