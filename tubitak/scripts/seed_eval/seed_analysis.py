#!/usr/bin/env python
"""Seed-level analysis for the 2x2 loss-factorial replication.

Registration: tubitak/docs/seed-replication-registration.md. This file encodes the
registered readings and NOTHING ELSE. It is committed BEFORE any seed is scored, per that
registration's "the seed-level analysis script is committed before any seed is scored" rule
and per corrections-log entries 22 and 25. Any change after scoring begins must be
registered as a dated amendment with the original preserved (standing practice 4).

THE CORRECTION THIS FILE EXISTS TO MAKE
---------------------------------------
The treatment (an adversarial term; a reconstruction term) was applied ONCE PER CELL. Every
standard error in the seed-42 package is chip-level, which measures how consistently one
checkpoint beats another across 130 evaluation chips, not how consistently the treatment
works. So:

  * PRIMARY INFERENCE IS AT THE SEED LEVEL. Per seed, the per-chip paired difference is
    averaged to ONE NUMBER PER SEED PER CONTRAST; inference runs across those numbers.
  * Chip-level statistics are computed and printed, but only under the heading
    "within-run consistency", and are never used as evidence about the treatment.

SEED 42 IS THE GENERATING OBSERVATION, NOT A REPLICATE
------------------------------------------------------
The direction under test was read off seed 42, so seed 42 cannot confirm it. Every
registered reading is scored on the NEW seeds only. Seed 42 is carried through the tables,
labelled, and range-checked against the new seeds (a code-path check: its C1/C2 were trained
19-20 Aug on an earlier build than its C4/C5).

Usage
-----
    python tubitak/scripts/seed_eval/seed_analysis.py --seeds 43,44 [--with-42]

Reads, per seed S:  tubitak/data/tool_runs/C45_s{S}/C45_per_chip.csv       (residuals)
                    tubitak/data/tool_runs/C45_s{S}/C45_edge_ratio.csv     (edge ratios)
Seed 42 reads the committed C45/ directory.
Writes:             tubitak/data/tool_runs/seed_eval/seed_summary.json
                    tubitak/data/tool_runs/seed_eval/seed_per_seed.csv
"""
import argparse
import json
import os
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
ROOT = Path("/Users/vedat/Documents/GenCP-Generative-Goruntu-Uretimi-OpenStreetMap")
RUNS = ROOT / "tubitak/data/tool_runs"
OUT = RUNS / "seed_eval"

ARMS = ("pre", "C1", "C2", "C4", "C5")
# Column names in C45_per_chip.csv, written by c45_eval/c45_score.py.
MED = {a: f"{a}_med" for a in ARMS}
# Edge-ratio columns use the long arm name for pretrained.
EDGE = {"pre": "pretrained", "C1": "C1", "C2": "C2", "C4": "C4", "C5": "C5"}

LOG_MAX_DROPPED = 5      # registered: >5 of 130 chips dropped -> log transform unusable
N_CHIPS = 130


# ----------------------------------------------------------------------------------------
# per-seed contrast machinery
# ----------------------------------------------------------------------------------------
def paired(df, a, b):
    """Per-chip paired difference a - b, dropping chips where either is missing."""
    return (df[MED[a]] - df[MED[b]]).dropna()


def seed_mean(df, a, b):
    """ONE NUMBER PER SEED: the mean of the per-chip paired difference."""
    return float(paired(df, a, b).mean())


def within_run(df, a, b):
    """Chip-level statistics. WITHIN-RUN CONSISTENCY ONLY - never evidence about the
    treatment. Reported so the paper's old numbers remain reproducible and correctly
    labelled."""
    d = paired(df, a, b)
    se = float(d.std(ddof=1) / np.sqrt(len(d)))
    return {"chip_mean": float(d.mean()), "chip_se": se,
            "chip_t": float(d.mean() / se) if se else float("nan"),
            "n_chips": int(len(d)),
            "chips_first_better": int((d < 0).sum())}


def interaction_raw(df):
    """I = (C4 - C5) - (C1 - C2), per chip, averaged -> one number per seed."""
    return float(((df[MED["C4"]] - df[MED["C5"]]) -
                  (df[MED["C1"]] - df[MED["C2"]])).dropna().mean())


