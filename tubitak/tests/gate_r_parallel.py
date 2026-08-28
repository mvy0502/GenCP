#!/usr/bin/env python
"""The parallel renderer must produce the SAME BYTES as the serial one, tile by tile.

"It looks fine" is not a check. Tiles finish in a different order under a process pool,
each worker builds its own index over its own block, and blocks have different bounds - all
three are places where a different answer could hide. So render the same tiles both ways
into separate directories and compare SHA-256 per tile.

    python tubitak/tests/gate_r_parallel.py --pbf=<extract> [--n=24] [--workers=8]
"""
from __future__ import annotations
import hashlib
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import os.path as _op  # noqa: E402
sys.path.insert(0, _op.join(_op.dirname(_op.abspath(__file__))))
from _guard import strict_argv  # noqa: E402
strict_argv(known=("--pbf=", "--n=", "--workers="), positional=0)

from gencp_core import pipeline, extent as ext  # noqa: E402
from rasterio.warp import transform_bounds  # noqa: E402

PBF, N, W = None, 24, 8
for a in sys.argv[1:]:
    if a.startswith("--pbf="):
        PBF = a.split("=", 1)[1]
    elif a.startswith("--n="):
        N = int(a.split("=", 1)[1])
    elif a.startswith("--workers="):
        W = int(a.split("=", 1)[1])
# Everything below runs under a __main__ guard. Without it, multiprocessing's "spawn"
# start method re-imports this file in every child, which re-runs the pool creation, which
# spawns more children - the first attempt at this test forked until the machine complained.
def main():
    if not PBF or not Path(PBF).exists():
        print("GATE R-PARALLEL: NOT RUN - pass --pbf=<an .osm.pbf covering the tiles>")
        return 2
    bbox = transform_bounds("EPSG:4326", "EPSG:32635",
                            28.769311, 40.840341, 29.233362, 41.293203)
    e, crs, _ = ext.resolve(bbox, "EPSG:32635")
    tiles = ext.tile_grid(e, 640.0)[0][:N]


    def sha(p):
        return hashlib.sha256(Path(p).read_bytes()).hexdigest()


    def run(workers, d):
        seen = []
        t0 = time.perf_counter()
        out = pipeline.render_inputs(tiles, crs, Path(d), pbf=PBF, base_product="clcplus",
                                     workers=workers, stats_out={},
                                     progress=lambda n, t: seen.append(n))
        return out, time.perf_counter() - t0, seen


    with tempfile.TemporaryDirectory() as d1, tempfile.TemporaryDirectory() as d2:
        ser, t_ser, _ = run(1, d1)
        par, t_par, prog = run(W, d2)

        # Compare INSIDE the context: the first version of this test hashed after the
        # temporary directories had been removed and failed on a missing file.
        same = 0
        for ij in ser:
            h1, h2 = sha(ser[ij]), sha(par[ij])
            same += h1 == h2
            if h1 != h2:
                print(f"  [FAIL] tile {ij}  {h1[:16]} != {h2[:16]}")

    print(f"  [{'PASS' if same == len(ser) else 'FAIL'}] "
          f"{same}/{len(ser)} tiles byte-identical between serial and {W}-way parallel")
    keys_match = sorted(map(str, ser)) == sorted(map(str, par))
    print(f"  [{'PASS' if keys_match else 'FAIL'}] the same tiles were produced by both")
    mono = all(b >= a for a, b in zip(prog, prog[1:]))
    never_early = all(n <= len(tiles) for n in prog)
    ends_full = (not prog) or prog[-1] == len(tiles)
    print(f"  [{'PASS' if mono else 'FAIL'}] progress never goes backwards  - {prog}")
    print(f"  [{'PASS' if never_early else 'FAIL'}] progress never exceeds the tile count")
    print(f"  [{'PASS' if ends_full else 'FAIL'}] progress reaches 100% only at the end")
    print(f"\n  serial   {t_ser:6.2f} s   ({t_ser/len(tiles):.3f} s/tile)")
    print(f"  {W}-way    {t_par:6.2f} s   ({t_par/len(tiles):.3f} s/tile)   "
          f"speed-up {t_ser/t_par:.2f}x")
    ok = same == len(ser) and keys_match and mono and never_early and ends_full
    print("\n" + "=" * 70)
    print(f"GATE R-PARALLEL: {'PASS' if ok else 'FAIL'}")
    print("=" * 70)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
