#!/usr/bin/env python
"""Parallel CLC+ chip renderer with counted heartbeat and per-chip resume.

Rendering is fully local (PBF mini-extracts, the local CLC+ GeoTIFF, CPU
palette/kernel work) — the external-service constraint that once forced serial
execution is gone. 8 worker processes; each opens its own file handles.

Heartbeat: a timestamped line every 25 chips with done/total/rate/ETA.
The wrapper script adds a stall detector on the file count itself —
absence of error is not presence of progress.
"""
from __future__ import annotations
import argparse, csv, sys, time, warnings
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/"tubitak/scripts")); sys.path.insert(0, str(ROOT/"GenCP_HR_demo"))
N, GSD = 257, 10.0

def _work(task):
    td, tag, gx, gy, easting, northing, crs = task
    import warnings as w; w.filterwarnings("ignore")
    import osm_to_raster as OTR
    out = Path(td)/"clc_renders"/f"{tag}_{gx}_{gy}.tif"
    if out.exists(): return "skip"
    mini = Path(td)/"minipbf"/f"{tag}_{gx}_{gy}.osm.pbf"
    if not mini.exists(): return "nopbf"
    try:
        OTR.make_chip((easting, northing-N*GSD, easting+N*GSD, northing),
                      crs, out, pbf=mini, base_product="clcplus")
        return "ok"
    except Exception as e:
        return f"ERR:{type(e).__name__}"

def main():
    warnings.filterwarnings("ignore")
    ap = argparse.ArgumentParser()
    ap.add_argument("--tile-dir", required=True); ap.add_argument("--tag", required=True)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    td = Path(a.tile_dir)
    import rasterio
    with rasterio.open(td/"TCI.tif") as s: crs = str(s.crs)
    rows = [r for r in csv.DictReader(open(td/"chip_grid.csv"))
            if float(r["nodata"])<=0.005 and float(r["cloud_scl"])<=0.01
            and float(r["snow"])<=0.02]
    (td/"clc_renders").mkdir(exist_ok=True)
    tasks = [(str(td), a.tag, r["gx"], r["gy"], float(r["easting"]),
              float(r["northing"]), crs) for r in rows]
    done_already = sum(1 for t in tasks
                       if (td/"clc_renders"/f"{a.tag}_{t[2]}_{t[3]}.tif").exists())
    todo = [t for t in tasks
            if not (td/"clc_renders"/f"{a.tag}_{t[2]}_{t[3]}.tif").exists()]
    if a.limit: todo = todo[:a.limit]
    total = len(tasks)
    print(f"[{a.tag}] valid {total}, already {done_already}, rendering {len(todo)} "
          f"with {a.workers} workers", flush=True)
    t0 = time.time(); done = 0; errs = 0
    with Pool(a.workers) as pool:
        for res in pool.imap_unordered(_work, todo, chunksize=4):
            done += 1
            if res.startswith("ERR"): errs += 1
            if done % 25 == 0 or done == len(todo):
                el = time.time()-t0; rate = done/el
                eta = (len(todo)-done)/rate if rate>0 else 0
                print(f"[{a.tag}] {time.strftime('%H:%M:%S')} "
                      f"{done_already+done}/{total} done  rate {rate:.2f}/s  "
                      f"ETA {eta/60:.0f} min  errs {errs}", flush=True)
    print(f"[{a.tag}] RENDER COMPLETE ({errs} errors)", flush=True)

if __name__ == "__main__":
    main()
