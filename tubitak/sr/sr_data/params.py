"""The registered constants of the WP3A Wald corpus, in one place.

Every number the registration (`tubitak/sr/docs/03a-wald-corpus.md`) states is defined HERE
and imported by the corpus builder, the dataloader degradation, the control baseline and the
checks. Nothing restates a constant with a literal. This is deliberate: the registration is
only meaningful if the thing that ran used the numbers the registration names, and the
cheapest way to guarantee that is to have exactly one definition.

Changing any value in this file is a CORPUS REGENERATION, not a code change. See the
invariance section of the registration.
"""
from __future__ import annotations

import math

# --------------------------------------------------------------------------- provenance
#: The five granules, keyed by MGRS tile. Directory names under DATA_ROOT/s2_reflectance_l2a.
#: Product IDs are WP2A's, proved byte-identical to what is on disk (02a §1.2).
GRANULES = {
    "36TVK": dict(dirname="36TVK_20260430", date="2026-04-30", datatake="A008614",
                  orbit="R064",
                  product_uri="S2C_MSIL2A_20260430T083651_N0512_R064_T36TVK_20260430T140714.SAFE",
                  stac_item="S2C_36TVK_20260430_0_L2A"),
    "36TUK": dict(dirname="36TUK_20260430", date="2026-04-30", datatake="A008614",
                  orbit="R064",
                  product_uri="S2C_MSIL2A_20260430T083651_N0512_R064_T36TUK_20260430T140714.SAFE",
                  stac_item="S2C_36TUK_20260430_0_L2A"),
    "36SVJ": dict(dirname="36SVJ_20260430", date="2026-04-30", datatake="A008614",
                  orbit="R064",
                  product_uri="S2C_MSIL2A_20260430T083651_N0512_R064_T36SVJ_20260430T140714.SAFE",
                  stac_item="S2C_36SVJ_20260430_0_L2A"),
    "36SWJ": dict(dirname="36SWJ_20260430", date="2026-04-30", datatake="A008614",
                  orbit="R064",
                  product_uri="S2C_MSIL2A_20260430T083651_N0512_R064_T36SWJ_20260430T140714.SAFE",
                  stac_item="S2C_36SWJ_20260430_0_L2A"),
    "36SXJ": dict(dirname="36SXJ_20260527", date="2026-05-27", datatake="A009000",
                  orbit="R021",
                  product_uri="S2C_MSIL2A_20260527T082601_N0512_R021_T36SXJ_20260527T135213.SAFE",
                  stac_item="S2C_36SXJ_20260527_0_L2A"),
}

#: Band order stored in every chip array, channel-first. Not alphabetical by accident:
#: this is (blue, green, red), the order a viewer expects to map to B, G, R.
BANDS = ("B02", "B03", "B04")

# ------------------------------------------------------------------------ clear masking
#: SCL classes treated as CLEAR. Everything not listed is rejected.
#:   2  dark area / cast shadow   - real land, topographic shadow; dark but valid
#:   4  vegetation                - keep
#:   5  not vegetated             - keep
#:   6  water                     - keep (1.4 % of pixels; a model that has never seen
#:                                  water will hallucinate texture on lakes)
#:   7  unclassified              - keep; the processor declined to label it, which is not
#:                                  the same as it being cloud
#: Rejected: 0 nodata, 1 saturated/defective, 3 cloud shadow, 8/9 cloud, 10 cirrus,
#: 11 snow/ice.
#:
#: This differs from WP0/WP2A's screen ("not in {0,3,8,9,10,11}") by ALSO rejecting class 1,
#: saturated/defective. WP2A measured class 1 at exactly 0 pixels across all five granules,
#: so the two definitions select the same pixels on this corpus; the difference is that this
#: one does not depend on that population staying empty.
CLEAR_CLASSES = frozenset({2, 4, 5, 6, 7})
SCL_MEANING = {0: "no data", 1: "saturated/defective", 2: "dark area/cast shadow",
               3: "cloud shadow", 4: "vegetation", 5: "not vegetated", 6: "water",
               7: "unclassified", 8: "cloud medium probability",
               9: "cloud high probability", 10: "thin cirrus", 11: "snow/ice"}

#: A chip is accepted only if EVERY SCL pixel over its footprint is clear.
MIN_CLEAR_FRACTION = 1.0

#: ...and only if no band pixel carries the nodata sentinel. WP2A open item 2: DN 0 is both
#: the declared nodata value and a legal reflectance, and the encoding cannot tell them
#: apart. 3443/568/1290 pixels per band are SCL-clear yet store 0. Rejecting the chip is the
#: decision; it costs almost nothing and removes the ambiguity from the corpus rather than
#: carrying it into a loss function.
REJECT_CHIPS_CONTAINING_DN = 0

# ------------------------------------------------------------------------ chip geometry
CHIP_PX = 256              # target chip, 10 m pixels
CHIP_STRIDE_PX = 256       # non-overlapping; chips share no pixel
GSD_M = 10.0
CHIP_M = CHIP_PX * GSD_M   # 2560 m
SCALE = 2                  # Wald factor: 128 px at 20 m -> 256 px at 10 m
INPUT_PX = CHIP_PX // SCALE

#: WP4 inference tile contract, recorded here so it is not rediscovered. WP1's bicubic path
#: tiles the SOURCE at 512 px; the trained network consumes 128 source pixels, because its
#: input is the 20 m image. Overlap stays 32 source pixels.
INFER_TILE_SRC_PX = 128
INFER_OVERLAP_SRC_PX = 32

