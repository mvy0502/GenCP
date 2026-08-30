#!/usr/bin/env python3
"""D23 — join B08 to the EXISTING chips. `build_corpus.py` is not re-run.

Re-screening over four bands would change the accepted chip set, invalidating the v2
manifest, `config.DEDUP_ORDER_COUNTS`, and the `== 47` anchor in `leakage.py` that is the
only independent arm of the leakage gate. So the chips, the split, the dedup and the buffer
are carried over untouched and only the band dimension grows, 3 -> 4.

Written to a NEW directory. The WP3B corpus is never overwritten, so a WP3B number can still
be reproduced after this.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

SR = Path(__file__).resolve().parents[1]
if str(SR) not in sys.path:
    sys.path.insert(0, str(SR))

from sr_data import params as P                                         # noqa: E402
from sr_train import config as C, data as D                             # noqa: E402

SPLITS = ("train", "val", "test", "heldout")


def grid_of(path):
    import rasterio
    with rasterio.open(path) as d:
        return dict(crs=str(d.crs), transform=tuple(round(v, 10) for v in d.transform[:6]),
                    w=d.width, h=d.height, dtype=d.dtypes[0])


def assert_b08_grid(root, verbose=True):
    """X1. B08 on the same grid as B02, per granule, TRANSFORM included.

    All five granules share EPSG:32636 and 10980 x 10980, so only the transform separates
    them: a check comparing CRS and shape alone passes every wrong pairing (WP2A open item 4).
    """
    ok = True
    for g, m in P.GRANULES.items():
        ref = grid_of(root / P.DATA_SUBDIR / m["dirname"] / "B02.tif")
        b8 = grid_of(root / "s2_b08" / f"B08_{g}.tif")
        same = ref == b8
        ok &= same
        if verbose:
            print(f"    {g}: {'IDENTICAL' if same else 'MISMATCH'}  "
                  f"{b8['w']}x{b8['h']} {b8['dtype']} {b8['crs']}")
        if not same:
            raise SystemExit(f"join_b08: {g} B08 grid differs from B02: "
                             f"{ {k: (ref[k], b8[k]) for k in ref if ref[k] != b8[k]} }")
    return ok


def known_false_grid(root):
    """The same check shown REJECTING B08 of one granule against another's B02."""
    pairs = [("36TVK", "36SVJ"), ("36SWJ", "36SXJ"), ("36TUK", "36TVK")]
    fired = 0
    for a, b in pairs:
        ra = grid_of(root / "s2_b08" / f"B08_{a}.tif")
        rb = grid_of(root / P.DATA_SUBDIR / P.GRANULES[b]["dirname"] / "B02.tif")
        diff = [k for k in ra if ra[k] != rb[k]]
        fired += bool(diff)
        print(f"    B08 {a} vs B02 {b}: {'MISMATCH' if diff else '*** BLIND ***'} {diff}")
    if fired != len(pairs):
        raise SystemExit("join_b08: the grid check cannot fail; its verdict is not trusted")
    return fired


def main():
    ap = argparse.ArgumentParser(prog="join_b08.py")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    if C.VARIANT != "x4":
        raise SystemExit("join_b08: run with GENCP_SR_VARIANT=x4")
    import rasterio

    root = C.data_root()
    src_corpus = root / P.CORPUS_SUBDIR
    out = Path(a.out or (root / C.CORPUS_SUBDIR))
    out.mkdir(parents=True, exist_ok=True)

    print("X1 known-true: B08 on the same grid as B02, per granule")
    assert_b08_grid(root)
    print("X1 known-false: B08 against ANOTHER granule's B02")
    known_false_grid(root)

    print("\nX2: the split carries over UNCHANGED - hashes of what WP3B used")
    for f in ("manifest_v2.csv", "split_v2.json", "leakage.json"):
        p = root / C.SPLIT_SUBDIR / f
        print(f"    {f:18s} sha256 {hashlib.sha256(p.read_bytes()).hexdigest()[:32]}")
    for s in SPLITS:
        p = src_corpus / f"chips_{s}.npy"
        print(f"    chips_{s+'.npy':16s} {p.stat().st_size:>13,} B")

    b8 = {g: rasterio.open(root / "s2_b08" / f"B08_{g}.tif") for g in P.GRANULES}
    recs_all = D.read_manifest_v2()
    counts, t0 = {}, time.perf_counter()
    print("\njoining B08 as plane 4")
    for split in SPLITS:
        recs = [r for r in recs_all if r["split"] == split]
        recs.sort(key=lambda r: int(r["index_in_split_v2"]))
        old = np.load(src_corpus / f"chips_{split}.npy", mmap_mode="r")
        n = len(recs)
        arr = np.empty((n, C.N_BANDS, C.CHIP_PX, C.CHIP_PX), np.uint16)
        cache = {}
        for k, r in enumerate(recs):
            s1 = r["split_v1"]
            if s1 not in cache:
                cache[s1] = np.load(src_corpus / f"chips_{s1}.npy", mmap_mode="r")
            arr[k, :3] = cache[s1][int(r["index_in_split"])]
            row, col = int(r["chip_row"]), int(r["chip_col"])
            win = rasterio.windows.Window(col * C.CHIP_PX, row * C.CHIP_PX,
                                          C.CHIP_PX, C.CHIP_PX)
            arr[k, 3] = b8[r["granule"]].read(1, window=win)
        np.save(out / f"chips_{split}.npy", arr)
        counts[split] = n
        print(f"    {split:8s} {n:5d} chips -> {(out / f'chips_{split}.npy').stat().st_size:>13,} B")
        del arr
    for d in b8.values():
        d.close()

    total = sum((out / f"chips_{s}.npy").stat().st_size for s in SPLITS)
    rec = dict(work_package="P2-WP7", variant=C.VARIANT, scale=C.SCALE,
               bands=list(C.BANDS), band_order=",".join(C.BANDS),
               n_bands=C.N_BANDS, chip_px=C.CHIP_PX, input_px=C.INPUT_PX,
               norm_divisor_dn=C.NORM_DIVISOR_DN, psnr_data_range=C.PSNR_DATA_RANGE,
               mtf_at_nyquist=C.MTF_AT_NYQUIST,
               sigma_source_px=P.sigma_for_mtf(C.MTF_AT_NYQUIST, C.SCALE),
               source_corpus=str(src_corpus), split_dir=str(root / C.SPLIT_SUBDIR),
               counts=counts, total_bytes=total,
               split_carried_over_unchanged=True,
               wall_clock_s=time.perf_counter() - t0)
    (out / "corpus_x4.json").write_text(json.dumps(rec, indent=2))
    print(f"\n  total {total:,} B = {total/1e9:.3f} GB in {time.perf_counter()-t0:.1f} s")
    print(f"  sigma at s={C.SCALE}: {rec['sigma_source_px']:.8f} source px "
          f"= {rec['sigma_source_px']*P.GSD_M:.4f} m")
    print(f"  wrote {out/'corpus_x4.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
