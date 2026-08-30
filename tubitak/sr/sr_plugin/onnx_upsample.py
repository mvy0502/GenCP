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


def _from_onnx_metadata(md, model_path):
    """Our own models: the contract is inside the file, written at export time."""
    missing = [k for k in REQUIRED_META if k not in md]
    if missing:
        raise ModelInputError("err_model_meta", missing=", ".join(missing),
                              name=Path(model_path).name)
    return dict(
        scale=int(md["scale_factor"]),
        in_channels=int(md["in_channels"]),
        band_order=md["band_order"],
        # OUR models are normalised by the CALLER: the graph sees DN / norm_divisor_dn.
        normalisation="external",
        norm_divisor_dn=float(md["norm_divisor_dn"]),
        tiling="feather",
        margin_out=0,
        tile_src=int(md.get("infer_tile_src_px", 128)),
        overlap_src=int(md.get("infer_overlap_src_px", 32)),
        corpus_id=md.get("corpus_id", "?"),
        completed_steps=md.get("completed_steps", "?"),
        registered_schedule_steps=md.get("registered_schedule_steps", "?"),
        contract_source="ONNX metadata_props",
        raw=md)


#: Default inference tile, in SOURCE px, for a crop-tiled model. The reference tool's own
#: default is `-ts 1000` OUTPUT px, which at factor 4 is 250 source px; 256 is the nearest
#: power of two and is what we use.
CROP_TILE_SRC_PX = 256


def _from_yaml_sidecar(path, model_path):
    """The reference tool's own configuration, used as the contract for its weights.

    `wsx4_spatrad.onnx` carries NO `metadata_props` at all - verified in WP5 - so there is
    nothing inside the file to read. Its parameters live beside it in `wsx4_spatrad.yaml`,
    which is the file the tool itself reads. We read the same file rather than restating its
    numbers, so a different model of theirs is a different sidecar and not a code change.
    """
    try:
        import yaml
    except ImportError:
        # Fires HERE, on the wsx4 path only, and never at plugin load: the bicubic path is
        # the demonstration's recovery plan and must not depend on a package it never uses.
        # ModelInputError carries a strings key, so the dialog shows the Turkish message
        # through the same handler it already uses for every other model-contract failure,
        # instead of a raw ImportError behind a bare "Başarısız:".
        raise ModelInputError("err_no_yaml", name=Path(path).name)
    cfg = yaml.safe_load(Path(path).read_text())
    for k in ("bands", "factor", "margin"):
        if k not in cfg:
            raise ModelInputError("err_model_meta", missing=k, name=Path(path).name)
    bands = list(cfg["bands"])
    scale = int(float(cfg["factor"]))
    margin = int(cfg["margin"])
    from sr_core.mosaic import min_overlap_for_margin
    return dict(
        scale=scale,
        in_channels=len(bands),
        band_order=",".join(bands),
        # THEIR graph divides by 10000 on the way in and multiplies by 10000 on the way out,
        # and their run.py reads with scale=1.0. The caller must apply NOTHING. Normalising
        # outside as well would divide twice and produce an image that is wrong by a large
        # factor while still looking entirely ordinary.
        normalisation="internal",
        norm_divisor_dn=None,
        # A GAN's tile predictions must not be averaged. WP5 measured 37 DN at overlap 32.
        tiling="crop",
        margin_out=margin,
        tile_src=CROP_TILE_SRC_PX,
        overlap_src=min_overlap_for_margin(margin, scale),
        corpus_id=f"reference tool config {Path(path).name}",
        completed_steps="?", registered_schedule_steps="?",
        contract_source=f"sidecar {Path(path).name} (the reference tool's own config)",
        raw={k: str(v) for k, v in cfg.items()})


def read_provenance(model_path):
    """The model's declared contract. Lazily imports onnxruntime.

    Two sources, in order: the ONNX file's own `metadata_props` (our models), else a
    same-stem `.yaml` beside it (the reference tool's models, whose graphs carry none).
    A model with neither is refused rather than run under guessed defaults.
    """
    import onnxruntime as ort
    sess = ort.InferenceSession(str(model_path), providers=["CPUExecutionProvider"])
    md = dict(sess.get_modelmeta().custom_metadata_map)
    if md:
        return sess, _from_onnx_metadata(md, model_path)
    side = Path(model_path).with_suffix(".yaml")
    if side.is_file():
        return sess, _from_yaml_sidecar(side, model_path)
    raise ModelInputError("err_model_meta",
                          missing=f"metadata_props, and no sidecar {side.name}",
                          name=Path(model_path).name)


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
        self.normalisation = prov["normalisation"]
        self.norm = prov["norm_divisor_dn"]
        if self.normalisation == "external" and not self.norm:
            raise ModelInputError("err_model_meta", missing="norm_divisor_dn",
                                  name=Path(model_path).name)
        self.name = f"onnx:{Path(model_path).name}"
        self.clip = clip
        self.n_clipped = 0
        self.n_total = 0
        self._in = self.sess.get_inputs()[0].name

    def upsample(self, arr):
        a = np.asarray(arr)
        dt = a.dtype
        x = np.moveaxis(a, -1, 0)[None].astype(np.float32)
        # THE DECLARATION IS HONOURED HERE, and it is the difference between a correct
        # image and one that is wrong by a factor of thousands while looking ordinary.
        #   external : the graph expects DN / norm_divisor_dn, applied by us.
        #   internal : the graph does its own scaling; we must pass raw DN untouched.
        if self.normalisation == "external":
            x = x / self.norm
        y = self.sess.run(None, {self._in: x})[0][0]
        y = np.moveaxis(y, 0, -1)
        if self.normalisation == "external":
            y = y * self.norm
        self.n_total += int(y.size)
        if np.issubdtype(dt, np.integer):
            info = np.iinfo(dt)
            if self.clip:
                # Same argument as the bicubic path: an unclipped float cast to an integer
                # dtype WRAPS, so an overshoot becomes a dark pixel at the brightest place
                # in the scene, which reads as data rather than as an artefact.
                out = np.rint(y)
                self.n_clipped += int(np.count_nonzero(
                    (out < info.min) | (out > info.max)))
                np.clip(out, info.min, info.max, out=out)
                return out.astype(dt)
            return np.rint(y).astype(dt)
        return y.astype(dt)

    def describe(self):
        p = self.prov
        norm = ("DN/%.0f" % p["norm_divisor_dn"]) if p["normalisation"] == "external" \
            else "norm in-graph"
        return (f"{Path(self.model_path).name} | {norm} | x{p['scale']} | "
                f"{p['in_channels']}ch {p['band_order']} | {p['tiling']}"
                f"{'' if p['tiling'] != 'crop' else ' m=' + str(p['margin_out'])} | "
                f"{p['contract_source']}")
