# Gate S — the super-resolution grid contract

**Registered:** 2026-08-30, Project 2 WP1, **before Gate S was run and before any
super-resolved raster existed on disk.** Standing practice 4: predictions are registered
before outcomes. This file is never edited to match a result; a revision is permitted only
if an *input measurement* improves and no outcome has been seen, and the earlier version is
never deleted.

---

## 1. What Gate S claims, and what it does not

Gate S asserts that a super-resolved raster sits on **the exact integer refinement of its
source raster's grid**. It is a claim about georeferencing arithmetic only. It says nothing
about whether the interpolated pixel values are good, and nothing about whether an
upsampler is better than any other. Those are separate questions and are not measured here.

### Gate S is not an analogue of Gate G, and inherits nothing from it

This must be stated because the two look superficially similar and are not.

| | Gate G (Project 1) | Gate S (Project 2) |
|---|---|---|
| quantity | placement of *generated* content against an independently warped reference | arithmetic relation between a *source* grid and its refinement |
| method | FFT cross-correlation of image content, parabolic sub-pixel peak refinement | exact float comparison of affine terms and pixel-centre coordinates |
| tolerance | 0.05 px bound; measured 0.000181 px | **exact equality, no tolerance** |
| what a failure means | the mosaic places pixels wrongly | the output raster is not on the grid it claims |

Gate G's 0.000181 px is a measurement of a different quantity by a different method against
a different reference. **Gate S is new. It has no track record and borrows none.** Its
credibility rests entirely on the known-false cases in §4 and on nothing else.

## 2. Sign and index conventions — stated once, never flipped

* Rasters are **north-up and axis-aligned**: the affine's `b` and `d` terms are zero. A
  rotated or sheared source is refused, not handled. This is checked where the assumption
  is made (`sr_core.grid.require_north_up`), not assumed at the call site.
* A pixel is addressed as **(row `i`, column `j`)**, `i` increasing **southward**, `j`
  increasing **eastward**, both zero-based.
* For an affine `T = Affine(a, 0, c, 0, e, f)`, the **centre** of source pixel `(i, j)` is

  ```
  P_src(i, j) = ( a·(j + 0.5) + c ,  e·(i + 0.5) + f )
  ```

  with `e` negative for a north-up raster.
* At integer scale `s`, source pixel `(i, j)` is covered by the output block of rows
  `[s·i, s·i + s)` and columns `[s·j, s·j + s)`. Its **centre** is

  ```
  P_out(i, j) = ( (a/s)·(s·j + s/2) + c ,  (e/s)·(s·i + s/2) + f )
  ```

* **Offset is defined as `P_out − P_src`**, in CRS units, **positive east** in `x` and
  **positive north** in `y`. This sign is used in every number Gate S prints and is not
  reversed anywhere.

## 3. The five assertions

Let the source have transform `T_src = Affine(a, 0, c, 0, e, f)`, width `W`, height `H`,
CRS `K`; let the output have `T_out`, `W_out`, `H_out`, `K_out`; let `s` be the integer
scale factor.

| # | assertion | predicate |
|---|---|---|
| S1 | output CRS identical to source CRS | `K_out == K` |
| S2 | output pixel size exactly source / s | `T_out.a == a / s` **and** `-T_out.e == -e / s` |
| S3 | output origin exactly the source origin | `T_out.c == c` **and** `T_out.f == f` |
| S4 | output size exactly s times the source | `W_out == s·W` **and** `H_out == s·H` |
| S5 | no shift | `P_out(i, j) == P_src(i, j)` exactly, for every sampled `(i, j)` |

### Why S2 and S3 are asserted as exact equality rather than with a tolerance

`s` is constrained to a **power of two** (`sr_core.grid.require_integer_scale`). Under
IEEE-754 binary64, dividing by a power of two only decrements the exponent: it is exact,
with no rounding, for every finite non-subnormal operand. So `a / s` is the exact real
quotient, and a correct implementation reproduces it bit-for-bit. A tolerance would
therefore admit only *incorrect* implementations, and a half-pixel error at 10 m — 5 m — is
enormous compared with any tolerance one would be tempted to write. **No tolerance is
used.** Origins are copied unchanged, so S3 is exact by construction and any inequality is
a real defect.

S5 is predicted to hold exactly for the same reason. Writing out the algebra with
`b = d = 0`:

```
P_out.x = (a/s)·(s·j + s/2) + c        P_src.x = a·(j + 0.5) + c
```

`a/s` is exact; `s·j + s/2` is an exactly representable integer-or-half-integer for the
sizes in use; both products round the same real number `a·(2j+1)/2` to nearest, so they are
bit-identical, and the identical `c` is then added to both. **Prediction: max |offset| is
exactly 0.0, not merely small.** If it is small-but-nonzero, that is a finding to report,
not a threshold to widen.

