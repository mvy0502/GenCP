#!/usr/bin/env python
"""Verify that the georeferenced GenCP outputs are what they claim to be.

The original smoke test (CRS / size / resolution) cannot distinguish a correct
output from a badly wrong one: gencp_georeferencing.py copies `crs` and
`transform` verbatim from the reference raster, so those fields are inherited
regardless of which PNG was actually written. This script closes that gap.

Checks performed, per file in GenCP_HR_demo/data/GenCP_DB/:

  1. IDENTITY   - does the GeoTIFF pixel array equal the `_fake.png` (correct)
                  or the `_real.png` (hard failure)? Exact equality, per band.
  2. TRANSFORM  - is the output affine transform element-by-element identical to
                  the same-named source raster in data/dataset/test/?
  3. PAIRING    - is the filename mapping 1:1, and is each output's transform
                  unique to its own input (i.e. not derived from another tile)?

Read-only: opens files, writes nothing. Exit code 0 = PASS, 1 = FAIL.
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import rasterio
from rasterio.errors import NotGeoreferencedWarning

REPO_ROOT = Path(__file__).resolve().parents[2]
HR_DEMO = REPO_ROOT / "GenCP_HR_demo"
GEN_DB_DIR = HR_DEMO / "data" / "GenCP_DB"
INPUT_DIR = HR_DEMO / "data" / "dataset" / "test"
PNG_DIR = HR_DEMO / "data" / "fake_images" / "genCP_HR_RGB_model" / "test_latest" / "images"

# PNGs legitimately carry no geotransform; that warning is noise here.
warnings.filterwarnings("ignore", category=NotGeoreferencedWarning)


def read_array(path):
    with rasterio.open(path) as src:
        return src.read()


def read_meta(path):
    with rasterio.open(path) as src:
        return src.transform, src.crs, src.width, src.height


def fmt_transform(t):
    return "[" + ", ".join(f"{v:.6f}" for v in tuple(t)[:6]) + "]"


def main():
    for label, d in (("GenCP_DB", GEN_DB_DIR), ("dataset/test", INPUT_DIR), ("images", PNG_DIR)):
        if not d.is_dir():
            sys.exit(f"FATAL: missing directory ({label}): {d}")

    outputs = sorted(GEN_DB_DIR.glob("*.tif"))
    if not outputs:
        sys.exit(f"FATAL: no GeoTIFFs found in {GEN_DB_DIR}")

    identity_pass, identity_fail, identity_matched_real, identity_unknown = 0, 0, [], []
    transform_pass, transform_fail = 0, []
    missing_assets, size_notes = [], []

    print("=" * 78)
    print("GenCP georeferencing verification")
    print("=" * 78)
    print(f"outputs : {GEN_DB_DIR.relative_to(REPO_ROOT)}")
    print(f"inputs  : {INPUT_DIR.relative_to(REPO_ROOT)}")
    print(f"pngs    : {PNG_DIR.relative_to(REPO_ROOT)}")
    print()

    # ---- per-file identity + transform checks --------------------------------
    for out_path in outputs:
        stem = out_path.stem
        fake_png = PNG_DIR / f"{stem}_fake.png"
        real_png = PNG_DIR / f"{stem}_real.png"
        src_tif = INPUT_DIR / f"{stem}.tif"

        missing = [p.name for p in (fake_png, real_png, src_tif) if not p.exists()]
        if missing:
            missing_assets.append((stem, missing))
            identity_unknown.append(stem)
            transform_fail.append((stem, "missing source raster", ""))
            continue

        # --- 1. identity check
        out_arr = read_array(out_path)
        fake_arr = read_array(fake_png)
        real_arr = read_array(real_png)

        matches_fake = out_arr.shape == fake_arr.shape and np.array_equal(out_arr, fake_arr)
        matches_real = out_arr.shape == real_arr.shape and np.array_equal(out_arr, real_arr)

        if matches_fake and not matches_real:
            identity_pass += 1
        elif matches_real:
            identity_fail += 1
            identity_matched_real.append(stem)
        else:
            identity_fail += 1
            identity_unknown.append(stem)

        # --- 2. transform check
        out_t, out_crs, out_w, out_h = read_meta(out_path)
        in_t, in_crs, in_w, in_h = read_meta(src_tif)

        if tuple(out_t)[:6] == tuple(in_t)[:6] and out_crs == in_crs:
            transform_pass += 1
        else:
            transform_fail.append((stem, fmt_transform(out_t), fmt_transform(in_t)))

        if (out_w, out_h) != (in_w, in_h):
            size_notes.append((stem, f"{in_w}x{in_h}", f"{out_w}x{out_h}"))

    # ---- 3. pairing sanity ---------------------------------------------------
    out_stems = {p.stem for p in outputs}
    fake_stems = {p.name[:-9] for p in PNG_DIR.glob("*_fake.png")}
    input_stems = {p.stem for p in INPUT_DIR.glob("*.tif")}

    outputs_without_fake = sorted(out_stems - fake_stems)
    fakes_without_output = sorted(fake_stems - out_stems)
    outputs_without_input = sorted(out_stems - input_stems)
    inputs_not_processed = sorted(input_stems - out_stems)

    # Is each output's transform unique to its own input?
    input_transforms = {}
    for p in INPUT_DIR.glob("*.tif"):
        input_transforms.setdefault(tuple(read_meta(p)[0])[:6], []).append(p.stem)

    cross_derived = []
    for out_path in outputs:
        if not (INPUT_DIR / f"{out_path.stem}.tif").exists():
            continue
        key = tuple(read_meta(out_path)[0])[:6]
        owners = input_transforms.get(key, [])
        if owners != [out_path.stem]:
            cross_derived.append((out_path.stem, owners))

    # ---- report --------------------------------------------------------------
    print("-" * 78)
    print("1. IDENTITY CHECK  (GeoTIFF pixels vs _fake.png / _real.png)")
    print("-" * 78)
    print(f"  matched _fake (correct) : {identity_pass}")
    print(f"  matched _real (FAILURE) : {len(identity_matched_real)}")
    print(f"  matched neither         : {len(identity_unknown)}")
    if identity_matched_real:
        print("\n  *** HARD FAILURE - these outputs contain the INPUT image, not the generated one:")
        for s in identity_matched_real:
            print(f"      {s}")
    if identity_unknown:
        print("\n  *** these outputs matched neither PNG:")
        for s in identity_unknown:
            print(f"      {s}")

    print()
    print("-" * 78)
    print("2. TRANSFORM CHECK  (output affine vs same-named input, element-wise)")
    print("-" * 78)
    print(f"  identical : {transform_pass}")
    print(f"  mismatched: {len(transform_fail)}")
    for stem, got, want in transform_fail:
        print(f"      {stem}\n        output: {got}\n        input : {want}")

    print()
    print("-" * 78)
    print("3. PAIRING SANITY")
    print("-" * 78)
    print(f"  outputs in GenCP_DB           : {len(out_stems)}")
    print(f"  _fake.png files available     : {len(fake_stems)}")
    print(f"  source rasters available      : {len(input_stems)}")
    fully_paired = out_stems - set(outputs_without_fake) - set(outputs_without_input)
    print(f"  1:1 matched (output/fake/input): {len(fully_paired)}")
    print(f"  outputs with no _fake.png     : {len(outputs_without_fake)} {outputs_without_fake or ''}")
    print(f"  outputs with no source raster : {len(outputs_without_input)} {outputs_without_input or ''}")
    print(f"  _fake.png with no output      : {len(fakes_without_output)} {fakes_without_output or ''}")
    print(f"  outputs derived from a DIFFERENT input : {len(cross_derived)}")
    for stem, owners in cross_derived:
        print(f"      {stem} -> transform belongs to {owners}")
    print(f"\n  note: {len(inputs_not_processed)} source rasters were not processed "
          f"(test.py --num_test default is 50); informational, not a failure.")

    if size_notes:
        print()
        print("-" * 78)
        print("NOTE: input/output raster dimensions differ (upstream pipeline behaviour)")
        print("-" * 78)
        print(f"  {len(size_notes)} of {len(outputs)} files; transform is copied unchanged,")
        print("  so each output covers one pixel-row/col less extent than its input.")
        print(f"  example: {size_notes[0][0]}  input {size_notes[0][1]} -> output {size_notes[0][2]}")

    # ---- summary -------------------------------------------------------------
    total = len(outputs)
    ok = (identity_fail == 0
          and not transform_fail
          and not outputs_without_fake
          and not outputs_without_input
          and not cross_derived
          and not missing_assets)

    print()
    print("=" * 78)
    print(f"{'SUMMARY':<34}{'PASS':>10}{'FAIL':>10}")
    print("-" * 78)
    print(f"{'total files':<34}{total:>10}{'':>10}")
    print(f"{'identity check':<34}{identity_pass:>10}{identity_fail:>10}")
    print(f"{'transform check':<34}{transform_pass:>10}{len(transform_fail):>10}")
    print(f"{'pairing check':<34}{total - len(cross_derived) - len(outputs_without_fake) - len(outputs_without_input):>10}{len(cross_derived) + len(outputs_without_fake) + len(outputs_without_input):>10}")
    print("=" * 78)
    print(f"OVERALL: {'PASS' if ok else 'FAIL'}")
    print("=" * 78)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
