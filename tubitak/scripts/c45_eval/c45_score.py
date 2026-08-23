#!/usr/bin/env python
"""C45 step 5: score C4/C5 against the registration
(tubitak/docs/phase-c-lpips-registration.md).

Pairing base: B1_per_chip.csv — the regenerated seed-42 STOCH draws, so all
four fine-tuned arms (C1_e20, C2_e20, C4, C5) plus pretrained sit on one draw
family and one KARIOS config. The registered comparison target for C2-C1 is
the committed -0.638 +/- 0.054 (phase-c-results.md); the same-draw-family
recomputation is reported beside it, per Gate 1.

Registered readings computed here:
  PRIMARY  band: C5 - C4 negative at >= 2 SE (paired mean, ank130)
  NULL 2   check: C5 - C2 positive at >= 2 SE (perceptual own-penalty)
  RETRACT  check: all four fine-tuned arms pairwise within noise (<2 SE)
  INTERACTION: I = (C4-C5) - (C1-C2) per chip; bands additive / substitutes /
  super-additive per the registration.
Label: [STOCH seed42, OVP inputs] n=130, single draw. Sign: delta =
candidate - baseline, negative = candidate better."""
import glob, json, warnings
from pathlib import Path
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
ROOT = Path("/Users/vedat/Documents/GenCP-Generative-Goruntu-Uretimi-OpenStreetMap")
C45 = ROOT / "tubitak/data/tool_runs/C45"
B1 = ROOT / "tubitak/data/tool_runs/B1"
LABEL = "[STOCH seed42, OVP inputs] n=130, single draw (standing practice 2)"

b1 = pd.read_csv(B1 / "B1_per_chip.csv").set_index("stem")
stems = sorted(p.name[:-4] for p in (ROOT / "tubitak/data/ankara/run/inputs").glob("*.png"))
assert len(stems) == 130 and set(stems) <= set(b1.index)


def med_n(arm, st):
    csvs = glob.glob(str(C45 / "karios" / arm / st / "*" / "KLT_matcher_*.csv"))
    if not csvs:
        return np.nan, 0
    d = pd.read_csv(csvs[0], sep=None, engine="python")
    if not len(d):
        return np.nan, 0
    return float(np.median(np.hypot(d.dx, d.dy))), len(d)


rows = []
for st in stems:
    r = dict(stem=st,
             pre_med=float(b1.loc[st, "pre_med"]), pre_n=int(b1.loc[st, "pre_n"]),
             C1_med=float(b1.loc[st, "C1_e20_med"]), C1_n=int(b1.loc[st, "C1_e20_n"]),
             C2_med=float(b1.loc[st, "C2_e20_med"]), C2_n=int(b1.loc[st, "C2_e20_n"]))
    for arm in ("C4", "C5"):
        m, n = med_n(arm, st)
        r[f"{arm}_med"], r[f"{arm}_n"] = m, n
    rows.append(r)
df = pd.DataFrame(rows)
df.to_csv(C45 / "C45_per_chip.csv", index=False)

summary = {"label": LABEL, "n_chips": len(df),
           "convention": "delta = candidate - baseline; negative = candidate better",
           "pairing_base": "B1_per_chip.csv (regenerated seed-42 draws; C1/C2 = e20)",
           "registered_target_C2_minus_C1": "-0.638 +/- 0.054 committed (phase-c-results.md)",
           "arms": {}, "paired": {}, "registered": {}}

print(f"C45 — scoring against phase-c-lpips-registration.md  {LABEL}\n")
print(f"{'arm':<11} {'mean':>8} {'median':>8} {'pts med':>8} {'n0':>3}")
for arm in ("pre", "C1", "C2", "C4", "C5"):
    m, n = df[f"{arm}_med"], df[f"{arm}_n"]
    summary["arms"][arm] = dict(
        mean_of_medians=round(float(m.mean()), 4),
        se_of_mean=round(float(m.std(ddof=1) / np.sqrt(m.notna().sum())), 4),
        median_of_medians=round(float(m.median()), 4),
        points_median=float(n.median()), zero_point_chips=int((n == 0).sum()))
    print(f"{arm:<11} {m.mean():>8.4f} {m.median():>8.4f} {n.median():>8.0f} {(n==0).sum():>3}")


