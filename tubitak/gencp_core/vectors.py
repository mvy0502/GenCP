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
import os
from pathlib import Path
import numpy as np

from .extent import SIZE, GSD, SUPERSAMPLE

MARGIN_M = 300.0

_REPO_ROOT = Path(__file__).resolve().parents[2]

# CLC+ Backbone 2021 V1_1 (CLMS delivery, local). The repository location is only a
# default: a deployed plugin points GENCP_CLC_PATH at wherever the institution keeps it.
CLC_PATH = Path(os.environ.get("GENCP_CLC_PATH") or (
    _REPO_ROOT / "tubitak/data/clcplus/CLMS_CLCplus_RASTER_2021_010m_eu_03035_V1_1.tif"))


def clc_path(explicit=None):
    """Resolve the CLC+ raster: explicit argument, then GENCP_CLC_PATH, then the default."""
    return Path(explicit or os.environ.get("GENCP_CLC_PATH") or CLC_PATH)

WC_URL = ("https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/"
          "ESA_WorldCover_10m_2021_v200_{lat}{lon}_Map.tif")

# Tags kept from the PBF stream; must match the Overpass tag request below.
KEEP = ("building", "landuse", "natural", "water", "waterway", "highway", "leisure")


def fetch_clcplus(bounds_utm, crs, clc_path_override=None):
    """CLC+ Backbone classes on the SUPERSAMPLE grid (nearest -> speckle preserved)."""
    import rasterio
    from rasterio.transform import from_origin
    from rasterio.warp import reproject, Resampling, transform_bounds
    from rasterio.windows import from_bounds as wfb
    n = SIZE * SUPERSAMPLE
    x0, y0, x1, y1 = bounds_utm
    tgt = from_origin(x0, y1, GSD / SUPERSAMPLE, GSD / SUPERSAMPLE)
    dst = np.zeros((n, n), np.uint8)
    with rasterio.open(str(clc_path(clc_path_override))) as src:
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
    """The tile footprint plus a margin, in EPSG:4326.

    Uses rasterio's PROJ binding rather than pyproj: a pyproj CRS built on a QgsTask worker
    thread segfaults QGIS when the main thread has already built one, and this function
    runs on the worker for every tile the preview did not already cache. The same four
    corners are transformed and the same min/max taken, so the numbers are unchanged -
    confirmed by Gate R still rendering byte-identically.
    """
    from . import extent as _extent
    x0, y0, x1, y1 = bounds_utm
    xs, ys = _extent._transform_points(
        crs, "EPSG:4326",
        [x0 - MARGIN_M, x1 + MARGIN_M, x1 + MARGIN_M, x0 - MARGIN_M],
        [y0 - MARGIN_M, y0 - MARGIN_M, y1 + MARGIN_M, y1 + MARGIN_M])
    return (min(xs), min(ys), max(xs), max(ys))


def _pbf_rows(pbf_path):
    """Every KEEP-tagged feature in the extract, in file order, as dict rows.

    Split out of fetch_pbf so the single-tile path and the whole-run index share ONE
    implementation. If these ever diverge, Gate R's byte-identity claim quietly stops
    covering the fast path.
    """
    import osmium
    import shapely.wkb as swkb

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
    return rows


def pbf_coverage(pbf_path, bbox_4326):
    """(features intersecting bbox, total features, file bounds) - WITHOUT geopandas.

    Deliberately built from `_pbf_rows` and plain shapely bounds. Constructing a
    GeoDataFrame with a CRS makes pyproj build a CRS object, and this project has already
    recorded that doing that on a QgsTask worker thread SEGFAULTS QGIS - the first version
    of this coverage check crashed the end-to-end harness in exactly that way. A pre-flight
    check has no business touching the CRS machinery: bounding boxes in degrees are all it
    needs, and the extract is in EPSG:4326 already.
    """
    rows = _pbf_rows(pbf_path)
    W, S, E, N = bbox_4326
    n_in = 0
    minx = miny = float("inf")
    maxx = maxy = float("-inf")
    for r in rows:
        g = r.get("geometry")
        if g is None:
            continue
        try:
            x0, y0, x1, y1 = g.bounds
        except Exception:                          # noqa: BLE001
            continue
        if x0 < minx: minx = x0
        if y0 < miny: miny = y0
        if x1 > maxx: maxx = x1
        if y1 > maxy: maxy = y1
        if x0 <= E and x1 >= W and y0 <= N and y1 >= S:
            n_in += 1
    bounds = None if minx == float("inf") else (minx, miny, maxx, maxy)
    return n_in, len(rows), bounds


class PbfIndex:
    """Read an .osm.pbf ONCE for a whole run, then answer per-tile queries from memory.

    The measured reason. Profiling 24 consecutive Istanbul tiles put 98.7% of the render
    cost - 7.83 s of 7.94 s per tile - inside `fetch_pbf`, which walked the entire extract
    for every single tile. Drawing was 1.0% and the CLC+ window 0.3%. A 567-tile scene
    therefore parsed the same 39 MB file 567 times.

    Byte-identity is the binding constraint, so this deliberately does NOT get clever. It
    runs the same handler over the same file, keeps the rows in the same file order, and
    then applies exactly the same `.cx` clip and `.to_crs` that `fetch_pbf` applies. The
    only addition is a one-off pre-clip to the union of every tile's footprint, which
    cannot change any per-tile answer: `.cx` selects on bounding-box intersection, so a
    feature that survives a tile's box necessarily survives a box containing it.
    """

    def __init__(self, pbf_path, run_bounds_utm=None, crs=None):
        import geopandas as gpd
        rows = _pbf_rows(pbf_path)
        self.path = str(pbf_path)
        self.n_file = len(rows)
        # Coverage of the FEATURES, computed before the run clip and therefore free. Node
        # bounds would be the cheaper answer and the wrong one: `osmium extract -s smart`
        # pulls in member nodes of ways that cross the cut, so a city-sized extract reports
        # a node bbox spanning half a continent. What a caller needs to know is where this
        # file can actually draw something.
        self.file_bounds = None
        self._empty = not rows
        if self._empty:
            self._gdf = gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")
            return
        g = gpd.GeoDataFrame(rows, crs="EPSG:4326")
        try:
            self.file_bounds = tuple(float(v) for v in g.total_bounds)
        except Exception:                          # noqa: BLE001
            self.file_bounds = None
        if run_bounds_utm is not None and crs is not None:
            W, S, E, N = _margin_bbox(run_bounds_utm, crs)
            g = g.cx[W:E, S:N]
        self._gdf = g
        self._empty = len(g) == 0

    def __len__(self):
        return len(self._gdf)

    def query(self, bounds_utm, crs):
        """The same GeoDataFrame `fetch_pbf` would have returned for this footprint."""
        import geopandas as gpd
        if self._empty:
            return gpd.GeoDataFrame(geometry=[], crs="EPSG:4326").to_crs(crs)
        W, S, E, N = _margin_bbox(bounds_utm, crs)
        return self._gdf.cx[W:E, S:N].to_crs(crs)


def fetch_pbf(bounds_utm, crs, pbf_path):
    """Read OSM features for a UTM footprint from a LOCAL .osm.pbf extract.

    Single-tile path. A whole run should use `PbfIndex`, which reads the file once instead
    of once per tile; both go through `_pbf_rows`, so they cannot drift apart.
    """
    import geopandas as gpd
    W, S, E, N = _margin_bbox(bounds_utm, crs)
    rows = _pbf_rows(pbf_path)
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
