"""End-to-end orchestration: extent -> render -> infer -> mosaic -> GeoTIFF.

This module exists so that the QGIS dialog contains NO generation logic. Everything the
plugin's Run button does is here, and all of it is testable without QGIS running.

`progress` and `cancelled` are plain callables, so the QgsTask wrapper can report and
cancel without gencp_core knowing what a QgsTask is.
"""
from __future__ import annotations
import datetime, hashlib, json, os, tempfile
import os
from pathlib import Path

import numpy as np

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


class ExtentNotCovered(RuntimeError):
    """The chosen .osm.pbf yields NO features anywhere in the requested extent.

    Not a sparse-input warning. A sparse tile is a real condition with a real output, and
    the confidence layer already carries it. Zero features across the WHOLE extent means
    something different in kind: the file does not cover the area asked for, and every tile
    would be drawn from land cover alone. That produces a clean, plausible, entirely
    fictional mosaic - which is worse than an error, because it looks like a result.

    It happened. An Istanbul run of 567 tiles was generated against an Ankara test extract;
    `coverage_warnings` fired for 567 of 567 tiles and had no authority to stop anything,
    and a day of analysis was spent on the output before the provenance was read.

    Carries both bounding boxes so the message can show the mismatch rather than assert it.
    """

    def __init__(self, pbf_path, pbf_bounds, want_bounds, n_file=None):
        self.pbf_path = pbf_path
        self.pbf_bounds = pbf_bounds
        self.want_bounds = want_bounds
        self.n_file = n_file
        super().__init__(self.describe())

    @staticmethod
    def _fmt(b):
        if not b:
            return "unknown"
        return ("%.4f, %.4f  ->  %.4f, %.4f" % tuple(b))

    def describe(self):
        count = f"  ({self.n_file:,} features)" if self.n_file is not None else ""
        return (
            "The selected .osm.pbf does not cover this extent.\n"
            f"  file      : {Path(self.pbf_path).name}{count}\n"
            f"  it covers : {self._fmt(self.pbf_bounds)}\n"
            f"  requested : {self._fmt(self.want_bounds)}\n"
            "Every tile would be drawn from land cover alone, with no roads, buildings or "
            "water. Choose an extract that covers the requested area, or switch to "
            "Overpass.")


def _render_block(job):
    """Render one contiguous block of tiles in a worker process.

    Each worker parses the .osm.pbf ONCE for its own block. That repeats the parse K times
    across K workers, but the parses run concurrently, so the run pays about one parse of
    wall-clock instead of K - and it avoids shipping a 1.1 GB GeoDataFrame through pickle,
    which costs more than the parse it would save.
    """
    import json as _json
    from . import rasterize, vectors
    from . import extent as _ex
    (block, work_crs, work_dir, pbf, base_product, names) = job
    work_dir = Path(work_dir)
    index = None
    if pbf is not None:
        xs = [t[2] for t in block]
        ys = [t[3] for t in block]
        bounds = (min(xs), min(ys) - _ex.TILE_M, max(xs) + _ex.TILE_M, max(ys))
        index = vectors.PbfIndex(pbf, bounds, work_crs)
    out = []
    for (i, j, tx, ty) in block:
        p = work_dir / names[(i, j)]
        st = {}
        if not p.exists():
            b = (tx, ty - _ex.TILE_M, tx + _ex.TILE_M, ty)
            _render_one(p, b, work_crs, index, pbf, base_product, st)
        else:
            side = p.with_suffix(".stats.json")
            if side.is_file():
                try:
                    st = _json.loads(side.read_text())
                except (OSError, ValueError):
                    st = {}
        out.append(((i, j), str(p), st))
    return out


