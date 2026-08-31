#!/usr/bin/env python
"""Cut the WP3A Wald corpus. Targets only; the degradation happens at load time (D10).

    python -m sr_data.build_corpus [--out=DIR] [--dry-run]

Writes, under `tubitak/data/sr_wald_corpus/`:
    chips_<split>.npy   uint16 (N, 3, 256, 256), B02/B03/B04
    manifest.csv        one row per accepted chip, with its geometry and split
    corpus.json         the parameters this run used, read back by the checks

`--dry-run` does the whole screen and the split arithmetic and reports the counts and the
projected size WITHOUT writing any array, so the 5 GB question can be answered before 2.6 GB
is committed to disk.
"""
from __future__ import annotations

import csv
import json
import sys
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

HERE = Path(__file__).resolve()
SR = HERE.parents[1]
ROOT = HERE.parents[3]
if __package__ in (None, ""):
    sys.path.insert(0, str(SR))
sys.path.insert(0, str(ROOT / "tubitak" / "tests"))
from _guard import strict_argv                                          # noqa: E402

strict_argv(known=("--out=", "--dry-run", "--source="), positional=0,
            usage="build_corpus.py [--out=DIR] [--dry-run] [--source=tci]")

import numpy as np                                                      # noqa: E402
import rasterio                                                         # noqa: E402
from rasterio.windows import Window                                     # noqa: E402

from sr_data import params as P                                         # noqa: E402
from sr_data.clear import clear_mask_20m, expand_to_10m, require_nested  # noqa: E402
from sr_data import splits as S                                         # noqa: E402

DATA = ROOT / "tubitak" / "data" / P.DATA_SUBDIR
OUT_DEFAULT = ROOT / "tubitak" / "data" / P.CORPUS_SUBDIR


#: WP12 D32: the TCI source. Everything about the cut is unchanged - same chip grid, same
#: SCL, same clear classes, same nodata rejection - and ONLY where the pixels come from
#: differs: one three-band uint8 raster per granule instead of three single-band uint16 ones.
#: The SCL used is the reflectance directory's, which is byte-identical to the tiles
#: directory's (verified by sha256), so screening cannot differ between the two corpora.
SOURCE = "reflectance"


def _open_bands(tile, meta):
    """Return (dict-or-list of readers, profile, close_fn) for the configured source."""
    if SOURCE == "tci":
        f = ROOT / "tubitak" / "data" / f"tiles{tile}" / "TCI.tif"
        if not f.is_file():
            raise SystemExit(f"build_corpus: no TCI for {tile} at {f}")
        src = rasterio.open(f)
        if src.count != len(P.BANDS):
            raise SystemExit(f"{f}: {src.count} bands, expected {len(P.BANDS)}")
        return src, src.profile, src.close
    srcs = {b: rasterio.open(ROOT / "tubitak" / "data" / P.DATA_SUBDIR /
                             meta["dirname"] / f"{b}.tif") for b in P.BANDS}
    prof0 = srcs[P.BANDS[0]].profile
    for b in P.BANDS[1:]:
        pb = srcs[b].profile
        if (pb["transform"], pb["width"], pb["height"], pb["crs"]) != \
                (prof0["transform"], prof0["width"], prof0["height"], prof0["crs"]):
            raise ValueError(f"{tile}/{b} grid differs from {P.BANDS[0]}")
    return srcs, prof0, lambda: [s.close() for s in srcs.values()]


def _read_chip(srcs, win):
    if SOURCE == "tci":
        return srcs.read(window=win)
    return np.stack([srcs[b].read(1, window=win) for b in P.BANDS])


#: WP13 D35: how "nodata" is recognised, and it is NOT the same test in both products.
#:
#: For uint16 reflectance, 0 is a rare sentinel and ANY band at 0 marks a nodata pixel. That
#: is WP3A's rule and it is correct there; it is left exactly as it was, so WP3A, WP3B and
#: WP7 remain reproducible.
#:
#: For 8-bit TCI it is wrong, and WP12 measured the cost: 902 rejected chips on 36SXJ alone
#: and a held-out granule of 740 instead of 1332. Quantisation to 8 bits puts genuinely dark
#: LAND - deep shadow, water - at 0 in one band while the others carry signal, so the rule
#: rejected dark terrain rather than nodata. Nodata in this product is written as all three
#: bands zero together. That is the test used here.
#:
#: The sixth instance of the shape WP7 catalogued: code written for one parameter, met by
#: another.
def _is_nodata(arr):
    """Per-pixel nodata mask for the configured source. `arr` is (bands, H, W)."""
    if SOURCE == "tci":
        return (arr == P.REJECT_CHIPS_CONTAINING_DN).all(axis=0)
    return (arr == P.REJECT_CHIPS_CONTAINING_DN).any(axis=0)


