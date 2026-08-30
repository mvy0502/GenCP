"""The super-resolution network — D15 and D16.

Residual convolutional network, NO normalisation layer, NO dropout, upsampling by a single
PixelShuffle at the end. No resize of the input anywhere, including on the global skip.

Two properties are structural rather than tested-after-the-fact:

**D15 - no mode-dependent operation.** There is no BatchNorm, no InstanceNorm, no LayerNorm
and no dropout, so `train()` and `eval()` are the same function and `torch.onnx.export`
calling `.eval()` cannot silently change behaviour. Project 1 paid for that trap once.

**D16 - receptive field 31 input pixels <= the 32 px tiling overlap.** Every 3x3 stride-1
convolution adds 2; the PixelShuffle and the global skip add nothing. N=6 residual blocks is
the largest depth that fits: N=7 would give 35.

The global skip is a NEAREST-NEIGHBOUR 2x upsample built from `repeat_interleave` plus the
same PixelShuffle, so it is a shuffle and not a resize. The network therefore learns the
residual over nearest-neighbour upsampling and starts near a sensible baseline.
"""
from __future__ import annotations

import sys
from pathlib import Path

import torch
import torch.nn as nn

SR = Path(__file__).resolve().parents[1]
if str(SR) not in sys.path:
    sys.path.insert(0, str(SR))

from sr_train import config as C                                        # noqa: E402


class ResBlock(nn.Module):
    def __init__(self, ch):
        super().__init__()
        self.c1 = nn.Conv2d(ch, ch, 3, 1, 1)
        self.c2 = nn.Conv2d(ch, ch, 3, 1, 1)
        self.act = nn.ReLU(inplace=True)

    def forward(self, x):
        return x + self.c2(self.act(self.c1(x)))


class SRNet(nn.Module):
    def __init__(self, ch=C.WIDTH, n_blocks=C.N_BLOCKS, scale=C.SCALE, bands=3):
        super().__init__()
        self.scale, self.bands = scale, bands
        self.head = nn.Conv2d(bands, ch, 3, 1, 1)
        self.act = nn.ReLU(inplace=True)
        self.body = nn.Sequential(*[ResBlock(ch) for _ in range(n_blocks)])
        self.fuse = nn.Conv2d(ch, ch, 3, 1, 1)
        self.to_shuffle = nn.Conv2d(ch, bands * scale * scale, 3, 1, 1)
        self.shuffle = nn.PixelShuffle(scale)

    def forward(self, x):
        f = self.act(self.head(x))
        f = self.fuse(self.body(f))
        residual = self.shuffle(self.to_shuffle(f))
        # Nearest-neighbour 2x upsample of the input, built from a shuffle, not a resize:
        # channels [r,r,r,r, g,g,g,g, b,b,b,b] -> each output 2x2 block is constant.
        base = self.shuffle(x.repeat_interleave(self.scale * self.scale, dim=1))
        return base + residual

    def n_params(self):
        return sum(p.numel() for p in self.parameters())


def receptive_field(model, size=97, device="cpu"):
    """MEASURED receptive field in input pixels, by gradient support.

    A unit gradient is placed on one output pixel and the number of input pixels with a
    non-zero gradient is counted. This measures the network as built, which is the point:
    the derivation in the registration is an argument, and an argument is not a measurement.
    """
    model = model.to(device).eval()
    x = torch.zeros(1, model.bands, size, size, device=device, requires_grad=True)
    y = model(x)
    g = torch.zeros_like(y)
    c = (size * model.scale) // 2
    g[0, 0, c, c] = 1.0
    y.backward(g)
    sup = (x.grad[0].abs().sum(0) > 0)
    rows = torch.nonzero(sup.any(1)).flatten()
    cols = torch.nonzero(sup.any(0)).flatten()
    h = int(rows.max() - rows.min() + 1)
    w = int(cols.max() - cols.min() + 1)
    return h, w


def mode_invariance(model, device="cpu", seed=C.TRAIN_SEED):
    """D15-C: train() and eval() must be the SAME function. Predicted max |diff| = 0.0."""
    g = torch.Generator(device="cpu").manual_seed(seed)
    x = torch.rand(2, model.bands, 64, 64, generator=g).to(device)
    model = model.to(device)
    with torch.no_grad():
        model.train(); a = model(x).clone()
        model.eval();  b = model(x).clone()
    return float((a - b).abs().max())


def mode_dependent_layers(model):
    """Every module whose behaviour differs between train() and eval(). Must be empty."""
    bad = []
    for name, m in model.named_modules():
        if isinstance(m, (nn.BatchNorm1d, nn.BatchNorm2d, nn.BatchNorm3d,
                          nn.InstanceNorm1d, nn.InstanceNorm2d, nn.InstanceNorm3d,
                          nn.Dropout, nn.Dropout1d, nn.Dropout2d, nn.Dropout3d,
                          nn.AlphaDropout, nn.SyncBatchNorm)):
            bad.append(f"{name}: {type(m).__name__}")
    return bad


def charbonnier(pred, target, eps=C.CHARBONNIER_EPS):
    """D14. L1 everywhere except within eps of zero; `- eps` makes it 0 at zero error."""
    return (torch.sqrt((pred - target) ** 2 + eps * eps) - eps).mean()