def paired(a, b):  # delta = a - b
    d = (df[f"{a}_med"] - df[f"{b}_med"]).dropna()
    se = d.std(ddof=1) / np.sqrt(len(d))
    return dict(mean=round(float(d.mean()), 4), se=round(float(se), 4),
                t=round(float(d.mean() / se), 2), n=len(d),
                chips_first_better=int((d < 0).sum()))


print("\npaired deltas (negative = first arm better):")
for a, b in (("C5", "C4"), ("C2", "C1"), ("C4", "C1"), ("C5", "C2"),
             ("C4", "pre"), ("C5", "pre")):
    p = paired(a, b)
    summary["paired"][f"{a}-{b}"] = p
    print(f"  {a}-{b}: {p['mean']:+.4f} ± {p['se']:.4f} px  (t={p['t']}; {a} better on {p['chips_first_better']}/{p['n']})")

# interaction I = (C4-C5) - (C1-C2), per chip
i = ((df["C4_med"] - df["C5_med"]) - (df["C1_med"] - df["C2_med"])).dropna()
i_se = i.std(ddof=1) / np.sqrt(len(i))
i_t = i.mean() / i_se
d_lpips = summary["paired"]["C5-C4"]
d_lpips_pos_2se = (-d_lpips["mean"] > 0) and (abs(d_lpips["t"]) >= 2)  # penalty C4-C5 > 0 at 2SE
if abs(i_t) < 2:
    i_band = "additive (|I| < 2 SE): pressures similar in magnitude"
elif i_t <= -2 and d_lpips_pos_2se:
    i_band = "substitutes (I < 0 at >=2 SE, D_LPIPS > 0 at >=2 SE): LPIPS already supplies the pressure"
elif i_t >= 2:
    i_band = "super-additive (I > 0 at >=2 SE): predicted by neither story, reported as its own finding"
else:
    i_band = "I < 0 at >=2 SE but D_LPIPS not itself >= 2 SE: degenerate case, primary null branch governs"
summary["registered"]["interaction"] = dict(
    mean=round(float(i.mean()), 4), se=round(float(i_se), 4), t=round(float(i_t), 2),
    n=len(i), band=i_band)

# registered checks
p54 = summary["paired"]["C5-C4"]
primary_fired = (p54["mean"] < 0) and (abs(p54["t"]) >= 2)
p52 = summary["paired"]["C5-C2"]
null2_fired = (p52["mean"] > 0) and (abs(p52["t"]) >= 2)
pairs4 = [("C1", "C2"), ("C1", "C4"), ("C1", "C5"), ("C2", "C4"), ("C2", "C5"), ("C4", "C5")]
all_noise = all(abs(paired(a, b)["t"]) < 2 for a, b in pairs4)
summary["registered"]["primary_C5_lt_C4_at_2SE"] = primary_fired
summary["registered"]["null2_C5_worse_than_C2_at_2SE"] = null2_fired
summary["registered"]["retraction_all_arms_within_noise"] = all_noise

print(f"\ninteraction I = (C4-C5) - (C1-C2): {i.mean():+.4f} ± {i_se:.4f} px (t={i_t:.2f})")
print(f"  band: {i_band}")
print(f"\nPRIMARY band (C5-C4 < 0 at >=2 SE): {'FIRED' if primary_fired else 'NOT FIRED'}")
print(f"NULL 2 (C5 worse than C2 at >=2 SE): {'FIRED' if null2_fired else 'NOT FIRED'}")
print(f"RETRACTION (all four arms within noise): {'FIRED' if all_noise else 'not fired'}")

with open(C45 / "C45_summary.json", "w") as f:
    json.dump(summary, f, indent=2)
print(f"\nwrote {C45/'C45_per_chip.csv'} and {C45/'C45_summary.json'}")