def screen_granule(tile, meta):
    """Return (accepted records, rejection counts) for one granule.

    A chip is accepted iff every SCL pixel over its footprint is clear AND no band pixel
    equals the nodata sentinel.
    """
    d = DATA / meta["dirname"]
    with rasterio.open(d / "SCL.tif") as s:
        scl_prof, scl = s.profile, s.read(1)
    srcs, prof0, _close = _open_bands(tile, meta)
    try:
        require_nested(prof0, scl_prof, who=f"{tile}")
        W, H, T, crs = prof0["width"], prof0["height"], prof0["transform"], prof0["crs"]
        nrow, ncol = H // P.CHIP_STRIDE_PX, W // P.CHIP_STRIDE_PX
        clear10 = expand_to_10m(clear_mask_20m(scl))

        recs = []
        rej = dict(not_all_clear=0, has_nodata_dn=0, accepted=0, total=0)
        n = P.CHIP_PX
        for cr in range(nrow):
            r0 = cr * P.CHIP_STRIDE_PX
            for cc in range(ncol):
                c0 = cc * P.CHIP_STRIDE_PX
                rej["total"] += 1
                sub = clear10[r0:r0 + n, c0:c0 + n]
                frac = float(sub.mean())
                if frac < P.MIN_CLEAR_FRACTION:
                    rej["not_all_clear"] += 1
                    continue
                win = Window(c0, r0, n, n)
                arr = _read_chip(srcs, win)
                if _is_nodata(arr).any():
                    rej["has_nodata_dn"] += 1
                    continue
                rej["accepted"] += 1
                wt = rasterio.windows.transform(win, T)
                recs.append(dict(granule=tile, chip_row=cr, chip_col=cc,
                                 easting=wt.c, northing=wt.f,
                                 transform=[wt.a, wt.b, wt.c, wt.d, wt.e, wt.f],
                                 crs=str(crs), clear_fraction=frac, _arr=arr))
            if (cr + 1) % 10 == 0:
                print(f"    [{tile}] chip row {cr + 1}/{nrow}", flush=True)
        return recs, rej, (nrow, ncol)
    finally:
        _close()


