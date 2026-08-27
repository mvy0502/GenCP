"""Refuse arguments a verifier does not understand.

Every gate in this project resolves its inputs from the repository, so `sys.argv` is at
most a small set of flags. That made ignoring the rest look harmless. It is not:

    python tubitak/tests/gate_g.py --overlap=2560     # runs at 2560 m
    python tubitak/tests/gate_g.py --overlp=2560      # runs at 0 m and prints PASS

The second one is a PASS for a configuration nobody asked for, and nothing on screen says
so. The audit that found this ran every verifier with no arguments, an empty input and a
missing file: eighteen of twenty-three exited 0, and all but one did it by ignoring the
argument and re-running their real work. A verdict that does not depend on what you asked
for is not a verdict about what you asked for.

So: unknown arguments are an error, not noise.

QGIS `--code` harnesses do not use this. Their `sys.argv` belongs to the QGIS application
(`--nologo --code <path>`), not to the harness, so refusing unknown entries there would
refuse QGIS's own. Those take their inputs from the environment instead, and the audit
confirms they already fail when GENCP_REPO_ROOT points somewhere empty.
"""
from __future__ import annotations

import sys


def strict_argv(known=(), positional=0, usage=""):
    """Exit 2 on any argument not in `known` and beyond `positional` bare arguments.

    `known` holds accepted flag PREFIXES, e.g. ("--overlap=", "--no-net"). Prefix rather
    than exact match so valued flags work without each caller re-parsing them.
    """
    args = sys.argv[1:]
    bare, unknown = [], []
    for a in args:
        if a.startswith("-"):
            if not any(a == k or (k.endswith("=") and a.startswith(k)) for k in known):
                unknown.append(a)
        else:
            bare.append(a)
    if len(bare) > positional:
        unknown.extend(bare[positional:])
    if unknown:
        sys.stderr.write(
            f"{sys.argv[0]}: unrecognised argument(s): {' '.join(unknown)}\n"
            f"  This verifier refuses arguments it does not understand rather than\n"
            f"  ignoring them and reporting a verdict for something you did not ask for.\n"
            + (f"  Usage: {usage}\n" if usage else ""))
        raise SystemExit(2)
    return bare
