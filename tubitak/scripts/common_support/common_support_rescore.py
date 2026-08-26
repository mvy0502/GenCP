#!/usr/bin/env python
"""Common-support re-scoring of the six-seed Modal block.

Registration: tubitak/docs/common-support-registration.md, committed 89eee9f4 BEFORE any
contrast below was computed. This file implements that registration and nothing else.

PRIMARY   equal-count truncation: per chip, K_c = min over arms of matched-point count;
          each arm's chip residual = median of its own K_c best-scoring points, ranked by
          the KLT `score` column DESCENDING. Ranking is never by `radial error`, which is
          the outcome.
SECONDARY chip-level common support: chip enters only if all four arms have >= K points,
          K in {1, 10, 20, 30}.

Reads only committed KARIOS per-point CSVs. No training, no inference, no GPU.
"""
import csv, glob, os, math, json, statistics as st
from collections import defaultdict

ROOT = "/Users/vedat/Documents/GenCP-Generative-Goruntu-Uretimi-OpenStreetMap/tubitak/data/tool_runs/"
ARMS = ("C1", "C2", "C4", "C5")
SEEDS = (45, 46, 47, 48, 49, 50)


def chip_points(seed, arm, chip):
    """(score, radial_error) for every matched point of one arm on one chip."""
    g = glob.glob(f"{ROOT}C45_s{seed}_modal/karios/{arm}/{chip}/*/KLT_matcher_*.csv")
    if not g:
        return []
    rows = list(csv.reader(open(g[0]), delimiter=';'))
    h = rows[0]
    si, ri = h.index("score"), h.index("radial error")
    out = []
    for r in rows[1:]:
        if len(r) > max(si, ri) and r[si] and r[ri]:
            out.append((float(r[si]), float(r[ri])))
    return out


def load_seed(seed):
    base = f"{ROOT}C45_s{seed}_modal/karios/C1"
    chips = sorted(os.listdir(base))
    return {c: {a: chip_points(seed, a, c) for a in ARMS} for c in chips}


def arm_mean(per_chip):
    return st.mean(per_chip.values())


def paired(A, B):
    ch = sorted(set(A) & set(B))
    d = [A[c] - B[c] for c in ch]
    return st.mean(d), (st.stdev(d) / math.sqrt(len(d)) if len(d) > 1 else float("nan")), len(d)


def main():
    out = {"registration": "tubitak/docs/common-support-registration.md @ 89eee9f4",
           "seeds": {}}
    for seed in SEEDS:
        data = load_seed(seed)
        orig, trunc, kept = {a: {} for a in ARMS}, {a: {} for a in ARMS}, {}
        lost = defaultdict(int); total = defaultdict(int)
        for c, P in data.items():
            if any(len(P[a]) == 0 for a in ARMS):
                continue
            for a in ARMS:
                orig[a][c] = st.median(e for _, e in P[a])
                total[a] += len(P[a])
            K = min(len(P[a]) for a in ARMS)
            kept[c] = K
            for a in ARMS:
                best = sorted(P[a], key=lambda t: -t[0])[:K]      # descending score
                trunc[a][c] = st.median(e for _, e in best)
                lost[a] += len(P[a]) - K
        rec = {"n_chips": len(kept), "K_sum": sum(kept.values()),
               "K_mean": round(st.mean(kept.values()), 2),
               "points_total": dict(total), "points_dropped": dict(lost),
               "frac_dropped": {a: round(lost[a] / total[a], 4) for a in ARMS}}
        for tag, src in (("original", orig), ("equal_count", trunc)):
            rec[tag] = {"arm_mean": {a: round(arm_mean(src[a]), 4) for a in ARMS}}
            for name, (x, y) in {"C5-C4": ("C5", "C4"), "C1-C2": ("C1", "C2"),
                                 "C4-C5": ("C4", "C5"), "C5-C2": ("C5", "C2")}.items():
                mu, se, n = paired(src[x], src[y])
                rec[tag][name] = {"mean": round(mu, 4), "se": round(se, 4), "n": n}
            m = rec[tag]["arm_mean"]
            rec[tag]["I_raw"] = round((m["C4"] - m["C5"]) - (m["C1"] - m["C2"]), 4)
        # chip-level common support under floors
        rec["floors"] = {}
        for K in (1, 10, 20, 30):
            sel = [c for c, P in data.items() if all(len(P[a]) >= K for a in ARMS)]
            if not sel:
                rec["floors"][K] = {"n_chips": 0}
                continue
            sub = {a: {c: orig[a][c] for c in sel if c in orig[a]} for a in ARMS}
            e = {"n_chips": len(sub["C1"])}
            for name, (x, y) in {"C5-C4": ("C5", "C4"), "C5-C2": ("C5", "C2"),
                                 "C1-C2": ("C1", "C2"), "C4-C5": ("C4", "C5")}.items():
                mu, se, n = paired(sub[x], sub[y])
                e[name] = {"mean": round(mu, 4), "se": round(se, 4), "n": n}
            rec["floors"][K] = e
        out["seeds"][seed] = rec
        print(f"seed {seed}: {rec['n_chips']} chips, K_mean {rec['K_mean']}, "
              f"dropped {rec['frac_dropped']}", flush=True)
    d = "/Users/vedat/Documents/GenCP-Generative-Goruntu-Uretimi-OpenStreetMap/tubitak/docs/evidence/common_support"
    os.makedirs(d, exist_ok=True)
    json.dump(out, open(d + "/common_support.json", "w"), indent=1)
    print("wrote common_support.json")


if __name__ == "__main__":
    main()
