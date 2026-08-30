"""The upsampler seam, and bicubic as its first implementation.

This interface is the point a trained ONNX model plugs into in WP4, so it is deliberately
one method and nothing else:

    upsample(arr: H x W x C) -> sH x sW x C, same dtype

No registry, no factory, no configuration object. A second implementation is a class that
subclasses `Upsampler`; the caller chooses it, not a lookup table.

------------------------------------------------------------------------------------
WHY PIL, AND NOT scipy.ndimage.zoom
------------------------------------------------------------------------------------
Super-resolution's whole content is a coordinate convention, so the resampler was chosen by
measurement rather than by availability. A linear ramp is reproduced exactly by cubic
convolution in the interior, so the output values identify the convention unambiguously.
Measured 2026-08-30, PIL 12.3.0 / scipy 1.17.1 / numpy 2.4.6, upsampling a 12-wide ramp by
2 and comparing the interior against the two candidate conventions:

    PIL BICUBIC          vs half-pixel centres  : max |diff| = 0.000e+00
    PIL BICUBIC          vs align-corners       : max |diff| = 1.630e-01
    scipy zoom (default) vs half-pixel centres  : max |diff| = 1.701e-01   <- WRONG
    scipy zoom (default) vs align-corners       : max |diff| = 1.220e-02
    scipy zoom grid_mode=True vs half-pixel     : max |diff| = 1.133e-02

`scipy.ndimage.zoom`'s default `grid_mode=False` uses the align-corners convention, which
puts a half-pixel shift into every output — a shift that would be invisible in any
generated-vs-target metric and would silently contradict Gate S assertion S5. Even
`grid_mode=True` does not reproduce the ramp exactly, because scipy's `order=3` is an
interpolating B-spline, not cubic convolution.

PIL's half-pixel-centre convention is exactly the geometry `sr_core.grid` asserts:
output pixel `k` samples source coordinate `(k + 0.5)/s - 0.5`, which maps the centre of
source pixel `(i, j)` onto the centre of its `s x s` output block. It is also already
present inside QGIS's bundled Python, which matters for WP2.

------------------------------------------------------------------------------------
CLIPPING — A DOCUMENTED CHOICE, NOT AN IMPLICIT ONE
------------------------------------------------------------------------------------
Cubic convolution has negative kernel lobes and overshoots at sharp edges: upsampling a
uint8 raster produces values below 0 and above 255 next to any hard boundary.

**This implementation CLIPS to the source dtype's range for integer dtypes**, and does not
clip floating-point dtypes (where the dtype range carries no physical meaning). The reason
is that the alternative is worse in a specific way: an unclipped float cast back to uint8
WRAPS, so an overshoot to 257 becomes 1 — a black pixel at the brightest edge in the
scene, which reads as data rather than as an artefact. Clipping loses the overshoot;
wrapping invents a value. Clipping is the lesser harm and is the only one of the two that
is visible as saturation rather than as content.

What is lost is stated rather than hidden: clipped pixels are counted. `n_clipped` and
`n_total` accumulate across every call, so a run can report the exact fraction of output
pixels whose value was altered by this decision instead of asserting it is negligible.

------------------------------------------------------------------------------------
NODATA
------------------------------------------------------------------------------------
This upsampler is nodata-blind. It interpolates the raw array it is given, so at a nodata
boundary the fill value is mixed into neighbouring valid pixels over the kernel support.
The five TCI scenes in the inventory use nodata = 0, and two of them (36SWJ, 36TUK) carry
substantial nodata. This is a real, unaddressed limitation of WP1, recorded as an open
item, not silently handled.
"""
from __future__ import annotations

import numpy as np

_INT_KINDS = "iub"


class Upsampler:
    """The seam. One method; subclasses override `upsample` and nothing else.

    Attributes:
        scale      integer factor; an implementation must honour it exactly
        name       short identifier, recorded in the output's provenance tag
        n_clipped  output values altered by range clipping, cumulative across calls
        n_total    output values produced, cumulative across calls

    `n_clipped` and `n_total` are part of the INTERFACE, not of the bicubic
    implementation, and they default to 0 so an implementation that clips nothing needs no
    code for them. They live here because of a defect this arrangement already caught: the
    pipeline reads them when it writes the provenance record, and while they were
    `BicubicUpsampler` attributes, substituting ANY other upsampler failed immediately with
    `AttributeError: 'X' object has no attribute 'n_clipped'` — before a single tile was
    processed. It was found by running the pipeline against a stub with a trained ONNX
    model's constraints (static input shape, fixed channel count), which is the WP4 swap in
    miniature.
    """

    scale = 1
    name = "identity"
    n_clipped = 0
    n_total = 0

    def upsample(self, arr):
        """H x W x C -> (scale*H) x (scale*W) x C, same dtype. Override this."""
        raise NotImplementedError


class BicubicUpsampler(Upsampler):
    """Bicubic (cubic-convolution) upsampling on the half-pixel-centre convention, via PIL.

    Deliberately NOT `gencp_core.infer.preprocess`. That function bicubic-resizes its input
    to 256 px because pix2pix consumes a 257 px render at 256 px, which is correct there and
    destructive here: in super-resolution the resampling is precisely what the model must
    learn, so pre-resizing the input both removes the problem and leaves output that still
    looks plausible and still scores plausibly. Nothing in this module calls it.
    """

    name = "bicubic"

    def __init__(self, scale=2, clip=True):
        from .grid import require_integer_scale
        self.scale = require_integer_scale(scale, "BicubicUpsampler")
        self.clip = bool(clip)
        self.n_clipped = 0
        self.n_total = 0

    def upsample(self, arr):
        from PIL import Image
        a = np.asarray(arr)
        if a.ndim != 3:
            raise ValueError(
                f"upsample expects H x W x C, got shape {a.shape}. A single-band array "
                "must be passed as H x W x 1 rather than H x W, so that the band axis is "
                "never inferred.")
        h, w, c = a.shape
        if h < 1 or w < 1 or c < 1:
            raise ValueError(f"upsample: empty array, shape {a.shape}")
        s = self.scale
        dt = a.dtype
        if s == 1:
            return a.copy()

        out = np.empty((h * s, w * s, c), np.float32)
        for b in range(c):
            im = Image.fromarray(np.ascontiguousarray(a[..., b], dtype=np.float32))
            out[..., b] = np.asarray(
                im.resize((w * s, h * s), Image.Resampling.BICUBIC), np.float32)

        self.n_total += out.size
        if dt.kind in _INT_KINDS:
            lo, hi = np.iinfo(dt).min, np.iinfo(dt).max
            if self.clip:
                self.n_clipped += int(np.count_nonzero((out < lo) | (out > hi)))
                np.clip(out, lo, hi, out=out)
            # Round half away from zero before the integer cast: a bare astype() truncates
            # toward zero, which biases every interpolated value downward by up to 1 DN.
            return np.rint(out).astype(dt)
        return out.astype(dt)
