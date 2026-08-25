#!/usr/bin/env python
"""C45 step 4: edge-density ratio in input-silent regions, ALL FIVE ARMS in one
pass (pretrained/C1/C2 from the pkgA BT.601 grays — the B3 artifacts; C4/C5
grayed here with the same BT.601 formula from the C45 warps).

Definition (headline-registrations.md B3 part 3; phase-c-lpips-registration.md):
  input-silent = grad_mag(BT.601 gray of the warped input render) <= 20
  edge         = grad_mag > 20 on the arm's output and on the real chip,
                 evaluated on the SAME input-silent pixels
  per-chip ratio = edge_fraction(fake) / edge_fraction(real)
Edge operator = hallucination_analysis.py's: scipy.ndimage.sobel hypot.
Mask source = the 256-px input PNG warped to the 228 grid (validated against
the committed B3 numbers: C2 0.2177 vs 0.218).

Committed B3 values quoted for continuity: pretrained 1.016, C1 1.023, C2 0.218.
All five arms are recomputed with THIS code so the C4/C5 comparison is
internally exact; both sets are reported.
Registered bands: near 1.0 = mean >= 0.8; well below = mean <= 0.5."""
import json, warnings
from pathlib import Path
import numpy as np

warnings.filterwarnings("ignore")
import rasterio
from scipy.ndimage import sobel

ROOT = Path(__file__).resolve().parents[3]
C45 = ROOT / "tubitak/data/tool_runs/C45"
PKGA = ROOT / "tubitak/data/tool_runs/pkgA/gray"
THRESH = 20.0


def grad_mag(g):
    return np.hypot(sobel(g.astype(float), 0), sobel(g.astype(float), 1))


def bt601(rgb):  # (3,H,W) uint8 -> (H,W) uint8
    return np.round(0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]).astype(np.uint8)


def read1(p):
    with rasterio.open(p) as s:
        a = s.read()
    return a[0] if a.shape[0] == 1 else bt601(a)


stems = sorted(p.name[:-4] for p in (ROOT / "tubitak/data/ankara/run/inputs").glob("*.png"))
assert len(stems) == 130

ARMS = {
    "pretrained": lambda st: PKGA / f"ank130/pretrained/bt601/{st}.tif",
    "C1": lambda st: PKGA / f"ank130/C1/bt601/{st}.tif",
    "C2": lambda st: PKGA / f"ank130/C2/bt601/{st}.tif",
    "C4": lambda st: C45 / f"warp/C4/{st}.tif",
    "C5": lambda st: C45 / f"warp/C5/{st}.tif",
}

rows, skipped = [], []
for st in stems:
    with rasterio.open(C45 / f"warp/input/{st}.tif") as s:
        mask = grad_mag(bt601(s.read())) <= THRESH
    r = read1(PKGA / f"ref_ank/bt601/{st}.tif")
    r_edge = float((grad_mag(r)[mask] > THRESH).mean()) if mask.any() else 0.0
    if not mask.any() or r_edge == 0.0:
        skipped.append(st)
        continue
    row = {"stem": st, "silent_frac": float(mask.mean()), "ref_edge": r_edge}
    for arm, pf in ARMS.items():
        f = read1(pf(st))
        row[arm] = float((grad_mag(f)[mask] > THRESH).mean()) / r_edge
    rows.append(row)

import pandas as pd
df = pd.DataFrame(rows)
df.to_csv(C45 / "C45_edge_ratio.csv", index=False)

committed = {"pretrained": 1.016, "C1": 1.023, "C2": 0.218}
summary = {"n_chips": len(df), "skipped_zero_ref": skipped,
           "mask": "input PNG warped to 228 grid, BT.601, sobel<=20",
           "committed_B3": committed, "bands": "near 1.0: mean>=0.8; well below: mean<=0.5",
           "arms": {}}
print(f"edge-density ratio in input-silent regions, n={len(df)} (skipped {len(skipped)})")
print(f"{'arm':<11} {'mean':>7} {'median':>7} {'q25':>7} {'q75':>7}  band")
for arm in ARMS:
    v = df[arm]
    band = "near 1.0" if v.mean() >= 0.8 else ("well below" if v.mean() <= 0.5 else "intermediate")
    summary["arms"][arm] = dict(mean=round(float(v.mean()), 4), median=round(float(v.median()), 4),
                                q25=round(float(v.quantile(.25)), 4), q75=round(float(v.quantile(.75)), 4),
                                band=band, committed=committed.get(arm))
    print(f"{arm:<11} {v.mean():>7.4f} {v.median():>7.4f} {v.quantile(.25):>7.4f} {v.quantile(.75):>7.4f}  {band}")

with open(C45 / "C45_edge_summary.json", "w") as f:
    json.dump(summary, f, indent=2)
print(f"wrote {C45/'C45_edge_ratio.csv'} and {C45/'C45_edge_summary.json'}")
