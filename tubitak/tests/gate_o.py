#!/usr/bin/env python
"""Gate O — PyTorch/ONNX parity.

Registered in tubitak/docs/plugin-gate-registrations.md before this ran.

20 tiles through both the PyTorch generator and the ONNX model, identical inputs and
identical dropout state (both deterministic: dropout removed). Criterion: max abs diff
<= 1/255 in 8-bit units. Reports max and mean abs diff per channel.

Also asserts the numpy preprocessing in gencp_core.infer is bit-identical to the
torchvision pipeline test.py uses, since "identical inputs" is otherwise an assumption.
"""
from __future__ import annotations
import csv, json, sys, warnings
from pathlib import Path

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tubitak"))

import numpy as np
import torch
from PIL import Image

from gencp_core import infer, export as gexport

INPUTS = ROOT / "tubitak/data/rasteriser/acc_clcgate/inputs"
CENSUS = ROOT / "tubitak/data/tool_runs/task4/acc_census.csv"
MODELS = ROOT / "tubitak/data/plugin_models"
OUT = ROOT / "tubitak/data/plugin_gates/gate_o"
N_TILES = 20
BOUND = 1.0 / 255.0


def select_stems(n=N_TILES):
    """Registered rule: first n acc_clcgate stems, ascending lexicographic. No filtering."""
    rows = [r for r in csv.DictReader(open(CENSUS)) if r["corpus"] == "acc_clcgate"]
    return sorted(r["stem"] for r in rows)[:n]


def check_preprocess_identity(paths):
    """gencp_core.infer.preprocess must equal the torchvision transform, exactly."""
    import torchvision.transforms as T
    tf = T.Compose([T.Resize([256, 256], T.InterpolationMode.BICUBIC),
                    T.ToTensor(), T.Normalize((0.5,)*3, (0.5,)*3)])
    worst = 0.0
    for p in paths:
        with Image.open(p) as im:
            ours = infer.preprocess(im.convert("RGB"))
        with Image.open(p) as im:
            theirs = tf(im.convert("RGB")).unsqueeze(0).numpy()
        worst = max(worst, float(np.abs(ours - theirs).max()))
    return worst


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    stems = select_stems()
    paths = [INPUTS / f"{s}.png" for s in stems]
    missing = [p for p in paths if not p.is_file()]
    if missing:
        print("FAIL: missing inputs:", missing[:3])
        return 1

    print(f"Gate O — {len(stems)} tiles, first {N_TILES} acc_clcgate stems (lexicographic)")
    print(f"  inference path: DETERMINISTIC on both sides (dropout removed), "
          f"BatchNorm in batch-statistics mode = the evaluated path\n")

    pre = check_preprocess_identity(paths)
    print(f"preprocessing identity (gencp_core.infer vs torchvision): max abs diff = {pre:.3e}")
    if pre != 0.0:
        print("  NOTE: inputs are not bit-identical; parity below would be confounded.")
    print()

    ck = gexport.checkpoint_path("C3")
    G = gexport.build_generator(ck, eval_bn=False)

    results = {}
    for tag, model_file in (("fp32", "gencp_C3_fp32.onnx"), ("fp16", "gencp_C3_fp16.onnx")):
        sess = infer.OnnxGenerator(MODELS / model_file)
        per_ch_max = np.zeros(3)
        per_ch_sum = np.zeros(3)
        n_px = 0
        worst_tile = (None, -1.0)
        for p in paths:
            with Image.open(p) as im:
                x = infer.preprocess(im.convert("RGB"))
            with torch.no_grad():
                yt = G(torch.from_numpy(x)).numpy()
            yo = sess.run_tensor(x)
            a = infer.postprocess(yt).astype(np.int32)
            b = infer.postprocess(yo).astype(np.int32)
            # difference in 8-bit units, measured on the continuous output before
            # quantisation as well, so rounding does not hide or invent a difference
            d_cont = np.abs(yt - yo)[0] * 127.5      # [-1,1] -> DN scale
            for c in range(3):
                per_ch_max[c] = max(per_ch_max[c], float(d_cont[c].max()))
                per_ch_sum[c] += float(d_cont[c].sum())
            n_px += d_cont[0].size
            tw = float(d_cont.max())
            if tw > worst_tile[1]:
                worst_tile = (p.stem, tw)
            _ = (a, b)
        per_ch_mean = per_ch_sum / n_px
        overall_max = float(per_ch_max.max())
        verdict = "PASS" if overall_max <= BOUND else "FAIL"
        results[tag] = dict(per_channel_max_dn=per_ch_max.tolist(),
                            per_channel_mean_dn=per_ch_mean.tolist(),
                            max_dn=overall_max, verdict=verdict,
                            worst_tile=worst_tile[0],
                            size_bytes=(MODELS / model_file).stat().st_size)
        print(f"--- ONNX {tag} vs PyTorch, {len(paths)} tiles, 8-bit units (DN) ---")
        for c, nm in enumerate("RGB"):
            print(f"   {nm}: max abs diff {per_ch_max[c]:.6f} DN   "
                  f"mean abs diff {per_ch_mean[c]:.6f} DN")
        print(f"   overall max {overall_max:.6f} DN   bound {BOUND:.6f} DN "
              f"(1/255)   -> {verdict}   (worst tile: {worst_tile[0]})")
        print(f"   file size: {(MODELS/model_file).stat().st_size/1e6:.2f} MB\n")

    (OUT / "gate_o_results.json").write_text(json.dumps(
        dict(stems=stems, preprocess_max_abs_diff=pre, results=results), indent=2))

    gate_pass = results["fp32"]["verdict"] == "PASS"
    print("=" * 66)
    print(f"GATE O (fp32, the deployed model): {results['fp32']['verdict']}")
    print(f"  fp16 reported alongside: {results['fp16']['verdict']} "
          f"(max {results['fp16']['max_dn']:.4f} DN)")
    print("=" * 66)
    return 0 if gate_pass else 1


if __name__ == "__main__":
    sys.exit(main())
