"""The GenCP rendering spec — OSM vectors composited over land cover, 257x257 px, 10 m.

LIFTED VERBATIM from `tubitak/scripts/osm_to_raster.py` (classify, render, write,
make_chip, and the palette/width/class tables). The bodies below are unchanged from the
upstream script, including operation order and every constant.

This is deliberate and it is the whole point of Gate R. The generator was trained on
inputs drawn in this exact visual language; a subtly different render — a changed blend
sigma, a reordered paint pass, a different rounding — produces an output that still looks
plausible and is silently wrong. So the lift is mechanical, and the gate requires the
rendered raster to be byte-identical to the stored originals.

Pipeline: land-cover base on the 4x grid -> classify OSM features -> paint hard edges at
4x -> box-average down -> Gaussian blend fitted to the measured edge profile (erf sigma
0.68 px) -> snap near-palette pixels back to byte-exact. Constant regions are preserved
exactly by both resampling steps, so region interiors stay byte-exact and only boundaries
blend.
"""
from __future__ import annotations
import numpy as np

from .extent import SIZE, GSD, SUPERSAMPLE
from . import palette as _palette
from . import vectors

BLEND_SIGMA = 0.60          # fitted: box(1/S) + this Gaussian ~ measured erf sigma 0.68


def _hex2rgb(h):
    if h == "white": return (255,255,255)
    if h == "black": return (0,0,0)
    h = h.lstrip("#"); return tuple(int(h[i:i+2],16) for i in (0,2,4))


_upstream = _palette.load()
color_dict = _upstream.color_dict
highway_colors = _upstream.highway_colors
natural_colors = _upstream.natural_colors
landuse_colors = _upstream.landuse_colors

RGB = {k: _hex2rgb(v) for k, v in color_dict.items()}
RGB["building"] = (165, 42, 42)

# road core widths in px at 10 m, from the VHR width table / measured 2 px median
ROAD_W = {"motorway":3,"trunk":2,"primary":2,"secondary":2,"tertiary":2,
          "residential":2,"living_street":2,"service":2,"unclassified":2,
          "road":2,"track":2,"footway":1,"path":1,"cycleway":1,"pedestrian":2}

# ESA WorldCover v200 class -> palette class. Derived from evidence (confusion vs 40
# fitting chips disjoint from all scored sets — osm-palette.md §9), not inspection.
WC_MAP = {10:"forest_green", 20:"light_green", 30:"light_green", 40:"light_green",
          50:"light_purple", 60:"no_vegetation", 70:"snow", 80:"water", 90:"water",
          95:"forest_green", 100:"light_green", 0:"black"}

# CLC+ Backbone 2021 V1_1 class -> palette class. DERIVED by confusion on the 40 fitting
# chips (osm-palette.md §11); agrees with the released CLC_color_mapping on every class
# present.
CLC_MAP = {1:"gray", 2:"forest_green", 3:"forest_green", 4:"forest_green",
           5:"light_green", 6:"light_green", 7:"light_green", 8:"light_green",
           9:"no_vegetation", 10:"water", 11:"snow", 253:"water", 254:"water",
           0:"black"}


def classify(g):
    """Split the feature frame into paint groups. Returns list of (class, geoms)."""
    from shapely.geometry import Polygon, MultiPolygon, LineString, MultiLineString
    polys = {}; lines = {}
    def addp(cls, geom):
        if cls in RGB: polys.setdefault(cls, []).append(geom)
    def addl(cls, geom, w):
        lines.setdefault((cls, w), []).append(geom)
    for idx, row in g.iterrows():
        geom = row.geometry
        if geom is None or geom.is_empty: continue
        is_poly = isinstance(geom, (Polygon, MultiPolygon))
        is_line = isinstance(geom, (LineString, MultiLineString))
        b = row.get("building")
        if isinstance(b, str) and b != "no" and is_poly:
            addp("building", geom); continue
        lu = row.get("landuse"); na = row.get("natural")
        wa = row.get("water"); ww = row.get("waterway"); hw = row.get("highway")
        le = row.get("leisure")
        if isinstance(wa, str) and is_poly: addp("water", geom); continue
        if isinstance(na, str):
            cls = natural_colors.get(na)
            if cls and is_poly: addp(cls, geom); continue
        if isinstance(lu, str):
            cls = landuse_colors.get(lu)
            if cls and is_poly: addp(cls, geom); continue
        if isinstance(le, str) and is_poly: addp("light_green", geom); continue
        if isinstance(ww, str):
            if is_poly: addp("water", geom)
            elif is_line and ww in ("river","canal"): addl("water", geom, 2)
            continue
        if isinstance(hw, str) and is_line:
            cls = highway_colors.get(hw)
            if cls: addl(cls, geom, ROAD_W.get(hw, 2))
    return polys, lines


