"""The Wald degradation: MTF-matched Gaussian low-pass, then decimation by `scale`.

Every function here takes `scale`; the module-level default is `params.SCALE` (2) and is
the SCALE-2 value. A caller working at another scale must pass it explicitly - omitting it
is silent and has caused four separate defects in this project. The concrete figures in the
text below (20 m, 2 x 2) describe the scale-2 case.

**This is the one implementation.** Training imports it, the bicubic control imports it, and
the checks import it. D10 stores targets only and degrades at load time precisely so that
there is nothing for a second copy to drift away from.

It is deliberately NOT a resize. `PIL.Image.resize(..., BICUBIC)` downward, or a 2 x 2 mean,
or `scipy.ndimage.zoom`, would each apply some low-pass, but not one whose modulation at the
20 m Nyquist frequency is a stated number. The whole point of the Wald protocol is that the
degradation models the sensor, so the filter has to be specified by its MTF rather than
chosen for convenience. See `params.sigma_for_mtf` for the derivation of the sigma from
`params.MTF_AT_NYQUIST`.

Phase matters and is easy to get wrong. Decimation samples the centre of each 2 x 2 source
block, so the 20 m grid nests exactly inside the 10 m grid under the same half-pixel-centre
convention WP1's Gate S asserts. A block centre sits at a HALF-INTEGER source coordinate, so
the Gaussian is evaluated at half-integer offsets. Sampling instead at source pixels
0, 2, 4, ... - the obvious `a[::2]` - would place every 20 m sample half a 10 m pixel
north-west of where it belongs, and nothing downstream would complain: the arrays would have
the right shape, the images would look right, and the model would learn a half-pixel
translation baked into the task.
"""
from __future__ import annotations

import math

import numpy as np

from .params import (KERNEL_RADIUS_SIGMAS, MTF_AT_NYQUIST, SCALE, sigma_for_mtf)


def gaussian_decimation_kernel(sigma=None, scale=SCALE,
                               radius_sigmas=KERNEL_RADIUS_SIGMAS):
    """1-D kernel over INTEGER source offsets that samples the 2x2 block centre.

    Returns (offsets, weights). `offsets` are integers; `weights` sum to 1.

    Output sample `j` is at source coordinate `scale*j + (scale-1)/2` — the block centre.
    For scale 2 that is `2j + 0.5`. Writing the source index as `2j + o` for integer `o`,
    the Gaussian argument is `(2j + o) - (2j + 0.5) = o - 0.5`, so the weight of offset `o`
    is proportional to `exp(-0.5 * ((o - 0.5)/sigma)^2)`, independent of `j`. The kernel is
    symmetric about `o = 0.5`, which is the block centre, so the filter introduces no shift.
    """
    if sigma is None:
        sigma = sigma_for_mtf(MTF_AT_NYQUIST, scale)
    centre = (scale - 1) / 2.0
    # The window is built around the CENTRE, not around zero. Building it as
    # `arange(-r, r+1)` and then filtering by distance from the centre truncates one side
    # whenever the centre is not near 0: at scale 4 the centre is 1.5 and offset +9 lies
    # within the radius but was never a candidate, so the kernel came out asymmetric and
    # baked a -0.0011 px shift into every degraded input - the exact shift this docstring
    # promises does not exist. Scale 2 was symmetric only by arithmetic coincidence.
    # Caught by the dihedral commutation check at s=4 (max |diff| 4.03e-05), not by review.
    r = radius_sigmas * sigma
    offsets = np.arange(int(math.ceil(centre - r)), int(math.floor(centre + r)) + 1,
                        dtype=np.int64)
    d = offsets - centre
    w = np.exp(-0.5 * (d / sigma) ** 2)
    w /= w.sum()
    return offsets, w.astype(np.float64)


def _reflect_index(idx, n):
    """Reflect out-of-range indices back inside [0, n). Edge handling, stated: `reflect`
    (mirror without repeating the edge sample), which is what a physical sensor's
    neighbourhood does not do either, but which avoids inventing a dark border the way
    zero-padding would. Chips are cut whole from the granule interior, so this only affects
    the outermost few pixels of a chip."""
    idx = np.asarray(idx)
    n2 = 2 * n - 2 if n > 1 else 1
    idx = np.abs(idx) % n2
    return np.where(idx >= n, n2 - idx, idx)


def degrade(x, sigma=None, scale=SCALE):
    """Degrade `x` (..., H, W) by MTF-matched low-pass then decimation by `scale`.

    Returns (..., H//scale, W//scale), float64 internally, cast back to the input's float
    dtype. H and W must be exact multiples of `scale`.
    """
    a = np.asarray(x)
    if a.shape[-1] % scale or a.shape[-2] % scale:
        raise ValueError(
            f"degrade: last two dims {a.shape[-2:]} must be multiples of scale {scale}")
    off, w = gaussian_decimation_kernel(sigma, scale)
    h, wd = a.shape[-2], a.shape[-1]
    oh, ow = h // scale, wd // scale
    src = a.astype(np.float64)

    # separable: rows first, then columns
    j = np.arange(oh) * scale
    rows = np.zeros(a.shape[:-2] + (oh, wd), np.float64)
    for o, k in zip(off, w):
        rows += k * src[..., _reflect_index(j + o, h), :]
    j = np.arange(ow) * scale
    out = np.zeros(a.shape[:-2] + (oh, ow), np.float64)
    for o, k in zip(off, w):
        out += k * rows[..., :, _reflect_index(j + o, wd)]

    dt = a.dtype if a.dtype.kind == "f" else np.float32
    return out.astype(dt)


def area_average(x, scale=SCALE):
    """Plain 2x2 (scale x scale) block mean. NOT the degradation.

    Present only so the checks can assert that `degrade` differs from it. If the MTF filter
    were ever silently replaced by a resize, this is what it would collapse to, and every
    number in the work package would still be produced and would still look reasonable.
    """
    a = np.asarray(x).astype(np.float64)
    h, w = a.shape[-2], a.shape[-1]
    a = a.reshape(a.shape[:-2] + (h // scale, scale, w // scale, scale))
    out = a.mean(axis=(-3, -1))
    dt = np.asarray(x).dtype
    return out.astype(dt if dt.kind == "f" else np.float32)


def degrade_chip(target_dn, norm_divisor, sigma=None, scale=SCALE):
    """The dataloader entry point: stored uint16 DN target -> (input, target) normalised.

    `target_dn` is (B, 256, 256) uint16 as stored, B = 3 at scale 2 and 4 at scale 4.
    Returns (input (B, 256/scale, 256/scale) float32, target (B,256,256) float32),
    both in normalised units
    `DN / norm_divisor`. Normalisation is applied BEFORE the filter, which is equivalent
    because both are linear, and is done in this order so nothing downstream ever handles
    a DN-valued float that could be mistaken for a normalised one.
    """
    t = np.asarray(target_dn, np.float32) / np.float32(norm_divisor)
    return degrade(t, sigma=sigma, scale=scale).astype(np.float32), t


def mtf_at(f, sigma=None, scale=SCALE):
    """Modulation of the Gaussian at frequency `f` in cycles per source pixel.

    Exposed so a check can assert the filter is the one the registration names, instead of
    trusting that the sigma was derived correctly.
    """
    if sigma is None:
        sigma = sigma_for_mtf(MTF_AT_NYQUIST, scale)
    return math.exp(-2.0 * math.pi ** 2 * sigma ** 2 * f ** 2)
