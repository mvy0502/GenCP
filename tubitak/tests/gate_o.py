#!/usr/bin/env python
"""Gate O — PyTorch/ONNX parity. UNITS PINNED (amendment 2, 2026-08-26).

Registered in tubitak/docs/plugin-gate-registrations.md before this ran.

20 tiles through both the PyTorch generator and the ONNX model, identical inputs and
identical dropout state (both deterministic: dropout removed).

UNITS. The first run of this gate compared a difference expressed in 8-bit DN against
the number 1/255 = 0.003922, which is a NORMALISED-unit value. Those are different
units, and the mismatch made fp16's 0.435565 readable either as "well under half a grey
level, negligible" or as "over a hundred grey levels, catastrophic". Every difference is
now reported in all three units, and the bound is stated in each.

The generator ends in Tanh, so the network output tensor lives in [-1, 1]. util.tensor2im
maps it to bytes with DN = (x + 1) / 2 * 255. Therefore:

    1 DN  =  2/255 tensor units (0.007843)  =  1/255 of full scale
    DN    =  |delta_tensor| * 127.5

The registered bound "max abs diff <= 1/255" is one 255th of full scale, i.e. ONE GREY
LEVEL: 1.0 DN, 0.007843 tensor units, 0.003922 normalised. The strict alternative
reading - 1/255 of a DN - is also reported, because the original registration text was
ambiguous and the two readings disagree about fp16.

The decisive number, which needs no unit convention at all, is the last block: how many
pixels of the FINAL uint8 IMAGE actually differ. That is what a user would see, and it
is what the fp16 decision now rests on.

Also asserts the numpy preprocessing in gencp_core.infer is bit-identical to the
torchvision pipeline test.py uses, since "identical inputs" is otherwise an assumption.
"""
from __future__ import annotations
import csv, json, sys, warnings
from pathlib import Path

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

# Unknown arguments are refused, not ignored: a verifier that runs its default
# and prints PASS when you asked for something else is reporting on the wrong run.
import os.path as _op  # noqa: E402
sys.path.insert(0, _op.join(_op.dirname(_op.abspath(__file__)),
                            *(['..', 'tests'] if _op.basename(
                                _op.dirname(_op.abspath(__file__))) != 'tests'
                              else [])))
from _guard import strict_argv  # noqa: E402
strict_argv(known=(), positional=0)
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

