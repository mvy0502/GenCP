#!/usr/bin/env python
"""gencp-ref: extent -> georeferenced 10 m synthetic reference raster.

The institutional deliverable: given an extent, produce a single georeferenced GeoTIFF
(10 m, requested CRS) their Georef software consumes as reference data, plus a
reliability sidecar (their "orman maskesi" request, as a continuous ranked score) and
an embedded provenance record.

    python tubitak/tool/gencp_ref.py --bbox XMIN YMIN XMAX YMAX --crs EPSG:32636 \
        --arm C3 --out tubitak/data/tool_runs/demo [--bands rgb] [--overlap-m 640] \
        [--align-origin E N] [--fetch-s2 DATE1/DATE2]

Design constraints inherited from the measurement phases, non-negotiable:
  * The corrected georeferencing (fix_georeferencing.py finding: 256 px of content
    span 257x10 m, TRUE_GSD = 2570/256) is hard-wired into the mosaic path. There is
    no code path that places a tile with the uncorrected 10.0 m transform.
  * OSM extraction uses `osmium extract -s smart` (default `simple` silently drops
    boundary-crossing multipolygons; corrections-log entry 6).
  * Adjacent tiles are generated independently and disagree at seams. Tiles overlap
    and are feather-blended, and residual seam energy is MEASURED and reported
    (gradient energy on seam-line buffers vs background), never eyeballed.
  * Band output is configurable; only "rgb" is implemented, "single" is reserved for
    the parallel panchromatic work package and refuses to run rather than invent an
    untested conversion.

Runs in the `gencp` conda environment. Inference reuses the repository's own test.py
(the byte-verified path from the evaluation phases) via subprocess, never a reimplementation.
"""
from __future__ import annotations
import argparse, hashlib, json, math, os, shutil, subprocess, sys, datetime
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tubitak" / "scripts"))
TOOL_VERSION = "0.1.0"
SRC_PX, OUT_PX, NOMINAL = 257, 256, 10.0
TRUE_GSD = SRC_PX * NOMINAL / OUT_PX          # 10.0390625 — the Option-A correction
TILE_M = SRC_PX * NOMINAL                     # 2570 m footprint per generated tile
GENCP_PY = sys.executable
OSMIUM = shutil.which("osmium") or str(Path(sys.executable).parent / "osmium")

ARMS = {
    "pretrained": ("GenCP_HR_demo/checkpoints", "genCP_HR_RGB_model"),
    "C1": ("tubitak/outputs/c1_checkpoints/checkpoints", "C1"),
    "C2": ("tubitak/outputs/c2_checkpoints/checkpoints", "C2"),
    "C3": ("tubitak/outputs/c3_checkpoints/checkpoints", "C3"),
}

GEOFABRIK_DIR = ROOT / "tubitak" / "data" / "geofabrik"
# Snapshot policy: prefer the dated, md5-recorded snapshots used by the render phases.
SNAPSHOT_PREFERENCE = ["turkey-latest.osm.pbf"]  # extended by --osm-pbf

PAL = {"light_green": (133, 224, 133), "no_veg": (195, 186, 141), "forest": (0, 153, 51),
       "gray": (204, 204, 204), "water": (128, 204, 255), "building": (165, 42, 42),
       "white": (255, 255, 255), "black": (0, 0, 0)}


def log(msg):
    print(f"[gencp-ref] {msg}", flush=True)


