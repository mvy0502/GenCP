#!/usr/bin/env python
"""Gate ALPHA — the confidence alpha band must not disturb the validated RGB.

The claim being protected: an application that ignores the alpha band sees exactly what it
saw before alpha existed. That is only worth anything if it is asserted on the BYTES, so
this generates the same extent twice - once 3-band, once 4-band - and compares band by
band.

Also re-asserts Gate G's grid contract on the 4-band file, because adding a band must not
move a pixel, and checks that the alpha band is the CONTINUOUS score rather than the
three-band rounding.

    /opt/homebrew/Caskroom/miniforge/base/envs/gencp/bin/python tubitak/tests/gate_alpha.py
"""
from __future__ import annotations

import json
import sys
import warnings
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

from gencp_core import confidence as C, extent as gext, pipeline
from gencp_core.extent import NOMINAL

REF = ROOT / "tubitak/data/ankara/run/ref/ank_4_23.tif"
PBF = ROOT / "tubitak/data/geofabrik/ankara_chips/ank_4_23.osm.pbf"
MODEL = ROOT / "tubitak/data/plugin_models/gencp_C2_fp32.onnx"
OUT = ROOT / "tubitak/data/plugin_gates/gate_alpha"
CHECKS = []


def check(name, ok, detail=""):
    CHECKS.append((name, bool(ok), detail))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}\n         {detail}")


def run(tag, **kw):
    out = OUT / f"{tag}.tif"
    for f in (out, out.with_name(out.stem + "_osm.tif")):
        if f.exists():
            f.unlink()
    return pipeline.generate(
        EXT, CRS, str(MODEL), out, pbf=str(PBF), base_product="clcplus", overlap_m=0.0,
        work_dir=OUT / "work", confidence=True, **kw), out


def main():
    global EXT, CRS
    OUT.mkdir(parents=True, exist_ok=True)
    with rasterio.open(REF) as s:
        b = s.bounds
        EXT, CRS = (b.left, b.bottom, b.right, b.top), s.crs.to_string()
    print("Gate ALPHA — confidence in the alpha channel")
    print(f"  extent {REF.name}, arm C2, single tile\n")

    r3, p3 = run("three_band", alpha_confidence=False, band_layer=True, write_osm=False)
    r4, p4 = run("four_band", alpha_confidence=True, band_layer=False, write_osm=True)

    with rasterio.open(p3) as s3, rasterio.open(p4) as s4:
        print("--- band counts and interpretation ---")
        check("3-band file has 3 bands", s3.count == 3, f"count={s3.count}")
        check("4-band file has 4 bands", s4.count == 4, f"count={s4.count}")
        # Compared against the ENUM, not its str(): str(ColorInterp.alpha) is "6", so a
        # string test here passed nothing and failed a correctly written file.
        from rasterio.enums import ColorInterp
        check("the 4th band is declared ALPHA, not a plain extra band",
              s4.colorinterp[3] == ColorInterp.alpha,
              " ".join(c.name for c in s4.colorinterp))

        print("\n--- the claim: RGB unchanged, byte for byte ---")
        a3, a4 = s3.read(), s4.read(indexes=[1, 2, 3])
        check("RGB bands are byte-identical between the 3-band and 4-band outputs",
              np.array_equal(a3, a4),
              f"max abs difference {int(np.abs(a3.astype(int) - a4.astype(int)).max())} DN "
              f"over {a3.size} samples")
        for i, nm in enumerate("RGB"):
            check(f"band {i+1} ({nm}) identical", np.array_equal(a3[i], a4[i]),
                  f"{int(np.abs(a3[i].astype(int) - a4[i].astype(int)).max())} DN")

        print("\n--- Gate G grid contract, on the 4-BAND file ---")
        exp_w, exp_h, exp_T = gext.output_grid(EXT)
        T = s4.transform
        check("pixel size exactly 10.0 m on both axes",
              T.a == NOMINAL and -T.e == NOMINAL, f"x={T.a!r} y={-T.e!r}")
        check("origin is the reference NW corner exactly",
              T.c == EXT[0] and T.f == EXT[3],
              f"offset {T.c - EXT[0]!r} m, {T.f - EXT[3]!r} m")
        check("size == ceil(span / GSD)", (s4.width, s4.height) == (exp_w, exp_h),
              f"{s4.width}x{s4.height} vs {exp_w}x{exp_h}")
        check("transform equals the registered affine term by term",
              tuple(T)[:6] == tuple(exp_T)[:6], f"{tuple(T)[:6]}")
        check("adding a band moved nothing",
              tuple(T)[:6] == tuple(s3.transform)[:6] and
              (s3.width, s3.height) == (s4.width, s4.height),
              "3-band and 4-band share transform and shape")

        print("\n--- the alpha band is CONTINUOUS, not the 3-band rounding ---")
        alpha = s4.read(4)
        vals = np.unique(alpha)
        check("alpha takes many distinct values, not 3 or 4",
              len(vals) > 32, f"{len(vals)} distinct values in 0..255")
        bands = r4.get("_confidence_bands")
        nb = len(np.unique(bands))
        check("the band raster it is NOT is coarse by comparison", nb <= 4,
              f"band raster has {nb} distinct values")
        z = C.alpha_to_score(alpha)
        check("alpha inverts to a score in the calibrated range",
              float(z.min()) >= -C.ALPHA_RANGE - 1e-6 and float(z.max()) <= C.ALPHA_RANGE + 1e-6,
              f"z in [{z.min():.3f}, {z.max():.3f}]")

        print("\n--- provenance says what alpha is ---")
        prov = json.loads(s4.tags().get("GENCP_PROVENANCE", "{}"))
        check("alpha_band documented with its inverse mapping",
              "alpha_band" in prov and "Invert" in prov["alpha_band"],
              prov.get("alpha_band", "MISSING")[:100])
        check("provenance states the RGB bands are unchanged",
              "rgb_bands_unchanged" in prov, prov.get("rgb_bands_unchanged", "MISSING")[:70])

    print("\n--- the rasterised OSM input is written as its own file ---")
    osm = r4.get("osm_output")
    check("OSM input mosaic written", bool(osm) and Path(osm).is_file(),
          Path(osm).name if osm else "missing")
    if osm:
        with rasterio.open(osm) as so:
            check("it is the 257 px input grid, not the output grid",
                  so.width >= 257 and so.crs.to_string() == CRS,
                  f"{so.width}x{so.height} {so.crs}")

    failed = [n for n, ok, _ in CHECKS if not ok]
    print("\n" + "=" * 70)
    print(f"GATE ALPHA: {'PASS' if not failed else 'FAIL'} "
          f"({len(CHECKS)-len(failed)}/{len(CHECKS)})")
    if failed:
        print("  failed: " + "; ".join(failed))
    print("=" * 70)
    (OUT / "gate_alpha_results.json").write_text(json.dumps(
        [dict(check=n, ok=o, detail=d) for n, o, d in CHECKS], indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
