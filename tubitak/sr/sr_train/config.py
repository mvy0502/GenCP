"""The registered constants of WP3B, in one place.

Every number `tubitak/sr/docs/03b-registration.md` states is defined HERE and imported.
Nothing restates a constant with a literal. The WP3A constants are NOT redefined: they are
re-exported from `sr_data.params`, so there is exactly one definition of each in the project
and a drift between the corpus and the training run is impossible.

Changing a value here invalidates the registration, not just the code.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

SR = Path(__file__).resolve().parents[1]
if str(SR) not in sys.path:
    sys.path.insert(0, str(SR))

from sr_data import params as P                                        # noqa: E402

#: WHICH CONFIGURATION IS IN FORCE. "x2" is WP3A/WP3B's, unchanged and still the default, so
#: every WP3B number remains reproducible by importing this module with nothing set. "x4" is
#: WP7's: scale 4, four bands, normalised = reflectance.
#:
#: A variant rather than a forked copy of every module, so there is ONE implementation of the
#: dataloader, the trainer, the evaluator and the exporter. The variant name is written into
#: every artefact those produce, so a number always says which configuration made it.
VARIANT = os.environ.get("GENCP_SR_VARIANT", "x2")
if VARIANT not in ("x2", "x4", "tci"):
    raise SystemExit(f"config: unknown GENCP_SR_VARIANT {VARIANT!r}; known: x2, x4, tci")

#: WP12 D30: "tci" is the three-band 8-bit configuration - Sentinel-2's own TCI product at
#: scale 4, for the 8-bit RGB imagery the institute holds today. It shares x4's scale and
#: x2's band set, and has its own divisor, so it is a third variant rather than a flag.
_TCI = VARIANT == "tci"
_X4 = VARIANT == "x4"
_S4 = _X4 or _TCI                      # the scale-4 family

# ------------------------------------------------------- inherited from WP3A, not redefined
CHIP_PX = P.CHIP_PX                    # 256, both variants
SCALE = 4 if _S4 else P.SCALE
INPUT_PX = CHIP_PX // SCALE            # 64 at x4, 128 at x2
CHIP_M = P.CHIP_M                      # 2560.0
BLOCK_CHIPS = P.BLOCK_CHIPS            # 14
BLOCKS_PER_GRANULE = P.BLOCKS_PER_GRANULE
SPLIT_BUFFER_M = P.SPLIT_BUFFER_M      # 2560.0
SPLIT_SEED = P.SPLIT_SEED              # 20260830
HELDOUT_GRANULE = P.HELDOUT_GRANULE    # 36SXJ
#: D24: re-derived for WP7, not reused. B08's clear-pixel p99.9 is 6650 DN, so DN/5000 would
#: put it at 1.330, outside a nominal full scale of 1. 10000 is 1/DN_TO_REFLECTANCE, so the
#: normalised value IS the surface reflectance - a physical constant rather than a fitted one,
#: and the same domain the reference model uses internally.
#: WP12 D31: 255 is TCI's full scale - a constant of the format, not fitted to the corpus,
#: the same reasoning that put 10000 here for x4. PSNR_DATA_RANGE 1.0 accompanies it and the
#: two are meaningless apart.
NORM_DIVISOR_DN = 255.0 if _TCI else (10000.0 if _X4 else P.NORM_DIVISOR_DN)
PSNR_DATA_RANGE = P.PSNR_DATA_RANGE    # 1.0
#: D23/D28: B08 is APPENDED as plane 4; the first three keep their existing order.
BANDS = (tuple(P.BANDS) + ("B08",)) if _X4 else tuple(P.BANDS)   # tci keeps the three
N_BANDS = len(BANDS)
GRANULES = P.GRANULES

# ------------------------------------------------------------------------- D13, new in WP3B
#: A block may be assigned to `val` or `test` only if it retains at least this many chips
#: AFTER deduplication. Ineligible blocks go to `train`. Fixes WP3A open item 1: 36SWJ's
#: block (2,2) is 94.81 % nodata, yielded 0 chips, and was nevertheless assigned `test`.
MIN_BLOCK_CHIPS_FOR_EVAL = 50

#: Deduplication keep order: ascending accepted-chip count, ties by MGRS name ascending.
#: The counts are WP3A's screening result (03a-wald-corpus.md 3.1), an input measurement.
#: Stated as an explicit tuple rather than recomputed, so the order cannot silently change
#: with the corpus.
DEDUP_ORDER = ("36TUK", "36SWJ", "36TVK", "36SXJ", "36SVJ")
DEDUP_ORDER_COUNTS = {"36TUK": 1036, "36SWJ": 1122, "36TVK": 1283,
                      "36SXJ": 1332, "36SVJ": 1659}

# --------------------------------------------------------------------------- D16 architecture
WIDTH = 64                 #: C
N_BLOCKS = 6               #: N residual blocks; the largest depth with RF <= 32
RECEPTIVE_FIELD_PREDICTED = 31        #: input pixels; derived in the registration D16

# ------------------------------------------------------------------------------- D14 loss
CHARBONNIER_EPS = 1e-3     #: normalised units (= 5 DN)

# --------------------------------------------------------------------------- D19 training
TRAIN_SEED = 20260831
LR = 2e-4
LR_MIN = 2e-5
BATCH = 32
CHECKPOINT_EVERY = 500

# ---------------------------------------------------------------------------------- paths
#: WP7 writes a NEW directory. The WP3B corpus is never overwritten, so a WP3B number can
#: still be reproduced after this work package.
#: WP13 D35: the tci variant points at the CORRECTED corpus. WP12's is kept on disk under
#: sr_wald_corpus_tci and is not deleted; it is reachable by passing its path explicitly.
CORPUS_SUBDIR = ("sr_wald_corpus_tci_v2" if _TCI else
                 "sr_wald_corpus_x4" if _X4 else P.CORPUS_SUBDIR)
SPLIT_SUBDIR = ("sr_wald_split_tci_v2" if _TCI else "sr_wald_split_v2")
#: the corrected manifest lives here, beside the corpus it corrects. WP12: the TCI
#: corpus has its own, because its chip set differs (see 12-tci-model.md section 9).
RUN_SUBDIR = ("sr_train_runs_tci_v2" if _TCI else
              "sr_train_runs_x4" if _X4 else "sr_train_runs")
WORK_PACKAGE = "P2-WP13" if _TCI else ("P2-WP7" if _X4 else "P2-WP3B")
GSD_M = P.GSD_M                        # target GSD, 10 m
SRC_GSD_M = P.GSD_M * SCALE            # training input: 20 m at s=2, 40 m at s=4
OUT_GSD_M = P.GSD_M / SCALE            # deployment output: 5 m at s=2, 2.5 m at s=4


def data_root():
    return SR.parent / "data"


# ------------------------------------------------------------------ inference tile contract
#: Inference tile in SOURCE px. At x4 the network consumes 64 source px (the training input);
#: overlap stays 32, comfortably above the measured receptive field of 31 input px.
INFER_TILE_SRC_PX = 64 if _S4 else P.INFER_TILE_SRC_PX
INFER_OVERLAP_SRC_PX = P.INFER_OVERLAP_SRC_PX
PSNR_DATA_RANGE = P.PSNR_DATA_RANGE
MTF_AT_NYQUIST = P.MTF_AT_NYQUIST
