# gencp-ref correctness gate — registered before the gate is run

> **STATUS (2026-08-21): FAILED-as-designed.** Criterion 1 failed because the reference
> outputs were rendered from Overpass while the tool renders from the Geofabrik snapshots —
> the two sides never drew from the same OSM data, so the test could not have passed for a
> correct tool. The mismatch this registration anticipated ("extract scope") turned out to be
> a source discontinuity in the archive (corrections-log entry 13). This registration is
> retained unmodified below; the well-posed replacement is
> [tool-gate-registration-2.md](tool-gate-registration-2.md). Criteria 2–3 were never
> evaluated under this registration.

**Registered 2026-08-20, branch `tubitak-tool`.** The extent→reference tool
(`tubitak/tool/gencp_ref.py`) must reproduce the already-verified evaluation outputs where
it overlaps them. Test extent: the union of Ankara evaluation chips **ank_26_21 and
ank_26_22** (vertically adjacent, 2,570 m apart, same easting — chosen so a 1×2 tile grid
with `--align-origin` at ank_26_21's NW corner makes the tool's tiles coincide with the
chips' footprints exactly). Arm: **C3** (its verified per-chip fakes exist from the C3
evaluation). Two runs: `--overlap-m 0` (gate mode) and `--overlap-m 640` (production mode).

## Accepted deviations, fixed in advance

1. **Tile space (generation-path identity):** each tool tile fake must be **bit-exact**
   against the verified evaluation fake for the same chip. The render inputs must also be
   bit-exact. Known risk stated in advance: the tool renders from one extent-wide
   `osmium -s smart` extract, the evaluation chips from per-chip mini-extracts; if the OSM
   content over a chip differs between the two extract scopes, the renders differ — and that
   is a **bug/finding to report, not a tolerance** (the transparency-gate lesson).
2. **Mosaic space:** the mosaic lives on a 10 m grid while tiles are 10.0390625 m, so
   bit-exactness against the 256-px chips is not the criterion there. Instead: for the
   overlap-0 run, the mosaic raster restricted to each tile's footprint must equal, exactly,
   an independently computed single-tile bilinear warp of that tile with the corrected
   affine onto the same grid (the warp proven byte-identical in the evaluation phases).
   For the overlap-640 run, pixels outside the blend zone must satisfy the same equality;
   pixels inside the blend zone must lie within **[min−1, max+1]** of the two contributing
   tiles' warped values at that pixel (±1 for uint8 rounding). Anything beyond that is a bug.
3. **Georeferencing:** the mosaic transform must be `(10.0, 0, extent_xmin, 0, −10.0,
   extent_ymax)` on the working CRS; the per-tile placement must use GSD exactly
   10.0390625 = 257·10/256 (read back from the embedded provenance tag); and the warped
   content must land within one output pixel of where the validated per-chip corrected
   transform places it (verified by cross-correlating the mosaic's chip-footprint region
   against the evaluation warp — peak at lag 0).
4. **Seam metric (measured, not eyeballed):** reported for the production run: gradient
   energy in ±2-px buffers along interior tile-edge lines vs background. No pass threshold
   is registered for the ratio (it is a *watch* metric with no prior distribution); what is
   registered is that the number is computed and reported, and that a ratio visibly above 1
   blocks any "seams are fine" wording.

If any criterion fails: stop, report, do not adjust the gate.
