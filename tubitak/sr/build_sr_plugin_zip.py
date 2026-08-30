#!/usr/bin/env python3
"""Build the installable zip for the SR plugin, with `sr_core` vendored inside it.

    python tubitak/sr/build_sr_plugin_zip.py [--out DIR]

Deployed into a QGIS profile, the plugin directory is NOT inside `tubitak/sr/`, so
`sr_core` is not one level up any more and `plugin.ensure_core_importable()` finds it only
if it sits beside the plugin's own modules. Vendoring is therefore not tidiness: without
it the plugin installs, loads, and fails on the first click - which is the failure mode
Project 1's zip already had once.

`__pycache__` is excluded. A stale `.pyc` compiled by a different Python is the kind of
thing that installs cleanly and then fails to import on someone else's machine.

Not placed under `tubitak/scripts/`: that directory belongs to Project 1 and this file
would be read by nothing there. It sits beside the tree it packages.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
import zipfile
from pathlib import Path

SR = Path(__file__).resolve().parent
PKG_NAME = "gencp_super_resolution"
SKIP_DIRS = {"__pycache__", ".pytest_cache"}
SKIP_SUFFIX = {".pyc", ".pyo"}


def _files(d):
    for p in sorted(d.rglob("*")):
        if p.is_dir() or any(part in SKIP_DIRS for part in p.parts) \
                or p.suffix in SKIP_SUFFIX:
            continue
        yield p


def build(out_dir):
    plugin_src = SR / "sr_plugin"
    core_src = SR / "sr_core"
    for d in (plugin_src, core_src):
        if not (d / "__init__.py").is_file() and d.name != "sr_plugin":
            raise SystemExit(f"build_sr_plugin_zip: {d} is not a package")
    if not (plugin_src / "metadata.txt").is_file():
        raise SystemExit("build_sr_plugin_zip: sr_plugin/metadata.txt missing")

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    zpath = out_dir / f"{PKG_NAME}.zip"
    n = 0
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for p in _files(plugin_src):
            z.write(p, f"{PKG_NAME}/{p.relative_to(plugin_src)}")
            n += 1
        for p in _files(core_src):
            z.write(p, f"{PKG_NAME}/sr_core/{p.relative_to(core_src)}")
            n += 1
    h = hashlib.sha256(zpath.read_bytes()).hexdigest()
    print(f"{zpath}  {n} files  {zpath.stat().st_size} bytes  sha256 {h}")

    # A zip that unpacks to a plugin QGIS cannot start is a zip that passed its own build.
    # These three are the failures that have actually happened, so they are checked here
    # rather than discovered at install time.
    with zipfile.ZipFile(zpath) as z:
        names = set(z.namelist())
    need = {f"{PKG_NAME}/metadata.txt", f"{PKG_NAME}/__init__.py",
            f"{PKG_NAME}/sr_core/__init__.py", f"{PKG_NAME}/sr_core/run.py"}
    missing = sorted(need - names)
    if missing:
        raise SystemExit(f"build_sr_plugin_zip: zip is missing {missing}")
    stale = sorted(x for x in names if x.endswith((".pyc", ".pyo")))
    if stale:
        raise SystemExit(f"build_sr_plugin_zip: compiled files leaked in: {stale}")
    print(f"  checked: metadata, classFactory module, vendored sr_core, no .pyc")
    return zpath


def main():
    ap = argparse.ArgumentParser(prog="build_sr_plugin_zip.py")
    ap.add_argument("--out", default=str(SR.parent / "data" / "sr_dist"),
                    help="output directory (default tubitak/data/sr_dist, gitignored)")
    a = ap.parse_args()
    build(a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
