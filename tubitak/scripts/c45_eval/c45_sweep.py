#!/usr/bin/env python
"""C45 step 8 (full dose-response sweep): epochs 1,2,5,10 for C4/C5 (e20 is the
main panel). Run because the endpoints (c45_e1.py) showed the relationship:
penalty grows e1->e20, C5 improves with training, C4 flat. Same procedure as
steps 1-3; e1 cells are skipped by checkpointing. Writes C45_sweep_per_chip.csv
and C45_sweep_summary.json with the D_LPIPS(epoch) trajectory.
Label: [STOCH seed42, OVP inputs] n=130, single draw."""
import csv, glob, json, os, shutil, subprocess, warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import numpy as np

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[3]
C45 = ROOT / "tubitak/data/tool_runs/C45"
GP = os.environ.get("GENCP_PYTHON", "/opt/homebrew/Caskroom/miniforge/base/envs/gencp/bin/python")
KARIOS = os.environ.get("KARIOS_BIN", "/opt/homebrew/Caskroom/miniforge/base/envs/karios/bin/karios")
CONF = str(ROOT / "tubitak/configs/karios_gencp.json")
REF = ROOT / "tubitak/data/ankara/run/ref"
SRCCK = {"C4": ROOT / "tubitak/outputs/c4_checkpoints/checkpoints",
         "C5": ROOT / "tubitak/outputs/c5_checkpoints/checkpoints"}
SHIM = C45 / "_shims/s42"
EPOCHS = (1, 2, 5, 10)
CELLS = [f"{a}_e{e}" for a in ("C4", "C5") for e in EPOCHS]

stems = sorted(p.name[:-4] for p in (ROOT / "tubitak/data/ankara/run/inputs").glob("*.png"))
assert len(stems) == 130 and (SHIM / "sitecustomize.py").exists()

for arm in ("C4", "C5"):
    for e in EPOCHS:
        dst = C45 / f"ck/{arm}_e{e}/{arm}/latest_net_G.pth"
        if not dst.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(SRCCK[arm] / arm / f"{e}_net_G.pth", dst)
            print(f"staged {arm} epoch {e}", flush=True)


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


with ThreadPoolExecutor(max_workers=3) as ex:
    for f in as_completed([ex.submit(infer, c) for c in CELLS]):
        cell, rc, note = f.result()
        print(f"infer {cell}: rc={rc} {note}", flush=True)
        assert rc == 0 and n_fakes(cell) >= 130, cell

import rasterio
from rasterio.transform import Affine
from rasterio.warp import reproject, Resampling
CRS, GRID_N, INSET, PX = "EPSG:32636", 228, 145.0, 10.0
GSD_SRC = 257 * 10.0 / 256
with open(ROOT / "tubitak/data/ankara/final_selection.csv") as fh:
    sel = {f"ank_{r['gx']}_{r['gy']}": (float(r["easting"]), float(r["northing"]))
           for r in csv.DictReader(fh)}
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
print("sweep warps complete", flush=True)


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
jobs = [(c, st) for c in CELLS for st in stems]
with ThreadPoolExecutor(max_workers=8) as ex:
    for f in as_completed([ex.submit(krun, j) for j in jobs]):
        job, rc, ncsv = f.result()
        done += 1
        if rc != 0 or ncsv == 0:
            bad.append(job)
        if done % 40 == 0:
            print(f"KARIOS {done}/{len(jobs)}", flush=True)
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
df = pd.DataFrame(rows).set_index("stem").join(e20[["C4_med", "C4_n", "C5_med", "C5_n"]])
df = df.rename(columns={"C4_med": "C4_e20_med", "C4_n": "C4_e20_n",
                        "C5_med": "C5_e20_med", "C5_n": "C5_e20_n"})
df.to_csv(C45 / "C45_sweep_per_chip.csv")

ALL_E = (1, 2, 5, 10, 20)
summary = {"label": "[STOCH seed42, OVP inputs] n=130, single draw; sweep run because endpoints showed the relationship",
           "trajectory": {}, "penalty_by_epoch": {}}
print("\ndose-response under LPIPS (mean of per-chip medians):")
print(f"{'epoch':>5} {'C4':>8} {'C5':>8} {'D=C4-C5 ± SE':>18} {'t':>6}")
for e in ALL_E:
    m4, m5 = df[f"C4_e{e}_med"], df[f"C5_e{e}_med"]
    d = (m4 - m5).dropna()
    se = d.std(ddof=1) / np.sqrt(len(d))
    summary["trajectory"][f"e{e}"] = dict(C4_mean=round(float(m4.mean()), 4), C4_median=round(float(m4.median()), 4),
                                          C5_mean=round(float(m5.mean()), 4), C5_median=round(float(m5.median()), 4),
                                          C4_pts=float(df[f"C4_e{e}_n"].median()), C5_pts=float(df[f"C5_e{e}_n"].median()))
    summary["penalty_by_epoch"][f"e{e}"] = dict(mean=round(float(d.mean()), 4), se=round(float(se), 4),
                                                t=round(float(d.mean() / se), 2))
    print(f"{e:>5} {m4.mean():>8.4f} {m5.mean():>8.4f} {d.mean():>+11.4f} ± {se:.4f} {d.mean()/se:>6.2f}")
with open(C45 / "C45_sweep_summary.json", "w") as f:
    json.dump(summary, f, indent=2)
print(f"wrote {C45/'C45_sweep_per_chip.csv'} and {C45/'C45_sweep_summary.json'}")
