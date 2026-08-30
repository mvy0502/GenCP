"""Geographic block splits with an enforced buffer — D11.

A random chip split leaks: neighbouring chips of one granule, taken minutes apart on the same
pass over the same landform under the same illumination, are close to duplicates of each
other, and a model that has memorised one has effectively seen the other. Splitting by
contiguous spatial blocks is the standard remedy; the buffer is what makes it honest at the
block boundaries, where two adjacent chips would otherwise sit in different splits with
nothing between them.

Chips here do not overlap (stride == chip size), so the buffer is not guarding against shared
pixels. It guards against spatial autocorrelation, which does not stop at a pixel boundary.
"""
from __future__ import annotations

import hashlib

import numpy as np

from .params import (BLOCK_CHIPS, BLOCKS_PER_GRANULE, CHIP_M, HELDOUT_GRANULE,
                     SPLIT_BUFFER_M, SPLIT_SEED)

#: Split labels. `heldout` is the whole-granule test set and never mixes with `test`.
SPLITS = ("train", "val", "test", "heldout")


def block_of(chip_row, chip_col, block_chips=BLOCK_CHIPS):
    return int(chip_row) // block_chips, int(chip_col) // block_chips


def granule_seed(granule, seed=SPLIT_SEED):
    """A stable per-granule seed. NOT `hash()`.

    Python's `hash()` of a str is salted per process (PYTHONHASHSEED), so a seed derived
    from it changes on every run. The first version of this module used
    `abs(hash((seed, granule)))` and was caught by comparing a `--dry-run` against the real
    build: the two disagreed, train 3747 against 3680, from the same code, the same data and
    the same registered seed. The registration claims the assignment is deterministic given
    (granule, seed); with `hash()` it was not, and nothing in the output said so — the counts
    simply differed between two runs nobody would normally compare.

    SHA-256 of the seed and the granule name is stable across processes, machines and Python
    versions.
    """
    h = hashlib.sha256(f"{int(seed)}:{granule}".encode("utf-8")).digest()
    return int.from_bytes(h[:8], "big")


def assign_blocks(granule, n_blocks_row, n_blocks_col, seed=SPLIT_SEED,
                  per_granule=BLOCKS_PER_GRANULE):
    """{(block_row, block_col): split} for one training granule.

    Deterministic given (granule, seed): the granule name is folded into the seed via
    `granule_seed` so that two granules do not receive the identical block pattern, which
    would put every split boundary at the same place in every granule.
    """
    rng = np.random.default_rng(granule_seed(granule, seed))
    blocks = [(r, c) for r in range(n_blocks_row) for c in range(n_blocks_col)]
    want = sum(per_granule.values())
    if len(blocks) != want:
        raise ValueError(
            f"{granule}: {n_blocks_row}x{n_blocks_col} = {len(blocks)} blocks but "
            f"BLOCKS_PER_GRANULE sums to {want}. The grid must divide exactly; 42 chips "
            f"and {BLOCK_CHIPS}-chip blocks give 3x3=9.")
    labels = ([("train")] * per_granule["train"] + ["val"] * per_granule["val"]
              + ["test"] * per_granule["test"])
    order = rng.permutation(len(blocks))
    return {blocks[i]: labels[k] for k, i in enumerate(order)}


def split_for_chip(granule, chip_row, chip_col, block_assignment):
    if granule == HELDOUT_GRANULE:
        return "heldout"
    return block_assignment[granule][block_of(chip_row, chip_col)]


def buffer_violations(records, buffer_m=SPLIT_BUFFER_M, chip_m=CHIP_M):
    """Chips within `buffer_m` of a chip in a DIFFERENT split, within the same granule.

    `records` is a list of dicts with `granule`, `chip_row`, `chip_col`, `split`.
    Distance is Chebyshev in metres between chip north-west corners, which for a
    non-overlapping grid of `chip_m` chips equals `chip_m * Chebyshev distance in chips`.
    Returns the set of record indices that must be dropped.

    Granules are disjoint footprints in this corpus only up to the ~9.8 km granule overlap
    measured in `00-recon.md`; the buffer is applied WITHIN a granule, and the separate
    cross-granule overlap question is handled by `heldout` being a whole granule and by the
    open items.
    """
    reach = int(np.ceil(buffer_m / chip_m))
    by_granule = {}
    for i, r in enumerate(records):
        by_granule.setdefault(r["granule"], {})[(r["chip_row"], r["chip_col"])] = (i,
                                                                                  r["split"])
    drop = set()
    for g, cells in by_granule.items():
        for (rr, cc), (i, s) in cells.items():
            for dr in range(-reach, reach + 1):
                for dc in range(-reach, reach + 1):
                    if dr == 0 and dc == 0:
                        continue
                    other = cells.get((rr + dr, cc + dc))
                    if other is not None and other[1] != s:
                        drop.add(i)
                        break
                else:
                    continue
                break
    return drop
