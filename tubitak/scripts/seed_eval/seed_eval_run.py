#!/usr/bin/env python
"""Seed-parameterised evaluation runner for the 2x2 loss-factorial replication.

Registration: tubitak/docs/seed-replication-registration.md (AMENDMENT SEED-a for the
inference seed). This is a THIN WRAPPER around the committed c45_eval harness
(tubitak/scripts/c45_eval/, commit 40cde9b). The per-step logic - inference command,
warp geometry, KARIOS invocation, edge-ratio definition, scoring formula - is reused
VERBATIM. What this file changes is only:

  * WHICH SEED's checkpoints are read, and where the outputs go (tool_runs/C45_s{seed}/)
  * FOUR arms instead of two. For seed 42 the committed harness inferred only C4 and C5 and
    read C1/C2/pretrained from B1_per_chip.csv. For a replication seed, C1 and C2 are NEW
    CHECKPOINTS and must be inferred, warped and KARIOS-scored like C4 and C5.

PRETRAINED IS TRAINING-INDEPENDENT and therefore continues to come from B1_per_chip.csv (and,
for the edge ratio, from the pkgA grays). It is the released generator: no training happens
to it, so it does not vary with the training seed and re-inferring it per seed would produce
the same numbers at four times the cost. It is the one arm the seed factor cannot touch.

INFERENCE SEED IS FIXED AT 42 FOR EVERY TRAINING SEED (AMENDMENT SEED-a). The training seed
is the only manipulated factor; letting the evaluation dropout draw follow it would vary two
things at once. The shim written below is byte-identical in effect to B1's _shims/s42.

Usage
-----
    python tubitak/scripts/seed_eval/seed_eval_run.py --seed 43
    python tubitak/scripts/seed_eval/seed_eval_run.py --seed 42 --reproduce   # the gate

`--reproduce` runs seed 42 through this runner into tool_runs/C45_s42_repro/ and diffs the
result against the committed tool_runs/C45/ files, per arm and per column. The committed
files are never written to.
"""
import argparse
import csv
import glob
import hashlib
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd

DEFAULT_ROOT = Path(__file__).resolve().parents[3]
GP = os.environ.get("GENCP_PYTHON", "/opt/homebrew/Caskroom/miniforge/base/envs/gencp/bin/python")
KARIOS = os.environ.get("KARIOS_BIN", "/opt/homebrew/Caskroom/miniforge/base/envs/karios/bin/karios")

FINE_TUNED = ("C1", "C2", "C4", "C5")     # the four cells of the 2x2; all vary with the seed
CRS = "EPSG:32636"
GRID_N, INSET, PX = 228, 145.0, 10.0
GSD_SRC = 257 * 10.0 / 256                # 10.0390625, from c45_warp.py
EDGE_THRESH = 20.0                        # from c45_edge_ratio.py / hallucination_analysis.py


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def ckpt_dir(root, arm, seed):
    """Checkpoints for one arm at one seed.

    Seed 42 lives in the original directories; replication seeds carry an _s{seed} suffix,
    matching how the kernel outputs are downloaded.
    """
    base = f"{arm.lower()}_checkpoints" if seed == 42 else f"{arm.lower()}_checkpoints_s{seed}"
    return root / "tubitak/outputs" / base / "checkpoints"


