#!/usr/bin/env python
"""Does tiled + feather-blended upsampling equal a single whole-window upsample?

**This is NOT part of Gate S**, deliberately. Gate S asserts georeferencing arithmetic; this
asserts pixel values. Keeping them apart means a seam defect can never be reported as a
georeferencing defect, or the reverse — the same separation Gate G maintains between its
part A (grid) and part B (content).

The claim under test: at the DEFAULT overlap the tiled result is identical to a single-shot
upsample of the same window.

It is worth recording what this check has already overturned. The original claim written
here was that an overlap of 4 px suffices, because the cubic-convolution kernel reaches only
2 source pixels each side. The measurement says otherwise — 4 px leaves a 1 DN residue and
2 px leaves 6 DN — because the feather ramp spans the whole overlap, so at a small overlap
the very pixels whose neighbourhood was truncated at the tile edge still carry appreciable
weight. The sweep below is therefore kept in the output rather than reduced to a single
pass/fail, so the threshold is visible instead of asserted.

Born with its failing case, per standing practice 11: the same comparison is run at
overlap 0, where tiles cannot see past their own edges and seams MUST appear. If the
overlap-0 case also reports zero difference, this check is measuring nothing and says so.
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

HERE = Path(__file__).resolve()
SR = HERE.parents[1]
ROOT = HERE.parents[3]
sys.path.insert(0, str(SR))
sys.path.insert(0, str(ROOT / "tubitak" / "tests"))
from _guard import strict_argv                                          # noqa: E402

strict_argv(known=("--scene=", "--window=", "--scale=", "--keep"), positional=0,
            usage="tiling_equivalence.py [--scene=X.tif] [--window=c0,r0,w,h] [--scale=2]")

import numpy as np                                                      # noqa: E402
import rasterio                                                         # noqa: E402

from sr_core.run import superresolve                                    # noqa: E402

SCENE = ROOT / "tubitak/data/tiles36SVJ/TCI.tif"
OUT = ROOT / "tubitak/data/sr_gates/tiling"
WINDOW = (4096, 4096, 512, 512)
SCALE = 2


def _read(p):
    with rasterio.open(str(p)) as s:
        return s.read()


def run(scene, window, scale):
    OUT.mkdir(parents=True, exist_ok=True)
    w, h = window[2], window[3]

    # Reference: ONE tile covering the whole window, so no blending happens at all.
    ref = OUT / "single_shot.tif"
    superresolve(scene, ref, scale=scale, window=window,
                 tile_px=max(w, h), overlap_px=0, progress=None)
    a_ref = _read(ref).astype(np.int32)

    rows = []
    for tile_px, ov in ((256, 32), (256, 8), (256, 4), (256, 2), (256, 0), (128, 32)):
        p = OUT / f"tiled_{tile_px}_{ov}.tif"
        rec = superresolve(scene, p, scale=scale, window=window,
                           tile_px=tile_px, overlap_px=ov, progress=None)
        a = _read(p).astype(np.int32)
        d = np.abs(a - a_ref)
        rows.append((tile_px, ov, rec["n_tiles"], int(d.max()), float(d.mean()),
                     int(np.count_nonzero(d))))

    print("=" * 78)
    print("Tiled + feathered  vs  single whole-window upsample   (NOT part of Gate S)")
    print("=" * 78)
    print(f"  scene  : {Path(scene).name}  window {window}  scale x{scale}")
    print(f"  ref    : one {max(w, h)} px tile, overlap 0 -> no blending occurs")
    print(f"  units  : DN, uint8 imagery; {a_ref.size:,} output values compared\n")
    print(f"  {'tile':>5s} {'overlap':>8s} {'tiles':>6s} {'max|d|':>7s} "
          f"{'mean|d|':>9s} {'n differing':>12s}")
    for t, ov, n, mx, mn, nz in rows:
        print(f"  {t:5d} {ov:8d} {n:6d} {mx:7d} {mn:9.5f} {nz:12,d}")

    by_ov = {ov: mx for (t, ov, _n, mx, _mn, _nz) in rows if t == 256}
    ok_default = by_ov.get(32, None) == 0
    can_fail = by_ov.get(0, 0) > 0
    print()
    print(f"  default overlap 32 px identical to single-shot : "
          f"{'YES' if ok_default else 'NO (max |d| = %s DN)' % by_ov.get(32)}")
    print(f"  KNOWN-FALSE control, overlap 0 px shows seams   : "
          f"{'YES, max |d| = %d DN' % by_ov.get(0, 0) if can_fail else 'NO — THIS CHECK IS MEASURING NOTHING'}")
    print("=" * 78)
    if not can_fail:
        print("VERDICT: the check could not fail on its own known-false case. Do not "
              "trust its positive result.")
        return 1
    print(f"VERDICT: {'tiling is value-transparent at the default overlap' if ok_default else 'TILING CHANGES VALUES AT THE DEFAULT OVERLAP'}")
    return 0 if ok_default else 1


def main():
    scene, window, scale = SCENE, WINDOW, SCALE
    for a in sys.argv[1:]:
        if a.startswith("--scene="):
            scene = Path(a.split("=", 1)[1])
        elif a.startswith("--window="):
            window = tuple(int(v) for v in a.split("=", 1)[1].split(","))
        elif a.startswith("--scale="):
            scale = int(a.split("=", 1)[1])
    if not Path(scene).is_file():
        sys.stderr.write(f"tiling_equivalence.py: scene not found: {scene}\n")
        return 2
    if len(window) != 4:
        sys.stderr.write("tiling_equivalence.py: --window needs c0,r0,w,h\n")
        return 2
    return run(scene, window, scale)


if __name__ == "__main__":
    sys.exit(main())
