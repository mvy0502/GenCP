"""Fetch a Geofabrik country extract, and prove the bytes arrived intact.

Why this exists. The plugin's local vector source was built for the measurement phase,
whose OSM came from per-chip extracts cut from country files that were already on the
machine. A user outside Ankara has no local source at all, and the fallback - Overpass -
is not a serious answer for a real scene: a 567-tile Istanbul run means 567 queries against
a rate-limited public API, over a network the institution may not want in the loop, and the
API returns whatever OSM looks like at that moment, so two runs of the same extent are not
comparable. A dated local file fixes all three.

No Qt here, by the rule that `gencp_core` stays importable outside QGIS
(`tubitak/tests/test_no_qgis_imports.py` enforces it). Progress and cancellation are
delivered through plain callables, and the plugin wraps this in a QgsTask.

The verification is the point. A truncated .osm.pbf is not a loud failure: it opens, it
parses, and it yields fewer features over part of the extent - which looks exactly like
countryside. This project has already been bitten by an extract that silently did not cover
the area asked for. So a download is not finished when the bytes stop arriving; it is
finished when the size and the published MD5 both match, and until then it lives under a
`.part` name that nothing else will pick up.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE = "https://download.geofabrik.de"
UA = "gencp-qgis-plugin (+https://github.com/mvy0502/gencp-validation)"

#: Region key -> Geofabrik path. Turkey is the one this project needs; the map exists so
#: adding a neighbour is a one-line change rather than a new function.
REGIONS = {
    "turkey": "europe/turkey",
}

#: Where else the same file can be fetched when Geofabrik will not serve it. Geofabrik
#: answered 502 and 503 for the .pbf for a sustained period while the .md5 stayed up, and a
#: user in front of a supervisor cannot be told "try again later". The mirror is a pinned
#: snapshot published on our own release, so it is a fixed date rather than "latest" - which
#: is stated in the UI, because which file you got changes what you can reproduce.
MIRRORS = {
    "turkey": ("https://github.com/mvy0502/gencp-validation/releases/download/"
               "osm-turkey-2026-08-19/turkey-2026-08-19.osm.pbf"),
}

#: MD5 of each pinned mirror. The mirror is a fixed file, so unlike Geofabrik's moving
#: "latest" checksum this one can be pinned here and checked - a mirror that is not
#: verified is just a second way to get a corrupt file.
MIRROR_MD5 = {
    "turkey": "76af5efb51c5ef9fcb738795753a402a",
}

#: Only used when the server refuses to state a size, and labelled as approximate wherever
#: it is shown. Geofabrik answers HEAD and Range on the .pbf with 502/503 under load, so
#: "unknown" is a normal outcome, not an error - but showing nothing before starting a
#: multi-hundred-megabyte download is worse than showing a figure marked approximate.
APPROX_SIZE_BYTES = {"turkey": 642_000_000}

CHUNK = 1 << 20          # 1 MiB
CONNECT_TIMEOUT = 60     # Geofabrik answers slowly under load and 503s when overloaded


class GeofabrikError(RuntimeError):
    """Anything that stops us handing back a verified file."""


def urls(region="turkey"):
    """(.pbf url, .md5 url) for a region key."""
    try:
        path = REGIONS[region]
    except KeyError:
        raise GeofabrikError(f"unknown region {region!r}; known: {sorted(REGIONS)}")
    pbf = f"{BASE}/{path}-latest.osm.pbf"
    return pbf, pbf + ".md5"


def _open(url, extra_headers=None, timeout=CONNECT_TIMEOUT):
    h = {"User-Agent": UA}
    h.update(extra_headers or {})
    return urlopen(Request(url, headers=h), timeout=timeout)


def remote_md5(region="turkey", timeout=CONNECT_TIMEOUT):
    """The MD5 Geofabrik publishes beside the extract, or None if it cannot be read.

    The .md5 is a tiny file and stays available even when the multi-hundred-megabyte
    .pbf is 503ing, which makes it the cheapest way to ask "is my copy current?".
    """
    _, md5_url = urls(region)
    try:
        with _open(md5_url, timeout=timeout) as r:
            first = r.read(4096).decode("utf-8", "replace").split()
            return first[0].lower() if first else None
    except (HTTPError, URLError, OSError):
        return None


def remote_size(region="turkey", timeout=CONNECT_TIMEOUT):
    """Size of the extract in bytes, or None if the server will not say.

    Three ways are tried because Geofabrik does not answer all of them. A HEAD on the
    .pbf returns 503 rather than a size, so it is tried last, not first.
    """
    pbf_url, _ = urls(region)
    # 1. a one-byte range request: cheapest, and Content-Range carries the total
    try:
        with _open(pbf_url, {"Range": "bytes=0-0"}, timeout) as r:
            cr = r.headers.get("Content-Range")
            if cr and "/" in cr:
                total = cr.rsplit("/", 1)[1].strip()
                if total.isdigit():
                    return int(total)
    except (HTTPError, URLError, OSError):
        pass
    # 2. a normal GET, reading only the headers before closing
    try:
        with _open(pbf_url, timeout=timeout) as r:
            n = r.headers.get("Content-Length")
            if n and n.isdigit():
                return int(n)
    except (HTTPError, URLError, OSError):
        pass
    # 3. HEAD, which Geofabrik currently answers with 503 for large files
    try:
        req = Request(pbf_url, method="HEAD", headers={"User-Agent": UA})
        with urlopen(req, timeout=timeout) as r:
            n = r.headers.get("Content-Length")
            if n and n.isdigit():
                return int(n)
    except (HTTPError, URLError, OSError):
        pass
    return None


def file_md5(path, progress=None, cancel=None):
    """MD5 of a local file, streamed. `progress(done, total)` is called as it goes."""
    path = Path(path)
    total = path.stat().st_size
    h = hashlib.md5()
    done = 0
    with open(path, "rb") as f:
        while True:
            if cancel is not None and cancel():
                return None
            b = f.read(CHUNK)
            if not b:
                break
            h.update(b)
            done += len(b)
            if progress is not None:
                progress(done, total)
    return h.hexdigest()


def local_status(path, region="turkey", want_md5=None, progress=None):
    """Describe a local copy WITHOUT downloading: missing, current, stale, or unverifiable.

    `want_md5` lets a caller pass an already-fetched remote checksum rather than paying
    for the request twice.
    """
    path = Path(path)
    if not path.exists():
        return {"state": "missing", "path": str(path)}
    size = path.stat().st_size
    remote = want_md5 if want_md5 is not None else remote_md5(region)
    if remote is None and MIRROR_MD5.get(region) is None:
        return {"state": "unverifiable", "path": str(path), "size": size,
                "reason": "the published checksum could not be fetched"}
    have = file_md5(path, progress=progress)
    # The pinned mirror is a DATED file, so it never matches Geofabrik's moving "latest"
    # checksum. Calling that stale would re-download 642 MB on every click for anyone whose
    # copy came from the mirror - which is everyone, whenever Geofabrik is down.
    src = None
    if have == remote:
        src = "Geofabrik"
    elif have == MIRROR_MD5.get(region):
        src = "pinned mirror"
    return {"state": "current" if src else "stale", "source": src,
            "path": str(path), "size": size, "local_md5": have, "remote_md5": remote}


def download(dest, region="turkey", progress=None, cancel=None, expect_md5=None,
             url=None, allow_mirror=True):
    """Download the extract to `dest`, verify it, and only then put it in place.

    `progress(done, total_or_None)` is called about once per megabyte. `cancel()` is polled
    at the same rate; returning True aborts, removes the partial file, and raises nothing -
    the caller gets None.

    Tries Geofabrik, then the pinned mirror. Returns a dict describing the verified file
    (including which source served it), or None if cancelled.
    """
    primary, _ = urls(region)
    candidates = [url] if url else [primary]
    if allow_mirror and not url and region in MIRRORS:
        candidates.append(MIRRORS[region])
    # Every attempt is reported, not just the last. The first version kept only the final
    # error, so a Geofabrik outage followed by a missing mirror surfaced as a bare 404 for
    # the mirror and said nothing at all about the source that actually mattered.
    failures = []
    for i, u in enumerate(candidates):
        try:
            return _download_one(dest, region, u, progress, cancel, expect_md5,
                                 mirror=(i > 0))
        except GeofabrikError as e:
            failures.append(f"{'mirror' if i else 'Geofabrik'} ({u}): {e}")
            if progress is not None and i + 1 < len(candidates):
                progress(0, None)                  # reset the bar for the next attempt
    raise GeofabrikError(
        "no source could supply the extract.\n  " + "\n  ".join(failures))


def _download_one(dest, region, pbf_url, progress, cancel, expect_md5, mirror=False):
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_suffix(dest.suffix + ".part")
    # The mirror is a pinned snapshot, so Geofabrik's "latest" checksum does not describe
    # it. Verifying a dated file against a moving checksum would fail every time the
    # upstream file changed, which is the opposite of a useful check.
    want = expect_md5
    if want is None:
        want = MIRROR_MD5.get(region) if mirror else remote_md5(region)

    h = hashlib.md5()
    done = 0
    try:
        with _open(pbf_url) as r:
            total = r.headers.get("Content-Length")
            total = int(total) if total and total.isdigit() else None
            with open(part, "wb") as f:
                while True:
                    if cancel is not None and cancel():
                        raise _Cancelled()
                    b = r.read(CHUNK)
                    if not b:
                        break
                    f.write(b)
                    h.update(b)
                    done += len(b)
                    if progress is not None:
                        progress(done, total)
    except _Cancelled:
        part.unlink(missing_ok=True)
        return None
    except (HTTPError, URLError, OSError) as e:
        part.unlink(missing_ok=True)
        raise GeofabrikError(
            f"download failed after {done:,} bytes: {type(e).__name__}: {e}. "
            "Nothing was left on disk.") from e

    got = h.hexdigest()
    size = part.stat().st_size

    # A short read is not an error at the socket level. It is only visible here.
    if total is not None and size != total:
        part.unlink(missing_ok=True)
        raise GeofabrikError(
            f"truncated download: got {size:,} bytes, server said {total:,}. "
            "The partial file was removed - a short .osm.pbf still parses and would "
            "have looked like empty countryside.")
    if want is not None and got != want:
        part.unlink(missing_ok=True)
        raise GeofabrikError(
            f"checksum mismatch: computed {got}, Geofabrik published {want}. "
            "The file was removed.")

    os.replace(part, dest)
    return {"path": str(dest), "size": size, "md5": got,
            "verified": want is not None, "url": pbf_url, "mirror": bool(mirror)}


class _Cancelled(Exception):
    pass
