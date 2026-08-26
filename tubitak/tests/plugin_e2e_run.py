#!/usr/bin/env python
"""End-to-end run of the INSTALLED plugin, through the dialog's own code path.

Distinct from `test_plugin_headless.py`, which imports `qgis_plugin.dialog` straight from
the checkout. This one goes the way a user goes:

    QGIS starts -> reads the user profile -> loads the plugin from
    python/plugins/gencp_synthetic_reference -> calls classFactory -> initGui ->
    the toolbar action's slot -> GenCPDialog

so it also proves the *installation* works, not only that the code works. If the symlink,
the profile ini entry or `ensure_core_importable` were wrong, this fails at phase A and the
checkout-based test would still pass.

Run it through the QGIS APPLICATION BINARY (see run_in_qgis.sh for why the bundled
python3.12 is the wrong interpreter on macOS).

Writes:
  - a transcript to GENCP_TEST_OUT
  - PNG screenshots to tubitak/docs/evidence/plugin_screens/
  - a JSON summary to tubitak/data/plugin_gates/plugin_e2e_summary.json
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

from qgis.core import (Qgis, QgsApplication, QgsMapSettings, QgsProject,
                       QgsRasterLayer, QgsRectangle)
from qgis.core import QgsMapRendererParallelJob
from qgis.PyQt.QtCore import QSize, QThread
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import QApplication, QMessageBox

SHOTS = ROOT / "tubitak/docs/evidence/plugin_screens"
GATES = ROOT / "tubitak/data/plugin_gates"
REF = ROOT / "tubitak/data/ankara/run/ref/ank_0_30.tif"
PBF = ROOT / "tubitak/data/tool_runs/task3/extent.osm.pbf"
MODEL = ROOT / "tubitak/data/plugin_models/gencp_C3_fp32.onnx"
CLC = ROOT / "tubitak/data/clcplus/CLMS_CLCplus_RASTER_2021_010m_eu_03035_V1_1.tif"
PLUGIN_ID = "gencp_synthetic_reference"

CHECKS = []
SUMMARY = {}
_OUT = open(os.environ.get("GENCP_TEST_OUT", "/tmp/gencp_e2e.txt"), "w")


def say(*a):
    print(*a, file=_OUT, flush=True)


def check(name, cond, detail=""):
    CHECKS.append((name, bool(cond), detail))
    say(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f"  - {detail}" if detail else ""))
    return bool(cond)


POPUPS = []


def stub_popups():
    """A modal QMessageBox never returns offscreen: it would hang, not fail."""
    for _name in ("critical", "warning", "information", "question"):
        def _stub(parent, title, text, *a, _n=_name, **k):
            POPUPS.append((_n, title, str(text)))
            say(f"    [popup:{_n}] {title}: {str(text)[:200]}")
            return 0
        setattr(QMessageBox, _name, staticmethod(_stub))


def shot(widget, name):
    """QWidget.grab() renders the widget through the paint system, no display needed."""
    SHOTS.mkdir(parents=True, exist_ok=True)
    QApplication.processEvents()
    pm = widget.grab()
    p = SHOTS / name
    ok = pm.save(str(p))
    say(f"    [shot] {name}  {pm.width()}x{pm.height()}  {'ok' if ok else 'SAVE FAILED'}")
    return ok and p.is_file()


def canvas_png(layers, extent, name, size=(760, 760)):
    """Render layers offscreen through QGIS's own renderer - proves they overlay."""
    ms = QgsMapSettings()
    ms.setLayers(layers)
    ms.setBackgroundColor(QColor(255, 255, 255))
    ms.setOutputSize(QSize(*size))
    ms.setExtent(extent)
    ms.setDestinationCrs(layers[0].crs())
    job = QgsMapRendererParallelJob(ms)
    job.start()
    job.waitForFinished()
    img = job.renderedImage()
    SHOTS.mkdir(parents=True, exist_ok=True)
    ok = img.save(str(SHOTS / name))
    say(f"    [canvas] {name}  {img.width()}x{img.height()}  {'ok' if ok else 'FAILED'}")
    return ok


