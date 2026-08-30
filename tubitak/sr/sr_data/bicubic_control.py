#!/usr/bin/env python
"""The registered bicubic control — the bar WP3B has to clear.

    degraded 128x128 input  ->  sr_core BicubicUpsampler x2  ->  256x256 prediction
                            compared against the 256x256 target

Computed BEFORE any model exists, so the bar cannot move after a model's numbers are seen.

Domain and convention are the registration's, restated because getting them wrong is silent:
metrics are in NORMALISED REFLECTANCE (`DN / params.NORM_DIVISOR_DN`), each computed PER CHIP
and reported as the UNWEIGHTED MEAN over the chips of a split. The in-distribution `test`
split and the held-out granule `heldout` are reported SEPARATELY and are never pooled.

The upsampler is WP1's, imported read-only. On float32 input it does not clip (sr_core clips
integer dtypes only), so this control carries no clipping decision.
"""
from __future__ import annotations

import json
import sys
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

HERE = Path(__file__).resolve()
SR = HERE.parents[1]
ROOT = HERE.parents[3]
if __package__ in (None, ""):
    sys.path.insert(0, str(SR))
sys.path.insert(0, str(ROOT / "tubitak" / "tests"))
from _guard import strict_argv                                          # noqa: E402

strict_argv(known=("--corpus=", "--splits=", "--json="), positional=0,
            usage="bicubic_control.py [--corpus=DIR] [--splits=test,heldout] [--json=OUT]")

import numpy as np                                                      # noqa: E402

from sr_core.upsample import BicubicUpsampler                           # noqa: E402
from sr_data import params as P                                         # noqa: E402
from sr_data.degrade import degrade_chip                                # noqa: E402
from sr_data.metrics import (mae_chip, psnr_chip, ssim_chip, summarise)  # noqa: E402

CORPUS = ROOT / "tubitak" / "data" / P.CORPUS_SUBDIR


def validate_ssim():
    """The SSIM implementation is validated before its numbers are used.

    No reference implementation is available (scikit-image is not installed and this work
    package installs nothing), so this is weaker than a cross-implementation check and is
    reported as such. It does establish that the function is not a constant.
    """
    rng = np.random.default_rng(P.SPLIT_SEED)
    x = rng.random((3, 64, 64)).astype(np.float32)
    cases = [
        ("identical images -> 1.0", ssim_chip(x, x), lambda v: abs(v - 1.0) < 1e-9),
        ("independent noise -> near 0", ssim_chip(x, rng.random((3, 64, 64)).astype(
            np.float32)), lambda v: v < 0.05),
        ("constant offset +0.1 -> < 1", ssim_chip(x, x + 0.1), lambda v: v < 1.0),
        ("heavy blur -> < 1", ssim_chip(x, np.repeat(np.repeat(
            x[:, ::4, ::4], 4, 1), 4, 2)), lambda v: v < 1.0),
    ]
    print("  SSIM implementation, known cases:")
    ok = True
    for name, v, pred in cases:
        good = bool(pred(v))
        ok &= good
        print(f"    [{'PASS' if good else 'FAIL'}] {name:32s} SSIM = {v:.6f}")
    return ok


def run_split(split, corpus):
    arr = np.load(corpus / f"chips_{split}.npy", mmap_mode="r")
    up = BicubicUpsampler(scale=P.SCALE)
    psnr, ssim, mae = [], [], []
    for i in range(arr.shape[0]):
        lo, hi = degrade_chip(np.asarray(arr[i]), P.NORM_DIVISOR_DN)
        pred = np.moveaxis(up.upsample(np.moveaxis(lo, 0, -1)), -1, 0)
        psnr.append(psnr_chip(pred, hi, P.PSNR_DATA_RANGE))
        ssim.append(ssim_chip(pred, hi, P.PSNR_DATA_RANGE))
        mae.append(mae_chip(pred, hi))
        if (i + 1) % 500 == 0:
            print(f"    {split}: {i + 1}/{arr.shape[0]}", flush=True)
    return dict(n=int(arr.shape[0]), psnr_db=summarise(psnr), ssim=summarise(ssim),
                mae_normalised=summarise(mae))


def main():
    t0 = time.perf_counter()
    corpus, want, out_json = CORPUS, ["test", "heldout", "val"], None
    for a in sys.argv[1:]:
        if a.startswith("--corpus="):
            corpus = Path(a.split("=", 1)[1])
        elif a.startswith("--splits="):
            want = a.split("=", 1)[1].split(",")
        elif a.startswith("--json="):
            out_json = a.split("=", 1)[1]

    import scipy
    print("=" * 84)
    print("WP3A — registered bicubic control (computed before any model exists)")
    print("=" * 84)
    print(f"  corpus     : {corpus}")
    print(f"  domain     : normalised reflectance = DN / {P.NORM_DIVISOR_DN}  "
          f"(= reflectance / {P.NORM_DIVISOR_REFLECTANCE})")
    print(f"  convention : PER CHIP, then unweighted mean over chips. Never pooled.")
    print(f"  PSNR range : {P.PSNR_DATA_RANGE}")
    print(f"  degradation: Gaussian sigma {P.sigma_for_mtf():.9f} src px "
          f"(MTF {P.MTF_AT_NYQUIST} at 20 m Nyquist), then decimate by {P.SCALE}")
    print(f"  numpy {np.__version__} · scipy {scipy.__version__}\n")

    if not validate_ssim():
        print("\n  SSIM validation FAILED - not reporting metrics computed with it.")
        return 2
    print()

    res = {}
    for s in want:
        p = corpus / f"chips_{s}.npy"
        if not p.is_file():
            print(f"  {s}: MISSING {p}")
            return 2
        res[s] = run_split(s, corpus)

    print()
    print(f"  {'split':10s} {'n':>6s} {'PSNR dB':>18s} {'SSIM':>18s} "
          f"{'MAE (normalised)':>22s}")
    for s in want:
        r = res[s]
        print(f"  {s:10s} {r['n']:6d} "
              f"{r['psnr_db']['mean']:10.4f} +/- {r['psnr_db']['std']:5.3f} "
              f"{r['ssim']['mean']:11.6f} +/- {r['ssim']['std']:5.4f} "
              f"{r['mae_normalised']['mean']:13.8f} +/- {r['mae_normalised']['std']:7.6f}")
    print()
    print("  test    = in-distribution blocks of the four April granules")
    print(f"  heldout = {P.HELDOUT_GRANULE}, whole granule, different datatake and landform")
    print("  val     = supplementary, not a registered bar")
    print("  These are reported separately and are NEVER pooled.")
    print(f"\n  wall clock {time.perf_counter() - t0:.1f} s")

    if out_json:
        Path(out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(out_json).write_text(json.dumps(dict(
            results=res, norm_divisor_dn=P.NORM_DIVISOR_DN,
            psnr_data_range=P.PSNR_DATA_RANGE,
            sigma_source_px=P.sigma_for_mtf(), mtf_at_nyquist=P.MTF_AT_NYQUIST,
            convention="per chip, unweighted mean over chips; never pooled",
            domain="normalised reflectance = DN / 5000",
            versions=dict(numpy=np.__version__, scipy=scipy.__version__),
            wall_clock_s=time.perf_counter() - t0), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
