#!/usr/bin/env python
"""What the plugin does when things go wrong.

A tool is judged by its failure modes, and they are not equally bad. Ranked worst first:

  SILENT   produces an output that looks fine and is wrong. Nothing tells the user.
  FREEZE   the application stops responding.
  CRASH    a raw traceback reaches the user, or the dialog dies.
  MESSAGE  a comprehensible sentence naming the problem, and the dialog survives.
  BLOCKED  the control that would cause the failure is disabled before it can be pressed.

Each case below is driven through the INSTALLED plugin's dialog and classified. Run
through the QGIS application binary (see run_in_qgis.sh).
"""
from __future__ import annotations
import json
import os
import sys
import time
from pathlib import Path

try:
    ROOT = Path(__file__).resolve().parents[2]
except NameError:                                    # pragma: no cover - --code path
    ROOT = Path(os.environ.get("GENCP_REPO_ROOT", os.getcwd())).resolve()
sys.path.insert(0, str(ROOT / "tubitak"))

from qgis.core import (QgsCoordinateReferenceSystem, QgsCoordinateTransform,
                       QgsProject, QgsRasterLayer, QgsVectorLayer, QgsRectangle)
from qgis.PyQt.QtWidgets import QApplication, QMessageBox

REF = ROOT / "tubitak/data/ankara/run/ref/ank_0_30.tif"
PBF = ROOT / "tubitak/data/tool_runs/task3/extent.osm.pbf"
MODEL = ROOT / "tubitak/data/plugin_models/gencp_C3_fp32.onnx"
CLC = ROOT / "tubitak/data/clcplus/CLMS_CLCplus_RASTER_2021_010m_eu_03035_V1_1.tif"
GATES = ROOT / "tubitak/data/plugin_gates/failure_paths"
PLUGIN_ID = "gencp_synthetic_reference"

FINDINGS = []
_OUT = open(os.environ.get("GENCP_TEST_OUT", "/tmp/gencp_failures.txt"), "w")


def say(*a):
    print(*a, file=_OUT, flush=True)


POPUPS = []
SLOT_EXCEPTIONS = []


def capture_slot_exceptions():
    """Record exceptions raised inside Qt slots instead of letting QGIS block on them.

    PyQt cannot propagate an exception out of a slot, so it calls sys.excepthook. QGIS
    replaces that hook with one that opens a MODAL QgsMessageOutput dialog - which under
    the offscreen platform never returns, so the harness hangs instead of failing. That is
    how the construction-time AttributeError in _validate was found: this harness stopped
    dead, and the stack showed QDialog::exec() under _PyErr_PrintEx.
    """
    import traceback

    def hook(t, v, tb):
        SLOT_EXCEPTIONS.append("".join(traceback.format_exception(t, v, tb)))
        say("    [slot exception] " + "".join(
            traceback.format_exception_only(t, v)).strip())
    sys.excepthook = hook


def stub_popups():
    for _name in ("critical", "warning", "information", "question"):
        def _stub(parent, title, text, *a, _n=_name, **k):
            POPUPS.append((_n, title, str(text)))
            return 0
        setattr(QMessageBox, _name, staticmethod(_stub))


def record(case, verdict, evidence, note=""):
    FINDINGS.append(dict(case=case, verdict=verdict, evidence=evidence, note=note))
    say(f"\n  {case}")
    say(f"    verdict : {verdict}")
    say(f"    seen    : {evidence}")
    if note:
        say(f"    note    : {note}")


def fresh_dialog(plugin):
    if plugin.dialog is not None:
        plugin.dialog.close()
        plugin.dialog = None
    plugin.action.trigger()
    QApplication.processEvents()
    return plugin.dialog


def fill(dlg, layer, clc=str(CLC), pbf=str(PBF), model=str(MODEL), overlap_m=0):
    dlg.layer_box.setLayer(layer)
    dlg.clc_w.setFilePath(clc)
    dlg.rb_local.setChecked(True)
    dlg.pbf_w.setFilePath(pbf)
    dlg.model_w.setFilePath(model)
    dlg._describe_model()
    dlg.overlap_box.setValue(overlap_m)
    QApplication.processEvents()


