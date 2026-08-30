#!/usr/bin/env python
"""Gate S — the super-resolution grid contract.

Registered in `tubitak/sr/docs/gate-s-registration.md` BEFORE this ran and before any
super-resolved raster existed. Read that file for the conventions, the five assertions, the
predicted outcome of every case below, and the invariance list.

Gate S is NOT an analogue of Gate G. Gate G asserts a 0.05 px bound on the placement of
generated content, measured by FFT cross-correlation, and reports 0.000181 px. Gate S
asserts exact float equality on affine arithmetic. Different quantity, different method,
no inherited credibility. See registration §1.

Two modes:

    gate_s.py --source=A.tif --output=B.tif --scale=2     assert the contract on one pair
    gate_s.py --self-test                                  run the whole registered protocol

With no arguments it exits 2 and prints no verdict. That is deliberate: an audit of this
project's 23 verifiers found 18 exiting 0 on degenerate invocations, 17 of them by ignoring
the argument and re-running their real work. A verdict that does not depend on what you
asked for is not a verdict about what you asked for.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

HERE = Path(__file__).resolve()
SR = HERE.parents[1]                 # tubitak/sr
ROOT = HERE.parents[3]               # repository root
sys.path.insert(0, str(SR))
# The argument guard is Project 1's and is REUSED, not copied: one definition of "refuse
# what you do not understand" is better than two that can drift. This import makes
# tubitak/sr/tests/gate_s.py a reader of tubitak/tests/_guard.py — relevant to CLAUDE.md's
# deletion rule, which asks whether anything in the repository reads a file before it moves.
sys.path.insert(0, str(ROOT / "tubitak" / "tests"))
from _guard import strict_argv                                          # noqa: E402

strict_argv(known=("--source=", "--output=", "--scale=", "--self-test", "--keep"),
            positional=0,
            usage="gate_s.py --source=A.tif --output=B.tif --scale=2 | --self-test")

import numpy as np                                                      # noqa: E402
import rasterio                                                         # noqa: E402
from rasterio.transform import Affine                                   # noqa: E402

from sr_core import grid as sgrid                                       # noqa: E402
from sr_core.run import superresolve                                    # noqa: E402

#: A real scene from the WP0 inventory. 36SVJ is the cleanest of the five
#: (99.9 % of its 256 px chips are cloud-free) and its corner window carries data.
REAL_SCENE = ROOT / "tubitak/data/tiles36SVJ/TCI.tif"
OUT = ROOT / "tubitak/data/sr_gates/gate_s"
WINDOW = (4096, 4096, 512, 512)      # col0, row0, w, h — interior, away from granule edges


# --------------------------------------------------------------------------- assertions


def gate_s(src_path, out_path, scale, src_window=None, label=""):
    """Assert the five registered assertions. Returns (checks, n_failed).

    `checks` is a list of (name, ok, detail). Nothing is printed here; the caller decides.
    """
    checks = []

    def check(name, ok, detail):
        checks.append((name, bool(ok), detail))

    s = int(scale)
    with rasterio.open(str(src_path)) as src:
        if src_window is None:
            sT, W, H = src.transform, src.width, src.height
        else:
            from rasterio.windows import Window
            c0, r0, w, h = src_window
            sT, W, H = src.window_transform(Window(c0, r0, w, h)), w, h
        sK = src.crs
    with rasterio.open(str(out_path)) as dst:
        oT, oW, oH, oK = dst.transform, dst.width, dst.height, dst.crs

    # S1 -------------------------------------------------------------------------------
    check("S1  output CRS identical to source CRS",
          oK == sK, f"output {oK}  ==  source {sK}")

    # S2 -------------------------------------------------------------------------------
    exp_a, exp_e = sT.a / s, sT.e / s
    check(f"S2  output pixel size == source / {s} exactly, both axes",
          oT.a == exp_a and oT.e == exp_e,
          f"x = {oT.a!r} (expected {exp_a!r}), y = {-oT.e!r} (expected {-exp_e!r})  "
          f"[exact float equality; s is a power of two so the division is exact]")

    # S3 -------------------------------------------------------------------------------
    dc, df = oT.c - sT.c, oT.f - sT.f
    check("S3  output origin == source origin exactly",
          oT.c == sT.c and oT.f == sT.f,
          f"origin offset  x {dc!r}, y {df!r}  (sign convention: output minus source, "
          f"positive east / positive north)")

    # S4 -------------------------------------------------------------------------------
    check(f"S4  output size == {s} x source exactly",
          (oW, oH) == (s * W, s * H),
          f"got {oW} x {oH}, expected {s * W} x {s * H}  (source {W} x {H})")

    # S5 -------------------------------------------------------------------------------
    # Every corner, the first and last two indices on each axis, and a strided sample.
    def idx(n):
        v = {0, 1, max(0, n - 2), n - 1}
        v.update(range(0, n, max(1, n // 17)))
        return sorted(i for i in v if 0 <= i < n)

    rows, cols = idx(H), idx(W)
    worst_x = worst_y = 0.0
    worst_at = None
    n_cmp = 0
    for i in rows:
        for j in cols:
            px, py = sgrid.source_pixel_centre(sT, i, j)
            qx, qy = sgrid.output_block_centre(oT, i, j, s)
            n_cmp += 1
            ex, ey = qx - px, qy - py           # output minus source, as registered
            if abs(ex) > abs(worst_x):
                worst_x, worst_at = ex, (i, j)
            if abs(ey) > abs(worst_y):
                worst_y, worst_at = ey, (i, j)
    # A sample of size zero is a failure, not a pass (registration §3).
    check("S5  source pixel centre == centre of its s x s output block, exactly",
          n_cmp > 0 and worst_x == 0.0 and worst_y == 0.0,
          f"{n_cmp} pixel centres compared; worst offset dx {worst_x!r}, dy {worst_y!r} "
          f"at (row, col) = {worst_at}  [output minus source, +E/+N]")

    return checks, sum(1 for _, ok, _ in checks if not ok)


def report(title, checks, n_failed, indent="  "):
    print(f"{indent}{title}")
    for name, ok, detail in checks:
        print(f"{indent}  [{'PASS' if ok else 'FAIL'}] {name}")
        print(f"{indent}         {detail}")
    print(f"{indent}  -> {len(checks) - n_failed}/{len(checks)} assertions passed")
    return n_failed


# ------------------------------------------------------------------- fixture construction


def _rewrite(src_tif, dst_tif, transform=None, crs=None):
    """Copy a raster's pixels under a deliberately altered georeference."""
    with rasterio.open(str(src_tif)) as s:
        prof, arr = s.profile.copy(), s.read()
    if transform is not None:
        prof["transform"] = transform
    if crs is not None:
        prof["crs"] = crs
    with rasterio.open(str(dst_tif), "w", **prof) as d:
        d.write(arr)
    return dst_tif


