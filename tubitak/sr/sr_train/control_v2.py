#!/usr/bin/env python3
"""The bicubic control, recomputed on the CORRECTED split.

Same code path as WP3A's `sr_data/bicubic_control.py`, same conventions, same imported
upsampler and degradation; only the chip membership differs. The WP3A numbers are retained
in the report and relabelled, not replaced.
"""
from __future__ import annotations

import json
import sys
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

SR = Path(__file__).resolve().parents[1]
ROOT = SR.parents[1]
for p in (str(SR), str(ROOT / "tubitak" / "tests")):
    if p not in sys.path:
        sys.path.insert(0, p)

from _guard import strict_argv                                          # noqa: E402
strict_argv(known=("--splits=", "--json="), positional=0,
            usage="control_v2.py [--splits=test,heldout,val] [--json=OUT]")

import numpy as np                                                      # noqa: E402

from sr_core.upsample import BicubicUpsampler                           # noqa: E402
from sr_data import params as P                                         # noqa: E402
from sr_data.degrade import degrade_chip                                # noqa: E402
from sr_data.metrics import mae_chip, psnr_chip, ssim_chip, summarise   # noqa: E402
from sr_train import config as C, data as D                             # noqa: E402


def run_split(split):
    chips, recs = D.load_split(split)
    div = D.assert_norm_divisor(P.NORM_DIVISOR_DN)
    up = BicubicUpsampler(scale=P.SCALE)
    psnr, ssim, mae = [], [], []
    for i in range(chips.shape[0]):
        lo, hi = degrade_chip(chips[i], div)
        pred = np.moveaxis(up.upsample(np.moveaxis(lo, 0, -1)), -1, 0)
        psnr.append(psnr_chip(pred, hi, P.PSNR_DATA_RANGE))
        ssim.append(ssim_chip(pred, hi, P.PSNR_DATA_RANGE))
        mae.append(mae_chip(pred, hi))
    return dict(n=len(psnr), psnr=summarise(psnr), ssim=summarise(ssim), mae=summarise(mae),
                per_chip=dict(psnr=[float(v) for v in psnr],
                              ssim=[float(v) for v in ssim],
                              mae=[float(v) for v in mae]))


def main():
    argv = sys.argv[1:]
    splits = ["test", "heldout", "val"]
    out = C.data_root() / C.SPLIT_SUBDIR / "bicubic_control_v2.json"
    for a in argv:
        if a.startswith("--splits="):
            splits = a.split("=", 1)[1].split(",")
        if a.startswith("--json="):
            out = Path(a.split("=", 1)[1])
    t0 = time.perf_counter()
    res = {}
    print("bicubic control on the CORRECTED split")
    print(f"  domain normalised reflectance DN/{P.NORM_DIVISOR_DN:.0f}, per chip, "
          f"unweighted mean over chips, PSNR range {P.PSNR_DATA_RANGE}")
    for s in splits:
        res[s] = run_split(s)
        r = res[s]
        print(f"  {s:8s} n={r['n']:5d}  PSNR {r['psnr']['mean']:8.4f} +- "
              f"{r['psnr']['std']:.3f}   SSIM {r['ssim']['mean']:.6f} +- "
              f"{r['ssim']['std']:.4f}   MAE {r['mae']['mean']:.8f} +- {r['mae']['std']:.6f}")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(dict(
        work_package="P2-WP3B", split="v2-corrected",
        norm_divisor_dn=P.NORM_DIVISOR_DN, psnr_data_range=P.PSNR_DATA_RANGE,
        convention="per chip, unweighted mean over chips, never pooled",
        wall_clock_s=time.perf_counter() - t0, results=res), indent=2))
    print(f"  wrote {out}  ({time.perf_counter()-t0:.1f} s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
