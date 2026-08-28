#!/usr/bin/env python
"""Prove the Geofabrik downloader REFUSES bad bytes before trusting it with good ones.

A truncated .osm.pbf is the failure this guards against, and it is silent: the file opens,
it parses, and it yields fewer features over part of the extent - which is indistinguishable
from countryside. So the interesting cases here are the negative ones, and they are served
from a local HTTP server rather than from Geofabrik, because a test that only passes when
a third party is up is a test that will be ignored the first time it goes down.

    python tubitak/tests/geofabrik_download.py            # offline cases only
    python tubitak/tests/geofabrik_download.py --net      # also probe the real endpoints
"""
from __future__ import annotations
import hashlib
import http.server
import os
import socketserver
import sys
import threading
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import os.path as _op  # noqa: E402
sys.path.insert(0, _op.join(_op.dirname(_op.abspath(__file__))))
from _guard import strict_argv  # noqa: E402
strict_argv(known=("--net",), positional=0)

from gencp_core import geofabrik as gf  # noqa: E402

CHECKS = []


def check(name, ok, detail=""):
    CHECKS.append(bool(ok))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f"  - {detail}" if detail else ""))


PAYLOAD = b"gencp-fake-pbf-payload" * 5000          # ~110 KB
GOOD_MD5 = hashlib.md5(PAYLOAD).hexdigest()


class Handler(http.server.BaseHTTPRequestHandler):
    mode = "good"

    def log_message(self, *a):
        pass

    def do_GET(self):
        if self.path.endswith(".md5"):
            body = f"{self.server.md5_to_serve}  turkey-latest.osm.pbf\n".encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        m = self.server.mode
        if m == "truncate":
            # Declares the full length, sends half. This is the silent one.
            self.send_response(200)
            self.send_header("Content-Length", str(len(PAYLOAD)))
            self.end_headers()
            self.wfile.write(PAYLOAD[: len(PAYLOAD) // 2])
            return
        self.send_response(200)
        self.send_header("Content-Length", str(len(PAYLOAD)))
        self.end_headers()
        self.wfile.write(PAYLOAD)


def serve(mode, md5_to_serve):
    srv = socketserver.TCPServer(("127.0.0.1", 0), Handler)
    srv.mode = mode
    srv.md5_to_serve = md5_to_serve
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}/x-latest.osm.pbf"


def main():
    print("=" * 74)
    print("GEOFABRIK DOWNLOADER")
    print("=" * 74)

    orig = dict(gf.REGIONS)
    for mode, md5, label, expect in (
        ("good", GOOD_MD5, "a complete, correctly-checksummed file", "ok"),
        ("truncate", GOOD_MD5, "a TRUNCATED file with a correct declared length", "refuse"),
        ("good", "0" * 32, "a complete file whose published MD5 does not match", "refuse"),
    ):
        srv, url = serve(mode, md5)
        try:
            gf.BASE = url.rsplit("/", 1)[0]
            gf.REGIONS["x"] = "x"
            with tempfile.TemporaryDirectory() as d:
                dest = Path(d) / "x-latest.osm.pbf"
                err = None
                try:
                    res = gf.download(dest, "x")
                except gf.GeofabrikError as e:
                    res = None
                    err = str(e)
                if expect == "ok":
                    check(f"accepts {label}", res is not None and dest.exists(),
                          f"{res and res['size']:,} bytes, md5 {res and res['md5'][:12]}")
                    check("  and the .part file is gone",
                          not dest.with_suffix(dest.suffix + ".part").exists())
                else:
                    check(f"REFUSES {label}", err is not None,
                          (err or "accepted it")[:95])
                    check("  and leaves nothing behind",
                          not dest.exists()
                          and not dest.with_suffix(dest.suffix + ".part").exists(),
                          "dest exists" if dest.exists() else "clean")
        finally:
            srv.shutdown()
            gf.REGIONS = dict(orig)

    # cancellation
    srv, url = serve("good", GOOD_MD5)
    try:
        gf.BASE = url.rsplit("/", 1)[0]
        gf.REGIONS["x"] = "x"
        with tempfile.TemporaryDirectory() as d:
            dest = Path(d) / "x-latest.osm.pbf"
            res = gf.download(dest, "x", cancel=lambda: True)
            check("a cancelled download returns None", res is None)
            check("  and leaves no partial file",
                  not dest.exists()
                  and not dest.with_suffix(dest.suffix + ".part").exists())
    finally:
        srv.shutdown()
        gf.REGIONS = dict(orig)

    check("an unknown region is refused, not silently defaulted",
          _raises(lambda: gf.urls("atlantis")))
    check("local_status reports a missing file as missing",
          gf.local_status("/definitely/not/here.pbf", want_md5="x")["state"] == "missing")

    if "--net" in sys.argv:
        print("\n  --net: probing the real Geofabrik endpoints")
        m = gf.remote_md5("turkey")
        check("the published MD5 is reachable", m is not None and len(m) == 32, str(m))
        s = gf.remote_size("turkey")
        print(f"  remote_size -> {s if s is None else format(s, ',')} "
              f"({'server declined; the UI shows the approximate figure' if s is None else 'exact'})")

    print()
    print("=" * 74)
    print(f"{sum(CHECKS)}/{len(CHECKS)} checks passed")
    print("=" * 74)
    return 0 if all(CHECKS) else 1


def _raises(fn):
    try:
        fn()
        return False
    except Exception:
        return True


sys.exit(main())
