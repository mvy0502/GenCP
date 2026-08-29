#!/usr/bin/env python
"""The cached index must render the SAME BYTES as a fresh parse, and reject damage.

Practice 11: the known-false cases come first. A cache that is read without being verified
is a truncated file waiting to be accepted, and this project has already accepted one.

    python tubitak/tests/index_cache_gate.py --pbf=<extract> [--n=6]
"""
from __future__ import annotations
import hashlib
import os
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import os.path as _op  # noqa: E402
sys.path.insert(0, _op.join(_op.dirname(_op.abspath(__file__))))
from _guard import strict_argv  # noqa: E402
strict_argv(known=("--pbf=", "--n="), positional=0)

from gencp_core import vectors, rasterize, extent as ext, index_cache as ic  # noqa: E402
from rasterio.warp import transform_bounds  # noqa: E402

PBF, N = None, 6
for a in sys.argv[1:]:
    if a.startswith("--pbf="):
        PBF = a.split("=", 1)[1]
    elif a.startswith("--n="):
        N = int(a.split("=", 1)[1])

CHECKS = []


def check(name, ok, detail=""):
    CHECKS.append(bool(ok))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f"  - {detail}" if detail else ""))


def main():
    if not PBF or not Path(PBF).exists():
        print("INDEX CACHE GATE: NOT RUN - pass --pbf=<an .osm.pbf>")
        return 2
    print("=" * 74)
    print("INDEX CACHE GATE")
    print("=" * 74)

    bbox = transform_bounds("EPSG:4326", "EPSG:32635",
                            28.769311, 40.840341, 29.233362, 41.293203)
    e, crs, _ = ext.resolve(bbox, "EPSG:32635")
    tiles = ext.tile_grid(e, 640.0)[0][:N]
    xs = [t[2] for t in tiles]
    ys = [t[3] for t in tiles]
    rb = (min(xs), min(ys) - ext.TILE_M, max(xs) + ext.TILE_M, max(ys))

    with tempfile.TemporaryDirectory() as cd:
        os.environ["GENCP_CACHE_DIR"] = cd

        # --- the false cases first -------------------------------------------------
        key = ic.cache_key(PBF, vectors._margin_bbox(rb, crs))
        cp = ic.cache_path(key)
        rows = vectors._pbf_rows(PBF, bbox=vectors._margin_bbox(rb, crs))
        ic.save(cp, key, rows)
        good = cp.read_bytes()

        cp.write_bytes(good[: len(good) // 2])
        check("a TRUNCATED cache is rejected", ic.load(cp, key) is None,
              f"{len(good)//2:,} of {len(good):,} bytes")

        bad = bytearray(good)
        bad[-1] ^= 0xFF
        cp.write_bytes(bytes(bad))
        check("a cache with ONE flipped byte is rejected", ic.load(cp, key) is None)

        cp.write_bytes(b"not a cache at all")
        check("garbage is rejected", ic.load(cp, key) is None)

        cp.write_bytes(good)
        other = dict(key, sha256="0" * 64)
        check("a cache built from a DIFFERENT extract is rejected",
              ic.load(cp, other) is None,
              "content-addressed, so a replaced file invalidates it")

        check("the intact cache still loads", ic.load(cp, key) is not None,
              f"{len(rows):,} rows")

        # --- and only now the true case --------------------------------------------
        os.environ["GENCP_CACHE_DIR"] = cd + "/fresh"
        t0 = time.perf_counter()
        i_parse = vectors.PbfIndex(PBF, rb, crs)
        t_parse = time.perf_counter() - t0
        check("first build parses", not i_parse.from_cache, f"{t_parse:.1f} s")

        t0 = time.perf_counter()
        i_cache = vectors.PbfIndex(PBF, rb, crs)
        t_load = time.perf_counter() - t0
        check("second build loads from cache", i_cache.from_cache, f"{t_load:.2f} s")
        check("the cache is faster than the parse", t_load < t_parse,
              f"{t_parse:.1f} s parse vs {t_load:.2f} s load "
              f"({t_parse / max(t_load, 1e-9):.0f}x)")
        check("both hold the same number of features",
              len(i_parse) == len(i_cache), f"{len(i_parse):,} vs {len(i_cache):,}")

        # byte-identity of the RENDER, which is what actually matters
        same = 0
        with tempfile.TemporaryDirectory() as d:
            for (i, j, tx, ty) in tiles:
                b = (tx, ty - ext.TILE_M, tx + ext.TILE_M, ty)
                pa, pb = Path(d) / f"a{i}_{j}.tif", Path(d) / f"b{i}_{j}.tif"
                rasterize.make_chip(b, crs, pa, gdf=i_parse.query(b, crs),
                                    pbf=PBF, base_product="clcplus", stats={})
                rasterize.make_chip(b, crs, pb, gdf=i_cache.query(b, crs),
                                    pbf=PBF, base_product="clcplus", stats={})
                same += (hashlib.sha256(pa.read_bytes()).hexdigest()
                         == hashlib.sha256(pb.read_bytes()).hexdigest())
        check("every tile renders byte-identically from cache and from parse",
              same == len(tiles), f"{same}/{len(tiles)}")

    print()
    print("=" * 74)
    print(f"INDEX CACHE GATE: {sum(CHECKS)}/{len(CHECKS)} checks passed")
    print("=" * 74)
    return 0 if all(CHECKS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
