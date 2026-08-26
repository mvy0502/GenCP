"""QgsTask wrapper around gencp_core.pipeline.

Inference MUST NOT run on the main thread. A modest extent is minutes of CPU; on the GUI
thread QGIS stops repainting, macOS shows the spinning wheel, and users force-quit the
application and lose their session. So the whole chain runs in a QgsTask.

This file contains no generation logic: it forwards to gencp_core.pipeline.generate and
translates its progress/cancel callbacks into QgsTask's.
"""
from __future__ import annotations
import traceback

from qgis.core import QgsTask, QgsMessageLog, Qgis

from .qtcompat import member

# Rough share of total wall-clock per stage, used only to make one progress bar out of
# three sequential stages. Inference dominates.
STAGE_WEIGHTS = {"render": 0.25, "infer": 0.65, "mosaic": 0.10}
STAGE_START = {"render": 0.0, "infer": 0.25, "mosaic": 0.90}


class GenerateTask(QgsTask):
    """Runs the generation chain off the main thread."""

    def __init__(self, description, params):
        super().__init__(description, member(QgsTask, 'CanCancel'))
        self.params = dict(params)
        self.result = None
        self.exception = None
        self.message = ""

    def run(self):
        """Executed on a worker thread. No Qt widget may be touched from here."""
        try:
            from gencp_core import pipeline

            def progress(stage, done, total):
                if total:
                    frac = STAGE_START.get(stage, 0.0) + \
                        STAGE_WEIGHTS.get(stage, 0.0) * (done / total)
                    self.setProgress(min(99.0, 100.0 * frac))
                self.message = f"{stage}: {done}/{total}"

            self.result = pipeline.generate(
                progress=progress, cancelled=self.isCanceled, **self.params)
            if self.isCanceled():
                return False
            self.setProgress(100.0)
            return True
        except Exception as e:                       # noqa: BLE001 - reported to the UI
            if type(e).__name__ == "Cancelled":
                return False
            self.exception = e
            QgsMessageLog.logMessage(
                "GenCP generation failed:\n" + traceback.format_exc(),
                "GenCP", member(Qgis, 'Critical'))
            return False

    def cancel(self):
        QgsMessageLog.logMessage("GenCP generation cancelled by user", "GenCP", member(Qgis, 'Info'))
        super().cancel()
