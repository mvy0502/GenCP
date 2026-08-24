#!/usr/bin/env python
"""C45 step 7 (dose-response endpoints): epoch-1 cells for C4/C5, run only
because the primary band fired (registration: sweep only if the main effect
replicates; endpoints first). Same procedure as steps 1-3 and 5: STOCH seed 42,
OVP inputs, B1 warp geometry, karios_gencp.json unchanged. Compares the
adversarial penalty D_LPIPS = C4 - C5 at epoch 1 vs epoch 20 (dose-response
under LPIPS, analogous to B1's C1/C2 sweep). Checkpointed throughout.
Label: [STOCH seed42, OVP inputs] n=130, single draw."""
import csv, glob, json, os, shutil, subprocess, sys, warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import numpy as np

warnings.filterwarnings("ignore")
ROOT = Path("/Users/vedat/Documents/GenCP-Generative-Goruntu-Uretimi-OpenStreetMap")
C45 = ROOT / "tubitak/data/tool_runs/C45"
GP = "/opt/homebrew/Caskroom/miniforge/base/envs/gencp/bin/python"
KARIOS = "/opt/homebrew/Caskroom/miniforge/base/envs/karios/bin/karios"
CONF = str(ROOT / "tubitak/configs/karios_gencp.json")
REF = ROOT / "tubitak/data/ankara/run/ref"
SRCCK = {"C4": ROOT / "tubitak/outputs/c4_checkpoints/checkpoints",
         "C5": ROOT / "tubitak/outputs/c5_checkpoints/checkpoints"}
SHIM = C45 / "_shims/s42"
assert (SHIM / "sitecustomize.py").exists()

stems = sorted(p.name[:-4] for p in (ROOT / "tubitak/data/ankara/run/inputs").glob("*.png"))
assert len(stems) == 130

# stage epoch-1 checkpoints
for arm in ("C4", "C5"):
    dst = C45 / f"ck/{arm}_e1/{arm}/latest_net_G.pth"
    if not dst.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(SRCCK[arm] / arm / "1_net_G.pth", dst)
        print(f"staged {arm} epoch 1", flush=True)


def n_fakes(cell):
    arm = cell.split("_")[0]
    d = C45 / f"out/{cell}/{arm}/test_latest/images"
    return len(list(d.glob("*_fake.png"))) if d.is_dir() else 0


def infer(cell):
    arm = cell.split("_")[0]
    if n_fakes(cell) >= 130:
        return cell, 0, "skipped"
    env = dict(os.environ)
    env["PYTHONPATH"] = str(SHIM) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    cmd = [GP, "test.py",
           "--dataroot", "tubitak/data/ankara/run/inputs", "--name", arm,
           "--checkpoints_dir", str(C45 / f"ck/{cell}"),
           "--model", "test", "--netG", "unet_256", "--norm", "batch",
           "--dataset_mode", "single", "--load_size", "256", "--crop_size", "256",
           "--num_test", "130", "--gpu_ids", "-1",
           "--results_dir", str(C45 / f"out/{cell}")]
    with open(C45 / f"_logs/infer_{cell}.log", "w") as lf:
        p = subprocess.run(cmd, cwd=ROOT, env=env, stdout=lf, stderr=subprocess.STDOUT)
    return cell, p.returncode, f"{n_fakes(cell)} fakes"


CELLS = ("C4_e1", "C5_e1")
with ThreadPoolExecutor(max_workers=2) as ex:
    for f in as_completed([ex.submit(infer, c) for c in CELLS]):
        cell, rc, note = f.result()
        print(f"infer {cell}: rc={rc} {note}", flush=True)
        assert rc == 0 and n_fakes(cell) >= 130, cell

# warp (B1 geometry verbatim)
import rasterio
from rasterio.transform import Affine
from rasterio.warp import reproject, Resampling
CRS, GRID_N, INSET, PX = "EPSG:32636", 228, 145.0, 10.0
GSD_SRC = 257 * 10.0 / 256
sel = {f"ank_{r['gx']}_{r['gy']}": (float(r["easting"]), float(r["northing"]))
       for r in csv.DictReader(open(ROOT / "tubitak/data/ankara/final_selection.csv"))}
