#!/usr/bin/env python3
"""Static guards on `tubitak/sr/sr_plugin`. Runs without QGIS and without Qt.

Three properties are asserted, each of which has already been violated once in this
project or in Project 1:

  G1  No user-facing Turkish literal outside `strings.py`. Project 1's dialog grew Turkish
      inline before `strings.py` existed, and the strings could not then be reviewed or
      changed in one place.
  G2  No forbidden import anywhere in the plugin package: `onnxruntime` (must stay absent
      so the bicubic path loads where it cannot be imported), `pyproj` (segfaults a
      QgsTask worker in QGIS 4.2.1), `multiprocessing` (spawn re-executes the QGIS binary),
      and `gencp_core` (Project 1's core - the two plugins must not couple).
  G3  Every `t()` / `tip()` key used in the package exists in `strings.py`.

Standing practice 11: each guard is born with a failing case, and `--self-test` runs all
three against a known-false fixture BEFORE the real verdict is trusted. Standing practice
10: the guard refuses arguments it does not understand, via `tubitak/tests/_guard.py`.
"""
from __future__ import annotations

import ast
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
# Makes this file a fourth reader of tubitak/tests/_guard.py - relevant to CLAUDE.md's
# rule that nothing read by the repository may be moved without checking.
sys.path.insert(0, str(ROOT / "tubitak" / "tests"))
from _guard import strict_argv                       # noqa: E402

PKG = HERE.parent / "sr_plugin"
STRINGS = "strings.py"
FORBIDDEN = ("onnxruntime", "pyproj", "multiprocessing", "gencp_core")
# Turkish-specific letters. Restricted to these rather than "any non-ASCII" so that an
# English comment containing a dash or a degree sign is not reported as a Turkish string.
TR = re.compile(r"[çğıİöşüÇĞÖŞÜ]")


def _string_literals(tree):
    """(lineno, value) for every str constant in the tree, docstrings excluded.

    Docstrings are excluded because they are developer documentation, not UI, and this
    file's own module docstring would otherwise be flagged.
    """
    docs = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                             ast.AsyncFunctionDef)):
            body = getattr(node, "body", None)
            if body and isinstance(body[0], ast.Expr) \
                    and isinstance(body[0].value, ast.Constant) \
                    and isinstance(body[0].value.value, str):
                docs.add(id(body[0].value))
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) \
                and id(node) not in docs:
            out.append((node.lineno, node.value))
    return out