def load_ref():
    lyr = QgsRasterLayer(str(REF), "reference")
    QgsProject.instance().addMapLayer(lyr)
    return lyr


def memory_layer_in(crs_authid, name):
    """A one-feature layer whose extent is the reference extent expressed in `crs_authid`.

    Used to hand the dialog a reference in a CRS it was not designed around, without
    fabricating a raster.
    """
    src = QgsRasterLayer(str(REF), "src")
    e = src.extent()
    tr = QgsCoordinateTransform(src.crs(), QgsCoordinateReferenceSystem(crs_authid),
                                QgsProject.instance())
    e2 = tr.transformBoundingBox(e)
    vl = QgsVectorLayer(f"Polygon?crs={crs_authid}", name, "memory")
    from qgis.core import QgsFeature, QgsGeometry
    f = QgsFeature()
    f.setGeometry(QgsGeometry.fromRect(e2))
    vl.dataProvider().addFeatures([f])
    vl.updateExtents()
    QgsProject.instance().addMapLayer(vl)
    return vl, e2


# --------------------------------------------------------------------- cases --
def case_clc_missing(plugin, layer):
    dlg = fresh_dialog(plugin)
    bad = "/no/such/place/clcplus.tif"
    fill(dlg, layer, clc=bad)
    blocked = not dlg.btn_preview.isEnabled()
    msg = dlg.lbl_status.text()
    # The message must NAME THE FILE, which is language-independent and is the part that
    # makes it actionable. Asserting an English phrase would test the locale instead.
    record("CLC+ path points at a file that does not exist",
           "BLOCKED" if blocked and bad in msg else "SEE EVIDENCE",
           f"preview button enabled={dlg.btn_preview.isEnabled()}; "
           f"message shown={msg!r}")


def case_clc_empty(plugin, layer):
    dlg = fresh_dialog(plugin)
    fill(dlg, layer, clc="")
    record("CLC+ path left empty",
           "BLOCKED" if not dlg.btn_preview.isEnabled() else "SEE EVIDENCE",
           f"preview enabled={dlg.btn_preview.isEnabled()}; status={dlg.lbl_status.text()!r}")


def case_clc_not_a_raster(plugin, layer):
    """The path exists but is not a raster - validation cannot catch this by stat()."""
    bogus = GATES / "not_a_raster.tif"
    bogus.parent.mkdir(parents=True, exist_ok=True)
    bogus.write_text("this is not a GeoTIFF\n")
    dlg = fresh_dialog(plugin)
    fill(dlg, layer, clc=str(bogus))
    POPUPS.clear()
    ok_before = dlg.isVisible()
    try:
        dlg._render_preview()
        crashed = False
        exc = ""
    except Exception as e:                           # noqa: BLE001
        crashed, exc = True, f"{type(e).__name__}: {e}"
    QApplication.processEvents()
    status = dlg.lbl_status.text()
    popup = POPUPS[-1] if POPUPS else None
    # _apply_clc_path sets GENCP_CLC_PATH for the whole QGIS session, so this case must
    # put it back or every later case renders against a text file. That leak is the
    # harness's, not the plugin's - the dialog rewrites the variable from its own field on
    # the next preview or run, and an empty field is blocked before it gets that far.
    os.environ["GENCP_CLC_PATH"] = str(CLC)
    try:
        from gencp_core import vectors as _v
        _v.CLC_PATH = CLC
    except Exception:                                # noqa: BLE001
        pass
    record("CLC+ path exists but is not a raster",
           "CRASH (uncaught)" if crashed else
           ("MESSAGE" if popup else "SEE EVIDENCE"),
           f"uncaught={exc or 'none'}; popup={str(popup)[:220]!r}; "
           f"status={status[:120]!r}; dialog still open={dlg.isVisible() and ok_before}",
           "the message is the underlying library's, not one this plugin wrote")


def case_pbf_missing(plugin, layer):
    dlg = fresh_dialog(plugin)
    fill(dlg, layer, pbf="/no/such/extract.osm.pbf")
    record("OSM extract path points at a file that does not exist",
           "BLOCKED" if not dlg.btn_preview.isEnabled() else "SEE EVIDENCE",
           f"preview enabled={dlg.btn_preview.isEnabled()}; status={dlg.lbl_status.text()!r}")


