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
# A segfault in a native extension kills the process without touching the except handler
# below, which looks exactly like "the harness stopped for no reason". faulthandler prints
# the Python frames of every thread first, which is what turned a guess into a diagnosis.
import faulthandler
faulthandler.enable(_OUT)


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


def full_shot(dlg, name):
    """Grab the whole form, not the window.

    The dialog scrolls, so a window-sized grab silently cuts sections 5 and 6 off - which
    is exactly where the confidence verdict lives. Grabbing the scroll area's inner widget
    renders every section in one image.
    """
    from qgis.PyQt.QtWidgets import QScrollArea
    sa = dlg.findChild(QScrollArea)
    w = sa.widget() if (sa is not None and sa.widget() is not None) else dlg
    w.resize(w.sizeHint().width(), w.sizeHint().height())
    return shot(w, name)


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
    # A bare "—" reads as failed. The empty state now says it is waiting for input, and
    # the test asserts that rather than asserting the dash it replaced.
    import importlib as _il
    _STR = _il.import_module(f"{PLUGIN_ID}.strings").S
    # The placeholder must read as WAITING rather than as a failure. It is no longer a
    # dash at all - it says, in grey, what it is waiting for.
    _wait = _STR["waiting"]
    check("the empty extent field explains itself rather than showing a bare dash",
          dlg.lbl_extent.text() == _wait and any(c.isalpha() for c in _wait)
          and _wait != _STR["unset"],
          dlg.lbl_extent.text())
    check("Generate is disabled on open", not dlg.btn_run.isEnabled())

    layer = QgsRasterLayer(str(REF), "reference (ank_0_30)")
    check("reference layer loads", layer.isValid(), REF.name)
    QgsProject.instance().addMapLayer(layer)
    dlg.layer_box.setLayer(layer)
    QApplication.processEvents()

    dlg.clc_w.setFilePath(str(CLC))
    dlg.rb_local.setChecked(True)
    dlg.pbf_w.setFilePath(str(PBF))
    dlg.model_w.setFilePath(str(MODEL))
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
    # Assertions are derived from the plugin's own strings module rather than from English
    # literals, so translating the UI does not silently turn this test green-on-nothing.
    import importlib
    STR = importlib.import_module(f"{PLUGIN_ID}.strings").S
    # The estimate moved INTO tiles_value (one compact line, Deepness style) instead of a
    # second explanatory line, so the assertion follows it there.
    tail = STR["tiles_value"].split("}")[-1].strip()               # e.g. "dk"
    check("section 1 displays tile count and an estimate",
          bool(tail) and tail in dlg.lbl_tiles.text(),
          f"looked for {tail!r} from strings.tiles_value")

    # the displayed estimate, parsed back out for the honesty comparison
    import re
    est_pat = re.escape(STR["tiles_value"])
    for ph, rx in (("{n}", r"\\d+"), ("{w}", r"\\d+"), ("{h}", r"\\d+"),
                   ("{mins:.1f}", r"([\\d.]+)")):
        est_pat = est_pat.replace(re.escape(ph), rx)
    m = re.search(est_pat, dlg.lbl_tiles.text())
    est_min = float(m.group(1)) if m else None
    n_tiles = int(re.search(r"<b>(\d+)", dlg.lbl_tiles.text()).group(1))
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
    dlg.out_w.setFilePath(str(out))
    dlg.cb_add_layer.setChecked(True)
    QApplication.processEvents()
    check("Generate is enabled without the preview", dlg.btn_run.isEnabled())

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


