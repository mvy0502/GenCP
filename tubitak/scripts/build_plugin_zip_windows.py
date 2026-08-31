#!/usr/bin/env python
"""Build the WINDOWS variant of the Project 1 plugin zip: the normal zip plus `_vendor/`.

    python tubitak/scripts/build_plugin_zip_windows.py

Two artefacts exist on purpose and this script produces only the second:

    gencp_plugin.zip           cross-platform, no _vendor/, ~95 KB
    gencp_plugin_win_amd64.zip Windows only, onnxruntime + osmium vendored, ~15 MB

The vendored wheels are `win_amd64` / `cp312` binaries. Shipping them in the single
cross-platform artefact would put 44 MB of unusable Windows binaries on every macOS and
Linux install, so the Windows build is a SEPARATE release asset, named for its platform.

`rasterio` is NOT vendored. It carries its own GDAL and QGIS has already loaded a different
one into the same process; two GDALs in one process is a known crash class. It stays in the
offline wheel kit, which the user installs by hand.
"""
from __future__ import annotations
import hashlib, shutil, subprocess, sys, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KIT = ROOT / "tubitak/data/kit/wheels"
OUT = ROOT / "tubitak/data/dist"
PKG = "gencp_synthetic_reference"
VENDOR = ("onnxruntime", "osmium")


def main():
    base = OUT / "gencp_plugin.zip"
    if not base.is_file():
        subprocess.run([sys.executable, str(ROOT / "tubitak/scripts/build_plugin_zip.py")],
                       check=True)
    staging = OUT / "_win_staging"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    with zipfile.ZipFile(base) as z:
        z.extractall(staging)

    vend = staging / PKG / "_vendor"
    vend.mkdir(parents=True)
    for name in VENDOR:
        hits = sorted(KIT.glob(f"{name}-*-cp312-cp312-win_amd64.whl"))
        if not hits:
            raise SystemExit(f"no win_amd64 cp312 wheel for {name} in {KIT}")
        with zipfile.ZipFile(hits[-1]) as z:
            z.extractall(vend)
        print(f"  vendored {hits[-1].name}")

    out = OUT / "gencp_plugin_win_amd64.zip"
    if out.exists():
        out.unlink()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(staging.rglob("*")):
            if p.is_file() and "__pycache__" not in p.parts and p.suffix not in (".pyc",):
                z.write(p, p.relative_to(staging))
    shutil.rmtree(staging)
    sha = hashlib.sha256(out.read_bytes()).hexdigest()
    print(f"  {out}  {out.stat().st_size:,} bytes  sha256 {sha}")
    print(f"  (cross-platform zip unchanged: {base.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
