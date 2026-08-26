#!/usr/bin/env python
"""Gate D, stage 3 — score the arms against the registered bands.

Convention (project-wide): Delta = candidate - baseline, NEGATIVE = candidate better.
Bands: |paired mean Delta| <= 0.05 px indistinguishable; > 0.15 px materially different.

Control first. `det_onnx` must reproduce Registration A's recorded `det` numbers. If the
control fails, the reconstructed harness is wrong and nothing else here can be trusted.
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
GATE = ROOT / "tubitak/data/plugin_gates/gate_d"
REGA = ROOT / "tubitak/docs/evidence/regA/regA_per_chip.csv"

ARM_KEY = {"C3": "C3", "C2": "C2"}
IND_BAND, MAT_BAND = 0.05, 0.15


def paired(a: pd.Series, b: pd.Series):
    """Delta = a - b over the shared index. Returns mean, sd, se, n, t."""
    idx = a.index.intersection(b.index)
    d = (a.loc[idx] - b.loc[idx]).dropna()
    n = len(d)
    mean, sd = float(d.mean()), float(d.std(ddof=1))
    se = sd / np.sqrt(n) if n > 1 else np.nan
    return dict(mean=mean, sd=sd, se=se, n=n, t=mean / se if se else np.nan)


def band(mean):
    m = abs(mean)
    if m <= IND_BAND:
        return "indistinguishable"
    if m > MAT_BAND:
        return "MATERIALLY DIFFERENT"
    return "documented difference"


def fmt(lbl, r):
    return (f"  {lbl:<42s} {r['mean']:+.4f} +/- {r['sd']:.4f} px  "
            f"(SE {r['se']:.4f}, t={r['t']:+.2f}, n={r['n']})  -> {band(r['mean'])}")


def main():
    new = pd.read_csv(GATE / "gate_d_per_chip.csv")
    rega = pd.read_csv(REGA)

    print("=" * 78)
    print("GATE D — determinism. Delta = candidate - baseline; negative = candidate better")
    print("Inference path is stated for every number. Bands: <=0.05 indistinguishable, "
          ">0.15 material")
    print("=" * 78)

    for arm in ("C3", "C2"):
        key = ARM_KEY[arm]
        seeded = rega[(rega.side == "seeded") & (rega.arm == key)].set_index("stem")["med_resid"]
        det = rega[(rega.side == "det") & (rega.arm == key)].set_index("stem")["med_resid"]
        det_onnx = new[new.cell == f"det_onnx_{arm}"].set_index("stem")["med_resid"]
        evalbn = new[new.cell == f"evalbn_{arm}"].set_index("stem")["med_resid"]

        print(f"\n--- arm {arm} ---")
        print(f"  medians (px): seeded {seeded.median():.4f} | regA det {det.median():.4f} "
              f"| det_onnx {det_onnx.median():.4f} | evalbn {evalbn.median():.4f}")
        print()
        print("  CONTROL — does the reconstructed harness reproduce Registration A?")
        c = paired(det_onnx, det)
        print(fmt("det_onnx - regA det  [CONTROL]", c))
        ok = abs(c["mean"]) <= IND_BAND
        print(f"    control {'OK' if ok else 'FAILED'}: "
              f"{'harness reproduces the recorded path' if ok else 'HARNESS IS NOT THE RECORDED PATH'}")
        print()
        print("  Registration A, recorded (arm 2 vs arm 1), dropout-off vs seeded stochastic:")
        print(fmt("regA det - seeded", paired(det, seeded)))
        print()
        print("  THIS GATE (arm 3), eval-mode BatchNorm + dropout off:")
        print(fmt("evalbn - seeded  [vs evaluated path]", paired(evalbn, seeded)))
        print(fmt("evalbn - regA det  [vs tool default]", paired(evalbn, det)))
        print(fmt("evalbn - det_onnx  [same runtime]", paired(evalbn, det_onnx)))

    print("\n" + "=" * 78)
    print("Point counts (median per chip):")
    for arm in ("C3", "C2"):
        for cell in (f"det_onnx_{arm}", f"evalbn_{arm}"):
            s = new[new.cell == cell]["n_points"]
            print(f"  {cell:<16s} median {s.median():.0f}  min {s.min():.0f}  max {s.max():.0f}")
        for side in ("seeded", "det"):
            s = rega[(rega.side == side) & (rega.arm == ARM_KEY[arm])]["n_points"]
            print(f"  regA {side}_{arm:<10s} median {s.median():.0f}  min {s.min():.0f}  max {s.max():.0f}")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
