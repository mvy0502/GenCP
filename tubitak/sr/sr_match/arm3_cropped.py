#!/usr/bin/env python
"""WP8 addendum: arm 3 re-run WITH the crop margin wsx4 declares.

The uncropped arm 3 fed a bare 64x64 chip and kept the whole 256x256 output, so wsx4's border
artefacts were inside the matched region. `wsx4_spatrad.yaml` declares margin 130, and
`run.py:326` (margin_in_meters = target_resolution * margin) fixes the unit as OUTPUT pixels:
130 output px = 32.5 source px = 325 m at the model's native scale.

32.5 source px is not an integer, so the window is padded by 33 source px per side, giving a
crop of 132 output px - the smallest integer margin that satisfies the declared 130.

    real 10 m window   520 x 520   ( 256 target + 2 x 132 context )
    degrade  /4        130 x 130
    wsx4     x4        520 x 520
    crop 132/side      256 x 256   <- exactly the chip, matched against the same reference

Context is REAL granule pixels, not padding, so 76 of 1332 chips that lie within 132 px of the
granule edge are excluded and reported rather than given invented context.

Stage A only (gencp env: rasterio + onnxruntime). Matching is stage B, in the karios env, by
the same `pipeline.match` the other arms used.
"""
from __future__ import annotations
import csv, json, sys, time
from pathlib import Path
import numpy as np
import onnxruntime as ort
import rasterio
from rasterio.windows import Window

sys.path.insert(0, "tubitak/sr")
from sr_data import params as P                                  # noqa: E402
from sr_data.degrade import degrade                              # noqa: E402

TARGET, MARGIN_OUT, SCALE = 256, 132, 4
MARGIN_SRC = MARGIN_OUT // SCALE                                 # 33 source px
WIN = TARGET + 2 * MARGIN_OUT                                    # 520
D = Path("tubitak/data") / P.DATA_SUBDIR / P.GRANULES["36SXJ"]["dirname"]
B08 = Path("tubitak/data/s2_b08/B08_36SXJ.tif")

rows = [r for r in csv.DictReader(open("tubitak/data/sr_wald_split_v2/manifest_v2.csv"))
        if r["split"] == "heldout"]
srcs = [rasterio.open(D / "B02.tif"), rasterio.open(D / "B03.tif"),
        rasterio.open(D / "B04.tif"), rasterio.open(B08)]
H, W = srcs[0].height, srcs[0].width
tr = srcs[0].transform
for s in srcs[1:]:                       # D23 again, here, where it is being relied on
    if s.transform != tr or (s.height, s.width) != (H, W):
        raise SystemExit(f"arm3_cropped: {s.name} is not on the B02 grid")

keep = [i for i, r in enumerate(rows)
        if int(r["chip_row"]) * TARGET - MARGIN_OUT >= 0
        and int(r["chip_col"]) * TARGET - MARGIN_OUT >= 0
        and int(r["chip_row"]) * TARGET + TARGET + MARGIN_OUT <= H
        and int(r["chip_col"]) * TARGET + TARGET + MARGIN_OUT <= W]
print(f"  {len(keep)}/{len(rows)} chips have a full {MARGIN_OUT}px REAL context window", flush=True)

so = ort.SessionOptions(); so.intra_op_num_threads = 4
ws = ort.InferenceSession("tubitak/data/wp5_reference/models/wsx4_spatrad.onnx", so,
                          providers=["CPUExecutionProvider"])
out = np.zeros((len(keep), TARGET, TARGET), np.float32)
t0 = time.perf_counter()
for n, i in enumerate(keep):
    r = rows[i]
    r0 = int(r["chip_row"]) * TARGET - MARGIN_OUT
    c0 = int(r["chip_col"]) * TARGET - MARGIN_OUT
    win = Window(c0, r0, WIN, WIN)
    big = np.stack([s.read(1, window=win) for s in srcs]).astype(np.float32)   # (4,520,520) DN
    lo = degrade(big, scale=SCALE).astype(np.float32)                          # (4,130,130) DN
    y = ws.run(None, {ws.get_inputs()[0].name: lo[None]})[0][0]                # (4,520,520) DN
    out[n] = y[2, MARGIN_OUT:MARGIN_OUT + TARGET, MARGIN_OUT:MARGIN_OUT + TARGET]  # B04
    if (n + 1) % 100 == 0 or n + 1 == len(keep):
        el = time.perf_counter() - t0
        print(f"    {n+1}/{len(keep)}  {el:6.1f}s  eta {(len(keep)-n-1)/((n+1)/el)/60:4.1f} min",
              flush=True)
o = Path("tubitak/data/sr_match"); o.mkdir(parents=True, exist_ok=True)
np.save(o / "arm3_cropped_b04.npy", out)
(o / "arm3_cropped_meta.json").write_text(json.dumps(dict(
    kept_chip_indices=keep, n_kept=len(keep), n_total=len(rows),
    margin_out_px=MARGIN_OUT, margin_src_px=MARGIN_SRC, declared_margin_out_px=130,
    window_px=WIN, wall_clock_s=time.perf_counter() - t0), indent=2))
print(f"  wrote {o/'arm3_cropped_b04.npy'}  ({time.perf_counter()-t0:.0f} s)")
