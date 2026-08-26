#!/usr/bin/env python
"""Install gencp_plugin.zip into a CLEAN QGIS profile and run one generation from it.

An installer that has never been installed from is not verified. This runs QGIS against a
throwaway profile that has never seen this plugin, feeds the zip to the SAME code path the
Plugins > Manage and Install Plugins > Install from ZIP button uses
(`pyplugin_installer.instance().installFromZipFile`), starts the plugin, and generates a
raster through the dialog.

The point that the development profile cannot test: there is no symlink and no repository
on sys.path, so `gencp_core` must resolve to the copy VENDORED inside the zip. That is
asserted explicitly - if it silently resolved to the checkout, the test would pass while
the zip was broken for everyone else.

    QT_QPA_PLATFORM=offscreen /Applications/QGIS-*.app/Contents/MacOS/QGIS-* \
        --profile gencp_zip_test --nologo --code tubitak/tests/plugin_zip_install.py

Driven by tubitak/tests/run_zip_install.sh, which creates and destroys the profile.
"""
from __future__ import annotations
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(os.environ["GENCP_REPO_ROOT"]).resolve()
ZIP = Path(os.environ.get("GENCP_PLUGIN_ZIP",
                          ROOT / "tubitak/data/dist/gencp_plugin.zip"))
PLUGIN_ID = "gencp_synthetic_reference"
# Data paths are passed explicitly: a zip install has no repository to prefill from, and
# that is exactly the situation a real user is in.
REF = ROOT / "tubitak/data/ankara/run/ref/ank_0_30.tif"
PBF = ROOT / "tubitak/data/tool_runs/task3/extent.osm.pbf"
MODEL = ROOT / "tubitak/data/plugin_models/gencp_C3_fp32.onnx"
CLC = ROOT / "tubitak/data/clcplus/CLMS_CLCplus_RASTER_2021_010m_eu_03035_V1_1.tif"

CHECKS = []
_OUT = open(os.environ.get("GENCP_TEST_OUT", "/tmp/gencp_zip_install.txt"), "w")


def say(*a):
    print(*a, file=_OUT, flush=True)


def check(name, cond, detail=""):
    CHECKS.append((name, bool(cond), detail))
    say(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f"  - {detail}" if detail else ""))
    return bool(cond)