# ----------------------------------------------------------------------------- step 1
def step_infer(root, out, seed):
    """c45_infer.py verbatim, over four arms instead of two, shim pinned to 42."""
    shim = out / "_shims/s42"
    shim.mkdir(parents=True, exist_ok=True)
    (shim / "sitecustomize.py").write_text(
        "import random, numpy, torch\n"
        "SEED = 42\n"
        "random.seed(SEED)\n"
        "numpy.random.seed(SEED)\n"
        "torch.manual_seed(SEED)\n"
        "torch.cuda.manual_seed_all(SEED)\n"
        "print('[seed-hook] random/numpy/torch seeded with %d' % SEED, flush=True)\n")
    (out / "_logs").mkdir(parents=True, exist_ok=True)

    import torch
    for arm in FINE_TUNED:
        ck = ckpt_dir(root, arm, seed)
        a = torch.load(ck / arm / "latest_net_G.pth", map_location="cpu")
        b = torch.load(ck / arm / "20_net_G.pth", map_location="cpu")
        assert set(a) == set(b) and all(torch.equal(a[k], b[k]) for k in a), \
            f"{arm}: latest_net_G.pth is not tensor-equal to 20_net_G.pth"
        print(f"  {arm}: latest_net_G.pth tensor-equal to 20_net_G.pth", flush=True)

    def n_fakes(arm):
        d = out / f"out/{arm}/{arm}/test_latest/images"
        return len(list(d.glob("*_fake.png"))) if d.is_dir() else 0

    def run(arm):
        if n_fakes(arm) >= 130:
            return arm, 0, "skipped"
        env = dict(os.environ)
        env["PYTHONPATH"] = str(shim) + (os.pathsep + env["PYTHONPATH"]
                                         if env.get("PYTHONPATH") else "")
        cmd = [GP, "test.py",
               "--dataroot", "tubitak/data/ankara/run/inputs",
               "--name", arm,
               "--checkpoints_dir", str(ckpt_dir(root, arm, seed)),
               "--model", "test", "--netG", "unet_256", "--norm", "batch",
               "--dataset_mode", "single", "--load_size", "256", "--crop_size", "256",
               "--num_test", "130", "--gpu_ids", "-1",
               "--results_dir", str(out / f"out/{arm}")]
        with open(out / f"_logs/infer_{arm}.log", "w") as lf:
            p = subprocess.run(cmd, cwd=root, env=env, stdout=lf, stderr=subprocess.STDOUT)
        return arm, p.returncode, f"{n_fakes(arm)} fakes"

    bad = []
    with ThreadPoolExecutor(max_workers=2) as ex:
        for f in as_completed([ex.submit(run, a) for a in FINE_TUNED]):
            arm, rc, note = f.result()
            print(f"  infer {arm}: rc={rc} {note}", flush=True)
            if rc != 0 or n_fakes(arm) < 130:
                bad.append((arm, rc))
    if bad:
        raise SystemExit(f"inference failures: {bad}")


# ----------------------------------------------------------------------------- step 2
def step_warp(root, out, stems):
    """c45_warp.py geometry verbatim; four arms plus the input renders."""
    import warnings
    warnings.filterwarnings("ignore", category=UserWarning)   # rasterio NotGeoreferenced
    import rasterio
    from rasterio.transform import Affine
    from rasterio.warp import reproject, Resampling

    REF = root / "tubitak/data/ankara/run/ref"
    INP = root / "tubitak/data/ankara/run/inputs"
    with open(root / "tubitak/data/ankara/final_selection.csv") as fh:
        sel = {f"ank_{r['gx']}_{r['gy']}": (float(r["easting"]), float(r["northing"]))
               for r in csv.DictReader(fh)}
    assert all(s in sel for s in stems)

    def warp_one(src_png, out_tif, stem, E, N):
        tgt = Affine(PX, 0, E + INSET, 0, -PX, N - INSET)
        with rasterio.open(REF / f"{stem}_warp.tif") as s:
            assert s.transform == tgt and str(s.crs) == CRS, f"grid mismatch {stem}"
        with rasterio.open(src_png) as s:
            arr = s.read()
        assert arr.shape == (3, 256, 256), (src_png, arr.shape)
        dst = np.zeros((3, GRID_N, GRID_N), "uint8")
        for b in range(3):
            reproject(source=arr[b], destination=dst[b],
                      src_transform=Affine(GSD_SRC, 0, E, 0, -GSD_SRC, N), src_crs=CRS,
                      dst_transform=tgt, dst_crs=CRS, resampling=Resampling.bilinear)
        prof = dict(driver="GTiff", height=GRID_N, width=GRID_N, count=3,
                    dtype="uint8", crs=CRS, transform=tgt)
        with rasterio.open(out_tif, "w", **prof) as d:
            d.write(dst)

    jobs = [(a, st) for a in FINE_TUNED for st in stems] + [("input", st) for st in stems]
    n = done = 0
    for cell, st in jobs:
        n += 1
        outdir = out / f"warp/{cell}"
        outdir.mkdir(parents=True, exist_ok=True)
        dst = outdir / f"{st}.tif"
        if dst.exists():
            continue
        src = (INP / f"{st}.png") if cell == "input" else \
              (out / f"out/{cell}/{cell}/test_latest/images/{st}_fake.png")
        assert src.exists(), src
        E, N = sel[st]
        warp_one(src, dst, st, E, N)
        done += 1
        if n % 100 == 0:
            print(f"  warp {n}/{len(jobs)}", flush=True)
    print(f"  warp complete {n}/{len(jobs)} ({done} newly written)", flush=True)


