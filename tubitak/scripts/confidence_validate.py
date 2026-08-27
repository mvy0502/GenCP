#!/usr/bin/env python
"""Does the confidence score predict KARIOS matching error on held-out chips?

Executes tubitak/docs/confidence-registration.md exactly as registered. Nothing here
chooses a signal, a weight, a window or a threshold: all of those are fixed in that file,
which was committed before this script was written.

Sign convention: higher confidence = better = lower expected error. A NEGATIVE correlation
between confidence and error is the result that supports the score.

    /opt/homebrew/Caskroom/miniforge/base/envs/gencp/bin/python \
        tubitak/scripts/confidence_validate.py

Writes tubitak/docs/evidence/confidence/{per_chip.csv,results.json} and prints the report.
"""
from __future__ import annotations

import csv
import json
import sys
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tubitak"))

import numpy as np
from PIL import Image

from gencp_core import confidence as C
from gencp_core import infer as ginfer

# --- everything below is quoted from the registration, not chosen here -----------------
PER_CHIP = ROOT / "tubitak/docs/evidence/regD/regD_per_chip.csv"
# Registration 2 evaluates the same scores on the Ankara Overpass corpus. One switch, one
# implementation: a copied script would drift from this one.
_ANKARA = "--ankara" in sys.argv
INPUTS = (ROOT / "tubitak/data/ankara/run/inputs") if _ANKARA else (ROOT / "tubitak/data/eu_holdout/inputs")
ARM_PRIMARY = "C2"
ARM_SECONDARY = "C1"
CORPUS_TAG = "ankara" if _ANKARA else "eu"
SITEVAR = "ank_overpass" if _ANKARA else "eu"
ERR_COL = "med_mean32"
N_COL = "n_mean32"
N_PASSES = 16
SEEDS = list(range(N_PASSES))
WINDOW = C.WINDOW
CKPT = ROOT / "tubitak/outputs/c2_checkpoints/checkpoints/C2/latest_net_G.pth"
ONNX = ROOT / "tubitak/data/plugin_models/gencp_C2_fp32.onnx"
ONNX_STOCHASTIC = ROOT / "tubitak/data/plugin_models/gencp_C2_stochastic_fp32.onnx"
OUT = ROOT / "tubitak/docs/evidence/confidence"
RHO_PASS = -0.25
RHO_STRONG = -0.35
N_BOOT = 10_000
BOOT_SEED = 20260827
WIN_CHIPS = 30
RESULTS = {}


def say(*a):
    print(*a, flush=True)


# ------------------------------------------------------------------ statistics --------
def spearman(x, y):
    from scipy.stats import spearmanr
    return float(spearmanr(x, y).statistic)


def rank(x):
    from scipy.stats import rankdata
    return rankdata(x)


def partial_spearman(x, y, z):
    """Spearman of x vs y with z partialled out, on ranks (Pearson of the residuals)."""
    rx, ry, rz = rank(x), rank(y), rank(z)

    def resid(a, b):
        b1 = np.c_[np.ones_like(b), b]
        return a - b1 @ np.linalg.lstsq(b1, a, rcond=None)[0]
    ex, ey = resid(rx, rz), resid(ry, rz)
    return float(np.corrcoef(ex, ey)[0, 1])


def boot_ci(fn, n, seed=BOOT_SEED, reps=N_BOOT):
    """Percentile bootstrap over CHIPS. fn takes an index array and returns a scalar."""
    rng = np.random.default_rng(seed)
    vals = np.array([fn(rng.integers(0, n, n)) for _ in range(reps)])
    vals = vals[np.isfinite(vals)]
    return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


# ------------------------------------------------------------------ the data ----------
def load_errors():
    rows = list(csv.DictReader(open(PER_CHIP)))
    out = {}
    for arm in (ARM_PRIMARY, ARM_SECONDARY):
        sel = [r for r in rows if r["sitevar"] == SITEVAR and r["arm"] == arm]
        out[arm] = {r["stem"]: (float(r[ERR_COL]), float(r[N_COL]), int(r["stratum"]))
                    for r in sel}
    stems = sorted(out[ARM_PRIMARY])
    say(f"  held-out chips with {ARM_PRIMARY} errors : {len(stems)}")
    say(f"  also with {ARM_SECONDARY} errors               : "
        f"{len(set(stems) & set(out[ARM_SECONDARY]))}")
    missing = [s for s in stems if not (INPUTS / f"{s}.png").is_file()]
    if missing:
        raise SystemExit(f"{len(missing)} chips have no input render: {missing[:5]}")
    say(f"  input renders present                  : {len(stems)}/{len(stems)}")
    return stems, out


