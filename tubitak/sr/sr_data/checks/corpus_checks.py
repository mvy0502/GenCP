#!/usr/bin/env python
"""The four checks registered in `03a-corpus-registration.md` §12, each with a known-false.

    C1  target is exactly SCALE x the input in both dimensions
    C2  no chip contains an SCL class declared not clear
    C3  no chip is in more than one split, and none lies within the buffer of another
        split OF THE SAME GRANULE
    C4  the degraded input is NOT a plain area-average downsample, and the kernel actually
        built has the registered modulation at the output Nyquist frequency

Every check is run twice: once on the real corpus, where it must pass, and once on a
deliberately broken input, where it must fail. A check that passes on both is not a check —
an audit of this project's 23 verifiers found 18 that reported success when given nothing to
check.

WP15 rewrote the known-false arms. Four of them did not exercise the check at all:

    C1  re-evaluated the geometry predicate inline instead of calling it, so a defect in
        the predicate would have been present in both arms and cancelled out.
    C2  built a small array in memory and called `np.isin` on it directly. It never touched
        the manifest, the SCL raster or the footprint arithmetic, which is where the risk is.
    C4  compared `area_average(t)` with `area_average(t)`. Unconditionally true. Nothing
        ever substituted an area average for the real degradation.
    C4's MTF arm composed `sigma_for_mtf` with `mtf_at`, two closed forms of the same
        Gaussian, so it returned the target by construction and could not have failed. The
        kernel actually applied is truncated at 4 sigma and renormalised, and its discrete
        response was never computed here.

So every predicate below is now a single function that BOTH arms call, and the known-false
arms feed it real inputs that violate the property.

C2 and C3 re-read the SOURCE rather than trusting the builder's own bookkeeping: C2 opens
each granule's SCL again and looks at the chip footprints the manifest names, so an error in
the screening logic cannot hide behind the same error in the check.
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
SR = HERE.parents[2]
ROOT = HERE.parents[4]
sys.path.insert(0, str(SR))
sys.path.insert(0, str(ROOT / "tubitak" / "tests"))
from _guard import strict_argv                                          # noqa: E402

strict_argv(known=("--corpus=", "--json="), positional=0,
            usage="corpus_checks.py [--corpus=DIR] [--json=OUT]")

import numpy as np                                                      # noqa: E402
import rasterio                                                         # noqa: E402

from sr_data import params as P                                         # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "sr_train"))
import config as C                                                      # noqa: E402
from sr_data import splits as S                                         # noqa: E402
from sr_data.clear import clear_mask_20m                                # noqa: E402
from sr_data.degrade import (area_average, degrade, degrade_chip,       # noqa: E402
                             gaussian_decimation_kernel)

CORPUS = ROOT / "tubitak" / "data" / P.CORPUS_SUBDIR
DATA = ROOT / "tubitak" / "data" / P.DATA_SUBDIR
RESULTS = []

#: How far the discrete kernel may sit from the registered MTF target before C4 rejects it.
#:
#: The kernel is a Gaussian truncated at KERNEL_RADIUS_SIGMAS (4.0) sigma and renormalised,
#: so its discrete modulation cannot equal the closed form exactly. WP3A measured the gap at
#: scale 2 as 0.299970210 against 0.300000000 — 3.0e-5, of the same order as the Gaussian
#: mass falling outside the window (2.5e-5). WP15 measured scale 4 at 0.299975794, gap
#: 2.4e-5, outside-mass 4.3e-5.
#:
#: 1e-4 is chosen to sit above both truncation gaps with room to spare and far below any
#: error that would matter: a sigma derived for a target of 0.4 instead of 0.3 lands about
#: 0.1 away, three orders of magnitude outside this tolerance. The tolerance accommodates
#: the truncation deliberately. It is NOT a tuned number — widening the kernel would close
#: the gap and would also change the corpus, so the truncation stays and is reported.
MTF_TOL = 1e-4


def record(cid, name, kind, ok, detail):
    RESULTS.append(dict(check=cid, name=name, case=kind, ok=bool(ok), detail=detail))
    tag = "PASS" if ok else "FAIL"
    print(f"    [{tag}] {kind:12s} {detail}")
    return ok


# ------------------------------------------------------------------------------- C1
def c1_geometry_ok(lo, hi, scale, n_bands):
    """THE C1 predicate. Both arms call this; neither re-implements it."""
    return bool(hi.shape[-2] == lo.shape[-2] * scale
                and hi.shape[-1] == lo.shape[-1] * scale
                and lo.shape[0] == hi.shape[0] == n_bands)


def _wrong_factor_degrade(target_dn, norm_divisor, scale=P.SCALE):
    """A degradation that decimates by scale+1. Substituted for the real one by C1's
    known-false, so the check runs on a genuinely mis-shaped pair rather than on a
    hand-built array. scale+1 rather than a literal 3, which would be a correct rejection
    at s=2 and s=4 and blind at s=3 — how D27's known-false decayed."""
    w = scale + 1
    t = np.asarray(target_dn, np.float32) / np.float32(norm_divisor)
    h = (t.shape[-2] // w) * w
    ww = (t.shape[-1] // w) * w
    return degrade(t[..., :h, :ww], scale=w).astype(np.float32), t


def c1(corpus):
    print(f"  C1  target is exactly {C.SCALE}x the input in both dimensions")
    arr = np.load(corpus / "chips_test.npy", mmap_mode="r")
    if arr.shape[0] == 0:
        return record("C1", "geometry", "known-true", False,
                      "chips_test.npy holds zero chips - nothing to check")

    lo, hi = degrade_chip(np.asarray(arr[0]), C.NORM_DIVISOR_DN, scale=C.SCALE)
    ok_t = record("C1", "geometry", "known-true",
                  c1_geometry_ok(lo, hi, C.SCALE, C.N_BANDS),
                  f"input {lo.shape} -> target {hi.shape}; ratio "
                  f"{hi.shape[-1] / lo.shape[-1]:.0f} in both axes")

    # known-false: run the REAL check over a pair produced by a degradation at the wrong
    # factor. Previously this arm rebuilt the predicate inline and so tested nothing.
    lo_b, hi_b = _wrong_factor_degrade(np.asarray(arr[0]), C.NORM_DIVISOR_DN, scale=C.SCALE)
    bad = c1_geometry_ok(lo_b, hi_b, C.SCALE, C.N_BANDS)
    ok_f = record("C1", "geometry", "known-false", not bad,
                  f"degradation replaced by one decimating {C.SCALE + 1}x -> input "
                  f"{lo_b.shape} against target {hi_b.shape}; "
                  f"{'correctly rejected' if not bad else 'ACCEPTED - CHECK IS BLIND'}")
    return ok_t and ok_f


# ------------------------------------------------------------------------------- C2
def c2_scan(rows, scl_by_tile, n_scl, stride_half, clear_classes):
    """THE C2 scan. Re-reads the SCL under every chip footprint the manifest names.

    Returns (checked, census, bad_chips, off_raster).

    `off_raster` is why this function exists in this shape. A slice past the array bound
    yields an EMPTY array, and `np.isin(empty, ...).all()` is True, so a chip whose
    footprint runs off the raster used to pass vacuously — the check reported clear for a
    window it never read. The window's shape is now asserted before its contents are
    tested, and a wrong shape is a violation rather than a silent skip.
    """
    bad_chips, off_raster, census, checked = [], [], {}, 0
    for tile, scl in scl_by_tile.items():
        for r in rows:
            if r["granule"] != tile:
                continue
            r0 = int(r["chip_row"]) * stride_half
            c0 = int(r["chip_col"]) * stride_half
            sub = scl[r0:r0 + n_scl, c0:c0 + n_scl]
            if sub.shape != (n_scl, n_scl):
                off_raster.append((tile, r["chip_row"], r["chip_col"], tuple(sub.shape)))
                continue
            v, n = np.unique(sub, return_counts=True)
            for a, b in zip(v, n):
                census[int(a)] = census.get(int(a), 0) + int(b)
            checked += 1
            if not np.isin(sub, list(clear_classes)).all():
                bad_chips.append((tile, r["chip_row"], r["chip_col"],
                                  sorted(set(v.tolist()) - set(clear_classes))))
    return checked, census, bad_chips, off_raster


def c2(corpus):
    print("  C2  no chip contains an SCL class declared not clear")
    rows = list(csv.DictReader(open(corpus / "manifest.csv")))
    n_scl = P.CHIP_PX // 2
    stride_half = P.CHIP_STRIDE_PX // 2
    scl_by_tile = {}
    for tile, meta in P.GRANULES.items():
        with rasterio.open(DATA / meta["dirname"] / "SCL.tif") as s:
            scl_by_tile[tile] = s.read(1)

    checked, census, bad_chips, off = c2_scan(rows, scl_by_tile, n_scl, stride_half,
                                              P.CLEAR_CLASSES)
    ok_t = record("C2", "clear", "known-true", checked > 0 and not bad_chips and not off,
                  f"{checked} chips re-read from source SCL; classes present "
                  f"{sorted(census)} (declared clear {sorted(P.CLEAR_CLASSES)}); "
                  f"{len(bad_chips)} class violations, {len(off)} off-raster footprints")

    # known-false A: plant a class-9 (cloud, high probability) pixel inside a REAL chip
    # footprint of a REAL granule, then run the REAL scan. Previously this arm called
    # np.isin on a hand-built array and never touched a manifest, a raster or the
    # footprint arithmetic.
    victim = rows[0]
    forged_scl = {t: a.copy() for t, a in scl_by_tile.items()}
    fr = int(victim["chip_row"]) * stride_half
    fc = int(victim["chip_col"]) * stride_half
    forged_scl[victim["granule"]][fr + 7, fc + 11] = 9
    _, _, bad_f, _ = c2_scan(rows, forged_scl, n_scl, stride_half, P.CLEAR_CLASSES)
    caught = any(b[0] == victim["granule"] and b[1] == victim["chip_row"]
                 and b[2] == victim["chip_col"] for b in bad_f)
    ok_f = record("C2", "clear", "known-false", caught,
                  f"class-9 pixel planted in the source SCL under real chip "
                  f"{victim['granule']} ({victim['chip_row']},{victim['chip_col']}) -> "
                  f"{len(bad_f)} violations reported; "
                  f"{'correctly rejected' if caught else 'ACCEPTED - CHECK IS BLIND'}")

    # known-false B: a chip whose footprint runs off the raster. Before WP15 this passed:
    # the slice returned an empty array and np.isin(empty, ...).all() is True.
    tile0 = rows[0]["granule"]
    far = scl_by_tile[tile0].shape[0] // stride_half + 5
    ghost = dict(rows[0]); ghost["chip_row"] = str(far); ghost["chip_col"] = str(far)
    _, _, _, off_g = c2_scan([ghost], scl_by_tile, n_scl, stride_half, P.CLEAR_CLASSES)
    legacy = bool(np.isin(scl_by_tile[tile0][far * stride_half:far * stride_half + n_scl,
                                             far * stride_half:far * stride_half + n_scl],
                          list(P.CLEAR_CLASSES)).all())
    ok_g = record("C2", "clear", "known-false-2", len(off_g) == 1,
                  f"chip planted at ({far},{far}), past the {scl_by_tile[tile0].shape} "
                  f"raster -> window {off_g[0][3] if off_g else 'n/a'}, "
                  f"{len(off_g)} off-raster reported "
                  f"(the pre-WP15 predicate returned clear={legacy} for this window); "
                  f"{'correctly rejected' if off_g else 'ACCEPTED - CHECK IS BLIND'}")
    return ok_t and ok_f and ok_g


# ------------------------------------------------------------------------------- C3
def c3(corpus):
    print("  C3  no chip in two splits, and none within the buffer of another split "
          "OF THE SAME GRANULE")
    rows = list(csv.DictReader(open(corpus / "manifest.csv")))
    recs = [dict(granule=r["granule"], chip_row=int(r["chip_row"]),
                 chip_col=int(r["chip_col"]), split=r["split"]) for r in rows]
    keys = [(r["granule"], r["chip_row"], r["chip_col"]) for r in recs]
    dup = len(keys) - len(set(keys))
    viol = S.buffer_violations(recs)
    ok_t = record("C3", "splits", "known-true", len(recs) > 0 and dup == 0 and not viol,
                  f"{len(recs)} chips, {dup} appearing in more than one split, "
                  f"{len(viol)} within {P.SPLIT_BUFFER_M:.0f} m of a different split of "
                  f"the same granule (cross-granule proximity is NOT asserted here - "
                  f"see D18, tubitak/sr/sr_train/leakage.py)")
    # known-false: relabel one interior chip so it neighbours a different split. This arm
    # already called the real S.buffer_violations and was left as it stood.
    forged = [dict(r) for r in recs]
    target = None
    for i, r in enumerate(forged):
        if r["split"] == "train":
            target = i
            break
    forged[target]["split"] = "test"
    v2 = S.buffer_violations(forged)
    ok_f = record("C3", "splits", "known-false", len(v2) > 0,
                  f"one train chip relabelled 'test' at "
                  f"{forged[target]['granule']} ({forged[target]['chip_row']},"
                  f"{forged[target]['chip_col']}) -> {len(v2)} buffer violations "
                  f"{'correctly detected' if v2 else 'MISSED - CHECK IS BLIND'}")
    return ok_t and ok_f


# ------------------------------------------------------------------------------- C4
def c4_worst_difference(arr, n, divisor, scale, degrade_fn):
    """THE C4 measurement: the largest gap between `degrade_fn` and a plain area average.

    `degrade_fn` is a parameter precisely so the known-false can substitute the area
    average itself and watch the check report failure.
    """
    worst = 0.0
    for i in range(n):
        t = np.asarray(arr[i], np.float32) / np.float32(divisor)
        worst = max(worst, float(np.abs(degrade_fn(t, scale=scale)
                                        - area_average(t, scale=scale)).max()))
    return worst


def c4_differs(worst):
    """THE C4 predicate."""
    return bool(worst > 1e-6)


def discrete_mtf_at_nyquist(scale, sigma=None):
    """Modulation of the kernel AS BUILT at the output grid's Nyquist frequency.

    Not the closed form. `gaussian_decimation_kernel` truncates the Gaussian at
    KERNEL_RADIUS_SIGMAS sigma and renormalises the surviving taps, so its response is a
    finite sum, not exp(-2 pi^2 sigma^2 f^2). This evaluates the DTFT of the actual taps

        H(f) = sum_o w_o exp(-2 pi i f (o - centre))

    at f = 1/(2*scale) cycles per source pixel, measured about the block centre. Returns
    (|H|, Im(H), n_taps). Im(H) is returned because a kernel that is not symmetric about
    the block centre shifts the image, and that is not hypothetical: the scale-4 window was
    asymmetric until WP7 and baked a -0.0011 px shift into every degraded input.
    """
    off, w = gaussian_decimation_kernel(sigma=sigma, scale=scale)
    d = off - (scale - 1) / 2.0
    f = 1.0 / (2 * scale)
    h = np.sum(w * np.exp(-2j * np.pi * f * d))
    return float(abs(h)), float(h.imag), int(len(off))


def c4(corpus):
    print(f"  C4  the degraded input is NOT a plain {C.SCALE}x{C.SCALE} area-average "
          f"downsample")
    arr = np.load(corpus / "chips_test.npy", mmap_mode="r")
    n = min(64, arr.shape[0])
    if n == 0:
        return record("C4", "mtf", "known-true", False,
                      "chips_test.npy holds zero chips - nothing to check")

    worst = c4_worst_difference(arr, n, C.NORM_DIVISOR_DN, C.SCALE, degrade)
    ok_t = record("C4", "mtf", "known-true", c4_differs(worst),
                  f"over {n} chips, max |MTF-degraded - area-average| = {worst:.8f} "
                  f"normalised ({worst * C.NORM_DIVISOR_DN:.4f} DN); "
                  f"{'the filter does something' if c4_differs(worst) else 'FILTER IS A NO-OP'}")

    # known-false: substitute the area average FOR the degradation and require the check to
    # report failure. Previously this arm compared area_average(t) with area_average(t),
    # which is unconditionally true and never substituted anything.
    worst_f = c4_worst_difference(arr, n, C.NORM_DIVISOR_DN, C.SCALE, area_average)
    caught = not c4_differs(worst_f)
    ok_f = record("C4", "mtf", "known-false", caught,
                  f"degradation replaced by the {C.SCALE}x{C.SCALE} mean, run through the "
                  f"same measurement -> max difference {worst_f:.8f}; "
                  f"{'correctly identified as a no-op' if caught else 'NOT DETECTED'}")

    # the MTF of the kernel ACTUALLY BUILT, not the closed form it was derived from
    mag, imag, taps = discrete_mtf_at_nyquist(C.SCALE)
    within = abs(mag - P.MTF_AT_NYQUIST) < MTF_TOL and abs(imag) < 1e-12
    ok_m = record("C4", "mtf", "value", within,
                  f"discrete MTF of the {taps}-tap kernel as built, at the "
                  f"{10 * C.SCALE:.0f} m Nyquist frequency = {mag:.9f} "
                  f"(registered {P.MTF_AT_NYQUIST}, deviation {mag - P.MTF_AT_NYQUIST:+.2e}, "
                  f"tolerance {MTF_TOL:.0e} for 4-sigma truncation); "
                  f"Im(H) = {imag:+.1e} (a kernel off the block centre would shift)")

    # known-false for the MTF arm: a kernel derived for a DIFFERENT target must be rejected.
    wrong_sigma = P.sigma_for_mtf(0.4, C.SCALE)
    mag_w, _, _ = discrete_mtf_at_nyquist(C.SCALE, sigma=wrong_sigma)
    rejected = abs(mag_w - P.MTF_AT_NYQUIST) >= MTF_TOL
    ok_mf = record("C4", "mtf", "value-false", rejected,
                   f"kernel rebuilt from a sigma derived for MTF 0.4 -> discrete "
                   f"{mag_w:.9f}, {abs(mag_w - P.MTF_AT_NYQUIST):.3f} from the registered "
                   f"target; {'correctly rejected' if rejected else 'ACCEPTED - ARM IS BLIND'}")
    return ok_t and ok_f and ok_m and ok_mf


def main():
    t0 = time.perf_counter()
    corpus, out_json, asked = CORPUS, None, False
    for a in sys.argv[1:]:
        if a.startswith("--corpus="):
            corpus, asked = Path(a.split("=", 1)[1]), True
        elif a.startswith("--json="):
            out_json = a.split("=", 1)[1]

    # The corpus these checks read is params.CORPUS_SUBDIR, which is the scale-2 corpus.
    # config.CORPUS_SUBDIR follows GENCP_SR_VARIANT, and C.SCALE, C.N_BANDS and
    # C.NORM_DIVISOR_DN below all come from config. Under any variant but x2 those two
    # disagree, and the checks would have reported a verdict about a corpus nobody asked
    # for - degrading scale-2 chips by 4 and calling the result registered. Refuse instead.
    if not asked and C.CORPUS_SUBDIR != P.CORPUS_SUBDIR:
        sys.stderr.write(
            f"corpus_checks.py: GENCP_SR_VARIANT selects corpus {C.CORPUS_SUBDIR!r} at "
            f"scale {C.SCALE}, but this script's default corpus is {P.CORPUS_SUBDIR!r} "
            f"at scale {P.SCALE}.\n"
            f"  Refusing rather than checking one corpus with another's parameters.\n"
            f"  Pass --corpus=DIR explicitly to say which you mean.\n")
        return 2

    if not (corpus / "manifest.csv").is_file():
        sys.stderr.write(f"corpus_checks.py: no manifest at {corpus}\n")
        return 2
    # A manifest with no rows would let C2 and C3 report success having examined nothing.
    # That is the exact failure the 23-verifier audit found eighteen times.
    if len(list(csv.DictReader(open(corpus / "manifest.csv")))) == 0:
        sys.stderr.write(f"corpus_checks.py: manifest at {corpus} has no rows - there is "
                         f"nothing to check, which is not the same as everything passing\n")
        return 2

    print("=" * 84)
    print("WP3A — corpus checks, each against a known-true and a known-false case")
    print("=" * 84)
    allok = True
    for fn in (c1, c2, c3, c4):
        allok &= bool(fn(corpus))
        print()
    print("=" * 84)
    n_ok = sum(1 for r in RESULTS if r["ok"])
    print(f"{'ALL CHECKS BEHAVED AS REGISTERED' if allok else 'A CHECK DID NOT BEHAVE AS REGISTERED'}"
          f"  ({n_ok}/{len(RESULTS)} cases)")
    print("=" * 84)
    print(f"  wall clock {time.perf_counter() - t0:.1f} s")
    if out_json:
        Path(out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(out_json).write_text(json.dumps(RESULTS, indent=2))
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
