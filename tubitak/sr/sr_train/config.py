"""The registered constants of WP3B, in one place.

Every number `tubitak/sr/docs/03b-registration.md` states is defined HERE and imported.
Nothing restates a constant with a literal. The WP3A constants are NOT redefined: they are
re-exported from `sr_data.params`, so there is exactly one definition of each in the project
and a drift between the corpus and the training run is impossible.

Changing a value here invalidates the registration, not just the code.
"""
from __future__ import annotations

import sys
from pathlib import Path

SR = Path(__file__).resolve().parents[1]
if str(SR) not in sys.path:
    sys.path.insert(0, str(SR))

from sr_data import params as P                                        # noqa: E402

# ------------------------------------------------------- inherited from WP3A, not redefined
CHIP_PX = P.CHIP_PX                    # 256
INPUT_PX = P.INPUT_PX                  # 128
SCALE = P.SCALE                        # 2
CHIP_M = P.CHIP_M                      # 2560.0
BLOCK_CHIPS = P.BLOCK_CHIPS            # 14
BLOCKS_PER_GRANULE = P.BLOCKS_PER_GRANULE
SPLIT_BUFFER_M = P.SPLIT_BUFFER_M      # 2560.0
SPLIT_SEED = P.SPLIT_SEED              # 20260830
HELDOUT_GRANULE = P.HELDOUT_GRANULE    # 36SXJ
NORM_DIVISOR_DN = P.NORM_DIVISOR_DN    # 5000.0
PSNR_DATA_RANGE = P.PSNR_DATA_RANGE    # 1.0
BANDS = P.BANDS
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
CORPUS_SUBDIR = P.CORPUS_SUBDIR           # sr_wald_corpus
SPLIT_SUBDIR = "sr_wald_split_v2"         # the corrected manifest lives here, beside it
RUN_SUBDIR = "sr_train_runs"


def data_root():
    return SR.parent / "data"
