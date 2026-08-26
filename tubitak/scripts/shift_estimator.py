#!/usr/bin/env python
"""Subpixel translation estimation between two rasters.

Phase correlation with upsampled-DFT refinement (Guizar-Sicairos et al.,
*Opt. Lett.* **33**, 156, 2008), implemented directly on NumPy so the analysis
carries no dependency beyond what the GenCP environment already provides.

This is the measurement primitive behind the 257->256 geometry investigation
(see ``tubitak/docs/geometry-finding.md``) and is intended for reuse during
KARIOS validation.

Two representations are supported:

``intensity``
    Raw (mean-of-bands) pixel values. Correct when both images are the same
    modality — e.g. an OSM raster against the same OSM raster resampled.

``gradient``
    Sobel gradient magnitude of a lightly smoothed image. Use this when the two
    images are *different modalities* (categorical OSM colours vs continuous
    satellite texture), where raw intensities are uncorrelated but edges — roads,
    field boundaries, water margins — survive in both.

Run the built-in validation harness before trusting any number this produces:

    python tubitak/scripts/shift_estimator.py --self-test
"""
from __future__ import annotations

import argparse
import sys

import numpy as np

__all__ = ["phase_shift", "ncc_shift", "edge_representation", "prepare", "self_test"]


# --------------------------------------------------------------------------- #
# core estimator
# --------------------------------------------------------------------------- #
def _upsampled_dft(data, ups_size, upsample_factor, axis_offsets):
    """Local upsampled inverse DFT around an integer peak (matrix-multiply form)."""
    im2pi = 1j * 2 * np.pi
    for (n_items, ax_offset) in list(zip(data.shape, axis_offsets))[::-1]:
        kernel = ((np.arange(ups_size) - ax_offset)[:, None]
                  * np.fft.fftfreq(n_items, upsample_factor))
        kernel = np.exp(-im2pi * kernel)
        data = np.tensordot(kernel, data, axes=(1, -1))
    return data