def _imports(tree):
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                names.add(a.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.level == 0:
                names.add(node.module.split(".")[0])
    return names


def _string_keys(tree):
    """Keys passed as the first positional arg to t() / tip()."""
    keys = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                and node.func.id in ("t", "tip") and node.args:
            a = node.args[0]
            if isinstance(a, ast.Constant) and isinstance(a.value, str):
                keys.add(a.value)
    return keys


def check(pkg, strings_module_name=STRINGS):
    """Return (offences, stats). An offence is (guard, file, line, detail)."""
    pkg = Path(pkg)
    files = sorted(p for p in pkg.glob("*.py"))
    if not files:
        raise SystemExit(f"plugin_guards: no .py files under {pkg} - nothing to check")
    off = []
    used_keys, n_lit = set(), 0
    for p in files:
        tree = ast.parse(p.read_text(encoding="utf-8"))
        if p.name != strings_module_name:
            for lineno, val in _string_literals(tree):
                n_lit += 1
                if TR.search(val):
                    off.append(("G1", p.name, lineno,
                                f"Turkish literal outside {strings_module_name}: "
                                f"{val[:60]!r}"))
        for mod in sorted(_imports(tree) & set(FORBIDDEN)):
            off.append(("G2", p.name, 0, f"forbidden import {mod!r}"))
        used_keys |= _string_keys(tree)

    sp = pkg / strings_module_name
    defined = set()
    if sp.is_file():
        ns = {}
        exec(compile(sp.read_text(encoding="utf-8"), str(sp), "exec"), ns)
        defined = set(ns.get("S", {})) | set(ns.get("TIP", {}))
        for k in sorted(used_keys - defined):
            off.append(("G3", "<any>", 0, f"string key {k!r} used but not defined"))
    else:
        off.append(("G3", strings_module_name, 0, "strings module missing"))
    return off, dict(files=len(files), literals=n_lit, keys_used=len(used_keys),
                     keys_defined=len(defined))


_BAD_DIALOG = '''\
"""A docstring with Türkçe in it - must NOT be reported, it is not UI."""
import onnxruntime
import pyproj
from gencp_core import pipeline
from .strings import t, tip

def build():
    lab = "Çalıştır"
    return t("run"), t("no_such_key_at_all"), lab
'''
_GOOD_STRINGS = 'S = {"run": "Çalıştır"}\nTIP = {"run": "ipucu"}\n'


def self_test():
    """Known-false first, then known-true. The guard is not trusted until both behave."""
    ok = True
    with tempfile.TemporaryDirectory() as d:
        bad = Path(d) / "bad"
        bad.mkdir()
        (bad / "dialog.py").write_text(_BAD_DIALOG, encoding="utf-8")
        (bad / STRINGS).write_text(_GOOD_STRINGS, encoding="utf-8")
        off, st = check(bad)
        got = sorted({o[0] for o in off})
        print(f"  KF  known-false fixture -> {len(off)} offences {got}")
        for o in off:
            print(f"        {o[0]} {o[1]}:{o[2]}  {o[3]}")
        want = ["G1", "G2", "G3"]
        if got != want:
            print(f"  *** KF FAILED: expected {want}, got {got}"); ok = False
        if not any("onnxruntime" in o[3] for o in off) \
                or not any("pyproj" in o[3] for o in off) \
                or not any("gencp_core" in o[3] for o in off):
            print("  *** KF FAILED: not all three forbidden imports reported"); ok = False
        if any("docstring" in o[3] for o in off):
            print("  *** KF FAILED: a docstring was reported as a UI literal"); ok = False

        good = Path(d) / "good"
        good.mkdir()
        (good / "dialog.py").write_text(
            'from .strings import t\ndef f():\n    return t("run")\n', encoding="utf-8")
        (good / STRINGS).write_text(_GOOD_STRINGS, encoding="utf-8")
        off2, _ = check(good)
        print(f"  KT  known-true fixture  -> {len(off2)} offences")
        if off2:
            print(f"  *** KT FAILED: {off2}"); ok = False

        empty = Path(d) / "empty"
        empty.mkdir()
        try:
            check(empty)
            print("  *** DG FAILED: an empty package produced a verdict"); ok = False
        except SystemExit as e:
            print(f"  DG  empty package      -> refused: {e}")
    return ok


def main():
    strict_argv(known=("--self-test", "--pkg="), positional=0,
                usage="plugin_guards.py [--self-test] [--pkg=DIR]")
    argv = sys.argv[1:]
    self_only = "--self-test" in argv
    pkg = PKG
    for a in argv:
        if a.startswith("--pkg="):
            pkg = Path(a.split("=", 1)[1])

    print("plugin_guards: self-test (known-false first, per standing practice 11)")
    if not self_test():
        print("FAILED: the guard itself did not behave. Its verdict is not trusted.")
        return 1
    if self_only:
        print("PASS  self-test only; no package verdict requested")
        return 0

    off, st = check(pkg)
    print(f"\nplugin_guards: {pkg}")
    print(f"  {st['files']} files, {st['literals']} string literals outside "
          f"{STRINGS}, {st['keys_used']} keys used, {st['keys_defined']} defined")
    for o in off:
        print(f"  [FAIL] {o[0]} {o[1]}:{o[2]}  {o[3]}")
    if off:
        print(f"FAILED: {len(off)} offence(s)")
        return 1
    print("PASS  G1 no Turkish outside strings.py · G2 no forbidden import · "
          "G3 every string key defined")
    return 0


if __name__ == "__main__":
    sys.exit(main())
