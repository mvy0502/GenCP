# Registration: is the visible tile grid caused by instance normalisation?

Written and committed BEFORE the seam metric was computed on any mosaic. Nothing below was
chosen after seeing a number.

## The claim under test

The deployed generator uses BatchNorm in batch-statistic mode. At batch size 1 that is
arithmetically identical to InstanceNorm: each tile is normalised by its OWN mean and
variance. Two adjacent tiles with different content are therefore rescaled differently, and
the boundary between them becomes a step in intensity.

The mechanism predicts something specific and falsifiable: the discontinuity is a GLOBAL
offset between whole tiles, not a local artefact at the join. That is why 640 m of overlap
blending has not removed it - blending averages a neighbourhood across the seam, which
cannot cancel a difference that extends across the entire tile.

## Metric, fixed here

Two numbers, because the mechanism makes claims about both scales.

**S1, the seam step.** For every interior tile boundary in the mosaic, the mean absolute
difference between the two columns (or rows) straddling it:

    S1 = mean |I[:, c] - I[:, c-1]|   over boundary columns c

**C1, the control.** The identical statistic computed on interior lines that are NOT
boundaries, sampled at the same count and from the same rows, to absorb the scene's own
texture. Reported as the ratio S1/C1.

A ratio of 1.0 means boundaries are indistinguishable from ordinary image structure. The
eye notices a grid well below the ratio at which a difference is large in absolute DN,
because the grid is spatially regular, so the ratio is the number that matters.

**S2, the per-tile offset.** The standard deviation, across tiles, of each tile's mean
intensity taken over its interior only (a centre crop that excludes all blended margins).
Instance normalisation predicts this is large; a purely local seam artefact predicts it is
small. S2 is what separates the stated mechanism from the alternatives.

Grey is used throughout - the unweighted RGB mean, this project's existing convention.

## Predictions, registered

1. On the current (train-mode) İstanbul mosaic, **S1/C1 > 1.3**.
2. Regenerating the same scene in eval mode, which uses running statistics identical for
   every tile, **reduces S1/C1 by at least 25% of its excess over 1.0**.
3. **S2 falls by at least 30%** in eval mode. This is the discriminating prediction: if S1
   improves but S2 does not, the cause is not per-tile normalisation and the hypothesis is
   wrong however good the picture looks.

## What would falsify it

S1/C1 near 1.0 in train mode - the grid would then be a rendering or mosaicking artefact,
not a normalisation one. Or eval mode leaving S2 unchanged, which would mean the tiles were
never being individually rescaled.

## What this is not

Image quality has never been a gate in this project. Every registered gate scores matching
error. If eval mode wins here it does not follow that eval mode should ship - the
common-support test attributed roughly 79% of its apparent matching advantage to
survivorship. Two criteria pointing different directions is a decision for the project
owner, and this registration does not pre-empt it.
