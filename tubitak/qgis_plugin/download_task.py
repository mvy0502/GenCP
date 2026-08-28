"""QgsTask wrapper around gencp_core.geofabrik.download.

Separate from GenerateTask because it fails differently and is cancelled differently. A
download that stops halfway must leave nothing behind; a generation that stops halfway
leaves a usable tile cache.
"""
from __future__ import annotations
import traceback

from qgis.core import QgsTask, QgsMessageLog, Qgis

from .qtcompat import member


class DownloadTask(QgsTask):
    """Fetch the country extract off the main thread, verified before it is put in place."""

    def __init__(self, description, dest, region="turkey"):
        super().__init__(description, member(QgsTask, 'CanCancel'))
        self.dest = str(dest)
        self.region = region
        self.result = None
        self.exception = None
        self.total = None
        self.done = 0

    def run(self):
        try:
            from gencp_core import geofabrik as gf

            def progress(done, total):
                self.done, self.total = done, total
                if total:
                    self.setProgress(min(99.0, 100.0 * done / total))

            self.result = gf.download(self.dest, self.region,
                                      progress=progress, cancel=self.isCanceled)
            if self.result is None:                 # cancelled
                return False
            self.setProgress(100.0)
            return True
        except Exception as e:                      # noqa: BLE001 - reported to the UI
            self.exception = e
            QgsMessageLog.logMessage(
                "GenCP download failed:\n" + traceback.format_exc(),
                "GenCP", member(Qgis, 'Critical'))
            return False
