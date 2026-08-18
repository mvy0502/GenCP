#!/usr/bin/env python
"""Does the generator invent structure the OSM input does not describe?

GenCP's premise is that a generated chip inherits known coordinates and is then
matched against real imagery. An invented edge is a **false control point**:
matching can lock onto structure that does not exist on the ground and return a
confident wrong position. Visual realism and GCP fitness pull in opposite
directions here.

The diagnostic
--------------
Two quantities per chip, measured against the real satellite half:

* **edge-density ratio** generated / real - is the output as *busy* as reality?
* **gradient correlation** generated vs real - do its edges land in *real places*?

The failure signature is the combination: a chip where the generator produces as
much structure as reality (ratio near 1) but that structure is uncorrelated with
reality (correlation near chance) is a chip full of confident, wrong control
points. Either number alone is uninformative.

Chance level is measured, not assumed: gradient correlation between each
generated chip and a *different* chip's real satellite half gives the floor that
"uncorrelated" actually means for this data.

OSM information-content scores (three, because they capture different things)
-----------------------------------------------------------------------------
* **edge density** - fraction of pixels on a class boundary. Directly measures the
  boundary structure the generator can legitimately place.
* **class count** - distinct landcover colours covering >=0.1 % of the chip.
  Semantic richness, independent of geometry: two classes in a simple layout
  differ from eight.
* **non-dominant fraction** - 1 - (share of the most common colour). A chip that is
  95 % uniform green carries almost no information however many rare classes it
  technically contains; this captures how much of the chip is not background.

Usage
-----
    python tubitak/scripts/hallucination_analysis.py \\
        --figure tubitak/docs/figures/hallucination-analysis.png
"""
from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from shift_estimator import ncc_shift, prepare  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "tubitak" / "data" / "scale_test"
GEN = BASE / "out_a/genCP_HR_RGB_model/test_latest/images"


def read(path):
    import rasterio
    from rasterio.errors import NotGeoreferencedWarning
    warnings.filterwarnings("ignore", category=NotGeoreferencedWarning)
    with rasterio.open(path) as s:
        return np.transpose(s.read(), (1, 2, 0)).astype(float)


def grad_mag(img):
    from scipy.ndimage import sobel
    g = img.mean(axis=2) if img.ndim == 3 else img
    return np.hypot(sobel(g, 0), sobel(g, 1))


def edge_density(img, thresh=20.0):
    """Fraction of pixels whose gradient magnitude exceeds `thresh` DN."""
    return float((grad_mag(img) > thresh).mean())


def grad_corr(a, b):
    A, B = grad_mag(a).ravel(), grad_mag(b).ravel()
    if A.std() < 1e-9 or B.std() < 1e-9:
        return np.nan
    return float(np.corrcoef(A, B)[0, 1])


def osm_scores(osm, min_share=0.001):
    px = osm.reshape(-1, osm.shape[2]).astype(np.uint8)
    colours, counts = np.unique(px, axis=0, return_counts=True)
    share = counts / counts.sum()
    return dict(
        edge_density=edge_density(osm),
        class_count=int((share >= min_share).sum()),
        non_dominant=float(1.0 - share.max()),
    )


def local_match_failures(gen, real, grid=4, win=64, tol=2.0, max_shift=8):
    """Fraction of local windows whose generated->real registration is implausible.

    This is closer to what KARIOS actually does than a global correlation: it
    matches local features. Both images depict the SAME ground, so a correct match
    returns a shift near zero. A window returning a large shift has locked onto
    structure that does not correspond - a false control point, which is exactly
    the GCP failure mode.
    """
    from scipy.ndimage import gaussian_filter
    R = gaussian_filter(prepare(real, "gradient"), 1.0)
    G = gaussian_filter(prepare(gen, "gradient"), 1.0)
    step = R.shape[0] // grid
    bad = tot = 0
    mags = []
    for i in range(grid):
        for j in range(grid):
            r0 = i * step + (step - win) // 2
            c0 = j * step + (step - win) // 2
            dy, dx, _ = ncc_shift(R[r0:r0 + win, c0:c0 + win],
                                  G[r0:r0 + win, c0:c0 + win], max_shift=max_shift)
            if not np.isfinite(dy):
                continue
            m = float(np.hypot(dy, dx))
            mags.append(m)
            tot += 1
            if m > tol:
                bad += 1
    return (bad / tot if tot else np.nan), (float(np.median(mags)) if mags else np.nan)


