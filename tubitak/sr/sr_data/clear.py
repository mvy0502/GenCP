"""SCL clear-masking, and the 20 m -> 10 m expansion it needs.

The expansion is lossless and that is a checkable property, not a convenience: WP2A §4.3
established that each granule's 20 m SCL grid nests exactly inside its 10 m band grid — same
CRS, same origin, exactly half the sample spacing, exactly half the width and height. Under
that condition one SCL pixel covers exactly the 2 x 2 block of band pixels at (2i, 2j), so
`np.repeat` twice is an exact restatement of the mask rather than a resampling of it.

The nesting is REQUIRED here rather than assumed, because if it ever failed the mask would
silently slide by half a pixel and every clear-fraction in the corpus would be subtly wrong
while still looking entirely reasonable.
"""
from __future__ import annotations

import numpy as np

from .params import CLEAR_CLASSES


class GridMismatch(ValueError):
    """Raised when an SCL grid does not nest exactly inside its band grid."""


def require_nested(band_profile, scl_profile, who="clear mask"):
    """Refuse an SCL grid that is not an exact 2x factor of the band grid.

    Checks the CRS, the origin (exactly equal), the pixel size (exactly 2x) and the
    dimensions (exactly half). Exact equality throughout: these are the same product from the
    same processor and any deviation is a defect, not a rounding difference.
    """
    bt, st = band_profile["transform"], scl_profile["transform"]
    if band_profile["crs"] != scl_profile["crs"]:
        raise GridMismatch(f"{who}: CRS differs, band {band_profile['crs']} vs "
                           f"SCL {scl_profile['crs']}")
    if (bt.c, bt.f) != (st.c, st.f):
        raise GridMismatch(
            f"{who}: origins differ, band ({bt.c!r}, {bt.f!r}) vs SCL ({st.c!r}, {st.f!r}). "
            "WP2A open item 4: comparing CRS and shape alone passes every wrong pairing, "
            "because all five granules share EPSG:32636 and 10980 x 10980.")
    if st.a != bt.a * 2 or st.e != bt.e * 2:
        raise GridMismatch(f"{who}: SCL pixel size {st.a!r} x {-st.e!r} is not exactly twice "
                           f"the band's {bt.a!r} x {-bt.e!r}")
    if (scl_profile["width"] * 2, scl_profile["height"] * 2) != \
            (band_profile["width"], band_profile["height"]):
        raise GridMismatch(
            f"{who}: SCL {scl_profile['width']} x {scl_profile['height']} is not exactly "
            f"half the band's {band_profile['width']} x {band_profile['height']}")
    return True


def clear_mask_20m(scl, clear_classes=CLEAR_CLASSES):
    """Boolean mask at 20 m: True where the SCL class is one of `clear_classes`."""
    scl = np.asarray(scl)
    out = np.zeros(scl.shape, dtype=bool)
    for c in sorted(clear_classes):
        out |= (scl == c)
    return out


def expand_to_10m(mask20):
    """Exact 2 x 2 nearest replication of a 20 m mask onto the 10 m grid.

    Valid only when the grids nest (see `require_nested`), which is why that check exists.
    """
    return np.repeat(np.repeat(np.asarray(mask20), 2, axis=0), 2, axis=1)


def class_census(scl):
    """Counts per SCL class, as a dict. Used to report what a chip actually contains."""
    v, n = np.unique(np.asarray(scl), return_counts=True)
    return {int(a): int(b) for a, b in zip(v, n)}
