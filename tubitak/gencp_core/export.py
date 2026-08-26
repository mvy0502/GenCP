"""Export a trained pix2pix generator to ONNX.

This module is the ONE place in gencp_core that imports torch, and it is never imported
by the plugin — it is a build-time tool. `infer.py`, which the plugin does use, needs only
onnxruntime and numpy.

Two determinism decisions are made here, and neither is a default:

1. **Dropout is removed.** pix2pix keeps dropout active at test time by design (it is the
   generator's noise source in place of a z vector). A delivered tool must return the same
   image for the same input, so the exported graph has no dropout. The dropout modules are
   parameterless, so the checkpoint loads unchanged.

2. **BatchNorm is exported in BATCH-STATISTICS mode, not running-statistics mode.** This
   is the decision that matters and it is easy to get wrong silently. The generator is
   built with `--norm batch`, and `test.py` runs it WITHOUT `model.eval()`, so every number
   this project has ever measured was produced with BatchNorm using the statistics of the
   single image being generated. `torch.onnx.export` calls `model.eval()` by default, which
   would switch to the running statistics accumulated during training — measured on this
   checkpoint as a mean 32 DN / max 94 DN change affecting 100% of pixels. Exporting that
   way would have produced a plugin that silently generates different images from the ones
   the whole evaluation phase scored.

   With batch size 1, BatchNorm2d in train mode normalises by the per-channel mean and
   variance of that one image over its spatial dimensions — which is exactly instance
   normalisation with the BatchNorm affine parameters. That equivalence is exact (verified
   to max abs diff 0.0), so each BatchNorm2d is replaced by an InstanceNorm2d carrying the
   same weight, bias and eps. The exported graph then reproduces the evaluated path, and it
   is deterministic because instance statistics depend only on the input.

`--eval-bn` exports the running-statistics variant instead, so the two can be compared
(Gate D). It is not the default.
"""
from __future__ import annotations
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]

ARMS = {
    "pretrained": ("GenCP_HR_demo/checkpoints", "genCP_HR_RGB_model"),
    "C1": ("tubitak/outputs/c1_checkpoints/checkpoints", "C1"),
    "C2": ("tubitak/outputs/c2_checkpoints/checkpoints", "C2"),
    "C3": ("tubitak/outputs/c3_checkpoints/checkpoints", "C3"),
}


def checkpoint_path(arm):
    ckdir, name = ARMS[arm]
    return _REPO_ROOT / ckdir / name / "latest_net_G.pth"


def build_generator(checkpoint, eval_bn=False, repo_root=None):
    """Load the generator exactly as test.py builds it, with dropout removed.

    Returns a torch module in the mode the export should capture.
    """
    import torch
    import torch.nn as nn
    root = Path(repo_root or _REPO_ROOT)
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from models import networks

    # Same call test.py makes, with use_dropout=False (i.e. --no_dropout).
    G = networks.define_G(3, 3, 64, "unet_256", "batch", False, "normal", 0.02, [])
    G = G.module if isinstance(G, nn.DataParallel) else G
    sd = torch.load(str(checkpoint), map_location="cpu")
    if hasattr(sd, "_metadata"):
        del sd._metadata
    G.load_state_dict(sd)
    G.eval()

    if not eval_bn:
        _swap_batchnorm_for_instancenorm(G)
    return G


def build_stochastic_generator(checkpoint, repo_root=None):
    """The same generator, with dropout PUT BACK and left active.

    The delivered image never comes from this path. It exists only to estimate how much of
    the output is invention: N passes with dropout live, per-pixel spread across them. See
    tubitak/docs/confidence-registration.md, signal S.

    Two things are kept identical to the deployed export so the spread describes the
    delivered image rather than some other model:

      - BatchNorm is still swapped for the exactly-equivalent batch-size-1 InstanceNorm,
        so the passes sit on the evaluated inference path.
      - The weights are the same checkpoint, loaded the same way. Dropout is parameterless,
        which is why `export.py` can strip it and this can restore it without either one
        touching the state dict.

    The checkpoint must have been TRAINED with dropout for this to mean anything. C1-C5
    were (`no_dropout: False` in their train_opt.txt).
    """
    import torch
    import torch.nn as nn
    root = Path(repo_root or _REPO_ROOT)
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from models import networks

    # use_dropout=True - the ONE difference from build_generator().
    G = networks.define_G(3, 3, 64, "unet_256", "batch", True, "normal", 0.02, [])
    G = G.module if isinstance(G, nn.DataParallel) else G
    sd = torch.load(str(checkpoint), map_location="cpu")
    if hasattr(sd, "_metadata"):
        del sd._metadata
    G.load_state_dict(sd)
    G.eval()
    _swap_batchnorm_for_instancenorm(G)
    # eval() above turned dropout off along with everything else; turn it back on, and
    # only it. Calling G.train() instead would also revive BatchNorm's training behaviour
    # in the modules that have not been swapped.
    n_dropout = 0
    for m in G.modules():
        if isinstance(m, nn.Dropout):
            m.train()
            n_dropout += 1
    if n_dropout == 0:
        raise RuntimeError(
            "no Dropout modules in the generator - a stochastic pass would return the "
            "deterministic image N times and its spread would be identically zero")
    return G, n_dropout


class _MaskedDropout:
    """Placeholder marker; the real class is built inside export_stochastic (needs torch)."""