def utm_for(lon, lat):
    zone = int((lon + 180) // 6) + 1
    return f"EPSG:{32600 + zone if lat >= 0 else 32700 + zone}"


def resolve_extent(args):
    from pyproj import Transformer
    if args.vector:
        gj = json.loads(Path(args.vector).read_text())
        from shapely.geometry import shape
        geoms = [shape(f["geometry"]) for f in gj.get("features", [gj])]
        from shapely.ops import unary_union
        g = unary_union(geoms)
        xmin, ymin, xmax, ymax = g.bounds
        src_crs = args.crs or "EPSG:4326"
    else:
        xmin, ymin, xmax, ymax = args.bbox
        src_crs = args.crs
    if src_crs.upper() in ("EPSG:4326",):
        work = utm_for((xmin + xmax) / 2, (ymin + ymax) / 2)
        tr = Transformer.from_crs(src_crs, work, always_xy=True)
        xs, ys = zip(*[tr.transform(x, y) for x, y in
                       [(xmin, ymin), (xmin, ymax), (xmax, ymin), (xmax, ymax)]])
        return (min(xs), min(ys), max(xs), max(ys)), work, src_crs
    return (xmin, ymin, xmax, ymax), src_crs, src_crs


def tile_grid(extent, overlap_m, align_origin=None):
    xmin, ymin, xmax, ymax = extent
    stride = TILE_M - overlap_m
    if align_origin:
        ox, oy = align_origin        # NW corner of tile (0,0) — gate mode
    else:
        ox, oy = xmin, ymax
    tiles = []
    j = 0
    while True:
        ty = oy - j * stride
        if ty - TILE_M > ymax and j > 0:
            j += 1
            continue
        i = 0
        placed = False
        while True:
            tx = ox + i * stride
            if tx > xmax:
                break
            tiles.append((i, j, tx, ty))
            placed = True
            if tx + TILE_M >= xmax + overlap_m:
                break
            i += 1
        if ty - TILE_M <= ymin:
            break
        j += 1
        if not placed and j > 4096:
            raise RuntimeError("tile grid runaway")
    return tiles, stride


def osm_window(extent, work_crs, out_pbf, extra_pbfs):
    """One `-s smart` extract covering the extent (+margin), merged across snapshots."""
    from pyproj import Transformer
    xmin, ymin, xmax, ymax = extent
    m = 500.0
    tr = Transformer.from_crs(work_crs, "EPSG:4326", always_xy=True)
    lons, lats = zip(*[tr.transform(x, y) for x, y in
                       [(xmin - m, ymin - m), (xmin - m, ymax + m),
                        (xmax + m, ymin - m), (xmax + m, ymax + m)]])
    bbox = f"{min(lons)},{min(lats)},{max(lons)},{max(lats)}"
    sources = []
    for name in SNAPSHOT_PREFERENCE + list(extra_pbfs or []):
        p = (GEOFABRIK_DIR / name) if not os.path.isabs(str(name)) else Path(name)
        if p.exists():
            sources.append(p)
    if not sources:
        raise SystemExit("no Geofabrik snapshot found; pass --osm-pbf")
    parts = []
    for k, src in enumerate(sources):
        part = out_pbf.with_suffix(f".part{k}.pbf")
        r = subprocess.run([OSMIUM, "extract", "-s", "smart", "-b", bbox,
                            "-o", str(part), "--overwrite", str(src)],
                           capture_output=True, text=True)
        if r.returncode == 0 and part.exists() and part.stat().st_size > 100:
            parts.append(part)
        log(f"osm extract {src.name}: rc={r.returncode} size={part.stat().st_size if part.exists() else 0}")
    if not parts:
        raise SystemExit("osmium produced no data for this extent (outside snapshot coverage?)")
    if len(parts) == 1:
        shutil.move(parts[0], out_pbf)
    else:
        subprocess.run([OSMIUM, "merge", *map(str, parts), "-o", str(out_pbf),
                        "--overwrite"], check=True)
        for p in parts:
            p.unlink(missing_ok=True)
    return out_pbf, [s.name for s in sources]


def render_tiles(tiles, work_crs, pbf, render_dir):
    import warnings
    warnings.filterwarnings("ignore")
    import osm_to_raster as OTR
    render_dir.mkdir(parents=True, exist_ok=True)
    made = 0
    for n, (i, j, tx, ty) in enumerate(tiles):
        out = render_dir / f"t_{i}_{j}.tif"
        if out.exists():
            made += 1
            continue
        bounds = (tx, ty - TILE_M, tx + TILE_M, ty)
        OTR.make_chip(bounds, work_crs, out, pbf=str(pbf), base_product="clcplus")
        made += 1
        if made % 5 == 0 or made == len(tiles):
            log(f"render {made}/{len(tiles)} tiles")
    # PNG copies for the inference dataloader
    from PIL import Image
    import rasterio
    png_dir = render_dir / "png"
    png_dir.mkdir(exist_ok=True)
    for i, j, tx, ty in tiles:
        png = png_dir / f"t_{i}_{j}.png"
        if png.exists():
            continue
        with rasterio.open(render_dir / f"t_{i}_{j}.tif") as s:
            Image.fromarray(np.moveaxis(s.read()[:3], 0, -1)).save(png)
    return png_dir


def infer(png_dir, arm, work_dir, n_tiles, seed, deterministic):
    """Inference through the repository's own test.py — the evaluated path.

    pix2pix applies dropout at test time BY DESIGN (its noise source in place of a z
    vector; corrections-log entry 14), so this path is stochastic. The tool therefore
    pins a SEED via a sitecustomize shim on the subprocess (reproducibility without
    changing the distribution every evaluation measured). --deterministic instead passes
    --no_dropout, which drops the parameterless Dropout modules from the generator and
    leaves normalisation untouched — deliberately NOT --eval, whose BatchNorm switch is
    a different, output-shifting effect that must not be conflated with dropout.
    """
    ckdir, name = ARMS[arm]
    res = work_dir / "inference"
    shim = work_dir / "_seedshim"
    shim.mkdir(parents=True, exist_ok=True)
    (shim / "sitecustomize.py").write_text(
        "import random, numpy, torch\n"
        f"SEED = {int(seed)}\n"
        "random.seed(SEED); numpy.random.seed(SEED)\n"
        "torch.manual_seed(SEED); torch.cuda.manual_seed_all(SEED)\n")
    env = dict(os.environ)
    env["PYTHONPATH"] = str(shim) + ((os.pathsep + env["PYTHONPATH"]) if env.get("PYTHONPATH") else "")
    cmd = [GENCP_PY, str(ROOT / "test.py"), "--dataroot", str(png_dir), "--name", name,
           "--checkpoints_dir", str(ROOT / ckdir), "--model", "test", "--netG", "unet_256",
           "--norm", "batch", "--dataset_mode", "single", "--load_size", "256",
           "--crop_size", "256", "--num_test", str(n_tiles), "--gpu_ids", "-1",
           "--results_dir", str(res)]
    if deterministic:
        cmd.append("--no_dropout")
    log(f"inference: arm={arm} tiles={n_tiles} seed={seed} "
        f"path={'deterministic (dropout off; default)' if deterministic else 'stochastic (evaluated; --stochastic)'}")
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, env=env)
    if r.returncode != 0:
        sys.exit(f"inference failed:\n{r.stderr[-2000:]}")
    imgs = res / name / "test_latest" / "images"
    fakes = sorted(imgs.glob("*_fake.png"))
    if len(fakes) < n_tiles:
        sys.exit(f"inference produced {len(fakes)}/{n_tiles} tiles")
    ck = ROOT / ckdir / name / "latest_net_G.pth"
    sha = hashlib.sha256(ck.read_bytes()).hexdigest()
    return imgs, sha


