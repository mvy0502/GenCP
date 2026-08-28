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


def building_mask(rgb_image):
    """Pixels whose nearest colour is the BUILDING colour, judged independently of class_map.

    `class_map` classifies against the 22-colour upstream HR palette, which has no building
    entry - the rasteriser adds `building` = (165, 42, 42) on top of it. A building pixel is
    therefore assigned to its nearest palette neighbour, which is `red_road`, 104.8 DN away.
    The interface counted class `light_gray` for "buildings", which is neither buildings nor
    what buildings are classified as, so it reported roughly zero over the densest city in
    Europe. That wrong number cost a day.

    This counts buildings by their own colour and touches nothing else. `class_map` is
    deliberately NOT changed: it feeds `conf_D`, and the confidence bands were calibrated
    through exactly this mapping, so altering it would invalidate them. The
    building/road conflation inside the score is recorded as a known limitation instead.
    """
    names, pal = palette_rgb()
    a = np.asarray(rgb_image, dtype=np.float64)[:, :, :3]
    b = np.asarray(_BUILDING_RGB, dtype=np.float64)
    d_pal = ((a[:, :, None, :] - pal[None, None, :, :]) ** 2).sum(axis=-1).min(axis=-1)
    d_bld = ((a - b[None, None, :]) ** 2).sum(axis=-1)
    return d_bld < d_pal


#: The rasteriser's building colour. Duplicated as a literal rather than imported from
#: `rasterize`, which would make this module depend on the render path it is meant to audit.
_BUILDING_RGB = (165, 42, 42)


def osm_class_breakdown(idx, names, rgb_image=None):
    """Pixel counts per OSM-only class, grouped the way a user would read them.

    "4 OSM feature(s) in this tile" is not a number a user can judge. Which four, and of
    what kind, is.

    Pass `rgb_image` to count buildings correctly. Without it the building count is
    reported as None rather than as a wrong number, because a plausible wrong count is
    worse than an absent one.
    """
    groups = {
        "roads": ("red_road", "orange_road", "medium_orange_road", "light_orange_road",
                  "residential_road", "tertiary_road", "unclassified_road", "track",
                  "foot_path"),
        # NOT a class list: buildings are counted from rgb_image below. Left empty so a
        # future edit cannot quietly reintroduce a palette class that is not buildings.
        "buildings": (),
        "water": ("salt_pond", "light_purple"),
        "landuse": ("yellow_farm", "sand", "rock"),
    }
    bmask = None
    if rgb_image is not None:
        bmask = building_mask(rgb_image)
    keep = ~bmask if bmask is not None else np.ones(idx.shape, bool)

    # Road classes are counted OUTSIDE the building mask. A building pixel classifies as
    # red_road, so counting both without excluding one would report every building twice:
    # once as a building and once as a road.
    by_name = {n: int(((idx == i) & keep).sum()) for i, n in enumerate(names)}
    out = {g: int(sum(by_name.get(n, 0) for n in members))
           for g, members in groups.items() if g != "buildings"}
    out["buildings"] = int(bmask.sum()) if bmask is not None else None
    out["total_osm_px"] = int(sum(v for v in out.values() if v is not None))
    return out


# --------------------------------------------------------------------------------------
# Calibration. Every constant below was MEASURED on the 150 held-out European chips and is
# reported in tubitak/docs/confidence-results.md. None of it may be re-fitted to whatever
# the user happens to be generating: a run over one flat tile would z-score itself to the
# middle of the scale and report green.
# --------------------------------------------------------------------------------------

# The score that SHIPS. Registration 2 (confidence-registration-2.md) tested dropping the
# stochastic term as a NON-INFERIORITY question, because the justification was
# simplification rather than correlation, and all three registered conditions passed on the
# 130 Ankara chips - a corpus with zero stem overlap with the European set that raised the
# question. conf_D also turned out to be strictly better there (-0.768 vs -0.645), and the
# confound check is what settles it: with matched-point count held constant, conf_D keeps
# rho -0.287 while the combination collapses to +0.012. The combination's entire Ankara
# association ran through point count; conf_D's did not.
#
# So: no stochastic pass, no second 208 MB model, no explicit-noise ONNX, and no need to
# explain that the image is deterministic while its confidence map is not.
ACTIVE_SCORE = "conf_D"