def render(bounds_utm, crs, polys, lines, base=None, base_map=None):
    from rasterio import features as rfeat
    from rasterio.transform import from_origin
    from scipy.ndimage import gaussian_filter
    S = SUPERSAMPLE
    n = SIZE * S
    x0, y0, x1, y1 = bounds_utm
    t_hi = from_origin(x0, y1, GSD/S, GSD/S)
    img = np.zeros((n, n, 3), np.float64)
    img[:] = RGB["light_green"]                                    # fallback background
    if base is not None:                                           # land-cover base layer
        cmap = base_map if base_map is not None else WC_MAP
        for code, cls in cmap.items():
            if code == 0: continue
            m = (base == code)
            if m.any(): img[m] = RGB[cls]

    def paint(cls, geoms):
        m = rfeat.rasterize(((gm, 1) for gm in geoms), out_shape=(n, n),
                            transform=t_hi, fill=0, all_touched=False).astype(bool)
        img[m] = RGB[cls]

    # landuse/natural polygons, largest first so small parcels stay visible
    order = sorted(((c, gs) for c, gs in polys.items() if c not in ("water","building")),
                   key=lambda cg: -sum(g.area for g in cg[1]))
    for cls, gs in order: paint(cls, gs)
    if "water" in polys: paint("water", polys["water"])
    for (cls, w), gs in sorted(lines.items(), key=lambda kv: kv[0][1], reverse=True):
        half = w * GSD / 2.0
        paint(cls, [g.buffer(half, cap_style=2) for g in gs])
    if "building" in polys: paint("building", polys["building"])

    # box-average S x S, then the fitted blend
    small = img.reshape(SIZE, S, SIZE, S, 3).mean(axis=(1, 3))
    if BLEND_SIGMA > 0:
        small = np.stack([gaussian_filter(small[:,:,k], BLEND_SIGMA) for k in range(3)], -1)
    out = np.clip(np.rint(small), 0, 255).astype(np.uint8)

    # snap near-palette interior pixels back to byte-exact (within 1 DN)
    pal = np.array(sorted({RGB[k] for k in RGB}), np.int16)
    d = np.abs(out.astype(np.int16)[:,:,None,:] - pal[None,None,:,:]).max(axis=3)
    near = d.min(axis=2) <= 1
    out[near] = pal[d.argmin(axis=2)[near]].astype(np.uint8)
    return out


def write(path, arr, bounds_utm, crs):
    import rasterio
    from rasterio.transform import from_origin
    x0, y0, x1, y1 = bounds_utm
    prof = dict(driver="GTiff", height=SIZE, width=SIZE, count=3, dtype="uint8",
                crs=crs, transform=from_origin(x0, y1, GSD, GSD))
    with rasterio.open(path, "w", **prof) as d:
        d.write(np.transpose(arr, (2, 0, 1)))


def make_chip(bounds_utm, crs, out_path, gdf=None, use_worldcover=True, pbf=None,
              base_product=None):
    """base_product: None->WorldCover if use_worldcover, 'clcplus', or 'none'."""
    if gdf is None:
        gdf = vectors.fetch_pbf(bounds_utm, crs, pbf) if pbf else vectors.fetch(bounds_utm, crs)
    polys, lines = classify(gdf)
    if base_product == "clcplus":
        base, bmap = vectors.fetch_clcplus(bounds_utm, crs), CLC_MAP
    elif base_product == "none" or not use_worldcover:
        base, bmap = None, None
    else:
        base, bmap = vectors.fetch_worldcover(bounds_utm, crs), WC_MAP
    arr = render(bounds_utm, crs, polys, lines, base=base, base_map=bmap)
    write(out_path, arr, bounds_utm, crs)
    return arr