def main():
    t0 = time.perf_counter()
    out = OUT_DEFAULT
    dry = False
    for a in sys.argv[1:]:
        if a.startswith("--source="):
            globals()["SOURCE"] = a.split("=", 1)[1]
        if a.startswith("--out="):
            out = Path(a.split("=", 1)[1])
        elif a == "--dry-run":
            dry = True

    print("=" * 84)
    print("WP3A — cutting the Wald corpus (targets only; degradation is at load time)")
    print("=" * 84)
    print(f"  source        : {DATA}")
    print(f"  chip          : {P.CHIP_PX} px @ {P.GSD_M} m, stride {P.CHIP_STRIDE_PX}")
    print(f"  clear classes : {sorted(P.CLEAR_CLASSES)}   min clear fraction "
          f"{P.MIN_CLEAR_FRACTION}")
    print(f"  reject DN     : {P.REJECT_CHIPS_CONTAINING_DN} "
          f"({'all bands together' if SOURCE == 'tci' else 'any band'})")
    print(f"  held out      : {P.HELDOUT_GRANULE} (whole granule)")
    print(f"  split         : {P.BLOCK_CHIPS}x{P.BLOCK_CHIPS} chip blocks, "
          f"{P.BLOCKS_PER_GRANULE}, seed {P.SPLIT_SEED}, buffer {P.SPLIT_BUFFER_M} m")
    print(f"  numpy {np.__version__} · rasterio {rasterio.__version__} · "
          f"GDAL {rasterio.__gdal_version__}\n")

    all_recs, rejections, grids = [], {}, {}
    for tile, meta in P.GRANULES.items():
        print(f"  screening {tile} ...")
        recs, rej, grid = screen_granule(tile, meta)
        rejections[tile] = rej
        grids[tile] = grid
        all_recs.extend(recs)
        print(f"    {tile}: {rej['accepted']}/{rej['total']} accepted "
              f"(not all clear {rej['not_all_clear']}, nodata DN {rej['has_nodata_dn']})")
    print()

    # ---- split assignment -------------------------------------------------------------
    block_assign = {}
    for tile in P.GRANULES:
        if tile == P.HELDOUT_GRANULE:
            continue
        nrow, ncol = grids[tile]
        block_assign[tile] = S.assign_blocks(tile, nrow // P.BLOCK_CHIPS,
                                             ncol // P.BLOCK_CHIPS)
    for r in all_recs:
        r["split"] = S.split_for_chip(r["granule"], r["chip_row"], r["chip_col"],
                                      block_assign)

    before = len(all_recs)
    drop = S.buffer_violations(all_recs)
    kept = [r for i, r in enumerate(all_recs) if i not in drop]
    print(f"  buffer {P.SPLIT_BUFFER_M:.0f} m: dropped {len(drop)} of {before} chips that "
          f"sat within one chip of a different split")
    print()

    counts = {}
    for s in S.SPLITS:
        counts[s] = sum(1 for r in kept if r["split"] == s)
    per_split_bytes = {s: counts[s] * len(P.BANDS) * P.CHIP_PX * P.CHIP_PX * 2
                       for s in S.SPLITS}
    total_bytes = sum(per_split_bytes.values())

    print(f"  {'split':10s} {'chips':>7s} {'GB':>7s}")
    for s in S.SPLITS:
        print(f"  {s:10s} {counts[s]:7d} {per_split_bytes[s]/1e9:7.3f}")
    print(f"  {'TOTAL':10s} {len(kept):7d} {total_bytes/1e9:7.3f}")
    print()

    if total_bytes > 5e9:
        print("=" * 84)
        print(f"STOP: the corpus would be {total_bytes/1e9:.2f} GB, over the 5 GB ceiling.")
        print("      Not writing. A reduction must be proposed and chosen, not assumed.")
        print("=" * 84)
        return 2

    if dry:
        print("  --dry-run: nothing written.")
        return 0

    out.mkdir(parents=True, exist_ok=True)
    for s in S.SPLITS:
        rs = [r for r in kept if r["split"] == s]
        # WP12: TCI is uint8. Storing it as uint16 would double the corpus for nothing
        # and would misdescribe the product. The source's own dtype is used.
        _dt = np.uint8 if SOURCE == "tci" else np.uint16
        arr = np.zeros((len(rs), len(P.BANDS), P.CHIP_PX, P.CHIP_PX), _dt)
        for i, r in enumerate(rs):
            arr[i] = r["_arr"]
        np.save(out / f"chips_{s}.npy", arr)
        print(f"  wrote chips_{s}.npy  {arr.shape}  {arr.dtype}  "
              f"{(out / f'chips_{s}.npy').stat().st_size/1e9:.3f} GB")

    cols = ["granule", "split", "chip_row", "chip_col", "easting", "northing",
            "crs", "clear_fraction", "index_in_split", "t_a", "t_b", "t_c",
            "t_d", "t_e", "t_f"]
    with open(out / "manifest.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for s in S.SPLITS:
            for i, r in enumerate(x for x in kept if x["split"] == s):
                t = r["transform"]
                w.writerow(dict(granule=r["granule"], split=s, chip_row=r["chip_row"],
                                chip_col=r["chip_col"], easting=r["easting"],
                                northing=r["northing"], crs=r["crs"],
                                clear_fraction=r["clear_fraction"], index_in_split=i,
                                t_a=t[0], t_b=t[1], t_c=t[2], t_d=t[3], t_e=t[4],
                                t_f=t[5]))

    rec = dict(
        work_package="P2-WP3A", generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                                            time.gmtime()),
        granules={k: v for k, v in P.GRANULES.items()},
        bands=list(P.BANDS), clear_classes=sorted(P.CLEAR_CLASSES),
        min_clear_fraction=P.MIN_CLEAR_FRACTION,
        reject_dn=P.REJECT_CHIPS_CONTAINING_DN,
        chip_px=P.CHIP_PX, stride_px=P.CHIP_STRIDE_PX, scale=P.SCALE,
        input_px=P.INPUT_PX, gsd_m=P.GSD_M,
        dn_to_reflectance=P.DN_TO_REFLECTANCE, boa_offset_applied=P.BOA_OFFSET_APPLIED,
        norm_divisor_dn=P.NORM_DIVISOR_DN,
        mtf_at_nyquist=P.MTF_AT_NYQUIST, sigma_source_px=P.sigma_for_mtf(),
        block_chips=P.BLOCK_CHIPS, blocks_per_granule=P.BLOCKS_PER_GRANULE,
        split_buffer_m=P.SPLIT_BUFFER_M, split_seed=P.SPLIT_SEED,
        heldout_granule=P.HELDOUT_GRANULE,
        counts=counts, rejections=rejections, buffer_dropped=len(drop),
        bytes_per_split=per_split_bytes, total_bytes=total_bytes,
        block_assignment={g: {f"{r},{c}": s for (r, c), s in a.items()}
                          for g, a in block_assign.items()},
        versions=dict(numpy=np.__version__, rasterio=rasterio.__version__,
                      gdal=rasterio.__gdal_version__),
        wall_clock_s=time.perf_counter() - t0)
    (out / "corpus.json").write_text(json.dumps(rec, indent=2, default=str))
    print(f"\n  manifest.csv and corpus.json written to {out}")
    print(f"  wall clock {time.perf_counter() - t0:.1f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
