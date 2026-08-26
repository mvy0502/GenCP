#!/usr/bin/env python
"""Gate G — the georeferencing contract.

Registered in tubitak/docs/plugin-gate-registrations.md before this ran.

A separate application consumes this GeoTIFF and extracts GCPs from it. A half-pixel
offset is invisible to us and becomes wrong GCPs downstream. So this gate reports actual
numbers, never "passed".

Two distinct things are asserted, and keeping them apart matters:

  A) GRID alignment - arithmetic on the transforms. Does the output sit on the grid the
     registered snapping rule says it should, with pixel edges coincident with the
     reference's? This is exact integer/float arithmetic, and a half-pixel bug shows up
     here as a non-zero number.

  B) CONTENT placement - does the generated imagery land where the corrected affine says
     it should? Cross-correlated against an INDEPENDENTLY computed single-tile warp of the
     same generated tile. This catches a transform that is arithmetically tidy but places
     pixels wrongly.

What this gate does NOT test is how well synthetic imagery matches real satellite imagery.
That is a scientific question, already measured by KARIOS at a median residual of roughly
1.9 px, and it is NOT a georeferencing defect. Correlating the synthetic output against a
real reference image would conflate the two, so it is not done here.
"""
from __future__ import annotations
import json, sys, warnings
from pathlib import Path

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tubitak"))

import numpy as np
import rasterio
from rasterio.transform import Affine
from rasterio.warp import reproject, Resampling

from gencp_core import extent as gext, pipeline
from gencp_core.extent import NOMINAL, TRUE_GSD, TILE_M

REF = ROOT / "tubitak/data/ankara/run/ref/ank_0_30.tif"
PBF = ROOT / "tubitak/data/tool_runs/task3/extent.osm.pbf"
MODEL = ROOT / "tubitak/data/plugin_models/gencp_C3_fp32.onnx"
OUT = ROOT / "tubitak/data/plugin_gates/gate_g"

CHECKS = []


def check(name, ok, detail):
    CHECKS.append((name, bool(ok), detail))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}\n         {detail}")


