#!/usr/bin/env python
"""WP12: the WP8 matching experiment, on the TCI corpus and the TCI model.

The detector, the matcher, the parameters, the band and the RANSAC settings are WP8's,
imported unchanged from `pipeline.py`. Only three things differ, and each is a property of
the corpus rather than of the measurement: the chips are TCI (8-bit), the divisor is 255,
and the model is the three-band one. wsx4 and the four-band model have no arm here - they
need four bands and this product has three, so they are out of domain by band count alone.
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path
import numpy as np
import onnxruntime as ort
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pipeline as P

DIV = 255.0                     # WP12 D31, not WP8's 10000
CORPUS = "tubitak/data/sr_wald_corpus_tci"
LIMIT = int(sys.argv[1]) if len(sys.argv) > 1 else 0

sys.path.insert(0, "tubitak/sr")
import os
os.environ["GENCP_SR_VARIANT"] = "tci"
from sr_train import data as D                                          # noqa: E402

chips, recs = D.load_split("heldout")
N = LIMIT or chips.shape[0]
so = ort.SessionOptions(); so.intra_op_num_threads = 4
model = ort.InferenceSession("tubitak/data/plugin_models/gencp_sr_tci_x4_b3.onnx", so,
                             providers=["CPUExecutionProvider"])
print(f"  {N} chips of the TCI heldout split (36SXJ), band index {P.BAND} (B04), "
      f"divisor {DIV:.0f}, seed {P.SEED}", flush=True)
res = {a: [] for a in ("oracle", "bicubic", "tci_model")}
t0 = time.perf_counter()
for i in range(N):
    chip = np.asarray(chips[i], np.float32)          # 3 x 256 x 256, 0..255
    ref_plane = chip[P.BAND]
    lo, hi = float(ref_plane.min()), float(ref_plane.max())
    ref_u8 = P.to_uint8_fixed(ref_plane, lo, hi)
    d40 = P.degrade_to_40m(chip.astype(np.uint16))   # the registered degradation, scale 4
    x = (d40 / np.float32(DIV))[None]
    y = model.run(None, {model.get_inputs()[0].name: x.astype(np.float32)})[0][0] * DIV
    outs = {"oracle": chip, "bicubic": P.arm_bicubic(d40), "tci_model": y.astype(np.float32)}
    for arm, o in outs.items():
        m = P.match(P.to_uint8_fixed(o[P.BAND], lo, hi), ref_u8); m["chip"] = i
        res[arm].append(m)
    if (i + 1) % 100 == 0 or i + 1 == N:
        el = time.perf_counter() - t0
        print(f"    {i+1}/{N}  {el:6.1f}s  {(i+1)/el:5.2f} chips/s", flush=True)
out = Path("tubitak/data/sr_match/wp12_arms_tci.json")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(dict(
    n_chips=N, band="B04", band_index=P.BAND, seed=P.SEED, split="heldout", granule="36SXJ",
    corpus="TCI", divisor=DIV, klt=P.KLT,
    ransac=dict(thresh_px=P.RANSAC_THRESH_PX, iters=P.RANSAC_ITERS, confidence=P.RANSAC_CONF),
    wall_clock_s=time.perf_counter() - t0, results=res), indent=2))
print(f"  wrote {out}")