def checkerboard(a_name, b_name, out_name, blocks=8):
    """Interleave two same-size renders in a checkerboard. Misalignment steps at seams."""
    from PIL import Image, ImageDraw
    a = Image.open(SHOTS / a_name).convert("RGB")
    b = Image.open(SHOTS / b_name).convert("RGB").resize(a.size)
    out = a.copy()
    bw, bh = a.width // blocks, a.height // blocks
    for r in range(blocks):
        for c in range(blocks):
            if (r + c) % 2 == 0:
                continue
            box = (c * bw, r * bh, (c + 1) * bw, (r + 1) * bh)
            out.paste(b.crop(box), box)
    d = ImageDraw.Draw(out)
    for k in range(1, blocks):
        d.line([(k * bw, 0), (k * bw, a.height)], fill=(255, 255, 0), width=1)
        d.line([(0, k * bh), (a.width, k * bh)], fill=(255, 255, 0), width=1)
    out.save(SHOTS / out_name)
    say(f"    [checker] {out_name}  {out.width}x{out.height}  "
        f"({blocks}x{blocks} blocks: generated output vs the real reference image)")
    return (SHOTS / out_name).is_file()


def gate_g_contract_on(tif, ref_layer):
    """Gate G part A, re-asserted on the raster THIS dialog run produced.

    tubitak/tests/gate_g.py calls pipeline.generate itself. That proves the contract holds
    for the library; it does not prove the dialog passes the library the right arguments.
    The arithmetic below is the same registered snapping rule, read off the file the
    Generate button wrote.
    """
    import json
    import rasterio
    from gencp_core import extent as gext
    from gencp_core.extent import NOMINAL
    say("\n  --- Gate G georeferencing contract, on the dialog's own output ---")
    r = ref_layer.extent()
    ref_extent = (r.xMinimum(), r.yMinimum(), r.xMaximum(), r.yMaximum())
    with rasterio.open(tif) as s_:
        o_T, o_w, o_h, o_crs = s_.transform, s_.width, s_.height, s_.crs
        prov = json.loads(s_.tags().get("GENCP_PROVENANCE", "{}"))
    exp_w, exp_h, exp_T = gext.output_grid(ref_extent)
    check("G/A pixel size is exactly 10.0 m on both axes",
          o_T.a == NOMINAL and -o_T.e == NOMINAL, f"x={o_T.a!r} y={-o_T.e!r}")
    check("G/A origin is the reference NW corner exactly",
          o_T.c == ref_extent[0] and o_T.f == ref_extent[3],
          f"offset x {o_T.c - ref_extent[0]!r} m, y {o_T.f - ref_extent[3]!r} m")
    check("G/A size == ceil(span / GSD)", (o_w, o_h) == (exp_w, exp_h),
          f"got {o_w}x{o_h}, expected {exp_w}x{exp_h}")
    check("G/A transform equals the registered affine term by term",
          tuple(o_T)[:6] == tuple(exp_T)[:6], f"{tuple(o_T)[:6]}")
    check("G/A output CRS == reference CRS",
          o_crs.to_string() == ref_layer.crs().toWkt() or
          o_crs.to_authority() == tuple(ref_layer.crs().authid().split(":")),
          f"{o_crs} vs {ref_layer.crs().authid()}")
    check("G provenance embedded in the dialog's output",
          bool(prov.get("model_sha256")) and bool(prov.get("snapping_rule")),
          f"{len(prov)} fields; model {prov.get('model_file')}")
    SUMMARY["gate_g_provenance"] = prov


