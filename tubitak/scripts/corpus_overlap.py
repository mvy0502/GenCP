#!/usr/bin/env python
"""Is the demo site in the GenCP HR training corpus?

Answers whether demo results should be read as in-distribution or held out, by
comparing chip names between the demo dataset and the downloaded training corpus.
Reports the MGRS tile distribution, tile-level presence, and — the question that
actually matters — **exact chip-name overlap**, since two chips in the same MGRS
tile are different places.

Also checks whether the corpus's own train/test splits are disjoint.

Usage
-----
    python tubitak/scripts/corpus_overlap.py
    python tubitak/scripts/corpus_overlap.py --top 20
"""
from __future__ import annotations

import argparse
import collections
import glob
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEF_DEMO = ROOT / "GenCP_HR_demo" / "data" / "dataset" / "test"
DEF_CORPUS = ROOT / "tubitak" / "data" / "GenCP_HR_DB" / "image_pairs"
DEF_PROCESSED = ROOT / "GenCP_HR_demo" / "data" / "GenCP_DB"


def stems(pattern):
    return {os.path.basename(f)[:-4] for f in glob.glob(pattern)}


def tile(stem):
    return stem.split("_")[0]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--demo", default=str(DEF_DEMO))
    ap.add_argument("--corpus", default=str(DEF_CORPUS))
    ap.add_argument("--processed", default=str(DEF_PROCESSED))
    ap.add_argument("--top", type=int, default=15, help="tiles to list in the distribution")
    a = ap.parse_args()

    tr = stems(f"{a.corpus}/train/*.tif")
    te = stems(f"{a.corpus}/test/*.tif")
    if not tr:
        sys.exit(f"training corpus not found under {a.corpus}\n"
                 f"download GenCP_HR_DB.zip from https://zenodo.org/records/15044428 "
                 f"into tubitak/data/ (gitignored)")
    demo = stems(f"{a.demo}/*.tif")
    proc = stems(f"{a.processed}/*.tif")

    tiles = collections.Counter(tile(s) for s in tr | te)
    total = sum(tiles.values())
    print("=" * 66)
    print("MGRS TILE DISTRIBUTION ACROSS THE CORPUS")
    print("=" * 66)
    print(f"chips: {len(tr)} train + {len(te)} test = {total}   distinct tiles: {len(tiles)}\n")
    print(f"{'tile':<10}{'chips':>8}{'share':>9}")
    print("-" * 30)
    for t, n in tiles.most_common(a.top):
        print(f"{t:<10}{n:>8}{100*n/total:>8.2f}%")
    rest = len(tiles) - a.top
    if rest > 0:
        shown = sum(n for _, n in tiles.most_common(a.top))
        print(f"{f'+{rest} more':<10}{total-shown:>8}{100*(total-shown)/total:>8.2f}%")

    print("\n" + "=" * 66)
    print("EXACT CHIP-NAME OVERLAP (not merely tile-level)")
    print("=" * 66)
    print(f"demo dataset chips        : {len(demo)}")
    print(f"  also in corpus train    : {len(demo & tr)}")
    print(f"  also in corpus test     : {len(demo & te)}")
    print(f"  in neither              : {len(demo - tr - te)}")

    print(f"\n{'tile':<9}{'demo':>7}{'in train':>10}{'in test':>9}{'overlap':>9}")
    print("-" * 44)
    for t in sorted({tile(s) for s in demo}):
        d = {s for s in demo if tile(s) == t}
        print(f"{t:<9}{len(d):>7}{len(d & tr):>10}{len(d & te):>9}{len(d & (tr | te)):>9}")

    if proc:
        print("\n" + "=" * 66)
        print("THE CHIPS ACTUALLY PROCESSED")
        print("=" * 66)
        pt = collections.Counter(tile(s) for s in proc)
        print(f"processed          : {len(proc)}   tiles: {dict(pt)}")
        print(f"  in corpus train  : {len(proc & tr)}")
        print(f"  in corpus test   : {len(proc & te)}")
        held_out = not (proc & (tr | te))
        print(f"\nVERDICT: the processed chips are "
              f"{'HELD OUT (out-of-distribution)' if held_out else 'PARTLY IN-DISTRIBUTION'}.")
        if held_out:
            print("  Observed behaviour is genuine generalisation, not memorisation.")

    leak = tr & te
    print("\n" + "=" * 66)
    print("ARE THE CORPUS'S OWN SPLITS DISJOINT?")
    print("=" * 66)
    print(f"train {len(tr)}, test {len(te)}, intersection {len(leak)}"
          f"{'  <- the published test split is NOT strictly held out' if leak else '  (clean)'}")
    if leak:
        print("  examples:", sorted(leak)[:5])
    return 0


if __name__ == "__main__":
    sys.exit(main())
