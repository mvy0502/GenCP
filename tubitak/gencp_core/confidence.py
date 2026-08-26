"""Per-pixel confidence signals, computed from the rasterised input alone.

The question these answer, per pixel: **how much does the output here rest on input
information, and how much is invention?**

Registered in `tubitak/docs/confidence-registration.md` before anything was measured. The
window size, the class sets and the aggregation rule are all fixed there; changing one
here without a new registration invalidates the numbers that document reports.

**Sign convention, used throughout and never flipped: higher confidence = better = lower
expected matching error.** Every function that returns a confidence orients itself to that
convention where it is defined.

No torch. The stochastic-spread signal needs a dropout-enabled generator and therefore
lives in `export.py`, which is the one module in gencp_core allowed to import torch and is
never imported by the plugin.
"""
from __future__ import annotations

import numpy as np

# The registered window: 33 px at 10 m GSD = 330 m. Odd, so it is centred on its pixel.
WINDOW = 33

# `black` is the render's nodata/void colour and is included in CLC_MAP, so it counts as
# base rather than as OSM evidence.
CLC_BASE_NAMES = frozenset(
    {"black", "forest_green", "gray", "light_green", "no_vegetation", "snow", "water"})


def palette_rgb():
    """The 22 GenCP palette colours as (names, Nx3 float array), name order sorted.

    Sorted so the class index is stable across runs and machines - an unsorted dict order
    would silently renumber the classes and make two runs incomparable.
    """
    import matplotlib.colors as mcolors
    from . import palette as _palette
    cd = _palette.load().color_dict
    names = sorted(cd)
    rgb = np.array([mcolors.to_rgb(cd[n]) for n in names], dtype=np.float64) * 255.0
    return names, rgb


def class_map(rgb_image):
    """Assign every pixel to its nearest palette colour. Returns (index HxW, names).

    The renders are supersampled, so a minority of pixels are blends of two palette
    entries and have no exact match. Nearest-in-RGB is used rather than an exact lookup;
    the median nearest-palette distance measured over held-out chips is 0.0 DN, so this is
    near-exact for the bulk of a chip and only approximate on anti-aliased edges.
    """
    names, pal = palette_rgb()
    a = np.asarray(rgb_image, dtype=np.float64)
    if a.ndim != 3 or a.shape[2] < 3:
        raise ValueError(f"expected an HxWx3 RGB image, got shape {a.shape}")
    a = a[:, :, :3]
    # (H, W, 1, 3) - (1, 1, N, 3) -> squared distance to each palette entry
    d2 = ((a[:, :, None, :] - pal[None, None, :, :]) ** 2).sum(axis=-1)
    return d2.argmin(axis=-1).astype(np.int16), names


def osm_mask(idx, names):
    """True where a pixel's class can ONLY have come from an OSM vector, not the CLC+ base.

    Deliberately conservative. `gray`, `water`, `forest_green` and `light_green` are
    reachable from either source, so they are excluded even though many of them really are
    OSM features. Undercounting evidence can only weaken a confidence signal built on it;
    overcounting would inflate one.
    """
    osm_ids = [i for i, n in enumerate(names) if n not in CLC_BASE_NAMES]
    return np.isin(idx, osm_ids)


def input_density(idx, n_classes=None, window=WINDOW):
    """Shannon entropy in bits of the palette-class histogram in a window, per pixel.

    Zero where the window is one flat class - the input says nothing there, so whatever
    texture the model produces is invention. Rises wherever classes meet: a road, a field
    boundary, a shoreline.

    Oriented already: higher = more input information = higher confidence.
    """
    from scipy.ndimage import uniform_filter
    idx = np.asarray(idx)
    n = int(n_classes if n_classes is not None else idx.max() + 1)
    h, w = idx.shape
    ent = np.zeros((h, w), dtype=np.float64)
    for c in range(n):
        p = uniform_filter((idx == c).astype(np.float64), size=window, mode="reflect")
        # 0 log 0 = 0; clip only the log's argument so p itself stays exact
        np.subtract(ent, p * np.log2(np.clip(p, 1e-12, None)), out=ent)
    return ent


def distance_to_osm(mask):
    """Euclidean distance in pixels to the nearest OSM-drawn pixel.

    A chip with no OSM pixel at all gets the chip diagonal everywhere, so it is the worst
    value the transform could otherwise have produced rather than an infinity that would
    poison a mean.
    """
    from scipy.ndimage import distance_transform_edt
    mask = np.asarray(mask, dtype=bool)
    h, w = mask.shape
    if not mask.any():
        return np.full((h, w), float(np.hypot(h, w)))
    return distance_transform_edt(~mask).astype(np.float64)


def signals(rgb_image, window=WINDOW):
    """The two no-model signals for one chip, both already oriented as confidences.

    Returns {'conf_D': HxW, 'conf_B': HxW, 'idx': HxW, 'osm_fraction': float}.
    `conf_S` (stochastic spread) is not here: it needs a dropout-enabled generator.
    """
    idx, names = class_map(rgb_image)
    m = osm_mask(idx, names)
    return {
        "conf_D": input_density(idx, n_classes=len(names), window=window),
        "conf_B": -distance_to_osm(m),
        "idx": idx,
        "names": names,
        "osm_fraction": float(m.mean()),
    }


def osm_class_breakdown(idx, names):
    """Pixel counts per OSM-only class, grouped the way a user would read them.

    "4 OSM feature(s) in this tile" is not a number a user can judge. Which four, and of
    what kind, is.
    """
    groups = {
        "roads": ("red_road", "orange_road", "medium_orange_road", "light_orange_road",
                  "residential_road", "tertiary_road", "unclassified_road", "track",
                  "foot_path"),
        "buildings": ("light_gray",),
        "water": ("salt_pond", "light_purple"),
        "landuse": ("yellow_farm", "sand", "rock"),
    }
    by_name = {n: int((idx == i).sum()) for i, n in enumerate(names)}
    out = {g: int(sum(by_name.get(n, 0) for n in members)) for g, members in groups.items()}
    out["total_osm_px"] = int(sum(out.values()))
    return out