# ------------------------------------------------------------------ phase A --
def phase_a():
    say("=" * 72)
    say("PHASE A - is the plugin actually INSTALLED in this profile?")
    say("=" * 72)
    import qgis.utils
    prof = QgsApplication.qgisSettingsDirPath()
    say(f"  profile in use : {prof}")
    say(f"  QGIS           : {Qgis.QGIS_VERSION}")
    say(f"  executable     : {sys.executable}")
    SUMMARY["profile"] = prof
    SUMMARY["qgis_version"] = Qgis.QGIS_VERSION

    loaded = sorted(qgis.utils.plugins.keys())
    say(f"  loaded plugins : {loaded}")
    check("plugin is loaded by QGIS from the user profile", PLUGIN_ID in loaded,
          f"{PLUGIN_ID} in qgis.utils.plugins")
    if PLUGIN_ID not in loaded:
        say(f"  plugin load errors: {qgis.utils.pluginLoadErrors() if hasattr(qgis.utils,'pluginLoadErrors') else 'n/a'}")
        return None

    plugin = qgis.utils.plugins[PLUGIN_ID]
    say(f"  plugin object  : {plugin!r}")
    say(f"  plugin module  : {sys.modules[PLUGIN_ID].__file__}")
    SUMMARY["plugin_module"] = sys.modules[PLUGIN_ID].__file__

    # QGIS only registers a plugin in qgis.utils.plugins AFTER initGui() returns without
    # raising, so the action existing is the observable evidence that it completed.
    check("initGui() completed - the QAction exists", plugin.action is not None,
          plugin.action.text() if plugin.action else "no action")

    iface = qgis.utils.iface
    tb_actions = [a.text() for a in iface.mainWindow().findChildren(type(plugin.action))]
    in_menu = plugin.action.text() in tb_actions
    check("the action is registered on the main window (menu/toolbar)", in_menu,
          plugin.action.text())
    return plugin


