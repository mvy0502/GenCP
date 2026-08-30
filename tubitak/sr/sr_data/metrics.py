"""PSNR, SSIM and MAE, in normalised reflectance, with one stated convention.

**Domain.** Every function here takes float arrays in NORMALISED REFLECTANCE
(`DN / params.NORM_DIVISOR_DN`, dimensionless, nominal full scale 1.0). Not DN, not 8-bit.
Passing DN would give a PSNR about 74 dB higher and an MAE 5000x larger, both of which look
like plausible numbers, which is exactly why the domain is named in the registration and
restated here.

**Convention, once.** Each function returns a PER-CHIP value. The reported figure for a
split is the UNWEIGHTED ARITHMETIC MEAN of the per-chip values over that split - never a
pooled statistic over all pixels of the split. A pooled MSE lets one bad chip dominate; a
per-chip mean weights every scene equally, which is the question being asked.

**SSIM.** `scikit-image` is not installed in this environment and this work package installs
nothing, so SSIM is implemented here to Wang et al. (2004): an 11 x 11 Gaussian window with
sigma 1.5, K1 = 0.01, K2 = 0.03, computed per band and averaged over bands. It is validated
against its own known-true and known-false cases in
`sr_data/checks/`, which is weaker than a cross-implementation comparison and is reported as
such rather than presented as equivalent.
"""
from __future__ import annotations

import numpy as np
from scipy.ndimage import gaussian_filter

SSIM_SIGMA = 1.5
SSIM_TRUNCATE = 3.5      # 11x11 window: radius = round(3.5 * 1.5) = 5 -> 11 taps
SSIM_K1, SSIM_K2 = 0.01, 0.03


def mse_chip(pred, target):
    d = np.asarray(pred, np.float64) - np.asarray(target, np.float64)
    return float(np.mean(d * d))


def psnr_chip(pred, target, data_range=1.0):
    """PSNR in dB for one chip, over all its values at once (not per band then averaged)."""
    m = mse_chip(pred, target)
    if m == 0.0:
        return float("inf")
    return float(10.0 * np.log10((data_range ** 2) / m))


def mae_chip(pred, target):
    return float(np.mean(np.abs(np.asarray(pred, np.float64)
                                - np.asarray(target, np.float64))))


def _ssim_plane(a, b, data_range):
    a = np.asarray(a, np.float64)
    b = np.asarray(b, np.float64)
    c1 = (SSIM_K1 * data_range) ** 2
    c2 = (SSIM_K2 * data_range) ** 2
    kw = dict(sigma=SSIM_SIGMA, truncate=SSIM_TRUNCATE, mode="reflect")
    mu_a = gaussian_filter(a, **kw)
    mu_b = gaussian_filter(b, **kw)
    saa = gaussian_filter(a * a, **kw) - mu_a * mu_a
    sbb = gaussian_filter(b * b, **kw) - mu_b * mu_b
    sab = gaussian_filter(a * b, **kw) - mu_a * mu_b
    num = (2 * mu_a * mu_b + c1) * (2 * sab + c2)
    den = (mu_a ** 2 + mu_b ** 2 + c1) * (saa + sbb + c2)
    return float(np.mean(num / den))


def ssim_chip(pred, target, data_range=1.0):
    """Mean over bands of the per-band SSIM. `pred`/`target` are (C, H, W)."""
    p = np.asarray(pred)
    t = np.asarray(target)
    if p.ndim != 3 or t.ndim != 3:
        raise ValueError(f"ssim_chip expects (C, H, W), got {p.shape} and {t.shape}")
    return float(np.mean([_ssim_plane(p[c], t[c], data_range) for c in range(p.shape[0])]))


def summarise(per_chip):
    """Mean, standard deviation and n of a list of per-chip values.

    Infinities (a PSNR of a perfect chip) are excluded from the mean and counted separately,
    rather than propagating to make the whole split's mean infinite.
    """
    v = np.asarray(per_chip, np.float64)
    finite = np.isfinite(v)
    return dict(mean=float(v[finite].mean()) if finite.any() else float("nan"),
                std=float(v[finite].std(ddof=1)) if finite.sum() > 1 else 0.0,
                n=int(v.size), n_nonfinite=int((~finite).sum()))