# ------------------------------------------------------------------ signal S ----------
def stochastic_spread(G, arr, seeds=SEEDS):
    """Per-pixel std over N dropout passes, averaged over channels. Also returns the mean."""
    import torch
    x = torch.from_numpy(arr)
    outs = []
    with torch.no_grad():
        for s in seeds:
            torch.manual_seed(s)
            outs.append(G(x).numpy()[0])
    stack = np.stack(outs)                       # (N, 3, H, W) in [-1, 1]
    # to DN so the control below compares like with like
    dn = (stack + 1.0) / 2.0 * 255.0
    return dn.std(axis=0).mean(axis=0), dn.mean(axis=0)


def control_stochastic_is_around_deterministic(G, stems):
    """Registered control, run FIRST: is the stochastic mean a perturbation of the image
    we actually deliver? If not, its spread describes some other model."""
    say("\n--- CONTROL: stochastic passes must sit around the deterministic output ---")
    det = ginfer.OnnxGenerator(str(ONNX))
    rows = []
    for stem in stems[:5]:
        with Image.open(INPUTS / f"{stem}.png") as im:
            arr = ginfer.preprocess(im)
            d = det.run_tensor(arr)
        d_dn = (np.asarray(d)[0] + 1.0) / 2.0 * 255.0
        _, m_dn = stochastic_spread(G, arr)
        diff = np.abs(d_dn - m_dn)
        rows.append((stem, float(diff.mean()), float(diff.max())))
        say(f"    {stem}  mean |det - stoch_mean| {rows[-1][1]:6.2f} DN   "
            f"max {rows[-1][2]:6.2f} DN")
    RESULTS["control_stochastic_vs_deterministic"] = [
        dict(stem=s, mean_dn=a, max_dn=b) for s, a, b in rows]
    worst = max(r[1] for r in rows)
    say(f"    worst chip mean difference: {worst:.2f} DN")
    return worst