def feather_weight(overlap_px):
    """Separable raised-cosine ramp over the overlap margin, 1.0 in the interior."""
    w1 = np.ones(OUT_PX)
    r = max(overlap_px, 1)
    ramp = 0.5 - 0.5 * np.cos(np.pi * (np.arange(r) + 0.5) / r)
    w1[:r] = ramp
    w1[-r:] = ramp[::-1]
    return np.outer(w1, w1)


def mosaic(tiles, imgs_dir, work_crs, extent, overlap_m, out_tif, dst_crs, bands):
    import warnings
    warnings.filterwarnings("ignore")
    import rasterio
    from rasterio.transform import Affine
    from rasterio.warp import reproject, Resampling
    from PIL import Image
    xmin, ymin, xmax, ymax = extent
    W = int(math.ceil((xmax - xmin) / NOMINAL))
    H = int(math.ceil((ymax - ymin) / NOMINAL))
    target = Affine(NOMINAL, 0, xmin, 0, -NOMINAL, ymax)
    acc = np.zeros((3, H, W), np.float64)
    wac = np.zeros((H, W), np.float64)
    ov_px = int(round(overlap_m / TRUE_GSD))
    wtile = feather_weight(ov_px)
    for n, (i, j, tx, ty) in enumerate(tiles):
        arr = np.moveaxis(np.asarray(Image.open(imgs_dir / f"t_{i}_{j}_fake.png").convert("RGB"), np.float64), -1, 0)
        # THE CORRECTED TRANSFORM — hard-wired; no 10.0 m code path exists for tiles.
        src_T = Affine(TRUE_GSD, 0, tx, 0, -TRUE_GSD, ty)
        wa = np.zeros((H, W), np.float64)
        reproject(wtile, wa, src_transform=src_T, src_crs=work_crs,
                  dst_transform=target, dst_crs=work_crs, resampling=Resampling.bilinear)
        for b in range(3):
            da = np.zeros((H, W), np.float64)
            reproject(arr[b] * wtile, da, src_transform=src_T, src_crs=work_crs,
                      dst_transform=target, dst_crs=work_crs, resampling=Resampling.bilinear)
            acc[b] += da
        wac += wa
        if (n + 1) % 5 == 0 or n + 1 == len(tiles):
            log(f"mosaic {n+1}/{len(tiles)}")
    valid = wac > 1e-6
    out = np.zeros((3, H, W), np.uint8)
    for b in range(3):
        out[b][valid] = np.clip(np.round(acc[b][valid] / wac[valid]), 0, 255)
    if bands == "single":
        sys.exit("--bands single is reserved for the panchromatic work package; "
                 "no tested single-band conversion exists yet. Refusing to invent one.")
    prof = dict(driver="GTiff", height=H, width=W, count=3, dtype="uint8",
                crs=work_crs, transform=target, nodata=0, compress="deflate")
    tmp = out_tif.with_suffix(".native.tif")
    with rasterio.open(tmp, "w", **prof) as d:
        d.write(out)
    if dst_crs and dst_crs.upper() != str(work_crs).upper():
        from rasterio.warp import calculate_default_transform
        with rasterio.open(tmp) as s:
            t2, w2, h2 = calculate_default_transform(s.crs, dst_crs, s.width, s.height, *s.bounds,
                                                     resolution=NOMINAL)
            prof2 = prof | dict(crs=dst_crs, transform=t2, width=w2, height=h2)
            with rasterio.open(out_tif, "w", **prof2) as d:
                for b in range(1, 4):
                    reproject(rasterio.band(s, b), rasterio.band(d, b),
                              resampling=Resampling.bilinear)
        tmp.unlink()
    else:
        shutil.move(tmp, out_tif)
    return out_tif, (H, W), valid, target


