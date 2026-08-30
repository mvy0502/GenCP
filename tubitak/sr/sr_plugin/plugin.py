"""Menu and toolbar registration. Holds no super-resolution logic."""
from __future__ import annotations
import sys
from pathlib import Path

from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QIcon

PLUGIN_DIR = Path(__file__).resolve().parent


def ensure_core_importable():
    """Make `sr_core` importable, and return the directory it was found under.

    Deployed, `sr_core` is vendored beside this file. In the research repository it sits
    one level up, in `tubitak/sr/`. Both are supported so the plugin can be run from a
    checkout without a packaging step - the same arrangement Project 1's plugin uses for
    `gencp_core`, and for the same reason.
    """
    for cand in (PLUGIN_DIR, PLUGIN_DIR.parent, PLUGIN_DIR.parent.parent):
        if (cand / "sr_core" / "__init__.py").is_file():
            if str(cand) not in sys.path:
                sys.path.insert(0, str(cand))
            return cand
    return None


class GenCPSRPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.dialog = None

    def initGui(self):
        # Resolve sr_core as soon as the plugin STARTS, not on the first click. Project 1
        # shipped a version that resolved it only in run(), and anything that touched the
        # core between startPlugin() and the first button press got ModuleNotFoundError.
        ensure_core_importable()
        icon_path = PLUGIN_DIR / "icon.png"
        icon = QIcon(str(icon_path)) if icon_path.is_file() else QIcon()
        self.action = QAction(icon, "GenCP Super-Resolution...",
                              self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addPluginToRasterMenu("&GenCP SR", self.action)
        self.iface.addToolBarIcon(self.action)

    def unload(self):
        if self.action is not None:
            self.iface.removePluginRasterMenu("&GenCP SR", self.action)
            self.iface.removeToolBarIcon(self.action)
            self.action = None
        if self.dialog is not None:
            self.dialog.close()
            self.dialog = None

    def run(self):
        ensure_core_importable()
        from .dialog import SRDialog
        if self.dialog is None:
            self.dialog = SRDialog(self.iface, self.iface.mainWindow())
        self.dialog.show()
        self.dialog.raise_()
        self.dialog.activateWindow()
