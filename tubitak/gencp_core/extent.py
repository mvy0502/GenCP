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


def resolve(bbox, crs: str):
    """Resolve a requested extent to a projected working CRS.

    Geographic input (EPSG:4326) is reprojected to the UTM zone of the extent centre,
    because the whole chain works in metres. Anything already projected is used as-is.

    Returns (extent_in_working_crs, working_crs, source_crs).
    """
    xmin, ymin, xmax, ymax = validate_bbox(bbox)
    if not crs:
        raise ExtentError("a CRS is required")
    if crs.upper() == "EPSG:4326":
        from pyproj import Transformer
        work = utm_for((xmin + xmax) / 2.0, (ymin + ymax) / 2.0)
        tr = Transformer.from_crs(crs, work, always_xy=True)
        pts = [tr.transform(x, y) for x, y in
               ((xmin, ymin), (xmin, ymax), (xmax, ymin), (xmax, ymax))]
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
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


def estimate(extent, overlap_m=DEFAULT_OVERLAP_M, sec_per_tile=None):
    """Tile count, output size and a rough wall-clock estimate, for the dialog.

    sec_per_tile defaults to a measured CPU figure; it is a display estimate, and the
    dialog labels it as such rather than presenting it as a guarantee.
    """
    tiles, stride = tile_grid(extent, overlap_m)
    width, height, _ = output_grid(extent)
    n = len(tiles)
    spt = 6.0 if sec_per_tile is None else float(sec_per_tile)
    return dict(n_tiles=n, stride_m=stride, width=width, height=height,
                seconds=n * spt, megapixels=width * height / 1e6)
