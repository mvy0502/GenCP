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


# The palette is 20 hex literals plus "black" and "white". Parsing those directly avoids
# importing matplotlib, which is NOT a documented QGIS dependency and which segfaulted the
# QGIS process when first touched from a QgsTask worker thread - a crash that only appeared
# once the confidence pass moved off the main thread, because nothing else in gencp_core
# imported it. A four-line parser has no such failure mode.
_NAMED = {"black": (0.0, 0.0, 0.0), "white": (1.0, 1.0, 1.0)}


def _to_rgb(spec):
    """'#rrggbb' or one of two colour names -> (r, g, b) floats in [0, 1]."""
    t = str(spec).strip().lower()
    if t in _NAMED:
        return _NAMED[t]
    if t.startswith("#"):
        h = t[1:]
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        if len(h) == 6:
            return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    raise ValueError(f"unrecognised palette colour {spec!r}")


def palette_rgb():
    """The 22 GenCP palette colours as (names, Nx3 float array), name order sorted.

    Sorted so the class index is stable across runs and machines - an unsorted dict order
    would silently renumber the classes and make two runs incomparable.
    """
    from . import palette as _palette
    cd = _palette.load().color_dict
    names = sorted(cd)
    rgb = np.array([_to_rgb(cd[n]) for n in names], dtype=np.float64) * 255.0
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


# --------------------------------------------------------------------------------------
# Calibration. Every constant below was MEASURED on the 150 held-out European chips and is
# reported in tubitak/docs/confidence-results.md. None of it may be re-fitted to whatever
# the user happens to be generating: a run over one flat tile would z-score itself to the
# middle of the scale and report green.
# --------------------------------------------------------------------------------------

CALIBRATION = {
    "corpus": "150 held-out EU chips, sitevar=eu in tubitak/docs/evidence/regD/regD_per_chip.csv",
    "arm": "C2",
    "error_column": "med_mean32 (KARIOS median radial residual, px)",
    "spread_path": "gencp_C2_stochastic_fp32.onnx, 16 draws, seed 0",
    "spearman_rho": -0.7466,
    "spearman_ci": [-0.8226, -0.6473],
    "partial_rho_given_point_count": -0.3810,
    "registration": "tubitak/docs/confidence-registration.md",
    "results": "tubitak/docs/confidence-results.md",
    # z-score statistics, taken over the held-out corpus
    "conf_D_mean": 0.716106, "conf_D_std": 0.514109,
    "conf_S_mean": -1.807605, "conf_S_std": 0.805370,
    # band boundaries on the combined score
    "red_hi": -0.728778, "green_lo": -0.104970,
    "band_median_px": {"red": 3.133, "amber": 2.7054, "green": 1.3804},
    "band_n": {"red": 23, "amber": 43, "green": 84},
    "corpus_median_px": 1.9802,
}

# The one model this score is calibrated for. C3 has no held-out EU KARIOS errors, so the
# bands have no meaning there and the plugin must not pretend otherwise.
VALIDATED_MODEL_STEMS = ("gencp_C2_fp32", "gencp_C2_stochastic_fp32")

BAND_RED, BAND_AMBER, BAND_GREEN = 1, 2, 3
BAND_NAMES = {BAND_RED: "red", BAND_AMBER: "amber", BAND_GREEN: "green"}
# The bands are NAMED red/amber/green, so they are DRAWN red/amber/green. A first pass used
# a blue for the green band on colour-blind grounds and produced a legend that read
# "Yeşil - kullanılabilir" beside a blue swatch, which is worse: the reader now has to
# remember a mapping. Red-green confusion is mitigated the other way instead - the three
# differ markedly in LIGHTNESS (relative luminance 0.13 / 0.48 / 0.22), so they stay
# distinguishable in greyscale, and every place the bands are reported in words carries the
# operational meaning next to the colour name.
BAND_COLOURS = {BAND_RED: (202, 0, 32), BAND_AMBER: (244, 165, 130), BAND_GREEN: (26, 150, 65)}


def align_to(field, shape):
    """Resample a smooth per-pixel field onto another grid, bilinearly.

    conf_D is computed on the 257 px RENDER, because class assignment has to see the
    palette colours before `infer.preprocess` resizes them to 256 with BICUBIC and blends
    them into things that are no longer palette entries. conf_S necessarily lives on the
    model's 256 px output grid. The two have to meet somewhere, and it is the entropy field
    that moves, because it is smooth over a 33 px window and resampling it costs nothing.

    Validation aggregated both to chip means, where this never arose; the per-pixel map is
    what forced the question. Re-running the validation with the alignment applied leaves
    rho unchanged to four decimals.
    """
    from scipy.ndimage import zoom
    a = np.asarray(field, dtype=np.float64)
    if a.shape == tuple(shape):
        return a
    return zoom(a, (shape[0] / a.shape[0], shape[1] / a.shape[1]), order=1)


def combined_score(conf_D, conf_S):
    """The registered score: mean of the two z-scores, using held-out corpus statistics."""
    c = CALIBRATION
    conf_D = np.asarray(conf_D, dtype=np.float64)
    conf_S = np.asarray(conf_S, dtype=np.float64)
    if conf_D.shape != conf_S.shape:
        conf_D = align_to(conf_D, conf_S.shape)
    zd = (conf_D - c["conf_D_mean"]) / c["conf_D_std"]
    zs = (np.asarray(conf_S, dtype=np.float64) - c["conf_S_mean"]) / c["conf_S_std"]
    return (zd + zs) / 2.0


def band_map(score):
    """Score -> band index. Boundaries from the held-out error distribution, not by eye.

    Applied per pixel here. The boundaries were DERIVED and VALIDATED at chip level (a
    chip-mean score against a chip-median error), so a per-pixel band is the same quantity
    at finer granularity and not a separately calibrated per-pixel probability. Anywhere
    this is shown to a user, the run-level verdict is the number with evidence behind it.
    """
    s = np.asarray(score, dtype=np.float64)
    out = np.full(s.shape, BAND_AMBER, dtype=np.uint8)
    out[s <= CALIBRATION["red_hi"]] = BAND_RED
    out[s >= CALIBRATION["green_lo"]] = BAND_GREEN
    return out


def run_verdict(score, red_warn_fraction=0.20):
    """What percentage of the output falls in each band, plus the run-level band.

    `mean_band` comes from the MEAN score over the run, which is the chip-level quantity
    the validation actually tested. `fractions` come from the per-pixel map.
    """
    s = np.asarray(score, dtype=np.float64)
    b = band_map(s)
    n = b.size
    fr = {BAND_NAMES[k]: float((b == k).sum()) / n for k in (BAND_RED, BAND_AMBER, BAND_GREEN)}
    mean_score = float(s.mean())
    return {
        "fractions": fr,
        "mean_score": mean_score,
        "mean_band": BAND_NAMES[int(band_map(np.array([mean_score]))[0])],
        "red_exceeds_threshold": fr["red"] > red_warn_fraction,
        "red_warn_fraction": red_warn_fraction,
        "expected_median_px": CALIBRATION["band_median_px"],
    }


def model_is_validated(model_path):
    """True when the chosen weights are the ones the bands were calibrated on."""
    from pathlib import Path as _P
    return _P(str(model_path)).stem in VALIDATED_MODEL_STEMS


def stochastic_model_for(model_path):
    """The matching noise-input export for a deterministic model, if it sits beside it."""
    from pathlib import Path as _P
    p = _P(str(model_path))
    cand = p.with_name(p.stem.replace("_fp32", "_stochastic_fp32") + p.suffix)
    return cand if cand.is_file() else None
