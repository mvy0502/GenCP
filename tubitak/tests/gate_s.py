#!/usr/bin/env python
"""Gate S — the size table. Real measured on-disk sizes, no estimates.

Answers Mustafa Bey's question (WhatsApp, 26 Aug): the total model + data size, as a
byproduct of the build.

The two data rows are normalised to MB per 1000 km2 so the figure scales to any coverage
area. The test area and its area in km2 are stated so the normalisation is checkable.

Data is measured IN THE FORMAT THE PLUGIN ACTUALLY CONSUMES:
  * OSM  - a .osm.pbf extract cut with `osmium extract -s smart` (the strategy the whole
           project uses; the default `simple` silently drops boundary-crossing
           multipolygons).
  * CLC+ - a windowed clip of the CLC+ Backbone raster in the plugin's own read path,
           written with the same deflate compression the plugin writes.
"""
from __future__ import annotations
import json, os, shutil, subprocess, sys, warnings
from pathlib import Path

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tubitak"))

# Unknown arguments are refused, not ignored: a verifier that runs its default
# and prints PASS when you asked for something else is reporting on the wrong run.
import os.path as _op  # noqa: E402
sys.path.insert(0, _op.join(_op.dirname(_op.abspath(__file__)),
                            *(['..', 'tests'] if _op.basename(
                                _op.dirname(_op.abspath(__file__))) != 'tests'
                              else [])))
from _guard import strict_argv  # noqa: E402
strict_argv(known=(), positional=0)

import numpy as np
import rasterio

MODELS = ROOT / "tubitak/data/plugin_models"
OUT = ROOT / "tubitak/data/plugin_gates/gate_s"
SNAPSHOT = ROOT / "tubitak/data/geofabrik/turkey-latest.osm.pbf"

# The test area: the Ankara evaluation footprint used throughout this project, as a
# single rectangle in EPSG:32636. Stated here so the normalisation is checkable.
TEST_AREA_CRS = "EPSG:32636"
TEST_AREA = (399960.0, 4390200.0, 509760.0, 4500000.0)   # 109.8 km x 109.8 km


def mb(nbytes):
    return nbytes / 1e6


def dir_size(p: Path):
    return sum(f.stat().st_size for f in Path(p).rglob("*") if f.is_file())


def area_km2(extent):
    x0, y0, x1, y1 = extent
    return (x1 - x0) * (y1 - y0) / 1e6