**Sampling for S5.** All four corners, plus every pixel on a stride of
`max(1, W // 17)` × `max(1, H // 17)`, plus indices `0, 1, W-2, W-1` and
`0, 1, H-2, H-1`. The number of pixels actually compared is printed with the result. A
sample of size zero is a failure, not a pass.

## 4. Known-false cases — registered before they were run

Standing practice 10 and 11. A check is trusted only after it has been watched reporting a
case it must reject. Each row states the **predicted** verdict.

| # | case | predicted |
|---|---|---|
| KT1 | the real bicubic output of the pipeline under test | **PASS**, all five assertions |
| KF1 | output transform offset by **half an output pixel** (`c += a/(2s)`, `f -= -e/(2s)`) | **FAIL on S3 and S5**; S1, S2, S4 pass |
| KF2 | output pixel size `a/s · (1 + 1e-9)` | **FAIL on S2**; S5 also fails, because a pixel size that is wrong by a relative 1e-9 moves the far-corner centre by ~1e-4 m at this raster size, and S5 is exact |
| KF3 | output at the **wrong scale** (`s·W` asserted, file is `(s/2)·W`) | **FAIL on S2 and S4** |
| KF4 | output in a **different CRS** (EPSG:4326 tag on the same array) | **FAIL on S1** |
| DG1 | **no arguments** | **exit 2**, refusing to run. Must not print a verdict. |
| DG2 | **missing file** | **exit 2 or a named error**, no verdict |
| DG3 | **empty raster** (0 valid bytes / unreadable body) | **error, no verdict** |
| DG4 | **single-pixel raster** (1×1 source) | **PASS** — this is a legitimate degenerate input, not a malformed one, and the arithmetic is defined for it. A crash here is a defect in the gate. |
| DG5 | an **unrecognised argument** (`--scalee=2`) | **exit 2**, via `tubitak/tests/_guard.py::strict_argv` |

**The gate is not trusted unless KF1–KF4 all fail and DG1–DG3, DG5 all refuse to emit a
verdict.** If Gate S passes on any of KF1–KF4, or emits a verdict for any of DG1–DG3 or
DG5, then Gate S is not a gate and that is the finding this work package reports, in place
of a green result.

## 5. Invariance — what must not change for this result to mean what it claims

Standing practice 1. Gate S's verdict is about the pipeline *as configured below*. Change
any of these and the registered result no longer describes what is running.

1. **Scale `s` is an integer power of two**, enforced in `sr_core.grid.require_integer_scale`.
   S2's exactness argument is a statement about binary floating point and does not survive
   `s = 3`. At a non-power-of-two scale the exactness claim must be re-derived or replaced
   by a stated tolerance; it must not be silently inherited.
2. **The source is north-up and axis-aligned** (`b == d == 0`), enforced in
   `sr_core.grid.require_north_up`. Every formula in §2 assumes it.
3. **The output origin is copied, never recomputed.** If a future version snaps or
   re-derives the origin, S3 becomes a real test of that derivation rather than a test of a
   copy, and its meaning changes.
4. **Tiles are laid out and placed in source pixel coordinates, by integer indexing —
   never by resampling.** An output block for source tile at `(row0, col0)` occupies output
   rows `[s·row0, …)` and columns `[s·col0, …)` exactly. If a future version places blocks
   with `rasterio.warp.reproject` (as `gencp_core.mosaic.build` does, because its tiles sit
   on a *different* grid from its output), the placement stops being exact integer
   arithmetic and S5 stops being a statement about arithmetic.
5. **No distance in metres is used anywhere in the SR grid or tiling path.** Tiling is in
   pixels; the grid is a scaling of the source affine. This is why `require_metric` is
   deliberately *not* applied here, and it is what keeps Project 1's recurring
   metres-into-degrees failure out of this code. If a metre-valued parameter is ever
   introduced, this invariant is broken and `require_metric` becomes mandatory.
6. **The upsampler does not change the grid.** `Upsampler.upsample` takes `H×W×C` and
   returns `sH×sW×C`. Gate S's arithmetic is independent of *which* upsampler ran, which is
   the point: it must give the same verdict for `BicubicUpsampler` today and for a trained
   ONNX model in WP4. If a future upsampler returns a differently-shaped array, S4 fails,
   and that is the correct outcome rather than something to accommodate.

## 6. What Gate S deliberately does not assert

* Anything about pixel **values**. A raster of zeros on the correct grid passes Gate S.
  This is intentional: the grid contract must be separable from image quality, exactly as
  Gate G separates grid alignment from content placement.
* That the tiled-and-blended result equals a single whole-image upsample. That is a real
  property and it is checked, but **it is not part of Gate S** and is reported separately,
  so that a seam defect cannot be mistaken for a georeferencing defect or vice versa.
* Anything about nodata handling. Bicubic interpolation mixes the nodata fill value into
  neighbouring valid pixels at a nodata boundary; that is a known, unaddressed limitation
  of this WP1 implementation and is recorded as an open item, not as a gate assertion.