# ------------------------------------------------------------------ main --------------
def main():
    OUT.mkdir(parents=True, exist_ok=True)
    import torch
    import onnxruntime
    say("=" * 78)
    say("CONFIDENCE SCORE VALIDATION - executing confidence-registration.md")
    say("=" * 78)
    say(f"  torch {torch.__version__} | numpy {np.__version__} | "
        f"onnxruntime {onnxruntime.__version__}")
    say(f"  window {WINDOW} | N passes {N_PASSES} | seeds {SEEDS[0]}..{SEEDS[-1]}")
    RESULTS["versions"] = dict(torch=torch.__version__, numpy=np.__version__,
                               onnxruntime=onnxruntime.__version__)
    RESULTS["config"] = dict(window=WINDOW, n_passes=N_PASSES, seeds=SEEDS,
                             arm=ARM_PRIMARY, corpus=SITEVAR, err_col=ERR_COL)

    use_onnx = "--onnx-spread" in sys.argv
    RESULTS["spread_path"] = ("onnx (the deployed path)" if use_onnx
                              else "torch (the registered path)")
    say(f"  stochastic spread computed via         : {RESULTS['spread_path']}")

    stems, errs = load_errors()
    from gencp_core import export as gexport
    G, n_drop = gexport.build_stochastic_generator(str(CKPT))
    sto = None
    if use_onnx:
        sto = ginfer.StochasticOnnxGenerator(str(ONNX_STOCHASTIC))
    say(f"  dropout modules re-enabled             : {n_drop}")
    RESULTS["dropout_modules"] = n_drop

    control_stochastic_is_around_deterministic(G, stems)

    say(f"\n--- computing signals over {len(stems)} chips ---")
    recs = []
    t0 = time.time()
    for k, stem in enumerate(stems, 1):
        with Image.open(INPUTS / f"{stem}.png") as im:
            rgb = np.asarray(im.convert("RGB"))
            arr = ginfer.preprocess(im)
        sig = C.signals(rgb, window=WINDOW)
        if sto is not None:
            with Image.open(INPUTS / f"{stem}.png") as im2:
                spread, _ = sto.spread(im2, n_passes=N_PASSES, seed=0)
        else:
            spread, _ = stochastic_spread(G, arr)
        e, n, stratum = errs[ARM_PRIMARY][stem]
        e1 = errs[ARM_SECONDARY].get(stem, (np.nan,))[0]
        recs.append(dict(
            stem=stem, stratum=stratum,
            conf_D=float(sig["conf_D"].mean()),
            conf_B=float(sig["conf_B"].mean()),
            conf_S=float(-spread.mean()),          # oriented: less spread = more confidence
            osm_fraction=sig["osm_fraction"],
            err_C2=e, n_C2=n, err_C1=e1,
        ))
        if k % 25 == 0 or k == len(stems):
            say(f"    {k}/{len(stems)} chips   ({time.time()-t0:.0f}s elapsed)")

    # z-scores taken ACROSS CHIPS after aggregation, as registered
    D = np.array([r["conf_D"] for r in recs])
    B = np.array([r["conf_B"] for r in recs])
    S = np.array([r["conf_S"] for r in recs])
    E = np.array([r["err_C2"] for r in recs])
    E1 = np.array([r["err_C1"] for r in recs])
    N = np.array([r["n_C2"] for r in recs])

    def z(v):
        return (v - v.mean()) / v.std(ddof=0)
    COMB = (z(D) + z(S)) / 2.0
    for r, c in zip(recs, COMB):
        r["conf_COMB"] = float(c)

    _name = ("per_chip_onnx.csv" if use_onnx else "per_chip.csv").replace(
        ".csv", f"_{CORPUS_TAG}.csv" if _ANKARA else ".csv")
    with open(OUT / _name, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(recs[0]))
        w.writeheader()
        w.writerows(recs)
    say(f"  wrote {OUT/'per_chip.csv'}")

    # ------------------------------------------------------------ correlations --------
    say("\n" + "=" * 78)
    say("PRIMARY - Spearman rho against KARIOS median residual (arm C2, 150 held-out chips)")
    say("=" * 78)
    say("  convention: higher confidence = better, so a NEGATIVE rho supports the score")
    table = {}
    for name, v in (("conf_D  (input density)", D), ("conf_B  (distance baseline)", B),
                    ("conf_S  (stochastic spread)", S), ("conf_COMB (registered)", COMB)):
        rho = spearman(v, E)
        lo, hi = boot_ci(lambda i, v=v: spearman(v[i], E[i]), len(E))
        table[name] = dict(rho=rho, ci=[lo, hi])
        flag = "excludes 0" if (lo < 0 and hi < 0) or (lo > 0 and hi > 0) else "INCLUDES 0"
        say(f"    {name:32s} rho {rho:+.3f}   95% CI [{lo:+.3f}, {hi:+.3f}]  {flag}")
    RESULTS["spearman_C2"] = table

    rho_comb = table["conf_COMB (registered)"]["rho"]
    rho_base = table["conf_B  (distance baseline)"]["rho"]
    d_lo, d_hi = boot_ci(
        lambda i: spearman(COMB[i], E[i]) - spearman(B[i], E[i]), len(E))
    beats = d_hi < 0
    say(f"\n  rho(COMB) - rho(B) = {rho_comb - rho_base:+.3f}  "
        f"95% CI [{d_lo:+.3f}, {d_hi:+.3f}]  -> "
        f"{'COMB beats the baseline' if beats else 'COMB does NOT beat the baseline'}")
    RESULTS["comb_minus_baseline"] = dict(diff=rho_comb - rho_base, ci=[d_lo, d_hi],
                                          beats_baseline=bool(beats))

    passed = rho_comb <= RHO_PASS and table["conf_COMB (registered)"]["ci"][1] < 0
    say(f"\n  REGISTERED PRIMARY TEST (rho <= {RHO_PASS} and CI excludes 0): "
        f"{'PASS' if passed else 'FAIL'}")
    RESULTS["primary_pass"] = bool(passed)

    # secondary arm, a replication check and not a second chance
    say("\n  secondary arm C1 (replication check only):")
    for name, v in (("conf_B", B), ("conf_COMB", COMB)):
        ok = np.isfinite(E1)
        rho = spearman(v[ok], E1[ok])
        say(f"    {name:10s} rho {rho:+.3f}  (n={int(ok.sum())})")
        RESULTS.setdefault("spearman_C1", {})[name] = rho

    # ------------------------------------------------------------ confounds ----------
    say("\n" + "=" * 78)
    say("CONFOUND - matched point count (this mechanism produced a false result once)")
    say("=" * 78)
    rho_cn = spearman(COMB, N)
    rho_en = spearman(N, E)
    pr = partial_spearman(COMB, E, N)
    say(f"    rho(conf_COMB, n_mean32)                 {rho_cn:+.3f}")
    say(f"    rho(n_mean32,  err)                      {rho_en:+.3f}")
    say(f"    partial rho(conf_COMB, err | n_mean32)   {pr:+.3f}   "
        f"(primary was {rho_comb:+.3f})")
    keep = N >= 10
    rho_k = spearman(COMB[keep], E[keep])
    say(f"    restricted to n_mean32 >= 10             rho {rho_k:+.3f}  "
        f"(n={int(keep.sum())}, dropped {int((~keep).sum())})")
    RESULTS["confound_n"] = dict(rho_conf_n=rho_cn, rho_n_err=rho_en, partial=pr,
                                 rho_n_ge_10=rho_k, n_kept=int(keep.sum()))

    # ------------------------------------------------------------ discard curve ------
    say("\n" + "=" * 78)
    say("OPERATIONAL - discard the lowest-confidence X%, what happens to the rest")
    say("=" * 78)
    med_all = float(np.median(E))
    say(f"    median residual over all {len(E)} chips: {med_all:.4f} px")
    rng = np.random.default_rng(BOOT_SEED)
    curve = {}
    say(f"    {'X%':>4}  {'kept':>5}  {'COMB':>8}  {'conf_D':>8}  {'baseline B':>11}  {'random':>8}")
    for X in (10, 25, 50):
        k = int(round(len(E) * X / 100.0))
        keep_n = len(E) - k
        res = {}
        for nm, v in (("COMB", COMB), ("B", B), ("D", D)):
            idx = np.argsort(v)[::-1][:keep_n]     # highest confidence retained
            res[nm] = float(np.median(E[idx]))
        rnd = float(np.mean([np.median(E[rng.choice(len(E), keep_n, replace=False)])
                             for _ in range(1000)]))
        res["random"] = rnd
        curve[X] = res
        say(f"    {X:>3}%  {keep_n:>5}  {res['COMB']:>8.4f}  {res['D']:>8.4f}  "
            f"{res['B']:>11.4f}  {rnd:>8.4f}")
    RESULTS["discard_curve"] = curve
    RESULTS["median_all"] = med_all

    # ------------------------------------------------------------ bands --------------
    say("\n" + "=" * 78)
    say("BANDS")
    say("=" * 78)
    if not passed:
        say("    Primary test FAILED. Per the registration, no bands are produced and no")
        say("    confidence layer ships.")
        RESULTS["bands"] = None
    else:
        score = COMB
        order = np.argsort(score)
        se, sc = E[order], score[order]
        conds, centres = [], []
        for i in range(0, len(se) - WIN_CHIPS + 1):
            conds.append(float(np.median(se[i:i + WIN_CHIPS])))
            centres.append(float(sc[i + WIN_CHIPS // 2]))
        conds, centres = np.array(conds), np.array(centres)
        M = med_all
        allow_red = rho_comb <= RHO_STRONG
        red_hi = green_lo = None
        hot = conds >= 1.5 * M
        if allow_red and hot.any() and hot[0]:
            last = np.argmax(~hot) if (~hot).any() else len(hot)
            red_hi = float(centres[last - 1])
        cool = conds <= 1.0 * M
        if cool.any() and cool[-1]:
            first = len(cool) - 1 - np.argmax(~cool[::-1]) if (~cool).any() else -1
            green_lo = float(centres[first + 1]) if first + 1 < len(centres) else float(centres[-1])
        say(f"    corpus median M = {M:.4f} px; red requires a conditional median "
            f">= {1.5*M:.4f}")
        say(f"    red band permitted by |rho| >= {abs(RHO_STRONG)}: {allow_red}")
        say(f"    red upper boundary  : {red_hi}")
        say(f"    green lower boundary: {green_lo}")
        bands = {}
        for nm, m in (("red", score <= red_hi if red_hi is not None else np.zeros(len(score), bool)),
                      ("green", score >= green_lo if green_lo is not None else np.zeros(len(score), bool)),
                      ("amber", None)):
            if m is None:
                m = ~(bands["red"]["mask"] | bands["green"]["mask"])
            bands[nm] = dict(mask=m, n=int(m.sum()),
                             median=float(np.median(E[m])) if m.any() else None,
                             iqr=float(np.subtract(*np.percentile(E[m], [75, 25]))) if m.any() else None)
            say(f"    {nm:6s} n={bands[nm]['n']:3d}  median residual "
                f"{bands[nm]['median'] if bands[nm]['median'] is None else round(bands[nm]['median'],4)} px"
                f"  IQR {bands[nm]['iqr'] if bands[nm]['iqr'] is None else round(bands[nm]['iqr'],4)}")
        RESULTS["bands"] = dict(
            red_hi=red_hi, green_lo=green_lo, allow_red=bool(allow_red), M=M,
            counts={k: v["n"] for k, v in bands.items()},
            medians={k: v["median"] for k, v in bands.items()},
            iqrs={k: v["iqr"] for k, v in bands.items()})

    tag = ("_onnx" if use_onnx else "") + ("_ankara" if _ANKARA else "")
    # ------------------------------------------------- registration 2 decision -------
    say("\n" + "=" * 78)
    say("REGISTRATION 2 - non-inferiority: is conf_D alone not meaningfully worse?")
    say("=" * 78)
    rho_D = spearman(D, E)
    d_lo2, d_hi2 = boot_ci(lambda i: spearman(D[i], E[i]) - spearman(COMB[i], E[i]), len(E))
    b_lo2, b_hi2 = boot_ci(lambda i: spearman(D[i], E[i]) - spearman(B[i], E[i]), len(E))
    ci_D = boot_ci(lambda i: spearman(D[i], E[i]), len(E))
    MARGIN = 0.05
    c1 = d_hi2 < MARGIN
    c2 = rho_D <= RHO_PASS and ci_D[1] < 0
    c3 = b_hi2 < 0
    say(f"  rho(conf_D)                    {rho_D:+.3f}  95% CI [{ci_D[0]:+.3f}, {ci_D[1]:+.3f}]")
    say(f"  rho(conf_COMB)                 {spearman(COMB, E):+.3f}")
    say(f"  rho(conf_B)                    {spearman(B, E):+.3f}")
    say(f"  rho(D) - rho(COMB)             {rho_D - spearman(COMB, E):+.3f}  "
        f"95% CI [{d_lo2:+.3f}, {d_hi2:+.3f}]")
    say(f"  rho(D) - rho(B)                {rho_D - spearman(B, E):+.3f}  "
        f"95% CI [{b_lo2:+.3f}, {b_hi2:+.3f}]")
    say("")
    say(f"  1 non-inferiority  upper CI {d_hi2:+.3f} < +{MARGIN}      : {'PASS' if c1 else 'FAIL'}")
    say(f"  2 stands alone     rho <= {RHO_PASS}, CI excludes 0 : {'PASS' if c2 else 'FAIL'}")
    say(f"  3 beats baseline   upper CI {b_hi2:+.3f} < 0        : {'PASS' if c3 else 'FAIL'}")
    say("")
    say(f"  REGISTERED DECISION: {'SWITCH to conf_D alone' if (c1 and c2 and c3) else 'KEEP conf_COMB'}")
    RESULTS["registration2"] = dict(
        rho_D=rho_D, ci_D=list(ci_D), rho_COMB=spearman(COMB, E), rho_B=spearman(B, E),
        diff_D_COMB=[d_lo2, d_hi2], diff_D_B=[b_lo2, b_hi2], margin=MARGIN,
        cond_noninferior=bool(c1), cond_standalone=bool(c2), cond_beats_baseline=bool(c3),
        decision=("switch_to_conf_D" if (c1 and c2 and c3) else "keep_conf_COMB"))
    say("\n  partial rho given n_mean32, every score:")
    for nm, v in (("conf_D", D), ("conf_B", B), ("conf_S", S), ("conf_COMB", COMB)):
        pr_ = partial_spearman(v, E, N)
        say(f"    {nm:10s} raw {spearman(v, E):+.3f}   partial {pr_:+.3f}")
        RESULTS.setdefault("partial_all", {})[nm] = pr_

    (OUT / f"results{tag}.json").write_text(json.dumps(RESULTS, indent=2, default=str))
    say(f"\nwrote {OUT}/results{tag}.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
