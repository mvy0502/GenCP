"""The trained model as an `sr_core.upsample.Upsampler`, plus input validation.

Two jobs, kept in one file because they share the model's provenance:

1. `OnnxUpsampler` - runs the ONNX graph tile by tile through the same seam the bicubic
   baseline uses, so `sr_core.run.superresolve` needs no knowledge of models.
2. `validate_input` - refuses a raster the model was not trained for, BEFORE any tile runs.

**Nothing here carries a normalisation constant, a scale factor or a channel count as a
literal.** All three are read from the ONNX file's own `metadata_props`, which
`export_onnx.py` wrote at export time. A plugin that hard-coded `5000.0` would keep working
and be silently wrong the day a model is retrained with a different divisor - and the output
would look entirely plausible, which is this project's dominant failure class.

`onnxruntime` is imported LAZILY, inside the constructor. The bicubic path must keep loading
and running on a machine where onnxruntime cannot be imported at all (WP2B 4.1).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

#: Keys the plugin requires the model to declare. A model without them is refused rather
#: than run under guessed defaults.
REQUIRED_META = ("norm_divisor_dn", "scale_factor", "in_channels", "band_order")


class ModelInputError(ValueError):
    """The raster is not something this model can be run on. Carries a Turkish message."""

    def __init__(self, key, **fmt):
        self.key, self.fmt = key, fmt
        super().__init__(f"{key}: {fmt}")


def read_provenance(model_path):
    """The model's declared contract, from its own metadata. Lazily imports onnxruntime."""
    import onnxruntime as ort
    sess = ort.InferenceSession(str(model_path), providers=["CPUExecutionProvider"])
    md = dict(sess.get_modelmeta().custom_metadata_map)
    missing = [k for k in REQUIRED_META if k not in md]
    if missing:
        raise ModelInputError("err_model_meta", missing=", ".join(missing),
                              name=Path(model_path).name)
    return sess, dict(
        norm_divisor_dn=float(md["norm_divisor_dn"]),
        scale=int(md["scale_factor"]),
        in_channels=int(md["in_channels"]),
        band_order=md["band_order"],
        corpus_id=md.get("corpus_id", "?"),
        completed_steps=md.get("completed_steps", "?"),
        registered_schedule_steps=md.get("registered_schedule_steps", "?"),
        infer_tile_src_px=int(md.get("infer_tile_src_px", 128)),
        infer_overlap_src_px=int(md.get("infer_overlap_src_px", 32)),
        raw=md)


def validate_input(raster_path, prov, sample_px=1024):
    """Assert the raster matches the model's declared contract. Raises ModelInputError.

    This is the check that stops the plugin producing plausible garbage from the wrong file.
    The specific case it exists for: the 8-bit TCI visual composite. It has three bands, so
    a band-count check alone lets it through; what separates it is the DTYPE, and, for a TCI
    that someone has converted to 16-bit, the VALUE RANGE.
    """
    import rasterio
    with rasterio.open(str(raster_path)) as d:
        count, dtype = d.count, d.dtypes[0]
        w, h = d.width, d.height
        if count != prov["in_channels"]:
            raise ModelInputError("err_bands", got=count, want=prov["in_channels"],
                                  order=prov["band_order"])
        if dtype != "uint16":
            raise ModelInputError("err_dtype", got=dtype, want="uint16",
                                  bands=count, order=prov["band_order"])
        # A TCI converted to uint16 keeps 0..255 values. Reflectance DN over land runs to
        # several thousand (WP2A: pooled p99.9 of 4084/4663/5029 DN). Sampling a window
        # rather than the whole raster keeps this cheap enough to run before every job.
        c0, r0 = max(0, (w - sample_px) // 2), max(0, (h - sample_px) // 2)
        win = rasterio.windows.Window(c0, r0, min(sample_px, w), min(sample_px, h))
        a = d.read(window=win)
        hi = float(np.percentile(a[a > 0], 99.9)) if (a > 0).any() else 0.0
        if hi < 300.0:
            raise ModelInputError("err_range", p999=hi, order=prov["band_order"])
    return dict(count=count, dtype=dtype, width=w, height=h, sample_p999=hi)


class OnnxUpsampler:
    """`sr_core.upsample.Upsampler`-compatible wrapper around the trained graph.

    The interface contract (`sr_core.upsample.Upsampler`): `upsample` takes H x W x C and
    returns (scale*H) x (scale*W) x C of the SAME dtype, and the object carries `scale`,
    `name`, `n_clipped` and `n_total`. Those four are read by the pipeline when it writes
    the provenance tag; an upsampler missing them fails before the first tile.
    """

    def __init__(self, model_path, sess=None, prov=None, clip=True):
        self.model_path = str(model_path)
        if sess is None or prov is None:
            sess, prov = read_provenance(model_path)
        self.sess, self.prov = sess, prov
        self.scale = int(prov["scale"])
        self.norm = float(prov["norm_divisor_dn"])
        self.name = f"onnx:{Path(model_path).name}"
        self.clip = clip
        self.n_clipped = 0
        self.n_total = 0
        self._in = self.sess.get_inputs()[0].name

    def upsample(self, arr):
        a = np.asarray(arr)
        dt = a.dtype
        # H x W x C -> 1 x C x H x W, normalised by the constant the MODEL declares.
        x = (np.moveaxis(a, -1, 0)[None].astype(np.float32) / self.norm)
        y = self.sess.run(None, {self._in: x})[0][0]          # C x sH x sW, normalised
        y = np.moveaxis(y, 0, -1) * self.norm                  # sH x sW x C, DN
        self.n_total += int(y.size)
        if np.issubdtype(dt, np.integer):
            info = np.iinfo(dt)
            if self.clip:
                # Same argument as the bicubic path: an unclipped float cast to an integer
                # dtype WRAPS, so an overshoot to 65536 becomes 0 - a black pixel at the
                # brightest place in the scene, which reads as data rather than as an
                # artefact. Clipping loses the overshoot; wrapping invents a value.
                out = np.rint(y)
                self.n_clipped += int(np.count_nonzero(
                    (out < info.min) | (out > info.max)))
                np.clip(out, info.min, info.max, out=out)
                return out.astype(dt)
            return np.rint(y).astype(dt)
        return y.astype(dt)

    def describe(self):
        p = self.prov
        return (f"{Path(self.model_path).name} | DN/{p['norm_divisor_dn']:.0f} | x{p['scale']}"
                f" | {p['in_channels']}ch {p['band_order']} | step {p['completed_steps']}"
                f"/{p['registered_schedule_steps']}")
