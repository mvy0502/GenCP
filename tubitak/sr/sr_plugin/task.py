"""QgsTask wrapper around `sr_core.run.superresolve`.

The work MUST NOT run on the main thread. A full 10980 x 10980 granule is roughly half a
minute of solid CPU; on the GUI thread QGIS stops repainting, macOS shows the spinning
wheel, and users force-quit the application and lose their session. So the whole chain
runs on a QgsTask.

This file contains no super-resolution logic. It forwards to `sr_core.run.superresolve`
and translates its per-tile progress callback into QgsTask's progress and cancellation.

Three traps from Project 1 are paid for here rather than rediscovered:

* **No `pyproj` on this thread.** `pyproj` on a QgsTask worker segfaults QGIS 4.2.1 if and
  only if the main thread built a CRS first. `sr_core` reads CRS through rasterio's own
  PROJ binding and never imports `pyproj`; this module does not import it either, and
  `_pyproj_state()` records what was actually loaded so the claim is observed rather than
  asserted.
* **No `multiprocessing`.** `spawn` re-executes `sys.executable`, which inside QGIS is the
  QGIS application binary, so a pool would launch N copies of QGIS. The work is serial.
* **No `onnxruntime`.** The bicubic path must not import it, so that the plugin loads and
  completes a job on a machine where `onnxruntime` cannot be imported at all - which on
  macOS is the ordinary case inside QGIS's bundled Python, a code-signing split. There is
  no import of it anywhere in this plugin or in `sr_core`.
"""
from __future__ import annotations
import sys
import traceback

from qgis.core import QgsTask, QgsMessageLog, Qgis

from .qtcompat import member

LOG_TAG = "GenCP SR"


class SRCancelled(Exception):
    """Raised out of the progress callback to unwind a cancelled run.

    Cancellation is implemented as an exception rather than as a `return False` because
    `sr_core.run.superresolve` takes a progress callback whose return value it ignores -
    a deliberately narrow interface, and one this plugin must not widen, because another
    session is importing that module right now.

    Unwinding through an exception is not a workaround; it is the path that gives the
    required on-disk guarantee. `superresolve` writes inside
    `sr_core.mosaic.atomic_path`, whose `except BaseException` arm unlinks the temporary
    file and leaves the destination exactly as it was. So a cancelled run leaves neither a
    truncated `.tif` at the output path nor a stray `.part` beside it. Returning a flag
    instead would have required `superresolve` to decide what to do with a half-built
    file, which is a decision `atomic_path` already makes correctly.
    """


def _pyproj_state():
    """Whether `pyproj` is loaded in this process - recorded, never used.

    Loaded-in-the-process is not the same as used-on-this-thread; QGIS itself may import
    it at startup. What matters is that nothing on this code path CALLS it, and this note
    exists so the distinction is visible in the log rather than argued about later.
    """
    return "loaded" if "pyproj" in sys.modules else "not loaded"


class SuperResolveTask(QgsTask):
    """Runs `sr_core.run.superresolve` off the main thread."""

    def __init__(self, description, params):
        super().__init__(description, member(QgsTask, 'CanCancel'))
        self.params = dict(params)
        self.result = None
        self.exception = None
        self.was_cancelled = False
        self.tiles_done = 0
        self.tiles_total = 0

    def run(self):
        """Executed on a worker thread. No Qt widget may be touched from here."""
        try:
            from sr_core.run import superresolve

            QgsMessageLog.logMessage(
                f"worker start: pyproj {_pyproj_state()}, "
                f"onnxruntime {'loaded' if 'onnxruntime' in sys.modules else 'not loaded'}",
                LOG_TAG, member(Qgis, 'Info'))

            def progress(k, n):
                # Cancellation is honoured BETWEEN tiles: the check happens after tile k
                # has been fully blended and before tile k+1 is read. A tile is never
                # abandoned half-written into the accumulator.
                self.tiles_done, self.tiles_total = k, n
                if self.isCanceled():
                    raise SRCancelled(f"cancelled after tile {k} of {n}")
                if n:
                    self.setProgress(min(99.0, 100.0 * k / n))

            self.result = superresolve(progress=progress, **self.params)
            if self.isCanceled():
                self.was_cancelled = True
                return False
            self.setProgress(100.0)
            return True
        except SRCancelled as e:
            self.was_cancelled = True
            QgsMessageLog.logMessage(f"cancelled by user: {e}", LOG_TAG,
                                     member(Qgis, 'Info'))
            return False
        except Exception as e:                       # noqa: BLE001 - reported to the UI
            self.exception = e
            QgsMessageLog.logMessage(
                "super-resolution failed:\n" + traceback.format_exc(),
                LOG_TAG, member(Qgis, 'Critical'))
            return False

    def cancel(self):
        QgsMessageLog.logMessage(
            f"cancel requested at tile {self.tiles_done}/{self.tiles_total}",
            LOG_TAG, member(Qgis, 'Info'))
        super().cancel()