def spearman(x, y):
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = x[ok], y[ok]
    rx = np.argsort(np.argsort(x)).astype(float)
    ry = np.argsort(np.argsort(y)).astype(float)
    return float(np.corrcoef(rx, ry)[0, 1]), len(x)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--figure", default=None)
    ap.add_argument("--edge-threshold", type=float, default=20.0)
    ap.add_argument("--per-chip", action="store_true")
    a = ap.parse_args()

    stems = sorted(f.name[:-9] for f in GEN.glob("*_fake.png"))
    if not stems:
        sys.exit(f"no generated chips in {GEN}")

    rows = []
    for st in stems:
        osm = read(BASE / "inputs_a" / f"{st}.png")
        real = read(BASE / "refs_a" / f"{st}.png")
        gen = read(GEN / f"{st}_fake.png")
        s = osm_scores(osm)
        s.update(stem=st,
                 gen_edges=edge_density(gen, a.edge_threshold),
                 real_edges=edge_density(real, a.edge_threshold),
                 osm_edges_t=edge_density(osm, a.edge_threshold),
                 fidelity=grad_corr(gen, real))
        s["busy_ratio"] = s["gen_edges"] / s["real_edges"] if s["real_edges"] > 0 else np.nan
        s["fail_rate"], s["median_shift"] = local_match_failures(gen, real)
        rows.append(s)

    # measured chance floor: generated chip vs a DIFFERENT chip's real half
    rng = np.random.default_rng(0)
    chance = []
    for i, st in enumerate(stems):
        j = int(rng.choice([k for k in range(len(stems)) if k != i]))
        chance.append(grad_corr(read(GEN / f"{st}_fake.png"),
                                read(BASE / "refs_a" / f"{stems[j]}.png")))
    chance = np.array(chance, float)
    chance_mu, chance_sd = float(np.nanmean(chance)), float(np.nanstd(chance))

    info = {k: np.array([r[k] for r in rows], float)
            for k in ("edge_density", "class_count", "non_dominant")}
    fid = np.array([r["fidelity"] for r in rows], float)
    busy = np.array([r["busy_ratio"] for r in rows], float)
    gen_e = np.array([r["gen_edges"] for r in rows], float)
    osm_e = np.array([r["osm_edges_t"] for r in rows], float)

    print("=" * 78)
    print(f"HALLUCINATION ANALYSIS — {len(rows)} held-out chips")
    print("=" * 78)
    print(f"edge threshold {a.edge_threshold:g} DN")
    print(f"measured chance floor for gradient correlation: "
          f"{chance_mu:+.4f} +/- {chance_sd:.4f}\n")

    if a.per_chip:
        print(f"{'chip':<18}{'OSMedge':>9}{'classes':>9}{'nondom':>9}"
              f"{'genEdge':>9}{'realEdge':>9}{'ratio':>8}{'fidelity':>10}")
        print("-" * 78)
        for r in sorted(rows, key=lambda r: r["edge_density"]):
            print(f"{r['stem']:<18}{r['edge_density']:>9.4f}{r['class_count']:>9}"
                  f"{r['non_dominant']:>9.4f}{r['gen_edges']:>9.4f}"
                  f"{r['real_edges']:>9.4f}{r['busy_ratio']:>8.3f}{r['fidelity']:>10.4f}")
        print()

    print("--- 1. does OSM information content predict fidelity? ---")
    print(f"{'info score':<20}{'Spearman rho':>14}{'n':>5}")
    print("-" * 42)
    for k, v in info.items():
        rho, n = spearman(v, fid)
        print(f"{k:<20}{rho:>14.4f}{n:>5}")

    print("\n--- 2. invention: output structure vs input structure ---")
    print(f"OSM edge density      mean {osm_e.mean():.4f}")
    print(f"generated edge density mean {gen_e.mean():.4f}   "
          f"({gen_e.mean()/max(osm_e.mean(),1e-9):.1f}x the OSM input)")
    print(f"generated / real busy ratio  mean {np.nanmean(busy):.3f}  "
          f"median {np.nanmedian(busy):.3f}")

    print("\n--- 3. the diagnostic: split by OSM information content ---")
    med = np.median(info["edge_density"])
    lo = info["edge_density"] <= med
    hi = ~lo
    print(f"split at median OSM edge density = {med:.4f}\n")
    print(f"{'group':<22}{'n':>4}{'OSMedge':>10}{'busy ratio':>12}"
          f"{'fidelity':>10}{'vs chance':>11}")
    print("-" * 70)
    for name, m in [("LOW information", lo), ("HIGH information", hi)]:
        f_ = fid[m]
        z = (np.nanmean(f_) - chance_mu) / (chance_sd / np.sqrt(m.sum()) + 1e-12)
        print(f"{name:<22}{m.sum():>4}{info['edge_density'][m].mean():>10.4f}"
              f"{np.nanmean(busy[m]):>12.3f}{np.nanmean(f_):>10.4f}{z:>10.1f}s")
    print("\n('vs chance' is how many standard errors the group's mean fidelity sits")
    print(" above the measured chance floor.)")

    fail = np.array([r["fail_rate"] for r in rows], float)
    mshift = np.array([r["median_shift"] for r in rows], float)
    print("\n--- 3b. LOCAL match failures (closer to what KARIOS does) ---")
    print("A window is a 'failure' if generated->real registration returns >2 px,")
    print("since both depict the same ground and a correct match returns ~0.")
    print(f"mean failure rate      : {np.nanmean(fail):.3f} of windows")
    print(f"median local shift     : {np.nanmedian(mshift):.3f} px")
    for k, v in info.items():
        rho, n = spearman(v, fail)
        print(f"  Spearman rho({k:<13} , failure rate) = {rho:+.4f}")
    print(f"{'group':<22}{'n':>4}{'failure rate':>14}{'median shift':>14}")
    print("-" * 56)
    for name, m in [("LOW information", lo), ("HIGH information", hi)]:
        print(f"{name:<22}{m.sum():>4}{np.nanmean(fail[m]):>14.3f}{np.nanmedian(mshift[m]):>14.3f}")

    print("\n--- 4. is there a usable threshold? ---")
    qs = np.quantile(info["edge_density"], [0.2, 0.4, 0.6, 0.8])
    print(f"{'OSM edge density bin':<26}{'n':>4}{'mean fidelity':>15}{'busy ratio':>12}"
          f"{'fail rate':>14}")
    print("-" * 74)
    edges = [-np.inf] + list(qs) + [np.inf]
    for i in range(len(edges) - 1):
        m = (info["edge_density"] > edges[i]) & (info["edge_density"] <= edges[i + 1])
        if m.sum() == 0:
            continue
        lab = f"{max(edges[i],0):.4f} - {min(edges[i+1], info['edge_density'].max()):.4f}"
        print(f"{lab:<26}{m.sum():>4}{np.nanmean(fid[m]):>15.4f}{np.nanmean(busy[m]):>12.3f}"
              f"{np.nanmean(fail[m]):>14.3f}")

    if a.figure:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(2, 3, figsize=(16.5, 9.2))
        labels = {"edge_density": "OSM edge density",
                  "class_count": "OSM landcover classes",
                  "non_dominant": "OSM non-dominant fraction"}

        # row 1 — global fidelity (the metric that finds nothing)
        for ax, k in zip(axes[0], labels):
            ax.scatter(info[k], fid, s=44, c="#c1443c", edgecolor="k", linewidth=0.5, zorder=3)
            ax.axhline(chance_mu, color="0.35", ls="--", lw=1.4, zorder=2,
                       label=f"chance ({chance_mu:+.3f})")
            ax.axhspan(chance_mu - chance_sd, chance_mu + chance_sd, color="0.6",
                       alpha=0.25, zorder=1)
            rho, _ = spearman(info[k], fid)
            ax.set_xlabel(labels[k]); ax.set_ylabel("global gradient correlation")
            ax.set_title(f"GLOBAL fidelity vs {labels[k]}\nSpearman rho = {rho:+.3f}  (no trend)",
                         fontsize=10)
            ax.grid(alpha=0.3, ls=":"); ax.legend(fontsize=8, loc="lower right")

        # row 2 — invention, and the local metric that does find the trend
        ax = axes[1][0]
        ax.scatter(info["edge_density"], busy, s=44, c="#2b6cb0",
                   edgecolor="k", linewidth=0.5, zorder=3)
        ax.axhline(1.0, color="0.35", ls="--", lw=1.4, label="as busy as reality")
        ax.set_xlabel("OSM edge density"); ax.set_ylabel("generated / real edge density")
        ax.set_title(f"INVENTION: output busyness\nmean ratio {np.nanmean(busy):.3f} "
                     f"regardless of input", fontsize=10)
        ax.grid(alpha=0.3, ls=":"); ax.legend(fontsize=8, loc="lower right")

        ax = axes[1][1]
        ax.scatter(info["non_dominant"], fail, s=44, c="#7b3f9d",
                   edgecolor="k", linewidth=0.5, zorder=3)
        rho, _ = spearman(info["non_dominant"], fail)
        ax.set_xlabel("OSM non-dominant fraction")
        ax.set_ylabel("local match failure rate")
        ax.set_title(f"LOCAL match failure vs information\nSpearman rho = {rho:+.3f}",
                     fontsize=10)
        ax.grid(alpha=0.3, ls=":")

        ax = axes[1][2]
        qs = np.quantile(info["edge_density"], [0.2, 0.4, 0.6, 0.8])
        edges = [-np.inf] + list(qs) + [np.inf]
        cents, vals = [], []
        for i in range(len(edges) - 1):
            m = (info["edge_density"] > edges[i]) & (info["edge_density"] <= edges[i + 1])
            if m.sum():
                cents.append(f"Q{i+1}"); vals.append(np.nanmean(fail[m]))
        ax.bar(cents, vals, color="#7b3f9d", edgecolor="k")
        ax.axhline(0.5, color="crimson", ls="--", lw=1.4, label="half of windows fail")
        ax.set_ylim(0, 1)
        ax.set_xlabel("OSM edge density quintile (low -> high)")
        ax.set_ylabel("local match failure rate")
        ax.set_title("Failure rate by quintile\nfalls with information, never becomes safe",
                     fontsize=10)
        ax.grid(alpha=0.3, ls=":", axis="y"); ax.legend(fontsize=8)

        fig.suptitle("Does the generator invent structure, and does it matter? — "
                     f"{len(rows)} held-out chips", fontsize=13)
        fig.tight_layout()
        Path(a.figure).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(a.figure, dpi=150, bbox_inches="tight")
        print(f"\nfigure -> {a.figure}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
