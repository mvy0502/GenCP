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


def write_geotiff(path, rgb, crs, transform, provenance=None, dst_crs=None):
    """Write the mosaic, optionally reprojecting, with provenance in GeoTIFF tags."""
    import rasterio
    from rasterio.warp import calculate_default_transform, reproject, Resampling
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    _, H, W = rgb.shape
    prof = dict(driver="GTiff", height=H, width=W, count=3, dtype="uint8",
                crs=crs, transform=transform, nodata=0, compress="deflate")
    tags = {"GENCP_PROVENANCE": json.dumps(provenance or {}, sort_keys=True)}

    if dst_crs and str(dst_crs).upper() != str(crs).upper():
        tmp = path.with_suffix(".native.tif")
        with rasterio.open(tmp, "w", **prof) as d:
            d.write(rgb)
            d.update_tags(**tags)
        with rasterio.open(tmp) as s:
            t2, w2, h2 = calculate_default_transform(
                s.crs, dst_crs, s.width, s.height, *s.bounds, resolution=NOMINAL)
            prof2 = dict(prof, crs=dst_crs, transform=t2, width=w2, height=h2)
            with rasterio.open(path, "w", **prof2) as d:
                for b in range(1, 4):
                    reproject(rasterio.band(s, b), rasterio.band(d, b),
                              resampling=Resampling.bilinear)
                d.update_tags(**tags)
        tmp.unlink(missing_ok=True)
    else:
        with rasterio.open(path, "w", **prof) as d:
            d.write(rgb)
            d.update_tags(**tags)
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
