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
    corpus = Path(corpus or (C.data_root() / C.CORPUS_SUBDIR))
    recs = [r for r in read_manifest_v2(manifest) if r["split"] == split]
    if not recs:
        raise SystemExit(f"data: v2 split {split!r} is empty")
    recs.sort(key=lambda r: int(r["index_in_split_v2"]))

    # Two corpus layouts, told apart by a marker file rather than by a guess:
    #  * WP3A/WP3B arrays are indexed by the ORIGINAL split and index_in_split, so a v2
    #    split is GATHERED out of them;
    #  * the WP7 (x4) arrays were written per v2 split, already in v2 order, so they are
    #    loaded straight. Gathering them by split_v1 would index the wrong chips.
    if (corpus / "corpus_x4.json").is_file():
        arr = np.load(corpus / f"chips_{split}.npy", mmap_mode="r")
        if arr.shape[0] != len(recs):
            raise SystemExit(
                f"data: {corpus.name}/chips_{split}.npy holds {arr.shape[0]} chips but the "
                f"v2 manifest names {len(recs)} for split {split!r}")
        if arr.shape[1] != C.N_BANDS:
            raise SystemExit(
                f"data: {corpus.name}/chips_{split}.npy has {arr.shape[1]} bands, variant "
                f"{C.VARIANT} expects {C.N_BANDS} ({','.join(C.BANDS)})")
        return np.asarray(arr), recs

    cache, out = {}, np.empty((len(recs), C.N_BANDS, C.CHIP_PX, C.CHIP_PX), np.uint16)
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
    if float(value) != float(C.NORM_DIVISOR_DN):
        raise SystemExit(
            f"data: normalisation divisor {value} != registered "
            f"{C.NORM_DIVISOR_DN} (sr_train.config.NORM_DIVISOR_DN, variant {C.VARIANT}). "
            f"Metrics computed with a "
            f"different divisor are not comparable with the registered control.")
    return float(C.NORM_DIVISOR_DN)


class BandOrderError(ValueError):
    """The band order a model was trained on is not the order it is being given."""


def assert_band_order(declared, expected=None, where="model"):
    """D28. The order is ASSERTED, never assumed.

    `onnx_upsample.validate_input` checks the CHANNEL COUNT only. Once our model is also four
    bands, a four-band file in any order satisfies that guard and would run, producing a
    plausible image from the wrong bands - the dominant failure class in this project. WP6
    measured a two-band swap on the reference model at max 1328 DN, median 36 DN, with the
    result still looking like an image.

    `declared` is what the artefact says (a comma string or a sequence); `expected` defaults
    to the variant's own band tuple.
    """
    exp = tuple(expected if expected is not None else C.BANDS)
    got = tuple(x.strip() for x in declared.split(",")) if isinstance(declared, str) \
        else tuple(declared)
    if got != exp:
        raise BandOrderError(
            f"{where}: band order {got} does not match the configured order {exp}. "
            f"A four-band file in the wrong order passes a channel-count check and produces "
            f"a plausible image from the wrong bands; it is refused here instead.")
    return exp