for cell in CELLS:
    arm = cell.split("_")[0]
    outdir = C45 / f"warp/{cell}"
    outdir.mkdir(parents=True, exist_ok=True)
    for st in stems:
        out = outdir / f"{st}.tif"
        if out.exists():
            continue
        E, N = sel[st]
        tgt = Affine(PX, 0, E + INSET, 0, -PX, N - INSET)
        with rasterio.open(C45 / f"out/{cell}/{arm}/test_latest/images/{st}_fake.png") as s:
            fake = s.read()
        dst = np.zeros((3, GRID_N, GRID_N), "uint8")
        for b in range(3):
            reproject(source=fake[b], destination=dst[b],
                      src_transform=Affine(GSD_SRC, 0, E, 0, -GSD_SRC, N),
                      src_crs=CRS, dst_transform=tgt, dst_crs=CRS,
                      resampling=Resampling.bilinear)
        with rasterio.open(out, "w", driver="GTiff", height=GRID_N, width=GRID_N,
                           count=3, dtype="uint8", crs=CRS, transform=tgt) as d:
            d.write(dst)
print("e1 warps complete", flush=True)


def krun(job):
    cell, st = job
    res = C45 / "karios" / cell / st
    if glob.glob(str(res / "*" / "KLT_matcher_*.csv")):
        return job, 0, 1
    res.mkdir(parents=True, exist_ok=True)
    p = subprocess.run([KARIOS, "process", str(C45 / f"warp/{cell}/{st}.tif"),
                        str(REF / f"{st}_warp.tif"), "--out", str(res),
                        "--conf", CONF, "--no-log-file"], capture_output=True, text=True)
    return job, p.returncode, len(glob.glob(str(res / "*" / "KLT_matcher_*.csv")))


bad, done = [], 0
with ThreadPoolExecutor(max_workers=8) as ex:
    for f in as_completed([ex.submit(krun, (c, st)) for c in CELLS for st in stems]):
        job, rc, ncsv = f.result()
        done += 1
        if rc != 0 or ncsv == 0:
            bad.append(job)
        if done % 40 == 0:
            print(f"KARIOS {done}/260", flush=True)
assert not bad, bad

import pandas as pd


def med(cell, st):
    csvs = glob.glob(str(C45 / "karios" / cell / st / "*" / "KLT_matcher_*.csv"))
    d = pd.read_csv(csvs[0], sep=None, engine="python")
    return (float(np.median(np.hypot(d.dx, d.dy))), len(d)) if len(d) else (np.nan, 0)


e20 = pd.read_csv(C45 / "C45_per_chip.csv").set_index("stem")
rows = []
for st in stems:
    r = {"stem": st}
    for cell in CELLS:
        r[f"{cell}_med"], r[f"{cell}_n"] = med(cell, st)
    rows.append(r)
df = pd.DataFrame(rows).set_index("stem").join(e20[["C4_med", "C5_med"]])
df.to_csv(C45 / "C45_e1_per_chip.csv")

summary = {"label": "[STOCH seed42, OVP inputs] n=130, single draw; endpoints only (e1 vs e20)",
           "cells": {}, "paired": {}}
print("\nepoch endpoints (dose-response under LPIPS):")
for col, name in (("C4_e1_med", "C4_e1"), ("C5_e1_med", "C5_e1"), ("C4_med", "C4_e20"), ("C5_med", "C5_e20")):
    v = df[col]
    summary["cells"][name] = dict(mean=round(float(v.mean()), 4), median=round(float(v.median()), 4))
    print(f"  {name:<7} mean {v.mean():.4f}  median {v.median():.4f}")
for a, b, tag in (("C4_e1_med", "C5_e1_med", "D_LPIPS_e1 (C4-C5 at e1)"),
                  ("C4_med", "C5_med", "D_LPIPS_e20 (C4-C5 at e20)"),
                  ("C4_e1_med", "C4_med", "C4 e1-e20"), ("C5_e1_med", "C5_med", "C5 e1-e20")):
    d = (df[a] - df[b]).dropna()
    se = d.std(ddof=1) / np.sqrt(len(d))
    summary["paired"][tag] = dict(mean=round(float(d.mean()), 4), se=round(float(se), 4),
                                  t=round(float(d.mean() / se), 2), n=len(d))
    print(f"  {tag}: {d.mean():+.4f} ± {se:.4f} px (t={d.mean()/se:.2f})")
with open(C45 / "C45_e1_summary.json", "w") as f:
    json.dump(summary, f, indent=2)
print(f"wrote {C45/'C45_e1_per_chip.csv'} and {C45/'C45_e1_summary.json'}")
