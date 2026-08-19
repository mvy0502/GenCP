#!/usr/bin/env python
"""Render OSM vector data into GenCP-convention categorical rasters.

Output: 257x257 px, 10 m, north-up, single UTM CRS, the 11-colour palette of
``osm-palette.md`` §2 byte-exact in region interiors, and the measured edge
profile of §8 (erf sigma = 0.68 px) at boundaries.

Pipeline: fetch OSM via Overpass (osmnx) -> classify features -> rasterize hard
edges at SUPERSAMPLE x resolution -> box-average down -> Gaussian blend fitted to
the measured profile. Constant regions are preserved exactly by both steps, so
interiors stay byte-exact; only boundaries blend.

Base layer: **ESA WorldCover 10 m (v200, 2021)**, window-read remotely from the
public COGs and reprojected nearest-neighbour so its per-pixel speckle survives —
the acceptance-test diagnosis showed the reference composites OSM vectors over a
per-pixel land-cover raster (sea/lakes and vegetation texture come from it).
OSM vectors are painted on top; the shared box+Gaussian stage then applies the
fitted edge profile to base and vectors alike.

Choices for the axes the sensitivity experiment showed are cheap (all LOOSE):
  draw order   WorldCover base -> landuse/natural (large polygons first) ->
               water -> roads -> buildings on top
  buildings    #a52a2a fill, no outline
  black/snow   snow from WorldCover class 70; black only where WC has nodata

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

# ESA WorldCover v200 class -> palette class (semantics follow CLC_color_mapping:
# trees->forest_green, low vegetation->light_green, built->gray, bare->no_vegetation,
# snow->snow, water->water, nodata->black)
# Derived from evidence (confusion vs 40 fitting chips disjoint from all scored
# sets — see osm-palette.md §9), not inspection. Two classes corrected from the
# initial inspected guess: 50 built -> light_purple (was gray; evidence 29% purple /
# 25% building / 13% gray, AMBIGUOUS plurality), 90 wetland -> water (85.4%, was
# light_green). 60 bare kept as no_vegetation on semantics (near-tie 45/41 with
# light_green). 70/95/100 absent from the fitting data: semantic defaults, unverified.
WC_MAP = {10:"forest_green", 20:"light_green", 30:"light_green", 40:"light_green",
          50:"light_purple", 60:"no_vegetation", 70:"snow", 80:"water", 90:"water",
          95:"forest_green", 100:"light_green", 0:"black"}
WC_URL = ("https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/"
          "ESA_WorldCover_10m_2021_v200_{lat}{lon}_Map.tif")

def wc_tiles(lonlat_bounds):
    """SW-corner names of the 3-degree WorldCover tiles covering a WGS84 bbox."""
    import math
    w, s_, e, n = lonlat_bounds
    tiles = set()
    for lon in range(int(math.floor(w/3))*3, int(math.floor(e/3))*3+1, 3):
        for lat in range(int(math.floor(s_/3))*3, int(math.floor(n/3))*3+1, 3):
            tiles.add(("N%02d"%lat if lat >= 0 else "S%02d"%-lat,
                       "E%03d"%lon if lon >= 0 else "W%03d"%-lon))
    return sorted(tiles)

def fetch_worldcover(bounds_utm, crs):
    """WorldCover classes on the SUPERSAMPLE grid (nearest -> speckle preserved)."""
    import rasterio
    from rasterio.transform import from_origin
    from rasterio.warp import reproject, Resampling, transform_bounds
    n = SIZE * SUPERSAMPLE
    x0, y0, x1, y1 = bounds_utm
    tgt = from_origin(x0, y1, GSD/SUPERSAMPLE, GSD/SUPERSAMPLE)
    dst = np.zeros((n, n), np.uint8)
    ll = transform_bounds(crs, "EPSG:4326", x0-200, y0-200, x1+200, y1+200)
    for lat, lon in wc_tiles(ll):
        url = WC_URL.format(lat=lat, lon=lon)
        try:
            with rasterio.open(url) as src:
                from rasterio.windows import from_bounds as wfb
                win = wfb(ll[0], ll[1], ll[2], ll[3], src.transform)
                win = win.round_offsets().round_lengths()
                if win.width <= 0 or win.height <= 0: continue
                arr = src.read(1, window=win)
                wtr = src.window_transform(win)
            tmp = np.zeros_like(dst)
            reproject(source=arr, destination=tmp, src_transform=wtr,
                      src_crs="EPSG:4326", dst_transform=tgt, dst_crs=crs,
                      resampling=Resampling.nearest)
            dst = np.where(tmp > 0, tmp, dst)
        except rasterio.errors.RasterioIOError:
            continue                      # ocean-only tiles are not published
    return dst

def fetch_pbf(bounds_utm, crs, pbf_path):
    """Read OSM features for a UTM footprint from a LOCAL .osm.pbf extract.

    Same return contract as :func:`fetch` (GeoDataFrame in `crs` with tag columns
    consumed by :func:`classify`), but from a fixed, dated Geofabrik snapshot:
    reproducible, no rate limits. Areas come from osmium's area assembler, which
    handles multipolygon relations; lines (highways, rivers) from the way stream.
    """
    import osmium
    import shapely.wkb as swkb
    import geopandas as gpd
    from pyproj import Transformer
    tr = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)
    x0, y0, x1, y1 = bounds_utm
    pts = [tr.transform(x, y) for x, y in
           ((x0-MARGIN_M,y0-MARGIN_M),(x1+MARGIN_M,y0-MARGIN_M),
            (x1+MARGIN_M,y1+MARGIN_M),(x0-MARGIN_M,y1+MARGIN_M))]
    W=min(p[0] for p in pts); S=min(p[1] for p in pts)
    E=max(p[0] for p in pts); N=max(p[1] for p in pts)

    KEEP = ("building","landuse","natural","water","waterway","highway","leisure")
    fab = osmium.geom.WKBFactory()
    rows = []

    class H(osmium.SimpleHandler):
        def area(self, a):
            t = {k: a.tags.get(k) for k in KEEP if k in a.tags}
            # parity with the Overpass fetch: leisure restricted to the same subset
            if t.get("leisure") not in (None, "park", "pitch", "garden"):
                del t["leisure"]
            if not t: return
            try: g = swkb.loads(fab.create_multipolygon(a), hex=True)
            except Exception: return
            t["geometry"] = g; rows.append(t)
        def way(self, w):
            if w.is_closed(): return          # closed ways surface via area()
            t = {}
            if "highway" in w.tags: t["highway"] = w.tags.get("highway")
            if "waterway" in w.tags: t["waterway"] = w.tags.get("waterway")
            if not t: return
            try: g = swkb.loads(fab.create_linestring(w), hex=True)
            except Exception: return
            t["geometry"] = g; rows.append(t)

    H().apply_file(str(pbf_path), locations=True)
    if not rows:
        return gpd.GeoDataFrame(geometry=[], crs="EPSG:4326").to_crs(crs)
    g = gpd.GeoDataFrame(rows, crs="EPSG:4326")
    g = g.cx[W:E, S:N]                        # clip to the footprint+margin
    return g.to_crs(crs)

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

def render(bounds_utm, crs, polys, lines, base=None):
    from rasterio import features as rfeat
    from rasterio.transform import from_origin
    from scipy.ndimage import gaussian_filter
    S = SUPERSAMPLE
    n = SIZE * S
    x0, y0, x1, y1 = bounds_utm
    t_hi = from_origin(x0, y1, GSD/S, GSD/S)
    img = np.zeros((n, n, 3), np.float64)
    img[:] = RGB["light_green"]                                    # fallback background
    if base is not None:                                           # WorldCover base layer
        for code, cls in WC_MAP.items():
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

def make_chip(bounds_utm, crs, out_path, gdf=None, use_worldcover=True, pbf=None):
    if gdf is None:
        gdf = fetch_pbf(bounds_utm, crs, pbf) if pbf else fetch(bounds_utm, crs)
    polys, lines = classify(gdf)
    base = fetch_worldcover(bounds_utm, crs) if use_worldcover else None
    arr = render(bounds_utm, crs, polys, lines, base=base)
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
