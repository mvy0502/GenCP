#!/usr/bin/env python
"""Render OSM vector data into GenCP-convention categorical rasters.

Output: 257x257 px, 10 m, north-up, single UTM CRS, the 11-colour palette of
``osm-palette.md`` §2 byte-exact in region interiors, and the measured edge
profile of §8 (erf sigma = 0.68 px) at boundaries.

Pipeline: fetch OSM via Overpass (osmnx) -> classify features -> rasterize hard
edges at SUPERSAMPLE x resolution -> box-average down -> Gaussian blend fitted to
the measured profile. Constant regions are preserved exactly by both steps, so
interiors stay byte-exact; only boundaries blend.

Choices for the axes the sensitivity experiment showed are cheap (all LOOSE):
  draw order   background -> landuse/natural (large polygons first) -> water ->
               roads -> buildings on top
  buildings    #a52a2a fill, no outline
  black/snow   not rendered (CORINE-derived upstream; measured cost ~0)
  background   light_green (the corpus-dominant class)

Usage
-----
    python tubitak/scripts/osm_to_raster.py --bounds E N --crs EPSG:32636 --out chip.tif
    python tubitak/scripts/osm_to_raster.py --like reference_chip.tif --out chip.tif
"""
from __future__ import annotations
import argparse, sys, warnings
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "GenCP_HR_demo"))
from genCP_HR_osm_colors import (color_dict, highway_colors,   # noqa: E402
                                 natural_colors, landuse_colors)

SIZE, GSD = 257, 10.0
SUPERSAMPLE = 4
BLEND_SIGMA = 0.60          # fitted: box(1/S) + this Gaussian ~ measured erf sigma 0.68
MARGIN_M = 300.0

def hex2rgb(h):
    if h == "white": return (255,255,255)
    if h == "black": return (0,0,0)
    h = h.lstrip("#"); return tuple(int(h[i:i+2],16) for i in (0,2,4))

RGB = {k: hex2rgb(v) for k, v in color_dict.items()}
RGB["building"] = (165, 42, 42)

# road core widths in px at 10 m, from the VHR width table / measured 2 px median
ROAD_W = {"motorway":3,"trunk":2,"primary":2,"secondary":2,"tertiary":2,
          "residential":2,"living_street":2,"service":2,"unclassified":2,
          "road":2,"track":2,"footway":1,"path":1,"cycleway":1,"pedestrian":2}

def fetch(bounds_utm, crs):
    """Fetch OSM features for a UTM footprint (+margin), reprojected to that CRS."""
    import osmnx as ox
    ox.settings.cache_folder = str(ROOT / "tubitak" / "data" / "osmnx_cache")
    from pyproj import Transformer
    tr = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)
    x0, y0, x1, y1 = bounds_utm
    lonlat = [tr.transform(x, y) for x, y in
              ((x0-MARGIN_M,y0-MARGIN_M),(x1+MARGIN_M,y0-MARGIN_M),
               (x1+MARGIN_M,y1+MARGIN_M),(x0-MARGIN_M,y1+MARGIN_M))]
    lons = [p[0] for p in lonlat]; lats = [p[1] for p in lonlat]
    bbox = (min(lons), min(lats), max(lons), max(lats))
    tags = {"landuse": True, "natural": True, "water": True, "waterway": True,
            "highway": True, "building": True, "leisure": ["park","pitch","garden"]}
    try:
        g = ox.features_from_bbox(bbox, tags)
    except Exception as e:
        if "InsufficientResponseError" in type(e).__name__:
            import geopandas as gpd
            return gpd.GeoDataFrame(geometry=[], crs="EPSG:4326").to_crs(crs)
        raise
    return g.to_crs(crs)

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

def render(bounds_utm, crs, polys, lines):
    from rasterio import features as rfeat
    from rasterio.transform import from_origin
    from scipy.ndimage import gaussian_filter, zoom
    S = SUPERSAMPLE
    n = SIZE * S
    x0, y0, x1, y1 = bounds_utm
    t_hi = from_origin(x0, y1, GSD/S, GSD/S)
    img = np.zeros((n, n, 3), np.float64)
    img[:] = RGB["light_green"]                                    # background

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

def make_chip(bounds_utm, crs, out_path, gdf=None):
    if gdf is None:
        gdf = fetch(bounds_utm, crs)
    polys, lines = classify(gdf)
    arr = render(bounds_utm, crs, polys, lines)
    write(out_path, arr, bounds_utm, crs)
    return arr

def main() -> int:
    warnings.filterwarnings("ignore")
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--like", help="reference GeoTIFF whose footprint+CRS to copy")
    ap.add_argument("--bounds", nargs=2, type=float, metavar=("EASTING","NORTHING"),
                    help="NW corner in the target CRS; chip extends 2570 m E and S")
    ap.add_argument("--crs", default=None, help="e.g. EPSG:32636")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    if a.like:
        import rasterio
        with rasterio.open(a.like) as s:
            b = s.bounds; crs = s.crs
        bounds = (b.left, b.bottom, b.right, b.top)
    else:
        e, n0 = a.bounds; crs = a.crs
        bounds = (e, n0 - SIZE*GSD, e + SIZE*GSD, n0)
    make_chip(bounds, crs, a.out)
    print(f"wrote {a.out}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