def _dropout_modules_in_execution_order(G, torch):
    """The Dropout modules and their input shapes, in the order forward() reaches them.

    Module registration order is not guaranteed to be execution order, and getting the two
    confused would pair a 4x4 mask with a 16x16 tensor - which broadcasts silently in some
    shapes rather than raising. So the order is measured with hooks, not assumed.
    """
    seen = []
    handles = []
    for mod in G.modules():
        if isinstance(mod, torch.nn.Dropout):
            handles.append(mod.register_forward_hook(
                lambda m, i, o, _s=seen: _s.append((m, tuple(i[0].shape)))))
    with torch.no_grad():
        G(torch.zeros(1, 3, 256, 256))
    for h in handles:
        h.remove()
    return seen


def export_stochastic(checkpoint, out_path, opset=17, repo_root=None):
    """Export a generator whose dropout noise arrives as EXPLICIT MODEL INPUTS.

    Needed because the confidence score's stochastic-spread term requires N different
    dropout draws at inference time, and neither alternative works:

      - The deployed export has no dropout at all; N passes would return one image N times
        and a spread of exactly zero.
      - ONNX's own Dropout operator in training mode carries its seed as a graph
        ATTRIBUTE, fixed at export. Every pass would draw the same mask, which is the same
        failure wearing a different hat.

    So each `nn.Dropout(0.5)` becomes a multiply by an input tensor. The caller draws the
    masks - Bernoulli(1-p) scaled by 1/(1-p), which is exactly what nn.Dropout does in
    train mode - and therefore controls and can record the seed, which standing practice 9
    requires and which Registration A could not do.

    Everything else is identical to the deterministic export, BatchNorm swap included, so
    the passes sit on the same inference path as the delivered image.

    Returns (path, [mask shapes in graph-input order]).
    """
    import torch
    import torch.nn as nn

    G, _ = build_stochastic_generator(checkpoint, repo_root=repo_root)
    order = _dropout_modules_in_execution_order(G, torch)
    shapes = [s for _, s in order]

    class MaskedDropout(nn.Module):
        def forward(self, x):
            return x * self.mask

    replaced = []
    targets = {id(m) for m, _ in order}
    def _replace(parent):
        for name, child in list(parent.named_children()):
            if id(child) in targets:
                md = MaskedDropout()
                setattr(parent, name, md)
                replaced.append((id(child), md))
            else:
                _replace(child)
    _replace(G)
    by_id = dict(replaced)
    ordered_masked = [by_id[id(m)] for m, _ in order]
    if len(ordered_masked) != len(order):
        raise RuntimeError("failed to replace every Dropout module")

    class Wrapper(nn.Module):
        def __init__(self, g, drops):
            super().__init__()
            self.g = g
            self._drops = drops

        def forward(self, x, *masks):
            for d, m in zip(self._drops, masks):
                d.mask = m
            return self.g(x)

    W = Wrapper(G, ordered_masked)
    dummy = (torch.zeros(1, 3, 256, 256),) + tuple(torch.ones(*s) for s in shapes)
    names = ["input"] + [f"mask{i}" for i in range(len(shapes))]
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with torch.no_grad():
        torch.onnx.export(
            W, dummy, str(out_path),
            input_names=names, output_names=["output"],
            opset_version=opset, do_constant_folding=True, dynamo=False,
        )
    return out_path, shapes


def _swap_batchnorm_for_instancenorm(module):
    """Replace every BatchNorm2d with the exactly-equivalent batch-size-1 InstanceNorm2d."""
    import torch.nn as nn
    for name, child in list(module.named_children()):
        if isinstance(child, nn.BatchNorm2d):
            inr = nn.InstanceNorm2d(child.num_features, eps=child.eps,
                                    affine=True, track_running_stats=False)
            inr.weight.data.copy_(child.weight.data)
            inr.bias.data.copy_(child.bias.data)
            inr.eval()
            setattr(module, name, inr)
        else:
            _swap_batchnorm_for_instancenorm(child)
    return module


def export(checkpoint, out_path, eval_bn=False, fp16=False, opset=17, repo_root=None):
    """Export to ONNX. Returns the written path."""
    import torch
    G = build_generator(checkpoint, eval_bn=eval_bn, repo_root=repo_root)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    dummy = torch.zeros(1, 3, 256, 256, dtype=torch.float32)
    with torch.no_grad():
        torch.onnx.export(
            G, dummy, str(out_path),
            input_names=["input"], output_names=["output"],
            opset_version=opset, do_constant_folding=True,
            dynamo=False,
        )
    if fp16:
        _to_fp16(out_path)
    return out_path


def _to_fp16(path):
    """Convert a float32 ONNX file to float16 in place."""
    import onnx
    from onnxconverter_common import float16 as f16
    m = onnx.load(str(path))
    onnx.save(f16.convert_float_to_float16(m, keep_io_types=False), str(path))


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="Export a GenCP generator to ONNX")
    ap.add_argument("--arm", choices=list(ARMS), default="C3")
    ap.add_argument("--checkpoint", default=None, help="override the arm's checkpoint")
    ap.add_argument("--out", required=True)
    ap.add_argument("--eval-bn", action="store_true",
                    help="export running-statistics BatchNorm (NOT the evaluated path)")
    ap.add_argument("--fp16", action="store_true")
    ap.add_argument("--opset", type=int, default=17)
    a = ap.parse_args(argv)
    ck = Path(a.checkpoint) if a.checkpoint else checkpoint_path(a.arm)
    p = export(ck, a.out, eval_bn=a.eval_bn, fp16=a.fp16, opset=a.opset)
    print(f"wrote {p} ({p.stat().st_size/1e6:.2f} MB) from {ck}"
          f" [{'eval-BN' if a.eval_bn else 'batch-stat BN'}"
          f"{', fp16' if a.fp16 else ', fp32'}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
