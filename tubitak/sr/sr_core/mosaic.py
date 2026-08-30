"""Feathered blending of upsampled tiles, and the atomic GeoTIFF write.

Two things here are deliberate departures from `gencp_core.mosaic`, and both matter.

**1. Blocks are placed by integer indexing, never by resampling.**
`gencp_core.mosaic.build` places every tile with `rasterio.warp.reproject`, and it has to:
its tiles carry a TRUE_GSD of 10.0390625 m while the output grid is 10.0 m, so a tile does
not land on integer output pixels and must be resampled onto them. Here the source tile at
`(row0, col0)` upsampled by `s` occupies output rows `[s*row0, s*row0 + s*h)` and columns
`[s*col0, s*col0 + s*w)` — exactly, by construction. Placing it with a warp would introduce
a second interpolation on top of the upsampler's, for no reason, and would turn Gate S
assertion S5 from a statement about arithmetic into a statement about GDAL's resampling.
This is Gate S invariance item 4.

**2. The mosaic is streamed, not accumulated whole.**
One 10980 x 10980 TCI scene at s=2 is a 21960 x 21960 x 3 output. A float64 accumulator for
that is 11.6 GB, plus 3.9 GB of weights — on a 36 GB machine that is an out-of-memory bug
waiting for the second concurrent run. `StreamingMosaic` keeps only the band of output rows
that tiles can still touch, and flushes rows below it as soon as the tile layout guarantees
nothing will write there again. Peak accumulator memory is `s*tile_px` output rows rather
than the whole raster, which for the default 512 px tile is 1024 rows regardless of scene
size.

**Atomic writes.** Every raster this module produces is written to a temporary file in the
same directory, fsynced, and then `os.replace`d into position. In Project 1 a truncated
`.tif` from an interrupted run was treated as a cache hit and silently baked into a later
mosaic; `os.replace` is atomic within a filesystem, so a reader sees either the previous
file or a complete new one and never a half-written one.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path

import numpy as np

_INT_KINDS = "iub"
#: Below this accumulated weight an output pixel is treated as uncovered. The tile layout
#: covers the whole raster, so in a correct run no interior pixel reaches it.
WEIGHT_EPS = 1e-6


def feather_weight(h, w, overlap_px, ramp_top=True, ramp_bottom=True,
                   ramp_left=True, ramp_right=True):
    """Separable raised-cosine ramp over the overlap margin, 1.0 in the interior.

    Derived from `gencp_core.mosaic.feather_weight`, same kernel:
    `0.5 - 0.5*cos(pi*(arange(r) + 0.5)/r)`. Divergences:

      * `h` and `w` are explicit, because edge tiles are clamped and are not square.
      * **the four sides ramp independently.** gencp_core ramps all four unconditionally,
        which is right when every tile has neighbours; at the outer boundary of the raster
        it drives the accumulated weight to ~1e-4 of its interior value, and the mosaic then
        divides by that. Normalisation still recovers the value algebraically, but it is
        numerically weak for no gain. A side with no neighbour is not ramped, so boundary
        pixels carry weight 1.0.
    """
    r = max(int(overlap_px), 1)

    def axis(n, lo, hi):
        v = np.ones(n, np.float32)
        k = min(r, n // 2)
        if k < 1:
            return v
        ramp = (0.5 - 0.5 * np.cos(np.pi * (np.arange(k) + 0.5) / k)).astype(np.float32)
        if lo:
            v[:k] = ramp
        if hi:
            v[-k:] = ramp[::-1]
        return v

    return np.outer(axis(h, ramp_top, ramp_bottom), axis(w, ramp_left, ramp_right))


def tile_ramp_sides(tile, tiles):
    """(top, bottom, left, right): which sides of `tile` have a neighbour to blend into.

    A side at the raster boundary has no neighbour and must not be ramped.
    """
    i, j = tile[0], tile[1]
    max_i = max(t[0] for t in tiles)
    max_j = max(t[1] for t in tiles)
    return (i > 0, i < max_i, j > 0, j < max_j)


def _sha256(path, limit=None):
    """SHA-256 of a file. `limit` caps the bytes read, for multi-GB inputs."""
    hsh, n = hashlib.sha256(), 0
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            if limit is not None and n + len(chunk) > limit:
                hsh.update(chunk[: limit - n])
                return hsh.hexdigest(), limit, True
            hsh.update(chunk)
            n += len(chunk)
    return hsh.hexdigest(), n, False


def provenance(src_path, upsampler, scale, src_profile, out_shape, tile_px, overlap_px,
               extra=None, hash_limit=256 << 20):
    """The record embedded in the output GeoTIFF as the `GENCP_SR_PROVENANCE` tag.

    Derived from `gencp_core.pipeline.provenance`. Divergences: it identifies a SOURCE
    RASTER and an upsampler rather than an ONNX model and a vector source, and it records
    the library versions that affect numerics, which gencp_core's version does not (standing
    practice 9 — Registration A's stochastic arm cannot be reproduced because they were not
    recorded).
    """
    import PIL
    import rasterio

    p = Path(src_path)
    digest, hashed, truncated = _sha256(p, hash_limit)
    rec = {
        "tool": "gencp-sr",
        "work_package": "P2-WP1",
        "generated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source_file": p.name,
        "source_sha256": digest,
        "source_sha256_bytes_hashed": hashed,
        "source_sha256_is_prefix": truncated,
        "source_size_bytes": p.stat().st_size,
        "source_crs": str(src_profile.get("crs")),
        "source_pixel_size": [abs(src_profile["transform"].a),
                              abs(src_profile["transform"].e)],
        "source_shape": [src_profile["height"], src_profile["width"]],
        "source_dtype": str(src_profile["dtype"]),
        "source_nodata": src_profile.get("nodata"),
        "method": upsampler.name,
        "scale": int(scale),
        "output_shape": list(out_shape),
        "tile_px": int(tile_px),
        "overlap_px": int(overlap_px),
        "block_placement": "integer indexing on the output grid; no resampling",
        "resampling_convention": "half-pixel centres (PIL); output k samples source "
                                 "(k + 0.5)/s - 0.5",
        "random_seed": None,
        "stochastic": False,
        "grid_contract": ("Gate S: out CRS == src CRS; out pixel size == src/s exactly; "
                          "out origin == src origin exactly; out size == s*src exactly; "
                          "source pixel centre == centre of its s x s output block"),
        "versions": {
            "numpy": np.__version__,
            "rasterio": rasterio.__version__,
            "gdal": rasterio.__gdal_version__,
            "pillow": PIL.__version__,
        },
    }
    rec.update(extra or {})
    return rec


@contextmanager
def atomic_path(final_path):
    """Yield a temp path in the same directory; fsync and `os.replace` it into place.

    Same directory so the rename is within one filesystem and therefore atomic. The
    directory itself is fsynced afterwards, so the rename survives a power loss rather than
    only the file's contents. On any exception the temp file is removed and `final_path` is
    left exactly as it was.
    """
    final_path = Path(final_path)
    final_path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(final_path.parent),
                               prefix=f".{final_path.name}.", suffix=".part")
    os.close(fd)
    tmp = Path(tmp)
    try:
        yield tmp
        f = os.open(str(tmp), os.O_RDONLY)
        try:
            os.fsync(f)
        finally:
            os.close(f)
        os.replace(str(tmp), str(final_path))
        d = os.open(str(final_path.parent), os.O_RDONLY)
        try:
            os.fsync(d)
        finally:
            os.close(d)
    except BaseException:
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass
        raise


def write_geotiff(path, arr, crs, transform, nodata=None, provenance_rec=None,
                  compress="deflate"):
    """Write an `H x W x C` array as a GeoTIFF, atomically, on the given transform.

    Derived from `gencp_core.mosaic.write_geotiff`. Divergences: dtype, band count and
    nodata come from the ARRAY and the caller rather than being fixed at 3-band uint8 with
    nodata 0; the write is atomic; the provenance tag is `GENCP_SR_PROVENANCE`, a distinct
    key, so a consumer never mistakes an SR product for a Project 1 synthetic reference.
    """
    import rasterio
    a = np.asarray(arr)
    if a.ndim != 3:
        raise ValueError(f"write_geotiff expects H x W x C, got shape {a.shape}")
    h, w, c = a.shape
    prof = dict(driver="GTiff", height=h, width=w, count=c, dtype=a.dtype.name,
                crs=crs, transform=transform, compress=compress, tiled=True,
                blockxsize=512, blockysize=512)
    if nodata is not None:
        prof["nodata"] = nodata
    with atomic_path(path) as tmp:
        with rasterio.open(str(tmp), "w", **prof) as d:
            d.write(np.moveaxis(a, -1, 0))
            if provenance_rec:
                d.update_tags(GENCP_SR_PROVENANCE=json.dumps(provenance_rec,
                                                             sort_keys=True))
    return Path(path)


class StreamingMosaic:
    """Weighted-average blending over a moving band of output rows.

    Usage is strictly in tile-row order: `add()` every tile of tile-row *i*, then `add()`
    tile-row *i+1*, and so on. `add` flushes rows the layout guarantees are finished. The
    caller closes it.

    Derived from `gencp_core.mosaic.build`, same accumulate-then-normalise arithmetic
    (`acc += value*weight`, `wacc += weight`, `out = acc/wacc`). Divergences: streamed
    rather than whole-raster, and blocks are placed by integer slicing rather than by
    `reproject`.
    """

    def __init__(self, dst, count, out_w, dtype, band_rows, nodata=None):
        """`band_rows` is the fixed height of the accumulator, in OUTPUT rows.

        It must be at least `scale * tile_px`, which is the tallest span any single tile
        row can occupy. The buffer is allocated ONCE at this height and never grown.

        The first version of this class grew the band with `np.concatenate` and consumed it
        with `self.acc = self.acc[:, n:]`. Both were wrong, and the second was the worse of
        the two: numpy basic slicing returns a VIEW, and a view keeps its base buffer alive,
        so the accumulator's memory was never actually released — it was merely no longer
        reachable through an index. It was found by measurement rather than by reading:
        two runs with equal output pixel counts but transposed aspect gave peak RSS
        2.655 GB (output 21960 wide x 4096 tall) against 0.953 GB (4096 wide x 21960 tall),
        which is the signature of a full-output-width buffer that is not being recycled.
        """
        self.dst = dst
        self.count = int(count)
        self.out_w = int(out_w)
        self.dtype = np.dtype(dtype)
        self.nodata = nodata
        self.band_rows = int(band_rows)
        if self.band_rows < 1:
            raise ValueError(f"band_rows must be >= 1, got {band_rows}")
        self.row0 = 0                      # first output row held in the band
        self.filled = 0                    # rows of the band currently in use
        self.acc = np.zeros((self.count, self.band_rows, self.out_w), np.float32)
        self.wacc = np.zeros((self.band_rows, self.out_w), np.float32)
        self.peak_band_rows = 0
        self.uncovered = 0

    def _reserve(self, r_hi):
        need = r_hi - self.row0
        if need > self.band_rows:
            raise ValueError(
                f"block needs output rows [{self.row0}, {r_hi}) = {need} rows but the "
                f"accumulator band is {self.band_rows}. band_rows must be >= scale * "
                "tile_px; tiles must be added in tile-row order.")
        self.filled = max(self.filled, need)
        self.peak_band_rows = max(self.peak_band_rows, self.filled)

    def flush_below(self, r):
        """Finalise and write every held output row strictly below `r`, then compact."""
        n = min(r - self.row0, self.filled)
        if n <= 0:
            return
        self._emit(self.acc[:, :n], self.wacc[:n], self.row0)
        keep = self.filled - n
        if keep > 0:
            # The retained tail is only the vertical overlap (scale * overlap_px rows), so
            # this copy is small. It is an explicit copy rather than an overlapping in-place
            # assignment, which numpy is not obliged to do correctly.
            tail_a = self.acc[:, n:self.filled].copy()
            tail_w = self.wacc[n:self.filled].copy()
            self.acc[:, :keep] = tail_a
            self.wacc[:keep] = tail_w
        self.acc[:, keep:self.filled] = 0.0
        self.wacc[keep:self.filled] = 0.0
        self.filled = keep
        self.row0 += n

    #: Rows normalised per pass in `_emit`. Every temporary there is
    #: (bands x rows x output_width) float32, so the whole band at once is expensive at a
    #: full-scene width. MEASURED on 36SVJ at output width 21960, GDAL_CACHEMAX=64:
    #: peak RSS 2.955 / 1.716 / 1.214 GB for accumulator bands of 1024 / 512 / 256 rows,
    #: i.e. ~2.42 MB per band row against the 0.35 MB the buffers themselves need — about
    #: seven simultaneous full-band float32 temporaries. Chunking and writing in place
    #: bounds them to this many rows regardless of the band or the scene.
    EMIT_CHUNK_ROWS = 128

    def _emit(self, acc, wacc, row0):
        import rasterio
        fill = float(0 if self.nodata is None else self.nodata)
        is_int = self.dtype.kind in _INT_KINDS
        if is_int:
            info = np.iinfo(self.dtype)
        n = acc.shape[1]
        for r0 in range(0, n, self.EMIT_CHUNK_ROWS):
            r1 = min(r0 + self.EMIT_CHUNK_ROWS, n)
            w = wacc[r0:r1]
            good = w > WEIGHT_EPS
            self.uncovered += int(np.count_nonzero(~good))
            out = np.full((self.count, r1 - r0, self.out_w), fill, np.float32)
            np.divide(acc[:, r0:r1], w[None, ...], out=out, where=good[None, ...])
            if is_int:
                # Normalising a weighted average of in-range values cannot leave the range
                # mathematically; this clip only absorbs float32 rounding at the last ulp,
                # so it is NOT counted as clipping in the upsampler's statistics.
                np.rint(out, out=out)
                np.clip(out, info.min, info.max, out=out)
            self.dst.write(out.astype(self.dtype),
                           window=rasterio.windows.Window(0, row0 + r0,
                                                          self.out_w, r1 - r0))

    def add(self, block, weight, out_row0, out_col0):
        """Blend one upsampled block in at output pixel (out_row0, out_col0).

        `block` is `h x w x C`; `weight` is `h x w`.
        """
        b = np.asarray(block)
        h, w = b.shape[0], b.shape[1]
        if weight.shape != (h, w):
            raise ValueError(f"weight {weight.shape} does not match block {(h, w)}")
        if out_row0 < self.row0:
            raise ValueError(
                f"tile at output row {out_row0} is behind the accumulator band, which "
                f"starts at {self.row0}. Tiles must be added in tile-row order; rows "
                "below the band have already been written and cannot be revised.")
        self.flush_below(out_row0)
        self._reserve(out_row0 + h)
        r = out_row0 - self.row0
        sl = (slice(r, r + h), slice(out_col0, out_col0 + w))
        wf = weight.astype(np.float32)
        self.wacc[sl] += wf
        bf = np.moveaxis(b.astype(np.float32), -1, 0)
        self.acc[(slice(None),) + sl] += bf * wf[None, ...]

    def close(self):
        self.flush_below(self.row0 + self.filled)


# ---------------------------------------------------------------------------------------
# WP6, PURELY ADDITIVE: crop-the-margin placement, for models that must not be blended.
#
# The feather path above is correct for an L1-trained model, whose tile predictions agree
# closely in the overlap so that averaging them is a smoothing of near-identical numbers.
# It is WRONG for a GAN-family model: WP5 measured that averaging two ESRGAN predictions of
# the same ground differs from either of them by up to 37 DN at a 32 px overlap, and still
# 20 DN at 64 px, so the residual is not context starvation and no overlap removes it.
#
# The reference tool (sentinel2_superresolution, Michel et al.) does not blend. It pads each
# tile by a margin, runs the network, crops the margin off, and lets the remainders abut.
# This is that scheme. Nothing above this line changes, and a model that does not ask for
# cropping never reaches this code.
# ---------------------------------------------------------------------------------------


class CropLayoutError(ValueError):
    """The tile layout cannot be cropped by the requested margin and still tile exactly."""


def crop_keep_bounds(tiles, out_h, out_w, scale, margin_out):
    """Per-tile output keep-box, proven to partition the output exactly.

    Returns {(i, j): (r0, r1, c0, c1)} in OUTPUT pixels, the half-open region of that tile's
    upsampled block that is written. Regions abut with no gap and no overlap, so no output
    pixel is written twice and none is left unwritten. That is asserted here on the
    INTERVALS - exact integer arithmetic over a few hundred numbers - rather than by
    painting a coverage raster, which at 21960 x 21960 would cost half a gigabyte to learn
    the same fact less reliably.

    The rule, per axis: a tile keeps from where its predecessor stopped to `margin_out`
    inside its own trailing edge; the first tile starts at 0 and the last runs to the end.
    A boundary side is never cropped, because there is no neighbour to supply its context
    and cropping it would leave the raster border unwritten.
    """
    s, m = int(scale), int(margin_out)
    if m < 0:
        raise CropLayoutError(f"margin must be >= 0 output px, got {m}")

    def axis(starts_sizes, out_extent):
        """starts_sizes: [(start_src, size_src)] in tile-index order."""
        n = len(starts_sizes)
        keep, prev_end = [], 0
        for k, (p, t) in enumerate(starts_sizes):
            lo = 0 if k == 0 else prev_end
            hi = out_extent if k == n - 1 else (p + t) * s - m
            if k > 0 and lo < p * s + m:
                raise CropLayoutError(
                    f"tile {k} would keep output pixels from {lo}, which is less than "
                    f"{m} px inside its own leading edge at {p * s}. The overlap is too "
                    f"small for a margin of {m} output px: it must be at least "
                    f"{2 * m / s:g} source px, and the tile layout gives less.")
            if hi <= lo:
                raise CropLayoutError(
                    f"tile {k} keeps an empty region [{lo}, {hi}); the margin {m} is too "
                    f"large for this tile size.")
            keep.append((lo, hi))
            prev_end = hi
        if keep[-1][1] != out_extent:
            raise CropLayoutError(f"kept regions end at {keep[-1][1]}, not {out_extent}")
        for a, b in zip(keep, keep[1:]):
            if a[1] != b[0]:
                raise CropLayoutError(f"kept regions {a} and {b} do not abut")
        return keep

    rows = sorted({(r, th) for (_i, _j, _c, r, _tw, th) in tiles})
    cols = sorted({(c, tw) for (_i, _j, c, _r, tw, _th) in tiles})
    kr = axis(rows, out_h)
    kc = axis(cols, out_w)
    ri = {r: k for k, (r, _t) in enumerate(rows)}
    ci = {c: k for k, (c, _t) in enumerate(cols)}
    out = {}
    for (i, j, c, r, _tw, _th) in tiles:
        r0, r1 = kr[ri[r]]
        c0, c1 = kc[ci[c]]
        out[(i, j)] = (r0, r1, c0, c1)
    return out


def min_overlap_for_margin(margin_out, scale):
    """Smallest source-pixel overlap that lets `margin_out` be cropped and still tile."""
    import math
    return int(math.ceil(2.0 * int(margin_out) / int(scale)))


class CropMosaic:
    """Writes cropped tile interiors straight to the dataset. No accumulation, no blending.

    Same `add`/`close` surface as `StreamingMosaic` so `run.superresolve` can choose between
    them, but the arithmetic is different in kind: nothing is averaged, so a pixel's value is
    exactly what the network produced for the tile that owns it.
    """

    def __init__(self, dst, count, out_h, out_w, dtype, keep, nodata=None):
        self.dst, self.count = dst, int(count)
        self.out_h, self.out_w = int(out_h), int(out_w)
        self.dtype = np.dtype(dtype)
        self.keep = keep
        self.nodata = nodata
        self.uncovered = 0                 # zero by construction; see crop_keep_bounds
        self.peak_band_rows = 0
        self.written = 0

    def add(self, block, tile):
        """`block` is the tile's upsampled H x W x C output; `tile` its layout entry."""
        import rasterio
        i, j, col0, row0, _tw, _th = tile
        r0, r1, c0, c1 = self.keep[(i, j)]
        s_r0, s_c0 = r0 - row0 * self._scale_r(block, _th), c0 - col0 * self._scale_c(block, _tw)
        sub = block[s_r0:s_r0 + (r1 - r0), s_c0:s_c0 + (c1 - c0)]
        if sub.shape[0] != r1 - r0 or sub.shape[1] != c1 - c0:
            raise CropLayoutError(
                f"tile ({i},{j}) keep box {(r0, r1, c0, c1)} does not lie inside its own "
                f"block of shape {block.shape[:2]} at output origin "
                f"{(row0 * self._scale_r(block, _th), col0 * self._scale_c(block, _tw))}")
        arr = np.moveaxis(np.ascontiguousarray(sub), -1, 0).astype(self.dtype, copy=False)
        self.dst.write(arr, window=rasterio.windows.Window(c0, r0, c1 - c0, r1 - r0))
        self.written += (r1 - r0) * (c1 - c0)
        self.peak_band_rows = max(self.peak_band_rows, r1 - r0)

    @staticmethod
    def _scale_r(block, th):
        return block.shape[0] // int(th)

    @staticmethod
    def _scale_c(block, tw):
        return block.shape[1] // int(tw)

    def close(self):
        if self.written != self.out_h * self.out_w:
            raise CropLayoutError(
                f"wrote {self.written} output pixels, expected exactly "
                f"{self.out_h * self.out_w}")
        return self
