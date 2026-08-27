"""Prove the tile-overlap spin box ENFORCES its two constraints, inside real QGIS.

The overlap became a free numeric input. Free means the user can type 645, or 3000, and
both must be refused rather than accepted and quietly rounded - a rounded value would run
fine, produce a plausible mosaic, and break the Gate G transform contract without saying
anything.

This drives Qt's validator the way typing does, so it tests the enforcement path rather
than a re-implementation of it.

    QT_QPA_PLATFORM=offscreen GENCP_REPO_ROOT=$PWD \
      /Applications/QGIS-final-4_2_1.app/Contents/MacOS/QGIS-final-4_2_1 \
      --nologo --code tubitak/tests/overlap_constraints.py
"""
import os
import sys
from pathlib import Path

# QGIS's --code execs this file in a namespace where __file__ may be undefined. Reading it
# as a dict default evaluates it EAGERLY and raises NameError on the first line, before the
# output file exists - which is indistinguishable from "QGIS never ran the script". It cost
# two ten-minute timeouts to see that.
try:
    ROOT = Path(__file__).resolve().parents[2]
except NameError:                                  # pragma: no cover - --code path
    ROOT = Path(os.environ.get("GENCP_REPO_ROOT", os.getcwd())).resolve()
sys.path.insert(0, str(ROOT / "tubitak"))

OUT = Path(os.environ.get("GENCP_TEST_OUT", "/tmp/overlap_constraints.txt"))
_lines, _n, _bad = [], 0, 0


def check(what, ok, detail=""):
    global _n, _bad
    _n += 1
    if not ok:
        _bad += 1
    _lines.append(f"  [{'PASS' if ok else 'FAIL'}] {what}" + (f"  - {detail}" if detail else ""))


def main():
    from qgis.PyQt.QtGui import QValidator
    from gencp_core import extent as ext
    from qgis_plugin import dialog as D

    box = D.OverlapSpinBox(int(ext.NOMINAL), ext.TILE_M)

    check("the limit is read from the pipeline, not restated",
          box.maximum_legal() == 2560 and ext.TILE_M == 2570.0,
          f"tile {ext.TILE_M:.0f} m ({ext.SRC_PX} px), max legal {box.maximum_legal()} m")
    check("the default is the value we measured",
          D.DEFAULT_OVERLAP_M == 640, f"{D.DEFAULT_OVERLAP_M} m")

    def state(text):
        return box.validate(text + box.suffix(), len(text))[0]

    A, I, X = (QValidator.State.Acceptable, QValidator.State.Intermediate,
               QValidator.State.Invalid)

    for legal in ("0", "10", "640", "1280", "2560"):
        check(f"{legal} m is accepted", state(legal) == A, str(state(legal)))
    for illegal in ("645", "641", "1", "1285"):
        check(f"{illegal} m is not committable (not a whole pixel)",
              state(illegal) == I, str(state(illegal)))
    for toobig in ("2570", "2600", "3000"):
        check(f"{toobig} m is rejected (at or above one tile)",
              state(toobig) == X, str(state(toobig)))

    # A refusal must reach the user. Capture what the widget emits.
    said = []
    box.constraintViolated.connect(said.append)
    state("3000")
    check("rejecting an oversized value names the limit",
          any("2570" in m and "2560" in m for m in said),
          said[-1] if said else "nothing emitted")

    said.clear()
    fixed = box.fixup("645" + box.suffix())
    check("a non-multiple snaps to the grid", fixed.startswith("640"), fixed)
    check("and the snap is announced, not silent",
          any("645" in m and "640" in m for m in said),
          said[-1] if said else "NOTHING EMITTED - this is the quiet rounding we forbade")

    # setValue is the programmatic path; Qt clamps range but not the step.
    box.setValue(3000)
    check("setValue cannot exceed the legal maximum either",
          box.value() == 2560, f"{box.value()} m")

    # And the grid itself must terminate at the largest legal overlap.
    try:
        tiles, _ = ext.tile_grid(
            (400000.0, 4400000.0, 400000.0 + 3 * ext.TILE_M, 4400000.0 + 3 * ext.TILE_M),
            float(box.maximum_legal()))
        check("tile_grid terminates at the largest legal overlap",
              len(tiles) > 0, f"{len(tiles)} tiles at {box.maximum_legal()} m")
    except Exception as exc:                       # noqa: BLE001
        check("tile_grid terminates at the largest legal overlap", False,
              f"{type(exc).__name__}: {exc}")
    try:
        ext.tile_grid((400000.0, 4400000.0, 400000.0 + 3 * ext.TILE_M,
                       4400000.0 + 3 * ext.TILE_M), ext.TILE_M)
        check("the core still rejects an overlap of exactly one tile", False,
              "tile_grid accepted it")
    except Exception:                              # noqa: BLE001
        check("the core still rejects an overlap of exactly one tile", True)


try:
    main()
except Exception as exc:                           # noqa: BLE001
    import traceback
    _lines.append("  [FAIL] harness crashed")
    _lines.append(traceback.format_exc())
    _bad += 1

_lines.append("")
_lines.append("=" * 72)
_lines.append(f"{_n - _bad}/{_n} checks passed")
_lines.append("=" * 72)
OUT.write_text("\n".join(_lines))
print("\n".join(_lines))

# A --code script runs inside a live application; sys.exit would not end it.
os._exit(2 if _bad else 0)
