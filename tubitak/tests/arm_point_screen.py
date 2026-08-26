#!/usr/bin/env python
"""Step 5 Pass 1 — screen every reported arm comparison for unequal matched-point counts.

Gate D showed that when two arms yield different numbers of matched KLT points, the arm
with fewer points can look better purely because the points it loses are the hard ones -
about 79% of the observed advantage in that case. That mechanism is not specific to
Gate D; it applies to any comparison between arms with unequal matched-point counts.

This is a SCREEN, not a test. It tabulates counts so that Pass 2 is run only where there
is something to find.

Screen threshold, stated before any number was looked at:
    materially different  <=>  |median(n_A) - median(n_B)| / max(median) >= 10%
Gate D's own case was 60 -> 50 (17%) and 61 -> 48 (21%), both above this line.
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
EV = ROOT / "tubitak/docs/evidence"
THRESH = 0.10


def arms_in(df):
    """Arm name -> (median_col, n_col) for every arm carrying a point count."""
    out = {}
    for c in df.columns:
        if c.endswith("_n"):
            base = c[:-2]
            for med in (base + "_med", base + "_rgb_med" if False else base + "_med"):
                if med in df.columns:
                    out[base] = (med, c)
                    break
    return out


def screen(path, label):
    df = pd.read_csv(path)
    arms = arms_in(df)
    if len(arms) < 2:
        return None
    meds = {a: float(np.nanmedian(df[n])) for a, (m, n) in arms.items()}
    rows = []
    names = list(arms)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            na, nb = meds[a], meds[b]
            if max(na, nb) == 0:
                continue
            rel = abs(na - nb) / max(na, nb)
            da = float(np.nanmedian(df[arms[a][0]]))
            db = float(np.nanmedian(df[arms[b][0]]))
            rows.append(dict(comparison=f"{a} vs {b}", n_a=na, n_b=nb,
                             rel_diff=rel, med_a=da, med_b=db,
                             flag="FLAG" if rel >= THRESH else "close"))
    return label, meds, pd.DataFrame(rows)


def main():
    targets = [
        (EV / "C45/C45_per_chip.csv", "C45 (2x2 factorial: pre, C1, C2, C4, C5)"),
        (EV / "C45/C45_b2_per_chip.csv", "C45 b2 (pre, C1, C2, C3, C4, C5)"),
        (EV / "C45/C45_e1_per_chip.csv", "C45 e1 (C4_e1, C5_e1)"),
        (EV / "C45/C45_sweep_per_chip.csv", "C45 epoch sweep (C4/C5 e1..e10)"),
        (EV / "B1/B1_per_chip.csv", "B1 (epoch sweep C1/C2 vs pre)"),
        (EV / "B2/B2_per_chip.csv", "B2 (band conversions)"),
    ]
    for s in sorted(EV.glob("C45_s*/C45_per_chip.csv")):
        targets.append((s, f"C45 seed replication: {s.parent.name}"))

    flagged_total = 0
    for path, label in targets:
        if not path.is_file():
            print(f"\n### {label}\n  MISSING: {path}")
            continue
        r = screen(path, label)
        if r is None:
            print(f"\n### {label}\n  no arm carries a point count — cannot screen")
            continue
        _, meds, tbl = r
        print(f"\n### {label}")
        print("  median matched points per arm: " +
              "  ".join(f"{a}={v:.0f}" for a, v in meds.items()))
        flags = tbl[tbl.flag == "FLAG"]
        if len(flags) == 0:
            print(f"  ALL {len(tbl)} pairwise comparisons within {THRESH:.0%} — "
                  "no common-support test needed for this package.")
        else:
            flagged_total += len(flags)
            print(f"  {len(flags)}/{len(tbl)} pairwise comparisons at or above "
                  f"{THRESH:.0%}:")
            for _, x in flags.sort_values("rel_diff", ascending=False).iterrows():
                print(f"     {x.comparison:<22s} n {x.n_a:6.0f} vs {x.n_b:6.0f}  "
                      f"({x.rel_diff:5.1%})   med {x.med_a:.3f} vs {x.med_b:.3f} px")
    print(f"\n{'='*74}\nflagged pairwise comparisons overall: {flagged_total}\n{'='*74}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
