#!/usr/bin/env python
"""Cut per-chip mini-PBFs from the country extracts in ONE osmium pass per country.

osmium extract supports many bboxes per run, so each multi-GB country file is
read once regardless of how many chips fall in it.
"""
from __future__ import annotations
import json, subprocess, sys, warnings
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
GEO  = ROOT/"tubitak/data/geofabrik"
OUT  = ROOT/"tubitak/data/geofabrik/chips"

COUNTRY_FILE = {
 "France":"france","Germany":"germany","Spain":"spain","United Kingdom":"great-britain",
 "Belgium":"belgium","Austria":"austria","Sweden":"sweden","Republic of Serbia":"serbia",
 "Italy":"italy","Hungary":"hungary","Turkey":"turkey"}

def main() -> int:
    import rasterio
    from rasterio.warp import transform_bounds
    warnings.filterwarnings("ignore")
    OUT.mkdir(parents=True, exist_ok=True)
    cc = json.load(open("/tmp/chip_country.json"))
    bycountry = {}
    for st, c in cc.items(): bycountry.setdefault(c, []).append(st)
    for country, stems in sorted(bycountry.items()):
        pbf = GEO/f"{COUNTRY_FILE[country]}-latest.osm.pbf"
        if not pbf.exists():
            print(f"  !! missing extract {pbf.name}"); continue
        todo = [st for st in stems if not (OUT/f"{st}.osm.pbf").exists()]
        if not todo:
            print(f"  {country}: all {len(stems)} cut already"); continue
        extracts = []
        for st in todo:
            with rasterio.open(ROOT/f"tubitak/data/karios/reference/osm/{st}.tif") as s:
                b = transform_bounds(s.crs, "EPSG:4326",
                                     s.bounds.left-400, s.bounds.bottom-400,
                                     s.bounds.right+400, s.bounds.top+400)
            extracts.append({"output": f"{st}.osm.pbf",
                             "bbox": [round(v,6) for v in b]})
        cfg = OUT/f"_cfg_{COUNTRY_FILE[country]}.json"
        cfg.write_text(json.dumps({"directory": str(OUT), "extracts": extracts}))
        print(f"  {country}: cutting {len(todo)} chips from {pbf.name} ...", flush=True)
        r = subprocess.run(["osmium","extract","-c",str(cfg),"--overwrite",str(pbf)],
                           capture_output=True, text=True)
        if r.returncode: print(f"    osmium FAILED: {r.stderr[:300]}")
    n = len(list(OUT.glob("*.osm.pbf")))
    print(f"mini-extracts present: {n}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
