"""End-to-end orchestration: extent -> render -> infer -> mosaic -> GeoTIFF.

This module exists so that the QGIS dialog contains NO generation logic. Everything the
plugin's Run button does is here, and all of it is testable without QGIS running.

`progress` and `cancelled` are plain callables, so the QgsTask wrapper can report and
cancel without gencp_core knowing what a QgsTask is.
"""
from __future__ import annotations
import datetime, hashlib, json, os, tempfile
from pathlib import Path

from . import extent as _extent
from . import infer as _infer
from . import mosaic as _mosaic
from .extent import DEFAULT_OVERLAP_M


class Cancelled(Exception):
    """Raised when the caller's cancelled() returned True."""


def _sha256(path, limit=None):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        read = 0
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
            read += len(chunk)
            if limit and read >= limit:
                break
    return h.hexdigest()


def provenance(model_path, work_crs, extent_m, overlap_m, n_tiles, source, extra=None):
    """The record embedded in the output GeoTIFF.

    A consumer that finds a GCP wrong needs to know exactly what produced the raster.
    """
    p = Path(model_path)
    rec = {
        "tool": "gencp-qgis-plugin",
        "generated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "model_file": p.name,
        "model_sha256": _sha256(p),
        "model_mtime_utc": datetime.datetime.fromtimestamp(
            p.stat().st_mtime, datetime.timezone.utc).isoformat(),
        "inference_path": "deterministic (dropout removed; BatchNorm batch statistics)",
        "runtime": "onnxruntime CPUExecutionProvider",
        "true_gsd_m": _extent.TRUE_GSD,
        "output_gsd_m": _extent.NOMINAL,
        "working_crs": str(work_crs),
        "extent": list(extent_m),
        "overlap_m": overlap_m,
        "n_tiles": n_tiles,
        "vector_source": source,
        "snapping_rule": ("grid anchored at the reference extent NW corner exactly; "
                          "width/height = ceil(span / 10.0); east and south edges may "
                          "extend up to one pixel beyond the requested extent"),
    }
    rec.update(extra or {})
    return rec


def default_work_dir():
    """Where renders are cached when the caller names no directory.

    tempfile.gettempdir() honours TMPDIR on POSIX and TEMP/TMP on Windows; reading TMPDIR
    directly with a "/tmp" fallback would put the work directory at a non-existent
    absolute path on Windows. Exposed as a function because the dialog's Preview must
    write into the same place the run reads from.
    """
    return Path(tempfile.gettempdir()) / "gencp_work"


def _source_fingerprint(pbf):
    """Identify the OSM source by content, not by name.

    A user who re-downloads `turkey-latest.osm.pbf` keeps the path and changes the data.
    Size and mtime are cheap and change when the file does; hashing 18 GB on every render
    is not an option.
    """
    if not pbf:
        return "overpass"
    p = Path(pbf)
    try:
        st = p.stat()
        return f"{p.resolve()}|{st.st_size}|{st.st_mtime_ns}"
    except OSError:
        return str(p)


def tile_cache_name(i, j, tx, ty, work_crs, base_product="clcplus", pbf=None,
                    clc_path=None):
    """File name for one cached render. Carries everything that changes its pixels.

    Keyed on the tile INDEX alone - `t_0_0.tif` - a render of Ankara was silently reused
    for an extent 28 km to the south: byte-identical output, no error raised, and a
    Preview section that had correctly rendered the NEW extent, because the preview writes
    to a fresh temp directory while `generate` writes to a fixed one. The dialog's whole
    premise is "check the preview, then trust the output", and an index-only key severs
    exactly that link.

    This was measured, not reasoned about: `tubitak/tests/plugin_cache_probe.py` runs two
    different extents through `generate` and compares the rasters. It asserted True before
    this change and asserts False after it.

    The key deliberately includes the CLC+ path, because switching base rasters changes
    every pixel while leaving tile indices and coordinates identical.
    """
    from . import vectors
    key = "|".join([
        f"{tx!r}", f"{ty!r}", f"{_extent.TILE_M!r}", str(work_crs), str(base_product),
        _source_fingerprint(pbf), str(vectors.clc_path(clc_path)),
    ])
    return f"t_{i}_{j}_{hashlib.sha256(key.encode()).hexdigest()[:16]}.tif"