def seam_metric(mosaic_tif, tiles):
    """Gradient energy in ±2 px buffers around interior tile edges vs elsewhere."""
    import rasterio
    from scipy.ndimage import sobel
    with rasterio.open(mosaic_tif) as s:
        g = s.read().astype(float).mean(axis=0)
        T = s.transform
    gm = np.hypot(sobel(g, 0), sobel(g, 1))
    H, W = g.shape
    mask = np.zeros((H, W), bool)
    xs = sorted({tx for _, _, tx, _ in tiles})[1:]          # interior vertical seam lines
    ys = sorted({ty for _, _, _, ty in tiles}, reverse=True)[1:]
    inv = ~T
    for x in xs:
        for edge in (x, x + TILE_M):  # both edges of the overlap band
            c, _ = inv * (edge, 0)
            c = int(round(c))
            if 2 <= c < W - 2:
                mask[:, c - 2:c + 3] = True
    for y in ys:
        for edge in (y, y - TILE_M):
            _, r = inv * (0, edge)
            r = int(round(r))
            if 2 <= r < H - 2:
                mask[r - 2:r + 3, :] = True
    if not mask.any() or mask.all():
        return None
    seam = float(gm[mask].mean())
    back = float(gm[~mask].mean())
    return dict(seam_grad=seam, background_grad=back,
                ratio=seam / back if back > 0 else float("inf"),
                seam_px=int(mask.sum()))