def subpixel_peak(c):
    """Parabolic refinement of a correlation peak. Returns (dy, dx) in pixels."""
    k = np.unravel_index(np.argmax(c), c.shape)
    out = []
    for ax, i in enumerate(k):
        if 0 < i < c.shape[ax] - 1:
            sl = [k[0], k[1]]
            sl[ax] = i - 1
            a = c[tuple(sl)]
            b = c[k]
            sl[ax] = i + 1
            d = c[tuple(sl)]
            den = (a - 2 * b + d)
            out.append(0.5 * (a - d) / den if den != 0 else 0.0)
        else:
            out.append(0.0)
    return k, tuple(out)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with rasterio.open(REF) as s:
        rb = s.bounds
        ref_crs, ref_T = s.crs, s.transform
    ref_extent = (rb.left, rb.bottom, rb.right, rb.top)

    print("Gate G — georeferencing contract")
    print(f"  reference layer : {REF.name}")
    print(f"  reference CRS   : {ref_crs}")
    print(f"  reference extent: {ref_extent}")
    print(f"  snapping rule   : grid anchored at the reference NW corner exactly; "
          f"w/h = ceil(span/{NOMINAL}); E and S edges may extend up to one pixel\n")

    out_tif = OUT / "gate_g_output.tif"
    res = pipeline.generate(ref_extent, ref_crs.to_string(), MODEL, out_tif,
                            pbf=str(PBF), base_product="clcplus", overlap_m=0.0,
                            work_dir=OUT / "work", seam=False)

    with rasterio.open(out_tif) as s:
        o_crs, o_T, o_w, o_h = s.crs, s.transform, s.width, s.height
        ob = s.bounds
        out_rgb = s.read()

    print("--- A. grid alignment ---")
    check("output CRS == reference CRS",
          o_crs == ref_crs, f"output {o_crs}  ==  reference {ref_crs}")

    px, py = o_T.a, -o_T.e
    check("output pixel size == 10.0 m exactly, both axes",
          px == NOMINAL and py == NOMINAL,
          f"x = {px!r} m, y = {py!r} m  (exact float equality against {NOMINAL!r})")

    exp_w, exp_h, exp_T = gext.output_grid(ref_extent)
    dx0 = o_T.c - ref_extent[0]
    dy0 = o_T.f - ref_extent[3]
    check("output NW corner == reference NW corner (snapping rule)",
          dx0 == 0.0 and dy0 == 0.0,
          f"origin offset  x {dx0!r} m, y {dy0!r} m  "
          f"(= {dx0/NOMINAL!r} px, {dy0/NOMINAL!r} px)")
    check("output size == ceil(span / GSD)",
          (o_w, o_h) == (exp_w, exp_h),
          f"got {o_w} x {o_h}, expected {exp_w} x {exp_h}  "
          f"(span {ref_extent[2]-ref_extent[0]:.1f} x {ref_extent[3]-ref_extent[1]:.1f} m)")
    over_e = ob.right - ref_extent[2]
    over_s = ref_extent[1] - ob.bottom
    check("E/S overhang within one pixel, as the rule allows",
          0 <= over_e < NOMINAL + 1e-9 and 0 <= over_s < NOMINAL + 1e-9,
          f"east overhang {over_e:.6f} m, south overhang {over_s:.6f} m "
          f"(rule permits [0, {NOMINAL}))")
    check("transform == the registered affine, term by term",
          tuple(o_T)[:6] == tuple(exp_T)[:6],
          f"got {tuple(o_T)[:6]}\n         expected {tuple(exp_T)[:6]}")

    # pixel-centre coincidence with the reference grid
    cx = (o_T.c - ref_T.c) / ref_T.a
    cy = (o_T.f - ref_T.f) / (-ref_T.e)
    check("output pixel grid is an integer offset of the reference grid",
          float(cx).is_integer() and float(cy).is_integer(),
          f"offset in reference pixels: x {cx!r}, y {cy!r} "
          f"(fractional part x {cx - round(cx)!r}, y {cy - round(cy)!r})")

    print("\n--- B. content placement (sub-pixel) ---")
    tiles = res["tiles"]
    i, j, tx, ty = tiles[0]
    fake_src = None
    from gencp_core import infer as ginfer
    model = ginfer.OnnxGenerator(MODEL)
    fake_src = model.run_image(pipeline.preview_image(res["renders"][f"{i}_{j}"]))

    indep = np.zeros((3, o_h, o_w), np.float64)
    src_T = Affine(TRUE_GSD, 0, tx, 0, -TRUE_GSD, ty)
    arr = np.moveaxis(np.asarray(fake_src, np.float64), -1, 0)
    for b in range(3):
        reproject(arr[b], indep[b], src_transform=src_T, src_crs=ref_crs,
                  dst_transform=o_T, dst_crs=ref_crs, resampling=Resampling.bilinear)

    a = out_rgb.astype(np.float64).mean(axis=0)
    b_ = indep.mean(axis=0)
    m = (a > 0) & (b_ > 0)
    inner = np.zeros_like(m)
    inner[10:-10, 10:-10] = True
    m &= inner
    check("independent warp overlaps the output", m.sum() > 1000, f"{int(m.sum())} px compared")
    maxdiff = float(np.abs(a[m] - b_[m]).max())
    check("single-tile mosaic equals the independent corrected-affine warp",
          maxdiff <= 1.0, f"max abs difference {maxdiff:.6f} DN (uint8 rounding allows 1)")

    A = np.where(m, a - a[m].mean(), 0.0)
    B = np.where(m, b_ - b_[m].mean(), 0.0)
    F = np.fft.rfft2(A) * np.conj(np.fft.rfft2(B))
    corr = np.fft.irfft2(F, s=A.shape)
    corr = np.fft.fftshift(corr)
    c0 = (A.shape[0] // 2, A.shape[1] // 2)
    win = corr[c0[0]-4:c0[0]+5, c0[1]-4:c0[1]+5]
    k, (sy, sx) = subpixel_peak(win)
    lag = (k[0] - 4, k[1] - 4)
    check("cross-correlation peaks at integer lag (0, 0)",
          lag == (0, 0), f"integer peak at lag (dy, dx) = {lag}")
    check("sub-pixel refined peak within 0.05 px of the origin",
          abs(sy) <= 0.05 and abs(sx) <= 0.05,
          f"sub-pixel offset dy = {sy:+.6f} px, dx = {sx:+.6f} px "
          f"(= {sy*NOMINAL:+.4f} m, {sx*NOMINAL:+.4f} m)")

    print("\n--- provenance embedded in the output ---")
    with rasterio.open(out_tif) as s:
        prov = json.loads(s.tags().get("GENCP_PROVENANCE", "{}"))
    for key in ("model_file", "model_sha256", "inference_path", "true_gsd_m",
                "snapping_rule"):
        v = str(prov.get(key, "MISSING"))
        print(f"  {key:16s} {v[:88]}")
    check("provenance embedded", bool(prov.get("model_sha256")),
          f"{len(prov)} fields in GENCP_PROVENANCE tag")

    failed = [n for n, ok, _ in CHECKS if not ok]
    print("\n" + "=" * 70)
    print(f"GATE G: {'PASS' if not failed else 'FAIL'} "
          f"({len(CHECKS)-len(failed)}/{len(CHECKS)} assertions)")
    if failed:
        print("  failed: " + ", ".join(failed))
    print("=" * 70)
    (OUT / "gate_g_results.json").write_text(json.dumps(
        [dict(check=n, ok=o, detail=d) for n, o, d in CHECKS], indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