def _render_one(p, bounds, work_crs, index, pbf, base_product, st):
    """Render one tile to `p` ATOMICALLY, and write its stats sidecar.

    The rename matters under parallelism and cancellation both. A worker killed mid-write
    would otherwise leave a truncated .tif in the cache directory, and the next run's
    `p.exists()` check would treat it as a hit - a corrupt tile silently baked into a later
    mosaic. Rendering to a unique temporary name and renaming makes a cache entry either
    absent or complete, never half-written.
    """
    import json as _json
    import os as _os
    from . import rasterize
    tmp = p.with_name(f".{p.name}.{_os.getpid()}.tmp")
    try:
        rasterize.make_chip(bounds, work_crs, tmp,
                            gdf=(index.query(bounds, work_crs)
                                 if index is not None else None),
                            pbf=pbf, base_product=base_product, stats=st)
        _os.replace(tmp, p)
    finally:
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass
    try:
        p.with_suffix(".stats.json").write_text(_json.dumps(st))
    except OSError:                     # a read-only temp dir must not fail a run
        pass


def _index_reporter(progress, pbf):
    """Turn PbfIndex's stage names into pipeline progress events the UI can label.

    Emitted with done=0, total=0 so the bar does not jump: this stage has no measurable
    fraction, only a name. Saying WHICH stage is the point - "reading the country file,
    about two minutes, first run only" is a different user experience from a bar frozen
    at 0% saying "working".
    """
    if progress is None:
        return None
    import os as _os
    try:
        big = pbf is not None and _os.path.getsize(pbf) > 150 * 1024 * 1024
    except OSError:
        big = False

    def report(stage, _detail):
        if stage == "parse":
            progress("index_country" if big else "index_region", 0, 0)
        elif stage == "cache_write":
            progress("index_write", 0, 0)
    return report


