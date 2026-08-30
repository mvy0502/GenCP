#!/usr/bin/env python
"""WP8: run the four arms over every heldout chip. Registered in `08-eslestirme.md`."""
from __future__ import annotations
import json, sys, time
from pathlib import Path
import numpy as np
import onnxruntime as ort
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pipeline as P

LIMIT = int(sys.argv[1]) if len(sys.argv) > 1 else 0
CH = np.load("tubitak/data/sr_wald_corpus_x4/chips_heldout.npy", mmap_mode="r")
N = LIMIT or CH.shape[0]
so = ort.SessionOptions(); so.intra_op_num_threads = 4
ours = ort.InferenceSession("tubitak/data/plugin_models/gencp_sr_x4_b4.onnx", so,
                            providers=["CPUExecutionProvider"])
ws = ort.InferenceSession("tubitak/data/wp5_reference/models/wsx4_spatrad.onnx", so,
                          providers=["CPUExecutionProvider"])
print(f"  {N} chips, band index {P.BAND} (B04), seed {P.SEED}", flush=True)
res = {a: [] for a in ("oracle", "bicubic", "ours", "wsx4")}
t0 = time.perf_counter()
for i in range(N):
    chip = np.asarray(CH[i], np.uint16)
    ref_plane = np.asarray(chip[P.BAND], np.float32)
    lo, hi = float(ref_plane.min()), float(ref_plane.max())
    ref_u8 = P.to_uint8_fixed(ref_plane, lo, hi)
    d40 = P.degrade_to_40m(chip)
    outs = {"oracle": np.asarray(chip, np.float32),
            "bicubic": P.arm_bicubic(d40),
            "ours": P.arm_onnx_ours(ours, d40),
            "wsx4": P.arm_onnx_wsx4(ws, d40)}
    for arm, y in outs.items():
        m = P.match(P.to_uint8_fixed(y[P.BAND], lo, hi), ref_u8)
        m["chip"] = i
        res[arm].append(m)
    if (i + 1) % 100 == 0 or i + 1 == N:
        el = time.perf_counter() - t0
        print(f"    {i+1}/{N}  {el:6.1f}s  {(i+1)/el:5.2f} chips/s  "
              f"eta {(N-i-1)/((i+1)/el)/60:5.1f} min", flush=True)
out = Path("tubitak/data/sr_match/wp8_arms.json"); out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(dict(
    n_chips=N, band="B04", band_index=P.BAND, seed=P.SEED, split="heldout", granule="36SXJ",
    klt=P.KLT, ransac=dict(thresh_px=P.RANSAC_THRESH_PX, iters=P.RANSAC_ITERS,
                           confidence=P.RANSAC_CONF),
    versions=dict(numpy=np.__version__, cv2=__import__("cv2").__version__,
                  onnxruntime=ort.__version__, python=sys.version.split()[0]),
    wall_clock_s=time.perf_counter() - t0, results=res), indent=2))
print(f"  wrote {out}  ({time.perf_counter()-t0:.0f} s)")
