#!/usr/bin/env python3
"""CLI for the MODEL path - the reference the plugin's output is compared against.

Uses the same `sr_core.run.superresolve` and the same `sr_plugin.onnx_upsample.OnnxUpsampler`
the plugin uses, so "the plugin and the CLI agree" is a statement about one implementation
run two ways, not two implementations that happen to agree.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

SR = Path(__file__).resolve().parents[1]
if str(SR) not in sys.path:
    sys.path.insert(0, str(SR))

from sr_core.run import superresolve                                    # noqa: E402
from sr_plugin.onnx_upsample import (OnnxUpsampler, read_provenance,    # noqa: E402
                                     validate_input)
from sr_train import config as C                                        # noqa: E402


def main():
    ap = argparse.ArgumentParser(prog="run_model.py")
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--model", default=None)
    ap.add_argument("--tile-px", type=int, default=None,
                    help="input tile in SOURCE px; default = the model's declared tile")
    ap.add_argument("--overlap-px", type=int, default=None)
    ap.add_argument("--window", type=int, nargs=4, default=None,
                    metavar=("COL0", "ROW0", "W", "H"))
    ap.add_argument("--no-validate", action="store_true",
                    help="skip the input assertion (for deliberately testing a refusal)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    model = Path(a.model or (C.data_root() / "sr_models" / "gencp_sr_x2_v1.onnx"))
    if not model.is_file():
        raise SystemExit(f"run_model: model not found: {model}")
    if not Path(a.input).is_file():
        raise SystemExit(f"run_model: input not found: {a.input}")

    sess, prov = read_provenance(model)
    if not a.no_validate:
        validate_input(a.input, prov)
    up = OnnxUpsampler(model, sess=sess, prov=prov, clip=True)
    tile = a.tile_px or int(prov["infer_tile_src_px"])
    ovl = a.overlap_px if a.overlap_px is not None else int(prov["infer_overlap_src_px"])

    t0 = time.perf_counter()
    rec = superresolve(a.input, a.output, scale=int(prov["scale"]),
                       tile_px=tile, overlap_px=ovl, window=a.window,
                       upsampler=up, progress=None)
    rec["tile_px_used"] = tile
    rec["overlap_px_used"] = ovl
    rec["model"] = str(model)
    rec["outer_wall_clock_s"] = time.perf_counter() - t0
    if a.json:
        print(json.dumps({k: v for k, v in rec.items() if k != "provenance"},
                         indent=2, default=str))
    else:
        print(f"{rec['method']}  tile {tile} ovl {ovl}  {rec['n_tiles']} tiles  "
              f"{rec['wall_clock_s']:.1f} s  {rec['output_size_bytes']/1e6:.1f} MB  "
              f"-> {rec['output']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
