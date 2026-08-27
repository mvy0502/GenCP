#!/usr/bin/env python
"""Exercise the plugin inside a real, headless QGIS.

The dialog is EXECUTED, not merely written: this constructs the real QDialog, drives the
real widgets, and runs a real QgsTask through the real task manager.

MUST be run through the QGIS APPLICATION BINARY, not the bundled python3.12:

    QT_QPA_PLATFORM=offscreen /Applications/QGIS-*.app/Contents/MacOS/QGIS-* \
        --nologo --code tubitak/tests/test_plugin_headless.py

Reason, and it is a deployment fact worth knowing: on macOS the QGIS app executable is
signed with `com.apple.security.cs.disable-library-validation`, but the bundled
`python3.12` executable is NOT. Under the hardened runtime, library validation therefore
blocks onnxruntime's native extension from loading in `python3.12` ("different Team IDs")
while it loads normally in the QGIS process the plugin actually runs in. Testing through
python3.12 would report a failure that does not exist in deployment.

Output goes to GENCP_TEST_OUT (default /tmp/gencp_plugin_test.txt), because a `--code`
script's stdout is swallowed by the application.
"""
from __future__ import annotations
import os, sys, time
from pathlib import Path

# QGIS's --code execs this file in a namespace where __file__ may be undefined, so the
# repository root is resolved defensively. Getting this wrong kills the script before it
# can open its output file, which looks exactly like "QGIS never ran the script".
try:
    ROOT = Path(__file__).resolve().parents[2]
except NameError:                                    # pragma: no cover - --code path
    ROOT = Path(os.environ.get("GENCP_REPO_ROOT", os.getcwd())).resolve()
sys.path.insert(0, str(ROOT / "tubitak"))

from qgis.core import (Qgis, QgsApplication, QgsCoordinateReferenceSystem, QgsProject,
                       QgsRasterLayer)
from qgis.PyQt.QtWidgets import QApplication

FAILURES = []
CHECKS = []
_OUT = open(os.environ.get("GENCP_TEST_OUT", "/tmp/gencp_plugin_test.txt"), "w")


def say(*a):
    print(*a, file=_OUT, flush=True)


def check(name, cond, detail=""):
    CHECKS.append((name, bool(cond), detail))
    say(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f"  - {detail}" if detail else ""))
    if not cond:
        FAILURES.append(name)