def render_inputs(tiles, work_crs, work_dir, pbf=None, base_product="clcplus",
                  progress=None, cancelled=None, stats_out=None):
    """Render every tile's input. Returns {(i, j): path to the 257 px GeoTIFF}.

    `stats_out`, if a dict is passed, receives {(i, j): {"n_osm_features": ...}}. The
    counts are also written to a JSON sidecar beside each cached render, so a cache HIT
    still knows how many OSM features the chip contains - otherwise the "this extent has
    no OSM coverage" warning would appear on the first run and silently vanish on the
    second. The sidecar is a separate file, never a tag inside the GeoTIFF, because
    gate_r.py compares those bytes.
    """
    from . import rasterize
    work_dir = Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    out = {}
    total = len(tiles)
    for n, (i, j, tx, ty) in enumerate(tiles, 1):
        if cancelled is not None and cancelled():
            raise Cancelled()
        p = work_dir / tile_cache_name(i, j, tx, ty, work_crs, base_product, pbf)
        side = p.with_suffix(".stats.json")
        st = {}
        if not p.exists():
            bounds = (tx, ty - _extent.TILE_M, tx + _extent.TILE_M, ty)
            rasterize.make_chip(bounds, work_crs, p, pbf=pbf, base_product=base_product,
                                stats=st)
            try:
                side.write_text(json.dumps(st))
            except OSError:                          # a read-only temp dir must not fail a run
                pass
        elif side.is_file():
            try:
                st = json.loads(side.read_text())
            except (OSError, ValueError):
                st = {}
        if stats_out is not None:
            stats_out[(i, j)] = st
        out[(i, j)] = p
        if progress is not None:
            progress(n, total)
    return out


def coverage_warnings(stats_by_tile, pbf=None):
    """Human-readable warnings about tiles the vector source did not cover.

    Returns a list of strings; empty when every tile had OSM features.
    """
    empty = [k for k, s in (stats_by_tile or {}).items()
             if s and s.get("n_osm_features", None) == 0]
    unknown = [k for k, s in (stats_by_tile or {}).items() if not s]
    msgs = []
    if empty:
        where = ("the .osm.pbf extract " + Path(pbf).name) if pbf else "Overpass"
        msgs.append(
            f"{len(empty)} of {len(stats_by_tile)} tile(s) contain ZERO OSM features "
            f"({', '.join(f'({i},{j})' for i, j in sorted(empty)[:6])}"
            f"{'…' if len(empty) > 6 else ''}). {where} returned nothing for that ground, "
            f"so those tiles are the CLC+ land-cover base alone: no roads, no buildings, "
            f"no water outlines. The result will look like plausible empty countryside "
            f"rather than like an error. Check that the extract covers this extent.")
    if unknown:
        msgs.append(f"{len(unknown)} tile(s) had no feature count available.")
    return msgs


def preview_image(render_path):
    """The rasterised input as a PIL image — what the dialog's Preview section shows."""
    import numpy as np
    import rasterio
    from PIL import Image
    with rasterio.open(render_path) as s:
        return Image.fromarray(np.moveaxis(s.read()[:3], 0, -1))


def generate(extent_bbox, crs, model_path, out_tif=None, *, pbf=None,
             base_product="clcplus", overlap_m=DEFAULT_OVERLAP_M, dst_crs=None,
             work_dir=None, progress=None, cancelled=None, seam=True):
    """Run the whole chain. Returns a dict describing what was produced.

    progress(stage, done, total) where stage is 'render' | 'infer' | 'mosaic'.
    """
    def sub(stage):
        if progress is None:
            return None
        return lambda d, t: progress(stage, d, t)

    ext, work_crs, src_crs = _extent.resolve(extent_bbox, crs)
    tiles, stride = _extent.tile_grid(ext, overlap_m)
    work_dir = Path(work_dir or default_work_dir())

    tile_stats = {}
    renders = render_inputs(tiles, work_crs, work_dir / "render", pbf=pbf,
                            base_product=base_product,
                            progress=sub("render"), cancelled=cancelled,
                            stats_out=tile_stats)

    model = _infer.OnnxGenerator(model_path)
    fakes = {}
    total = len(tiles)
    for n, (key, path) in enumerate(renders.items(), 1):
        if cancelled is not None and cancelled():
            raise Cancelled()
        fakes[key] = model.run_image(preview_image(path))
        if progress is not None:
            progress("infer", n, total)

    rgb, valid, transform = _mosaic.build(tiles, fakes, work_crs, ext, overlap_m,
                                          progress=sub("mosaic"))
    prov = provenance(model_path, work_crs, ext, overlap_m, len(tiles),
                      source=("local pbf: " + Path(pbf).name) if pbf else "overpass",
                      extra={"requested_crs": str(crs), "output_crs": str(dst_crs or work_crs)})
    result = dict(tiles=tiles, stride_m=stride, extent=ext, work_crs=str(work_crs),
                  transform=tuple(transform)[:6], shape=rgb.shape,
                  valid_fraction=float(valid.mean()), provenance=prov,
                  tile_stats={f"{i}_{j}": s for (i, j), s in tile_stats.items()},
                  warnings=coverage_warnings(tile_stats, pbf),
                  renders={f"{i}_{j}": str(p) for (i, j), p in renders.items()})
    if seam:
        result["seam"] = _mosaic.seam_metric(rgb, transform, tiles)
    if out_tif:
        result["output"] = str(_mosaic.write_geotiff(out_tif, rgb, work_crs, transform,
                                                     provenance=prov, dst_crs=dst_crs))
    result["_rgb"] = rgb
    return result