def reliability(tiles, render_dir, extent, work_crs, out_tif, out_csv):
    """Continuous per-tile score from INPUT PROPERTIES ONLY. Weights are documented
    design choices reflecting the institution's stated class preferences (coastline,
    road, building useful; forest maskable) — NOT fitted to any outcome (the fitted
    single-threshold veto failed held-out; gcp-veto-rule-results.md)."""
    import warnings
    warnings.filterwarnings("ignore")
    import rasterio
    from rasterio.transform import Affine
    from scipy.ndimage import sobel
    import csv as _csv
    anchors = np.array(list(PAL.values()), float)
    names = list(PAL.keys())
    rows = []
    for i, j, tx, ty in tiles:
        with rasterio.open(render_dir / f"t_{i}_{j}.tif") as s:
            a = np.moveaxis(s.read()[:3], 0, -1).astype(float)
        g = a.mean(axis=2)
        dens = float((np.hypot(sobel(g, 0), sobel(g, 1)) > 20).mean())
        lab = ((a.reshape(-1, 1, 3) - anchors.reshape(1, -1, 3)) ** 2).sum(-1).argmin(1).reshape(a.shape[:2])
        frac = {n: float((lab == k).mean()) for k, n in enumerate(names)}
        bnd = float((np.diff(lab, axis=0) != 0).mean() + (np.diff(lab, axis=1) != 0).mean()) / 2
        wmask = lab == names.index("water")
        wedge = float(((np.diff(wmask.astype(int), axis=0) != 0).mean()
                       + (np.diff(wmask.astype(int), axis=1) != 0).mean()) / 2)
        # NOTE: the argmin above assigns EVERY pixel a palette class, so
        # 1.0 - sum(frac.values()) is identically ~0 (float dust only). This term
        # therefore reduces to building + gray — i.e. building is effectively
        # double-weighted in the score, and the original "non-palette = cased
        # roads" reading never applied. The expression is kept verbatim because
        # the delivered rankings (tool-results.md) were produced with it;
        # changing the formula requires a re-registration, not a silent edit.
        road_bldg = 1.0 - sum(frac.values()) + frac["building"] + frac["gray"]
        score = (1.0 * dens + 0.5 * bnd + 0.5 * max(road_bldg, 0.0)
                 + 0.5 * frac["building"] + 0.5 * wedge
                 - 0.3 * frac["forest"] - 0.5 * frac["water"])
        rows.append(dict(i=i, j=j, x=tx, y=ty, dens=round(dens, 5), boundary=round(bnd, 5),
                         building=round(frac["building"], 5), forest=round(frac["forest"], 5),
                         water=round(frac["water"], 5), water_edge=round(wedge, 5),
                         score=round(float(score), 5)))
    rows.sort(key=lambda r: -r["score"])
    for rank, r in enumerate(rows, 1):
        r["rank"] = rank
    with open(out_csv, "w", newline="") as f:
        w = _csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    xmin, ymin, xmax, ymax = extent
    W = int(math.ceil((xmax - xmin) / NOMINAL))
    H = int(math.ceil((ymax - ymin) / NOMINAL))
    target = Affine(NOMINAL, 0, xmin, 0, -NOMINAL, ymax)
    rel = np.full((H, W), np.nan, np.float32)
    inv = ~target
    for r in rows:
        c0, r0 = inv * (r["x"], r["y"])
        c1, r1 = inv * (r["x"] + TILE_M, r["y"] - TILE_M)
        rel[max(int(r0), 0):int(r1), max(int(c0), 0):int(c1)] = r["score"]
    with rasterio.open(out_tif, "w", driver="GTiff", height=H, width=W, count=1,
                       dtype="float32", crs=work_crs, transform=target, nodata=np.nan,
                       compress="deflate") as d:
        d.write(rel, 1)
    return out_csv


