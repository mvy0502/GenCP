#!/usr/bin/env python
"""Gate R — byte-identical raster gate.

Registered in tubitak/docs/plugin-gate-registrations.md before this ran.

Renders three tiles through gencp_core.rasterize and compares them against the stored
originals. The three tiles are selected by the registered rule: the first three stems in
ascending lexicographic order of the acc_clcgate corpus whose census byte_exact == 1.

Criterion: raster payload byte-identical (exact array equality, all bands) AND
georeferencing exactly equal. Container-level file byte equality is reported separately
and is NOT the criterion (GeoTIFF headers carry writer/timestamp fields).

Supporting measurement, not a gate: the same tiles through the EXISTING script, in the
same process, to distinguish "the lift broke it" from "the archive drifted".
"""
from __future__ import annotations
import csv, hashlib, sys, warnings
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
sys.path.insert(0, str(ROOT / "tubitak" / "scripts"))

import numpy as np
import rasterio

from gencp_core import rasterize as core_rast

CENSUS = ROOT / "tubitak/data/tool_runs/task4/acc_census.csv"
ORIG_DIR = ROOT / "tubitak/data/rasteriser/chips_clc"
PBF_DIR = ROOT / "tubitak/data/geofabrik/chips"
FOOT_DIR = ROOT / "tubitak/data/karios/reference/satellite"
OUT_DIR = ROOT / "tubitak/data/plugin_gates/gate_r"

PALETTE_CLASSES = None


def select_tiles(n=3):
    """The registered selection rule. No outcome-dependent filtering."""
    rows = [r for r in csv.DictReader(open(CENSUS))
            if r["corpus"] == "acc_clcgate" and r["byte_exact"] == "1"]
    stems = sorted(r["stem"] for r in rows)
    return stems[:n]


def footprint(stem):
    with rasterio.open(FOOT_DIR / f"{stem}.tif") as s:
        b = s.bounds
        return (b.left, b.bottom, b.right, b.top), s.crs


def class_flow(a, b):
    """Dominant palette-class flows between two renders, same form as the census."""
    names = sorted(core_rast.RGB.keys())
    anchors = np.array([core_rast.RGB[k] for k in names], np.int32)

    def lab(x):
        d = ((x.reshape(-1, 1, 3).astype(np.int32) - anchors.reshape(1, -1, 3)) ** 2).sum(-1)
        return d.argmin(1)

    la, lb = lab(a), lab(b)
    diff = la != lb
    if not diff.any():
        return []
    from collections import Counter
    c = Counter(zip(la[diff].tolist(), lb[diff].tolist()))
    tot = diff.sum()
    return [(f"{names[i]}->{names[j]}", n / tot) for (i, j), n in c.most_common(2)]


def compare(stem, produced_path, tag):
    with rasterio.open(ORIG_DIR / f"{stem}.tif") as s:
        orig = s.read()
        o_t, o_c = s.transform, s.crs
    with rasterio.open(produced_path) as s:
        new = s.read()
        n_t, n_c = s.transform, s.crs

    same_px = orig.shape == new.shape and bool((orig == new).all())
    ndiff = int((orig != new).any(axis=0).sum()) if orig.shape == new.shape else -1
    total = orig.shape[1] * orig.shape[2]
    same_geo = (o_t == n_t) and (o_c == n_c)
    file_sha_orig = hashlib.sha256((ORIG_DIR / f"{stem}.tif").read_bytes()).hexdigest()
    file_sha_new = hashlib.sha256(Path(produced_path).read_bytes()).hexdigest()

    res = dict(stem=stem, tag=tag, raster_identical=same_px, geo_identical=same_geo,
               diff_px=ndiff, diff_frac=ndiff / total if ndiff >= 0 else None,
               file_sha_equal=file_sha_orig == file_sha_new,
               transform_orig=tuple(o_t)[:6], transform_new=tuple(n_t)[:6],
               crs_orig=str(o_c), crs_new=str(n_c))
    if not same_px and ndiff > 0:
        a = np.moveaxis(orig[:3], 0, -1).reshape(-1, 3)
        b = np.moveaxis(new[:3], 0, -1).reshape(-1, 3)
        res["flows"] = class_flow(a, b)
        res["max_abs_diff"] = int(np.abs(orig.astype(int) - new.astype(int)).max())
    return res


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stems = select_tiles(3)
    print("Gate R — registered tile selection rule applied")
    print("  first 3 acc_clcgate stems with census byte_exact==1:")
    for s in stems:
        print(f"    {s}")
    print()

    results = []
    for stem in stems:
        bounds, crs = footprint(stem)
        pbf = PBF_DIR / f"{stem}.osm.pbf"
        print(f"[{stem}] bounds={tuple(round(v,3) for v in bounds)} crs={crs}")

        core_out = OUT_DIR / f"{stem}.core.tif"
        core_rast.make_chip(bounds, crs, core_out, pbf=str(pbf), base_product="clcplus")
        r = compare(stem, core_out, "gencp_core.rasterize")
        results.append(r)
        print(f"   core  vs stored original: raster_identical={r['raster_identical']} "
              f"geo_identical={r['geo_identical']} diff_px={r['diff_px']}")
        if not r["raster_identical"]:
            print(f"   FLOWS: {r.get('flows')}  max_abs_diff={r.get('max_abs_diff')}")

        # supporting measurement: the existing script, same process
        import osm_to_raster as OTR
        script_out = OUT_DIR / f"{stem}.script.tif"
        OTR.make_chip(bounds, crs, script_out, pbf=str(pbf), base_product="clcplus")
        r2 = compare(stem, script_out, "scripts/osm_to_raster")
        results.append(r2)
        print(f"   script vs stored original: raster_identical={r2['raster_identical']} "
              f"diff_px={r2['diff_px']}")

        # lift equivalence: core vs script, directly
        with rasterio.open(core_out) as s1, rasterio.open(script_out) as s2:
            eq = bool((s1.read() == s2.read()).all()) and s1.transform == s2.transform
        print(f"   core vs script (lift equivalence): identical={eq}")
        results.append(dict(stem=stem, tag="core_vs_script", raster_identical=eq,
                            geo_identical=eq, diff_px=0 if eq else -1))
        print()

    gate = [r for r in results if r["tag"] == "gencp_core.rasterize"]
    passed = all(r["raster_identical"] and r["geo_identical"] for r in gate)
    print("=" * 66)
    print(f"GATE R: {'PASS' if passed else 'FAIL'}  "
          f"({sum(r['raster_identical'] and r['geo_identical'] for r in gate)}/{len(gate)} "
          "tiles byte-identical to stored originals)")
    print("=" * 66)

    import json
    (OUT_DIR / "gate_r_results.json").write_text(json.dumps(results, indent=2, default=str))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
