#!/usr/bin/env python3
"""Part C — read the two test sets ONCE, on BOTH numeric paths (D20).

A metric produced by a path nobody runs is not a measurement of the tool. The model trains
on MPS; what a user executes is the ONNX graph under onnxruntime on CPU, inside QGIS. So
every metric is computed TWICE on the identical chips - once from the exported ONNX graph on
CPU, once from the PyTorch model - and the maximum per-chip difference between the two paths
is reported. If they agree inside the registered tolerance the ONNX-on-CPU figures are the
registered ones; if they do not, that disagreement is the finding and outranks the margin.

Sign convention, stated once and never flipped: every difference is `model - bicubic`.
  PSNR, SSIM : positive means the MODEL IS BETTER.
  MAE        : negative means the MODEL IS BETTER.

D21: the scope caveat is printed next to the margin, here in the tool's own stdout, not only
in the report. The number and its scope travel together.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np
import torch

SR = Path(__file__).resolve().parents[1]
if str(SR) not in sys.path:
    sys.path.insert(0, str(SR))

from sr_core.upsample import BicubicUpsampler                           # noqa: E402
from sr_data import params as P                                         # noqa: E402
from sr_data.degrade import degrade_chip                                # noqa: E402
from sr_data.metrics import mae_chip, psnr_chip, ssim_chip              # noqa: E402
from sr_train import config as C, data as D                             # noqa: E402
from sr_train.data import BandOrderError, assert_band_order             # noqa: E402
from sr_train.model import SRNet                                        # noqa: E402

#: A1.1, registered before this was run.
TOL = dict(raw=1e-4, psnr=0.01, ssim=1e-4, mae=1e-6)

#: The REGISTERED schedule. What actually ran is read from train_record.json and reported
#: beside it, always both, never one alone.
SCHEDULE_STEPS = 20000

def _num(x):
    """Trim a trailing '.0' so 2.5 stays 2.5 and 5.0 prints as 5."""
    return f"{x:g}"


# D21: the caveat travels with the number. It is DERIVED from the scale, never written down:
# at scale 2 this text said "decimation by two ... real imagery at 5 m ... the 10 m -> 5 m
# relationship", and it printed those words unchanged under a scale-4 model, where the
# degradation is by four and the deployment output is 2.5 m. A caveat that is mandated to
# travel with a number is worthless if it travels hard-coded.
CAVEAT = (
    f"SCOPE OF THIS NUMBER: the model inverts a degradation we constructed and know exactly\n"
    f"  (Gaussian low-pass at MTF {C.MTF_AT_NYQUIST}, then decimation by {C.SCALE}: "
    f"{_num(C.SRC_GSD_M)} m -> {_num(C.GSD_M)} m).\n"
    f"  Beating bicubic at that task is partly a statement about inverting a KNOWN SYNTHETIC\n"
    f"  BLUR, not about how well it super-resolves real imagery at {_num(C.OUT_GSD_M)} m, where\n"
    f"  there is no ground truth and the true {_num(C.GSD_M)} m -> {_num(C.OUT_GSD_M)} m "
    f"relationship is not that blur.")


def edge_density(x):
    """Mean gradient magnitude. DIAGNOSTIC ONLY - not a gate, not a claim."""
    return float(0.5 * (np.abs(np.diff(x, axis=-2)).mean()
                        + np.abs(np.diff(x, axis=-1)).mean()))


def summarise(v):
    v = np.asarray(v, float)
    return dict(mean=float(v.mean()), std=float(v.std()), n=int(v.size))


def evaluate_split(split, torch_model, sess, batch=8):
    chips, recs = D.load_split(split)
    div = D.assert_norm_divisor(C.NORM_DIVISOR_DN)
    up = BicubicUpsampler(scale=C.SCALE)
    keys = ("psnr", "ssim", "mae", "ed")
    acc = {f"{k}_{p}": [] for k in keys for p in ("o", "t", "b")}
    acc["ed_tgt"], acc["raw_diff"] = [], []
    n = chips.shape[0]
    for s in range(0, n, batch):
        lo_l, hi_l = [], []
        for i in range(s, min(s + batch, n)):
            a, b = degrade_chip(chips[i], div, scale=C.SCALE)
            lo_l.append(a); hi_l.append(b)
        lo = np.stack(lo_l).astype(np.float32)
        hi = np.stack(hi_l).astype(np.float32)
        y_onnx = sess.run(None, {"input": lo})[0]
        with torch.no_grad():
            y_torch = torch_model(torch.from_numpy(lo)).numpy()
        for k in range(lo.shape[0]):
            t = hi[k]
            bic = np.moveaxis(up.upsample(np.moveaxis(lo[k], 0, -1)), -1, 0)
            o, w = y_onnx[k], y_torch[k]
            acc["raw_diff"].append(float(np.abs(o - w).max()))
            for tag, pred in (("o", o), ("t", w), ("b", bic)):
                acc[f"psnr_{tag}"].append(psnr_chip(pred, t, C.PSNR_DATA_RANGE))
                acc[f"ssim_{tag}"].append(ssim_chip(pred, t, C.PSNR_DATA_RANGE))
                acc[f"mae_{tag}"].append(mae_chip(pred, t))
                acc[f"ed_{tag}"].append(edge_density(pred))
            acc["ed_tgt"].append(edge_density(t))
    a = {k: np.asarray(v, float) for k, v in acc.items()}

    agree = dict(raw_max=float(a["raw_diff"].max()))
    for m in ("psnr", "ssim", "mae"):
        agree[f"{m}_max_per_chip"] = float(np.abs(a[f"{m}_o"] - a[f"{m}_t"]).max())
    agree["within_tolerance"] = bool(
        agree["raw_max"] < TOL["raw"] and agree["psnr_max_per_chip"] < TOL["psnr"]
        and agree["ssim_max_per_chip"] < TOL["ssim"]
        and agree["mae_max_per_chip"] < TOL["mae"])

    def paired(tag):
        out = {}
        for m, better in (("psnr", "positive"), ("ssim", "positive"), ("mae", "negative")):
            d = a[f"{m}_{tag}"] - a[f"{m}_b"]
            worse = int((d < 0).sum() if better == "positive" else (d > 0).sum())
            out[m] = dict(mean=float(d.mean()), std=float(d.std()),
                          chips_model_worse=worse, n=int(d.size), better_direction=better)
        return out

    return dict(
        n=n,
        onnx_cpu={m: summarise(a[f"{m}_o"]) for m in ("psnr", "ssim", "mae")},
        pytorch={m: summarise(a[f"{m}_t"]) for m in ("psnr", "ssim", "mae")},
        bicubic={m: summarise(a[f"{m}_b"]) for m in ("psnr", "ssim", "mae")},
        paired_onnx_minus_bicubic=paired("o"),
        paired_pytorch_minus_bicubic=paired("t"),
        path_agreement=agree, tolerance=TOL,
        edge_density=dict(onnx=summarise(a["ed_o"]), pytorch=summarise(a["ed_t"]),
                          bicubic=summarise(a["ed_b"]), target=summarise(a["ed_tgt"])),
        per_chip={k: [float(x) for x in v] for k, v in a.items()},
    )



def _load_checkpoint(path, map_location="cpu"):
    """Load a checkpoint, preferring torch's safe reader.

    Pre-WP16 checkpoints store `TorchVersion` objects (standing practice 9's version
    record), which `weights_only=True` refuses. Those files are our own, written by
    train.py in this repository, so falling back is safe - but the fallback is announced,
    because a silent `weights_only=False` everywhere is how the safe default stops meaning
    anything.
    """
    try:
        return torch.load(path, map_location=map_location, weights_only=True)
    except Exception as e:
        print(f"  note: {Path(path).name} is a pre-WP16 checkpoint (weights_only=True "
              f"refused it: {type(e).__name__}); re-reading with weights_only=False")
        return torch.load(path, map_location=map_location, weights_only=False)

def main():
    ap = argparse.ArgumentParser(prog="evaluate.py")
    ap.add_argument("--ckpt", default=None)
    ap.add_argument("--onnx", default=None)
    ap.add_argument("--splits", default="test,heldout")
    ap.add_argument("--json", default=None)
    a = ap.parse_args()

    ck_path = Path(a.ckpt or (C.data_root() / C.RUN_SUBDIR / "run1" / "best.pt"))
    onnx_path = Path(a.onnx or (C.data_root() / "sr_models" / "gencp_sr_x2_v1.onnx"))
    for p, what in ((ck_path, "checkpoint"), (onnx_path, "ONNX graph")):
        if not p.is_file():
            raise SystemExit(f"evaluate: {what} not found: {p}")

    import onnx
    import onnxruntime as ort
    # WP16: checkpoints written from 1 September 2026 store versions as plain strings and
    # host-resident tensors, so they load under torch's default weights_only=True. Older
    # ones store TorchVersion objects and do not. Try the safe path first and fall back,
    # saying so, rather than disabling the check for every file forever.
    ck = _load_checkpoint(ck_path)
    model = SRNet(bands=C.N_BANDS, scale=C.SCALE)
    model.load_state_dict(ck["model"]); model.eval()
    # X5: the graph states its own band order; refuse it if it is not the one this config
    # feeds. assert_band_order was DEFINED and never CALLED until now - a check nothing
    # invokes is not a check, which is this project's own standing finding about verifiers.
    _meta = {kv.key: kv.value for kv in onnx.load(str(onnx_path)).metadata_props}
    if "band_order" not in _meta:
        raise BandOrderError(f"{onnx_path}: graph declares no band_order; refusing to use it")
    assert_band_order(_meta["band_order"], where=str(onnx_path))
    sess = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
    if sess.get_providers() != ["CPUExecutionProvider"]:
        raise SystemExit(f"evaluate: expected CPU provider, got {sess.get_providers()}")

    tr_f = ck_path.parent / "train_record.json"
    tr = json.loads(tr_f.read_text()) if tr_f.is_file() else {}
    print("Part C - the two test sets, read ONCE, on BOTH numeric paths (D20)")
    print(f"  checkpoint {ck_path.name} step {ck.get('step')} best val {ck.get('best'):.6f}"
          f"   trained on {ck.get('train_device', tr.get('device', 'mps'))}")
    print(f"  SCHEDULE: registered {SCHEDULE_STEPS} steps; run STOPPED at "
          f"{tr.get('step_to', '?')} steps (stop_reason={tr.get('stop_reason', '?')}), "
          f"{tr.get('steps_per_s', float('nan')):.2f} steps/s.")
    print("  A model stopped early is a DIFFERENT MODEL, not a noisier version of the same")
    print("  one; every number below carries that step count.")
    print(f"  ONNX {onnx_path.name}, provider {sess.get_providers()[0]}, "
          f"onnxruntime {ort.__version__}, torch {torch.__version__}")
    print(f"  variant {C.VARIANT}: scale {C.SCALE}, {C.N_BANDS} bands "
          f"{','.join(C.BANDS)}")
    print(f"  domain normalised reflectance DN/{C.NORM_DIVISOR_DN:.0f}, per chip, unweighted "
          f"mean over chips, PSNR range {C.PSNR_DATA_RANGE}")
    print("  sign: model - bicubic. PSNR/SSIM positive = model better; MAE negative = better")
    print(f"  registered tolerance: raw < {TOL['raw']:g}, PSNR < {TOL['psnr']:g} dB, "
          f"SSIM < {TOL['ssim']:g}, MAE < {TOL['mae']:g}\n")

    t0 = time.perf_counter()
    res, all_agree = {}, True
    for s in a.splits.split(","):
        r = evaluate_split(s, model, sess)
        res[s] = r
        ag = r["path_agreement"]
        all_agree &= ag["within_tolerance"]
        print(f"== {s}  (n = {r['n']})")
        print(f"   PATH AGREEMENT onnx-cpu vs pytorch: raw {ag['raw_max']:.3e}  "
              f"PSNR {ag['psnr_max_per_chip']:.3e} dB  SSIM {ag['ssim_max_per_chip']:.3e}  "
              f"MAE {ag['mae_max_per_chip']:.3e}   "
              f"-> {'WITHIN TOLERANCE' if ag['within_tolerance'] else '*** DISAGREE ***'}")
        for m, fmt in (("psnr", "{:8.4f}"), ("ssim", "{:.6f}"), ("mae", "{:.8f}")):
            o, w, b = r["onnx_cpu"][m], r["pytorch"][m], r["bicubic"][m]
            po = r["paired_onnx_minus_bicubic"][m]
            print(f"   {m.upper():5s} onnx-cpu {fmt.format(o['mean'])}   "
                  f"pytorch {fmt.format(w['mean'])}   bicubic {fmt.format(b['mean'])}")
            print(f"         paired (onnx - bicubic) {po['mean']:+.6f} +- {po['std']:.6f}   "
                  f"chips model worse {po['chips_model_worse']}/{po['n']}")
        ed = r["edge_density"]
        print(f"   edge density (DIAGNOSTIC, not a gate): onnx {ed['onnx']['mean']:.6f}  "
              f"bicubic {ed['bicubic']['mean']:.6f}  target {ed['target']['mean']:.6f}")
        print(f"   {CAVEAT}")
        print()

    if not all_agree:
        print("*** THE TWO NUMERIC PATHS DISAGREE BEYOND THE REGISTERED TOLERANCE.")
        print("*** Per D20 that disagreement is the finding and outranks the margin over")
        print("*** bicubic. The margins above are provisional until it is explained.")
    else:
        print("The two paths agree inside the registered tolerance on every split, so per")
        print("D20 the ONNX-on-CPU figures are the REGISTERED ones - they are the numbers")
        print("produced by the artifact that ships.")

    out = Path(a.json or (ck_path.parent / "evaluation.json"))
    out.write_text(json.dumps(dict(
        work_package=C.WORK_PACKAGE, checkpoint=str(ck_path), onnx=str(onnx_path),
        step=ck.get("step"), best_val=ck.get("best"),
        registered_schedule_steps=SCHEDULE_STEPS,
        completed_steps=tr.get("step_to"), stop_reason=tr.get("stop_reason"),
        training_steps_per_s=tr.get("steps_per_s"),
        train_device=ck.get("train_device", "mps"),
        torch=torch.__version__, onnxruntime=ort.__version__,
        onnx_provider=sess.get_providers()[0],
        onnx_exporter="legacy TorchScript (dynamo=False)",
        norm_divisor_dn=C.NORM_DIVISOR_DN, variant=C.VARIANT, scale=C.SCALE,
        bands=list(C.BANDS), tolerance=TOL,
        registered_path=("onnx_cpu" if all_agree else "NONE - paths disagree"),
        all_paths_agree=all_agree, scope_caveat=CAVEAT.replace("\n", " "),
        sign_convention="model - bicubic; PSNR/SSIM positive = model better; "
                        "MAE negative = model better",
        never_pooled=True, results=res, wall_clock_s=time.perf_counter() - t0), indent=2))
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
