#!/usr/bin/env python
"""WP8 checks M1-M5, registered in `08-eslestirme.md` section 8. Run BEFORE any arm result."""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pipeline as P                                                    # noqa: E402
from scipy.ndimage import shift as ndshift                              # noqa: E402

R = []
def rec(name, kind, ok, detail):
    R.append(ok); print(f"    [{'PASS' if ok else 'FAIL'}] {name:4s} {kind:12s} {detail}")
    return ok

CH = np.load("tubitak/data/sr_wald_corpus_x4/chips_heldout.npy", mmap_mode="r")

def plane(i):
    return np.asarray(CH[i][P.BAND], np.float32)

def u8(a, ref):
    lo, hi = float(ref.min()), float(ref.max())
    return P.to_uint8_fixed(a, lo, hi)

# ---------------------------------------------------------------------------------- M1
print("  M1  the pipeline recovers a planted translation (tolerance 0.25 px both axes)")
PLANTED = (3.25, -2.75)          # (dy, dx): integer part plus a sub-pixel part
for idx in (0, 17, 101, 500):
    ref = plane(idx)
    moved = ndshift(ref, PLANTED, order=3, mode="reflect")
    m = P.match(u8(moved, ref), u8(ref, ref))
    # detection on the arm (the shifted image), tracked into the reference: the recovered
    # displacement is arm -> ref, i.e. the NEGATIVE of the shift applied to make the arm.
    got = (-m["dy"], -m["dx"])
    err = (abs(got[0] - PLANTED[0]), abs(got[1] - PLANTED[1]))
    rec("M1", "known-true", max(err) < 0.25,
        f"chip {idx:4d}: planted (dy,dx)=({PLANTED[0]:+.2f},{PLANTED[1]:+.2f}) "
        f"recovered ({got[0]:+.4f},{got[1]:+.4f}) err ({err[0]:.4f},{err[1]:.4f}) "
        f"from {m['n_inliers']} inliers")

# ---------------------------------------------------------------------------------- M2
print("\n  M2  unrelated ground: the inlier count must collapse")
ref0 = plane(0)
same = P.match(u8(ref0, ref0), u8(ref0, ref0))
for other in (700, 1200):
    o = plane(other)
    m = P.match(u8(o, ref0), u8(ref0, ref0))
    rec("M2", "known-false", m["n_inliers"] < 0.10 * max(same["n_inliers"], 1),
        f"chip {other} vs chip 0: {m['n_inliers']} inliers against {same['n_inliers']} "
        f"for the SAME chip ({100*m['n_inliers']/max(same['n_inliers'],1):.1f} % of it)")

# ---------------------------------------------------------------------------------- M3/M4
print("\n  M3/M4  degenerate images")
z = np.zeros((256, 256), np.float32)
m = P.match(u8(z, ref0), u8(ref0, ref0))
rec("M3", "degenerate", m["n_keypoints"] == 0,
    f"all-zero arm image -> {m['n_keypoints']} keypoints, {m['n_inliers']} inliers")
c = np.full((256, 256), 1234.0, np.float32)
m = P.match(u8(c, ref0), u8(ref0, ref0))
rec("M4", "degenerate", m["n_keypoints"] == 0,
    f"single-colour arm image -> {m['n_keypoints']} keypoints, {m['n_inliers']} inliers")
m = P.match(u8(ref0, ref0), u8(z, ref0))
rec("M4", "degenerate", m["n_inliers"] == 0,
    f"real arm against an all-zero REFERENCE -> {m['n_inliers']} inliers")

# ---------------------------------------------------------------------------------- M5
print("\n  M5  missing file")
try:
    np.load("tubitak/data/sr_wald_corpus_x4/does_not_exist.npy")
    rec("M5", "degenerate", False, "a missing corpus file was LOADED - impossible")
except FileNotFoundError as e:
    rec("M5", "degenerate", True, f"missing corpus file raises FileNotFoundError, not silence")
try:
    import onnxruntime as ort
    ort.InferenceSession("tubitak/data/plugin_models/no_such_model.onnx",
                         providers=["CPUExecutionProvider"])
    rec("M5", "degenerate", False, "a missing ONNX model was LOADED - impossible")
except Exception as e:
    rec("M5", "degenerate", True, f"missing ONNX model raises {type(e).__name__}")

print("\n" + "=" * 78)
print(f"  {'ALL CHECKS BEHAVED AS REGISTERED' if all(R) else 'A CHECK DID NOT BEHAVE AS REGISTERED'}"
      f"  ({sum(R)}/{len(R)} cases)")
sys.exit(0 if all(R) else 1)
