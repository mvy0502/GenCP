"""T3 — reliability layer as a ranking under a budget.
Pure analysis of existing files. No generation, no downloads, no model runs.
Reliability score = EXACT formula from tubitak/tool/gencp_ref.py::reliability(), applied
to the INPUT render of each chip. Not refitted, not tuned.
"""
import os, csv, math
import numpy as np
import pandas as pd
from PIL import Image
from scipy.ndimage import sobel
from scipy.stats import spearmanr

ROOT = "/Users/vedat/Documents/GenCP-Generative-Goruntu-Uretimi-OpenStreetMap"
OUT = os.path.join(ROOT, "tubitak/data/tool_runs/T3")
os.makedirs(OUT, exist_ok=True)

# --- verbatim from gencp_ref.py ---
PAL = {"light_green": (133, 224, 133), "no_veg": (195, 186, 141), "forest": (0, 153, 51),
       "gray": (204, 204, 204), "water": (128, 204, 255), "building": (165, 42, 42),
       "white": (255, 255, 255), "black": (0, 0, 0)}
ANCHORS = np.array(list(PAL.values()), float)
NAMES = list(PAL.keys())


def score_input(png_path):
    """Exact reliability() body, per-tile, reading the input render instead of the tif."""
    a = np.asarray(Image.open(png_path).convert("RGB"), dtype=float)
    g = a.mean(axis=2)
    dens = float((np.hypot(sobel(g, 0), sobel(g, 1)) > 20).mean())
    lab = ((a.reshape(-1, 1, 3) - ANCHORS.reshape(1, -1, 3)) ** 2).sum(-1).argmin(1).reshape(a.shape[:2])
    frac = {n: float((lab == k).mean()) for k, n in enumerate(NAMES)}
    bnd = float((np.diff(lab, axis=0) != 0).mean() + (np.diff(lab, axis=1) != 0).mean()) / 2
    wmask = lab == NAMES.index("water")
    wedge = float(((np.diff(wmask.astype(int), axis=0) != 0).mean()
                   + (np.diff(wmask.astype(int), axis=1) != 0).mean()) / 2)
    road_bldg = 1.0 - sum(frac.values()) + frac["building"] + frac["gray"]
    score = (1.0 * dens + 0.5 * bnd + 0.5 * max(road_bldg, 0.0)
             + 0.5 * frac["building"] + 0.5 * wedge
             - 0.3 * frac["forest"] - 0.5 * frac["water"])
    return float(score)


def score_site(label, indir, stems):
    out = {}
    for k, s in enumerate(stems, 1):
        out[s] = score_input(os.path.join(indir, s + ".png"))
        if k % 20 == 0:
            print(f"[T3][{label}] scored {k}/{len(stems)} chips", flush=True)
    print(f"[T3][{label}] scored {len(stems)}/{len(stems)} chips (done)", flush=True)
    return out


# ---------------- Ankara: fit site ----------------
ank_dir = os.path.join(ROOT, "tubitak/data/ankara/run/inputs")
rc = pd.read_csv(os.path.join(ROOT, "tubitak/data/tool_runs/regC/regC_per_chip.csv"))
ank = rc[(rc.sitevar == "ank_overpass") & (rc.arm == "C2")][["stem", "med_single"]].copy()
ank = ank.rename(columns={"med_single": "residual"})
print(f"[T3][ankara] C2 single-draw per-chip residuals: n={len(ank)}", flush=True)
ank_scores = score_site("ankara", ank_dir, list(ank.stem))
ank["score"] = ank.stem.map(ank_scores)

# ---------------- Cappadocia: validation site ----------------
cap_dir = os.path.join(ROOT, "tubitak/data/tiles36SXJ/run/inputs")
cap_stems = sorted(p[:-4] for p in os.listdir(cap_dir) if p.endswith(".png"))
cap_scores = score_site("cappadocia", cap_dir, cap_stems)

# ---------------- budget curve ----------------
BUDGETS = [100, 90, 75, 50]


def curve(df, site):
    d = df.sort_values(["score", "stem"], ascending=[False, True]).reset_index(drop=True)
    d["rank"] = np.arange(1, len(d) + 1)
    n = len(d)
    rows = []
    base = None
    for N in BUDGETS:
        k = int(math.floor(N / 100.0 * n + 0.5))
        kept = d.iloc[:k]
        mean = float(kept.residual.mean())
        med = float(kept.residual.median())
        if N == 100:
            base = med
        rows.append(dict(site=site, budget=N, n_kept=k, coverage_given_up_pct=100 - N,
                         mean=round(mean, 4), median=round(med, 4),
                         delta_median=round(med - base, 4)))
    rho, p = spearmanr(d.score.values, d.residual.values)
    return d, rows, float(rho), float(p)


ank_ranked, ank_rows, ank_rho, ank_p = curve(ank, "ankara")

# ---------------- write outputs ----------------
with open(os.path.join(OUT, "T3_curve.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["site", "budget", "n_kept", "coverage_given_up_pct",
                                      "mean", "median", "delta_median", "provenance"])
    w.writeheader()
    for r in ank_rows:
        r["provenance"] = "STOCH single-draw, OVP inputs"
        w.writerow(r)
    for N in BUDGETS:
        w.writerow(dict(site="cappadocia", budget=N, n_kept="NA", coverage_given_up_pct=100 - N,
                        mean="NA", median="NA", delta_median="NA",
                        provenance="STOCH single-draw, PRE inputs — NOT SCOREABLE: "
                                    "per-chip C2 residuals absent from archive"))

cap_ranked = (pd.DataFrame({"stem": cap_stems, "score": [cap_scores[s] for s in cap_stems]})
              .sort_values(["score", "stem"], ascending=[False, True]).reset_index(drop=True))
cap_ranked["rank"] = np.arange(1, len(cap_ranked) + 1)

with open(os.path.join(OUT, "T3_per_chip.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["site", "stem", "score", "rank", "residual", "provenance"])
    for r in ank_ranked.itertuples():
        w.writerow(["ankara", r.stem, round(r.score, 6), r.rank, round(r.residual, 6),
                    "STOCH single-draw, OVP inputs"])
    for r in cap_ranked.itertuples():
        w.writerow(["cappadocia", r.stem, round(r.score, 6), r.rank, "NA",
                    "STOCH single-draw, PRE inputs; residual NA (C2 per-chip archive missing)"])

print("\n=== ANKARA (fit site) [STOCH single-draw, OVP inputs] ===")
print(pd.DataFrame(ank_rows).to_string(index=False))
print(f"Spearman(score, residual) rho={ank_rho:.4f}  p={ank_p:.4g}  n={len(ank_ranked)}")
print("\n=== CAPPADOCIA (validation site) [STOCH single-draw, PRE inputs] ===")
print("scores computed for 130 chips; residual column NA — no C2 per-chip residuals in archive")
print(f"\nwrote {OUT}/T3_curve.csv and {OUT}/T3_per_chip.csv")