def main():
    import traceback
    from qgis.core import Qgis, QgsApplication, QgsProject, QgsRasterLayer
    from qgis.PyQt.QtWidgets import QApplication, QMessageBox

    SLOT_EXC = []

    def hook(t, v, tb):
        SLOT_EXC.append("".join(traceback.format_exception(t, v, tb)))
        say("    [slot exception] " + "".join(
            traceback.format_exception_only(t, v)).strip())
    sys.excepthook = hook
    for _n in ("critical", "warning", "information", "question"):
        setattr(QMessageBox, _n, staticmethod(lambda *a, **k: 0))

    prof = QgsApplication.qgisSettingsDirPath()
    say("=" * 72)
    say("ZIP INSTALL INTO A CLEAN PROFILE")
    say("=" * 72)
    say(f"  profile   : {prof}")
    say(f"  QGIS      : {Qgis.QGIS_VERSION}")
    say(f"  zip       : {ZIP}  ({ZIP.stat().st_size/1e6:.2f} MB)")

    plugins_dir = Path(prof) / "python" / "plugins"
    pre = sorted(p.name for p in plugins_dir.glob("*")) if plugins_dir.exists() else []
    check("the profile starts with this plugin absent", PLUGIN_ID not in pre,
          f"plugins present before install: {pre}")
    check("nothing in the profile is a symlink to the checkout",
          not any((plugins_dir / n).is_symlink() for n in pre), f"{pre}")

    say("\n  --- install from ZIP ---")
    import pyplugin_installer
    inst = pyplugin_installer.instance()
    used = ""
    try:
        inst.installFromZipFile(str(ZIP))
        used = "pyplugin_installer.installFromZipFile (the Install from ZIP button's own path)"
    except Exception as e:                           # noqa: BLE001
        say(f"    installFromZipFile raised: {type(e).__name__}: {e}")
        used = "FAILED"
    check("installFromZipFile completed without raising", used != "FAILED", used)

    landed = plugins_dir / PLUGIN_ID
    check("the zip unpacked to one folder named for the plugin", landed.is_dir(),
          str(landed))
    check("metadata.txt is at the root of that folder", (landed / "metadata.txt").is_file())
    check("gencp_core came with it (vendored, not borrowed)",
          (landed / "gencp_core" / "pipeline.py").is_file())
    check("the installed folder is a real directory, not a symlink",
          landed.is_dir() and not landed.is_symlink())

    say("\n  --- load and start it ---")
    import qgis.utils
    qgis.utils.updateAvailablePlugins()
    qgis.utils.loadPlugin(PLUGIN_ID)
    already = PLUGIN_ID in qgis.utils.plugins
    started = already or qgis.utils.startPlugin(PLUGIN_ID)
    # installFromZipFile starts the plugin itself, and QGIS's startPlugin returns False
    # for an already-started plugin. "False" there is not a failure, so the assertion is
    # on the observable end state.
    check("the plugin is started (classFactory + initGui ran)", started,
          "started by installFromZipFile" if already else "started explicitly")
    plugin = qgis.utils.plugins.get(PLUGIN_ID)
    check("the plugin object is registered", plugin is not None)
    if plugin is None:
        return 1
    check("initGui created the menu/toolbar action", plugin.action is not None,
          plugin.action.text() if plugin.action else "")

    import gencp_core
    core_file = Path(gencp_core.__file__).resolve()
    check("gencp_core resolves to the copy INSIDE the installed plugin",
          str(core_file).startswith(str(landed.resolve())),
          str(core_file))
    check("gencp_core did NOT come from the repository checkout",
          "tubitak/gencp_core" not in str(core_file).replace(str(landed), ""),
          str(core_file))

    say("\n  --- one generation, through the dialog ---")
    plugin.action.trigger()
    QApplication.processEvents()
    dlg = plugin.dialog
    check("the toolbar action opens the dialog", dlg is not None)
    if dlg is None:
        return 1

    layer = QgsRasterLayer(str(REF), "reference")
    check("reference layer loads", layer.isValid())
    QgsProject.instance().addMapLayer(layer)
    dlg.layer_box.setLayer(layer)
    dlg.clc_edit.setText(str(CLC))
    dlg.rb_local.setChecked(True)
    dlg.pbf_edit.setText(str(PBF))
    dlg.model_edit.setText(str(MODEL))
    dlg._describe_model()
    dlg.overlap_box.setCurrentIndex(0)
    QApplication.processEvents()
    check("section 1 reads the extent from the layer", "→" in dlg.lbl_extent.text(),
          dlg.lbl_extent.text()[:60])

    t0 = time.time()
    dlg._render_preview()
    QApplication.processEvents()
    pm = dlg.preview_label.pixmap()
    check("preview renders", pm is not None and not pm.isNull(),
          f"{pm.width()}x{pm.height()} px in {time.time()-t0:.1f}s" if pm else "none")

    out = Path(prof) / "gencp_zip_install_output.tif"
    if out.exists():
        out.unlink()
    dlg.out_edit.setText(str(out))
    dlg.cb_write.setChecked(True)
    dlg.cb_add_layer.setChecked(True)
    dlg.cb_confirm.setChecked(True)
    QApplication.processEvents()
    check("Generate is enabled", dlg.btn_run.isEnabled())

    t0 = time.time()
    dlg.btn_run.click()
    task = dlg._task
    deadline = time.time() + 900
    while dlg._task is not None and time.time() < deadline:
        QApplication.processEvents()
        time.sleep(0.05)
    wall = time.time() - t0
    check("generation completed", task is not None and task.exception is None,
          str(task.exception) if task and task.exception else f"{wall:.2f}s")
    check("GeoTIFF written", out.is_file(),
          f"{out.stat().st_size/1e6:.2f} MB" if out.is_file() else "missing")

    if out.is_file():
        import rasterio
        with rasterio.open(out) as s_:
            T, w, h, crs = s_.transform, s_.width, s_.height, s_.crs
            prov = json.loads(s_.tags().get("GENCP_PROVENANCE", "{}"))
        r = layer.extent()
        check("Gate G contract holds on the zip-installed plugin's output",
              T.a == 10.0 and -T.e == 10.0 and T.c == r.xMinimum() and T.f == r.yMaximum()
              and (w, h) == (257, 257),
              f"{w}x{h} px, transform {tuple(T)[:6]}, {crs}")
        check("provenance embedded", bool(prov.get("model_sha256")),
              f"{len(prov)} fields")

    names = [l.name() for l in QgsProject.instance().mapLayers().values()]
    check("output added to the project as a layer", out.stem in names, ", ".join(names))
    check("no exceptions were raised inside Qt slots", not SLOT_EXC,
          f"{len(SLOT_EXC)} slot exception(s)")

    say("\n" + "=" * 72)
    failed = [n for n, ok, _ in CHECKS if not ok]
    say(f"{len(CHECKS)-len(failed)}/{len(CHECKS)} checks passed")
    if failed:
        say("FAILED: " + "; ".join(failed))
    say("=" * 72)
    return 1 if failed else 0


if True:
    rc = 2
    try:
        rc = main()
    except Exception:
        import traceback
        say("HARNESS CRASH:\n" + traceback.format_exc())
    _OUT.close()
    os._exit(rc)
