#!/usr/bin/env python
"""C45 step 6 (secondary row): score C4/C5 on the 20-chip urban production
subset from the B2 outputs (POST inputs, STOCH mean-of-8 K=8 seeds 42-49,
BT.601). SECONDARY per the registration — comparability with the on-path
headline, no registered band. Existing B2 arms are read from the same KARIOS
tree so all six arms sit on one harness.
Label: [STOCH mean-of-8 K=8, POST inputs] n=20, BT.601."""
import glob, json, warnings
from pathlib import Path
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
ROOT = Path("/Users/vedat/Documents/GenCP-Generative-Goruntu-Uretimi-OpenStreetMap")
B2 = ROOT / "tubitak/data/tool_runs/B2"
C45 = ROOT / "tubitak/data/tool_runs/C45"
ARMS = ("pretrained", "C1", "C2", "C3", "C4", "C5")

stems = sorted(p.name for p in (B2 / "karios/bt601/pretrained").iterdir() if p.is_dir())
assert len(stems) == 20


def med_n(arm, st):
    csvs = glob.glob(str(B2 / "karios/bt601" / arm / st / "*" / "KLT_matcher_*.csv"))
    if not csvs:
        return np.nan, 0
    d = pd.read_csv(csvs[0], sep=None, engine="python")
    if not len(d):
        return np.nan, 0
    return float(np.median(np.hypot(d.dx, d.dy))), len(d)


rows = []
for st in stems:
    r = {"stem": st}
    for arm in ARMS:
        m, n = med_n(arm, st)
        r[f"{arm}_med"], r[f"{arm}_n"] = m, n
    rows.append(r)
df = pd.DataFrame(rows)
df.to_csv(C45 / "C45_b2_per_chip.csv", index=False)

summary = {"label": "[STOCH mean-of-8 K=8, POST inputs] n=20, BT.601 (secondary, no registered band)",
           "convention": "delta = candidate - baseline; negative = candidate better",
           "arms": {}, "paired": {}}
print(f"C45 secondary row — 20-chip urban production subset {summary['label']}\n")
print(f"{'arm':<11} {'mean':>8} {'median':>8} {'pts med':>8}")
for arm in ARMS:
    m, n = df[f"{arm}_med"], df[f"{arm}_n"]
    summary["arms"][arm] = dict(
        mean=round(float(m.mean()), 4),
        se=round(float(m.std(ddof=1) / np.sqrt(m.notna().sum())), 4),
        median=round(float(m.median()), 4), points_median=float(n.median()))
    print(f"{arm:<11} {m.mean():>8.4f} {m.median():>8.4f} {n.median():>8.0f}")

print("\npaired deltas (negative = first arm better):")
for a, b in (("C5", "C4"), ("C2", "C1"), ("C4", "C1"), ("C5", "C2"), ("C4", "pretrained"), ("C5", "pretrained")):
    d = (df[f"{a}_med"] - df[f"{b}_med"]).dropna()
    se = d.std(ddof=1) / np.sqrt(len(d))
    summary["paired"][f"{a}-{b}"] = dict(mean=round(float(d.mean()), 4), se=round(float(se), 4),
                                         t=round(float(d.mean() / se), 2), n=len(d),
                                         chips_first_better=int((d < 0).sum()))
    print(f"  {a}-{b}: {d.mean():+.4f} ± {se:.4f} px  (t={d.mean()/se:.2f}; {a} better on {(d<0).sum()}/{len(d)})")

with open(C45 / "C45_b2_summary.json", "w") as f:
    json.dump(summary, f, indent=2)
print(f"\nwrote {C45/'C45_b2_per_chip.csv'} and {C45/'C45_b2_summary.json'}")
