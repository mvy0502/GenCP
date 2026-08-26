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
# Measured, not guessed: on a cold cache a tile costs roughly 5 s to rasterise, 0.3 s to
# infer and 0.3 s for 16 confidence draws. The old weights put inference at 65%, which made
# the bar sit at 25% for most of the run and then leap. These reflect the real shape.
STAGE_WEIGHTS = {"render": 0.80, "infer": 0.06, "confidence": 0.06, "mosaic": 0.08}
STAGE_START = {"render": 0.0, "infer": 0.80, "confidence": 0.86, "mosaic": 0.92}


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
