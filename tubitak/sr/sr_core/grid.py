"""Output-grid arithmetic for integer-scale super-resolution.

The whole module is a scaling of one affine transform. It deliberately contains no
distance in metres and no CRS-unit assumption: dividing a pixel size by two is correct in
metres, in degrees, and in feet. That is why `gencp_core.vectors.require_metric` is NOT
applied here — see the Gate S registration, invariance item 5. Project 1 needed metres
because it added a 300 m margin and a 2570 m tile footprint to coordinates; this module
adds no distance to anything, and tiling is done in pixels (`sr_core.tiles`), so the
failure class that produced four bugs in Project 1 has no entry point here.

What IS assumed, and therefore checked where it is assumed:

  * the scale is an integer power of two   -> require_integer_scale
  * the source is north-up and axis-aligned -> require_north_up

Derived from `gencp_core.extent`. Divergences, stated per function below, are real; the two
modules are not interchangeable and are not meant to converge.
"""
from __future__ import annotations


class SRGridError(ValueError):
    """Raised when a requested grid, scale or transform cannot be used.

    Derived from `gencp_core.extent.ExtentError`. Divergence: a separate exception type,
    so that a caller catching Project 2's grid errors does not silently swallow Project 1's
    extent errors (and vice versa) when both are importable in the same process.
    """


def require_integer_scale(s, who="super-resolution"):
    """Refuse a scale factor that is not an integer power of two >= 1. Returns int(s).

    Not copied from anything in gencp_core — Project 1 has no scale factor. The power-of-two
    restriction is not decoration: Gate S asserts `out_pixel_size == src_pixel_size / s` with
    EXACT float equality, and that is only defensible because IEEE-754 division by a power of
    two is exact (it decrements the exponent and touches no significand bit). At s = 3 the
    quotient rounds, exact equality becomes the wrong assertion, and the tolerance that would
    replace it has to be derived rather than inherited. Refusing here keeps the gate honest
    instead of letting an unsupported scale reach an assertion written for a supported one.
    """
    if isinstance(s, bool) or not isinstance(s, int):
        # bool is an int subclass; True would otherwise sail through as scale 1.
        if isinstance(s, float) and s.is_integer():
            s = int(s)
        else:
            raise SRGridError(
                f"{who}: scale must be an integer, got {s!r} ({type(s).__name__})")
    if s < 1:
        raise SRGridError(f"{who}: scale must be >= 1, got {s}")
    if s & (s - 1):
        raise SRGridError(
            f"{who}: scale must be a power of two, got {s}. Gate S asserts the output "
            "pixel size with exact float equality, which is only sound because division "
            "by a power of two is exact in IEEE-754. Supporting {s} means re-deriving "
            "that assertion, not relaxing it.".replace("{s}", str(s)))
    return int(s)


def require_north_up(transform, who="super-resolution"):
    """Refuse a rotated or sheared transform, where axis alignment is about to be assumed.

    Written in the spirit of `gencp_core.vectors.require_metric` — check the assumption at
    the point it is made, not at each call site — but it checks a different assumption.
    Every formula in this module and in the Gate S registration writes the pixel centre as
    `a*(j+0.5) + c`, which drops the `b*(i+0.5)` term. That is correct only when `b == 0`,
    and equally for `d`. A rotated GeoTIFF would produce an output that is arithmetically
    tidy and geometrically wrong — output that looks plausible, which is this project's
    dominant failure class.
    """
    b, d = transform.b, transform.d
    if b != 0.0 or d != 0.0:
        raise SRGridError(
            f"{who} assumes a north-up, axis-aligned raster and was given a transform "
            f"with rotation/shear terms b={b!r}, d={d!r}. Every pixel-centre formula in "
            "sr_core drops those terms. Reproject the source to a north-up grid first.")
    if transform.a == 0.0 or transform.e == 0.0:
        raise SRGridError(
            f"{who}: degenerate transform, pixel size is zero on an axis "
            f"(a={transform.a!r}, e={transform.e!r}).")
    return transform


def output_grid(src_transform, width, height, scale=2):
    """The output grid for an integer refinement of a source raster.

    Returns (out_width, out_height, out_transform).

    Derived from `gencp_core.extent.output_grid`. Divergences, both material:

      * gencp_core's version takes a map-coordinate EXTENT and snaps a grid to it, with
        `ceil(span / NOMINAL)` and an east/south overhang of up to one pixel. This version
        takes a SOURCE RASTER and refines it, so there is no snapping, no ceiling and no
        overhang: the output covers exactly the source footprint.
      * gencp_core's version reads the pixel size from the module global `NOMINAL = 10.0`.
        This one derives it from the source transform and the scale argument, because
        Project 2's output pixel size is a function of its input rather than a constant.

    The origin is COPIED from the source, never recomputed — Gate S invariance item 3.
    """
    from rasterio.transform import Affine
    s = require_integer_scale(scale, "output_grid")
    require_north_up(src_transform, "output_grid")
    w, h = int(width), int(height)
    if w < 1 or h < 1:
        raise SRGridError(
            f"output_grid: source raster must have at least one pixel, got {w} x {h}")
    a, e = src_transform.a / s, src_transform.e / s
    return w * s, h * s, Affine(a, 0.0, src_transform.c, 0.0, e, src_transform.f)


def source_pixel_centre(transform, row, col):
    """Map coordinates of the centre of source pixel (row, col).

    The convention is registered in `tubitak/sr/docs/gate-s-registration.md` §2 and is not
    restated differently anywhere: rows increase southward, columns eastward, both
    zero-based, and the centre of pixel (i, j) is (a*(j+0.5) + c, e*(i+0.5) + f).
    """
    return (transform.a * (col + 0.5) + transform.c,
            transform.e * (row + 0.5) + transform.f)


def output_block_centre(out_transform, row, col, scale):
    """Map coordinates of the centre of the s x s output block covering source (row, col).

    The block is output rows [s*row, s*row + s) and columns [s*col, s*col + s), so its
    centre sits at output pixel coordinate (s*col + s/2, s*row + s/2). No rounding is
    applied: for even s the centre falls on a pixel boundary, which is exactly where the
    source pixel centre is, and that coincidence is what "no shift" means.
    """
    s = require_integer_scale(scale, "output_block_centre")
    return (out_transform.a * (col * s + s / 2) + out_transform.c,
            out_transform.e * (row * s + s / 2) + out_transform.f)
