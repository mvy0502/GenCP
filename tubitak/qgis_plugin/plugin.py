"""Menu and toolbar registration. Holds no generation logic."""
from __future__ import annotations
import os
import sys
from pathlib import Path

from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QIcon

PLUGIN_DIR = Path(__file__).resolve().parent


def ensure_core_importable():
    """Make `gencp_core` importable.

    Deployed, gencp_core is vendored beside this file. In the research repository it sits
    one level up, in tubitak/. Both are supported so the plugin can be run from a checkout
    without a packaging step.
    """
    for cand in (PLUGIN_DIR, PLUGIN_DIR.parent, PLUGIN_DIR.parent.parent):
        if (cand / "gencp_core" / "__init__.py").is_file():
            if str(cand) not in sys.path:
                sys.path.insert(0, str(cand))
            return cand
    return None


#: Heavy dependencies that are NOT bundled with QGIS and that this plugin cannot work
#: without. Checked by import, not by reading a manifest: what matters is whether THIS
#: interpreter can import it. `rasterio` is needed to open the dialog at all (gencp_core
#: .extent uses it); `onnxruntime` is needed to generate.
REQUIRED_MODULES = (("rasterio", "err_no_rasterio"),
                    ("onnxruntime", "err_no_onnxruntime"))


def _python_env_hint():
    """This QGIS's own site-packages directory, so the user installs into the right one."""
    import sys
    cands = [p for p in sys.path if p.endswith("site-packages")]
    return cands[-1] if cands else sys.prefix


def missing_requirements():
    """[(module, message_key)] for every required module this interpreter cannot import."""
    import importlib
    out = []
    for mod, key in REQUIRED_MODULES:
        try:
            importlib.import_module(mod)
        except Exception:
            out.append((mod, key))
    return out


class GenCPPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.dialog = None

    def initGui(self):
        # Make gencp_core importable as soon as the plugin STARTS, not on the first click.
        # run() also calls this, so the click path was fine, but anything that touched
        # gencp_core between startPlugin() and the first press of the button got
        # ModuleNotFoundError - which is exactly what the zip-install test hit. A plugin
        # that has been started should be usable, not usable-after-you-click-it.
        ensure_core_importable()
        icon_path = PLUGIN_DIR / "icon.png"
        icon = QIcon(str(icon_path)) if icon_path.is_file() else QIcon()
        self.action = QAction(icon, "GenCP Synthetic Reference...",
                              self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addPluginToRasterMenu("&GenCP", self.action)
        self.iface.addToolBarIcon(self.action)

    def unload(self):
        if self.action is not None:
            self.iface.removePluginRasterMenu("&GenCP", self.action)
            self.iface.removeToolBarIcon(self.action)
            self.action = None
        if self.dialog is not None:
            self.dialog.close()
            self.dialog = None

    def run(self):
        ensure_core_importable()
        missing = missing_requirements()
        if missing:
            # The dialog is NOT constructed. Building it would re-enter the same failing
            # import and put a traceback on screen, which is the behaviour this replaces.
            # The static call takes no enum argument, so there is nothing here that is
            # spelled differently on Qt5 and Qt6 - the failure mode qtcompat.member exists
            # for. Qt's default AutoText detects the <b> tags and renders rich text.
            from qgis.PyQt.QtWidgets import QMessageBox
            from .strings import t
            QMessageBox.warning(
                self.iface.mainWindow(), t("err_missing_title"),
                "<br><br>".join(t(k, where=_python_env_hint()) for _m, k in missing))
            return
        from .dialog import GenCPDialog
        if self.dialog is None:
            self.dialog = GenCPDialog(self.iface, self.iface.mainWindow())
        self.dialog.show()
        self.dialog.raise_()
        self.dialog.activateWindow()
