"""CLI and pipeline for integer-scale super-resolution of a GeoTIFF.

    python -m sr_core.run --input <tif> --output <tif> --scale 2 --method bicubic

Runs outside QGIS. Plugin wiring is WP2 and is not started here.

The pipeline is: open the source, derive the output grid from its transform
(`sr_core.grid`), lay tiles over it in source pixels (`sr_core.tiles`), upsample each tile
(`sr_core.upsample`), and blend the results onto the output grid by integer placement
(`sr_core.mosaic`). Band count, dtype and nodata are read from the source profile rather
than assumed, so a later 4-band uint16 reflectance input is a data change and not a rewrite.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

if __package__ in (None, ""):                       # run as a file path, not as -m
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from sr_core import grid as _grid, mosaic as _mosaic, tiles as _tiles, upsample as _up
else:
    from . import grid as _grid, mosaic as _mosaic, tiles as _tiles, upsample as _up

METHODS = {"bicubic": _up.BicubicUpsampler}


def peak_rss_bytes():
    """Peak resident set size of this process, in bytes.

    `ru_maxrss` is BYTES on macOS/BSD and KILOBYTES on Linux — a units difference that is
    exactly the kind of thing this project has been bitten by, so it is resolved by platform
    rather than assumed.
    """
    import resource
    v = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(v) if sys.platform == "darwin" else int(v) * 1024


def superresolve(src_path, out_path, scale=2, method="bicubic",
                 tile_px=_tiles.DEFAULT_TILE_PX, overlap_px=_tiles.DEFAULT_OVERLAP_PX,
                 window=None, clip=True, progress=None):
    """Super-resolve `src_path` onto `out_path`. Returns a dict describing the run.

    `window` is an optional `(col0, row0, width, height)` in source pixels; the grid
    contract then applies to that sub-raster, whose own transform becomes the source
    transform. This is what lets the verification cases work on a tractable subwindow of a
    10980 x 10980 scene without weakening what is being asserted.
    """
    import rasterio
    from rasterio.windows import Window

    t0 = time.perf_counter()
    up_cls = METHODS.get(method)
    if up_cls is None:
        raise ValueError(f"unknown method {method!r}; known: {sorted(METHODS)}")
    s = _grid.require_integer_scale(scale, "superresolve")
    up = up_cls(scale=s, clip=clip)

    with rasterio.open(str(src_path)) as src:
        if window is None:
            win = Window(0, 0, src.width, src.height)
        else:
            c0, r0, w, h = (int(v) for v in window)
            if c0 < 0 or r0 < 0 or w < 1 or h < 1 \
                    or c0 + w > src.width or r0 + h > src.height:
                raise _grid.SRGridError(
                    f"window {(c0, r0, w, h)} does not lie inside the source raster "
                    f"({src.width} x {src.height})")
            win = Window(c0, r0, w, h)
        W, H = int(win.width), int(win.height)
        src_T = _grid.require_north_up(src.window_transform(win), "superresolve")
        count, dtype, nodata, crs = src.count, src.dtypes[0], src.nodata, src.crs
        src_profile = dict(crs=crs, transform=src_T, width=W, height=H,
                           dtype=dtype, nodata=nodata, count=count)

        out_w, out_h, out_T = _grid.output_grid(src_T, W, H, s)
        tlist, stride = _tiles.tile_grid(W, H, tile_px, overlap_px)
        prov = _mosaic.provenance(src_path, up, s, src_profile, (out_h, out_w),
                                  tile_px, overlap_px,
                                  extra={"source_window_col0_row0_w_h":
                                         [int(win.col_off), int(win.row_off), W, H]})

        prof = dict(driver="GTiff", height=out_h, width=out_w, count=count,
                    dtype=dtype, crs=crs, transform=out_T, compress="deflate",
                    tiled=True, blockxsize=512, blockysize=512)
        if nodata is not None:
            prof["nodata"] = nodata

        n = len(tlist)
        with _mosaic.atomic_path(out_path) as tmp:
            with rasterio.open(str(tmp), "w", **prof) as dst:
                # The band must hold the tallest span one tile row can occupy.
                mos = _mosaic.StreamingMosaic(dst, count, out_w, dtype,
                                              band_rows=min(out_h, tile_px * s),
                                              nodata=nodata)
                for k, t in enumerate(tlist, 1):
                    i, j, col0, row0, tw, th = t
                    sub = Window(win.col_off + col0, win.row_off + row0, tw, th)
                    arr = np.moveaxis(src.read(window=sub), 0, -1)   # -> h x w x C
                    block = up.upsample(arr)
                    top, bot, left, right = _mosaic.tile_ramp_sides(t, tlist)
                    wgt = _mosaic.feather_weight(th * s, tw * s, overlap_px * s,
                                                 top, bot, left, right)
                    mos.add(block, wgt, row0 * s, col0 * s)
                    if progress is not None:
                        progress(k, n)
                mos.close()
                prov["uncovered_output_pixels"] = mos.uncovered
                prov["peak_accumulator_rows"] = mos.peak_band_rows
                prov["clipped_output_values"] = int(up.n_clipped)
                prov["total_output_values"] = int(up.n_total)
                dst.update_tags(GENCP_SR_PROVENANCE=json.dumps(prov, sort_keys=True))

    return {
        "input": str(src_path), "output": str(out_path),
        "scale": s, "method": up.name,
        "source_shape": [H, W], "output_shape": [out_h, out_w],
        "count": count, "dtype": str(dtype), "nodata": nodata, "crs": str(crs),
        "source_transform": tuple(src_T)[:6], "output_transform": tuple(out_T)[:6],
        "n_tiles": n, "tile_px": tile_px, "overlap_px": overlap_px, "stride_px": stride,
        "clipped_output_values": int(up.n_clipped),
        "total_output_values": int(up.n_total),
        "uncovered_output_pixels": mos.uncovered,
        "peak_accumulator_rows": mos.peak_band_rows,
        "wall_clock_s": time.perf_counter() - t0,
        "peak_rss_bytes": peak_rss_bytes(),
        "output_size_bytes": Path(out_path).stat().st_size,
        "provenance": prov,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="sr_core.run",
        description="Integer-scale super-resolution of a GeoTIFF, on the exact "
                    "refinement of the source grid (Gate S contract).")
    ap.add_argument("--input", required=True, help="source GeoTIFF")
    ap.add_argument("--output", required=True, help="destination GeoTIFF")
    ap.add_argument("--scale", type=int, default=2,
                    help="integer power-of-two scale factor (default 2)")
    ap.add_argument("--method", default="bicubic", choices=sorted(METHODS))
    ap.add_argument("--tile-px", type=int, default=_tiles.DEFAULT_TILE_PX,
                    help=f"tile size in SOURCE pixels (default {_tiles.DEFAULT_TILE_PX})")
    ap.add_argument("--overlap-px", type=int, default=_tiles.DEFAULT_OVERLAP_PX,
                    help=f"tile overlap in SOURCE pixels "
                         f"(default {_tiles.DEFAULT_OVERLAP_PX})")
    ap.add_argument("--window", type=int, nargs=4, metavar=("COL0", "ROW0", "W", "H"),
                    help="process only this source-pixel window")
    ap.add_argument("--no-clip", action="store_true",
                    help="do not clip bicubic overshoot to the dtype range "
                         "(see sr_core.upsample: the integer cast then WRAPS)")
    ap.add_argument("--json", action="store_true", help="print the run record as JSON")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)

    if not Path(a.input).is_file():
        ap.error(f"input not found: {a.input}")

    def prog(k, n):
        if not a.quiet and (k == n or k % 50 == 0):
            print(f"  tile {k}/{n}", file=sys.stderr, flush=True)

    rec = superresolve(a.input, a.output, scale=a.scale, method=a.method,
                       tile_px=a.tile_px, overlap_px=a.overlap_px,
                       window=a.window, clip=not a.no_clip, progress=prog)
    if a.json:
        print(json.dumps({k: v for k, v in rec.items() if k != "provenance"},
                         indent=2, default=str))
    elif not a.quiet:
        print(f"{rec['method']} x{rec['scale']}  "
              f"{rec['source_shape'][1]}x{rec['source_shape'][0]} -> "
              f"{rec['output_shape'][1]}x{rec['output_shape'][0]}  "
              f"{rec['n_tiles']} tiles  {rec['wall_clock_s']:.1f} s  "
              f"{rec['output_size_bytes']/1e6:.1f} MB  -> {rec['output']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