# ----------------------------------------------------------------------------- step 3
def step_karios(root, out, stems):
    """c45_karios.py verbatim; four arms instead of two. Config unchanged."""
    REF = root / "tubitak/data/ankara/run/ref"
    CONF = str(root / "tubitak/configs/karios_gencp.json")
    jobs = [(a, st) for a in FINE_TUNED for st in stems]

    def run(job):
        arm, st = job
        res = out / "karios" / arm / st
        if glob.glob(str(res / "*" / "KLT_matcher_*.csv")):
            return job, 0, 1, "skipped"
        res.mkdir(parents=True, exist_ok=True)
        p = subprocess.run([KARIOS, "process", str(out / f"warp/{arm}/{st}.tif"),
                            str(REF / f"{st}_warp.tif"), "--out", str(res),
                            "--conf", CONF, "--no-log-file"],
                           capture_output=True, text=True)
        csvs = glob.glob(str(res / "*" / "KLT_matcher_*.csv"))
        return job, p.returncode, len(csvs), p.stderr[-300:] if p.returncode else ""

    done, bad = 0, []
    with ThreadPoolExecutor(max_workers=8) as ex:
        for f in as_completed([ex.submit(run, j) for j in jobs]):
            job, rc, ncsv, err = f.result()
            done += 1
            if rc != 0 or ncsv == 0:
                bad.append((job, rc, err))
            if done % 100 == 0:
                print(f"  KARIOS {done}/{len(jobs)}", flush=True)
    print(f"  KARIOS complete: {done}/{len(jobs)}, failures: {len(bad)}", flush=True)
    for job, rc, err in bad[:20]:
        print("  FAIL", job, rc, err)
    if bad:
        raise SystemExit(f"KARIOS failures: {len(bad)}")


# ----------------------------------------------------------------------------- step 4
def step_edge(root, out, stems):
    """c45_edge_ratio.py definition verbatim: input-silent = grad_mag(BT.601 of the warped
    input render) <= 20; edge = grad_mag > 20 on the arm's output and on the real chip over
    the SAME pixels; per-chip ratio = edge_fraction(fake) / edge_fraction(real).

    Difference from the committed seed-42 run, stated because the gate will surface it:
    that run took pretrained/C1/C2 from the pkgA BT.601 grays and only C4/C5 from the C45
    warps. Here the four FINE-TUNED arms all come from this seed's own warps, because for a
    replication seed there are no pkgA grays for C1/C2 - they are new checkpoints. Only
    PRETRAINED still comes from pkgA, being training-independent.
    """
    import warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    import rasterio
    from scipy.ndimage import sobel

    PKGA = root / "tubitak/data/tool_runs/pkgA/gray"

    def grad_mag(g):
        g = g.astype(float)
        return np.hypot(sobel(g, 0), sobel(g, 1))

    def bt601(rgb):
        return np.round(0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]).astype(np.uint8)

    def read1(p):
        with rasterio.open(p) as s:
            a = s.read()
        return a[0] if a.shape[0] == 1 else bt601(a)

    srcs = {"pretrained": lambda st: PKGA / f"ank130/pretrained/bt601/{st}.tif"}
    for arm in FINE_TUNED:
        srcs[arm] = (lambda a: (lambda st: out / f"warp/{a}/{st}.tif"))(arm)

    rows, skipped = [], []
    for st in stems:
        with rasterio.open(out / f"warp/input/{st}.tif") as s:
            mask = grad_mag(bt601(s.read())) <= EDGE_THRESH
        r = read1(PKGA / f"ref_ank/bt601/{st}.tif")
        r_edge = float((grad_mag(r)[mask] > EDGE_THRESH).mean()) if mask.any() else 0.0
        if not mask.any() or r_edge == 0.0:
            skipped.append(st)
            continue
        row = {"stem": st, "silent_frac": float(mask.mean()), "ref_edge": r_edge}
        for arm, pf in srcs.items():
            f = read1(pf(st))
            row[arm] = float((grad_mag(f)[mask] > EDGE_THRESH).mean()) / r_edge
        rows.append(row)
    df = pd.DataFrame(rows)
    df.to_csv(out / "C45_edge_ratio.csv", index=False)
    print(f"  edge ratio: {len(df)} chips, skipped {skipped}", flush=True)