def interaction_log(df):
    """Interaction on ln(residual).

    Registered exclusion rule: chips where any of the four arms has a non-positive or
    non-finite residual are excluded PAIRWISE (i.e. the whole chip is dropped, since the
    contrast needs all four arms), the count is reported, and if MORE THAN 5 of 130 chips
    are lost the transform is UNUSABLE FOR THAT SEED and returns None rather than being
    silently thinned.
    """
    sub = df[[MED[a] for a in ("C1", "C2", "C4", "C5")]]
    ok = np.isfinite(sub.to_numpy()).all(axis=1) & (sub.to_numpy() > 0).all(axis=1)
    dropped = int((~ok).sum())
    if dropped > LOG_MAX_DROPPED:
        return None, dropped
    s = sub[ok]
    val = ((np.log(s[MED["C4"]]) - np.log(s[MED["C5"]])) -
           (np.log(s[MED["C1"]]) - np.log(s[MED["C2"]]))).mean()
    return float(val), dropped


def interaction_rank(df):
    """Interaction on within-chip ranks across the four fine-tuned arms.

    Per chip the four arms are ranked 1..4 by residual (1 = best/lowest). Ties take the
    MID-RANK (pandas 'average' method), as registered.
    """
    cols = [MED[a] for a in ("C1", "C2", "C4", "C5")]
    r = df[cols].rank(axis=1, method="average")
    val = ((r[MED["C4"]] - r[MED["C5"]]) - (r[MED["C1"]] - r[MED["C2"]])).dropna().mean()
    return float(val)


# ----------------------------------------------------------------------------------------
# across-seed inference
# ----------------------------------------------------------------------------------------
def across_seeds(values):
    """t-interval across seed-level numbers. Degrees of freedom are RETURNED, and the
    caller prints them, because with 2 or 4 df the multiplier is the whole story."""
    v = np.asarray([x for x in values if x is not None and np.isfinite(x)], float)
    n = len(v)
    if n < 2:
        return {"n_seeds": n, "mean": float(v[0]) if n else None, "sd": None,
                "se": None, "df": max(n - 1, 0), "t_crit": None,
                "ci_lo": None, "ci_hi": None, "excludes_zero": None,
                "all_negative": bool(n and (v < 0).all()),
                "all_positive": bool(n and (v > 0).all())}
    from scipy import stats
    m, sd = float(v.mean()), float(v.std(ddof=1))
    se = sd / np.sqrt(n)
    df_ = n - 1
    tc = float(stats.t.ppf(0.975, df_))
    lo, hi = m - tc * se, m + tc * se
    return {"n_seeds": n, "mean": m, "sd": sd, "se": se, "df": df_, "t_crit": tc,
            "ci_lo": float(lo), "ci_hi": float(hi),
            "excludes_zero": bool(lo > 0 or hi < 0),
            "all_negative": bool((v < 0).all()), "all_positive": bool((v > 0).all())}


# ----------------------------------------------------------------------------------------
# mechanism: edge ratio
# ----------------------------------------------------------------------------------------
def edge_stats(edf):
    """Per-arm MEAN of the 130 per-chip ratios - the registered statistic, chosen because
    it is what the seed-42 bands were written on. The median is carried alongside and the
    two must never be interchanged (corrections-log entry 24)."""
    out = {}
    for a in ARMS:
        col = EDGE[a]
        if col not in edf.columns:
            continue
        v = edf[col].dropna()
        out[a] = {"mean": float(v.mean()), "median": float(v.median()), "n": int(len(v))}
    return out


def c5_highest_or_tied(edf):
    """Registered tie rule: C5 counts as TIED with a competitor if the absolute difference
    between their per-seed MEAN ratios is smaller than the standard error of that
    difference computed across chips (paired per-chip differences, SE = sd/sqrt(n)).
    If C5's mean is below a competitor's by MORE than that SE, C5 is neither highest nor
    tied and the reading fails for that seed."""
    verdict, detail = True, {}
    c5 = edf[EDGE["C5"]].dropna()
    for a in ("pre", "C1", "C2", "C4"):
        col = EDGE[a]
        if col not in edf.columns:
            continue
        pair = pd.concat([edf[EDGE["C5"]], edf[col]], axis=1).dropna()
        d = pair.iloc[:, 0] - pair.iloc[:, 1]          # C5 - competitor
        se = float(d.std(ddof=1) / np.sqrt(len(d)))
        diff = float(d.mean())
        if diff >= 0:
            state = "C5 higher"
        elif abs(diff) < se:
            state = "tied"
        else:
            state = "C5 LOWER"
            verdict = False
        detail[a] = {"mean_diff_c5_minus": diff, "se_across_chips": se, "state": state}
    return verdict, detail


