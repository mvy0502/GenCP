"""Extent handling and the tile grid — the geometric spec, shared by every other module.

This module holds the numbers the rest of the chain must agree on, so that `vectors` and
`rasterize` can both depend on them without depending on each other.

The georeferencing correction is the important one. The upstream training chips carry 256
pixels of content spanning 257 x 10 m on the ground (`fix_georeferencing.py` finding), so
the true ground sample distance of a generated tile is 2570/256 = 10.0390625 m, not 10 m.
Placing tiles with a 10.0 m transform puts them progressively wrong. There is no code path
in this package that places a tile with the uncorrected transform.
"""
from __future__ import annotations
import math

# --- the rendering grid (must match the upstream renderer exactly) ---
SIZE = 257                 # rendered chip is 257 x 257 px
GSD = 10.0                 # nominal ground sample distance of the render, m
SUPERSAMPLE = 4            # hard edges are rasterised at 4x then box-averaged down

# --- the generation grid ---
SRC_PX = 257               # px of input handed to the renderer
OUT_PX = 256               # px of content the generator returns
NOMINAL = 10.0             # the output mosaic's grid spacing, m
TRUE_GSD = SRC_PX * NOMINAL / OUT_PX     # 10.0390625 — the Option-A correction
TILE_M = SRC_PX * NOMINAL                # 2570 m ground footprint of one tile

DEFAULT_OVERLAP_M = 640.0  # measured default: seam ratio 1.008, no point clustering


class ExtentError(ValueError):
    """Raised when a requested extent or CRS cannot be used."""


