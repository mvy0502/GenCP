#!/usr/bin/env python
"""Architectural guard: gencp_core must not import qgis or Qt.

This is not tidiness. The same gencp_core is what would run in an embedded or offline
context later, and it is what makes the whole chain testable without QGIS running. The
rule is easy to break by accident (one convenience import in a dialog-adjacent helper),
so it is enforced by a test that reads the source rather than by convention.

Static check by AST, so it catches imports on code paths that never execute here.
"""
from __future__ import annotations
import ast, sys

# Unknown arguments are refused, not ignored: a verifier that runs its default
# and prints PASS when you asked for something else is reporting on the wrong run.
import os.path as _op  # noqa: E402
sys.path.insert(0, _op.join(_op.dirname(_op.abspath(__file__)),
                            *(['..', 'tests'] if _op.basename(
                                _op.dirname(_op.abspath(__file__))) != 'tests'
                              else [])))
from _guard import strict_argv  # noqa: E402
strict_argv(known=(), positional=0)
from pathlib import Path

CORE = Path(__file__).resolve().parents[1] / "gencp_core"
FORBIDDEN_ROOTS = {"qgis", "PyQt5", "PyQt6", "qgis.PyQt", "processing"}


def offending_imports(path: Path):
    tree = ast.parse(path.read_text(), filename=str(path))
    bad = []
    for node in ast.walk(tree):
        names = []
        if isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names = [node.module]
        for n in names:
            root = n.split(".")[0]
            if root in FORBIDDEN_ROOTS or n in FORBIDDEN_ROOTS:
                bad.append((node.lineno, n))
    return bad


def main():
    files = sorted(CORE.rglob("*.py"))
    if not files:
        print(f"FAIL: no python files found under {CORE}")
        return 1
    failures = []
    for f in files:
        for lineno, name in offending_imports(f):
            failures.append(f"{f.relative_to(CORE.parent)}:{lineno}: imports {name!r}")
    print(f"checked {len(files)} files under gencp_core/ for qgis/Qt imports")
    if failures:
        print("FAIL — gencp_core must contain no logic that needs QGIS:")
        for x in failures:
            print("  " + x)
        return 1
    print("PASS — gencp_core is free of qgis and Qt imports")
    return 0


if __name__ == "__main__":
    sys.exit(main())