def case_model_missing(plugin, layer):
    dlg = fresh_dialog(plugin)
    fill(dlg, layer, model="/no/such/model.onnx")
    dlg._render_preview()
    QApplication.processEvents()
    dlg.out_w.setFilePath(str(GATES / "never.tif"))
    QApplication.processEvents()
    record("ONNX model path points at a file that does not exist",
           "BLOCKED" if not dlg.btn_run.isEnabled() else "SEE EVIDENCE",
           f"Generate enabled={dlg.btn_run.isEnabled()}; "
           f"model label={dlg.lbl_model.text()[:60]!r}")


def case_no_osm_coverage(plugin, layer):
    """An extent the .osm.pbf does not cover at all.

    The interesting question is not whether it errors - it is whether it produces a
    confident, empty-looking image with no warning.
    """
    import rasterio
    from gencp_core import pipeline, extent as gext
    # Same UTM zone, far outside the Ankara extract: 300 km east.
    e = layer.extent()
    far = (e.xMinimum(), e.yMinimum() - 300000.0,
           e.xMaximum(), e.yMaximum() - 300000.0)
    out = GATES / "no_osm_coverage.tif"
    out.parent.mkdir(parents=True, exist_ok=True)
    os.environ["GENCP_CLC_PATH"] = str(CLC)
    # A cache entry rendered before feature counting existed has no sidecar, and the
    # warning would then read "no feature count available" instead of the real answer.
    import shutil as _sh
    if (GATES / "work_nocov").exists():
        _sh.rmtree(GATES / "work_nocov")
    POPUPS.clear()
    err = ""
    try:
        res = pipeline.generate(far, "EPSG:32636", str(MODEL), out, pbf=str(PBF),
                                base_product="clcplus", overlap_m=0.0,
                                work_dir=GATES / "work_nocov")
        with rasterio.open(res["renders"]["0_0"]) as s:
            arr = s.read()
        import numpy as np
        uniq = len(np.unique(arr.reshape(arr.shape[0], -1).T, axis=0))
        wrote = out.is_file()
        warns = res.get("warnings") or []
        feats = (res.get("tile_stats") or {}).get("0_0", {}).get("n_osm_features")
    except Exception as ex:                          # noqa: BLE001
        err = f"{type(ex).__name__}: {ex}"
        uniq, wrote, warns, feats = -1, False, [], None
    record("extent with no OSM coverage in the chosen .osm.pbf",
           "CRASH" if err else ("WARNED" if warns else "SILENT"),
           f"error={err or 'none'}; output written={wrote}; "
           f"OSM features found={feats}; warnings raised={warns}; "
           f"distinct colours in the rasterised input={uniq}",
           "no vectors means no roads, buildings or water are drawn; the CLC+ base is "
           "still there, so the render looks like a plausible empty landscape rather "
           "than like an error")


def case_unexpected_crs(plugin):
    """A reference layer in a CRS the chain was not designed around."""
    from gencp_core import extent as gext
    for authid, why in (("EPSG:4326", "geographic, explicitly handled"),
                        ("EPSG:3857", "projected but NOT metric - units are metres only "
                                      "at the equator"),
                        ("EPSG:4258", "geographic (ETRS89) but not EPSG:4326")):
        vl, e2 = memory_layer_in(authid, f"ref_{authid.replace(':','_')}")
        dlg = fresh_dialog(plugin)
        fill(dlg, vl)
        label = dlg.lbl_tiles.text().replace("<br>", " | ")
        bbox = (e2.xMinimum(), e2.yMinimum(), e2.xMaximum(), e2.yMaximum())
        try:
            ext, work, src = gext.resolve(bbox, authid)
            span_x = ext[2] - ext[0]
            w, h, _ = gext.output_grid(ext)
            detail = (f"working CRS {work}; extent span {span_x:.1f} working units; "
                      f"output grid {w} x {h} px")
            # The reference really is 2570 m across. Anything far from that is wrong.
            wrong = not (2000 < span_x < 3200)
            verdict = "SILENT (wrong scale, no warning)" if wrong else "HANDLED"
        except Exception as ex:                      # noqa: BLE001
            detail = f"{type(ex).__name__}: {ex}"
            verdict = "MESSAGE"
        record(f"reference layer in {authid} ({why})", verdict,
               f"{detail}; dialog shows: {label[:150]}")
        QgsProject.instance().removeMapLayer(vl.id())


