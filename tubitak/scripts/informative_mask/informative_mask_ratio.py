#!/usr/bin/env python
"""Edge-density ratio on the INFORMATIVE mask (Sobel(input) > 20).

Registration: tubitak/docs/informative-mask-registration.md @ c158a7b, committed BEFORE any
number below was computed. Identical to c45_edge_ratio.py except that the mask is the
COMPLEMENT: the registered reading uses Sobel(warped input render) <= 20 (input-silent);
this uses > 20 (input asserts structure). Operator, chips, denominator and per-arm mean
are unchanged.
"""
import csv, json, os
import numpy as np, rasterio
from scipy.ndimage import sobel

ROOT = "/Users/vedat/Documents/GenCP-Generative-Goruntu-Uretimi-OpenStreetMap/"
RUNS = ROOT + "tubitak/data/tool_runs/"
REF  = RUNS + "pkgA/gray/ref_ank/bt601/"
ARMS = ("C1", "C2", "C4", "C5")
SEEDS = (45, 46, 47, 48, 49, 50)


def read1(p):
    with rasterio.open(p) as s:
        return s.read(1).astype(float)


def grad(g):
    return np.hypot(sobel(g, 0), sobel(g, 1))


def bt601(p):
    with rasterio.open(p) as s:
        a = s.read().astype(float)
    if a.shape[0] >= 3:
        return 0.299 * a[0] + 0.587 * a[1] + 0.114 * a[2]
    return a[0]


def main():
    stems = sorted(p[:-4] for p in os.listdir(RUNS + "C45_s45_modal/warp/input") if p.endswith(".tif"))
    out = {}
    for seed in SEEDS:
        C45 = f"{RUNS}C45_s{seed}_modal/"
        rows, skipped = [], []
        for st in stems:
            mask = grad(bt601(f"{C45}warp/input/{st}.tif")) > 20          # COMPLEMENT
            if mask.sum() == 0:
                skipped.append(st); continue
            r_edge = float((grad(read1(REF + st + ".tif"))[mask] > 20).mean())
            if r_edge == 0:
                skipped.append(st); continue
            row = {"stem": st, "informative_frac": float(mask.mean()), "ref_edge": r_edge}
            for a in ARMS:
                f_edge = float((grad(bt601(f"{C45}warp/{a}/{st}.tif"))[mask] > 20).mean())
                row[a] = f_edge / r_edge
            rows.append(row)
        means = {a: float(np.mean([r[a] for r in rows])) for a in ARMS}
        out[seed] = {"n_chips": len(rows), "skipped": skipped, "arm_mean": means,
                     "arm_median": {a: float(np.median([r[a] for r in rows])) for a in ARMS}}
        with open(f"{ROOT}tubitak/docs/evidence/informative_mask/s{seed}_informative_per_chip.csv", "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=["stem", "informative_frac", "ref_edge"] + list(ARMS))
            w.writeheader(); w.writerows(rows)
        print(f"seed {seed}: n={len(rows)} skipped={len(skipped)} "
              + "  ".join(f"{a}={means[a]:.4f}" for a in ARMS), flush=True)
    json.dump(out, open(f"{ROOT}tubitak/docs/evidence/informative_mask/informative_mask.json", "w"), indent=1)


if __name__ == "__main__":
    main()