# ----------------------------------------------------------------------------------------
def load_seed(seed):
    d = RUNS / ("C45" if seed == 42 else f"C45_s{seed}")
    per = pd.read_csv(d / "C45_per_chip.csv")
    edge = pd.read_csv(d / "C45_edge_ratio.csv")
    if len(per) != N_CHIPS:
        raise SystemExit(f"seed {seed}: expected {N_CHIPS} chips, found {len(per)} - refusing to score")
    return per, edge


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", default="43,44",
                    help="confirmatory seeds, comma-separated (seed 42 is NOT confirmatory)")
    ap.add_argument("--with-42", action="store_true",
                    help="also load seed 42 and report it as the generating observation")
    args = ap.parse_args()
    new_seeds = [int(s) for s in args.seeds.split(",") if s.strip()]

    OUT.mkdir(parents=True, exist_ok=True)
    data = {s: load_seed(s) for s in new_seeds}
    if args.with_42:
        data[42] = load_seed(42)

    CONTRASTS = [("C5", "C4", "primary: C5 - C4"),
                 ("C1", "C2", "main effect under L1: C1 - C2"),
                 ("C4", "C5", "main effect under LPIPS: C4 - C5"),
                 ("C5", "C2", "secondary: C5 - C2")]

    rows, per_seed = [], {}
    for s, (per, edge) in sorted(data.items()):
        rec = {"seed": s, "confirmatory": s in new_seeds}
        for a, b, _ in CONTRASTS:
            rec[f"{a}-{b}"] = seed_mean(per, a, b)
        rec["I_raw"] = interaction_raw(per)
        il, dropped = interaction_log(per)
        rec["I_log"], rec["I_log_dropped"] = il, dropped
        rec["I_rank"] = interaction_rank(per)
        e = edge_stats(edge)
        for a in ARMS:
            if a in e:
                rec[f"edge_{a}_mean"] = e[a]["mean"]
                rec[f"edge_{a}_median"] = e[a]["median"]
        ok, detail = c5_highest_or_tied(edge)
        rec["edge_C5_highest_or_tied"] = ok
        rec["edge_C2_below_0.5"] = bool(e["C2"]["mean"] < 0.5) if "C2" in e else None
        per_seed[s] = {"edge_tie_detail": detail,
                       "within_run": {f"{a}-{b}": within_run(per, a, b) for a, b, _ in CONTRASTS}}
        rows.append(rec)

    df = pd.DataFrame(rows).sort_values("seed")
    df.to_csv(OUT / "seed_per_seed.csv", index=False)

    conf = df[df.confirmatory]
    print("=" * 88)
    print("SEED-LEVEL ANALYSIS - one number per seed per contrast, inference across seeds")
    print("Registration: tubitak/docs/seed-replication-registration.md")
    print(f"Confirmatory seeds: {sorted(conf.seed.tolist())}"
          + (f"   |   seed 42 shown as the GENERATING OBSERVATION, not a replicate"
             if args.with_42 else ""))
    print("=" * 88)

    summary = {"confirmatory_seeds": sorted(conf.seed.tolist()),
               "seed_42_included_as_generating_observation": bool(args.with_42),
               "per_seed": df.to_dict(orient="records"),
               "readings": {}, "within_run_consistency": per_seed}

    def report(label, key, want_negative):
        vals = conf[key].tolist()
        st = across_seeds(vals)
        signs_ok = st["all_negative"] if want_negative else st["all_positive"]
        print(f"\n{label}")
        print(f"   per seed: " + "  ".join(f"s{int(r.seed)}={r[key]:+.4f}"
                                           for _, r in conf.iterrows()))
        if args.with_42 and 42 in df.seed.values:
            v42 = float(df[df.seed == 42][key].iloc[0])
            lo, hi = min(vals), max(vals)
            inside = lo <= v42 <= hi
            print(f"   seed 42 (generating observation): {v42:+.4f}  "
                  f"[{'inside' if inside else '*** OUTSIDE ***'} the range of the new seeds "
                  f"{lo:+.4f}..{hi:+.4f}]")
            summary["readings"].setdefault(key, {})["seed42"] = {
                "value": v42, "inside_new_seed_range": bool(inside)}
        if st["n_seeds"] >= 2:
            print(f"   across seeds: mean {st['mean']:+.4f}, sd {st['sd']:.4f}, "
                  f"se {st['se']:.4f}, df {st['df']}, t*(0.975,{st['df']}) {st['t_crit']:.2f}")
            print(f"   95% CI [{st['ci_lo']:+.4f}, {st['ci_hi']:+.4f}]  "
                  f"excludes zero: {st['excludes_zero']}")
        print(f"   REGISTERED SIGN READING ({'negative' if want_negative else 'positive'} "
              f"in every confirmatory seed): {'HOLDS' if signs_ok else 'FAILS'}")
        summary["readings"].setdefault(key, {}).update(
            {"per_seed": vals, "across_seeds": st, "sign_reading_holds": bool(signs_ok)})

    report("PRIMARY - C5 - C4 (registered: negative in every confirmatory seed)",
           "C5-C4", True)
    report("MAIN EFFECT under L1 - C1 - C2 (registered: positive in every seed)",
           "C1-C2", False)
    report("MAIN EFFECT under LPIPS - C4 - C5 (registered: positive in every seed)",
           "C4-C5", False)
    report("SECONDARY - C5 - C2 (registered: positive in every seed)", "C5-C2", False)

    print("\nINTERACTION  I = (C4 - C5) - (C1 - C2)")
    print("   Registered: negative at seed level AND after a monotone re-scaling.")
    print("   Sub-additivity on a raw scale with a floor at zero is the NULL EXPECTATION,")
    print("   so the raw-scale interaction alone is NOT reported as mechanistic.")
    for key, name in (("I_raw", "raw scale (null-expectation scale)"),
                      ("I_log", "ln(residual)"), ("I_rank", "within-chip rank, mid-rank ties")):
        vals = conf[key].tolist()
        if key == "I_log" and any(v is None or (isinstance(v, float) and not np.isfinite(v))
                                  for v in vals):
            bad = conf[conf[key].isna()].seed.tolist()
            print(f"   {name:38} UNUSABLE for seeds {bad} "
                  f"(>{LOG_MAX_DROPPED} of {N_CHIPS} chips dropped)")
            summary["readings"][key] = {"unusable_seeds": bad}
            continue
        st = across_seeds(vals)
        line = "  ".join(f"s{int(r.seed)}={r[key]:+.4f}" for _, r in conf.iterrows())
        print(f"   {name:38} {line}   all negative: {st['all_negative']}")
        if key == "I_log":
            print(f"   {'':38} chips dropped per seed: "
                  + "  ".join(f"s{int(r.seed)}={int(r.I_log_dropped)}"
                              for _, r in conf.iterrows()))
        summary["readings"][key] = {"per_seed": vals, "across_seeds": st,
                                    "all_negative": bool(st["all_negative"])}
    mono_ok = (summary["readings"].get("I_log", {}).get("all_negative") or
               summary["readings"].get("I_rank", {}).get("all_negative"))
    raw_ok = summary["readings"].get("I_raw", {}).get("all_negative")
    print(f"   REGISTERED INTERACTION READING (raw negative AND at least one monotone "
          f"re-scaling negative): {'HOLDS' if (raw_ok and mono_ok) else 'FAILS'}")
    summary["readings"]["interaction_verdict"] = bool(raw_ok and mono_ok)

    print("\nMECHANISM - edge ratio in input-silent regions")
    print("   Registered statistic: per-arm MEAN of the 130 per-chip ratios "
          "(median carried alongside, never interchanged).")
    for _, r in conf.iterrows():
        s = int(r.seed)
        means = "  ".join(f"{a}={r[f'edge_{a}_mean']:.3f}" for a in ARMS
                          if f"edge_{a}_mean" in r and pd.notna(r[f"edge_{a}_mean"]))
        print(f"   seed {s}: {means}")
        print(f"            medians: " + "  ".join(
            f"{a}={r[f'edge_{a}_median']:.3f}" for a in ARMS
            if f"edge_{a}_median" in r and pd.notna(r[f"edge_{a}_median"])))
        print(f"            C5 highest-or-tied: {r['edge_C5_highest_or_tied']}   "
              f"C2 mean < 0.5: {r['edge_C2_below_0.5']}")
        for a, d in per_seed[s]["edge_tie_detail"].items():
            print(f"              vs {a}: C5-{a} = {d['mean_diff_c5_minus']:+.4f}, "
                  f"chip SE {d['se_across_chips']:.4f} -> {d['state']}")
    mech = bool(conf["edge_C5_highest_or_tied"].all() and conf["edge_C2_below_0.5"].all())
    print(f"   REGISTERED MECHANISM READING: {'HOLDS' if mech else 'FAILS'}")
    summary["readings"]["mechanism_verdict"] = mech

    print("\n" + "-" * 88)
    print("WITHIN-RUN CONSISTENCY (chip-level). NOT evidence about the treatment - these say")
    print("how uniform an effect is across terrain within a single training run.")
    for s in sorted(per_seed):
        for k, w in per_seed[s]["within_run"].items():
            print(f"   seed {s} {k:8} chip mean {w['chip_mean']:+.4f} +/- {w['chip_se']:.4f} "
                  f"(t={w['chip_t']:+.2f}, n={w['n_chips']}, "
                  f"first better on {w['chips_first_better']}/{w['n_chips']})")

    with open(OUT / "seed_summary.json", "w") as f:
        json.dump(summary, f, indent=2, default=float)
    print(f"\nwrote {OUT/'seed_per_seed.csv'} and {OUT/'seed_summary.json'}")


if __name__ == "__main__":
    main()
