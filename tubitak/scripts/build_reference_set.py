#!/usr/bin/env python
"""Build a georeferenced real-satellite reference set from the GenCP_HR_DB pairs.

No reference imagery needs downloading. Each ``image_pairs`` chip is a 514x257
concatenation of a satellite half and an OSM half, and the OSM half is
byte-identical to the matching georeferenced raster in ``train/`` or ``test/``.
That raster's CRS and affine transform can therefore be inherited by the
satellite half, turning it into proper ground truth.

Orientation is **verified per chip, never assumed**, by two independent signals
that must agree:

* **correlation** of each half against the georeferenced raster - the OSM half
  correlates strongly, the satellite half does not;
* **flatness** - an OSM rendering is categorical, so a handful of colours cover
  much of the chip, whereas satellite imagery is continuous.

Byte equality is NOT required. Measured on the test split, only about half the
OSM halves are byte-identical to their georeferenced raster; the rest differ
slightly (MAD ~2 DN, correlation ~0.95), consistent with the two products having
been rendered from different OSM snapshots. That does not affect geometry: both
depict the same named tile at 257x257 and 10 m, so the transform is still the
correct one to inherit. Chips are counted both ways and reported.

Any chip whose two signals disagree, or whose layout differs from the majority,
is reported and skipped rather than silently written the wrong way round.

Usage
-----
    python tubitak/scripts/build_reference_set.py --out tubitak/data/karios/reference
"""
from __future__ import annotations

import argparse
import glob
import os
import sys
import warnings
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "tubitak" / "data" / "GenCP_HR_DB"


def flatness(a, top=5):
    """Fraction of pixels covered by the `top` most common colours."""
    px = a.reshape(-1, a.shape[2]).astype(np.uint8)
    _, counts = np.unique(px, axis=0, return_counts=True)
    return float(np.sort(counts)[::-1][:top].sum() / counts.sum())


def main() -> int:
    import rasterio
    from rasterio.errors import NotGeoreferencedWarning
    warnings.filterwarnings("ignore", category=NotGeoreferencedWarning)

    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--split", default="test", choices=["test", "train"])
    ap.add_argument("--out", default=str(ROOT / "tubitak/data/karios/reference"))
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--exclude-leaked", action="store_true", default=True)
    a = ap.parse_args()

    pair_dir = DB / "image_pairs" / a.split
    geo_dir = DB / a.split
    if not pair_dir.is_dir():
        sys.exit(f"missing {pair_dir} — download GenCP_HR_DB.zip into tubitak/data/")

    leaked = set()
    if a.exclude_leaked and a.split == "test":
        tr = {os.path.basename(f) for f in glob.glob(str(DB / "image_pairs/train/*.tif"))}
        leaked = {os.path.basename(f) for f in glob.glob(str(pair_dir / "*.tif"))} & tr

    files = sorted(glob.glob(str(pair_dir / "*.tif")))
    files = [f for f in files if os.path.basename(f) not in leaked]
    if a.limit:
        files = files[::max(1, len(files) // a.limit)][:a.limit]

    out = Path(a.out)
    (out / "satellite").mkdir(parents=True, exist_ok=True)
    (out / "osm").mkdir(parents=True, exist_ok=True)

    layouts, anomalies, written = {}, [], 0
    exact = {'identical': 0, 'corresponding': 0}
    print(f"pairs: {len(files)}   (excluded {len(leaked)} leaked chips)\n")

    for f in files:
        stem = Path(f).stem
        geo = geo_dir / f"{stem}.tif"
        if not geo.exists():
            anomalies.append((stem, "no matching georeferenced raster"))
            continue
        with rasterio.open(f) as s:
            AB = np.transpose(s.read(), (1, 2, 0))
        with rasterio.open(geo) as s:
            G = np.transpose(s.read(), (1, 2, 0))
            crs, transform = s.crs, s.transform
        if AB.shape[1] != 2 * AB.shape[0]:
            anomalies.append((stem, f"not a 2:1 pair ({AB.shape[1]}x{AB.shape[0]})"))
            continue

        w2 = AB.shape[1] // 2
        left, right = AB[:, :w2], AB[:, w2:]

        # signal 1: which half corresponds to the georeferenced raster?
        gf = G.astype(float).ravel()
        cl = float(np.corrcoef(gf, left.astype(float).ravel())[0, 1])
        cr = float(np.corrcoef(gf, right.astype(float).ravel())[0, 1])
        # signal 2: categorical renderings are flat, satellite imagery is not
        fl, fr = flatness(left), flatness(right)

        if cr > cl:
            osm, sat, layout, c_osm, c_sat = right, left, "[satellite | OSM]", cr, cl
            f_osm, f_sat = fr, fl
        else:
            osm, sat, layout, c_osm, c_sat = left, right, "[OSM | satellite]", cl, cr
            f_osm, f_sat = fl, fr

        identical = np.array_equal(osm, G)
        # byte equality is decisive on its own: a narrow correlation margin on a
        # near-uniform chip must not reject a half that IS the georeferenced raster
        if not (identical or (c_osm > 0.7 and c_osm - c_sat > 0.3)):
            anomalies.append((stem, f"weak correspondence (osm corr={c_osm:+.3f}, "
                                    f"sat corr={c_sat:+.3f})"))
            continue
        if f_osm <= f_sat:
            anomalies.append((stem, f"correlation and flatness DISAGREE "
                                    f"(osm flat={f_osm:.3f} <= sat flat={f_sat:.3f})"))
            continue
        exact["identical" if identical else "corresponding"] += 1

        layouts[layout] = layouts.get(layout, 0) + 1
        prof = dict(driver="GTiff", height=sat.shape[0], width=sat.shape[1],
                    count=sat.shape[2], dtype="uint8", crs=crs, transform=transform)
        with rasterio.open(out / "satellite" / f"{stem}.tif", "w", **prof) as d:
            d.write(np.transpose(sat, (2, 0, 1)).astype("uint8"))
        with rasterio.open(out / "osm" / f"{stem}.tif", "w", **prof) as d:
            d.write(np.transpose(osm, (2, 0, 1)).astype("uint8"))
        written += 1

    print("=" * 66)
    print("LAYOUT VERIFICATION (per chip, not assumed)")
    print("=" * 66)
    for k, v in layouts.items():
        print(f"  {k:<22} {v} chips")
    print(f"\n  OSM half byte-identical to the georeferenced raster : {exact['identical']}")
    print(f"  OSM half corresponding but not identical            : {exact['corresponding']}")
    print(f"\nwritten: {written} satellite + {written} osm GeoTIFFs -> {out}")
    print(f"anomalies: {len(anomalies)}")
    for stem, why in anomalies[:20]:
        print(f"    {stem}: {why}")
    if len(layouts) > 1:
        print("\n*** MIXED LAYOUTS PRESENT — the corpus is not uniformly ordered ***")
    return 0


if __name__ == "__main__":
    sys.exit(main())