def phase_shift(ref, mov, upsample: int = 100, window: bool = True):
    """Estimate the translation between ``ref`` and ``mov``.

    Both arrays must be 2-D and the same shape.

    Returns
    -------
    (dy, dx, confidence)
        ``dy``/``dx`` are in pixels. **Sign convention:** positive means the
        content of ``mov`` sits at LARGER row/column indices than the same
        content in ``ref``. ``confidence`` is the correlation peak height
        normalised by the mean of the surface; values below ~8 indicate a
        window too flat to register (returns NaN shifts if effectively constant).
    """
    ref = np.asarray(ref, dtype=float)
    mov = np.asarray(mov, dtype=float)
    if ref.shape != mov.shape:
        raise ValueError(f"shape mismatch: {ref.shape} vs {mov.shape}")

    ref = ref - ref.mean()
    mov = mov - mov.mean()
    if ref.std() < 1e-8 or mov.std() < 1e-8:
        return np.nan, np.nan, 0.0

    if window:
        w = np.outer(np.hanning(ref.shape[0]), np.hanning(ref.shape[1]))
        ref = ref * w
        mov = mov * w

    F = np.fft.fft2(ref)
    G = np.fft.fft2(mov)
    prod = G * F.conj()
    mag = np.abs(prod)
    mag[mag < 1e-12] = 1e-12
    prod_n = prod / mag                      # phase correlation

    acc = np.abs(np.fft.ifft2(prod_n))
    peak = np.unravel_index(np.argmax(acc), acc.shape)
    conf = float(acc[peak] / (acc.mean() + 1e-12))

    shifts = np.array(peak, dtype=float)
    shape = np.array(ref.shape, dtype=float)
    shifts[shifts > shape // 2] -= shape[shifts > shape // 2]

    if upsample > 1:
        shifts = np.round(shifts * upsample) / upsample
        ups_size = int(np.ceil(upsample * 1.5))
        dftshift = np.fix(ups_size / 2.0)
        offsets = dftshift - shifts * upsample
        fine = _upsampled_dft(prod_n.conj(), ups_size, upsample, offsets).conj()
        fp = np.unravel_index(np.argmax(np.abs(fine)), fine.shape)
        shifts = shifts + (np.array(fp, dtype=float) - dftshift) / upsample

    return float(shifts[0]), float(shifts[1]), conf


# --------------------------------------------------------------------------- #
# cross-modal estimator
# --------------------------------------------------------------------------- #
def ncc_shift(ref, mov, max_shift: int = 8):
    """Normalised cross-correlation with a bounded search and parabolic subpixel fit.

    Unlike :func:`phase_shift`, the spectrum is **not** whitened. Phase whitening
    sharpens the peak for same-modality pairs but is fragile across modalities,
    where it locks onto spurious peaks (measured: errors of 40-60 px between OSM
    and generated imagery). Plain NCC has a broader peak but is far more robust
    there.

    ``max_shift`` bounds the search to +/- that many pixels. This is a genuine
    limitation, not a formality: a displacement larger than ``max_shift`` cannot
    be detected and will saturate. State the bound whenever you report a result.

    Returns ``(dy, dx, confidence)`` with the same sign convention as
    :func:`phase_shift`.
    """
    a = np.asarray(ref, dtype=float)
    b = np.asarray(mov, dtype=float)
    if a.shape != b.shape:
        raise ValueError(f"shape mismatch: {a.shape} vs {b.shape}")
    w = np.outer(np.hanning(a.shape[0]), np.hanning(a.shape[1]))
    a = (a - a.mean()) * w
    b = (b - b.mean()) * w
    sa, sb = a.std(), b.std()
    if sa < 1e-8 or sb < 1e-8:
        return np.nan, np.nan, 0.0

    cc = np.fft.ifft2(np.fft.fft2(b) * np.conj(np.fft.fft2(a))).real / (a.size * sa * sb)
    cc = np.fft.fftshift(cc)
    cy, cx = np.array(cc.shape) // 2
    r = int(max_shift)
    sub = cc[cy - r:cy + r + 1, cx - r:cx + r + 1]
    pk = np.unravel_index(np.argmax(sub), sub.shape)

    def _par(v0, v1, v2):
        d = v0 - 2 * v1 + v2
        return 0.0 if abs(d) < 1e-12 else 0.5 * (v0 - v2) / d

    dy = dx = 0.0
    if 0 < pk[0] < sub.shape[0] - 1:
        dy = _par(sub[pk[0] - 1, pk[1]], sub[pk[0], pk[1]], sub[pk[0] + 1, pk[1]])
    if 0 < pk[1] < sub.shape[1] - 1:
        dx = _par(sub[pk[0], pk[1] - 1], sub[pk[0], pk[1]], sub[pk[0], pk[1] + 1])
    conf = float(sub[pk] / (np.abs(sub).mean() + 1e-12))
    return float((pk[0] - r) + dy), float((pk[1] - r) + dx), conf


# --------------------------------------------------------------------------- #
# representations
# --------------------------------------------------------------------------- #
def edge_representation(img, sigma: float = 1.0):
    """Sobel gradient magnitude of a Gaussian-smoothed image.

    Cross-modal registration handle: two images of the same scene in different
    modalities share edge *locations* even when their intensities are unrelated.
    """
    from scipy.ndimage import gaussian_filter, sobel

    a = np.asarray(img, dtype=float)
    if a.ndim == 3:
        a = a.mean(axis=2)
    a = gaussian_filter(a, sigma)
    gy = sobel(a, axis=0)
    gx = sobel(a, axis=1)
    return np.hypot(gy, gx)


def prepare(img, mode: str = "intensity", sigma: float = 1.0):
    """Convert an image to the representation used for correlation."""
    if mode == "gradient":
        return edge_representation(img, sigma=sigma)
    if mode == "intensity":
        a = np.asarray(img, dtype=float)
        return a.mean(axis=2) if a.ndim == 3 else a
    raise ValueError(f"unknown mode {mode!r} (expected 'intensity' or 'gradient')")


# --------------------------------------------------------------------------- #
# validation harness
# --------------------------------------------------------------------------- #
#: (dy, dx) test shifts — the table reproduced in geometry-finding.md section 2.
SELF_TEST_SHIFTS = [
    (0.00, 0.00), (0.13, 0.13), (0.38, 0.38), (0.63, 0.63),
    (0.88, 0.88), (1.00, 0.00), (-0.50, 0.75), (2.25, -1.40),
]


def _synthetic(seed: int = 0, n: int = 96):
    """Textured test image with blocky structure, similar in character to an OSM chip."""
    from scipy.ndimage import gaussian_filter

    rng = np.random.default_rng(seed)
    base = gaussian_filter(rng.normal(0, 1, (n, n)), 1.5)
    base += (np.add.outer(np.arange(n) // 12, np.arange(n) // 12) % 2) * 2.0
    return base


def self_test(mode: str = "intensity", tol: float = 0.25, verbose: bool = True) -> bool:
    """Recover known sub-pixel shifts. Returns True if max error < ``tol`` px."""
    from scipy.ndimage import shift as ndshift

    base = _synthetic()
    if verbose:
        print(f"VALIDATION — recover known sub-pixel shifts (mode={mode})")
        print(f"{'true dy':>9}{'true dx':>9}{'est dy':>9}{'est dx':>9}{'err dy':>9}{'err dx':>9}")
        print("-" * 54)

    errs = []
    for tdy, tdx in SELF_TEST_SHIFTS:
        moved = ndshift(base, (tdy, tdx), order=3, mode="reflect")
        a, b = prepare(base, mode), prepare(moved, mode)
        dy, dx, _ = phase_shift(a, b)
        errs.append((dy - tdy, dx - tdx))
        if verbose:
            print(f"{tdy:>9.2f}{tdx:>9.2f}{dy:>9.3f}{dx:>9.3f}{dy - tdy:>9.3f}{dx - tdx:>9.3f}")

    e = np.abs(np.array(errs))
    rms = float(np.sqrt((e ** 2).mean()))
    mx = float(e.max())
    if verbose:
        print("-" * 54)
        print(f"max abs error: {mx:.4f} px   RMS error: {rms:.4f} px")
        print(f"result: {'PASS' if mx < tol else 'FAIL'} (tolerance {tol} px)")
        print("\nsign convention: positive dy/dx means `mov` content sits at LARGER")
        print("row/column indices than the same content in `ref`.")
    return mx < tol


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--self-test", action="store_true", help="run the validation harness")
    p.add_argument("--mode", default="intensity", choices=["intensity", "gradient"])
    p.add_argument("--tol", type=float, default=0.25, help="pass tolerance in px")
    a = p.parse_args()
    if not a.self_test:
        p.print_help()
        return 0
    return 0 if self_test(mode=a.mode, tol=a.tol) else 1


if __name__ == "__main__":
    sys.exit(main())
