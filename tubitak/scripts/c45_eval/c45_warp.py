#!/usr/bin/env python
"""C45 step 2: warp C4/C5 fakes (2 x 130) plus the 130 input renders to the
228-grid — B1_warp.py geometry verbatim: origins from final_selection.csv,
src Affine(10.0390625, 0, E, 0, -10.0390625, N), tgt Affine(10, 0, E+145, 0,
-10, N-145), bilinear, EPSG:32636, target grid asserted equal to
run/ref/<stem>_warp.tif. The warped inputs feed the edge-ratio mask
(c45_edge_ratio.py). Checkpointed by file."""
import csv, warnings
from pathlib import Path
import numpy as np

warnings.filterwarnings("ignore")
import rasterio
from rasterio.transform import Affine
from rasterio.warp import reproject, Resampling

ROOT = Path("/Users/vedat/Documents/GenCP-Generative-Goruntu-Uretimi-OpenStreetMap")
C45 = ROOT / "tubitak/data/tool_runs/C45"
REF = ROOT / "tubitak/data/ankara/run/ref"
INP = ROOT / "tubitak/data/ankara/run/inputs"
CRS = "EPSG:32636"
GRID_N, INSET, PX = 228, 145.0, 10.0
GSD_SRC = 257 * 10.0 / 256  # 10.0390625

sel = {f"ank_{r['gx']}_{r['gy']}": (float(r["easting"]), float(r["northing"]))
       for r in csv.DictReader(open(ROOT / "tubitak/data/ankara/final_selection.csv"))}
stems = sorted(p.name[:-4] for p in INP.glob("*.png"))
assert len(stems) == 130 and all(s in sel for s in stems)


def warp_one(src_png, out, E, N):
    tgt = Affine(PX, 0, E + INSET, 0, -PX, N - INSET)
    with rasterio.open(REF / f"{out.stem}_warp.tif") as s:
        assert s.transform == tgt and str(s.crs) == CRS, f"grid mismatch {out.stem}"
    with rasterio.open(src_png) as s:
        arr = s.read()
    assert arr.shape == (3, 256, 256), (src_png, arr.shape)
    dst = np.zeros((3, GRID_N, GRID_N), "uint8")
    for b in range(3):
        reproject(source=arr[b], destination=dst[b],
                  src_transform=Affine(GSD_SRC, 0, E, 0, -GSD_SRC, N),
                  src_crs=CRS, dst_transform=tgt, dst_crs=CRS,
                  resampling=Resampling.bilinear)
    prof = dict(driver="GTiff", height=GRID_N, width=GRID_N, count=3,
                dtype="uint8", crs=CRS, transform=tgt)
    with rasterio.open(out, "w", **prof) as d:
        d.write(dst)


n = done = 0
jobs = [("C4", st) for st in stems] + [("C5", st) for st in stems] + [("input", st) for st in stems]
for cell, st in jobs:
    n += 1
    outdir = C45 / f"warp/{cell}"
    outdir.mkdir(parents=True, exist_ok=True)
    out = outdir / f"{st}.tif"
    if out.exists():
        continue
    if cell == "input":
        src = INP / f"{st}.png"
    else:
        src = C45 / f"out/{cell}/{cell}/test_latest/images/{st}_fake.png"
    assert src.exists(), src
    E, N = sel[st]
    warp_one(src, out, E, N)
    done += 1
    if n % 20 == 0:
        print(f"warp {n}/{len(jobs)}", flush=True)
print(f"warp complete {n}/{len(jobs)} ({done} newly written)", flush=True)
