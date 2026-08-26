#!/usr/bin/env python
"""Run KARIOS over the three arms and collect per-chip, per-point results.

Runs in the `karios` conda environment via subprocess so the `gencp` environment
is never involved. Writes one tidy CSV of every surviving key point across all
arms and chips, plus a per-chip summary.

Usage
-----
    conda activate karios
    python tubitak/scripts/run_karios_arms.py --arms A B C
"""
from __future__ import annotations

import argparse
import glob
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
KDIR = ROOT / "tubitak" / "data" / "karios"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--arms", nargs="+", default=["A", "B", "C"])
    ap.add_argument("--config", default=str(ROOT / "tubitak/configs/karios_gencp.json"))
    ap.add_argument("--arms-dir", default=str(KDIR / "arms"))
    ap.add_argument("--out", default=str(KDIR / "results"))
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()

    arms_dir, out = Path(a.arms_dir), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    stems = sorted(f.stem for f in (arms_dir / "ref").glob("*.tif"))
    if a.limit:
        stems = stems[:a.limit]
    print(f"{len(stems)} chips x {len(a.arms)} arms = {len(stems)*len(a.arms)} KARIOS runs\n")

    rows, summary = [], []
    for arm in a.arms:
        ok = fail = 0
        for i, st in enumerate(stems):
            mon = arms_dir / arm / f"{st}.tif"
            ref = arms_dir / "ref" / f"{st}.tif"
            res = out / arm / st
            if not mon.exists():
                continue
            cmd = ["karios", "process", str(mon), str(ref), "--out", str(res),
                   "--conf", a.config, "--no-log-file"]
            p = subprocess.run(cmd, capture_output=True, text=True)
            csvs = glob.glob(str(res / "*" / "KLT_matcher_*.csv"))
            n = 0
            if csvs:
                try:
                    d = pd.read_csv(csvs[0], sep=None, engine="python")
                    n = len(d)
                    if n:
                        d = d.assign(arm=arm, stem=st)
                        rows.append(d[["arm", "stem", "x0", "y0", "dx", "dy", "score"]])
                except Exception as e:
                    print(f"  {arm}/{st}: CSV unreadable ({e})")
            if n:
                ok += 1
            else:
                fail += 1
            summary.append(dict(arm=arm, stem=st, n_points=n,
                                returncode=p.returncode))
            if (i + 1) % 15 == 0:
                print(f"  arm {arm}: {i+1}/{len(stems)}")
        print(f"arm {arm}: {ok} chips with points, {fail} with none")

    if not rows:
        sys.exit("no key points collected from any run")
    pts = pd.concat(rows, ignore_index=True)
    pts.to_csv(out / "all_points.csv", index=False)
    pd.DataFrame(summary).to_csv(out / "per_chip_summary.csv", index=False)
    print(f"\nwrote {len(pts)} key points -> {out/'all_points.csv'}")
    print(f"wrote per-chip summary -> {out/'per_chip_summary.csv'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