def _synthetic(path, w, h, px=10.0, origin=(400000.0, 4400000.0), crs="EPSG:32636"):
    prof = dict(driver="GTiff", width=w, height=h, count=3, dtype="uint8", crs=crs,
                transform=Affine(px, 0, origin[0], 0, -px, origin[1]), nodata=0)
    rng = np.random.default_rng(20260830)        # seed recorded: standing practice 9
    with rasterio.open(str(path), "w", **prof) as d:
        d.write(rng.integers(1, 255, (3, h, w), dtype=np.uint8))
    return path


def _subproc(args):
    """Run this gate as a child process. Returns (returncode, stdout+stderr)."""
    p = subprocess.run([sys.executable, str(HERE)] + args,
                       capture_output=True, text=True)
    return p.returncode, (p.stdout + p.stderr)


# ------------------------------------------------------------------------- the protocol


def self_test(keep=False):
    OUT.mkdir(parents=True, exist_ok=True)
    verdicts = []            # (case, expectation_met, one-line detail)
    print("=" * 78)
    print("Gate S — self-test against the cases registered in")
    print("         tubitak/sr/docs/gate-s-registration.md §4")
    print("=" * 78)
    print(f"  seed (synthetic fixtures) : 20260830")
    print(f"  numpy {np.__version__} · rasterio {rasterio.__version__} · "
          f"GDAL {rasterio.__gdal_version__}")
    import PIL
    print(f"  pillow {PIL.__version__}  (does the resampling)")
    print()

    if not REAL_SCENE.is_file():
        print(f"  ABORT: real scene not found: {REAL_SCENE}")
        return 1

    # --- KT1: the real bicubic output ------------------------------------------------
    kt1 = OUT / "kt1_real_bicubic_x2.tif"
    rec = superresolve(REAL_SCENE, kt1, scale=2, window=WINDOW, progress=None)
    print(f"KT1  real bicubic output — predicted PASS on all five")
    print(f"     source {REAL_SCENE.name} window {WINDOW} -> {rec['output_shape']}")
    c, f = gate_s(REAL_SCENE, kt1, 2, src_window=WINDOW)
    report("", c, f, indent="     ")
    verdicts.append(("KT1 real bicubic output", f == 0, f"{f} failed (predicted 0)"))
    print()

    # --- KF1: half an output pixel of offset -----------------------------------------
    with rasterio.open(str(kt1)) as d:
        oT = d.transform
    half = Affine(oT.a, 0, oT.c + oT.a / 2.0, 0, oT.e, oT.f + oT.e / 2.0)
    kf1 = _rewrite(kt1, OUT / "kf1_half_pixel_offset.tif", transform=half)
    print("KF1  transform offset by half an OUTPUT pixel — predicted FAIL on S3 and S5")
    c, f = gate_s(REAL_SCENE, kf1, 2, src_window=WINDOW)
    report("", c, f, indent="     ")
    failed = {n.split()[0] for n, ok, _ in c if not ok}
    verdicts.append(("KF1 half-pixel offset", f > 0, f"failed {sorted(failed)}"))
    print()

    # --- KF2: pixel size wrong by a relative 1e-9 ------------------------------------
    eps = Affine(oT.a * (1 + 1e-9), 0, oT.c, 0, oT.e * (1 + 1e-9), oT.f)
    kf2 = _rewrite(kt1, OUT / "kf2_pixel_size_1e-9.tif", transform=eps)
    print("KF2  pixel size = source/s * (1 + 1e-9) — predicted FAIL on S2 (and S5)")
    c, f = gate_s(REAL_SCENE, kf2, 2, src_window=WINDOW)
    report("", c, f, indent="     ")
    failed = {n.split()[0] for n, ok, _ in c if not ok}
    verdicts.append(("KF2 pixel size off by 1e-9 relative", f > 0, f"failed {sorted(failed)}"))
    print()

    # --- KF3: wrong scale -------------------------------------------------------------
    kf3 = OUT / "kf3_wrong_scale.tif"
    superresolve(REAL_SCENE, kf3, scale=1, window=WINDOW, progress=None)
    print("KF3  output built at scale 1, asserted at scale 2 — predicted FAIL on S2 and S4")
    c, f = gate_s(REAL_SCENE, kf3, 2, src_window=WINDOW)
    report("", c, f, indent="     ")
    failed = {n.split()[0] for n, ok, _ in c if not ok}
    verdicts.append(("KF3 wrong scale", f > 0, f"failed {sorted(failed)}"))
    print()

    # --- KF4: wrong CRS ---------------------------------------------------------------
    kf4 = _rewrite(kt1, OUT / "kf4_wrong_crs.tif", crs=rasterio.crs.CRS.from_epsg(4326))
    print("KF4  same pixels tagged EPSG:4326 — predicted FAIL on S1")
    c, f = gate_s(REAL_SCENE, kf4, 2, src_window=WINDOW)
    report("", c, f, indent="     ")
    failed = {n.split()[0] for n, ok, _ in c if not ok}
    verdicts.append(("KF4 wrong CRS", f > 0, f"failed {sorted(failed)}"))
    print()

    # --- DG1 / DG5: argv discipline, as real child processes --------------------------
    print("DG1  no arguments — predicted exit 2, no verdict")
    rc, out = _subproc([])
    emitted = "GATE S" in out.upper()
    print(f"     exit {rc}; printed a verdict: {emitted}")
    print(f"     {out.strip().splitlines()[0] if out.strip() else '(no output)'}")
    verdicts.append(("DG1 no arguments", rc == 2 and not emitted, f"exit {rc}"))
    print()

    print("DG5  unrecognised argument --scalee=2 — predicted exit 2, no verdict")
    rc, out = _subproc(["--source=x", "--output=y", "--scalee=2"])
    emitted = "GATE S" in out.upper()
    print(f"     exit {rc}; printed a verdict: {emitted}")
    verdicts.append(("DG5 unrecognised argument", rc == 2 and not emitted, f"exit {rc}"))
    print()

    # --- DG2: missing file ------------------------------------------------------------
    print("DG2  missing file — predicted error, no verdict")
    rc, out = _subproc([f"--source={OUT / 'does_not_exist.tif'}",
                        f"--output={kt1}", "--scale=2"])
    emitted = "GATE S:" in out.upper()
    print(f"     exit {rc}; printed a verdict: {emitted}")
    verdicts.append(("DG2 missing file", rc != 0 and not emitted, f"exit {rc}"))
    print()

    # --- DG3: empty and truncated rasters ---------------------------------------------
    empty = OUT / "dg3_empty.tif"
    empty.write_bytes(b"")
    print("DG3a empty (0-byte) raster — predicted error, no verdict")
    rc, out = _subproc([f"--source={empty}", f"--output={kt1}", "--scale=2"])
    emitted = "GATE S:" in out.upper()
    print(f"     exit {rc}; printed a verdict: {emitted}")
    verdicts.append(("DG3a empty raster", rc != 0 and not emitted, f"exit {rc}"))

    trunc = OUT / "dg3_truncated.tif"
    trunc.write_bytes(kt1.read_bytes()[:4096])
    print("DG3b truncated raster (first 4096 bytes) — predicted error, no verdict")
    rc, out = _subproc([f"--source={REAL_SCENE}", f"--output={trunc}", "--scale=2"])
    emitted = "GATE S:" in out.upper()
    print(f"     exit {rc}; printed a verdict: {emitted}")
    verdicts.append(("DG3b truncated raster", rc != 0 and not emitted, f"exit {rc}"))
    print()

    # --- DG4: 1x1 source, a legitimate degenerate input -------------------------------
    print("DG4  single-pixel (1x1) source — predicted PASS; a crash here is a gate defect")
    one = _synthetic(OUT / "dg4_single_pixel_src.tif", 1, 1)
    one_out = OUT / "dg4_single_pixel_x2.tif"
    try:
        superresolve(one, one_out, scale=2, progress=None)
        c, f = gate_s(one, one_out, 2)
        report("", c, f, indent="     ")
        verdicts.append(("DG4 single-pixel raster", f == 0, f"{f} failed (predicted 0)"))
    except Exception as e:                                    # noqa: BLE001
        print(f"     RAISED {type(e).__name__}: {e}")
        verdicts.append(("DG4 single-pixel raster", False, f"raised {type(e).__name__}"))
    print()

    # --- verdict ----------------------------------------------------------------------
    print("=" * 78)
    print("Did each case behave as REGISTERED?")
    for name, ok, detail in verdicts:
        print(f"  [{'as registered' if ok else 'NOT AS REGISTERED'}]  {name:38s} {detail}")
    bad = [n for n, ok, _ in verdicts if not ok]
    print()
    if bad:
        print(f"GATE S IS NOT TRUSTWORTHY: {len(bad)} case(s) did not behave as "
              f"registered: {', '.join(bad)}")
    else:
        print("GATE S CAN FAIL, AND FAILS ONLY WHERE IT SHOULD: "
              f"{len(verdicts)}/{len(verdicts)} cases behaved as registered.")
    print("=" * 78)

    (OUT / "gate_s_selftest.json").write_text(json.dumps(
        [dict(case=n, as_registered=ok, detail=d) for n, ok, d in verdicts], indent=2))

    if not keep:
        for p in (empty, trunc):
            try:
                p.unlink()
            except FileNotFoundError:
                pass
    return 1 if bad else 0