def cut_osm(extent, crs, out_pbf):
    from pyproj import Transformer
    if out_pbf.exists():
        return out_pbf
    tr = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)
    x0, y0, x1, y1 = extent
    pts = [tr.transform(x, y) for x, y in ((x0, y0), (x0, y1), (x1, y0), (x1, y1))]
    bbox = (f"{min(p[0] for p in pts)},{min(p[1] for p in pts)},"
            f"{max(p[0] for p in pts)},{max(p[1] for p in pts)}")
    osmium = shutil.which("osmium") or str(Path(sys.executable).parent / "osmium")
    r = subprocess.run([osmium, "extract", "-s", "smart", "-b", bbox,
                        "-o", str(out_pbf), "--overwrite", str(SNAPSHOT)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"osmium failed: {r.stderr[-500:]}")
    return out_pbf


def clip_clc(extent, crs, out_tif):
    from gencp_core import vectors
    from rasterio.warp import transform_bounds
    from rasterio.windows import from_bounds as wfb
    if out_tif.exists():
        return out_tif
    x0, y0, x1, y1 = extent
    with rasterio.open(str(vectors.clc_path())) as src:
        bb = transform_bounds(crs, src.crs, x0, y0, x1, y1)
        win = wfb(*bb, src.transform).round_offsets().round_lengths()
        arr = src.read(1, window=win)
        prof = dict(driver="GTiff", height=arr.shape[0], width=arr.shape[1], count=1,
                    dtype=arr.dtype, crs=src.crs,
                    transform=src.window_transform(win), compress="deflate")
    with rasterio.open(out_tif, "w", **prof) as d:
        d.write(arr, 1)
    return out_tif


def onnxruntime_footprint():
    import onnxruntime
    p = Path(onnxruntime.__file__).parent
    total = dir_size(p)
    # the dist-info directory is part of what pip installs
    for sib in p.parent.glob("onnxruntime*.dist-info"):
        total += dir_size(sib)
    return p, total


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    km2 = area_km2(TEST_AREA)
    print("Gate S — measured on-disk sizes")
    print(f"  test area : {TEST_AREA} in {TEST_AREA_CRS}")
    print(f"  extent    : {(TEST_AREA[2]-TEST_AREA[0])/1000:.1f} km x "
          f"{(TEST_AREA[3]-TEST_AREA[1])/1000:.1f} km = {km2:,.0f} km2\n")

    rows = []

    for tag, name in (("ONNX model, fp32 (deployed)", "gencp_C3_fp32.onnx"),
                      ("ONNX model, fp16 (not deployed - fails Gate O)", "gencp_C3_fp16.onnx")):
        p = MODELS / name
        if p.is_file():
            rows.append((tag, mb(p.stat().st_size), None))

    ortp, ortsize = onnxruntime_footprint()
    rows.append(("onnxruntime installed footprint", mb(ortsize), None))

    pbf = cut_osm(TEST_AREA, TEST_AREA_CRS, OUT / "test_area.osm.pbf")
    rows.append((f"OSM subset (.osm.pbf, -s smart) for {km2:,.0f} km2",
                 mb(pbf.stat().st_size), mb(pbf.stat().st_size) / km2 * 1000))

    clc = clip_clc(TEST_AREA, TEST_AREA_CRS, OUT / "test_area_clc.tif")
    rows.append((f"CLC+ clip (deflate GeoTIFF) for {km2:,.0f} km2",
                 mb(clc.stat().st_size), mb(clc.stat().st_size) / km2 * 1000))

    w = max(len(r[0]) for r in rows) + 2
    print(f"{'item':<{w}}{'MB':>12}{'MB / 1000 km2':>18}")
    print("-" * (w + 30))
    for tag, size, norm in rows:
        n = f"{norm:,.2f}" if norm is not None else "n/a"
        print(f"{tag:<{w}}{size:>12,.2f}{n:>18}")
    print("-" * (w + 30))

    model_mb = next(s for t, s, _ in rows if "fp32" in t)
    fixed = model_mb + mb(ortsize)
    per1000 = sum(n for _, _, n in rows if n is not None)
    print(f"\nFIXED (model fp32 + onnxruntime), independent of coverage : "
          f"{fixed:,.1f} MB")
    print(f"PER-AREA data (OSM + CLC+ clip)                           : "
          f"{per1000:,.1f} MB per 1000 km2")
    print(f"\nWorked example — total for the {km2:,.0f} km2 test area    : "
          f"{fixed + per1000 * km2 / 1000:,.1f} MB")
    for label, a in (("Ankara province (~25,600 km2)", 25600),
                     ("Turkey (~783,600 km2)", 783600)):
        print(f"  scaled to {label:<32s}: "
              f"{fixed + per1000 * a / 1000:,.0f} MB")
    print("\nNote: CLC+ Backbone covers Europe only; the CLC+ row is the size of a CLIP "
          "for the area,\n      not of the 8.2 GB continental source, which the plugin "
          "window-reads and never ships.")

    (OUT / "gate_s_results.json").write_text(json.dumps(dict(
        test_area=TEST_AREA, crs=TEST_AREA_CRS, area_km2=km2,
        onnxruntime_path=str(ortp),
        rows=[dict(item=t, mb=s, mb_per_1000km2=n) for t, s, n in rows],
        fixed_mb=fixed, per_1000km2_mb=per1000), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
