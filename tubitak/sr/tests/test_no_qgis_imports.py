#!/usr/bin/env python
"""Architectural guard: sr_core must not import qgis or Qt.

Derived from `tubitak/tests/test_no_qgis_imports.py`, which guards `gencp_core`, and for the
same reason: `sr_core` is what runs headless, on Modal or Kaggle, and inside a plugin later,
and it is what makes the chain gateable without an application bundle. QGIS wiring is WP2
and belongs in the plugin layer, not here.

Divergence from the Project 1 original: it also refuses `gencp_core`. That is not tidiness
either. WP1's fixed decision is that Project 1's arithmetic was COPIED rather than shared,
so that Project 2 cannot force a change on a package that passes Gate G and Gate R today. An
`import gencp_core` anywhere in `sr_core` would quietly re-create the coupling that decision
exists to prevent, and would do it in a way no reviewer would notice.

Static check by AST, so it catches imports on code paths that never execute here.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "tubitak" / "tests"))
from _guard import strict_argv                                          # noqa: E402

strict_argv(known=(), positional=0, usage="test_no_qgis_imports.py")

CORE = HERE.parents[1] / "sr_core"
FORBIDDEN = {"qgis", "PyQt5", "PyQt6", "processing", "gencp_core"}


def offending(path):
    bad = []
    for node in ast.walk(ast.parse(path.read_text(), filename=str(path))):
        names = []
        if isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names = [node.module]
        for n in names:
            if n.split(".")[0] in FORBIDDEN or n in FORBIDDEN:
                bad.append((node.lineno, n))
    return bad


def main():
    files = sorted(CORE.glob("*.py"))
    if not files:
        sys.stderr.write(f"no modules found under {CORE} — nothing was checked\n")
        return 2
    total = 0
    for f in files:
        bad = offending(f)
        total += len(bad)
        mark = "FAIL" if bad else "PASS"
        print(f"  [{mark}] {f.relative_to(ROOT)}")
        for ln, n in bad:
            print(f"         line {ln}: import {n}")

    # Born with its failing case (standing practice 11): the checker is shown rejecting a
    # module that DOES import a forbidden name, before its verdict on the real ones is used.
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        probe = Path(td) / "known_false.py"
        probe.write_text("from qgis.core import QgsTask\nimport gencp_core\n")
        found = offending(probe)
    ok_probe = len(found) == 2
    print(f"  [{'PASS' if ok_probe else 'FAIL'}] known-false control: a module importing "
          f"qgis.core and gencp_core -> {len(found)} offence(s) detected (expected 2)")

    print(f"\n{len(files)} modules checked, {total} forbidden import(s)")
    if not ok_probe:
        print("VERDICT: the checker did not flag its own known-false case; its clean "
              "result on the real modules means nothing.")
        return 2
    print(f"VERDICT: {'PASS' if total == 0 else 'FAIL'}")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
