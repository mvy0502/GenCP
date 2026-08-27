#!/usr/bin/env python
"""Gate D, stage 2 — score the determinism arms with KARIOS.

Runs in the `karios` conda environment. Same config, same references, same residual
definition (per-point radial = hypot(dx, dy); per-chip statistic = median) as every
previous number in this project.

Checkpointed: an existing result directory with a readable KLT CSV is skipped, so a
respawn resumes rather than restarts (standing practice 7).
"""
from __future__ import annotations
import argparse, glob, subprocess, sys

# Unknown arguments are refused, not ignored: a verifier that runs its default
# and prints PASS when you asked for something else is reporting on the wrong run.
import os.path as _op  # noqa: E402
sys.path.insert(0, _op.join(_op.dirname(_op.abspath(__file__)),
                            *(['..', 'tests'] if _op.basename(
                                _op.dirname(_op.abspath(__file__))) != 'tests'
                              else [])))
from _guard import strict_argv  # noqa: E402
strict_argv(known=(), positional=0)
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
GATE = ROOT / "tubitak/data/plugin_gates/gate_d"
REFARM = ROOT / "tubitak/data/plugin_gates/gate_d/ref"   # warped satellite refs
CONFIG = ROOT / "tubitak/configs/karios_gencp.json"


def klt_csv(res_dir):
    c = glob.glob(str(Path(res_dir) / "*" / "KLT_matcher_*.csv"))
    return c[0] if c else None


def run_one(job):
    cell, stem, mon, ref, res = job
    existing = klt_csv(res)
    if existing is None:
        res.mkdir(parents=True, exist_ok=True)
        subprocess.run(["karios", "process", str(mon), str(ref), "--out", str(res),
                        "--conf", str(CONFIG), "--no-log-file"],
                       capture_output=True, text=True)
        existing = klt_csv(res)
    if existing is None:
        return dict(cell=cell, stem=stem, med_resid=np.nan, n_points=0)
    try:
        d = pd.read_csv(existing, sep=None, engine="python")
    except Exception:
        return dict(cell=cell, stem=stem, med_resid=np.nan, n_points=0)
    if not len(d):
        return dict(cell=cell, stem=stem, med_resid=np.nan, n_points=0)
    radial = np.hypot(d["dx"].to_numpy(float), d["dy"].to_numpy(float))
    return dict(cell=cell, stem=stem, med_resid=float(np.median(radial)),
                n_points=int(len(d)))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--cells", nargs="+",
                    default=["det_onnx_C3", "evalbn_C3", "det_onnx_C2", "evalbn_C2"])
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args(argv)

    jobs = []
    for cell in a.cells:
        wdir = GATE / cell / "warp"
        for mon in sorted(wdir.glob("*.tif")):
            stem = mon.stem
            ref = REFARM / f"{stem}.tif"
            if not ref.exists():
                continue
            jobs.append((cell, stem, mon, ref, GATE / cell / "karios" / stem))
    print(f"Gate D stage 2 — {len(jobs)} KARIOS runs ({len(a.cells)} cells), "
          f"{a.workers} workers")

    rows = []
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        for n, r in enumerate(ex.map(run_one, jobs), 1):
            rows.append(r)
            if n % 20 == 0:
                print(f"  {n}/{len(jobs)}")
    df = pd.DataFrame(rows)
    out = GATE / "gate_d_per_chip.csv"
    df.to_csv(out, index=False)
    print(f"\nwrote {out}")
    print(df.groupby("cell").agg(n=("stem", "size"),
                                 failed=("n_points", lambda s: int((s == 0).sum())),
                                 med=("med_resid", "median")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
