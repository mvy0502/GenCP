#!/usr/bin/env python
"""Build gencp_plugin.zip in the layout QGIS's "Install from ZIP" expects.

QGIS unpacks the archive straight into <profile>/python/plugins/, so the archive must
contain exactly ONE top-level directory, named for the plugin, with metadata.txt at its
root. A zip of loose files, or one with a wrapper directory, installs to a folder QGIS
then cannot import.

`gencp_core` is VENDORED into that directory. In the checkout the plugin finds it one
level up (tubitak/), but a zip install lands in a QGIS profile with no repository
anywhere near it, and `ensure_core_importable` checks the plugin directory first for
exactly this case. Vendoring is what makes the zip self-contained.

Not vendored, and deliberately: the ONNX weights (208 MB - shipped separately so the
archive stays small and the weights stay a choice), and the CLC+ raster (8.2 GB, a
third-party CLMS product).

    python tubitak/scripts/build_plugin_zip.py
"""
from __future__ import annotations
import argparse
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLUGIN_SRC = ROOT / "tubitak/qgis_plugin"
CORE_SRC = ROOT / "tubitak/gencp_core"
PLUGIN_NAME = "gencp_synthetic_reference"
SKIP_DIRS = {"__pycache__", ".pytest_cache", ".ipynb_checkpoints"}
SKIP_SUFFIX = {".pyc", ".pyo"}


def copy_tree(src: Path, dst: Path):
    n = 0
    for p in sorted(src.rglob("*")):
        if any(part in SKIP_DIRS for part in p.relative_to(src).parts):
            continue
        if p.suffix in SKIP_SUFFIX or p.name == ".DS_Store":
            continue
        target = dst / p.relative_to(src)
        if p.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, target)
            n += 1
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "tubitak/data/dist/gencp_plugin.zip"))
    ap.add_argument("--stage", default=None,
                    help="keep the staged tree here instead of a temp directory")
    args = ap.parse_args()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    stage_root = Path(args.stage) if args.stage else out.parent / "_stage"
    if stage_root.exists():
        shutil.rmtree(stage_root)
    top = stage_root / PLUGIN_NAME
    top.mkdir(parents=True)

    n_plugin = copy_tree(PLUGIN_SRC, top)
    n_core = copy_tree(CORE_SRC, top / "gencp_core")
    print(f"staged {n_plugin} plugin files and {n_core} gencp_core files")

    meta = top / "metadata.txt"
    if not meta.is_file():
        sys.exit("metadata.txt missing from the staged tree - QGIS will refuse the zip")
    if not (top / "gencp_core" / "__init__.py").is_file():
        sys.exit("gencp_core was not vendored - the zip would not run outside a checkout")
    version = ""
    for line in meta.read_text(encoding="utf-8").splitlines():
        if line.startswith("version="):
            version = line.split("=", 1)[1].strip()
    print(f"metadata version={version!r}")

    if out.exists():
        out.unlink()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(stage_root.rglob("*")):
            if p.is_file():
                z.write(p, p.relative_to(stage_root))

    # Assert the layout rather than trusting that the loop above produced it.
    with zipfile.ZipFile(out) as z:
        names = z.namelist()
    tops = {n.split("/")[0] for n in names}
    problems = []
    if tops != {PLUGIN_NAME}:
        problems.append(f"expected exactly one top-level folder {PLUGIN_NAME!r}, got {tops}")
    if f"{PLUGIN_NAME}/metadata.txt" not in names:
        problems.append("metadata.txt is not at the root of the plugin folder")
    if f"{PLUGIN_NAME}/__init__.py" not in names:
        problems.append("__init__.py (classFactory) missing")
    if f"{PLUGIN_NAME}/gencp_core/pipeline.py" not in names:
        problems.append("gencp_core not vendored inside the plugin folder")
    if any(n.endswith(".pyc") or "__pycache__" in n for n in names):
        problems.append("compiled bytecode leaked into the archive")
    if problems:
        for p_ in problems:
            print("  LAYOUT PROBLEM:", p_)
        sys.exit(1)

    size = out.stat().st_size
    print(f"\nwrote {out}")
    print(f"  {len(names)} entries, {size/1e6:.2f} MB")
    print(f"  top-level folder: {PLUGIN_NAME}/ (as QGIS Install from ZIP requires)")
    if not args.stage:
        shutil.rmtree(stage_root)
    return 0


if __name__ == "__main__":
    sys.exit(main())