def fetch_s2_preview(extent, work_crs, daterange, out_tif):
    """Optional QA companion: windowed S2 L2A RGB from Earth Search STAC (COG /vsicurl).
    NOT part of the generation path — the synthetic reference is produced without it."""
    import requests, rasterio
    from rasterio.warp import transform_bounds, reproject, Resampling
    from rasterio.windows import from_bounds
    from rasterio.transform import Affine
    xmin, ymin, xmax, ymax = extent
    bb = transform_bounds(work_crs, "EPSG:4326", xmin, ymin, xmax, ymax)
    q = dict(collections=["sentinel-2-l2a"], bbox=list(bb), datetime=daterange,
             limit=1, query={"eo:cloud_cover": {"lt": 20}},
             sortby=[{"field": "properties.eo:cloud_cover", "direction": "asc"}])
    r = requests.post("https://earth-search.aws.element84.com/v1/search", json=q, timeout=60)
    r.raise_for_status()
    feats = r.json().get("features", [])
    if not feats:
        log("s2: no scene found for the window; skipping preview")
        return None
    it = feats[0]
    sid = it["id"]
    hrefs = [it["assets"][b]["href"] for b in ("red", "green", "blue")]
    W = int(math.ceil((xmax - xmin) / NOMINAL)); H = int(math.ceil((ymax - ymin) / NOMINAL))
    target = Affine(NOMINAL, 0, xmin, 0, -NOMINAL, ymax)
    out = np.zeros((3, H, W), np.uint16)
    for b, href in enumerate(hrefs):
        with rasterio.open(href) as s:
            wb = transform_bounds(work_crs, s.crs, xmin, ymin, xmax, ymax)
            win = from_bounds(*wb, s.transform)
            arr = s.read(1, window=win)
            reproject(arr, out[b], src_transform=s.window_transform(win), src_crs=s.crs,
                      dst_transform=target, dst_crs=work_crs, resampling=Resampling.bilinear)
        log(f"s2 band {b+1}/3 windowed from {sid}")
    with rasterio.open(out_tif, "w", driver="GTiff", height=H, width=W, count=3,
                       dtype="uint16", crs=work_crs, transform=target, compress="deflate") as d:
        d.write(out)
    return sid


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bbox", nargs=4, type=float, metavar=("XMIN", "YMIN", "XMAX", "YMAX"))
    ap.add_argument("--vector", help="GeoJSON whose union bounds define the extent")
    ap.add_argument("--crs", required=True, help="CRS of --bbox AND of the output")
    ap.add_argument("--arm", choices=list(ARMS), default="C3")
    ap.add_argument("--bands", choices=["rgb", "single"], default="rgb")
    # 640 m default from the registered seam experiment (tool-gate-registration-2.md,
    # Task 2): at 160/320 m the registered inadequacy criteria do not fire, but seam
    # attraction of matched points is statistically detectable (p=0.029 / p=0.003); at
    # 640 m it vanishes (obs/exp 1.01, p=0.46; seam ratio 1.008). The failure mode is
    # delivering false control points into a matcher we cannot observe, so we take the
    # safe side of our own threshold and pay ~44% duplicate generation — the same
    # reasoning that discarded the C1 warm-up run. 160 m is the economy setting
    # (12% duplication) for previews; it passes the registered criteria but carries the
    # measured p=0.029 clustering signal.
    ap.add_argument("--overlap-m", type=float, default=640.0)
    ap.add_argument("--seed", type=int, default=42)
    # DEFAULT: deterministic (dropout disabled at inference). Decision 2026-08-21: a
    # delivered tool must satisfy "same input -> same output" UNCONDITIONALLY; seed-pinned
    # reproducibility holds only for one library build on one machine, dropout-off holds
    # everywhere. Measured cost is zero at the n=30 resolution (regA: every arm within
    # +/-0.05 px, SE ~0.077 -> shifts larger than ~0.15 px are excluded, smaller ones are
    # not). The evaluated stochastic path stays available via --stochastic; provenance
    # records which path produced every file.
    ap.add_argument("--stochastic", action="store_true",
                    help="use the evaluated dropout-active path (seeded); NON-default")
    ap.add_argument("--align-origin", nargs=2, type=float, metavar=("E", "N"),
                    help="pin tile (0,0) NW corner (gate/reproducibility mode)")
    ap.add_argument("--osm-pbf", nargs="*", default=[], help="additional snapshot pbf(s)")
    ap.add_argument("--fetch-s2", metavar="D1/D2", help="optional QA preview, e.g. 2026-04-01/2026-05-01")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    if not a.bbox and not a.vector:
        ap.error("need --bbox or --vector")
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    extent, work_crs, _ = resolve_extent(a)
    tiles, stride = tile_grid(extent, a.overlap_m, tuple(a.align_origin) if a.align_origin else None)
    log(f"extent {tuple(round(v,1) for v in extent)} in {work_crs}; {len(tiles)} tiles, "
        f"stride {stride} m, overlap {a.overlap_m} m")
    pbf, snapshots = osm_window(extent, work_crs, out / "extent.osm.pbf", a.osm_pbf)
    png_dir = render_tiles(tiles, work_crs, pbf, out / "renders")
    imgs, ck_sha = infer(png_dir, a.arm, out, len(tiles), a.seed, not a.stochastic)
    mosaic_tif = out / "reference.tif"
    mosaic_tif, shape, _, _ = mosaic(tiles, imgs, work_crs, extent, a.overlap_m,
                                     mosaic_tif, a.crs, a.bands)
    sm = seam_metric(mosaic_tif, tiles) if len(tiles) > 1 else None
    if sm:
        log(f"SEAM METRIC: seam grad {sm['seam_grad']:.3f} vs background {sm['background_grad']:.3f} "
            f"-> ratio {sm['ratio']:.3f} over {sm['seam_px']} px")
    rel_csv = reliability(tiles, out / "renders", extent, work_crs,
                          out / "reliability.tif", out / "reliability.csv")
    s2_id = fetch_s2_preview(extent, work_crs, a.fetch_s2, out / "s2_preview.tif") if a.fetch_s2 else None
    git = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
                         text=True).stdout.strip()
    import rasterio
    import torch
    prov = dict(tool=f"gencp-ref {TOOL_VERSION}", generated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                arm=a.arm, checkpoint_sha256=ck_sha, repo_commit=git,
                seed=a.seed, torch_version=torch.__version__,
                inference_path=("deterministic (dropout off; DEFAULT)" if not a.stochastic else
                                "stochastic (dropout active - the evaluated configuration; --stochastic)"),
                osm_snapshots=";".join(snapshots),
                clcplus="CLMS_CLCplus_RASTER_2021_010m_eu_03035_V1_1",
                s2_preview_scene=s2_id or "none",
                true_gsd=f"{TRUE_GSD} (corrected: 257*10/256; fix_georeferencing.py finding)",
                tiles=len(tiles), overlap_m=a.overlap_m,
                seam_ratio=f"{sm['ratio']:.4f}" if sm else "n/a (single tile)",
                bands=a.bands, extent_crs=a.crs)
    with rasterio.open(mosaic_tif, "r+") as d:
        d.update_tags(**{f"GENCP_{k.upper()}": str(v) for k, v in prov.items()})
    (out / "reference.provenance.txt").write_text(
        "\n".join(f"{k}: {v}" for k, v in prov.items()) + "\n")
    log(f"DONE: {mosaic_tif} ({shape[1]}x{shape[0]}), reliability.csv (ranked), provenance embedded")
    return 0


if __name__ == "__main__":
    sys.exit(main())
