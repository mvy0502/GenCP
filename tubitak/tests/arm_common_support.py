#!/usr/bin/env python
"""Step 5 Pass 2 — equal-count common-support audit of the uncovered arm contrasts.

Registered in tubitak/docs/plugin-gate-registration-C2.md before any contrast was computed.

Rule (the prior package's PRIMARY rule, unchanged): per chip, K_c = min over the two arms
of that chip's matched-point count; each arm's chip residual = median of its own K_c
best-scoring points, ranked by the KLT `score` column DESCENDING. Never by radial error -
that would be selection on the outcome.

Convention: Delta = candidate - baseline; negative = candidate better.
"""
from __future__ import annotations
import glob, sys

# Unknown arguments are refused, not ignored: a verifier that runs its default
# and prints PASS when you asked for something else is reporting on the wrong run.
import os.path as _op  # noqa: E402
sys.path.insert(0, _op.join(_op.dirname(_op.abspath(__file__)),
                            *(['..', 'tests'] if _op.basename(
                                _op.dirname(_op.abspath(__file__))) != 'tests'
                              else [])))
from _guard import strict_argv  # noqa: E402
strict_argv(known=(), positional=0)
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
EV = ROOT / "tubitak/docs/evidence"
IND, MAT = 0.05, 0.15

ARMS_C45 = {
    "pre": "tubitak/data/ankara/run/results/{stem}/*/KLT_matcher_*.csv",
    "C1":  "tubitak/data/tool_runs/B1/karios/C1_e20/{stem}/*/KLT_matcher_*.csv",
    "C2":  "tubitak/data/tool_runs/B1/karios/C2_e20/{stem}/*/KLT_matcher_*.csv",
    "C4":  "tubitak/data/tool_runs/C45/karios/C4/{stem}/*/KLT_matcher_*.csv",
    "C5":  "tubitak/data/tool_runs/C45/karios/C5/{stem}/*/KLT_matcher_*.csv",
}


def points(pattern, stem):
    """(score, radial) per matched point."""
    c = glob.glob(str(ROOT / pattern.format(stem=stem)))
    if not c:
        return None
    d = pd.read_csv(c[0], sep=None, engine="python")
    if not len(d):
        return None
    r = np.hypot(d["dx"].to_numpy(float), d["dy"].to_numpy(float))
    s = d["score"].to_numpy(float)
    return s, r


def med_topk(p, k):
    s, r = p
    order = np.argsort(-s, kind="stable")      # descending score
    return float(np.median(r[order[:k]]))


def contrast(stems, pat_a, pat_b):
    """Returns per-chip original and equal-count medians for both arms."""
    rows = []
    for st in stems:
        pa, pb = points(pat_a, st), points(pat_b, st)
        if pa is None or pb is None:
            continue
        na, nb = len(pa[1]), len(pb[1])
        k = min(na, nb)
        if k < 1:
            continue
        rows.append(dict(stem=st, n_a=na, n_b=nb, k=k,
                         a_orig=float(np.median(pa[1])), b_orig=float(np.median(pb[1])),
                         a_eq=med_topk(pa, k), b_eq=med_topk(pb, k)))
    return pd.DataFrame(rows)


def paired(d):
    d = np.asarray(d, float)
    d = d[np.isfinite(d)]
    n = len(d)
    sd = float(d.std(ddof=1)) if n > 1 else np.nan
    se = sd / np.sqrt(n) if n > 1 else np.nan
    return float(d.mean()), sd, se, n, (d.mean() / se if se else np.nan)


def band(x):
    a = abs(x)
    return "indistinguishable" if a <= IND else ("MATERIAL" if a > MAT else "documented")


def report(label, df, name_a, name_b):
    do_m, do_sd, do_se, n, do_t = paired(df.b_orig - df.a_orig)
    de_m, de_sd, de_se, _, de_t = paired(df.b_eq - df.a_eq)
    shift = de_m - do_m
    drop_a = 100.0 * (1 - df.k.sum() / df.n_a.sum())
    drop_b = 100.0 * (1 - df.k.sum() / df.n_b.sum())
    print(f"\n  {label}   (Delta = {name_b} - {name_a}; negative = {name_b} better)")
    print(f"     chips {n}   median points {df.n_a.median():.0f} vs {df.n_b.median():.0f}   "
          f"points discarded: {name_a} {drop_a:.1f}%, {name_b} {drop_b:.1f}%")
    print(f"     original    Delta {do_m:+.4f} +/- {do_sd:.4f}  (SE {do_se:.4f}, t={do_t:+.2f})")
    print(f"     equal-count Delta {de_m:+.4f} +/- {de_sd:.4f}  (SE {de_se:.4f}, t={de_t:+.2f})")
    print(f"     change {shift:+.4f} px -> {band(shift)}"
          f"   sign {'HOLDS' if np.sign(de_m) == np.sign(do_m) else '*** FLIPPED ***'}"
          f"   {'WIDENS' if abs(de_m) > abs(do_m) else 'narrows'}")
    return dict(comparison=label, n=n, orig=do_m, eq=de_m, change=shift,
                sign_holds=bool(np.sign(de_m) == np.sign(do_m)))


def main():
    ref = pd.read_csv(EV / "C45/C45_per_chip.csv")
    stems = list(ref.stem)
    print("Step 5 Pass 2 — equal-count common-support audit")
    print(f"  {len(stems)} chips, Ankara set; rule: median of each arm's K_c best-scoring")
    print("  points, K_c = min over the two arms, ranked by KLT score descending\n")
    print("=" * 78)
    print("A. contrasts involving pretrained (NOT covered by the six-seed block)")
    print("=" * 78)
    out = []
    for cand in ("C1", "C2", "C4", "C5"):
        df = contrast(stems, ARMS_C45["pre"], ARMS_C45[cand])
        out.append(report(f"pre vs {cand}", df, "pre", cand))

    print("\n" + "=" * 78)
    print("B. cross-check against the six-seed block's own finding (single seed here)")
    print("=" * 78)
    for a, b in (("C4", "C5"), ("C2", "C5"), ("C1", "C2")):
        df = contrast(stems, ARMS_C45[a], ARMS_C45[b])
        out.append(report(f"{a} vs {b}", df, a, b))

    print("\n" + "=" * 78)
    flips = [o for o in out if not o["sign_holds"]]
    mats = [o for o in out if abs(o["change"]) > MAT]
    print(f"sign flips: {len(flips)}    changes beyond {MAT} px: {len(mats)}")
    if flips:
        print("  FLIPPED: " + ", ".join(o["comparison"] for o in flips))
    if mats:
        print("  MATERIAL: " + ", ".join(f"{o['comparison']} ({o['change']:+.3f})" for o in mats))
    print("=" * 78)
    pd.DataFrame(out).to_csv(ROOT / "tubitak/data/plugin_gates/pass2_common_support.csv",
                             index=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
