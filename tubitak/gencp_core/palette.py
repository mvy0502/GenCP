"""The GenCP colour palette, loaded from the upstream module it belongs to.

The palette tables live in `GenCP_HR_demo/genCP_HR_osm_colors.py`, which is an UPSTREAM
file: this work package does not modify it. It is a pure data module (five dicts, no
imports, no side effects), so it is loaded by path rather than copied, and its SHA-256 is
pinned. If the upstream file ever changes, every render changes with it and Gate R would
start failing for a reason that has nothing to do with our code — so the mismatch is
raised at import time, loudly, instead of being discovered as a silent render drift.

A deployed QGIS plugin may not sit inside the research repository. `load()` therefore
searches, in order: an explicit path argument, the `GENCP_PALETTE` environment variable,
a copy vendored beside this file (as `_vendored_osm_colors.py`, a verbatim copy made by
the packaging step), and finally the upstream location relative to the repository root.
Whichever is found must match the pinned hash.
"""
from __future__ import annotations
import hashlib, os
from pathlib import Path

# Pinned 2026-08-26 against GenCP_HR_demo/genCP_HR_osm_colors.py.
PALETTE_SHA256 = "7876d9d3ae2b646cacd2b32fd1ea47e62484d7c99c247f4a4aae1c133cbaf919"

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parents[1]


def _candidates(explicit=None):
    if explicit:
        yield Path(explicit)
    env = os.environ.get("GENCP_PALETTE")
    if env:
        yield Path(env)
    yield _HERE / "_vendored_osm_colors.py"
    yield _REPO_ROOT / "GenCP_HR_demo" / "genCP_HR_osm_colors.py"


def resolve(explicit=None) -> Path:
    tried = []
    for c in _candidates(explicit):
        tried.append(str(c))
        if c.is_file():
            return c
    raise FileNotFoundError(
        "GenCP palette module not found. Set GENCP_PALETTE or vendor it beside "
        "gencp_core/palette.py. Tried:\n  " + "\n  ".join(tried))


def load(explicit=None):
    """Return the upstream palette module, verified against the pinned hash."""
    path = resolve(explicit)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != PALETTE_SHA256:
        raise RuntimeError(
            f"GenCP palette hash mismatch for {path}.\n"
            f"  expected {PALETTE_SHA256}\n  found    {digest}\n"
            "Every render depends on these tables. Refusing to render against an "
            "unrecognised palette: re-pin PALETTE_SHA256 deliberately, with a "
            "re-registration, or restore the upstream file.")
    import importlib.util
    spec = importlib.util.spec_from_file_location("_gencp_palette_upstream", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
