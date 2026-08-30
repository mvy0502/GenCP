"""Tiling of the source raster, in SOURCE PIXEL coordinates.

Everything here is integers. There is no map coordinate and no distance in metres in this
module, which is deliberate: `gencp_core.extent.tile_grid` works in metres because its
tiles are defined by a 2570 m ground footprint, and three of Project 1's four
metres-as-degrees bugs happened in code that mixed map units into layout arithmetic. A
source-pixel layout cannot have that bug, and it is also the natural unit for an upsampler,
whose patch size is a pixel count rather than a ground distance.

Why tiles overlap, and why the default is 32 rather than the kernel support.

The cubic-convolution kernel reaches 2 source pixels each side, so it is tempting to argue
that an overlap of 2 to 4 px suffices for bicubic. That argument was written here before it
was tested and it is WRONG. Measured by `tubitak/sr/tests/tiling_equivalence.py` on a
512 x 512 window of `tubitak/data/tiles36SVJ/TCI.tif` at s=2, tiled output against a
single whole-window upsample, in DN of uint8:

    overlap 32 px -> max |diff| 0 DN            overlap 4 px -> max |diff| 1 DN
    overlap  8 px -> max |diff| 0 DN            overlap 2 px -> max |diff| 6 DN
                                                overlap 0 px -> max |diff| 47 DN

The reason the naive argument fails is the feather itself: the ramp spans the whole overlap,
so at a small overlap the outermost source pixels — the ones whose bicubic neighbourhood was
truncated at the tile edge — still carry appreciable weight. Only from about 8 px does their
weight fall far enough that the difference rounds away in uint8. 8 px is where it happens to
vanish for THIS scene and dtype, which is not a guarantee; 32 px is the default because:

  * it is comfortably past the measured threshold rather than sitting on it, and
  * for a trained convolutional model the effective receptive field is tens of pixels and
    the tile edges genuinely disagree, which is what the feather blend in `sr_core.mosaic`
    exists for. Sizing the default for that case means swapping in an ONNX model in WP4 does
    not also require re-choosing the layout.
"""
from __future__ import annotations

DEFAULT_TILE_PX = 512
DEFAULT_OVERLAP_PX = 32


class TileError(ValueError):
    """Raised when a tile layout is impossible or would not terminate."""


def tile_grid(width, height, tile_px=DEFAULT_TILE_PX, overlap_px=DEFAULT_OVERLAP_PX):
    """Lay tiles over a `width` x `height` source raster. Returns (tiles, stride).

    Each tile is `(i, j, col0, row0, w, h)` in source pixel coordinates: `i` the tile row
    index, `j` the tile column index, `(col0, row0)` the north-west corner, `(w, h)` the
    size. Tiles are clamped to the raster, so an edge tile is shifted back rather than
    running past the boundary; when the raster is smaller than one tile in an axis, a
    single tile of the full extent is used on that axis.

    Guarantees, all of them asserted by `tubitak/sr/tests/gate_s.py`:
      * every tile lies wholly inside [0, width) x [0, height)
      * the union of the tiles is the whole raster, with no gap
      * `w == h == tile_px` except where the raster is smaller than a tile

    Derived from `gencp_core.extent.tile_grid`. Divergences:
      * source pixels, not metres; tile size is a pixel count, not `TILE_M = 2570`
      * edge tiles are CLAMPED back inside the raster. gencp_core lets its last tile run
        past the requested extent, because a generated tile is synthesised and there is
        nothing to run past; here a tile is READ from a real raster and reading past the
        edge would either raise or silently pad.
      * returns explicit per-tile sizes, because clamping makes them vary.
    """
    w, h = int(width), int(height)
    tile_px, overlap_px = int(tile_px), int(overlap_px)
    if w < 1 or h < 1:
        raise TileError(f"raster must have at least one pixel, got {w} x {h}")
    if tile_px < 1:
        raise TileError(f"tile size must be >= 1 px, got {tile_px}")
    if not 0 <= overlap_px < tile_px:
        raise TileError(
            f"overlap must be in [0, {tile_px}) px, got {overlap_px}. At or above the "
            "tile size the stride is zero or negative and the layout does not terminate.")
    stride = tile_px - overlap_px

    def starts(extent_px):
        """North-west corners along one axis, clamped so no tile leaves the raster."""
        if extent_px <= tile_px:
            return [0], min(tile_px, extent_px)
        out, p = [], 0
        while True:
            if p + tile_px >= extent_px:
                out.append(extent_px - tile_px)
                break
            out.append(p)
            p += stride
        return out, tile_px

    col0s, tw = starts(w)
    row0s, th = starts(h)
    tiles = [(i, j, c, r, tw, th)
             for i, r in enumerate(row0s)
             for j, c in enumerate(col0s)]
    return tiles, stride
