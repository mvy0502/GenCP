"""Menu and toolbar registration. Holds no super-resolution logic."""
from __future__ import annotations
import sys
from pathlib import Path

from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import Qt

from .qtcompat import member

_RICH = member(Qt.TextFormat, 'RichText') if hasattr(Qt, 'TextFormat') else 1

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
                # APPEND, not insert(0). WP2B open item: inserting at position 0 put this
                # plugin's own directory ahead of everything, so a bare `import strings` or
                # `import dialog` anywhere in the QGIS process resolved to OUR module. That
                # was demonstrated, not theorised - `import strings` was measured resolving
                # to this package. Appending means we are consulted only after every
                # existing path, so the SR plugin can no longer shadow another plugin's
                # modules. sr_core is unaffected: no other entry on sys.path provides it.
                sys.path.append(str(cand))
            return cand
    return None


#: Third-party modules the plugin cannot work without, with the strings key that explains
#: each absence in Turkish. WP2B open item 1: rasterio is the dependency most likely to be
#: missing on another machine, and its absence used to surface as a ModuleNotFoundError
#: behind a bare "Başarısız:".
# ONLY what EVERY path needs. rasterio is read by the dialog to describe the source and by
# sr_core to read and write every raster, so its absence stops everything.
#
# `yaml` is deliberately NOT here, although the wsx4 path needs it. Listing it would make
# the dialog refuse to open without PyYAML - including the BICUBIC path, which never touches
# yaml and which is the recovery plan if anything else fails during the demonstration. A
# recovery path must not depend on a package only the failing path needs. yaml is therefore
# checked where it is used, in `onnx_upsample._from_yaml_sidecar`, which raises the same
# readable Turkish message (`err_no_yaml`) the dialog already knows how to display.
REQUIRED_MODULES = (("rasterio", "err_no_rasterio"),)


def missing_requirements():
    """[(module, strings_key)] for every hard requirement that will not import."""
    import importlib
    out = []
    for mod, key in REQUIRED_MODULES:
        try:
            importlib.import_module(mod)
        except Exception:                            # noqa: BLE001 - absence is the answer
            out.append((mod, key))
    return out


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
        missing = missing_requirements()
        if missing:
            # Readable, in Turkish, naming the package - not a traceback in the log panel.
            from qgis.PyQt.QtWidgets import QMessageBox
            from .strings import t
            box = QMessageBox(self.iface.mainWindow())
            box.setWindowTitle(t("window_title"))
            box.setTextFormat(_RICH)
            box.setText("<br><br>".join(t(key) for _m, key in missing))
            box.exec()
            return
        from .dialog import SRDialog
        if self.dialog is None:
            self.dialog = SRDialog(self.iface, self.iface.mainWindow())
        self.dialog.show()
        self.dialog.raise_()
        self.dialog.activateWindow()
