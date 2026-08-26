"""OSM and land-cover acquisition.

LIFTED VERBATIM from `tubitak/scripts/osm_to_raster.py` (fetch_pbf, fetch, fetch_clcplus,
fetch_worldcover, wc_tiles). The bodies are unchanged: Gate R requires the render to be
byte-identical, and the vector acquisition is half of what the render sees.

Two OSM sources, both returning the same contract — a GeoDataFrame in the working CRS with
the tag columns `rasterize.classify` consumes:

  * `fetch_pbf`  a local, dated .osm.pbf extract. Reproducible, no rate limits, offline.
    Areas come from osmium's area assembler so multipolygon relations survive; note that
    extraction upstream of this must use `osmium extract -s smart`, because the default
    `simple` strategy silently drops boundary-crossing multipolygons (corrections-log
    entry 6).
  * `fetch`      online Overpass via osmnx. Convenient, but rate-limited and undated.

The base land-cover layer is CLC+ Backbone 2021 (local raster, what the upstream renderer
actually used) or ESA WorldCover (remote COGs). Both are read onto the SUPERSAMPLE grid
with nearest-neighbour resampling so their per-pixel speckle survives — the acceptance-test
diagnosis showed the reference composites OSM vectors over a per-pixel land-cover raster.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np

from .extent import SIZE, GSD, SUPERSAMPLE

MARGIN_M = 300.0

_REPO_ROOT = Path(__file__).resolve().parents[2]

# CLC+ Backbone 2021 V1_1 (CLMS delivery, local).
CLC_PATH = (_REPO_ROOT /
            "tubitak/data/clcplus/CLMS_CLCplus_RASTER_2021_010m_eu_03035_V1_1.tif")

WC_URL = ("https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/"
          "ESA_WorldCover_10m_2021_v200_{lat}{lon}_Map.tif")

# Tags kept from the PBF stream; must match the Overpass tag request below.
KEEP = ("building", "landuse", "natural", "water", "waterway", "highway", "leisure")


def fetch_clcplus(bounds_utm, crs, clc_path=None):
    """CLC+ Backbone classes on the SUPERSAMPLE grid (nearest -> speckle preserved)."""
    import rasterio
    from rasterio.transform import from_origin
    from rasterio.warp import reproject, Resampling, transform_bounds
    from rasterio.windows import from_bounds as wfb
    n = SIZE * SUPERSAMPLE
    x0, y0, x1, y1 = bounds_utm
    tgt = from_origin(x0, y1, GSD / SUPERSAMPLE, GSD / SUPERSAMPLE)
    dst = np.zeros((n, n), np.uint8)
    with rasterio.open(str(clc_path or CLC_PATH)) as src:
        bb = transform_bounds(crs, src.crs, x0 - 200, y0 - 200, x1 + 200, y1 + 200)
        win = wfb(*bb, src.transform).round_offsets().round_lengths()
        arr = src.read(1, window=win)
        wtr = src.window_transform(win)
        reproject(source=arr, destination=dst, src_transform=wtr, src_crs=src.crs,
                  dst_transform=tgt, dst_crs=crs, resampling=Resampling.nearest)
    return dst


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


def _margin_bbox(bounds_utm, crs):
    from pyproj import Transformer
    tr = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)
    x0, y0, x1, y1 = bounds_utm
    pts = [tr.transform(x, y) for x, y in
           ((x0 - MARGIN_M, y0 - MARGIN_M), (x1 + MARGIN_M, y0 - MARGIN_M),
            (x1 + MARGIN_M, y1 + MARGIN_M), (x0 - MARGIN_M, y1 + MARGIN_M))]
    return (min(p[0] for p in pts), min(p[1] for p in pts),
            max(p[0] for p in pts), max(p[1] for p in pts))


def fetch_pbf(bounds_utm, crs, pbf_path):
    """Read OSM features for a UTM footprint from a LOCAL .osm.pbf extract."""
    import osmium
    import shapely.wkb as swkb
    import geopandas as gpd
    W, S, E, N = _margin_bbox(bounds_utm, crs)

    fab = osmium.geom.WKBFactory()
    rows = []

    class H(osmium.SimpleHandler):
        def area(self, a):
            t = {k: a.tags.get(k) for k in KEEP if k in a.tags}
            # parity with the Overpass fetch: leisure restricted to the same subset
            if t.get("leisure") not in (None, "park", "pitch", "garden"):
                del t["leisure"]
            if not t:
                return
            try:
                g = swkb.loads(fab.create_multipolygon(a), hex=True)
            except Exception:
                return
            t["geometry"] = g
            rows.append(t)

        def way(self, w):
            if w.is_closed():
                return          # closed ways surface via area()
            t = {}
            if "highway" in w.tags:
                t["highway"] = w.tags.get("highway")
            if "waterway" in w.tags:
                t["waterway"] = w.tags.get("waterway")
            if not t:
                return
            try:
                g = swkb.loads(fab.create_linestring(w), hex=True)
            except Exception:
                return
            t["geometry"] = g
            rows.append(t)

    H().apply_file(str(pbf_path), locations=True)
    if not rows:
        return gpd.GeoDataFrame(geometry=[], crs="EPSG:4326").to_crs(crs)
    g = gpd.GeoDataFrame(rows, crs="EPSG:4326")
    g = g.cx[W:E, S:N]                        # clip to the footprint+margin
    return g.to_crs(crs)


def fetch(bounds_utm, crs, cache_folder=None):
    """Fetch OSM features for a UTM footprint (+margin) from Overpass, via osmnx."""
    import osmnx as ox
    ox.settings.cache_folder = str(
        cache_folder or (_REPO_ROOT / "tubitak" / "data" / "osmnx_cache"))
    bbox = _margin_bbox(bounds_utm, crs)
    tags = {"landuse": True, "natural": True, "water": True, "waterway": True,
            "highway": True, "building": True, "leisure": ["park", "pitch", "garden"]}
    try:
        g = ox.features_from_bbox(bbox, tags)
    except Exception as e:
        if "InsufficientResponseError" in type(e).__name__:
            import geopandas as gpd
            return gpd.GeoDataFrame(geometry=[], crs="EPSG:4326").to_crs(crs)
        raise
    return g.to_crs(crs)
