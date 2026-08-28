#!/usr/bin/env python
"""Gate R, extended: the whole-run PbfIndex must render the SAME BYTES as the per-tile read.

Gate R proves `make_chip` matches the original renderer. It exercises the single-tile path,
where the .osm.pbf is parsed for that one tile. The speed-up replaced that with a
read-once/query-many index, and a renderer that is fast but different is not an
optimisation - it invalidates every number this project has measured.

So this renders the same tiles both ways and compares the files byte for byte.

    python tubitak/tests/gate_r_index.py --pbf=<extract> [--n=8]
"""
from __future__ import annotations
import hashlib
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import os.path as _op  # noqa: E402
sys.path.insert(0, _op.join(_op.dirname(_op.abspath(__file__))))
from _guard import strict_argv  # noqa: E402
args = strict_argv(known=("--pbf=", "--n="), positional=0)

from gencp_core import vectors, rasterize, extent as ext  # noqa: E402

PBF = None
N = 8
for a in sys.argv[1:]:
    if a.startswith("--pbf="):
        PBF = a.split("=", 1)[1]
    elif a.startswith("--n="):
        N = int(a.split("=", 1)[1])

if not PBF or not Path(PBF).exists():
    print("GATE R-INDEX: NOT RUN - pass --pbf=<an .osm.pbf that covers the test tiles>")
    raise SystemExit(2)

from rasterio.warp import transform_bounds  # noqa: E402

bbox = transform_bounds("EPSG:4326", "EPSG:32635",
                        28.769311, 40.840341, 29.233362, 41.293203)
e, crs, _ = ext.resolve(bbox, "EPSG:32635")
tiles, _ = ext.tile_grid(e, 640.0)[0][:N], None
tiles = ext.tile_grid(e, 640.0)[0][:N]

xs = [t[2] for t in tiles]
ys = [t[3] for t in tiles]
run_bounds = (min(xs), min(ys) - ext.TILE_M, max(xs) + ext.TILE_M, max(ys))
index = vectors.PbfIndex(PBF, run_bounds, crs)
print(f"index holds {len(index):,} features for the run extent")

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

ok = 0
with tempfile.TemporaryDirectory() as d:
    d = Path(d)
    for (i, j, tx, ty) in tiles:
        b = (tx, ty - ext.TILE_M, tx + ext.TILE_M, ty)
        s1, s2 = {}, {}
        a = d / f"slow_{i}_{j}.tif"
        bb = d / f"fast_{i}_{j}.tif"
        rasterize.make_chip(b, crs, a, pbf=PBF, base_product="clcplus", stats=s1)
        rasterize.make_chip(b, crs, bb, gdf=index.query(b, crs), pbf=PBF,
                            base_product="clcplus", stats=s2)
        h1, h2 = sha(a), sha(bb)
        same = h1 == h2
        ok += same
        print(f"  [{'PASS' if same else 'FAIL'}] tile {i}_{j}  "
              f"{s1.get('n_osm_features')} vs {s2.get('n_osm_features')} features  "
              f"{h1[:16]} {'==' if same else '!='} {h2[:16]}")

print()
print("=" * 70)
print(f"GATE R-INDEX: {'PASS' if ok == len(tiles) else 'FAIL'} "
      f"({ok}/{len(tiles)} tiles byte-identical between the per-tile read and the index)")
print("=" * 70)
raise SystemExit(0 if ok == len(tiles) else 1)
