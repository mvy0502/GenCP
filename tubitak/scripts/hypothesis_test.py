#!/usr/bin/env python
"""Decide how the 257x257 OSM input becomes the network's 256x256 input.

Reconstructs each candidate transform from the source raster and compares it to
``_real.png`` — the network's own recorded input — pixel by pixel. The winner is
whichever reconstruction reproduces ``_real.png`` exactly (up to the float->uint8
round trip in ``util.tensor2im``, which is +/-1 DN).

Candidates
----------
H1   resize 257->256                        the pipeline path (preprocess=resize_and_crop
                                            with load_size == crop_size == 256)
H2   resize to load_size, then centre-crop   identical to H1 whenever
                                            load_size == crop_size; kept explicit so the
                                            degeneracy is visible rather than assumed
H2'  counterfactual with load_size=286      what pix2pix's *default* load_size would do;
                                            shown to quantify how much worse that case is
H3   four corner crops of 256x256           no rescaling at all

Losing scores are printed alongside the winner on purpose: a hypothesis test that
only reports its winner cannot be audited.

Usage
-----
    python tubitak/scripts/hypothesis_test.py                 # 8 demo tiles
    python tubitak/scripts/hypothesis_test.py --tiles 20
    python tubitak/scripts/hypothesis_test.py --input-dir DIR --png-dir DIR
"""
from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
HR = REPO_ROOT / "GenCP_HR_demo"
DEF_INPUT = HR / "data" / "dataset" / "test"
DEF_PNG = HR / "data" / "fake_images" / "genCP_HR_RGB_model" / "test_latest" / "images"
DEF_DB = HR / "data" / "GenCP_DB"


def read_png(path):
    import rasterio
    from rasterio.errors import NotGeoreferencedWarning
    warnings.filterwarnings("ignore", category=NotGeoreferencedWarning)
    with rasterio.open(path) as s:
        return np.transpose(s.read(), (1, 2, 0)).astype(np.int16)


def stats(a, b):
    a = np.asarray(a, np.int16); b = np.asarray(b, np.int16)
    if a.shape != b.shape:
        return None, np.nan, np.nan, np.nan
    d = np.abs(a - b)
    corr = float(np.corrcoef(a.ravel().astype(float), b.ravel().astype(float))[0, 1])
    return bool((d == 0).all()), float(d.mean()), int(d.max()), corr


def candidates(pil_img, load_size=256, crop_size=256, alt_load=286):
    """Build every candidate reconstruction from the source PIL image."""
    from torchvision import transforms
    BICUBIC = transforms.InterpolationMode.BICUBIC
    resize = transforms.Resize([load_size, load_size], BICUBIC)
    A = np.array(pil_img)
    out = {
        f"H1  resize {A.shape[0]}->{crop_size} (pipeline)": np.array(resize(pil_img)),
        f"H2  resize(load={load_size})+crop{crop_size}":
            np.array(transforms.CenterCrop(crop_size)(resize(pil_img))),
        f"H2' counterfactual load={alt_load}":
            np.array(transforms.CenterCrop(crop_size)(
                transforms.Resize([alt_load, alt_load], BICUBIC)(pil_img))),
    }
    if A.shape[0] > crop_size:
        o = A.shape[0] - crop_size
        out[f"H3  crop TL [0:{crop_size},0:{crop_size}]"] = A[:crop_size, :crop_size]
        out[f"H3  crop TR [0:{crop_size},{o}:]"] = A[:crop_size, o:]
        out[f"H3  crop BL [{o}:,0:{crop_size}]"] = A[o:, :crop_size]
        out[f"H3  crop BR [{o}:,{o}:]"] = A[o:, o:]
    return out


def main() -> int:
    from PIL import Image

    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--tiles", type=int, default=8, help="how many tiles to test")
    p.add_argument("--input-dir", default=str(DEF_INPUT), help="source OSM rasters")
    p.add_argument("--png-dir", default=str(DEF_PNG), help="directory holding _real.png")
    p.add_argument("--list-from", default=str(DEF_DB), help="directory whose stems select the tiles")
    p.add_argument("--load-size", type=int, default=256)
    p.add_argument("--crop-size", type=int, default=256)
    p.add_argument("--per-tile", action="store_true", help="print every tile, not just the mean")
    a = p.parse_args()

    in_dir, png_dir = Path(a.input_dir), Path(a.png_dir)
    stems = sorted(q.stem for q in Path(a.list_from).glob("*.tif"))[:a.tiles]
    if not stems:
        sys.exit(f"no tiles found via {a.list_from}")

    agg: dict[str, list] = {}
    if a.per_tile:
        print(f"{'tile':<16}{'hypothesis':<36}{'exact':<8}{'MAD':>9}{'maxdiff':>9}{'corr':>10}")
        print("-" * 88)

    for stem in stems:
        src = in_dir / f"{stem}.tif"
        real_p = png_dir / f"{stem}_real.png"
        if not (src.exists() and real_p.exists()):
            print(f"  skip {stem}: missing source or _real.png")
            continue
        img = Image.open(src).convert("RGB")
        R = read_png(real_p)
        for k, v in candidates(img, a.load_size, a.crop_size).items():
            e, m, mx, c = stats(v, R)
            agg.setdefault(k, []).append((m, mx, c))
            if a.per_tile:
                print(f"{stem:<16}{k:<36}{str(e):<8}{m:>9.4f}{mx:>9}{c:>10.6f}")
        if a.per_tile:
            print()

    print("=" * 88)
    print(f"MEAN over {len(stems)} tiles")
    print(f"{'hypothesis':<40}{'MAD':>12}{'max diff':>12}{'corr':>12}")
    print("-" * 88)
    ranked = sorted(agg.items(), key=lambda kv: np.mean([x[0] for x in kv[1]]))
    for k, v in ranked:
        print(f"{k:<40}{np.mean([x[0] for x in v]):>12.4f}"
              f"{max(x[1] for x in v):>12}{np.mean([x[2] for x in v]):>12.6f}")
    print("-" * 88)

    win, wv = ranked[0]
    runner, rv = ranked[1]
    wm, rm = np.mean([x[0] for x in wv]), np.mean([x[0] for x in rv])
    print(f"\nWINNER: {win.strip()}")
    print(f"  mean MAD {wm:.4f} DN, max deviation {max(x[1] for x in wv)} DN")
    if max(x[1] for x in wv) <= 1:
        print("  residual is <=1 DN everywhere = the float->uint8 round trip, not geometry.")
    if np.isclose(rm, wm, rtol=1e-9, atol=1e-12):
        print(f"  NOTE: {runner.strip()} scores identically - the two are degenerate")
        print(f"        under these options (load_size == crop_size makes the crop a no-op).")
        distinct = [(k, np.mean([x[0] for x in v])) for k, v in ranked
                    if not np.isclose(np.mean([x[0] for x in v]), wm, rtol=1e-9, atol=1e-12)]
        if distinct:
            k, m = distinct[0]
            print(f"  next genuinely different hypothesis ({k.strip()}) is {m / wm:.1f}x worse in MAD.")
    elif rm > 0 and wm > 0:
        print(f"  next best ({runner.strip()}) is {rm / wm:.1f}x worse in MAD.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
