#!/usr/bin/env python
"""Wrong extract blocks; right extract runs; partial extract warns without blocking.

An Istanbul run of 567 tiles was once generated against an Ankara test extract. Zero OSM
features in all 567 tiles, every one drawn from land cover alone, and a day of analysis
spent on the result before anyone read the provenance. `coverage_warnings` had detected it
perfectly and had no authority to stop anything.

The distinction under test is structural, not a threshold:
  * SOME tiles sparse  -> warn, keep going. A real condition with a real output.
  * EVERY tile zero    -> block before the first tile is rendered. The extract does not
                          cover the extent, and nothing useful can come of continuing.

    python tubitak/tests/coverage_block.py --wrong=<pbf> --right=<pbf> [--partial=<pbf>]
"""
from __future__ import annotations
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import os.path as _op  # noqa: E402
sys.path.insert(0, _op.join(_op.dirname(_op.abspath(__file__))))
from _guard import strict_argv  # noqa: E402
strict_argv(known=("--wrong=", "--right=", "--partial="), positional=0)

from gencp_core import pipeline  # noqa: E402
from rasterio.warp import transform_bounds  # noqa: E402

ARG = {}
for a in sys.argv[1:]:
    if a.startswith("--") and "=" in a:
        k, v = a[2:].split("=", 1)
        ARG[k] = v

CHECKS = []


def check(name, ok, detail=""):
    CHECKS.append(bool(ok))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f"  - {detail}" if detail else ""))


IST = transform_bounds("EPSG:4326", "EPSG:32635",
                       28.769311, 40.840341, 29.233362, 41.293203)
MODEL = Path(__file__).resolve().parents[1] / "data/plugin_models/gencp_C2_fp32.onnx"


def attempt(pbf, cancel_after_check=True):
    """Returns ('blocked', exc) | ('ran', stats) | ('cancelled', None)."""
    with tempfile.TemporaryDirectory() as d:
        try:
            res = pipeline.generate(
                IST, "EPSG:32635", str(MODEL), f"{d}/o.tif", pbf=pbf,
                base_product="clcplus", overlap_m=640.0, work_dir=f"{d}/wd",
                seam=False, workers=1,
                cancelled=(lambda: True) if cancel_after_check else None)
            return "ran", res
        except pipeline.ExtentNotCovered as e:
            return "blocked", e
        except pipeline.Cancelled:
            return "cancelled", None


def main():
    print("=" * 74)
    print("COVERAGE BLOCK")
    print("=" * 74)

    # --- A. wrong extract: must block, before rendering, with both boxes -------------
    t0 = time.perf_counter()
    kind, e = attempt(ARG["wrong"])
    dt = time.perf_counter() - t0
    check("A. an extract that does not cover the extent BLOCKS", kind == "blocked", kind)
    if kind == "blocked":
        msg = str(e)
        check("   it blocks before generation, in seconds not minutes", dt < 60,
              f"{dt:.1f} s")
        check("   the message names the file", Path(ARG['wrong']).name in msg)
        check("   it shows what the file covers", e.pbf_bounds is not None,
              e._fmt(e.pbf_bounds))
        check("   it shows what was requested", e.want_bounds is not None,
              e._fmt(e.want_bounds))
        check("   the two boxes genuinely do not overlap",
              not (e.pbf_bounds[0] < e.want_bounds[2] and e.pbf_bounds[2] > e.want_bounds[0]
                   and e.pbf_bounds[1] < e.want_bounds[3] and e.pbf_bounds[3] > e.want_bounds[1]))
        check("   it says what to do", "Overpass" in msg or "extract that covers" in msg)

    # --- B. right extract: must NOT block --------------------------------------------
    kind, _ = attempt(ARG["right"])
    check("B. an extract that covers the extent does NOT block",
          kind in ("cancelled", "ran"), kind)

    # --- C. partial coverage: warns, does not block ----------------------------------
    if ARG.get("partial"):
        kind, _ = attempt(ARG["partial"])
        check("C. an extract covering only PART of the extent does not block",
              kind in ("cancelled", "ran"), kind)
        # and the sparse warning still fires for the uncovered tiles
        stats = {}
        from gencp_core import extent as _ex, vectors as _v
        e2, crs, _ = _ex.resolve(IST, "EPSG:32635")
        tiles, _s = _ex.tile_grid(e2, 640.0)
        xs = [t[2] for t in tiles]; ys = [t[3] for t in tiles]
        idx = _v.PbfIndex(ARG["partial"],
                          (min(xs), min(ys) - _ex.TILE_M,
                           max(xs) + _ex.TILE_M, max(ys)), crs)
        zero = 0
        for (i, j, tx, ty) in tiles:
            b = (tx, ty - _ex.TILE_M, tx + _ex.TILE_M, ty)
            n = len(idx.query(b, crs))
            stats[(i, j)] = {"n_osm_features": n}
            zero += (n == 0)
        w = pipeline.coverage_warnings(stats, ARG["partial"])
        check("   some tiles are empty and some are not",
              0 < zero < len(tiles), f"{zero} of {len(tiles)} tiles empty")
        check("   the non-blocking sparse warning still fires",
              any(x.get("kind") == "zero_osm" for x in w),
              str(w)[:90])
    else:
        print("  (C skipped: no --partial extract given)")

    print()
    print("=" * 74)
    print(f"COVERAGE BLOCK: {sum(CHECKS)}/{len(CHECKS)} checks passed")
    print("=" * 74)
    return 0 if all(CHECKS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
