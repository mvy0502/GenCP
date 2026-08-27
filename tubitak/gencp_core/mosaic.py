"""Stitching, georeferencing and GeoTIFF write.

LIFTED from `tubitak/tool/gencp_ref.py` (feather_weight, mosaic), whose georeferencing was
gated and passed under tool-gate-registration-2 criterion 3.

The georeferencing is an INTERFACE CONTRACT, not a nicety. A separate application consumes
this GeoTIFF and extracts ground control points from it; a half-pixel offset is invisible
here and becomes wrong GCPs downstream. Two properties carry that contract:

  * **The corrected per-tile transform is hard-wired.** The upstream chips carry 256 px of
    content spanning 257 x 10 m, so a generated tile's true GSD is 2570/256 = 10.0390625 m.
    There is no code path that places a tile with the uncorrected 10.0 m transform.
  * **The output grid follows one written-down snapping rule** (see `extent.output_grid`):
    anchored at the reference extent's north-west corner exactly, growing east and south in
    whole 10 m pixels. Gate G asserts it numerically.

Adjacent tiles are generated independently and disagree at their seams, so tiles overlap
and are feather-blended with a separable raised-cosine ramp. 640 m is the measured default:
seam-energy ratio 1.008 and no detectable point clustering, against 1.124 unblended.
"""
from __future__ import annotations
import json, math
from pathlib import Path
import numpy as np

from .extent import TRUE_GSD, TILE_M, NOMINAL, OUT_PX, output_grid