def utm_for(lon: float, lat: float) -> str:
    """The UTM CRS whose zone contains a lon/lat, as an EPSG authority string."""
    zone = int((lon + 180) // 6) + 1
    return f"EPSG:{32600 + zone if lat >= 0 else 32700 + zone}"


def validate_bbox(bbox):
    """Check a 4-tuple is a well-formed, non-degenerate bbox. Returns it as floats."""
    if bbox is None or len(bbox) != 4:
        raise ExtentError("extent must be four numbers: xmin ymin xmax ymax")
    xmin, ymin, xmax, ymax = (float(v) for v in bbox)
    if not all(math.isfinite(v) for v in (xmin, ymin, xmax, ymax)):
        raise ExtentError("extent contains a non-finite coordinate")
    if xmax <= xmin or ymax <= ymin:
        raise ExtentError(
            f"degenerate extent: xmin={xmin} xmax={xmax} ymin={ymin} ymax={ymax} "
            "(need xmax > xmin and ymax > ymin)")
    return (xmin, ymin, xmax, ymax)


# CRS work goes through RASTERIO's PROJ binding, never pyproj, and the reason is a crash
# rather than a preference. Measured inside QGIS 4.2.1: a pyproj CRS created on a QgsTask
# WORKER thread segfaults the process outright IF the main thread has already created one.
# The reverse order is fine, which is what made it look intermittent - the plugin's dialog
# always touches pyproj first (to fill in the extent), so every worker-thread use was
# already living on borrowed time. rasterio's binding was probed under exactly the same
# main-thread-first condition and is unaffected.
#
# The arithmetic is deliberately unchanged: the same four corners are transformed and the
# same min/max is taken, rather than switching to transform_bounds, which densifies edges
# and would move rendered pixels. Gate R re-run after this change: still byte-identical.
# WP12: DEFERRED, not module-level. This single line was the whole of "the plugin does not
# work on QGIS 3.40": `dialog._build_ui` imports this module at line 375, so a QGIS whose
# Python has no rasterio died here with an ImportError and the dialog never opened. The user
# saw a stack trace, not a sentence naming the library. rasterio's other two uses in this
# file (rasterio.warp at ~line 88, rasterio.transform at ~line 178) were already deferred;
# this one was not, and it is the only one that runs at import time.
#
# Reproduced on QGIS 3.44.13 (Qt 5.15.18) by removing rasterio: identical traceback,
# extent.py line 65 reached from dialog.py line 375.
def _crs():
    """The rasterio CRS class, imported on first use. Raises ImportError if absent."""
    from rasterio.crs import CRS
    return CRS


def _crs_name(c):
    """A human name for a CRS, whatever the binding gives us."""
    try:
        d = c.to_dict()
        if d.get("init"):
            return str(d["init"])
    except Exception:                                # noqa: BLE001
        pass
    try:
        import re as _re
        m = _re.search(r'\[\s*"([^"]+)"', c.to_wkt() or "")
        if m:
            return m.group(1)
    except Exception:                                # noqa: BLE001
        pass
    return str(c)


def _transform_points(src, dst, xs, ys):
    """Transform coordinate lists. Thread-safe inside QGIS; pyproj is not - see above."""
    from rasterio.warp import transform as _rio_transform
    ox, oy = _rio_transform(_crs().from_user_input(src), _crs().from_user_input(dst),
                            list(xs), list(ys))
    return list(ox), list(oy)


def classify_crs(crs: str):
    """Decide how a requested CRS must be treated. Returns (kind, detail).

    kind is 'geographic' (reproject to UTM), 'metric' (use as-is) or 'unusable'.

    This exists because "is it projected?" is the wrong question and asking it produced
    two silently wrong outputs, both measured in tubitak/tests/plugin_failure_paths.py:

      EPSG:3857  projected, axis unit nominally metre, but a Pseudo-Mercator metre is a
                 metre only at the equator. A reference 2570 m across measured 3391 units
                 at Ankara's latitude, so the chain built a 340 x 341 px raster where 257
                 x 257 was correct and called every pixel 10 m. No warning.
      EPSG:4258  geographic, but the old test was `crs == "EPSG:4326"`, so ETRS89
                 latitude/longitude fell through to the projected branch and its degrees
                 were read as metres. Extent span 0.0, output grid 1 x 1 px. No warning.

    So the test is now on the CRS's own properties, not on one hard-coded EPSG code.
    """
    if not crs:
        return "unusable", "a CRS is required"
    try:
        c = _crs().from_user_input(crs)
    except Exception as e:                           # noqa: BLE001 - reported to the user
        return "unusable", (f"the reference layer's CRS ({crs}) could not be interpreted "
                            f"({e}). Reproject the layer to a UTM zone and try again.")
    if c.is_geographic:
        return "geographic", _crs_name(c)
    epsg = c.to_epsg()
    wkt = ""
    try:
        wkt = c.to_wkt() or ""
    except Exception:                                # noqa: BLE001
        wkt = ""
    if epsg in (3857, 900913, 3785) or "Pseudo-Mercator" in wkt \
            or "Popular Visualisation" in wkt:
        return "unusable", (
            f"{crs} ({_crs_name(c)}) is Web/Pseudo-Mercator. Its units are called metres but are "
            f"only true metres at the equator, so a 10 m grid built in it would not be 10 m "
            f"on the ground. Reproject the reference layer to its UTM zone "
            f"(Layer > Save As, or Processing > Reproject Layer) and run again.")
    units = ""
    try:
        units = (c.linear_units or "").lower()
    except Exception:                                # noqa: BLE001
        units = ""
    if units and units not in ("metre", "meter", "m", "unknown"):
        return "unusable", (
            f"{crs} ({_crs_name(c)}) has axis units of '{units}', not metres. The whole chain "
            f"works on a 10 m grid. Reproject the reference layer to a metric CRS "
            f"(its UTM zone) and run again.")
    return "metric", _crs_name(c)


def resolve(bbox, crs: str):
    """Resolve a requested extent to a metric working CRS.

    Any GEOGRAPHIC CRS is reprojected to the UTM zone of the extent centre, because the
    whole chain works in metres. A metric projected CRS is used as-is. Anything else is
    refused with a message that names the problem - see classify_crs.

    Returns (extent_in_working_crs, working_crs, source_crs).
    """
    xmin, ymin, xmax, ymax = validate_bbox(bbox)
    kind, detail = classify_crs(crs)
    if kind == "unusable":
        raise ExtentError(detail)
    if kind == "geographic":
        work = utm_for((xmin + xmax) / 2.0, (ymin + ymax) / 2.0)
        xs, ys = _transform_points(
            crs, work, [xmin, xmin, xmax, xmax], [ymin, ymax, ymin, ymax])
        return (min(xs), min(ys), max(xs), max(ys)), work, crs
    return (xmin, ymin, xmax, ymax), crs, crs


def output_grid(extent):
    """The output raster grid for an extent, under the registered snapping rule.

    Snapping rule (Gate G, written down so the downstream consumer can rely on it):
    the grid is anchored at the reference extent's NORTH-WEST corner exactly — it is not
    snapped to a multiple of the GSD — and grows east and south in whole 10 m pixels. The
    east and south edges may therefore extend up to one pixel beyond the requested extent.

    Returns (width, height, transform).
    """
    from rasterio.transform import Affine
    xmin, ymin, xmax, ymax = validate_bbox(extent)
    width = int(math.ceil((xmax - xmin) / NOMINAL))
    height = int(math.ceil((ymax - ymin) / NOMINAL))
    return width, height, Affine(NOMINAL, 0, xmin, 0, -NOMINAL, ymax)


def tile_grid(extent, overlap_m=DEFAULT_OVERLAP_M, align_origin=None):
    """Lay out generation tiles over an extent.

    Tiles are TILE_M square and step by (TILE_M - overlap_m). Adjacent tiles are generated
    independently and disagree at their seams, so they are overlapped and feather-blended
    downstream; 640 m is the measured default.

    align_origin pins the NW corner of tile (0,0), which is what lets a tile be made to
    coincide exactly with an existing evaluation chip footprint.

    Returns (tiles, stride) where each tile is (i, j, x_nw, y_nw).
    """
    xmin, ymin, xmax, ymax = validate_bbox(extent)
    overlap_m = float(overlap_m)
    if not 0.0 <= overlap_m < TILE_M:
        raise ExtentError(f"overlap must be in [0, {TILE_M}) m, got {overlap_m}")
    stride = TILE_M - overlap_m
    ox, oy = align_origin if align_origin else (xmin, ymax)
    tiles = []
    j = 0
    while True:
        ty = oy - j * stride
        i = 0
        while True:
            tx = ox + i * stride
            if tx > xmax:
                break
            tiles.append((i, j, tx, ty))
            if tx + TILE_M >= xmax + overlap_m:
                break
            i += 1
        if ty - TILE_M <= ymin:
            break
        j += 1
        if j > 4096:
            raise ExtentError("tile grid runaway")
    return tiles, stride


#: Measured per-tile cost, serial, after the read-once index landed: render 0.343 s
#: (query + make_chip on an Istanbul-density extract), inference 0.016 s, confidence
#: 0.031 s, mosaic 0.087 s. The old constant was 6.0 s/tile - a figure from before the
#: 21x speed-up that predicted 56.7 minutes for a scene that takes 4.7.
SEC_PER_TILE = 0.48

#: One-time vector index cost, which does NOT scale with tile count. Two numbers because
#: they differ by two orders of magnitude and a single estimate cannot be honest for both:
#: parsing the Turkey country extract, versus loading the cache built from it.
INDEX_PARSE_SEC = {"country": 124.0, "region": 8.0}
INDEX_CACHE_SEC = 3.4

#: Above this the extract is treated as country-sized for estimation purposes.
COUNTRY_BYTES = 150 * 1024 * 1024


def index_cost(pbf_path=None, cached=False):
    """Seconds for the one-time vector index step, and which case it is."""
    if pbf_path is None:
        return 0.0, "none"
    if cached:
        return INDEX_CACHE_SEC, "cache"
    try:
        import os
        big = os.path.getsize(pbf_path) > COUNTRY_BYTES
    except OSError:
        big = False
    return (INDEX_PARSE_SEC["country" if big else "region"],
            "country" if big else "region")


def estimate(extent, overlap_m=DEFAULT_OVERLAP_M, sec_per_tile=None,
             pbf_path=None, index_cached=False):
    """Tile count, output size and a wall-clock estimate SPLIT INTO ITS TWO TERMS.

    The one-time index step and the per-tile cost behave differently: the first is paid
    once whatever the extent, the second scales with tiles. Collapsing them into one
    number makes the estimate wrong for a first run and wrong again for a cached one, in
    opposite directions. So both are returned and the dialog shows both.
    """
    tiles, stride = tile_grid(extent, overlap_m)
    width, height, _ = output_grid(extent)
    n = len(tiles)
    spt = SEC_PER_TILE if sec_per_tile is None else float(sec_per_tile)
    idx_s, idx_kind = index_cost(pbf_path, index_cached)
    tile_s = n * spt
    return dict(n_tiles=n, stride_m=stride, width=width, height=height,
                index_seconds=idx_s, index_kind=idx_kind, tile_seconds=tile_s,
                seconds=idx_s + tile_s, megapixels=width * height / 1e6)
