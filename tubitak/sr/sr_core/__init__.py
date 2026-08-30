"""GenCP super-resolution core — plain Python, no Qt, no QGIS.

The same rule Project 1 enforces for `gencp_core` applies here and for the same reason:
this package must be importable and testable outside QGIS, so that the chain can be run and
gated without an application bundle. `tubitak/sr/tests/test_no_qgis_imports.py` checks it by
AST rather than by convention, and it also refuses `gencp_core` — see below.

Project 1's `gencp_core` is READ-ONLY to this package. Nothing here imports it. The
arithmetic it needed was copied rather than shared, deliberately: Project 1 passes Gate G
and Gate R today and is being demonstrated on 2026-09-04, and parameterising its module
globals to serve Project 2 would put a working, gated tool at risk to avoid duplicating a
handful of constants. Every copied function names its `gencp_core` origin and states how it
diverges, so the pair can be compared later.
"""
from __future__ import annotations

__all__ = ["grid", "tiles", "upsample", "mosaic"]