# ------------------------------------------------------------------ phase B --
def phase_b(plugin):
    say("")
    say("=" * 72)
    say("PHASE B - drive the dialog the way the toolbar button does")
    say("=" * 72)

    QgsProject.instance().removeAllMapLayers()
    QApplication.processEvents()

    # This is the toolbar action's own slot. Nothing here reaches into the dialog module.
    plugin.action.trigger()
    QApplication.processEvents()
    dlg = plugin.dialog
    check("triggering the toolbar action opened the dialog", dlg is not None)
    if dlg is None:
        return None, None

    dlg.resize(780, 1180)
    dlg.show()
    QApplication.processEvents()
    time.sleep(0.3)
    QApplication.processEvents()
    check("shot 1: dialog on open, nothing selected",
          shot(dlg, "01_dialog_on_open.png"))
    check("with no layer in the project the extent reads as unset",
          dlg.lbl_extent.text() == "—", repr(dlg.lbl_extent.text()))
    check("Generate is disabled on open", not dlg.btn_run.isEnabled())

    layer = QgsRasterLayer(str(REF), "reference (ank_0_30)")
    check("reference layer loads", layer.isValid(), REF.name)
    QgsProject.instance().addMapLayer(layer)
    dlg.layer_box.setLayer(layer)
    QApplication.processEvents()

    dlg.clc_edit.setText(str(CLC))
    dlg.rb_local.setChecked(True)
    dlg.pbf_edit.setText(str(PBF))
    dlg.model_edit.setText(str(MODEL))
    dlg._describe_model()
    dlg.overlap_box.setCurrentIndex(0)          # 0 m overlap -> single tile, small run
    QApplication.processEvents()
    time.sleep(0.2)
    QApplication.processEvents()

    say(f"    extent : {dlg.lbl_extent.text()}")
    say(f"    crs    : {dlg.lbl_crs.text()}")
    say(f"    tiles  : {dlg.lbl_tiles.text()}")
    SUMMARY["extent_label"] = dlg.lbl_extent.text()
    SUMMARY["crs_label"] = dlg.lbl_crs.text()
    SUMMARY["tiles_label"] = dlg.lbl_tiles.text()
    check("shot 2: reference chosen, extent and CRS displayed",
          shot(dlg, "02_reference_selected.png"))
    check("section 1 displays the extent", "→" in dlg.lbl_extent.text())
    check("section 1 displays the CRS", "EPSG:" in dlg.lbl_crs.text(), dlg.lbl_crs.text())
    check("section 1 displays tile count and an estimate",
          "tile" in dlg.lbl_tiles.text() and "min" in dlg.lbl_tiles.text())

    # the displayed estimate, parsed back out for the honesty comparison
    import re
    m = re.search(r"estimate ([\d.]+) min", dlg.lbl_tiles.text())
    est_min = float(m.group(1)) if m else None
    n_tiles = int(re.search(r"(\d+) tiles?", dlg.lbl_tiles.text()).group(1))
    SUMMARY["estimate_minutes"] = est_min
    SUMMARY["n_tiles"] = n_tiles
    say(f"    parsed estimate: {est_min} min for {n_tiles} tile(s)")

    say("\n  --- preview ---")
    t0 = time.time()
    dlg._render_preview()
    QApplication.processEvents()
    t_preview = time.time() - t0
    SUMMARY["preview_seconds"] = t_preview
    pm = dlg.preview_label.pixmap()
    got = pm is not None and not pm.isNull()
    check("preview renders a real rasterised input", got,
          f"{pm.width()}x{pm.height()} px in {t_preview:.1f}s" if got else "no pixmap")
    check("shot 3: preview section with the render in it",
          shot(dlg, "03_preview_rendered.png"))
    if got:
        pm.save(str(SHOTS / "03b_preview_tile_only.png"))
        say("    [shot] 03b_preview_tile_only.png (the preview pixmap alone)")

    out = GATES / "plugin_e2e_output.tif"
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()
    dlg.out_edit.setText(str(out))
    dlg.cb_write.setChecked(True)
    dlg.cb_add_layer.setChecked(True)
    dlg.cb_confirm.setChecked(True)
    QApplication.processEvents()
    check("Generate enabled once the preview is confirmed", dlg.btn_run.isEnabled())

    say("\n  --- run ---")
    import importlib
    task_mod = importlib.import_module(f"{PLUGIN_ID}.task")
    main_thread = QApplication.instance().thread()
    seen = {"offthread": None, "progress": [], "thread_name": ""}
    _orig = task_mod.GenerateTask.run

    def _instrumented(self):
        t = QThread.currentThread()
        seen["offthread"] = t is not main_thread
        seen["thread_name"] = f"{t}"
        return _orig(self)
    task_mod.GenerateTask.run = _instrumented

    t0 = time.time()
    dlg.btn_run.click()                    # the real button, not _start()
    task = dlg._task
    check("clicking Generate created a QgsTask", task is not None,
          type(task).__mro__[1].__name__ if task else "")
    mid_shot = False
    stage_first = {}
    deadline = time.time() + 1800
    while dlg._task is not None and time.time() < deadline:
        QApplication.processEvents()
        p = task.progress()
        seen["progress"].append(p)
        st = (task.message or "").split(":")[0]
        if st and st not in stage_first:
            stage_first[st] = time.time() - t0
        if not mid_shot and p >= 25.0:
            mid_shot = check("shot 4: run in progress, progress bar advancing",
                             shot(dlg, "04_run_in_progress.png"),
                             f"captured at {p:.0f}%")
        time.sleep(0.05)
    wall = time.time() - t0
    SUMMARY["run_wall_seconds"] = wall
    SUMMARY["stage_first_seen_s"] = stage_first
    say(f"    stage first seen at (s): { {k: round(v,2) for k,v in stage_first.items()} }")
    if not mid_shot:
        check("shot 4: run in progress, progress bar advancing", False,
              "run finished before progress crossed 25%")

    check("generation completed", dlg._task is None and task.exception is None,
          str(task.exception) if task.exception else dlg.lbl_status.text()[:90])
    check("inference ran OFF the main thread", seen["offthread"] is True,
          seen["thread_name"])
    check("progress bar advanced through distinct values",
          len(set(seen["progress"])) > 2,
          f"{len(set(seen['progress']))} distinct values, max {max(seen['progress']):.0f}%")
    say(f"    wall clock (Generate click -> done): {wall:.2f}s ({wall/60:.3f} min)")
    say(f"    preview render before it:            {SUMMARY['preview_seconds']:.2f}s")
    total = wall + SUMMARY["preview_seconds"]
    SUMMARY["user_total_seconds"] = total
    est_s = (SUMMARY.get("estimate_minutes") or 0) * 60.0
    SUMMARY["estimate_seconds"] = est_s
    say(f"    what the user actually waits for:    {total:.2f}s")
    say(f"    what the dialog PREDICTED:           {est_s:.2f}s "
        f"({SUMMARY.get('estimate_minutes')} min for {SUMMARY.get('n_tiles')} tile(s))")
    if est_s:
        say(f"    estimate / actual run  = {est_s/wall:.2f}x")
        say(f"    estimate / actual total= {est_s/total:.2f}x")

    QApplication.processEvents()
    check("shot 5: final state after the output layer was added",
          shot(dlg, "05_after_completion.png"))
    # The dialog scrolls, so a window-sized grab cuts sections 5 and 6 off. Grabbing the
    # scroll area's inner widget renders the whole form in one image.
    from qgis.PyQt.QtWidgets import QScrollArea
    sa = dlg.findChild(QScrollArea)
    if sa is not None and sa.widget() is not None:
        inner = sa.widget()
        inner.resize(inner.sizeHint().width(), inner.sizeHint().height())
        check("shot 5b: the whole form in one image, no scrolling",
              shot(inner, "05b_full_form.png"))
    say(f"    status line: {dlg.lbl_status.text()}")
    SUMMARY["status_line"] = dlg.lbl_status.text()

    check("GeoTIFF written to the chosen path", out.is_file(),
          f"{out.stat().st_size/1e6:.2f} MB" if out.is_file() else "missing")
    names = {l.name(): l for l in QgsProject.instance().mapLayers().values()}
    check("output added to the project as a layer", out.stem in names,
          ", ".join(names))
    outl = names.get(out.stem)
    if outl is not None:
        check("the added layer is valid and opens", outl.isValid(),
              f"{outl.width()}x{outl.height()} px, {outl.crs().authid()}")
        check("output layer CRS == reference layer CRS",
              outl.crs() == layer.crs(),
              f"{outl.crs().authid()} vs {layer.crs().authid()}")
        oe, re_ = outl.extent(), layer.extent()
        check("output extent overlaps the reference extent",
              oe.intersects(re_),
              f"out {oe.toString(1)}  ref {re_.toString(1)}")
        dx = abs(oe.xMinimum() - re_.xMinimum())
        dy = abs(oe.yMaximum() - re_.yMaximum())
        check("output NW corner coincides with the reference NW corner",
              dx == 0.0 and dy == 0.0, f"dx {dx!r} m, dy {dy!r} m")
        gate_g_contract_on(out, layer)
        canvas_png([outl], re_, "06_canvas_output_only.png")
        canvas_png([layer], re_, "07_canvas_reference_only.png")
        # Stacking the two layers is worthless as evidence: the output is opaque and
        # simply hides the reference, so the composite is pixel-identical to the output
        # alone. A checkerboard alternates 8x8 blocks between the two rasters rendered
        # through the SAME QgsMapSettings, so any georeferencing offset shows up as roads
        # and field edges stepping sideways at every block boundary.
        check("shot 8: checkerboard of output against reference",
              checkerboard("06_canvas_output_only.png", "07_canvas_reference_only.png",
                           "08_checkerboard_output_vs_reference.png"))
    SUMMARY["output_tif"] = str(out)
    return dlg, out


