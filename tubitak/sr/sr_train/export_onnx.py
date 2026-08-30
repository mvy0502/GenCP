#!/usr/bin/env python3
"""Part D — D17. Export with DYNAMIC spatial axes and verify against PyTorch.

WP1 open item 2 measured that a static-shape graph rejects a source smaller than one tile in
an axis, so height and width are dynamic. The graph is then RUN at 128 (the training size),
at 96, and at 100 (not a multiple of eight) and compared with PyTorch on the same inputs.

The provenance WP4 needs travels INSIDE the file, in ONNX `metadata_props`, not in someone's
memory: the normalisation constant, the scale factor, the input channel count and the corpus
registration this model was trained against.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import torch

SR = Path(__file__).resolve().parents[1]
if str(SR) not in sys.path:
    sys.path.insert(0, str(SR))

from sr_data import params as P                                         # noqa: E402
from sr_train import config as C                                        # noqa: E402
from sr_train.model import SRNet, receptive_field                       # noqa: E402

OPSET = 17


def training_record(ck_path):
    """The run as it ACTUALLY went, read from train_record.json beside the checkpoint.

    A model stopped early is a different model, not a noisier version of the same one, so
    the completed step count travels with the weights rather than living only in a report.
    """
    f = Path(ck_path).parent / "train_record.json"
    if not f.is_file():
        return {}
    return json.loads(f.read_text())


def provenance(ck_path, ck, schedule_steps, rec):
    stop = rec.get("stop_reason", "unknown")
    return {
        "gencp_sr_model": "1",
        "work_package": "P2-WP3B",
        "corpus_registration": "tubitak/sr/docs/03a-corpus-registration.md",
        "split_registration": "tubitak/sr/docs/03b-registration.md",
        "corpus_id": "sr_wald_corpus + sr_wald_split_v2 (D13 corrected split)",
        # --- what an inference caller MUST apply, in words, not by convention ---
        "input_normalisation": f"normalised = DN / {P.NORM_DIVISOR_DN:.1f}",
        "norm_divisor_dn": f"{P.NORM_DIVISOR_DN:.1f}",
        "dn_to_reflectance": f"{P.DN_TO_REFLECTANCE!r}",
        "boa_offset_applied": f"{P.BOA_OFFSET_APPLIED!r}",
        "scale_factor": str(P.SCALE),
        "in_channels": "3",
        "band_order": ",".join(P.BANDS),
        "input_layout": "NCHW float32, normalised, UNCLIPPED",
        "output_layout": "NCHW float32, normalised, UNCLIPPED, 2x spatial",
        "receptive_field_input_px": str(C.RECEPTIVE_FIELD_PREDICTED),
        "infer_tile_src_px": str(P.INFER_TILE_SRC_PX),
        "infer_overlap_src_px": str(P.INFER_OVERLAP_SRC_PX),
        "loss": f"charbonnier eps={C.CHARBONNIER_EPS}",
        "no_adversarial_or_perceptual_term": "true",
        "mode_dependent_layers": "none (no BatchNorm, no dropout)",
        "train_seed": str(C.TRAIN_SEED),
        "checkpoint": Path(ck_path).name,
        "checkpoint_step": str(ck.get("step")),
        # --- A1.2: the numeric path this model was produced by, so a future rerun on a
        # machine whose exporter default differs cannot switch silently ---
        "train_device": str(ck.get("train_device", rec.get("device", "mps"))),
        # --- the schedule, stated TWICE: what was registered, and what actually ran ---
        "registered_schedule_steps": str(schedule_steps),
        "completed_steps": str(rec.get("step_to", "unknown")),
        "stop_reason": stop,
        "schedule_note": (
            f"REGISTERED SCHEDULE {schedule_steps} steps; RUN STOPPED AT "
            f"{rec.get('step_to', '?')} steps because stop_reason={stop}. "
            f"A model stopped early is a DIFFERENT MODEL, not a noisier version of the "
            f"same one. Every number from this model carries this step count."),
        "training_wall_clock_s": f"{rec.get('wall_clock_s', float('nan')):.1f}",
        "training_steps_per_s": f"{rec.get('steps_per_s', float('nan')):.3f}",
        "best_val_charbonnier": f"{ck.get('best', float('nan')):.6f}",
        "torch": torch.__version__,
        "onnx_exporter": "legacy TorchScript (dynamo=False)",
        "onnx_exporter_note": ("torch 2.13 defaults to the dynamo exporter, which requires "
                               "onnxscript; that package is absent and this work package "
                               "installs nothing. dynamo=False is PINNED, not incidental."),
        "opset": str(OPSET),
        "caveat": ("Trained by the Wald protocol 20m->10m and applied 10m->5m; the "
                   "scale-invariance of the sensor MTF is assumed and is unverifiable with "
                   "this data. The 5 m output is NOT validated against ground truth."),
    }


def main():
    ap = argparse.ArgumentParser(prog="export_onnx.py")
    ap.add_argument("--ckpt", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--schedule", type=int, default=20000,
                    help="the REGISTERED schedule in steps, recorded beside what actually ran")
    a = ap.parse_args()
    ck_path = Path(a.ckpt or (C.data_root() / C.RUN_SUBDIR / "run1" / "best.pt"))
    if not ck_path.is_file():
        raise SystemExit(f"export_onnx: checkpoint not found: {ck_path}")
    out = Path(a.out or (C.data_root() / "sr_models" / "gencp_sr_x2_v1.onnx"))
    out.parent.mkdir(parents=True, exist_ok=True)

    ck = torch.load(ck_path, map_location="cpu")
    rec = training_record(ck_path)
    model = SRNet(); model.load_state_dict(ck["model"]); model.eval()

    dummy = torch.zeros(1, 3, C.INPUT_PX, C.INPUT_PX)
    # dynamo=False selects the legacy TorchScript exporter. torch 2.13 defaults to the
    # dynamo exporter, which requires `onnxscript`; that package is not installed and this
    # work package installs nothing. The TorchScript path supports `dynamic_axes`, which is
    # what D17 actually needs, so nothing is given up by pinning it.
    torch.onnx.export(
        model, (dummy,), str(out), opset_version=OPSET,
        input_names=["input"], output_names=["output"],
        dynamic_axes={"input": {0: "batch", 2: "height", 3: "width"},
                      "output": {0: "batch", 2: "height2", 3: "width2"}},
        do_constant_folding=True, dynamo=False)

    import onnx
    m = onnx.load(str(out))
    prov = provenance(ck_path, ck, a.schedule, rec)
    for k, v in prov.items():
        e = m.metadata_props.add(); e.key, e.value = k, v
    onnx.save(m, str(out))

    import onnxruntime as ort
    sess = ort.InferenceSession(str(out), providers=["CPUExecutionProvider"])
    print(f"exported {out}  {out.stat().st_size:,} bytes  opset {OPSET}")
    print(f"  torch {torch.__version__}  onnx {onnx.__version__}  "
          f"onnxruntime {ort.__version__}")
    print(f"  sha256 {hashlib.sha256(out.read_bytes()).hexdigest()}")
    dims = [d.dim_param or d.dim_value for d in
            m.graph.input[0].type.tensor_type.shape.dim]
    print(f"  declared input shape : {dims}")
    print()
    print("D17-C: the graph runs at 128 (training size), 96, and 100 (not a multiple of 8),")
    print("       and is compared with PyTorch on the same inputs.")
    rows, ok = [], True
    g = torch.Generator().manual_seed(C.TRAIN_SEED)
    for size in (C.INPUT_PX, 96, 100):
        x = torch.rand(1, 3, size, size, generator=g)
        try:
            y_ort = sess.run(None, {"input": x.numpy()})[0]
        except Exception as e:
            print(f"  [FAIL] {size:4d}: graph refused the shape: {e}")
            ok = False; rows.append(dict(size=size, ran=False, error=str(e)[:200])); continue
        with torch.no_grad():
            y_pt = model(x).numpy()
        shape_ok = y_ort.shape == y_pt.shape == (1, 3, size * 2, size * 2)
        d = float(np.abs(y_ort - y_pt).max())
        dn = d * P.NORM_DIVISOR_DN
        good = shape_ok and d < 1e-4
        ok &= good
        print(f"  [{'PASS' if good else 'FAIL'}] {size:4d} -> {y_ort.shape[2]}x"
              f"{y_ort.shape[3]}   max |onnx - torch| = {d:.3e} normalised = {dn:.5f} DN")
        rows.append(dict(size=size, ran=True, out_shape=list(y_ort.shape),
                         max_abs_diff_normalised=d, max_abs_diff_dn=dn, pass_=good))
    rec = dict(work_package="P2-WP3B", model=str(out), bytes=out.stat().st_size,
               sha256=hashlib.sha256(out.read_bytes()).hexdigest(), opset=OPSET,
               torch=torch.__version__, onnx=onnx.__version__, onnxruntime=ort.__version__,
               bound_normalised=1e-4, checks=rows, all_pass=ok,
               registered_schedule_steps=a.schedule,
               completed_steps=rec.get("step_to"), stop_reason=rec.get("stop_reason"),
               metadata=prov)
    (out.parent / "export_verification.json").write_text(json.dumps(rec, indent=2))
    print(f"\n  wrote {out.parent / 'export_verification.json'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
