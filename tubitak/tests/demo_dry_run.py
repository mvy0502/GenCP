#!/usr/bin/env python
"""Open tubitak/demo/gencp_demo.qgz fresh and run it through WITHOUT typing anything.

The demo is for a live audience, so the thing to verify is not "does it work" but "does it
work with no keyboard". Every field must arrive pre-filled from the project, and the only
interactions permitted here are the three a presenter performs: press Preview, tick the
confirmation box, press Generate.

Run through the QGIS application binary (see run_in_qgis.sh).
"""
from __future__ import annotations
import os, sys, time
from pathlib import Path

try:
    ROOT = Path(__file__).resolve().parents[2]
except NameError:                                    # pragma: no cover - --code path
    ROOT = Path(os.environ.get("GENCP_REPO_ROOT", os.getcwd())).resolve()
sys.path.insert(0, str(ROOT / "tubitak"))

_OUT = open(os.environ.get("GENCP_TEST_OUT", "/tmp/demo_dry_run.txt"), "w")
import faulthandler; faulthandler.enable(_OUT)
def say(*a): print(*a, file=_OUT, flush=True)

CHECKS = []
def check(name, cond, detail=""):
    CHECKS.append((name, bool(cond), detail))
    say(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f"  - {detail}" if detail else ""))
    return bool(cond)

def main():
    from qgis.core import QgsProject, QgsApplication, QgsSettings
    from qgis.PyQt.QtWidgets import QApplication, QMessageBox
    import qgis.utils
    for n in ("critical", "warning", "information"):
        setattr(QMessageBox, n, staticmethod(lambda *a, **k: 0))

    # Wipe any remembered settings so the project alone has to supply the paths - otherwise
    # this machine's QgsSettings could mask a project that carries nothing.
    s = QgsSettings()
    for k in ("clc_path", "model_path", "pbf_path", "out_dir"):
        s.remove("GenCP/" + k)
    say("cleared QgsSettings GenCP/* so ONLY the project can supply paths\n")

    t_open = time.time()
    ok = QgsProject.instance().read(str(ROOT / "tubitak/demo/gencp_demo.qgz"))
    QApplication.processEvents()
    t_open = time.time() - t_open
    check("the demo project opens", ok, f"{t_open:.2f}s")
    names = [l.name() for l in QgsProject.instance().mapLayers().values()]
    check("the reference raster is already loaded", any("referans" in n for n in names),
          ", ".join(names))

    plugin = qgis.utils.plugins.get("gencp_synthetic_reference")
    check("the plugin is loaded", plugin is not None)
    if plugin is None:
        return 1

    t0 = time.time()
    plugin.dialog = None
    plugin.action.trigger()
    QApplication.processEvents()
    dlg = plugin.dialog
    check("the dialog opens", dlg is not None)

    # Nothing is typed. Everything below must already be filled in.
    check("reference layer pre-selected", dlg.layer_box.currentLayer() is not None,
          dlg.layer_box.currentLayer().name() if dlg.layer_box.currentLayer() else "")
    for field, label in ((dlg.pbf_edit, "OSM extract"), (dlg.clc_edit, "CLC+ raster"),
                         (dlg.model_edit, "model"), (dlg.out_edit, "output path")):
        v = field.text().strip()
        check(f"{label} pre-filled from the project", bool(v) and
              (Path(v).exists() or Path(v).parent.exists()), v[-60:] if v else "EMPTY")
    check("the extent was read", "→" in dlg.lbl_extent.text(), dlg.lbl_extent.text()[:52])
    dlg.overlap_box.setCurrentIndex(0)
    QApplication.processEvents()

    say("\n  --- the three presenter actions ---")
    t_prev = time.time(); dlg.btn_preview.click(); QApplication.processEvents()
    t_prev = time.time() - t_prev
    pm = dlg.preview_label.pixmap()
    check("1. Preview renders", pm is not None and not pm.isNull(), f"{t_prev:.2f}s")
    check("the tile's band is shown in the confirmation frame",
          bool(dlg.lbl_warn.text()), dlg.lbl_warn.text()[:70].replace("<b>", ""))
    dlg.cb_confirm.setChecked(True); QApplication.processEvents()
    check("2. confirmation enables Generate", dlg.btn_run.isEnabled())

    t_run = time.time(); dlg.btn_run.click()
    task = dlg._task
    deadline = time.time() + 900
    while dlg._task is not None and time.time() < deadline:
        QApplication.processEvents(); time.sleep(0.05)
    t_run = time.time() - t_run
    check("3. Generate completes", task is not None and task.exception is None,
          str(task.exception) if task and task.exception else f"{t_run:.2f}s")

    res = task.result or {}
    v = (res.get("confidence") or {}).get("verdict") or {}
    if v:
        f = v["fractions"]
        say(f"    confidence: green {f['green']*100:.1f}%  amber {f['amber']*100:.1f}%  "
            f"red {f['red']*100:.1f}%  run band {v['mean_band']}")
        check("the confidence layer shows ALL THREE bands (a one-colour demo teaches nothing)",
              min(f['green'], f['amber'], f['red']) > 0.05,
              f"min band share {min(f.values())*100:.1f}%")
    names = [l.name() for l in QgsProject.instance().mapLayers().values()]
    # Named from the project's out_dir plus the dialog's default file name, so the layer
    # is "gencp_reference" - the first version of this assertion looked for "demo_output"
    # and failed on its own guess rather than on the plugin.
    out_stem = Path(res.get("output", "")).stem
    check("output layer added", bool(out_stem) and out_stem in names,
          f"looked for {out_stem!r} in {names}")
    check("confidence layer added", any("confidence" in n for n in names))

    total = time.time() - t0
    say(f"\n  project open        {t_open:6.2f}s")
    say(f"  dialog -> output    {total:6.2f}s   (preview {t_prev:.2f}s, generate {t_run:.2f}s)")
    say(f"  TOTAL, cold         {t_open + total:6.2f}s")

    say("\n" + "=" * 66)
    failed = [n for n, ok_, _ in CHECKS if not ok_]
    say(f"{len(CHECKS)-len(failed)}/{len(CHECKS)} checks passed")
    if failed:
        say("FAILED: " + "; ".join(failed))
    say("=" * 66)
    return 1 if failed else 0

if True:
    rc = 2
    try:
        rc = main()
    except Exception:
        import traceback; say("CRASH:\n" + traceback.format_exc())
    _OUT.close(); os._exit(rc)