CALIBRATION = {
    "score": ACTIVE_SCORE,
    "definition": "z(input density), z-scored against the European held-out corpus",
    "decision_corpus": ("130 Ankara Overpass chips, sitevar=ank_overpass in "
                        "tubitak/docs/evidence/regD/regD_per_chip.csv - chose the score"),
    "calibration_corpus": ("150 held-out EU chips, sitevar=eu in the same file - set the "
                           "band boundaries"),
    "arm": "C2",
    "error_column": "med_mean32 (KARIOS median radial residual, px)",
    # The model the bands were calibrated against, by CONTENT. A file name can be changed;
    # this cannot, so a renamed or substituted model cannot pass itself off as the one the
    # bands were measured on.
    "calibrated_model_file": "gencp_C2_fp32.onnx",
    "calibrated_model_sha256":
        "d3b75c364e46141eea6bbc3b2e5763dff46bff002d2afea93cd378e500fbec6b",
    "spearman_rho_eu": -0.7553,
    "spearman_rho_ankara": -0.7684,
    "partial_rho_given_point_count_eu": -0.3810,
    "partial_rho_given_point_count_ankara": -0.2870,
    "registration": "tubitak/docs/confidence-registration.md",
    "registration_2": "tubitak/docs/confidence-registration-2.md",
    "results": "tubitak/docs/confidence-results.md",
    # z-score statistics, from the EUROPEAN corpus. Never re-fitted to a user's run: a run
    # over one flat tile would z-score itself to the middle of the scale and report green.
    "conf_D_mean": 0.716106, "conf_D_std": 0.514109,
    # band boundaries on z(conf_D), derived on the European corpus by the registered rule
    "red_hi": -0.982375, "green_lo": -0.245312,
    "band_median_px": {"red": 3.3093, "amber": 2.6310, "green": 1.3310},
    "band_n": {"red": 19, "amber": 55, "green": 76},
    "corpus_median_px": 1.9802,
}

# Superseded by registration 2, kept because confidence-results.md reports its numbers and
# tubitak/scripts/confidence_validate.py still reproduces both registrations.
CALIBRATION_COMB_SUPERSEDED = {
    "score": "conf_COMB", "conf_S_mean": -1.807605, "conf_S_std": 0.805370,
    "red_hi": -0.728778, "green_lo": -0.104970,
    "spearman_rho_eu": -0.7466, "spearman_rho_ankara": -0.6449,
    "partial_rho_given_point_count_ankara": 0.0120,
}


# The model whose weights the bands were calibrated on, by name, used only as a fallback
# when the file cannot be hashed. model_is_validated() checks the SHA-256.
VALIDATED_MODEL_STEMS = ("gencp_C2_fp32",)

BAND_RED, BAND_AMBER, BAND_GREEN = 1, 2, 3
BAND_NAMES = {BAND_RED: "red", BAND_AMBER: "amber", BAND_GREEN: "green"}
# The bands are NAMED red/amber/green, so they are DRAWN red/amber/green. A first pass used
# a blue for the green band on colour-blind grounds and produced a legend that read
# "Yesil - kullanilabilir" beside a blue swatch, which is worse: the reader now has to
# remember a mapping. Red-green confusion is mitigated the other way instead - the three
# differ markedly in LIGHTNESS (relative luminance 0.13 / 0.48 / 0.22), so they stay
# distinguishable in greyscale, and every place the bands are reported in words carries the
# operational meaning next to the colour name.
BAND_COLOURS = {BAND_RED: (202, 0, 32), BAND_AMBER: (244, 165, 130),
                BAND_GREEN: (26, 150, 65)}


