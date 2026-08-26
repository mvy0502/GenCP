#!/usr/bin/env python
"""Regression test: a second run over a DIFFERENT extent must not reuse the first render.

Was a probe first, and it found the bug. Kept as a test so the bug cannot come back.

`pipeline.render_inputs` skips rendering when the cache file already exists, and `generate`
defaults `work_dir` to a FIXED path under the system temp directory. The name USED to be
`t_{i}_{j}.tif`, carrying only the tile INDEX - not the extent, the CRS, the OSM source or
the CLC+ path - so two different extents both produced a tile (0,0) and the second run read
the first run's file and wrote a confidently wrong raster with no error.

This script does not argue that. It runs two different extents through the same code path
the dialog uses and compares the rasters, then re-runs the first extent to confirm the
cache still does its job. Before the fix the first assertion read True.

Run through the QGIS application binary (onnxruntime; see run_in_qgis.sh).
"""
from __future__ import annotations
import os, sys, shutil, tempfile
from pathlib import Path

try:
    ROOT = Path(__file__).resolve().parents[2]
except NameError:                                    # pragma: no cover - --code path
    ROOT = Path(os.environ.get("GENCP_REPO_ROOT", os.getcwd())).resolve()
sys.path.insert(0, str(ROOT / "tubitak"))

_OUT = open(os.environ.get("GENCP_TEST_OUT", "/tmp/gencp_cache_probe.txt"), "w")


def say(*a):
    print(*a, file=_OUT, flush=True)


def main():
    import numpy as np
    import rasterio
    from gencp_core import pipeline

    MODEL = ROOT / "tubitak/data/plugin_models/gencp_C3_fp32.onnx"
    PBF = ROOT / "tubitak/data/tool_runs/task3/extent.osm.pbf"
    OUT = ROOT / "tubitak/data/plugin_gates/cache_probe"
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    shared_work = Path(tempfile.gettempdir()) / "gencp_work"
    say(f"default work_dir the dialog would use: {shared_work}")
    if shared_work.exists():
        shutil.rmtree(shared_work)
        say("  (cleared, so this probe starts from nothing)")

    def bounds_of(name):
        with rasterio.open(ROOT / f"tubitak/data/ankara/run/ref/{name}") as s:
            b = s.bounds
            return (b.left, b.bottom, b.right, b.top), s.crs.to_string()

    a_ext, crs = bounds_of("ank_0_30.tif")
    b_ext, _ = bounds_of("ank_0_41.tif")
    say(f"extent A (ank_0_30): {a_ext}")
    say(f"extent B (ank_0_41): {b_ext}")
    say(f"they are {'DIFFERENT' if a_ext != b_ext else 'THE SAME'} extents\n")

    outs = {}
    for tag, ext in (("A", a_ext), ("B", b_ext)):
        tif = OUT / f"run_{tag}.tif"
        # exactly what dialog._start() passes: no work_dir, so the fixed default is used
        pipeline.generate(ext, crs, str(MODEL), tif, pbf=str(PBF),
                          base_product="clcplus", overlap_m=0.0)
        with rasterio.open(tif) as s:
            outs[tag] = s.read()
        say(f"run {tag}: wrote {tif.name}, cache now holds "
            f"{sorted(p.name for p in (shared_work / 'render').glob('*.tif'))}")

    same = np.array_equal(outs["A"], outs["B"])
    say("")
    say(f"output A == output B ?  {same}")
    if same:
        say("  [FAIL] two different extents produced a byte-identical image.")
        say("  Run B silently reused run A's cached render. No error was raised, and the")
        say("  preview - which renders into a fresh temp dir every time - would have")
        say("  shown run B's CORRECT input while the file on disk is run A's.")
    else:
        d = np.abs(outs["A"].astype(float) - outs["B"].astype(float))
        say(f"  [PASS] outputs differ: mean |diff| {d.mean():.3f} DN, max {d.max():.0f} DN")
    say("")
    say(f"cache after both runs: {sorted(p.name for p in (shared_work / 'render').glob('*.tif'))}")
    n_cached = len(list((shared_work / "render").glob("*.tif")))
    say(f"  [{'PASS' if n_cached == 2 else 'FAIL'}] two distinct cache entries expected, got {n_cached}")
    say("")
    say("--- re-running extent A must HIT the cache (the cache still has to work) ---")
    import time
    t0 = time.time()
    pipeline.generate(a_ext, crs, str(MODEL), OUT / "run_A2.tif", pbf=str(PBF),
                      base_product="clcplus", overlap_m=0.0)
    t_hit = time.time() - t0
    with rasterio.open(OUT / "run_A2.tif") as s:
        a2 = s.read()
    n_after = len(list((shared_work / "render").glob("*.tif")))
    say(f"  re-run of A took {t_hit:.2f}s; cache entries still {n_after}")
    say(f"  [{'PASS' if n_after == 2 else 'FAIL'}] no new render was made for a repeat extent")
    say(f"  [{'PASS' if np.array_equal(a2, outs['A']) else 'FAIL'}] repeat of A reproduces A byte for byte")
    return 0 if (not same and n_cached == 2 and n_after == 2
                 and np.array_equal(a2, outs["A"])) else 1


if True:
    rc = 2
    try:
        rc = main()
    except Exception:
        import traceback
        say("PROBE CRASH:\n" + traceback.format_exc())
    _OUT.close()
    os._exit(rc)