def feather_weight(overlap_px, size=OUT_PX):
    """Separable raised-cosine ramp over the overlap margin, 1.0 in the interior."""
    w1 = np.ones(size)
    r = max(int(overlap_px), 1)
    r = min(r, size // 2)
    ramp = 0.5 - 0.5 * np.cos(np.pi * (np.arange(r) + 0.5) / r)
    w1[:r] = ramp
    w1[-r:] = ramp[::-1]
    return np.outer(w1, w1)


def build(tiles, fakes, work_crs, extent, overlap_m, progress=None):
    """Blend generated tiles onto the output grid.

    tiles  : [(i, j, x_nw, y_nw)]
    fakes  : {(i, j): HWC uint8 array}
    Returns (rgb uint8 (3,H,W), valid mask, transform).
    """
    from rasterio.transform import Affine
    from rasterio.warp import reproject, Resampling

    W, H, target = output_grid(extent)
    acc = np.zeros((3, H, W), np.float64)
    wac = np.zeros((H, W), np.float64)
    ov_px = int(round(overlap_m / TRUE_GSD))
    wtile = feather_weight(ov_px)

    total = len(tiles)
    for n, (i, j, tx, ty) in enumerate(tiles, 1):
        arr = fakes.get((i, j))
        if arr is None:
            continue
        arr = np.moveaxis(np.asarray(arr, np.float64), -1, 0)
        # THE CORRECTED TRANSFORM — hard-wired; no 10.0 m tile path exists.
        src_T = Affine(TRUE_GSD, 0, tx, 0, -TRUE_GSD, ty)
        wa = np.zeros((H, W), np.float64)
        reproject(wtile, wa, src_transform=src_T, src_crs=work_crs,
                  dst_transform=target, dst_crs=work_crs, resampling=Resampling.bilinear)
        for b in range(3):
            da = np.zeros((H, W), np.float64)
            reproject(arr[b] * wtile, da, src_transform=src_T, src_crs=work_crs,
                      dst_transform=target, dst_crs=work_crs,
                      resampling=Resampling.bilinear)
            acc[b] += da
        wac += wa
        if progress is not None:
            progress(n, total)

    valid = wac > 1e-6
    out = np.zeros((3, H, W), np.uint8)
    for b in range(3):
        out[b][valid] = np.clip(np.round(acc[b][valid] / wac[valid]), 0, 255)
    return out, valid, target


QML_TEMPLATE = """<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="3.28.0" styleCategories="AllStyleCategories">
  <pipe>
    <rasterrenderer type="multibandcolor" opacity="1" alphaBand="-1"
                    redBand="1" greenBand="2" blueBand="3" nodataColor="">
      <redContrastEnhancement><minValue>0</minValue><maxValue>255</maxValue>\
<algorithm>NoEnhancement</algorithm></redContrastEnhancement>
      <greenContrastEnhancement><minValue>0</minValue><maxValue>255</maxValue>\
<algorithm>NoEnhancement</algorithm></greenContrastEnhancement>
      <blueContrastEnhancement><minValue>0</minValue><maxValue>255</maxValue>\
<algorithm>NoEnhancement</algorithm></blueContrastEnhancement>
    </rasterrenderer>
    <brightnesscontrast brightness="0" contrast="0" gamma="1"/>
    <huesaturation saturation="0" grayscaleMode="0" colorizeOn="0"/>
    <rasterresampler maxOversampling="2"/>
  </pipe>
  <blendMode>0</blendMode>
</qgis>
"""


def write_qml_sidecar(tif_path):
    """Write `<output>.qml` next to a 4-band output so QGIS draws RGB, not a blend.

    Band 4 is CONFIDENCE, tagged ColorInterp.alpha because that is where the supervisor
    asked for it. Every viewer that honours alpha therefore composites the output over
    whatever sits beneath it. On the demo tile that measured as pulling the rendered image
    2.3x closer to the real reference than the generation actually is - a comparison tool
    silently flattering the thing it exists to compare.

    Forcing opaque rendering inside our own dialog fixes only our own case. QGIS auto-loads
    a `.qml` beside the raster when the layer is added by ANY route - drag and drop, Add
    Raster Layer, another person's project - so the sidecar carries the fix to everyone who
    opens the file, not just to users of this plugin.

    `alphaBand="-1"` is the whole mechanism: it tells QGIS no band supplies transparency.
    The file is untouched; only its default styling is specified.
    """
    qml = Path(tif_path).with_suffix(".qml")
    qml.write_text(QML_TEMPLATE, encoding="utf-8")
    return qml


def write_qml_if_alpha(tif_path):
    """Write the sidecar only if the file actually carries an alpha band.

    Used for outputs whose band layout is inherited rather than chosen here - the
    reprojected copy takes its colorinterp from its source, and the OSM mosaic takes its
    profile from the renders. Asserting "this one has alpha" from the calling context would
    be a guess; asking the file is not.
    """
    import rasterio
    from rasterio.enums import ColorInterp
    try:
        with rasterio.open(tif_path) as s:
            if s.count >= 4 and ColorInterp.alpha in s.colorinterp:
                return write_qml_sidecar(tif_path)
    except Exception:                              # noqa: BLE001
        return None
    return None


def write_geotiff(path, rgb, crs, transform, provenance=None, alpha=None):
    """Write the mosaic in its NATIVE metric CRS. Never reprojects.

    Reprojection used to live inside this function via a `dst_crs` argument, which meant
    the only file that reached disk was the resampled one. Gate G's contract is asserted on
    the native grid - exact 10.0 m pixels anchored on the reference NW corner - so the
    native file must always exist and must be the one the contract is checked against.
    `reproject_geotiff` writes the reprojected copy as a SECOND file.

    `alpha`, if given, is a uint8 HxW band written as a fourth band with
    ColorInterp.alpha. The three RGB bands are byte-identical whether or not it is passed:
    the alpha band is appended, never blended in. tubitak/tests/gate_alpha.py asserts that
    against a 3-band write of the same array.
    """
    import rasterio
    from rasterio.enums import ColorInterp
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    _, H, W = rgb.shape
    count = 3 if alpha is None else 4
    prof = dict(driver="GTiff", height=H, width=W, count=count, dtype="uint8",
                crs=crs, transform=transform, compress="deflate")
    # A 4-band file uses the alpha band to say what is absent, so a nodata VALUE would be
    # a second, contradictory answer to the same question. 3-band keeps nodata=0 so nothing
    # about the validated output changes.
    if alpha is None:
        prof["nodata"] = 0
    prov = dict(provenance or {})
    if alpha is not None:
        # Say it in the file, not only in the documentation a reader may never open.
        prov["band_4"] = ("confidence, NOT transparency. Software that honours "
                          "ColorInterp.alpha will blend this image over whatever is "
                          "beneath it; the accompanying .qml disables that in QGIS.")
        prov["rgb_unchanged_from_3band"] = True
    tags = {"GENCP_PROVENANCE": json.dumps(prov, sort_keys=True)}
    with rasterio.open(path, "w", **prof) as d:
        # indexes=[1,2,3] explicitly: a bare write() of a 3-band array into a 4-band
        # dataset is a shape error, and letting it default would have been a silent
        # band-order hazard even where it did not raise.
        d.write(rgb, indexes=[1, 2, 3])
        if alpha is not None:
            d.write(np.asarray(alpha, dtype=np.uint8), 4)
            d.colorinterp = [ColorInterp.red, ColorInterp.green, ColorInterp.blue,
                             ColorInterp.alpha]
        d.update_tags(**tags)
    if alpha is not None:
        write_qml_sidecar(path)
    return path


def reproject_geotiff(src_path, out_path, dst_crs, provenance=None):
    """Reproject a written mosaic into another CRS. The source file is left alone.

    The result is RESAMPLED: its pixels no longer sit on the 10 m grid anchored at the
    reference corner, so Gate G's contract does not describe it. That is recorded in its
    own provenance rather than left for a reader to infer.
    """
    import rasterio
    from rasterio.warp import calculate_default_transform, reproject, Resampling
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(src_path) as s:
        t2, w2, h2 = calculate_default_transform(
            s.crs, dst_crs, s.width, s.height, *s.bounds)
        prof = s.profile.copy()
        prof.update(crs=dst_crs, transform=t2, width=w2, height=h2)
        prov = dict(provenance or {})
        prov.update({
            "resampled": True,
            "resampled_from_crs": str(s.crs),
            "resampled_to_crs": str(dst_crs),
            "resampling": "bilinear",
            "grid_contract": ("NOT the Gate G grid. This file was reprojected after "
                              "generation; its pixels are resampled and are no longer "
                              "anchored on the reference NW corner at exactly 10.0 m. "
                              "The native-CRS file beside it is the one the contract "
                              "describes."),
        })
        with rasterio.open(out_path, "w", **prof) as d:
            for b in range(1, s.count + 1):
                reproject(rasterio.band(s, b), rasterio.band(d, b),
                          resampling=Resampling.bilinear)
            d.colorinterp = s.colorinterp
            d.update_tags(GENCP_PROVENANCE=json.dumps(prov, sort_keys=True))
    write_qml_if_alpha(out_path)
    return out_path


def write_osm_mosaic(path, render_paths, provenance=None):
    """Mosaic the rasterised OSM inputs so the preview survives the run as a layer.

    Merged, not resampled onto the output grid: these are the model's INPUT and are most
    useful compared against the output exactly as the model saw them.
    """
    import rasterio
    from rasterio.merge import merge
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    srcs = [rasterio.open(p) for p in render_paths]
    try:
        arr, t = merge(srcs)
        prof = srcs[0].profile.copy()
        prof.update(height=arr.shape[1], width=arr.shape[2], transform=t,
                    count=arr.shape[0], compress="deflate")
        with rasterio.open(path, "w", **prof) as d:
            d.write(arr)
            d.update_tags(GENCP_PROVENANCE=json.dumps(
                dict(provenance or {}, product="GenCP rasterised OSM input"),
                sort_keys=True))
    finally:
        for s in srcs:
            s.close()
    write_qml_if_alpha(path)
    return path


def seam_metric(rgb, transform, tiles):
    """Gradient energy in +/-2 px buffers around interior tile edges vs elsewhere.

    Measured, never eyeballed. Returns None when the extent has no interior seam.
    """
    from scipy.ndimage import sobel
    g = np.asarray(rgb, float).mean(axis=0)
    gm = np.hypot(sobel(g, 0), sobel(g, 1))
    H, W = g.shape
    mask = np.zeros((H, W), bool)
    xs = sorted({tx for _, _, tx, _ in tiles})[1:]
    ys = sorted({ty for _, _, _, ty in tiles}, reverse=True)[1:]
    inv = ~transform
    for x in xs:
        for edge in (x, x + TILE_M):
            c, _ = inv * (edge, 0)
            c = int(round(c))
            if 2 <= c < W - 2:
                mask[:, c - 2:c + 3] = True
    for y in ys:
        for edge in (y, y - TILE_M):
            _, r = inv * (0, edge)
            r = int(round(r))
            if 2 <= r < H - 2:
                mask[r - 2:r + 3, :] = True
    if not mask.any() or mask.all():
        return None
    seam, back = float(gm[mask].mean()), float(gm[~mask].mean())
    return dict(seam_grad=seam, background_grad=back,
                ratio=seam / back if back > 0 else float("inf"),
                seam_px=int(mask.sum()))


def write_band_geotiff(path, bands, crs, transform, provenance=None, colours=None):
    """Write a single-band uint8 raster with a colour table - the confidence layer.

    Single-band paletted rather than RGB so QGIS shows a legend with band names instead of
    three meaningless colour channels, and so 0 can mean nodata unambiguously (the score
    itself is signed, so no encoded score value is free to stand for "no data").
    """
    import rasterio
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    a = np.asarray(bands, dtype=np.uint8)
    H, W = a.shape
    prof = dict(driver="GTiff", height=H, width=W, count=1, dtype="uint8",
                crs=crs, transform=transform, nodata=0, compress="deflate")
    with rasterio.open(path, "w", **prof) as d:
        d.write(a, 1)
        if colours:
            d.write_colormap(1, {int(k): tuple(v) + (255,) for k, v in colours.items()})
        d.update_tags(GENCP_PROVENANCE=json.dumps(provenance or {}, sort_keys=True))
    return path
