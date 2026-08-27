#!/usr/bin/env python
"""Gate D, stage 1 — generate and warp the determinism arms.

Registered in tubitak/docs/plugin-gate-registrations.md before this ran.

Arms produced here (all deterministic, dropout removed):
  det_onnx  ONNX with BatchNorm in BATCH-STATISTICS mode. This is a CONTROL: it must
            reproduce Registration A's recorded `det` numbers. If it does not, the
            reconstructed harness is wrong and the new arm's number means nothing.
  evalbn    ONNX with BatchNorm in RUNNING-STATISTICS mode (`model.eval()`), which is
            what the work package's "eval-mode, dropout off" asks for. This is the arm
            Registration A deliberately did not measure.

Baselines `seeded` and `det` come from Registration A's committed per-chip CSV and are
not re-run.

Warp geometry is Registration A's, reconstructed from the artifacts and asserted against
them: 228x228 at 10 m, inset 145 m from the chip origin, source placed with the corrected
GSD 10.0390625 (2570/256), bilinear.

The KARIOS reference is built HERE, by warping the 257 px satellite reference
tubitak/data/ankara/run/ref/<stem>.tif onto the same 228 grid with its own (nominal 10 m)
transform - exactly what scripts/build_karios_arms.py does for its "ref" arm.

NOTE, recorded because a first run of this gate got it wrong: tubitak/data/ankara/run/arms/
does NOT hold warped references. It holds a warped generated arm. Using it as the reference
made the control fail by -0.44 px. The control exists precisely to catch this, and it did.
"""
from __future__ import annotations
import sys, warnings
from pathlib import Path

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tubitak"))

# Unknown arguments are refused, not ignored: a verifier that runs its default
# and prints PASS when you asked for something else is reporting on the wrong run.
import os.path as _op  # noqa: E402
sys.path.insert(0, _op.join(_op.dirname(_op.abspath(__file__)),
                            *(['..', 'tests'] if _op.basename(
                                _op.dirname(_op.abspath(__file__))) != 'tests'
                              else [])))
from _guard import strict_argv  # noqa: E402
strict_argv(known=(), positional=0)

import numpy as np
import rasterio
from rasterio.transform import Affine
from rasterio.warp import reproject, Resampling
from PIL import Image

from gencp_core import infer

SRC_PX, OUT_PX, NOMINAL = 257, 256, 10.0
TRUE_GSD = SRC_PX * NOMINAL / OUT_PX
GRID_N, INSET_M = 228, 145.0

INPUTS = ROOT / "tubitak/data/tool_runs/task3/inputs"
CHIPS = ROOT / "tubitak/data/ankara/run/ref"          # 257 px satellite reference
MODELS = ROOT / "tubitak/data/plugin_models"
OUT = ROOT / "tubitak/data/plugin_gates/gate_d"

VARIANTS = {
    "det_onnx": "gencp_{arm}_fp32.onnx",
    "evalbn":   "gencp_{arm}_evalbn_fp32.onnx",
}


def build_reference(stem, dst_path):
    """Warp the 257 px satellite reference onto the 228 grid with its own transform."""
    if dst_path.exists():
        return dst_path
    with rasterio.open(CHIPS / f"{stem}.tif") as s:
        T0, crs, arr = s.transform, s.crs, s.read()
    ox, oy = T0.c, T0.f
    target = Affine(NOMINAL, 0, ox + INSET_M, 0, -NOMINAL, oy - INSET_M)
    dst = np.zeros((3, GRID_N, GRID_N), np.uint8)
    for b in range(3):
        reproject(source=arr[b], destination=dst[b], src_transform=T0, src_crs=crs,
                  dst_transform=target, dst_crs=crs, resampling=Resampling.bilinear)
    prof = dict(driver="GTiff", height=GRID_N, width=GRID_N, count=3, dtype="uint8",
                crs=crs, transform=target)
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(dst_path, "w", **prof) as d:
        d.write(dst)
    return dst_path


def warp_to_grid(fake_hwc, origin, crs, dst_path):
    ox, oy = origin
    target = Affine(NOMINAL, 0, ox + INSET_M, 0, -NOMINAL, oy - INSET_M)
    src_T = Affine(TRUE_GSD, 0, ox, 0, -TRUE_GSD, oy)
    src = np.moveaxis(fake_hwc, -1, 0)
    dst = np.zeros((3, GRID_N, GRID_N), np.uint8)
    for b in range(3):
        reproject(source=src[b], destination=dst[b], src_transform=src_T, src_crs=crs,
                  dst_transform=target, dst_crs=crs, resampling=Resampling.bilinear)
    prof = dict(driver="GTiff", height=GRID_N, width=GRID_N, count=3, dtype="uint8",
                crs=crs, transform=target)
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(dst_path, "w", **prof) as d:
        d.write(dst)
    return target


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--arms", nargs="+", default=["C3", "C2"])
    a = ap.parse_args(argv)

    stems = sorted(p.stem for p in INPUTS.glob("*.png"))
    print(f"Gate D stage 1 — {len(stems)} task3 production-input chips, arms {a.arms}")
    print(f"  warp: {GRID_N}x{GRID_N} @ {NOMINAL} m, inset {INSET_M} m, "
          f"source GSD {TRUE_GSD} (corrected)\n")

    # Assert the reconstructed warp geometry against Registration A's own artifact.
    probe = ROOT / "tubitak/data/tool_runs/regA/det_C3/warp" / f"{stems[0]}.tif"
    with rasterio.open(CHIPS / f"{stems[0]}.tif") as s:
        ox, oy, crs0 = s.transform.c, s.transform.f, s.crs
    expect = Affine(NOMINAL, 0, ox + INSET_M, 0, -NOMINAL, oy - INSET_M)
    with rasterio.open(probe) as s:
        assert tuple(s.transform)[:6] == tuple(expect)[:6], (
            f"warp geometry mismatch vs regA artifact:\n  regA {tuple(s.transform)[:6]}"
            f"\n  ours {tuple(expect)[:6]}")
        assert (s.width, s.height) == (GRID_N, GRID_N)
    print(f"warp geometry asserted against regA artifact {probe.name}: MATCH")

    refdir = OUT / "ref"
    for st in stems:
        build_reference(st, refdir / f"{st}.tif")
    print(f"built {len(stems)} warped satellite references -> {refdir}\n")

    for arm in a.arms:
        for vname, pattern in VARIANTS.items():
            mp = MODELS / pattern.format(arm=arm)
            if not mp.is_file():
                print(f"  skip {arm}/{vname}: {mp.name} not exported")
                continue
            model = infer.OnnxGenerator(mp)
            wdir = OUT / f"{vname}_{arm}" / "warp"
            done = 0
            for st in stems:
                dst = wdir / f"{st}.tif"
                if dst.exists():
                    done += 1
                    continue
                with rasterio.open(CHIPS / f"{st}.tif") as s:
                    origin, crs = (s.transform.c, s.transform.f), s.crs
                fake = model.run_path(INPUTS / f"{st}.png")
                warp_to_grid(fake, origin, crs, dst)
                done += 1
                if done % 10 == 0:
                    print(f"  {arm}/{vname}: {done}/{len(stems)}")
            print(f"  {arm}/{vname}: {done}/{len(stems)} warped -> {wdir}")
    print("\nstage 1 complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