def case_cancel_midrun(plugin, layer):
    """Cancel must stop the work, not just grey the button."""
    from gencp_core import pipeline
    import shutil
    wd = pipeline.default_work_dir()
    if wd.exists():
        shutil.rmtree(wd)                # cold cache, so there is time to press Cancel
    dlg = fresh_dialog(plugin)
    # 160 m overlap over this extent gives 4 tiles; a cold render is seconds per tile.
    fill(dlg, layer, overlap_m=160)
    n = dlg.lbl_tiles.text()
    dlg._render_preview()
    QApplication.processEvents()
    out = GATES / "cancelled.tif"
    if out.exists():
        out.unlink()
    dlg.out_w.setFilePath(str(out))
    QApplication.processEvents()
    if not dlg.btn_run.isEnabled():
        record("cancel mid-run", "NOT TESTED", "Generate never became enabled")
        return
    dlg.btn_run.click()
    task = dlg._task
    t0 = time.time()
    # let it get properly under way
    while time.time() - t0 < 3.0 and dlg._task is not None:
        QApplication.processEvents()
        time.sleep(0.02)
    still_running = dlg._task is not None
    progress_at_cancel = task.progress() if still_running else None
    responsive_calls = 0
    if still_running:
        dlg.btn_cancel.click()
        t1 = time.time()
        while dlg._task is not None and time.time() - t1 < 120:
            QApplication.processEvents()     # if this ever blocked, the GUI had frozen
            responsive_calls += 1
            time.sleep(0.02)
        stop_seconds = time.time() - t1
    else:
        stop_seconds = None
    record("Cancel pressed mid-run",
           "NOT TESTED (finished too fast)" if not still_running else
           ("MESSAGE" if dlg._task is None else "FREEZE / did not stop"),
           f"tiles={n[:40]!r}; progress when cancelled={progress_at_cancel}; "
           f"stopped after {stop_seconds if stop_seconds is None else round(stop_seconds,2)}s; "
           f"event loop serviced {responsive_calls} times while cancelling; "
           f"status={dlg.lbl_status.text()[:60]!r}; "
           f"partial file left on disk={out.exists()}",
           "a partial GeoTIFF left behind after a cancel would be the dangerous outcome")


def main():
    stub_popups()
    capture_slot_exceptions()
    GATES.mkdir(parents=True, exist_ok=True)
    import qgis.utils
    plugin = qgis.utils.plugins.get(PLUGIN_ID)
    if plugin is None:
        say("plugin not loaded; cannot test failure paths")
        return 2
    say("=" * 74)
    say("FAILURE PATHS - what a user sees when things go wrong")
    say("=" * 74)
    layer = load_ref()

    case_clc_empty(plugin, layer)
    case_clc_missing(plugin, layer)
    case_pbf_missing(plugin, layer)
    case_model_missing(plugin, layer)
    case_clc_not_a_raster(plugin, layer)
    case_unexpected_crs(plugin)
    case_no_osm_coverage(plugin, layer)
    case_cancel_midrun(plugin, layer)

    record("exceptions raised inside Qt slots during all of the above",
           "CLEAN" if not SLOT_EXCEPTIONS else "CRASH (modal error box in real QGIS)",
           f"{len(SLOT_EXCEPTIONS)} uncaught slot exception(s)",
           SLOT_EXCEPTIONS[0][-300:] if SLOT_EXCEPTIONS else "")

    say("\n" + "=" * 74)
    say("SUMMARY")
    for f in FINDINGS:
        say(f"  {f['verdict']:34s} {f['case']}")
    say("=" * 74)
    (GATES / "failure_paths.json").write_text(json.dumps(FINDINGS, indent=2))
    return 0


if True:
    rc = 2
    try:
        rc = main()
    except Exception:
        import traceback
        say("HARNESS CRASH:\n" + traceback.format_exc())
    _OUT.close()
    os._exit(rc)
