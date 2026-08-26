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
        from .dialog import GenCPDialog
        if self.dialog is None:
            self.dialog = GenCPDialog(self.iface, self.iface.mainWindow())
        self.dialog.show()
        self.dialog.raise_()
        self.dialog.activateWindow()
