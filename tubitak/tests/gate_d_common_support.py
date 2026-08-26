#!/usr/bin/env python
"""Gate D on common support — Item C.

Registered in tubitak/docs/plugin-gate-registration-C.md before this ran.

Both arms' rasters share one 228x228 grid and transform, so KLT (x0, y0) are directly
comparable. Points are paired by mutual nearest neighbour within a fixed tolerance,
one-to-one, and each arm's median radial error is recomputed on the pairs only.

Convention: Delta = candidate - baseline; negative = candidate better.
Candidate = evalbn (running-statistic BatchNorm). Baseline = det_onnx (batch-statistic).
"""
from __future__ import annotations
import glob, json, sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
GATE = ROOT / "tubitak/data/plugin_gates/gate_d"
TOLERANCES = [1.0, 0.5, 2.0]      # 1.0 is the registered primary
MIN_COMMON = 5
IND_BAND, MAT_BAND = 0.05, 0.15


def load_points(cell, stem):
    c = glob.glob(str(GATE / cell / "karios" / stem / "*" / "KLT_matcher_*.csv"))
    if not c:
        return None
    d = pd.read_csv(c[0], sep=None, engine="python")
    if not len(d):
        return None
    return pd.DataFrame(dict(
        x0=d["x0"].to_numpy(float), y0=d["y0"].to_numpy(float),
        r=np.hypot(d["dx"].to_numpy(float), d["dy"].to_numpy(float))))


def mutual_nn_pairs(A, B, tol):
    """One-to-one pairing by mutual nearest neighbour, greedy in ascending distance."""
    if A is None or B is None or not len(A) or not len(B):
        return np.array([], int), np.array([], int)
    pa = A[["x0", "y0"]].to_numpy()
    pb = B[["x0", "y0"]].to_numpy()
    d = np.sqrt(((pa[:, None, :] - pb[None, :, :]) ** 2).sum(-1))
    cand = np.argwhere(d <= tol)
    if not len(cand):
        return np.array([], int), np.array([], int)
    order = np.argsort(d[cand[:, 0], cand[:, 1]], kind="stable")
    used_a, used_b, ia, ib = set(), set(), [], []
    for k in order:
        i, j = cand[k]
        if i in used_a or j in used_b:
            continue
        used_a.add(i); used_b.add(j); ia.append(i); ib.append(j)
    return np.array(ia, int), np.array(ib, int)


def paired(x, y):
    d = np.asarray(x, float) - np.asarray(y, float)
    d = d[np.isfinite(d)]
    n = len(d)
    mean, sd = float(d.mean()), float(d.std(ddof=1)) if n > 1 else (float(d.mean()), np.nan)
    se = sd / np.sqrt(n) if n > 1 else np.nan
    return dict(mean=mean, sd=sd, se=se, n=n, t=mean / se if se else np.nan)


def band(m):
    a = abs(m)
    return "indistinguishable" if a <= IND_BAND else (
        "MATERIALLY DIFFERENT" if a > MAT_BAND else "documented difference")


def main():
    stems = sorted(p.stem for p in (GATE / "ref").glob("*.tif"))
    out = {}
    print("Gate D on COMMON SUPPORT — Item C")
    print("  Delta = evalbn - det_onnx ; negative = evalbn better")
    print("  baseline  det_onnx = dropout off, BatchNorm BATCH statistics (deployed)")
    print("  candidate evalbn   = dropout off, BatchNorm RUNNING statistics\n")

    for arm in ("C3", "C2"):
        base_cell, cand_cell = f"det_onnx_{arm}", f"evalbn_{arm}"
        print(f"{'='*74}\narm {arm}\n{'='*74}")
        for tol in TOLERANCES:
            rows, dropped_stats = [], []
            excluded = []
            for st in stems:
                A = load_points(base_cell, st)
                B = load_points(cand_cell, st)
                if A is None or B is None:
                    excluded.append((st, "missing points"))
                    continue
                ia, ib = mutual_nn_pairs(A, B, tol)
                if len(ia) < MIN_COMMON:
                    excluded.append((st, f"only {len(ia)} common"))
                    continue
                base_common = float(np.median(A.r.to_numpy()[ia]))
                cand_common = float(np.median(B.r.to_numpy()[ib]))
                # secondary: points the candidate DROPPED, scored in the baseline arm
                mask = np.ones(len(A), bool); mask[ia] = False
                dropped = A.r.to_numpy()[mask]
                if len(dropped) >= MIN_COMMON:
                    dropped_stats.append((float(np.median(dropped)), base_common))
                rows.append(dict(stem=st, n_common=len(ia),
                                 n_base=len(A), n_cand=len(B),
                                 base_common=base_common, cand_common=cand_common,
                                 base_full=float(np.median(A.r)),
                                 cand_full=float(np.median(B.r))))
            df = pd.DataFrame(rows)
            pc = paired(df.cand_common, df.base_common)
            pf = paired(df.cand_full, df.base_full)
            tag = "  (registered primary)" if tol == 1.0 else ""
            print(f"\n-- tolerance {tol} px{tag} --")
            print(f"   chips used {len(df)}/{len(stems)}"
                  + (f"   excluded: {len(excluded)}" if excluded else ""))
            print(f"   n_common per chip: median {df.n_common.median():.0f}  "
                  f"min {df.n_common.min()}  max {df.n_common.max()}  "
                  f"total {int(df.n_common.sum())}")
            print(f"   points available : baseline median {df.n_base.median():.0f}, "
                  f"candidate median {df.n_cand.median():.0f}")
            print(f"   median error on COMMON set: baseline {df.base_common.median():.4f} px, "
                  f"candidate {df.cand_common.median():.4f} px")
            print(f"   median error on FULL   set: baseline {df.base_full.median():.4f} px, "
                  f"candidate {df.cand_full.median():.4f} px")
            print(f"   Delta COMMON : {pc['mean']:+.4f} +/- {pc['sd']:.4f} px  "
                  f"(SE {pc['se']:.4f}, t={pc['t']:+.2f}, n={pc['n']})  -> {band(pc['mean'])}")
            print(f"   Delta FULL   : {pf['mean']:+.4f} +/- {pf['sd']:.4f} px  "
                  f"(SE {pf['se']:.4f}, t={pf['t']:+.2f}, n={pf['n']})  -> {band(pf['mean'])}")
            shrank = abs(pc["mean"]) < abs(pf["mean"])
            print(f"   |Delta| shrank on common support: {shrank}")
            if tol == 1.0 and dropped_stats:
                dr = np.array(dropped_stats)
                dd = paired(dr[:, 0], dr[:, 1])
                print(f"   SECONDARY — points the candidate DROPPED, scored in the "
                      f"baseline arm:")
                print(f"      median error of dropped points {np.median(dr[:,0]):.4f} px "
                      f"vs surviving {np.median(dr[:,1]):.4f} px")
                print(f"      paired (dropped - surviving): {dd['mean']:+.4f} +/- "
                      f"{dd['sd']:.4f} px (SE {dd['se']:.4f}, t={dd['t']:+.2f}, "
                      f"n={dd['n']})")
                out[f"{arm}_secondary"] = dd
            out[f"{arm}_tol{tol}"] = dict(common=pc, full=pf, chips=len(df),
                                          n_common_total=int(df.n_common.sum()))
            if tol == 1.0:
                df.to_csv(GATE / f"common_support_{arm}.csv", index=False)
    (GATE / "common_support_results.json").write_text(json.dumps(out, indent=2, default=str))
    print(f"\nwrote {GATE/'common_support_results.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
