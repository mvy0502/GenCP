"""Persist a parsed OSM feature set so a run does not re-parse the extract.

Parsing the Turkey country file costs about 121 seconds and that is paid on every run,
which is most of a short run's wall-clock and all of its perceived latency.

Format is hand-rolled rather than parquet: pyarrow is present in QGIS's Python and absent
from the project's conda environment, and a cache that only works in one of them is worse
than none. This needs shapely, which is already required.

    magic   b"GENCPIDX"          8 bytes
    version uint32               format version, bumped when the layout changes
    keylen  uint32               length of the key JSON
    key     utf-8 JSON           what this cache is FOR - see cache_key()
    nrows   uint64
    digest  32 bytes             sha256 of everything after this field
    payload nrows records        u32 taglen | tag JSON | u32 wkblen | WKB

The digest is the whole point. This project has already had a truncated file accepted as
valid; a cache that is read without being verified is that failure waiting to happen, and
it fails silently - a short read yields fewer OSM features, which renders as empty
countryside rather than as an error.
"""
from __future__ import annotations

import hashlib
import json
import os
import struct
from pathlib import Path

MAGIC = b"GENCPIDX"
VERSION = 1
_HEAD = struct.Struct("<8sII")
_U32 = struct.Struct("<I")
_U64 = struct.Struct("<Q")


def file_fingerprint(path, chunk=1 << 20):
    """sha256 of the extract. Content-addressed, so replacing the file invalidates the
    cache automatically - a user who re-downloads a newer Turkey extract must not silently
    keep rendering from the old one."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def cache_key(pbf_path, bbox, fingerprint=None):
    """What the cached rows are valid for: this file, clipped to this box.

    The bbox is part of the key because the rows were filtered by it during the parse. A
    cache built for Istanbul does not answer for Ankara, and rounding it to 3 decimals
    (~100 m) keeps trivially different extents from each missing the cache.
    """
    return {
        "v": VERSION,
        "sha256": fingerprint or file_fingerprint(pbf_path),
        "bbox": [round(float(v), 3) for v in bbox] if bbox else None,
    }


def cache_dir():
    d = Path(os.environ.get("GENCP_CACHE_DIR")
             or (Path.home() / ".cache" / "gencp" / "osm-index"))
    d.mkdir(parents=True, exist_ok=True)
    return d


def cache_path(key):
    name = hashlib.sha256(json.dumps(key, sort_keys=True).encode()).hexdigest()[:32]
    return cache_dir() / f"{name}.gencpidx"


def save(path, key, rows):
    """Write atomically: build a .part, then rename. A half-written cache is never visible."""
    import shapely.wkb as swkb
    path = Path(path)
    body = bytearray()
    for r in rows:
        g = r.get("geometry")
        if g is None:
            continue
        tags = {k: v for k, v in r.items() if k != "geometry"}
        tb = json.dumps(tags, sort_keys=True).encode("utf-8")
        wb = swkb.dumps(g)
        body += _U32.pack(len(tb)) + tb + _U32.pack(len(wb)) + wb
    kb = json.dumps(key, sort_keys=True).encode("utf-8")
    n = sum(1 for r in rows if r.get("geometry") is not None)
    digest = hashlib.sha256(bytes(body)).digest()
    tmp = path.with_suffix(path.suffix + ".part")
    with open(tmp, "wb") as f:
        f.write(_HEAD.pack(MAGIC, VERSION, len(kb)))
        f.write(kb)
        f.write(_U64.pack(n))
        f.write(digest)
        f.write(body)
    os.replace(tmp, path)
    return path


def load(path, key):
    """Return rows, or None if the cache is absent, stale, or damaged in any way.

    Every failure returns None rather than raising: a bad cache must cost a re-parse, never
    a failed run and never a wrong render.
    """
    import shapely.wkb as swkb
    path = Path(path)
    try:
        raw = path.read_bytes()
    except OSError:
        return None
    try:
        if len(raw) < _HEAD.size:
            return None
        magic, version, keylen = _HEAD.unpack_from(raw, 0)
        if magic != MAGIC or version != VERSION:
            return None
        off = _HEAD.size
        kb = raw[off:off + keylen]
        off += keylen
        if json.loads(kb.decode("utf-8")) != key:
            return None
        (n,) = _U64.unpack_from(raw, off)
        off += _U64.size
        digest = raw[off:off + 32]
        off += 32
        body = raw[off:]
        if hashlib.sha256(body).digest() != digest:
            return None                    # truncated or corrupted - discard, do not use
        rows = []
        p = 0
        for _ in range(n):
            (tl,) = _U32.unpack_from(body, p)
            p += _U32.size
            tags = json.loads(body[p:p + tl].decode("utf-8"))
            p += tl
            (wl,) = _U32.unpack_from(body, p)
            p += _U32.size
            tags["geometry"] = swkb.loads(body[p:p + wl])
            p += wl
            rows.append(tags)
        if p != len(body):
            return None                    # trailing or missing bytes
        return rows
    except Exception:                      # noqa: BLE001 - any damage means re-parse
        return None
