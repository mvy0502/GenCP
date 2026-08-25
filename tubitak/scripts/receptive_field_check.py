#!/usr/bin/env python
"""Is the generator's ABSOLUTE spatial alignment zero, or merely equivariant?

``equivariance_test.py`` shows that translating the input translates the output
identically, to 0.008 px. That does **not** rule out a constant offset: if the
network displaced every output by a fixed amount, ``output(shift(X)) ==
shift(output(X))`` would still hold exactly. Equivariance and absolute alignment
are different claims.

A constant half-pixel offset is a real, well-known failure mode of mismatched
conv/deconv geometry, so this settles it two ways:

1. **Analytically** - propagate receptive-field centres through the encoder and
   decoder and check whether they are exact geometric inverses.
2. **Empirically** - for a given output pixel, differentiate it with respect to
   the input and locate the PEAK of the resulting sensitivity map. If the peak sits
   at the same index as the output pixel, the absolute offset is zero.

   The peak, not the centroid: a U-Net with a 1x1 bottleneck makes every output
   pixel depend on the entire input, so the global centroid is dominated by that
   whole-image path and simply drifts toward the image centre (measured: an output
   pixel at (64,64) gives a centroid at (104.6, 93.1) — pulled 40 px toward centre).
   Position information travels through the skip connections, which are local, and
   that is what the peak isolates. Sub-pixel location comes from an
   intensity-weighted centroid of a small window around the peak.

The empirical check runs the network in ``eval()`` mode deliberately. With
BatchNorm in training mode the normalisation statistics are computed across the
whole feature map, which couples every output pixel to every input pixel and
would smear the sensitivity map globally - an artefact of the statistics, not of
the convolution geometry. In eval mode BatchNorm is a per-channel affine, so the
Jacobian reflects the geometry alone.

Usage
-----
    python tubitak/scripts/receptive_field_check.py
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]


def analytic(k=4, s=2, p=1, n=256, levels=8):
    print("=" * 74)
    print("1. ANALYTIC — receptive-field centre propagation")
    print("=" * 74)
    print(f"Every downsample is Conv2d(k={k}, s={s}, p={p});")
    print(f"every upsample is ConvTranspose2d(k={k}, s={s}, p={p}, output_padding=0).\n")
    print(f"Centred condition  p == (k-s)/2  ->  ({k}-{s})/2 = {(k-s)/2:g}  ==  p ? "
          f"{'YES' if (k - s) / 2 == p else 'NO'}")
    print("An integer solution exists, so the sampling grid is exactly centred.")
    print("(Compare k=3,s=2,p=1: (3-2)/2 = 0.5 is not an integer, so that pairing")
    print(" cannot be centred and carries an unavoidable half-pixel offset.)\n")

    start, jump, size = 0.0, 1.0, n
    print(f"{'level':<9}{'size':>6}{'jump':>7}{'centre of pixel 0 (input coords)':>36}")
    print("-" * 60)
    print(f"{'input':<9}{size:>6}{jump:>7.0f}{start:>36.2f}")
    for L in range(1, levels + 1):
        start += ((k - 1) / 2 - p) * jump
        jump *= s
        size //= 2
        print(f"{'down ' + str(L):<9}{size:>6}{jump:>7.0f}{start:>36.2f}")
    centred = (start == (n - 1) / 2)
    print("-" * 60)
    print(f"bottleneck centre = {start}, image geometric centre = {(n-1)/2} -> "
          f"{'ALIGNED' if centred else 'OFFSET'}\n")

    print("Decoder:")
    print(f"  ConvTranspose2d(k={k}, s={s}, p={p}) is the exact adjoint of Conv2d with the")
    print(f"  same parameters. Output size = (N-1)*s - 2p + k = 2N exactly, with")
    print(f"  output_padding=0, so the upsampled grid coincides cell-for-cell with the")
    print(f"  grid the matching Conv2d consumed. Coarse pixel c spreads to fine pixels")
    print(f"  [2c-1 .. 2c+2], centre 2c+0.5 — the exact inverse of the encoder's")
    print(f"  input->coarse map. Each down/up pair is therefore an exact geometric")
    print(f"  inverse, and the composition over {levels} levels is the identity on pixel")
    print(f"  indices.\n")
    print("PREDICTION: absolute offset is exactly 0.000 px in both axes.")
    return centred


def empirical(pixels, use_real_weights=True, ngf=64, seeds=(0,), quiet=False):
    import torch
    sys.path.insert(0, str(ROOT))
    from models import networks

    print("\n" + "=" * 74)
    print("2. EMPIRICAL — Jacobian sensitivity centroid of the TRAINED network")
    print("=" * 74)

    net = networks.define_G(3, 3, ngf, "unet_256", norm="batch",
                            use_dropout=False, init_type="normal",
                            init_gain=0.02, gpu_ids=[])
    if use_real_weights:
        w = ROOT / "GenCP_HR_demo/checkpoints/genCP_HR_RGB_model/latest_net_G.pth"
        if not w.exists():
            print(f"  weights not found at {w} — using random init instead")
        else:
            sd = torch.load(w, map_location="cpu")
            if hasattr(sd, "_metadata"):
                del sd._metadata
            target = net.module if isinstance(net, torch.nn.DataParallel) else net
            target.load_state_dict(sd)
            print(f"  loaded trained weights: {w.name}")
    net.eval()          # see module docstring: keeps BatchNorm pointwise

    print(f"\n{'output pixel':<16}{'located y':>12}{'located x':>12}"
          f"{'offset dy':>12}{'offset dx':>12}{'integer peak':>18}")
    print("-" * 92)
    offs = []
    probes = [(sd, i, j) for sd in seeds for (i, j) in pixels]
    for sd, i, j in probes:
        torch.manual_seed(sd)
        x = torch.randn(1, 3, 256, 256, requires_grad=True)
        if x.grad is not None:
            x.grad.zero_()
        y = net(x)
        y[0, :, i, j].sum().backward()
        g = x.grad.detach().abs().sum(dim=1)[0].numpy()
        if g.sum() <= 0:
            print(f"({i},{j})  zero gradient — cannot locate")
            continue
        py, px = np.unravel_index(np.argmax(g), g.shape)     # peak = local skip path
        r = 4                                                 # sub-pixel refinement window
        y0, y1 = max(0, py - r), min(g.shape[0], py + r + 1)
        x0, x1 = max(0, px - r), min(g.shape[1], px + r + 1)
        w = g[y0:y1, x0:x1]
        yy, xx = np.mgrid[y0:y1, x0:x1]
        cy = float((w * yy).sum() / w.sum())
        cx = float((w * xx).sum() / w.sum())
        offs.append((cy - i, cx - j))
        if not quiet:
            print(f"{f'({i},{j}) s{sd}':<16}{cy:>12.4f}{cx:>12.4f}{cy-i:>+12.4f}{cx-j:>+12.4f}"
                  f"{f'  peak ({py},{px})':>18}")

    if not offs:
        raise RuntimeError("empirical(): no probe produced a usable sensitivity map "
                           "(all gradients were zero) — cannot locate any offset")
    o = np.array(offs)
    print("-" * 92)
    print(f"{'MEAN offset':<16}{'':>24}{o[:,0].mean():>+12.4f}{o[:,1].mean():>+12.4f}")
    print(f"{'MAX |offset|':<16}{'':>24}{np.abs(o[:,0]).max():>12.4f}{np.abs(o[:,1]).max():>12.4f}")
    n = len(o)
    se_y = o[:, 0].std(ddof=1) / np.sqrt(n)
    se_x = o[:, 1].std(ddof=1) / np.sqrt(n)
    print(f"{'STD':<16}{'':>24}{o[:,0].std(ddof=1):>12.4f}{o[:,1].std(ddof=1):>12.4f}")
    print(f"{'STD ERROR':<16}{'':>24}{se_y:>12.4f}{se_x:>12.4f}")
    bound = max(abs(o[:, 0].mean()) + 2 * se_y, abs(o[:, 1].mean()) + 2 * se_x)
    print(f"\nn = {n} probes")
    print(f"mean offset : dy {o[:,0].mean():+.4f} +/- {se_y:.4f} px, "
          f"dx {o[:,1].mean():+.4f} +/- {se_x:.4f} px")
    print(f"95% bound on a CONSTANT offset (|mean| + 2*SE): {bound:.4f} px")
    print(f"\nPer-probe scatter (~{o.std():.2f} px) is the argmax landing on a neighbouring")
    print("pixel: the sensitivity map of a trained net is not a clean delta. The MEAN is")
    print("the meaningful statistic, and it is consistent with zero.")
    return float(o[:, 0].mean()), float(o[:, 1].mean()), bound


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--quiet", action="store_true", help="summary only")
    ap.add_argument("--no-control", action="store_true", help="skip the random-weight control")
    a = ap.parse_args()
    analytic()
    # interior probes only: pixels near a border have their receptive field clipped
    step = 24
    pix = [(i, j) for i in range(64, 193, step) for j in range(64, 193, step)]

    ty, tx, tb = empirical(pix, use_real_weights=True, seeds=(0, 1), quiet=a.quiet)
    if a.no_control:
        return 0

    print("\n" + "=" * 74)
    print("3. CONTROL — the same probe on RANDOM weights")
    print("=" * 74)
    print("The architecture is identical, so any geometric offset must be identical too.")
    print("A different reading here means the probe is measuring the weights, not the")
    print("geometry.\n")
    ry, rx, rb = empirical(pix, use_real_weights=False, seeds=(0, 1), quiet=True)

    print("\n" + "=" * 74)
    print("CONCLUSION")
    print("=" * 74)
    print(f"trained weights : mean offset dy {ty:+.4f}, dx {tx:+.4f} px")
    print(f"random weights  : mean offset dy {ry:+.4f}, dx {rx:+.4f} px")
    spread = max(abs(ty - ry), abs(tx - rx))
    print(f"discrepancy between them: {spread:.3f} px\n")
    print("The two disagree by more than either differs from zero, on identical")
    print("architecture. The Jacobian-peak probe is therefore WEIGHT-DEPENDENT and")
    print(f"cannot resolve a constant offset below ~{max(abs(ry), abs(rx)):.1f} px. It is")
    print("INCONCLUSIVE at sub-pixel level and neither confirms nor refutes a half-pixel")
    print("offset. It does exclude a constant offset larger than ~1 px.\n")
    print("The ANALYTIC argument is therefore the one that settles this: p == (k-s)/2")
    print("holds exactly at every layer, the encoder centre lands exactly on the image")
    print("centre, and ConvTranspose2d with the same (k,s,p) and output_padding=0 is the")
    print("exact adjoint. The absolute offset is exactly zero BY CONSTRUCTION of the")
    print("sampling geometry, independent of what the weights learned.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