# The registered bound, expressed in every unit it can be expressed in.
BOUND_DN = 1.0                    # one grey level = 1/255 of full scale
BOUND_TENSOR = 2.0 / 255.0        # the same bound in [-1, 1] tensor units
BOUND_NORM = 1.0 / 255.0          # the same bound in [0, 1] normalised units
BOUND_DN_STRICT = 1.0 / 255.0     # the strict alternative reading: 1/255 of a DN


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
        per_ch_max = np.zeros(3)     # in DN
        per_ch_sum = np.zeros(3)
        n_px = 0
        worst_tile = (None, -1.0)
        px_diff = 0                  # uint8 pixels (any channel) that differ
        px_total = 0
        uint8_max = 0
        for p in paths:
            with Image.open(p) as im:
                x = infer.preprocess(im.convert("RGB"))
            with torch.no_grad():
                yt = G(torch.from_numpy(x)).numpy()
            yo = sess.run_tensor(x)
            # continuous difference, before quantisation, so rounding neither hides nor
            # invents a difference. yt, yo are in [-1, 1]; DN = |delta| * 127.5.
            d_cont = np.abs(yt - yo)[0] * 127.5
            for c in range(3):
                per_ch_max[c] = max(per_ch_max[c], float(d_cont[c].max()))
                per_ch_sum[c] += float(d_cont[c].sum())
            n_px += d_cont[0].size
            tw = float(d_cont.max())
            if tw > worst_tile[1]:
                worst_tile = (p.stem, tw)
            # the unit-free number: the FINAL uint8 images a user would see
            a = infer.postprocess(yt).astype(np.int32)
            b = infer.postprocess(yo).astype(np.int32)
            d8 = np.abs(a - b)
            px_diff += int((d8.max(axis=2) > 0).sum())
            px_total += d8.shape[0] * d8.shape[1]
            uint8_max = max(uint8_max, int(d8.max()))

        per_ch_mean = per_ch_sum / n_px
        max_dn = float(per_ch_max.max())
        mean_dn = float(per_ch_sum.sum() / (3 * n_px))
        max_tensor = max_dn / 127.5
        max_norm = max_dn / 255.0
        v_grey = "PASS" if max_dn <= BOUND_DN else "FAIL"
        v_strict = "PASS" if max_dn <= BOUND_DN_STRICT else "FAIL"
        results[tag] = dict(
            per_channel_max_dn=per_ch_max.tolist(),
            per_channel_mean_dn=per_ch_mean.tolist(),
            max_dn=max_dn, mean_dn=mean_dn,
            max_tensor_units=max_tensor, max_normalised=max_norm,
            verdict_one_grey_level=v_grey, verdict_strict_1_255_of_a_DN=v_strict,
            uint8_pixels_differing=px_diff, uint8_pixels_total=px_total,
            uint8_max_abs_diff=uint8_max,
            worst_tile=worst_tile[0],
            size_bytes=(MODELS / model_file).stat().st_size)

        print(f"--- ONNX {tag} vs PyTorch, {len(paths)} tiles ---")
        print(f"   {'channel':<9}{'max (DN)':>14}{'mean (DN)':>14}"
              f"{'max (tensor)':>16}{'max (norm)':>14}")
        for c, nm in enumerate("RGB"):
            print(f"   {nm:<9}{per_ch_max[c]:>14.6f}{per_ch_mean[c]:>14.6f}"
                  f"{per_ch_max[c]/127.5:>16.3e}{per_ch_max[c]/255.0:>14.3e}")
        print(f"   {'overall':<9}{max_dn:>14.6f}{mean_dn:>14.6f}"
              f"{max_tensor:>16.3e}{max_norm:>14.3e}")
        print(f"   tensor range [-1, 1] (Tanh);  1 DN = 2/255 tensor units = 1/255 "
              f"of full scale")
        print(f"   bound, one grey level      : {BOUND_DN:.6f} DN = "
              f"{BOUND_TENSOR:.6f} tensor = {BOUND_NORM:.6f} norm  -> {v_grey}")
        print(f"   bound, strict 1/255 of a DN: {BOUND_DN_STRICT:.6f} DN"
              f"                                  -> {v_strict}")
        print(f"   FINAL uint8 image: {px_diff}/{px_total} pixels differ "
              f"({100.0*px_diff/px_total:.4f}%), max abs diff {uint8_max} DN")
        print(f"   worst tile: {worst_tile[0]}   file size: "
              f"{(MODELS/model_file).stat().st_size/1e6:.2f} MB\n")

    (OUT / "gate_o_results.json").write_text(json.dumps(
        dict(stems=stems, preprocess_max_abs_diff=pre, results=results), indent=2))

    gate_pass = results["fp32"]["verdict_one_grey_level"] == "PASS"
    print("=" * 78)
    for tag in ("fp32", "fp16"):
        r = results[tag]
        print(f"  {tag}: max {r['max_dn']:.6f} DN | one-grey-level bound "
              f"{r['verdict_one_grey_level']} | strict bound "
              f"{r['verdict_strict_1_255_of_a_DN']} | uint8 pixels differing "
              f"{r['uint8_pixels_differing']}/{r['uint8_pixels_total']} "
              f"({100.0*r['uint8_pixels_differing']/r['uint8_pixels_total']:.4f}%)")
    print(f"GATE O (fp32, the deployed model): "
          f"{results['fp32']['verdict_one_grey_level']}")
    print("=" * 78)
    return 0 if gate_pass else 1


if __name__ == "__main__":
    sys.exit(main())