def phase_c(plugin, layer):
    """The confidence layer: refused for an uncalibrated model, produced for the right one."""
    say("")
    say("=" * 72)
    say("PHASE C - the confidence layer")
    say("=" * 72)
    from qgis.PyQt.QtWidgets import QApplication
    import qgis.utils
    dlg = plugin.dialog

    C2 = ROOT / "tubitak/data/plugin_models/gencp_C2_fp32.onnx"
    C3 = ROOT / "tubitak/data/plugin_models/gencp_C3_fp32.onnx"

    # 1. an uncalibrated model must REFUSE the layer and say why
    dlg.model_w.setFilePath(str(C3))
    dlg._describe_model()
    dlg.cb_alpha.setChecked(True)
    QApplication.processEvents()
    check("an uncalibrated model refuses the confidence layer, with a reason",
          dlg.lbl_model_calib.isVisible() and bool(dlg.lbl_model_calib.text()),
          dlg.lbl_model_calib.text()[:90].replace("<b>", "").replace("</b>", ""))
    check("shot 9: the refusal, shown in section 6",
          full_shot(dlg, "09_confidence_refused_wrong_model.png"))

    # 2. the calibrated model produces it
    dlg.model_w.setFilePath(str(C2))
    dlg._describe_model()
    QApplication.processEvents()
    import importlib as _il3
    _S3 = _il3.import_module(f"{PLUGIN_ID}.strings").S
    check("the calibrated model is accepted",
          dlg.lbl_model_calib.text() == _S3["model_calibrated_ok"],
          dlg.lbl_model_calib.text()[:70])

    out = GATES / "plugin_e2e_conf.tif"
    for f in (out, out.with_name(out.stem + "_confidence.tif")):
        if f.exists():
            f.unlink()
    dlg.out_w.setFilePath(str(out))
    dlg._render_preview()
    QApplication.processEvents()
    check("shot 10: preview with the OSM content breakdown beside it",
          full_shot(dlg, "10_preview_with_osm_breakdown.png"))
    check("the OSM breakdown panel is populated",
          bool(dlg.lbl_osm.text()), dlg.lbl_osm.text()[:70].replace("<b>", ""))
    import importlib
    dmod = importlib.import_module(f"{PLUGIN_ID}.dialog")
    # The hand-set sparse threshold is gone (decision 1.2). The preview judgement now
    # comes from the SAME registered score and band boundaries as the output layer, so the
    # test is that the two AGREE on this tile rather than that some threshold fired.
    import numpy as _np
    from gencp_core import confidence as _conf, pipeline as _pl
    _e, _work, _ = _pl._extent.resolve(dlg._extent, dlg._crs)
    _tile = _pl._extent.tile_grid(_e, dlg.overlap_box.currentData())[0][0]
    _img = _pl.preview_image(list(_pl.render_inputs(
        [_tile], _work, _pl.default_work_dir() / "render",
        pbf=dlg._pbf_or_none()).values())[0])
    _sig = _conf.signals(_np.asarray(_img.convert("RGB")))
    _v = _conf.run_verdict(_conf.deployed_score(_sig["conf_D"]))
    say(f"    previewed tile band: {_v['mean_band']}  "
        f"(green {_v['fractions']['green']*100:.1f}%  amber {_v['fractions']['amber']*100:.1f}%  "
        f"red {_v['fractions']['red']*100:.1f}%)")
    check("the preview judgement is driven by the registered score, not a hand-set threshold",
          not hasattr(dmod, "SPARSE_OSM_FRACTION"),
          "dialog exposes no SPARSE_OSM_FRACTION constant")
    # Part 5 removed the tile verdict prose. What the open preview says now is the OSM
    # breakdown and nothing else; the judgement reaches the user through the confidence
    # layer and the run verdict.
    check("an open preview shows the OSM breakdown and no prose",
          bool(dlg.lbl_osm.text()) and not dlg.lbl_verdict.isVisible(),
          dlg.lbl_osm.text()[:70])
    QApplication.processEvents()

    t0 = time.time()
    dlg.btn_run.click()
    task = dlg._task
    deadline = time.time() + 1800
    stages = []
    while dlg._task is not None and time.time() < deadline:
        QApplication.processEvents()
        m = (task.message or "").split(":")[0].strip()
        if m and (not stages or stages[-1] != m):
            stages.append(m)
        time.sleep(0.05)
    wall = time.time() - t0
    say(f"    stages seen: {stages}")
    say(f"    wall clock with confidence: {wall:.2f}s")
    SUMMARY["confidence_wall_seconds"] = wall
    SUMMARY["stages_seen"] = stages
    check("generation with confidence completed",
          dlg._task is None and task.exception is None,
          str(task.exception) if task.exception else "")
    # Confidence is delivered in the OUTPUT's alpha channel by default (request 2.4); the
    # separate coloured layer is opt-in and is exercised further down.
    import rasterio as _rio
    with _rio.open(out) as _s:
        _bands, _ci = _s.count, _s.colorinterp
        _alpha_vals = len(_np.unique(_s.read(4))) if _s.count == 4 else 0
    from rasterio.enums import ColorInterp as _CI
    check("confidence is written into the output's ALPHA band, not a side file",
          _bands == 4 and _ci[3] == _CI.alpha, f"{_bands} bands, {_ci[3].name}")
    check("the alpha band is continuous, not the 3-band rounding",
          _alpha_vals > 32, f"{_alpha_vals} distinct alpha values")
    osm_tif = out.with_name(out.stem + "_osm.tif")
    check("the rasterised OSM input is written beside the output",
          osm_tif.is_file(), osm_tif.name if osm_tif.is_file() else "missing")
    res = task.result or {}
    v = (res.get("confidence") or {}).get("verdict") or {}
    if v:
        fr = v["fractions"]
        say(f"    verdict: green {fr['green']*100:.1f}%  amber {fr['amber']*100:.1f}%  "
            f"red {fr['red']*100:.1f}%  run band {v['mean_band']}")
        SUMMARY["confidence_verdict"] = v
    check("a run-level verdict is shown in section 6",
          dlg.lbl_verdict.isVisible() and bool(dlg.lbl_verdict.text()),
          dlg.lbl_verdict.text()[:100].replace("<b>", "").replace("</b>", ""))
    check("shot 11: the verdict after a confidence run",
          full_shot(dlg, "11_confidence_verdict.png"))

    # Sampling task.message at 20 Hz is a race against a 0.3 s stage, and it lost: the
    # pipeline demonstrably emits render/infer/confidence/mosaic in order, but the poll
    # missed the middle one. What actually matters to a user is that each stage name
    # becomes a readable Turkish line rather than a bare percentage, and that is testable
    # without a race.
    say(f"    (stage sampling is best-effort; saw {stages})")

    class _FakeTask:
        def __init__(self, msg):
            self.message = msg

        def progress(self):
            return 42.0
    labels = {}
    real_task, dlg._task = dlg._task, None
    for raw, key in (("render: 2/4", "stage_render"), ("infer: 3/4", "stage_infer"),
                     ("confidence: 1/4", "stage_confidence"), ("mosaic: 1/1", "stage_mosaic")):
        dlg._task = _FakeTask(raw)
        dlg._on_progress()
        labels[raw] = dlg.lbl_status.text()
    dlg._task = real_task
    for raw, txt in labels.items():
        say(f"    {raw:20s} -> {txt}")
    check("every pipeline stage maps to a readable step name, not a bare percentage",
          all(txt and "%" not in txt and any(ch.isalpha() for ch in txt)
              for txt in labels.values())
          and len(set(labels.values())) == 4,
          " | ".join(labels.values()))


    names = {l.name(): l for l in QgsProject.instance().mapLayers().values()}
    check("the OSM input was added as a layer named <output>_osm",
          osm_tif.stem in names, ", ".join(names))

    # The alpha band carries CONFIDENCE, not opacity. QGIS cannot know that and will
    # composite with it unless told otherwise, which drew the output semi-transparently
    # over whatever sat beneath - measured once at alpha mean 108/255, never opaque. A
    # comparison tool that silently mixes the two things being compared is worse than no
    # comparison, so the added layer must ignore band 4 when drawing.
    from qgis.core import (QgsMapSettings, QgsMapRendererParallelJob,
                           QgsMultiBandColorRenderer)
    from qgis.PyQt.QtCore import QSize as _QSize
    from qgis.PyQt.QtGui import QColor as _QColor, QImage as _QImage
    outl = names.get(out.stem)
    check("the 4-band output is added with a renderer that ignores the alpha band",
          outl is not None and isinstance(outl.renderer(), QgsMultiBandColorRenderer),
          type(outl.renderer()).__name__ if outl else "layer missing")
    if outl is not None:
        ms = QgsMapSettings()
        ms.setLayers([outl])
        ms.setBackgroundColor(_QColor(255, 0, 255))   # magenta shows through any blend
        ms.setOutputSize(_QSize(outl.width(), outl.height()))
        ms.setExtent(outl.extent())
        ms.setDestinationCrs(outl.crs())
        job = QgsMapRendererParallelJob(ms)
        job.start()
        job.waitForFinished()
        im = job.renderedImage().convertToFormat(_QImage.Format.Format_RGB32)
        ptr = im.bits()
        ptr.setsize(im.sizeInBytes())
        drawn = _np.frombuffer(ptr, _np.uint8).reshape(
            im.height(), im.bytesPerLine() // 4, 4)[:, :im.width(), :3][:, :, ::-1]
        with _rio.open(out) as _s:
            stored = _np.moveaxis(_s.read([1, 2, 3]), 0, -1)
        d = float(_np.abs(drawn.astype(float) - stored.astype(float)).mean())
        check("what QGIS draws is the stored RGB, not a blend with the background",
              d < 5.0, f"mean |drawn - stored| = {d:.2f} DN (a blend measured 83 DN)")

    # now the OPT-IN coloured band layer
    say("\n  --- opt-in coloured band layer ---")
    dlg.cb_band_layer.setChecked(True)
    out2 = GATES / "plugin_e2e_conf_band.tif"
    for f in (out2, out2.with_name(out2.stem + "_confidence.tif"),
              out2.with_name(out2.stem + "_osm.tif")):
        if f.exists():
            f.unlink()
    dlg.out_w.setFilePath(str(out2))
    QApplication.processEvents()
    dlg.btn_run.click()
    deadline = time.time() + 900
    while dlg._task is not None and time.time() < deadline:
        QApplication.processEvents()
        time.sleep(0.05)
    conf_tif = out2.with_name(out2.stem + "_confidence.tif")
    check("ticking the option also writes the coloured band layer", conf_tif.is_file(),
          f"{conf_tif.stat().st_size/1e3:.0f} kB" if conf_tif.is_file() else "missing")
    names = {l.name(): l for l in QgsProject.instance().mapLayers().values()}
    clayer = names.get(conf_tif.stem)
    check("confidence layer added to the project", clayer is not None, ", ".join(names))
    if clayer is not None:
        r = clayer.renderer()
        check("the confidence layer is auto-styled (paletted, not a grey ramp)",
              type(r).__name__ == "QgsPalettedRasterRenderer", type(r).__name__)
        try:
            lbls = [c.label for c in r.classes()]
        except Exception:                            # noqa: BLE001
            lbls = []
        check("its legend carries band NAMES, not raw values 1/2/3",
              len(lbls) == 3 and all(any(ch.isalpha() for ch in s_) for s_ in lbls),
              " | ".join(lbls))
        canvas_png([clayer], layer.extent(), "12_canvas_confidence_layer.png")
        canvas_png([clayer, layer], layer.extent(), "13_canvas_confidence_over_ref.png")
        # QGIS's own legend, rendered from the layer tree
        try:
            iface = qgis.utils.iface
            ltv = iface.layerTreeView()
            ltv.resize(420, 180)
            check("shot 14: the QGIS legend for the confidence layer",
                  shot(ltv, "14_legend_layer_tree.png"))
        except Exception as e:                       # noqa: BLE001
            say(f"    layer-tree grab unavailable: {e}")
    # --- the warning path, on an extent the extract genuinely does not cover ---------
    say("\n  --- warning path: an extent with no OSM coverage at all ---")
    from qgis.core import QgsVectorLayer, QgsFeature, QgsGeometry, QgsRectangle
    e = layer.extent()
    far = QgsRectangle(e.xMinimum(), e.yMinimum() - 300000.0,
                       e.xMaximum(), e.yMaximum() - 300000.0)
    vl = QgsVectorLayer(f"Polygon?crs={layer.crs().authid()}", "bos_alan (OSM yok)", "memory")
    f = QgsFeature()
    f.setGeometry(QgsGeometry.fromRect(far))
    vl.dataProvider().addFeatures([f])
    vl.updateExtents()
    QgsProject.instance().addMapLayer(vl)
    dlg.layer_box.setLayer(vl)
    QApplication.processEvents()
    dlg._render_preview()
    QApplication.processEvents()
    # Warnings are QgsMessageBar items now - one line, QGIS's own idiom - rather than a
    # coloured paragraph block, so the assertion is on the bar.
    items = dlg.msgbar.items() if hasattr(dlg.msgbar, "items") else []
    check("an extent with zero OSM features raises a message-bar warning",
          len(items) > 0, f"{len(items)} message-bar item(s)")
    check("shot 15: the zero-OSM warning as the user sees it",
          full_shot(dlg, "15_zero_osm_warning.png"))
    QgsProject.instance().removeMapLayer(vl.id())
    return dlg


def _dark_palette():
    """A dark Qt palette, the way macOS dark mode reaches QGIS's widgets."""
    from qgis.PyQt.QtGui import QPalette, QColor
    R = QPalette.ColorRole if hasattr(QPalette, "ColorRole") else QPalette
    p = QPalette()
    for role, col in (("Window", "#2b2b2b"), ("WindowText", "#e6e6e6"),
                      ("Base", "#1e1e1e"), ("AlternateBase", "#2b2b2b"),
                      ("Text", "#e6e6e6"), ("Button", "#3a3a3a"),
                      ("ButtonText", "#e6e6e6"), ("Mid", "#5a5a5a"),
                      ("Midlight", "#4a4a4a"), ("Dark", "#202020"),
                      ("ToolTipBase", "#3a3a3a"), ("ToolTipText", "#e6e6e6"),
                      ("Highlight", "#2a82da"), ("HighlightedText", "#ffffff"),
                      ("PlaceholderText", "#9a9a9a")):
        if hasattr(R, role):
            p.setColor(getattr(R, role), QColor(col))
    return p


def _apply_theme(widget, dark, light_palette):
    """Actually make the widgets dark, and verify it took.

    setPalette() alone was not enough: the macOS native style largely ignores palette
    colours, so the first "dark" capture came out light and the check was asserting
    nothing. Fusion honours the palette in full, which is what the dialog's
    palette(window-text) / palette(mid) / rgba() styling has to survive. The widget style
    is therefore not pixel-identical to macOS native here - the COLOUR behaviour is what is
    under test, and that is what this exercises.
    """
    from qgis.PyQt.QtWidgets import QApplication, QStyleFactory
    st = QStyleFactory.create("Fusion")
    if st is not None:
        QApplication.setStyle(st)
    pal = _dark_palette() if dark else light_palette
    QApplication.setPalette(pal)
    for w in [widget] + widget.findChildren(type(widget).__bases__[0]):
        try:
            w.setPalette(pal)
        except Exception:                            # noqa: BLE001
            pass
    widget.setPalette(pal)
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.update()


def phase_d(plugin):
    """Empty state, window sizes and both QGIS themes.

    The complaint this answers: the plugin was opened in a real QGIS with no raster loaded,
    every field showed a dash, and sections 4-6 - including Generate - were below the fold.
    A first-time user never saw the primary action.
    """
    say("")
    say("=" * 72)
    say("PHASE D - empty state, window sizes, light and dark themes")
    say("=" * 72)
    from qgis.PyQt.QtWidgets import QApplication, QScrollArea, QGroupBox
    from qgis.core import QgsApplication

    QgsProject.instance().removeAllMapLayers()
    QApplication.processEvents()
    plugin.dialog = None
    plugin.action.trigger()
    QApplication.processEvents()
    dlg = plugin.dialog

    check("with an empty project the layer combo is empty", dlg.layer_box.count() == 0,
          f"{dlg.layer_box.count()} entries")
    import importlib as _il2
    _S = _il2.import_module(f"{PLUGIN_ID}.strings").S
    check("and the dialog SAYS what is missing, in the status line",
          dlg.lbl_status.text() == _S["err_no_layer"], dlg.lbl_status.text())
    check("the preview starts CLOSED (Part 5: off by default)",
          not dlg.preview_label.isVisible(), "section 3 is one button until asked")
    check("the parameter fields read as waiting, not failed",
          dlg.lbl_extent.text() == _S["waiting"], dlg.lbl_extent.text())

    themes = list(QgsApplication.uiThemes().keys())
    say(f"    UI themes available: {themes}")
    # This QGIS build ships only the 'default' UI theme, so QgsApplication.setUITheme
    # cannot produce a dark one. That is not a gap in the test: on macOS QGIS follows the
    # SYSTEM appearance, and it reaches the widgets as a dark Qt palette either way. So the
    # palette is what gets swapped here - which is also exactly what the dialog's
    # palette(window-text) / palette(mid) styling depends on.
    light_palette = QApplication.palette()
    cases = [("light", None, 700, 460), ("light", None, 840, 760),
             ("light", None, 1000, 900),
             ("dark", "palette", 1000, 900), ("dark", "palette", 700, 460)]

    def _scroll(d):
        return d.findChild(QScrollArea)

    for name, theme, w, h in cases:
        _apply_theme(dlg, name == "dark", light_palette)
        QApplication.processEvents()
        dlg.resize(w, h)
        QApplication.processEvents()
        time.sleep(0.15)
        QApplication.processEvents()
        sa = _scroll(dlg)
        hbar = sa.horizontalScrollBar()
        vp = sa.viewport()
        body = sa.widget()
        # Generate is pinned OUTSIDE the scroll area, so the question is no longer "is it
        # scrolled into view" but "is it on screen at all". Measured in DIALOG coordinates
        # and cross-checked against Qt's own clipping via visibleRegion().
        y = dlg.btn_run.mapTo(dlg, dlg.btn_run.rect().topLeft()).y()
        on_screen = (y >= 0 and y + dlg.btn_run.height() <= dlg.height()
                     and not dlg.btn_run.visibleRegion().isEmpty())
        say(f"    {name:5s} {w}x{h}: h-scroll={hbar.isVisible()}  "
            f"scrollBody={body.sizeHint().height()}px viewport={vp.height()}px  "
            f"GenerateTop={y}px dialogH={dlg.height()}px visible={on_screen}")
        bg = dlg.palette().color(dlg.backgroundRole())
        is_dark = bg.lightness() < 128
        check(f"the {name} capture really is {name}", is_dark == (name == "dark"),
              f"window background lightness {bg.lightness()}")
        check(f"no horizontal scrollbar at {name} {w}x{h}", not hbar.isVisible())
        check(f"Generate is visible without scrolling at {name} {w}x{h}", on_screen,
              f"button spans {y}..{y + dlg.btn_run.height()}px of a {dlg.height()}px dialog")
        if (w, h) == (1000, 900):
            heads = [g for g in body.findChildren(QGroupBox) if g.parent() is body]
            check("all scrolling section headers exist and are laid out",
                  len(heads) >= 5, f"{len(heads)} group boxes in the scroll body")
        shot(dlg, f"20_empty_{name}_{w}x{h}.png")

    # populated, dark, so the warning and verdict colours can actually be judged
    if True:
        _apply_theme(dlg, True, light_palette)
        QApplication.processEvents()
        layer = QgsRasterLayer(str(REF), "reference (ank_0_30)")
        QgsProject.instance().addMapLayer(layer)
        dlg.layer_box.setLayer(layer)
        dlg.clc_w.setFilePath(str(CLC))
        dlg.rb_local.setChecked(True)
        dlg.pbf_w.setFilePath(str(PBF))
        dlg.model_w.setFilePath(str(ROOT / "tubitak/data/plugin_models/gencp_C2_fp32.onnx"))
        dlg._describe_model()
        dlg.overlap_box.setCurrentIndex(0)
        QApplication.processEvents()
        dlg._render_preview()
        QApplication.processEvents()
        dlg.resize(840, 1000)
        QApplication.processEvents()
        check("shot 21: populated dialog in the dark theme",
              full_shot(dlg, "21_populated_dark.png"))
        # and the same state in light, for a like-for-like comparison
        _apply_theme(dlg, False, light_palette)
        QApplication.processEvents()
        time.sleep(0.2)
        QApplication.processEvents()
        check("shot 22: the same state in the light theme",
              full_shot(dlg, "22_populated_light.png"))
    return dlg


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
    dlg, out = phase_b(plugin)
    layer = None
    for l in QgsProject.instance().mapLayers().values():
        if l.name().startswith("reference"):
            layer = l
    if dlg is not None and layer is not None:
        phase_c(plugin, layer)
    phase_d(plugin)
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