def render_inputs(tiles, work_crs, work_dir, pbf=None, base_product="clcplus",
                  progress=None, cancelled=None, stats_out=None, workers=None,
                  index=None, index_progress=None):
    """Render every tile's input. Returns {(i, j): path to the 257 px GeoTIFF}.

    `stats_out`, if a dict is passed, receives {(i, j): {"n_osm_features": ...}}. The
    counts are also written to a JSON sidecar beside each cached render, so a cache HIT
    still knows how many OSM features the chip contains - otherwise the "this extent has
    no OSM coverage" warning would appear on the first run and silently vanish on the
    second. The sidecar is a separate file, never a tag inside the GeoTIFF, because
    gate_r.py compares those bytes.

    `workers` splits the tiles across processes. Threads were measured first and capped at
    1.28x on ten cores - the work is GIL-bound - so processes it is. Tiles are independent
    and each is written to its own file, so the output cannot depend on the order they
    finish; `gate_r_parallel.py` asserts that against a serial run rather than assuming it.
    """
    work_dir = Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    tiles = list(tiles)
    total = len(tiles)
    names = {(i, j): tile_cache_name(i, j, tx, ty, work_crs, base_product, pbf)
             for (i, j, tx, ty) in tiles}

    if workers is None:
        workers = default_workers()
    todo = [t for t in tiles if not (work_dir / names[(t[0], t[1])]).exists()]
    # One process is not worth its start-up, and neither is a pool for a handful of tiles.
    workers = 1 if (len(todo) < 2 * max(workers, 1) or workers <= 1) else min(workers, len(todo))

    out = {}
    if workers <= 1:
        for n, (i, j, tx, ty) in enumerate(tiles, 1):
            if cancelled is not None and cancelled():
                raise Cancelled()
            p = work_dir / names[(i, j)]
            side = p.with_suffix(".stats.json")
            st = {}
            if not p.exists():
                if index is None and pbf is not None:
                    from . import vectors
                    xs = [t[2] for t in tiles]
                    ys = [t[3] for t in tiles]
                    # Announce the index step. It is the longest single thing a run does
                    # on a country extract and it used to happen in complete silence, with
                    # the bar at 0% - which is indistinguishable from a hang and was read
                    # as one.
                    def _ip(stage, detail):
                        if index_progress is not None:
                            index_progress(stage, detail)
                    index = vectors.PbfIndex(
                        pbf, (min(xs), min(ys) - _extent.TILE_M,
                              max(xs) + _extent.TILE_M, max(ys)), work_crs,
                        progress=_ip)
                bounds = (tx, ty - _extent.TILE_M, tx + _extent.TILE_M, ty)
                _render_one(p, bounds, work_crs, index, pbf, base_product, st)
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

    # --- parallel ------------------------------------------------------------------
    import concurrent.futures as _cf
    import multiprocessing as _mp

    # Contiguous blocks, not round-robin: neighbouring tiles share OSM features, so a
    # block's index covers a compact area and stays small.
    k = workers
    blocks = [tiles[a * len(tiles) // k:(a + 1) * len(tiles) // k] for a in range(k)]
    blocks = [b for b in blocks if b]
    jobs = [(b, work_crs, str(work_dir), pbf, base_product,
             {(i, j): names[(i, j)] for (i, j, _, _) in b}) for b in blocks]

    ctx = _mp.get_context("spawn")
    exe, wenv = worker_python()
    # spawn re-imports __main__ in every child. A caller with no __main__ FILE - a heredoc,
    # `python -c`, an embedded interpreter - cannot be re-imported, and the children die on
    # a missing path. Cheap to detect, and the fallback is simply serial.
    import sys as _sys
    _mainfile = getattr(_sys.modules.get("__main__"), "__file__", None)
    if _mainfile is None:
        exe, wenv = None, {}
    usable, why = ((False, "the caller has no __main__ file to re-import")
                   if exe is None else workers_usable(exe, wenv))
    if not usable:
        # Refuse to guess. Spawning the host application instead of an interpreter, or
        # building a pool that will die halfway, are both worse than running serially.
        import logging
        logging.getLogger("gencp").info(
            "rendering serially: worker processes are unavailable (%s)", why)
        return render_inputs(tiles, work_crs, work_dir, pbf=pbf,
                             base_product=base_product, progress=progress,
                             cancelled=cancelled, stats_out=stats_out, workers=1)
    ctx.set_executable(exe)
    # Children inherit the parent environment at spawn. Set the override only around the
    # pool's life and put it back: PYTHONHOME is read at interpreter start-up, so this
    # cannot disturb the already-running parent.
    _saved = {k: os.environ.get(k) for k in wenv}
    os.environ.update(wenv)
    done_n = 0
    ex = _cf.ProcessPoolExecutor(max_workers=len(jobs), mp_context=ctx)
    try:
        futs = {ex.submit(_render_block, j): j for j in jobs}
        for fut in _cf.as_completed(futs):
            if cancelled is not None and cancelled():
                for f in futs:
                    f.cancel()
                raise Cancelled()
            rows = fut.result()
            for (ij, path, st) in rows:
                out[ij] = Path(path)
                if stats_out is not None:
                    stats_out[ij] = st
            # Honest progress: count tiles actually finished, never extrapolate. Blocks
            # finish unevenly because OSM density is uneven, so this advances in jumps -
            # but it never claims work that has not happened.
            done_n += len(rows)
            if progress is not None:
                progress(min(done_n, total), total)
    finally:
        ex.shutdown(wait=True, cancel_futures=True)
        for k, v in _saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    if progress is not None:
        progress(total, total)
    return {ij: out[ij] for ij in [(t[0], t[1]) for t in tiles] if ij in out}


def worker_python():
    """(interpreter, env overrides) safe to spawn workers with, or (None, {}).

    This is the difference between a speed-up and a catastrophe. `spawn` re-executes
    `sys.executable`, and inside QGIS that is the QGIS APPLICATION binary - so a pool
    would launch N copies of QGIS rather than N Python workers.

    QGIS ships a real interpreter beside its binary, but it cannot bootstrap on its own:
    it needs PYTHONHOME pointing at the prefix whose lib/pythonX.Y holds the stdlib. That
    is derived here rather than hard-coded, and if it cannot be derived the caller stays
    serial rather than guessing.
    """
    import sys as _sys
    exe = Path(_sys.executable)
    if exe.name.startswith("python"):
        return str(exe), {}
    cands = sorted((exe.parent / "bin").glob("python3*")) + sorted(exe.parent.glob("python3*"))
    tag = f"python{_sys.version_info.major}.{_sys.version_info.minor}"
    for cand in cands:
        if not (cand.is_file() and os.access(cand, os.X_OK)):
            continue
        for up in list(cand.parents)[:5]:
            if (up / "lib" / tag / "os.py").exists():
                return str(cand), {"PYTHONHOME": str(up)}
        return str(cand), {}
    return None, {}


_WORKERS_USABLE = {}


def workers_usable(exe, env):
    """Can a spawned worker actually import what it needs? Probed once, then cached.

    Asking is not paranoia. Inside QGIS on macOS the spawnable interpreter can import
    numpy, rasterio, shapely and geopandas but NOT osmium - the same code-signing split
    this project already documented for onnxruntime, where a native extension loads inside
    the signed application binary and refuses to load under the bundled python3.12. A pool
    built on that interpreter does not run slowly, it dies with BrokenProcessPool partway
    through a run. Better to find out in 200 ms and stay serial.
    """
    key = (exe, tuple(sorted(env.items())))
    if key in _WORKERS_USABLE:
        return _WORKERS_USABLE[key]
    import subprocess as _sp
    e = dict(os.environ)
    e.update(env)
    code = ("import numpy, rasterio, shapely, geopandas, osmium; print('ok')")
    try:
        r = _sp.run([exe, "-c", code], capture_output=True, timeout=120, env=e)
        ok = r.returncode == 0 and b"ok" in r.stdout
        why = "" if ok else (r.stderr.decode("utf-8", "replace").strip().splitlines() or [""])[-1]
    except Exception as exc:                       # noqa: BLE001
        ok, why = False, f"{type(exc).__name__}: {exc}"
    _WORKERS_USABLE[key] = (ok, why)
    return _WORKERS_USABLE[key]


def default_workers():
    """Physical-ish core count, leaving one for the UI thread."""
    import os as _os
    n = _os.cpu_count() or 4
    return max(1, min(10, n - 2))


def coverage_warnings(stats_by_tile, pbf=None):
    """Facts about tiles the vector source did not cover. STRUCTURED, not prose.

    Returns a list of dicts, each with a `kind` and the numbers behind it. It used to
    return English sentences, which the Turkish dialog then displayed under a Turkish
    heading - a half-translated warning box. gencp_core has no business holding user-facing
    prose in any language; the caller renders these in whatever language it speaks.

    Empty list when every tile had OSM features.
    """
    empty = sorted(k for k, s in (stats_by_tile or {}).items()
                   if s and s.get("n_osm_features", None) == 0)
    unknown = sorted(k for k, s in (stats_by_tile or {}).items() if not s)
    total = len(stats_by_tile or {})
    out = []
    if empty:
        out.append(dict(kind="zero_osm", n=len(empty), total=total,
                        tiles=[list(t) for t in empty[:6]],
                        more=max(0, len(empty) - 6),
                        source=(Path(pbf).name if pbf else None)))
    if unknown:
        out.append(dict(kind="count_unavailable", n=len(unknown), total=total))
    return out


def preview_image(render_path):
    """The rasterised input as a PIL image — what the dialog's Preview section shows."""
    import numpy as np
    import rasterio
    from PIL import Image
    with rasterio.open(render_path) as s:
        return Image.fromarray(np.moveaxis(s.read()[:3], 0, -1))


# The confidence score is signed and roughly spans [-4, +4]; it is carried through the
# existing, Gate-G-verified mosaic code as a uint8 image so the blending, the grid and the
# transform are literally the same code path as the picture. 8/255 of the range is 0.031 in
# score units, against band boundaries 0.62 apart, so the quantisation is immaterial.
SCORE_ENCODE_RANGE = 4.0


def _encode_score(score):
    a = (np.clip(np.asarray(score), -SCORE_ENCODE_RANGE, SCORE_ENCODE_RANGE)
         + SCORE_ENCODE_RANGE) / (2 * SCORE_ENCODE_RANGE)
    return np.repeat((a * 255.0).round().astype(np.uint8)[:, :, None], 3, axis=2)


def _decode_score(rgb):
    return (np.asarray(rgb, dtype=np.float64)[0] / 255.0) * (2 * SCORE_ENCODE_RANGE) \
        - SCORE_ENCODE_RANGE


def generate(extent_bbox, crs, model_path, out_tif=None, *, pbf=None,
             base_product="clcplus", overlap_m=DEFAULT_OVERLAP_M, dst_crs=None,
             work_dir=None, progress=None, cancelled=None, seam=True,
             confidence=False, stochastic_model=None, n_confidence_passes=16,
             confidence_seed=0, alpha_confidence=True, band_layer=False,
             write_osm=True, workers=None):
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

    # Coverage is checked BEFORE the first tile is rendered. The cost is one parse of the
    # extract, which the run pays anyway to build its index, so refusing takes seconds
    # rather than the three minutes a full generation would have taken before failing.
    if pbf is not None:
        from . import vectors as _v
        xs = [t[2] for t in tiles]
        ys = [t[3] for t in tiles]
        run_bounds = (min(xs), min(ys) - _extent.TILE_M,
                      max(xs) + _extent.TILE_M, max(ys))
        want4326 = _v._margin_bbox(run_bounds, work_crs)
        # Decide from the DECLARED bounds when the file has them. Geofabrik country files
        # do; osmium-cut extracts do not. This matters more than it looks: counting
        # features in the country file means parsing 9.1 M of them, 108 s and 11 GB, on
        # every single run - to answer a question its 23 ms header already answers.
        head = _v.pbf_header_bounds(pbf)
        if head is not None:
            disjoint = not (head[0] < want4326[2] and head[2] > want4326[0]
                            and head[1] < want4326[3] and head[3] > want4326[1])
            if disjoint:
                raise ExtentNotCovered(pbf, head, want4326, None)
            # Overlapping declared bounds: proceed. A file can still be empty over this
            # particular extent (a country file over open sea), and that case remains a
            # non-blocking per-tile warning rather than a block, because it is genuinely
            # ambiguous - the extract does cover the area, there is simply nothing in it.
        else:
            n_in, n_file, file_bounds = _v.pbf_coverage(pbf, want4326)
            if n_in == 0:
                raise ExtentNotCovered(pbf, file_bounds, want4326, n_file)

    tile_stats = {}
    renders = render_inputs(tiles, work_crs, work_dir / "render", pbf=pbf,
                            base_product=base_product,
                            progress=sub("render"), cancelled=cancelled,
                            stats_out=tile_stats, workers=workers,
                            index_progress=_index_reporter(progress, pbf))

    model = _infer.OnnxGenerator(model_path)
    fakes = {}
    total = len(tiles)
    for n, (key, path) in enumerate(renders.items(), 1):
        if cancelled is not None and cancelled():
            raise Cancelled()
        fakes[key] = model.run_image(preview_image(path))
        if progress is not None:
            progress("infer", n, total)

    # --- confidence, on the same tiles and the same grid -------------------------------
    conf_tiles = {}
    conf_meta = None
    if confidence:
        from . import confidence as _conf
        sto = None
        if _conf.needs_stochastic():
            # Only reachable if ACTIVE_SCORE is put back to a two-term score. Refused
            # rather than silently substituting a one-term score: bands calibrated on two
            # terms mean nothing computed from one.
            if not stochastic_model:
                raise ValueError(
                    f"score {_conf.ACTIVE_SCORE} needs the matching "
                    "*_stochastic_fp32.onnx export; without it the score is not the one "
                    "the bands were calibrated on")
            sto = _infer.StochasticOnnxGenerator(str(stochastic_model))
        for n, (key, path) in enumerate(renders.items(), 1):
            if cancelled is not None and cancelled():
                raise Cancelled()
            sig = _conf.signals(np.asarray(preview_image(path)))
            conf_s = None
            if sto is not None:
                spread, _m = sto.spread(preview_image(path),
                                        n_passes=n_confidence_passes,
                                        seed=confidence_seed)
                conf_s = -spread
            # conf_D lives on the 257 px RENDER (class assignment must see palette
            # colours before preprocess resizes them); the mosaic works on the model's
            # 256 px output grid. combined_score used to align them incidentally, via
            # conf_S's shape - dropping conf_S removed that, so the alignment is now
            # explicit rather than a side effect of a term that no longer exists.
            _field = _conf.align_to(sig["conf_D"], (_extent.OUT_PX, _extent.OUT_PX))
            conf_tiles[key] = _encode_score(
                _conf.deployed_score(_field, conf_s))
            if progress is not None:
                progress("confidence", n, len(renders))
        conf_meta = dict(score=_conf.ACTIVE_SCORE,
                         stochastic=bool(sto),
                         n_passes=(n_confidence_passes if sto else 0),
                         seed=(confidence_seed if sto else None),
                         model=(str(stochastic_model) if sto else None))

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
    if conf_tiles:
        from . import confidence as _conf
        crgb, _cv, ctransform = _mosaic.build(tiles, conf_tiles, work_crs, ext, overlap_m)
        score = _decode_score(crgb)
        bands = _conf.band_map(score)
        bands[~valid] = 0                      # nodata where the picture has no data
        verdict = _conf.run_verdict(score[valid]) if valid.any() else None
        cprov = dict(prov)
        cprov.update({
            "product": "GenCP confidence bands",
            "band_values": {"1": "red - do not use", "2": "amber - use with care",
                            "3": "green - usable", "0": "nodata"},
            "inference_path_image": "DETERMINISTIC - gencp_core.infer.OnnxGenerator",
            "inference_path_confidence": (
                (f"STOCHASTIC - dropout re-enabled via explicit noise inputs, "
                 f"{n_confidence_passes} draws, seed {confidence_seed}. The delivered "
                 f"image does NOT come from this path.")
                if conf_meta.get("stochastic") else
                ("DETERMINISTIC - computed from the rasterised INPUT alone (local "
                 "palette-class entropy). No inference of any kind is involved, so the "
                 "confidence map and the image cannot disagree about which model ran.")),
            "confidence": conf_meta,
            "calibration": _conf.CALIBRATION,
        })
        result["confidence"] = dict(verdict=verdict, provenance=cprov)
        result["_confidence_bands"] = bands
        result["_confidence_alpha"] = _conf.score_to_alpha(score, valid)
        if out_tif and band_layer:
            cpath = Path(out_tif).with_name(Path(out_tif).stem + "_confidence.tif")
            result["confidence"]["output"] = str(_mosaic.write_band_geotiff(
                cpath, bands, work_crs, ctransform, provenance=cprov,
                colours=_conf.BAND_COLOURS))

    # --- write, in this order: native image, then any reprojected copy, then extras ----
    if out_tif:
        alpha = result.get("_confidence_alpha") if alpha_confidence else None
        if alpha is not None:
            prov = dict(prov)
            prov.update({
                "alpha_band": ("CONTINUOUS confidence, not the three-band rounding: "
                               "alpha = clip((z(conf_D) + 4) / 8, 0, 1) * 255, so 255 is "
                               "the most confident. Invert with z = alpha/255*8 - 4."),
                "alpha_score": _conf.ACTIVE_SCORE,
                "alpha_calibration": _conf.CALIBRATION,
                "rgb_bands_unchanged": ("bands 1-3 are byte-identical to the validated "
                                        "3-band output; alpha is appended, never blended"),
            })
        result["output"] = str(_mosaic.write_geotiff(
            out_tif, rgb, work_crs, transform, provenance=prov, alpha=alpha))
        if dst_crs and str(dst_crs).upper() != str(work_crs).upper():
            rp = Path(out_tif).with_name(
                Path(out_tif).stem + "_" + str(dst_crs).replace(":", "").lower() + ".tif")
            result["output_reprojected"] = str(_mosaic.reproject_geotiff(
                result["output"], rp, dst_crs, provenance=prov))
        if write_osm and renders:
            opath = Path(out_tif).with_name(Path(out_tif).stem + "_osm.tif")
            result["osm_output"] = str(_mosaic.write_osm_mosaic(
                opath, list(renders.values()), provenance=prov))
    result["_rgb"] = rgb
    return result
