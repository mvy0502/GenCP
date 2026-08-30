#!/usr/bin/env python3
"""Build the stacked 3-band reflectance GeoTIFF the model path consumes.

WP2A downloaded B02, B03 and B04 as SEPARATE single-band files. The network takes three
channels at once, so nothing on disk was a valid input until this ran.

**Band order is not assumed.** It is taken from `sr_data.params.BANDS`, the same tuple the
corpus builder used, and cross-checked against the ONNX graph's own `band_order` metadata.
If the two disagree the build refuses: a silently transposed channel order would produce
output that looks plausible and is wrong, which is this project's dominant failure class.

Output dtype is **uint16 DN**, identical to what the corpus stores. Normalisation
(`DN / NORM_DIVISOR_DN`) happens at inference, from the constant in the model's provenance,
so this file carries no scaling decision.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

SR = Path(__file__).resolve().parents[1]
if str(SR) not in sys.path:
    sys.path.insert(0, str(SR))

from sr_data import params as P                                         # noqa: E402
from sr_train import config as C                                        # noqa: E402


def band_order_from_model(model_path):
    """The band order the MODEL says it was trained on, or None if unreadable."""
    try:
        import onnxruntime as ort
        s = ort.InferenceSession(str(model_path), providers=["CPUExecutionProvider"])
        return s.get_modelmeta().custom_metadata_map.get("band_order")
    except Exception:
        return None


def build(granule, out_path, model_path=None, window=None):
    import rasterio
    from rasterio.windows import Window

    g = P.GRANULES[granule]
    src_dir = C.data_root() / P.DATA_SUBDIR / g["dirname"]
    bands = list(P.BANDS)

    declared = band_order_from_model(model_path) if model_path else None
    if declared is not None and declared.split(",") != bands:
        raise SystemExit(
            f"make_model_input: band order disagreement. sr_data.params.BANDS = {bands}, "
            f"but the model's provenance says band_order = {declared!r}. Refusing to build "
            f"an input whose channel order the model does not expect.")

    paths = [src_dir / f"{b}.tif" for b in bands]
    for p in paths:
        if not p.is_file():
            raise SystemExit(f"make_model_input: missing band file {p}")

    with rasterio.open(paths[0]) as ref:
        prof = ref.profile.copy()
        win = None if window is None else Window(*window)
        H = ref.height if win is None else int(win.height)
        W = ref.width if win is None else int(win.width)
        T = ref.transform if win is None else ref.window_transform(win)
        ref_crs, ref_nodata, ref_dtype = ref.crs, ref.nodata, ref.dtypes[0]
        ref_full_T, ref_full_wh = ref.transform, (ref.width, ref.height)

    stack = np.empty((len(bands), H, W), ref_dtype)
    for k, p in enumerate(paths):
        with rasterio.open(p) as d:
            # Every band must sit on the SAME grid. Checked, not assumed - and the
            # TRANSFORM is compared, not only CRS and shape: WP2A open item 4 recorded that
            # all five granules share EPSG:32636 and 10980x10980, so a check omitting the
            # transform passes every wrong pairing.
            if (d.crs != ref_crs or tuple(d.transform)[:6] != tuple(ref_full_T)[:6]
                    or (d.width, d.height) != (ref_full_wh)):
                raise SystemExit(
                    f"make_model_input: {p.name} is not on the same grid as "
                    f"{paths[0].name}. crs {d.crs} vs {ref_crs}; transform "
                    f"{tuple(d.transform)[:6]} vs {tuple(ref_full_T)[:6]}; "
                    f"size {d.width}x{d.height} vs {ref_full_wh[0]}x{ref_full_wh[1]}")
            stack[k] = d.read(1, window=win)

    prof.update(count=len(bands), width=W, height=H, transform=T, dtype=ref_dtype,
                compress="deflate", tiled=True, blockxsize=512, blockysize=512,
                nodata=ref_nodata)
    out_path = Path(out_path); out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.with_suffix(".tif.part")
    with rasterio.open(tmp, "w", **prof) as dst:
        dst.write(stack)
        for k, b in enumerate(bands, 1):
            dst.set_band_description(k, b)
        dst.update_tags(GENCP_SR_INPUT=json.dumps(dict(
            work_package="P2-WP4", granule=granule, date=g["date"],
            product_uri=g["product_uri"], stac_item=g["stac_item"],
            band_order=",".join(bands),
            band_order_source="sr_data.params.BANDS, cross-checked against the ONNX "
                              "graph's band_order metadata",
            dtype="uint16 DN", radiometry=f"reflectance = DN * {P.DN_TO_REFLECTANCE}",
            normalisation_at_inference=f"normalised = DN / {P.NORM_DIVISOR_DN}",
            corpus_registration="tubitak/sr/docs/03a-corpus-registration.md",
            window=list(window) if window else None), sort_keys=True))
    tmp.replace(out_path)
    return out_path, dict(bands=bands, shape=(H, W), dtype=str(ref_dtype),
                          crs=str(ref_crs), transform=[round(v, 4) for v in tuple(T)[:6]],
                          nodata=ref_nodata, declared_by_model=declared)


def main():
    ap = argparse.ArgumentParser(prog="make_model_input.py")
    ap.add_argument("--granule", default="36SXJ")
    ap.add_argument("--out", default=None)
    ap.add_argument("--model", default=None)
    ap.add_argument("--window", type=int, nargs=4, default=None,
                    metavar=("COL0", "ROW0", "W", "H"))
    a = ap.parse_args()
    if a.granule not in P.GRANULES:
        raise SystemExit(f"make_model_input: unknown granule {a.granule!r}; "
                         f"known {sorted(P.GRANULES)}")
    g = P.GRANULES[a.granule]
    model = Path(a.model or (C.data_root() / "sr_models" / "gencp_sr_x2_v1.onnx"))
    tag = "" if a.window is None else f"_win{a.window[0]}-{a.window[1]}-{a.window[2]}"
    out = Path(a.out or (C.data_root() / "sr_model_input" /
                         f"MODEL_INPUT_{a.granule}_{g['date'].replace('-','')}"
                         f"_{'-'.join(P.BANDS)}_uint16DN_10m{tag}.tif"))
    p, info = build(a.granule, out, model, a.window)
    sz = p.stat().st_size
    print(f"wrote {p}")
    print(f"  {sz:,} bytes  bands {info['bands']} (band 1 = {info['bands'][0]})")
    print(f"  {info['shape'][1]} x {info['shape'][0]} px, {info['dtype']}, {info['crs']}, "
          f"nodata {info['nodata']}")
    print(f"  transform {info['transform']}")
    print(f"  band order source: sr_data.params.BANDS; model declares "
          f"{info['declared_by_model']!r} -> {'AGREE' if info['declared_by_model'] == ','.join(info['bands']) else 'NOT CHECKED'}")
    print(f"  sha256 {hashlib.sha256(p.read_bytes()).hexdigest()}" if sz < 3e8 else
          "  (sha256 skipped, file > 300 MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
