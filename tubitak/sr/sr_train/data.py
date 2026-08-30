"""Chip access under the CORRECTED (v2) split.

The corpus ARRAYS are WP3A's and are not rebuilt. `manifest_v2.csv` carries, per chip, both
where its pixels live (`split_v1`, `index_in_split`) and which split it now belongs to
(`split`), so a v2 split is assembled by gathering rows out of the v1 arrays.

Nothing here degrades, normalises or resizes: that is `sr_data.degrade.degrade_chip`,
imported wherever it is needed so the model inverts exactly what the control inverted.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import numpy as np

SR = Path(__file__).resolve().parents[1]
if str(SR) not in sys.path:
    sys.path.insert(0, str(SR))

from sr_data import params as P                                         # noqa: E402
from sr_train import config as C                                        # noqa: E402

V1_SPLITS = ("train", "val", "test", "heldout")


def read_manifest_v2(path=None):
    path = Path(path or (C.data_root() / C.SPLIT_SUBDIR / "manifest_v2.csv"))
    if not path.is_file():
        raise SystemExit(f"data: corrected manifest not found: {path}")
    out = []
    for r in csv.DictReader(open(path)):
        if r.get("kept") != "yes":
            continue
        out.append(r)
    if not out:
        raise SystemExit(f"data: {path} contains no kept chips")
    return out


def load_split(split, manifest=None, corpus=None):
    """(chips uint16 (N,3,256,256), records) for a v2 split, gathered from the v1 arrays."""
    corpus = Path(corpus or (C.data_root() / P.CORPUS_SUBDIR))
    recs = [r for r in read_manifest_v2(manifest) if r["split"] == split]
    if not recs:
        raise SystemExit(f"data: v2 split {split!r} is empty")
    recs.sort(key=lambda r: int(r["index_in_split_v2"]))
    cache, out = {}, np.empty((len(recs), 3, P.CHIP_PX, P.CHIP_PX), np.uint16)
    for k, r in enumerate(recs):
        s1 = r["split_v1"]
        if s1 not in cache:
            cache[s1] = np.load(corpus / f"chips_{s1}.npy", mmap_mode="r")
        out[k] = cache[s1][int(r["index_in_split"])]
    return out, recs


def assert_norm_divisor(value):
    """The registration's divisor, asserted where it is used rather than restated.

    D19: 'the normalisation divisor is asserted against sr_data.params.NORM_DIVISOR_DN, not
    hard-coded a second time'. A training run that silently used a different constant would
    produce metrics that cannot be compared with the registered control, and nothing else in
    the pipeline would notice.
    """
    if float(value) != float(P.NORM_DIVISOR_DN):
        raise SystemExit(
            f"data: normalisation divisor {value} != registered "
            f"{P.NORM_DIVISOR_DN} (sr_data.params.NORM_DIVISOR_DN). Metrics computed with a "
            f"different divisor are not comparable with the registered control.")
    return float(P.NORM_DIVISOR_DN)