# ------------------------------------------------------------------------- degradation
#: Modulation of the low-pass at the Nyquist frequency of the DECIMATED (20 m) grid.
#: An argument, not a constant of nature: changing it regenerates the corpus.
MTF_AT_NYQUIST = 0.3


def sigma_for_mtf(mtf_at_nyquist=MTF_AT_NYQUIST, scale=SCALE):
    """Gaussian sigma, in SOURCE pixels, whose MTF equals `mtf_at_nyquist` at the Nyquist
    frequency of the grid decimated by `scale`.

    Derivation, in full, because a sigma copied from a paper is a number nobody can check:

      A Gaussian point-spread function of standard deviation s (in source pixels) has
      Fourier transform, normalised to 1 at zero frequency,

          MTF(f) = exp(-2 * pi^2 * s^2 * f^2),      f in cycles per source pixel.

      The decimated grid has a sample spacing of `scale` source pixels, so its Nyquist
      frequency is

          f_nyq = 1 / (2 * scale)   cycles per source pixel     ( = 0.25 for scale 2,
                                                                  i.e. 0.025 cycles/m
                                                                  at 10 m sampling ).

      Setting MTF(f_nyq) = m and solving for s:

          exp(-2 * pi^2 * s^2 * f_nyq^2) = m
          -2 * pi^2 * s^2 * f_nyq^2      = ln m
          s^2                            = -ln m / (2 * pi^2 * f_nyq^2)
          s                              = sqrt( -ln m / (2 * pi^2 * f_nyq^2) )

      For m = 0.3, scale = 2:  f_nyq = 0.25, f_nyq^2 = 0.0625,
          s^2 = 1.2039728043259361 / (2 * 9.869604401089358 * 0.0625)
              = 1.2039728043259361 / 1.2337005501361697
              = 0.9759053...
          s   = 0.9878792...  source pixels  =  9.8788 m at a 10 m GSD.

    Returns the sigma in source pixels.
    """
    if not 0.0 < mtf_at_nyquist < 1.0:
        raise ValueError(
            f"MTF at Nyquist must be in (0, 1), got {mtf_at_nyquist}. At 1.0 the filter "
            "does nothing and the degradation is plain decimation with aliasing; at 0 the "
            "sigma is infinite.")
    f_nyq = 1.0 / (2.0 * scale)
    return math.sqrt(-math.log(mtf_at_nyquist) / (2.0 * math.pi ** 2 * f_nyq ** 2))


#: Kernel half-width in source pixels, as a multiple of sigma. 4 sigma truncates the
#: Gaussian at a weight of exp(-8) = 3.4e-4 of its peak before normalisation.
KERNEL_RADIUS_SIGMAS = 4.0

# ----------------------------------------------------------------------- radiometry (D7)
#: DN -> reflectance. Processing baseline 05.12, boa_offset_applied = true (WP2A §1, §7):
#: the +1000 BOA offset has ALREADY been removed from the stored DN, so the conversion is a
#: pure scale. The dissenting STAC `raster:bands offset: -0.1` is not applied; the D7
#: diagnostic in the registration measures both and shows the alternative is unphysical.
DN_TO_REFLECTANCE = 1.0 / 10000.0
BOA_OFFSET_APPLIED = 0.0          # deliberately zero; the alternative is -0.1

#: Fixed, corpus-wide normalisation: normalised = DN / NORM_DIVISOR_DN = reflectance / 0.5.
#: ONE constant for all three bands - a per-band scale would change the colour relationships
#: the downstream matching stage depends on. Justified in the registration.
NORM_DIVISOR_DN = 5000.0
NORM_DIVISOR_REFLECTANCE = NORM_DIVISOR_DN * DN_TO_REFLECTANCE   # 0.5

#: Nominal full scale of the normalised domain; the data range PSNR is computed against.
PSNR_DATA_RANGE = 1.0

# ----------------------------------------------------------------------------- splitting
#: Blocks are square in CHIP units. 42 chips span a granule (10980 // 256), and 42 = 3 * 14,
#: so 14 tiles a granule into exactly 3 x 3 = 9 blocks with no ragged remainder.
BLOCK_CHIPS = 14
BLOCK_M = BLOCK_CHIPS * CHIP_M    # 35840 m

#: Blocks per granule assigned to each split, out of BLOCK_CHIPS-grid's 9.
BLOCKS_PER_GRANULE = {"train": 7, "val": 1, "test": 1}

#: Minimum separation, in metres, between chips belonging to different splits. One full chip
#: width. Any chip within this distance of a chip in a different split is DROPPED from the
#: corpus entirely rather than reassigned.
SPLIT_BUFFER_M = CHIP_M           # 2560.0

#: The granule held out whole. 36SXJ is the only one of the five from a different datatake
#: (2026-05-27, orbit R021) - the other four are one datatake 14 seconds apart - and it is
#: also the morphologically distinct site (Cappadocia tuff badlands). Those two differences
#: are CONFOUNDED and this corpus cannot separate them; see the registration.
HELDOUT_GRANULE = "36SXJ"

#: Seed for the block-to-split assignment. The only stochastic step in the whole package.
SPLIT_SEED = 20260830

# --------------------------------------------------------------------------------- paths
DATA_SUBDIR = "s2_reflectance_l2a"
CORPUS_SUBDIR = "sr_wald_corpus"
