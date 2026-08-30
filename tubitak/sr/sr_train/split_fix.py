"""D13 — the corrected split: cross-granule dedup, then a corpus-wide buffer.

Reads the WP3A manifest, writes a corrected one. **The chip ARRAYS are not rebuilt**: the
corpus's uint16 targets are exactly WP3A's, and only the `split` column changes, plus a
`kept` column recording why a chip left the corpus. That is what makes the WP3A and WP3B
control numbers comparable chip-for-chip where the chips coincide.

Geometry, once: a chip with north-west corner (e, n) occupies [e, e+CHIP_M] x [n-CHIP_M, n]
in EPSG:32636. All five granules are in that CRS, so map coordinates are directly
comparable and no reprojection happens anywhere in this file.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

SR = Path(__file__).resolve().parents[1]
if str(SR) not in sys.path:
    sys.path.insert(0, str(SR))

from sr_data import splits as S                                        # noqa: E402
from sr_train import config as C                                       # noqa: E402


def footprints(recs):
    """(N,4) array of [e0, n0, e1, n1] with e0<e1, n0<n1, in metres."""
    e = np.array([r["e"] for r in recs], float)
    n = np.array([r["n"] for r in recs], float)
    return np.stack([e, n - C.CHIP_M, e + C.CHIP_M, n], axis=1)


def separation(a, B):
    """Chebyshev gap in metres between footprint `a` (4,) and each row of `B` (N,4).

    0 for overlapping or touching rectangles; positive for disjoint ones. This is the
    generalisation of WP3A's within-granule Chebyshev-in-chips rule to unaligned grids:
    two aligned adjacent chips give 0, two chips one gap apart give exactly CHIP_M.
    """
    gap_x = np.maximum(a[0] - B[:, 2], B[:, 0] - a[2])
    gap_y = np.maximum(a[1] - B[:, 3], B[:, 1] - a[3])
    return np.maximum(0.0, np.maximum(gap_x, gap_y))


def load_manifest(path):
    recs = []
    for i, r in enumerate(csv.DictReader(open(path))):
        r["e"] = float(r["easting"]); r["n"] = float(r["northing"])
        r["chip_row"] = int(r["chip_row"]); r["chip_col"] = int(r["chip_col"])
        r["row_index"] = i
        recs.append(r)
    if not recs:
        raise SystemExit(f"split_fix: {path} has no rows - nothing to split")
    return recs


# --------------------------------------------------------------------------- step one
def deduplicate(recs, order=C.DEDUP_ORDER):
    """Keep one chip per patch of ground. Returns (kept_flags, stats).

    Granules in `order`; a chip is dropped iff its footprint overlaps a chip already KEPT
    from an earlier granule. Overlap is positive-area intersection, i.e. separation == 0
    with a strict inequality on both axes.
    """
    unknown = sorted({r["granule"] for r in recs} - set(order))
    if unknown:
        raise SystemExit(f"split_fix: granule(s) {unknown} absent from DEDUP_ORDER")
    by_g = defaultdict(list)
    for r in recs:
        by_g[r["granule"]].append(r)

    keep = np.ones(len(recs), bool)
    kept_fp = np.zeros((0, 4))          # footprints kept so far
    kept_owner = []                     # granule that owns each kept footprint
    stats = {}
    for g in order:
        rs = by_g.get(g, [])
        if not rs:
            stats[g] = dict(n=0, dropped=0, dropped_against={})
            continue
        fp = footprints(rs)
        owner = np.array(kept_owner)
        dropped, against, keep_here = 0, defaultdict(int), []
        for k, r in enumerate(rs):
            if len(kept_fp):
                # strict overlap: positive-area intersection with anything already kept
                ov = ((fp[k, 0] < kept_fp[:, 2]) & (kept_fp[:, 0] < fp[k, 2])
                      & (fp[k, 1] < kept_fp[:, 3]) & (kept_fp[:, 1] < fp[k, 3]))
                if ov.any():
                    keep[r["row_index"]] = False
                    dropped += 1
                    for gg in owner[ov]:
                        against[str(gg)] += 1
                    continue
            keep_here.append(k)
        stats[g] = dict(n=len(rs), dropped=dropped, dropped_against=dict(against))
        if keep_here:
            new_fp = fp[keep_here]
            kept_fp = np.vstack([kept_fp, new_fp]) if len(kept_fp) else new_fp
            kept_owner.extend([g] * len(keep_here))
    return keep, stats


# --------------------------------------------------------------------------- step two
def assign_blocks_yield_aware(granule, block_counts, seed=C.SPLIT_SEED):
    """{(br,bc): split} using only blocks with >= MIN_BLOCK_CHIPS_FOR_EVAL chips for eval."""
    blocks = sorted(block_counts)
    eligible = [b for b in blocks if block_counts[b] >= C.MIN_BLOCK_CHIPS_FOR_EVAL]
    need = C.BLOCKS_PER_GRANULE["val"] + C.BLOCKS_PER_GRANULE["test"]
    if len(eligible) < need:
        raise SystemExit(
            f"split_fix: {granule} has only {len(eligible)} block(s) with "
            f">= {C.MIN_BLOCK_CHIPS_FOR_EVAL} chips, needs {need} for val+test. "
            f"Yields: {sorted(block_counts.values(), reverse=True)}")
    rng = np.random.default_rng(S.granule_seed(granule, seed))
    order = rng.permutation(len(eligible))
    out = {b: "train" for b in blocks}
    out[eligible[order[0]]] = "val"
    out[eligible[order[1]]] = "test"
    return out, eligible


def buffer_drop_corpus_wide(recs, buffer_m=C.SPLIT_BUFFER_M):
    """Indices (into `recs`) of chips within `buffer_m` of a chip in a DIFFERENT split.

    Corpus-wide: granule is not consulted. O(n^2) over ~6000 chips is a few seconds and is
    preferred here over a spatial index, because the whole point of this function is that it
    is obviously correct.
    """
    fp = footprints(recs)
    sp = np.array([r["split"] for r in recs])
    drop = set()
    for i in range(len(recs)):
        sep = separation(fp[i], fp)
        near = (sep < buffer_m)
        near[i] = False
        if (sp[near] != sp[i]).any():
            drop.add(i)
    return drop


def build(manifest_in, out_dir, dry_run=False):
    recs = load_manifest(manifest_in)
    n0 = len(recs)
    # Preserve where the chip's PIXELS live. The arrays chips_<split>.npy are indexed by the
    # WP3A split and its index_in_split; overwriting `split` in place would make the pixels
    # unfindable from this manifest, which is how the first version of this file was wrong.
    for r in recs:
        r["split_v1"] = r["split"]

    keep, dedup_stats = deduplicate(recs)
    surv = [r for r, k in zip(recs, keep) if k]
    for r, k in zip(recs, keep):
        r["kept"] = "yes" if k else "dropped_dedup"

    # block yields AFTER dedup, per granule
    yields = defaultdict(lambda: defaultdict(int))
    for r in surv:
        yields[r["granule"]][S.block_of(r["chip_row"], r["chip_col"])] += 1

    assignment, eligible_by_g = {}, {}
    for g in sorted(yields):
        if g == C.HELDOUT_GRANULE:
            continue
        full = {(br, bc): yields[g].get((br, bc), 0) for br in range(3) for bc in range(3)}
        assignment[g], eligible_by_g[g] = assign_blocks_yield_aware(g, full)

    for r in surv:
        r["split"] = ("heldout" if r["granule"] == C.HELDOUT_GRANULE
                      else assignment[r["granule"]][S.block_of(r["chip_row"], r["chip_col"])])

    drop_idx = buffer_drop_corpus_wide(surv)
    for i, r in enumerate(surv):
        if i in drop_idx:
            r["kept"] = "dropped_buffer"
    final = [r for i, r in enumerate(surv) if i not in drop_idx]

    counts = defaultdict(int)
    per_granule = defaultdict(lambda: defaultdict(int))
    for r in final:
        counts[r["split"]] += 1
        per_granule[r["granule"]][r["split"]] += 1
    for s in ("train", "val", "test", "heldout"):
        idx = 0
        for r in final:
            if r["split"] == s:
                r["index_in_split_v2"] = idx; idx += 1

    summary = dict(
        work_package="P2-WP3B", source_manifest=str(manifest_in),
        n_in=n0, dedup_dropped=int((~keep).sum()), dedup_per_granule=dedup_stats,
        min_block_chips_for_eval=C.MIN_BLOCK_CHIPS_FOR_EVAL,
        dedup_order=list(C.DEDUP_ORDER),
        block_yields_after_dedup={g: {f"{b[0]},{b[1]}": v for b, v in sorted(d.items())}
                                  for g, d in yields.items()},
        eligible_blocks={g: [f"{b[0]},{b[1]}" for b in e] for g, e in eligible_by_g.items()},
        block_assignment={g: {f"{b[0]},{b[1]}": s for b, s in sorted(a.items())}
                          for g, a in assignment.items()},
        buffer_dropped=len(drop_idx), buffer_m=C.SPLIT_BUFFER_M,
        counts=dict(counts),
        per_granule={g: dict(d) for g, d in per_granule.items()},
        n_out=len(final), split_seed=C.SPLIT_SEED,
    )
    if dry_run:
        return summary, None

    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    cols = [c for c in recs[0] if c not in ("e", "n", "row_index")]
    if "kept" not in cols:
        cols.append("kept")
    if "index_in_split_v2" not in cols:
        cols.append("index_in_split_v2")
    with open(out_dir / "manifest_v2.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in recs:
            r.setdefault("index_in_split_v2", "")
            w.writerow(r)
    (out_dir / "split_v2.json").write_text(json.dumps(summary, indent=2, sort_keys=True))
    return summary, out_dir


def main():
    ap = argparse.ArgumentParser(prog="split_fix.py", description=__doc__)
    ap.add_argument("--manifest", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    mi = Path(a.manifest or (C.data_root() / C.CORPUS_SUBDIR / "manifest.csv"))
    out = Path(a.out or (C.data_root() / C.SPLIT_SUBDIR))
    if not mi.is_file():
        raise SystemExit(f"split_fix: manifest not found: {mi}")
    s, d = build(mi, out, dry_run=a.dry_run)
    print(json.dumps({k: v for k, v in s.items()
                      if k not in ("block_yields_after_dedup", "block_assignment",
                                   "eligible_blocks", "dedup_per_granule")}, indent=2))
    print("\ndedup per granule:")
    for g in C.DEDUP_ORDER:
        st = s["dedup_per_granule"].get(g, {})
        print(f"  {g}: {st.get('n',0)} chips, dropped {st.get('dropped',0)}"
              f"  against {st.get('dropped_against',{})}")
    print("\nper granule x split (final):")
    for g in sorted(s["per_granule"]):
        print(f"  {g}: {dict(s['per_granule'][g])}")
    if d:
        print(f"\nwritten to {d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