# ----------------------------------------------------------------------------- step 5
def step_score(root, out, stems):
    """c45_score.py formula verbatim: per-chip statistic = median hypot(dx, dy) over the KLT
    rows. Column names match the committed C45_per_chip.csv exactly, so seed_analysis.py
    reads either without a special case. PRETRAINED comes from B1_per_chip.csv - it is
    training-independent (see module docstring)."""
    b1 = pd.read_csv(root / "tubitak/data/tool_runs/B1/B1_per_chip.csv").set_index("stem")

    def med_n(arm, st):
        cs = glob.glob(str(out / "karios" / arm / st / "*" / "KLT_matcher_*.csv"))
        if not cs:
            return np.nan, 0
        d = pd.read_csv(cs[0], sep=None, engine="python")
        if not len(d):
            return np.nan, 0
        return float(np.median(np.hypot(d.dx, d.dy))), len(d)

    rows = []
    for st in stems:
        r = {"stem": st,
             "pre_med": float(b1.loc[st, "pre_med"]), "pre_n": int(b1.loc[st, "pre_n"])}
        for arm in FINE_TUNED:
            m, n = med_n(arm, st)
            r[f"{arm}_med"], r[f"{arm}_n"] = m, n
        rows.append(r)
    cols = ["stem", "pre_med", "pre_n"] + [f"{a}_{k}" for a in FINE_TUNED for k in ("med", "n")]
    pd.DataFrame(rows)[cols].to_csv(out / "C45_per_chip.csv", index=False)
    print(f"  scored {len(rows)} chips -> {out/'C45_per_chip.csv'}", flush=True)


# ----------------------------------------------------------------------------- gate
def reproduce_gate(root, out):
    """Diff this runner's seed-42 output against the committed C45 files, per column."""
    ref = root / "tubitak/data/tool_runs/C45"
    print("\n" + "=" * 88)
    print("REPRODUCTION GATE - this runner's seed-42 output vs the committed C45 files")
    print("=" * 88)
    ok = True
    for name, keycol in (("C45_per_chip.csv", "stem"), ("C45_edge_ratio.csv", "stem")):
        a = pd.read_csv(out / name).set_index(keycol).sort_index()
        b = pd.read_csv(ref / name).set_index(keycol).sort_index()
        print(f"\n{name}")
        print(f"   committed sha256 {sha256(ref/name)}")
        print(f"   produced  sha256 {sha256(out/name)}")
        print(f"   rows {len(a)} vs {len(b)}; index identical: {a.index.equals(b.index)}")
        shared = [c for c in b.columns if c in a.columns]
        missing = [c for c in b.columns if c not in a.columns]
        if missing:
            print(f"   columns in committed but not produced: {missing}")
        for c in shared:
            x, y = pd.to_numeric(a[c], errors="coerce"), pd.to_numeric(b[c], errors="coerce")
            d = (x - y).abs()
            n_exact = int((d == 0).sum())
            print(f"   {c:14} max|diff| {d.max():.3e}   exact {n_exact}/{len(d)}   "
                  f"agree@1e-9 {int((d <= 1e-9).sum())}/{len(d)}   "
                  f"agree@1e-6 {int((d <= 1e-6).sum())}/{len(d)}")
            if d.max() > 1e-9:
                ok = False
    print("\n" + ("GATE PASSED - every shared column reproduces to 1e-9"
                  if ok else
                  "GATE NOT PASSED - see the per-column table above; do not proceed"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--root", default=None)
    ap.add_argument("--reproduce", action="store_true",
                    help="seed 42 only: write to C45_s42_repro and diff against committed C45")
    args = ap.parse_args()

    root = Path(args.root).resolve() if args.root else DEFAULT_ROOT
    runs = root / "tubitak/data/tool_runs"
    out = runs / ("C45_s42_repro" if args.reproduce else f"C45_s{args.seed}")
    if args.reproduce and args.seed != 42:
        raise SystemExit("--reproduce is the seed-42 gate")
    out.mkdir(parents=True, exist_ok=True)

    stems = sorted(p.name[:-4] for p in (root / "tubitak/data/ankara/run/inputs").glob("*.png"))
    assert len(stems) == 130, f"expected 130 chips, found {len(stems)}"

    print(f"seed {args.seed} -> {out}   arms {FINE_TUNED} (pretrained from B1_per_chip.csv)")
    print(f"inference shim pinned to seed 42 (AMENDMENT SEED-a)\n")
    print("step 1/5 inference");   step_infer(root, out, args.seed)
    print("step 2/5 warp");        step_warp(root, out, stems)
    print("step 3/5 KARIOS");      step_karios(root, out, stems)
    print("step 4/5 edge ratio");  step_edge(root, out, stems)
    print("step 5/5 score");       step_score(root, out, stems)

    for f in ("C45_per_chip.csv", "C45_edge_ratio.csv"):
        print(f"sha256 {f}: {sha256(out/f)}")

    if args.reproduce:
        sys.exit(0 if reproduce_gate(root, out) else 1)


if __name__ == "__main__":
    main()