def main():
    args = sys.argv[1:]
    if "--self-test" in args:
        return self_test(keep="--keep" in args)

    src = out = None
    scale = 2
    for a in args:
        if a.startswith("--source="):
            src = a.split("=", 1)[1]
        elif a.startswith("--output="):
            out = a.split("=", 1)[1]
        elif a.startswith("--scale="):
            scale = int(a.split("=", 1)[1])
    if not src or not out:
        sys.stderr.write(
            "gate_s.py: nothing to check.\n"
            "  This verifier refuses to run without being told what to check, rather\n"
            "  than running a default and printing a verdict for it.\n"
            "  Usage: gate_s.py --source=A.tif --output=B.tif --scale=2\n"
            "     or: gate_s.py --self-test\n")
        return 2
    for p, what in ((src, "source"), (out, "output")):
        if not Path(p).is_file():
            sys.stderr.write(f"gate_s.py: {what} not found: {p}\n")
            return 2
        if Path(p).stat().st_size == 0:
            sys.stderr.write(f"gate_s.py: {what} is a 0-byte file: {p}\n")
            return 2
    try:
        checks, failed = gate_s(src, out, scale)
    except Exception as e:                                       # noqa: BLE001
        sys.stderr.write(f"gate_s.py: could not evaluate the contract: "
                         f"{type(e).__name__}: {e}\n")
        return 2
    print(f"Gate S — grid contract   source {Path(src).name} -> output {Path(out).name} "
          f"at scale {scale}")
    report("", checks, failed, indent="  ")
    print(f"GATE S: {'PASS' if not failed else 'FAIL'} "
          f"({len(checks) - failed}/{len(checks)} assertions)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