def main():
    owned = QgsApplication.instance() is None
    if owned:
        qgs = QgsApplication([], True)
        QgsApplication.setPrefixPath(os.environ.get("QGIS_PREFIX", "/usr"), True)
        qgs.initQgis()
    say(f"QGIS {Qgis.QGIS_VERSION}, offscreen, "
        f"{'standalone' if owned else 'inside the QGIS application process'}")
    say(f"executable: {sys.executable}\n")

    # gencp_core must import inside QGIS's interpreter without torch
    import gencp_core
    from gencp_core import extent, infer, pipeline
    say("=== gencp_core inside QGIS python ===")
    check("gencp_core imports in QGIS python", True)
    check("torch is NOT required", "torch" not in sys.modules,
          "the plugin must not need PyTorch inside QGIS")
    import onnxruntime
    check("onnxruntime available in QGIS python", True, onnxruntime.__version__)

    # a real reference layer
    stem = "ank_0_30"
    ref_path = ROOT / f"tubitak/data/ankara/run/ref/{stem}.tif"
    layer = QgsRasterLayer(str(ref_path), "reference")
    check("reference layer loads", layer.isValid(), str(ref_path.name))
    QgsProject.instance().addMapLayer(layer)

    say("\n=== dialog construction and section wiring ===")
    from qgis_plugin.dialog import GenCPDialog
    from qgis.PyQt.QtWidgets import QMessageBox

    # A modal QMessageBox never returns under the offscreen platform, so an error path
    # would hang this harness forever instead of failing. Record instead of block.
    POPUPS = []
    for _name in ("critical", "warning", "information"):
        def _stub(parent, title, text, *a, _n=_name, **k):
            POPUPS.append((_n, title, text))
            say(f"    [popup:{_n}] {title}: {str(text)[:160]}")
            return 0
        setattr(QMessageBox, _name, staticmethod(_stub))

    class FakeIface:
        def mainWindow(self): return None
        def messageBar(self):
            class B:
                def pushMessage(self, *a, **k): say("    messageBar:", a[:2])
            return B()

    dlg = GenCPDialog(FakeIface())
    check("dialog constructs", dlg is not None)
    dlg.layer_box.setLayer(layer)
    QApplication.processEvents()

    # 1 Input
    check("section 1 shows the read extent", "→" in dlg.lbl_extent.text(),
          dlg.lbl_extent.text()[:60])
    check("section 1 shows the CRS", "EPSG:32636" in dlg.lbl_crs.text(), dlg.lbl_crs.text())
    # Derived from the plugin's own strings module, not from English literals: the UI is
    # Turkish, and a test that asserted "tiles"/"min" was testing the language rather than
    # the behaviour.
    from qgis_plugin.strings import S as STR
    note_lead = STR["tiles_estimate_note"].split("{")[0].strip()
    check("section 1 shows tiles + estimate",
          note_lead in dlg.lbl_tiles.text() and "<b>" in dlg.lbl_tiles.text(),
          dlg.lbl_tiles.text().replace("<br>", " ")[:90])

    # 2 Data source — must block until resolved
    dlg.pbf_edit.setText("")
    dlg.rb_local.setChecked(True)
    QApplication.processEvents()
    check("section 2 blocks preview until the source is resolved",
          not dlg.btn_preview.isEnabled(), "empty pbf path")
    pbf = ROOT / "tubitak/data/tool_runs/task3/extent.osm.pbf"
    dlg.pbf_edit.setText(str(pbf))
    QApplication.processEvents()
    check("section 2 unblocks once resolved", dlg.btn_preview.isEnabled(), pbf.name)

    # 4 Model
    model = ROOT / "tubitak/data/plugin_models/gencp_C3_fp32.onnx"
    dlg.model_edit.setText(str(model))
    dlg._describe_model()
    QApplication.processEvents()
    check("section 4 shows model name", model.name in dlg.lbl_model.text())
    mod_lead = STR["model_desc"].split("{name}")[1].split("{")[0].strip()
    check("section 4 shows modification date", mod_lead in dlg.lbl_model.text(),
          dlg.lbl_model.text().replace("<br>", " ")[:80])

    # 5 Run must be gated on the preview confirmation
    check("Run is disabled before the preview is confirmed", not dlg.btn_run.isEnabled())

    say("\n=== section 3: preview actually renders on screen ===")
    dlg.overlap_box.setCurrentIndex(0)   # 0 m overlap -> 1 tile over this small extent
    QApplication.processEvents()
    t0 = time.time()
    dlg._render_preview()
    QApplication.processEvents()
    pm = dlg.preview_label.pixmap()
    got = pm is not None and not pm.isNull()
    if POPUPS:
        say("    popups seen during preview: " + str(POPUPS[-1])[:200])
    check("preview renders a real image", got,
          f"{pm.width()}x{pm.height()} px in {time.time()-t0:.1f}s" if got else "no pixmap")
    check("preview is not a thumbnail", got and pm.width() >= 256,
          f"{pm.width()} px" if got else "")
    check("confirmation checkbox enabled after preview", dlg.cb_confirm.isEnabled())

    out = ROOT / "tubitak/data/plugin_gates/plugin_headless_out.tif"
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()
    dlg.out_edit.setText(str(out))
    dlg.cb_write.setChecked(True)
    dlg.cb_add_layer.setChecked(True)
    dlg.cb_confirm.setChecked(False)
    QApplication.processEvents()
    check("Run still disabled while the preview is unconfirmed",
          not dlg.btn_run.isEnabled(), "everything else is filled in")
    dlg.cb_confirm.setChecked(True)
    QApplication.processEvents()
    check("Run enabled once the preview is confirmed", dlg.btn_run.isEnabled())

    say("\n=== section 5/6: generation on a QgsTask, then layer + GeoTIFF ===")

    from qgis.PyQt.QtCore import QThread
    from qgis_plugin.task import GenerateTask
    main_thread = QApplication.instance().thread()
    seen = {"offthread": None, "progress": []}

    _orig_run = GenerateTask.run
    def _instrumented(self):
        seen["offthread"] = QThread.currentThread() is not main_thread
        return _orig_run(self)
    GenerateTask.run = _instrumented

    dlg._start()
    task = dlg._task
    check("a QgsTask was created", task is not None)

    deadline = time.time() + 900
    while dlg._task is not None and time.time() < deadline:
        QApplication.processEvents()
        seen["progress"].append(task.progress())
        time.sleep(0.05)

    check("generation completed", dlg._task is None and task.exception is None,
          str(task.exception) if task.exception else dlg.lbl_status.text()[:70])
    check("inference ran OFF the main thread", seen["offthread"] is True,
          "QgsTask worker thread")
    check("progress bar advanced", len(set(seen["progress"])) > 2,
          f"{len(set(seen['progress']))} distinct values")
    check("GeoTIFF written to the chosen path", out.is_file(),
          f"{out.stat().st_size/1e6:.2f} MB" if out.is_file() else "missing")
    names = [l.name() for l in QgsProject.instance().mapLayers().values()]
    check("result added as a QGIS layer", out.stem in names, ", ".join(names))

    say("\n=== cancellation ===")
    dlg.cb_confirm.setChecked(True)
    dlg.out_edit.setText(str(out.with_name("cancel_probe.tif")))
    QApplication.processEvents()
    # The cancelled flag is captured on the PYTHON side, before QGIS's task manager can
    # delete the C++ object. Reading t2.isCanceled() after the fact raised
    # "wrapped C/C++ object of type GenerateTask has been deleted" as soon as runs got fast
    # enough for the task to be reaped before the assertion - a lifetime bug in this
    # harness, not in the plugin, and one that only showed up once the confidence work
    # removed 16 inference passes.
    seen_cancel = {}

    _orig_cancel = GenerateTask.cancel
    def _record_cancel(self):
        seen_cancel["flag"] = True
        return _orig_cancel(self)
    GenerateTask.cancel = _record_cancel

    dlg._start()
    t2 = dlg._task
    t2.taskTerminated.connect(
        lambda: seen_cancel.setdefault("terminated", True))
    QApplication.processEvents()
    dlg._cancel()
    deadline = time.time() + 300
    while dlg._task is not None and time.time() < deadline:
        QApplication.processEvents()
        time.sleep(0.05)
    GenerateTask.cancel = _orig_cancel
    check("cancel stops the task",
          seen_cancel.get("flag") and seen_cancel.get("terminated")
          and dlg._task is None,
          f"cancel called={seen_cancel.get('flag')}, terminated="
          f"{seen_cancel.get('terminated')}, status={dlg.lbl_status.text()[:40]!r}")

    say("\n" + "=" * 62)
    say(f"{len(CHECKS)-len(FAILURES)}/{len(CHECKS)} checks passed")
    if FAILURES:
        say("FAILED: " + ", ".join(FAILURES))
    say("=" * 62)
    _OUT.close()
    return 1 if FAILURES else 0


# NOT guarded by __name__ == "__main__": QGIS's --code execs this file in a namespace
# where __name__ is not "__main__", so a guard would silently skip the whole test and
# leave an empty output file.
if True:
    rc = 0
    try:
        rc = main()
    except Exception:
        import traceback
        say("HARNESS CRASH:\n" + traceback.format_exc())
        _OUT.close()
        rc = 2
    # A --code script runs inside a live application; sys.exit would not end it.
    os._exit(rc)