def main():
    stub_popups()
    # An honest wall-clock number needs a cold cache. The first run of this harness
    # reported 0.6 s because a render left behind six hours earlier was still on disk.
    import shutil
    from gencp_core import pipeline as _pl
    wd = _pl.default_work_dir()
    if wd.exists():
        shutil.rmtree(wd)
        say(f"cleared the render cache at {wd} so the timing below is a cold one\n")
    plugin = phase_a()
    if plugin is None:
        return 1
    phase_b(plugin)
    say("")
    say("=" * 72)
    failed = [n for n, ok, _ in CHECKS if not ok]
    say(f"{len(CHECKS)-len(failed)}/{len(CHECKS)} checks passed")
    if failed:
        say("FAILED: " + "; ".join(failed))
    say("=" * 72)
    SUMMARY["checks"] = [dict(check=n, ok=o, detail=d) for n, o, d in CHECKS]
    SUMMARY["popups"] = POPUPS
    GATES.mkdir(parents=True, exist_ok=True)
    (GATES / "plugin_e2e_summary.json").write_text(json.dumps(SUMMARY, indent=2))
    return 1 if failed else 0


if True:                                   # --code execs with __name__ != "__main__"
    rc = 0
    try:
        rc = main()
    except Exception:
        import traceback
        say("HARNESS CRASH:\n" + traceback.format_exc())
        rc = 2
    _OUT.close()
    os._exit(rc)