def needs_stochastic():
    """Does the shipping score require a dropout-enabled model? Since registration 2, no."""
    return ACTIVE_SCORE != "conf_D"


def model_sha256(path):
    import hashlib
    h = hashlib.sha256()
    with open(str(path), "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def deployed_score(conf_D_field, conf_S_field=None):
    """The score the plugin actually draws bands from. See ACTIVE_SCORE."""
    if ACTIVE_SCORE == "conf_D":
        c = CALIBRATION
        return (np.asarray(conf_D_field, dtype=np.float64)
                - c["conf_D_mean"]) / c["conf_D_std"]
    if conf_S_field is None:
        raise ValueError(f"score {ACTIVE_SCORE} needs a stochastic spread field")
    return combined_score(conf_D_field, conf_S_field)


def align_to(field, shape):
    """Resample a smooth per-pixel field onto another grid, bilinearly.

    conf_D is computed on the 257 px RENDER, because class assignment has to see the
    palette colours before `infer.preprocess` resizes them to 256 with BICUBIC and blends
    them into things that are no longer palette entries. The mosaic works on the model's
    256 px output grid. It is the entropy field that moves, because it is smooth over a
    33 px window and resampling it costs nothing.

    Measured: this shifts the chip mean the validation used by at most 6.6e-06 bits,
    against a corpus standard deviation of 0.514.
    """
    from scipy.ndimage import zoom
    a = np.asarray(field, dtype=np.float64)
    if a.shape == tuple(shape):
        return a
    return zoom(a, (shape[0] / a.shape[0], shape[1] / a.shape[1]), order=1)


def combined_score(conf_D, conf_S):
    """The registered score: mean of the two z-scores, using held-out corpus statistics."""
    c = dict(CALIBRATION)
    c.update(CALIBRATION_COMB_SUPERSEDED)
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


ALPHA_RANGE = 4.0


def score_to_alpha(score, valid=None):
    """Continuous confidence as a uint8 alpha band. 255 = most confident.

    Deliberately NOT the three-band rounding. A downstream matcher may want finer
    discrimination than red/amber/green, and throwing that away at the file boundary would
    be a decision made on its behalf. The mapping is linear and stated in the output's
    provenance so it can be inverted: z = alpha / 255 * 8 - 4.

    Where the mosaic has no data the alpha is 0, which is what an alpha band means.
    """
    z = np.clip(np.asarray(score, dtype=np.float64), -ALPHA_RANGE, ALPHA_RANGE)
    a = ((z + ALPHA_RANGE) / (2 * ALPHA_RANGE) * 255.0).round().astype(np.uint8)
    if valid is not None:
        a = np.where(np.asarray(valid, dtype=bool), a, 0).astype(np.uint8)
    return a


def alpha_to_score(alpha):
    """Inverse of score_to_alpha, for anyone reading the delivered file."""
    return np.asarray(alpha, dtype=np.float64) / 255.0 * (2 * ALPHA_RANGE) - ALPHA_RANGE


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
    """True when the chosen weights ARE the ones the bands were calibrated on.

    Checked by SHA-256, not by file name. Names are trivially changed and a renamed C3
    would otherwise be handed C2's bands - the exact confusion the bands' scope exists to
    prevent. Falls back to the name only if the file cannot be read.
    """
    from pathlib import Path as _P
    try:
        return model_sha256(model_path) == CALIBRATION["calibrated_model_sha256"]
    except OSError:
        return _P(str(model_path)).stem in VALIDATED_MODEL_STEMS


def stochastic_model_for(model_path):
    """The matching noise-input export for a deterministic model, if it sits beside it."""
    from pathlib import Path as _P
    p = _P(str(model_path))
    cand = p.with_name(p.stem.replace("_fp32", "_stochastic_fp32") + p.suffix)
    return cand if cand.is_file() else None
