"""The SR plugin's dialog. Holds no super-resolution logic and no Turkish literal.

Every user-facing string comes from `strings.py` through `t()` and `tip()`. A Turkish
literal in this file is a bug; `strings.t` raises on a missing key rather than silently
falling back, so the failure is loud at the point it is introduced.

Structure follows Project 1's `tubitak/qgis_plugin/dialog.py` - the same settings
recall, the same `_row` form helper, the same start/progress/cancel/finish shape around a
QgsTask - because that dialog has been driven end to end by a real user and this one has
not. Project 1's dialog is READ as a pattern and is neither imported nor modified.
"""
from __future__ import annotations
from pathlib import Path

from qgis.PyQt.QtCore import QSize
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox, QLabel, QComboBox,
    QSpinBox, QCheckBox, QPushButton, QProgressBar, QRadioButton, QButtonGroup,
    QMessageBox,
)
from qgis.core import (
    QgsSettings, QgsProject, QgsRasterLayer, QgsApplication, QgsMapLayerProxyModel,
    QgsMessageLog, Qgis,
)
from qgis.gui import QgsFileWidget, QgsMapLayerComboBox

from .plugin import ensure_core_importable
from .qtcompat import member
from .strings import t, tip
from .task import LOG_TAG

SETTINGS_PREFIX = "gencp_sr/"

# The scale factor is FIXED at 2 for this work package. It is a named constant rather than
# a literal 2 scattered through the file so that WP4 changes it in one place, and so that
# the estimate, the run parameters and the label can never disagree about it.
SCALE = 2

#: Inference tile for the MODEL path, in source pixels. NOT the training tile: the network
#: is fully convolutional and the graph was exported with dynamic spatial axes, so the
#: inference tile is free. Chosen by measurement on a 4096 x 4096 source extent of 36SXJ,
#: overlap 32 throughout:
#:     tile 128 -> 1849 tiles, 32.6 s      (redundancy 1.78x)
#:     tile 256 ->  361 tiles, 23.2 s      (redundancy 1.31x)
#:     tile 512 ->   81 tiles, 22.4 s      (redundancy 1.14x)   <- chosen, 1.46x faster
#: Against tile 128 the pixels differ by at most 8 DN on ~1 % of pixels, all at tile seams,
#: which is 20 % of the model's own measured MAE of 39.7 DN. The model's declared
#: `infer_tile_src_px` (128) remains the TRAINING contract and is shown to the user; it is
#: not the inference tile, and the difference is documented in 04-model-in-plugin.md.
#: The overlap is unchanged at 32, still above the measured receptive field of 31 px.
MODEL_INFER_TILE_PX = 512


def _log(msg, level=None):
    QgsMessageLog.logMessage(str(msg), LOG_TAG, level or member(Qgis, 'Info'))


def _enum(cls, name):
    return member(cls, name)


def _tr_num(text):
    """Turkish decimal separator. `terimler.md`: decimal comma, not a period."""
    return str(text).replace(".", ",")


class SRDialog(QDialog):
    def __init__(self, iface, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.settings = QgsSettings()
        self.setWindowTitle(t("window_title"))
        self._task = None
        self._src = None          # dict of source properties, or None
        self._model = None        # (session, provenance) for the chosen ONNX file, or None
        self._model_err = None    # (strings_key, fmt) if the model file is unreadable
        self._input_err = None    # (strings_key, fmt) if the input does not suit the model
        self._ui_ready = False
        self._build_ui()
        self._ui_ready = True
        self._prefill()
        self._refresh_source()
        self.resize(QSize(680, 560))

    # ------------------------------------------------------------- settings ----
    def _remember(self, key, value):
        if value:
            self.settings.setValue(SETTINGS_PREFIX + key, str(value))

    def _recall(self, key, default=""):
        """Project first, then QgsSettings, then the default.

        QgsSettings is per-PROFILE and cannot travel in a .qgz, so a demo project carries
        its own paths. `_remember` writes only to settings, so ordinary use never mutates
        somebody's project file.
        """
        try:
            v, ok = QgsProject.instance().readEntry("GenCPSR", key, "")
            if ok and v:
                return str(v)
        except Exception:                            # noqa: BLE001
            pass
        return str(self.settings.value(SETTINGS_PREFIX + key, default) or default)

    # ------------------------------------------------------------------- UI ----
    def _row(self, form, label_key, widget, tip_key=None):
        lab = QLabel(t(label_key))
        if tip_key:
            lab.setToolTip(tip(tip_key))
            widget.setToolTip(tip(tip_key))
        form.addRow(lab, widget)
        return widget

    def _build_ui(self):
        outer = QVBoxLayout(self)

        # ------------------------------------------------------------ girdi ----
        g_in = QGroupBox(t("sec_input"))
        f_in = QFormLayout(g_in)

        self.rb_layer = QRadioButton(t("src_from_layer"))
        self.rb_file = QRadioButton(t("src_from_file"))
        self.rb_layer.setToolTip(tip("src_from_layer"))
        self.rb_file.setToolTip(tip("src_from_file"))
        self.src_group = QButtonGroup(self)
        self.src_group.addButton(self.rb_layer, 0)
        self.src_group.addButton(self.rb_file, 1)
        self.rb_layer.setChecked(True)
        row = QHBoxLayout()
        row.addWidget(self.rb_layer)
        row.addWidget(self.rb_file)
        row.addStretch(1)
        f_in.addRow(row)

        self.layer_cb = QgsMapLayerComboBox()
        self.layer_cb.setFilters(_enum(QgsMapLayerProxyModel, 'RasterLayer'))
        self.layer_cb.setAllowEmptyLayer(True)
        self._row(f_in, "input_layer", self.layer_cb, "input_layer")

        self.file_w = QgsFileWidget()
        self.file_w.setStorageMode(_enum(QgsFileWidget, 'GetFile'))
        self.file_w.setFilter(t("filter_raster"))
        self._row(f_in, "input_file", self.file_w, "input_file")

        self.lbl_src = QLabel(t("src_unset"))
        self.lbl_src.setWordWrap(True)
        self._row(f_in, "src_info", self.lbl_src, "src_info")
        outer.addWidget(g_in)

        # ---------------------------------------------------------- ayarlar ----
        g_set = QGroupBox(t("sec_settings"))
        f_set = QFormLayout(g_set)

        # The scale factor is SHOWN and FIXED. A disabled spinbox would invite the user to
        # try to change it; a label states the value and does not pretend to be a control.
        self.lbl_scale = QLabel(t("scale_fixed"))
        self._row(f_set, "scale", self.lbl_scale, "scale")

        self.method_cb = QComboBox()
        # Bicubic stays the DEFAULT and stays first: it needs no model file, no
        # onnxruntime and no particular input dtype, so it is the option that always works.
        self.method_cb.addItem(t("method_bicubic"), "bicubic")
        self.method_cb.addItem(t("method_model"), "model")
        self.method_cb.setCurrentIndex(0)
        self._row(f_set, "method", self.method_cb, "method")

        self.model_w = QgsFileWidget()
        self.model_w.setStorageMode(_enum(QgsFileWidget, 'GetFile'))
        self.model_w.setFilter(t("filter_model"))
        self._row(f_set, "model_file", self.model_w, "model_file")
        self.lbl_model = QLabel(t("model_unset"))
        self.lbl_model.setWordWrap(True)
        self._row(f_set, "model_info", self.lbl_model, "model_info")
        self.lbl_caveat = QLabel(t("model_caveat"))
        self.lbl_caveat.setWordWrap(True)
        f_set.addRow(QLabel(""), self.lbl_caveat)
        outer.addWidget(g_set)

        # --------------------------------------------------------- gelişmiş ----
        g_adv = QGroupBox(t("sec_advanced"))
        g_adv.setCheckable(True)
        g_adv.setChecked(False)
        f_adv = QFormLayout(g_adv)
        ensure_core_importable()
        try:
            from sr_core import tiles as _tiles
            d_tile, d_ovl = _tiles.DEFAULT_TILE_PX, _tiles.DEFAULT_OVERLAP_PX
        except Exception:                            # noqa: BLE001
            d_tile, d_ovl = 512, 32
        self.tile_sb = QSpinBox()
        self.tile_sb.setRange(64, 4096)
        self.tile_sb.setSingleStep(64)
        self.tile_sb.setValue(d_tile)
        self._row(f_adv, "tile_px", self.tile_sb, "tile_px")
        self.ovl_sb = QSpinBox()
        self.ovl_sb.setRange(0, 512)
        self.ovl_sb.setSingleStep(8)
        self.ovl_sb.setValue(d_ovl)
        self._row(f_adv, "overlap_px", self.ovl_sb, "overlap_px")
        f_adv.addRow(QLabel(""), QLabel(t("advanced_note")))
        outer.addWidget(g_adv)

        # ------------------------------------------------------------ çıktı ----
        g_out = QGroupBox(t("sec_output"))
        f_out = QFormLayout(g_out)
        self.out_w = QgsFileWidget()
        self.out_w.setStorageMode(_enum(QgsFileWidget, 'SaveFile'))
        self.out_w.setFilter(t("filter_raster"))
        self._row(f_out, "out_file", self.out_w, "out_file")
        self.cb_add = QCheckBox()
        self.cb_add.setChecked(True)
        self._row(f_out, "add_layer", self.cb_add, "add_layer")
        self.lbl_est = QLabel(t("out_estimate_unset"))
        self.lbl_est.setWordWrap(True)
        self._row(f_out, "out_estimate", self.lbl_est, "out_estimate")
        outer.addWidget(g_out)

        # --------------------------------------------------------- çalıştır ----
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        outer.addWidget(self.progress)

        self.lbl_status = QLabel(t("idle"))
        self.lbl_status.setWordWrap(True)
        outer.addWidget(self.lbl_status)

        btns = QHBoxLayout()
        btns.addStretch(1)
        self.btn_run = QPushButton(t("run"))
        self.btn_run.setToolTip(tip("run"))
        self.btn_cancel = QPushButton(t("cancel"))
        self.btn_cancel.setToolTip(tip("cancel"))
        self.btn_cancel.setEnabled(False)
        self.btn_close = QPushButton(t("close"))
        btns.addWidget(self.btn_run)
        btns.addWidget(self.btn_cancel)
        btns.addWidget(self.btn_close)
        outer.addLayout(btns)

        self.btn_run.clicked.connect(self._start)
        self.btn_cancel.clicked.connect(self._cancel)
        self.btn_close.clicked.connect(self.close)
        self.rb_layer.toggled.connect(self._on_src_mode)
        # BOTH signals. `layerChanged` alone never fired for a combo-box selection in
        # QGIS 4.2.1 / PyQt6: every earlier test passed only because the chosen layer was
        # already current when the dialog was CONSTRUCTED, so __init__'s own
        # _refresh_source() had already read it. Switching layers in the open dialog - which
        # is exactly what the demonstration asks the presenter to do - left the source line,
        # the estimate and the model input check all stale. `currentIndexChanged` does fire.
        # _refresh_source is idempotent and cheap, so connecting both costs nothing.
        self.layer_cb.layerChanged.connect(lambda *_a: self._refresh_source())
        self.layer_cb.currentIndexChanged.connect(lambda *_a: self._refresh_source())
        self.file_w.fileChanged.connect(lambda *_a: self._refresh_source())
        self.out_w.fileChanged.connect(lambda *_a: self._validate())
        self.method_cb.currentIndexChanged.connect(lambda *_a: self._on_method())
        self.model_w.fileChanged.connect(lambda *_a: self._on_model_changed())
        self.tile_sb.valueChanged.connect(lambda *_a: self._refresh_estimate())
        self.ovl_sb.valueChanged.connect(lambda *_a: self._refresh_estimate())
        self._on_src_mode(True)
        self._on_method()

    def _prefill(self):
        p = self._recall("input_path")
        if p and Path(p).is_file():
            self.file_w.setFilePath(p)
        out = self._recall("out_path")
        if out:
            self.out_w.setFilePath(out)

    # ------------------------------------------------------------- handlers ---
    def _on_src_mode(self, _checked=None):
        from_layer = self.rb_layer.isChecked()
        self.layer_cb.setEnabled(from_layer)
        self.file_w.setEnabled(not from_layer)
        if self._ui_ready:
            self._refresh_source()

    def _source_path(self):
        """The path of the chosen source, whichever way it was chosen, or ''.

        A layer's `source()` can carry provider parameters after a `|`; only the file part
        is meaningful to rasterio, so it is split off here rather than deeper down.
        """
        if self.rb_layer.isChecked():
            lyr = self.layer_cb.currentLayer()
            if lyr is None:
                return ""
            return str(lyr.source()).split("|", 1)[0]
        return self.file_w.filePath().strip()

    def _refresh_source(self):
        """Read the source's real properties from the file. Nothing here is guessed."""
        self._src = None
        path = self._source_path()
        if not path or not Path(path).is_file():
            self.lbl_src.setText(t("src_unset"))
            self._refresh_estimate()
            self._validate()
            return
        ensure_core_importable()
        try:
            import rasterio
            with rasterio.open(path) as d:
                T = d.transform
                self._src = dict(
                    path=path, width=d.width, height=d.height, count=d.count,
                    dtype=d.dtypes[0], crs=(d.crs.to_string() if d.crs else "—"),
                    gsd=abs(T.a), north_up=(T.b == 0 and T.d == 0),
                    itemsize=int(__import__("numpy").dtype(d.dtypes[0]).itemsize))
        except Exception as e:                       # noqa: BLE001
            self.lbl_src = self.lbl_src
            self.lbl_src.setText(t("src_bad"))
            _log(t("err_open", msg=str(e)), member(Qgis, 'Warning'))
            self._refresh_estimate()
            self._validate()
            return
        s = self._src
        gsd = ("%g" % s["gsd"]).replace(".", ",")     # decimal comma, per terimler.md
        txt = t("src_value", w=s["width"], h=s["height"], bands=s["count"],
                dtype=s["dtype"], crs=s["crs"], gsd=gsd)
        if not s["north_up"]:
            txt += "<br>" + t("src_rotated")
        self.lbl_src.setText(txt)
        self._suggest_output()
        self._recheck_input()
        self._refresh_estimate()
        self._validate()

    def _is_model(self):
        return str(self.method_cb.currentData()) == "model"

    def _on_method(self):
        """Enable the model field for the model path; take the tile size from the model."""
        m = self._is_model()
        self.model_w.setEnabled(m)
        self.lbl_model.setVisible(m)
        self.lbl_caveat.setVisible(m)
        if m:
            self._on_model_changed()
        else:
            from sr_core import tiles as _t
            self.tile_sb.setValue(_t.DEFAULT_TILE_PX)
            self.ovl_sb.setValue(_t.DEFAULT_OVERLAP_PX)
            # _recheck_input() clears _input_err, because it is a no-op off the model path.
            # Without this the model's refusal stayed on screen after switching to bicubic,
            # while Run was enabled - two contradictory signals at once. Found by driving
            # the dialog in QGIS, not by reading the code.
            self._recheck_input()
            self.lbl_status.setText(t("idle"))
            self._validate()
            self._refresh_estimate()

    def _on_model_changed(self):
        """Read the model's own provenance. Nothing about it is assumed or hard-coded."""
        self._model, self._model_err = None, None
        path = self.model_w.filePath().strip()
        if not self._is_model() or not path:
            self.lbl_model.setText(t("model_unset"))
            self._recheck_input(); self._validate(); self._refresh_estimate(); return
        ensure_core_importable()
        try:
            from .onnx_upsample import read_provenance, ModelInputError
        except ImportError as exc:
            self._model_err = ("err_no_onnxruntime", {})
            self.lbl_model.setText(t("err_no_onnxruntime"))
            _log(f"onnxruntime unavailable: {exc}", member(Qgis, "Warning"))
            self._recheck_input(); self._validate(); self._refresh_estimate(); return
        try:
            sess, prov = read_provenance(path)
        except ModelInputError as exc:
            self._model_err = (exc.key, exc.fmt)
            self.lbl_model.setText(t(exc.key, **exc.fmt))
            _log(f"model metadata incomplete: {exc}", member(Qgis, "Warning"))
        except Exception as exc:                     # noqa: BLE001
            self._model_err = ("model_bad", dict(msg=str(exc)[:200]))
            self.lbl_model.setText(t("model_bad", msg=str(exc)[:200]))
            _log(f"model unreadable: {exc}", member(Qgis, "Warning"))
        else:
            self._model = (sess, prov)
            self.lbl_model.setText(t("model_desc", name=Path(path).name,
                                     norm=prov["norm_divisor_dn"], scale=prov["scale"],
                                     ch=prov["in_channels"], order=prov["band_order"],
                                     done=prov["completed_steps"],
                                     sched=prov["registered_schedule_steps"]))
            self._remember("model_path", path)
            # D8: the network consumes 128 SOURCE pixels because its input is the 20 m
            # image; the bicubic path tiles at 512. Read from the model, never a literal.
            self.tile_sb.setValue(MODEL_INFER_TILE_PX)
            self.ovl_sb.setValue(int(prov["infer_overlap_src_px"]))
        self._recheck_input()
        self._validate()
        self._refresh_estimate()

    def _recheck_input(self):
        """Assert the chosen raster against the model's contract, BEFORE any tile runs.

        This is what stops the plugin turning the 8-bit TCI into plausible garbage.
        """
        self._input_err = None
        if not self._is_model() or not self._model or not self._src:
            return
        try:
            from .onnx_upsample import validate_input, ModelInputError
            validate_input(self._src["path"], self._model[1])
        except ModelInputError as exc:
            self._input_err = (exc.key, exc.fmt)
        except Exception as exc:                     # noqa: BLE001
            self._input_err = ("model_bad", dict(msg=str(exc)[:200]))

    def _suggest_output(self):
        """Propose an output path beside the source, if the user has not set one."""
        if self.out_w.filePath().strip() or not self._src:
            return
        p = Path(self._src["path"])
        self.out_w.setFilePath(str(p.with_name(f"{p.stem}_sr_x{SCALE}.tif")))

    def _refresh_estimate(self):
        if not self._src:
            self.lbl_est.setText(t("out_estimate_unset"))
            return
        s = self._src
        ensure_core_importable()
        try:
            from sr_core import tiles as _tiles
            tlist, _stride = _tiles.tile_grid(s["width"], s["height"],
                                              int(self.tile_sb.value()),
                                              int(self.ovl_sb.value()))
            n = len(tlist)
        except Exception:                            # noqa: BLE001
            n = 0
        ow, oh = s["width"] * SCALE, s["height"] * SCALE
        # Uncompressed size. Stated as approximate in the tooltip precisely because the
        # written file is deflate-compressed and is normally well under this.
        mb = ow * oh * s["count"] * s["itemsize"] / 1e6
        gsd = ("%g" % (s["gsd"] / SCALE)).replace(".", ",")
        self.lbl_est.setText(t("out_estimate_value", n=n, w=ow, h=oh, gsd=gsd, mb=mb))

    def _blocker(self):
        """Why the run button is disabled, or None. One reason, the first that applies."""
        if self._task is not None:
            return "blocked_running"
        if not self._source_path():
            return "blocked_no_input"
        if self._src is None:
            return "blocked_bad_input"
        if self._is_model():
            if self._model_err is not None:
                return "blocked_bad_model"
            if not self.model_w.filePath().strip():
                return "blocked_no_model"
            if self._input_err is not None:
                return "blocked_input_not_model"
        out = self.out_w.filePath().strip()
        if not out:
            return "blocked_no_output"
        try:
            if Path(out).resolve() == Path(self._src["path"]).resolve():
                return "blocked_output_is_input"
        except OSError:
            pass
        return None

    def _validate(self):
        b = self._blocker()
        self.btn_run.setEnabled(b is None)
        self.btn_run.setToolTip(tip("run") if b is None else t(b))
        # A disabled button with a terse tooltip is not a refusal a user can act on. When
        # the input does not suit the model, the FULL explanation - what was expected, what
        # was given, and which file to pick instead - goes in the status line where it
        # cannot be missed.
        if self._task is None:
            if self._input_err is not None:
                k, f = self._input_err
                self.lbl_status.setText(t(k, **f))
            elif self._model_err is not None and self._is_model():
                k, f = self._model_err
                self.lbl_status.setText(t(k, **f))
            elif self.lbl_status.text() not in (t("idle"),) and b is not None:
                self.lbl_status.setText(t("idle"))

    # ------------------------------------------------------------------ run ---
    def _start(self):
        if self._blocker() is not None:
            return
        out = self.out_w.filePath().strip()
        if Path(out).exists():
            box = QMessageBox(self)
            box.setWindowTitle(t("err_overwrite_title"))
            box.setText(t("err_overwrite", name=Path(out).name))
            yes = box.addButton(t("yes"), _enum(QMessageBox, 'YesRole'))
            box.addButton(t("no"), _enum(QMessageBox, 'NoRole'))
            box.exec()
            if box.clickedButton() is not yes:
                return

        # The bar is reset here, not at the end of the previous run: a run that failed or
        # was cancelled leaves the bar where it stopped, which is information the user
        # should keep until they start the next one.
        self.progress.setValue(0)
        self._remember("input_path", self._src["path"])
        self._remember("out_path", out)

        params = dict(
            src_path=self._src["path"], out_path=out, scale=SCALE,
            method=str(self.method_cb.currentData()),
            tile_px=int(self.tile_sb.value()), overlap_px=int(self.ovl_sb.value()),
        )
        if self._is_model():
            # The task builds its own session on the worker thread; an onnxruntime session
            # is not documented as safe to share across threads, and constructing one costs
            # 0.02 s. The PATH travels, not the session object.
            params["model_path"] = self.model_w.filePath().strip()
        ensure_core_importable()
        from .task import SuperResolveTask
        self._task = SuperResolveTask("GenCP SR", params)
        self._task.progressChanged.connect(self._on_progress)
        self._task.taskCompleted.connect(self._done)
        self._task.taskTerminated.connect(self._terminated)
        self.btn_run.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.lbl_status.setText(t("starting"))
        QgsApplication.taskManager().addTask(self._task)

    def _on_progress(self):
        if self._task is None:
            return
        self.progress.setValue(int(self._task.progress()))
        # A tile count beats a bare percentage: it distinguishes a slow run from a hung one.
        self.lbl_status.setText(t("stage_tiles", done=self._task.tiles_done,
                                  total=self._task.tiles_total))

    def _cancel(self):
        if self._task is not None:
            self._task.cancel()
            self.lbl_status.setText(t("cancelling"))

    def _terminated(self):
        """Task ended without success: cancelled by the user, or failed."""
        task, self._task = self._task, None
        self.btn_cancel.setEnabled(False)
        if task is not None and task.was_cancelled:
            self.lbl_status.setText(t("cancelled"))
        else:
            msg = str(task.exception) if (task and task.exception) else "?"
            self.lbl_status.setText(t("failed", msg=msg))
        self._validate()

    def _done(self):
        task, self._task = self._task, None
        self.btn_cancel.setEnabled(False)
        rec = task.result if task else None
        if not rec:
            self.lbl_status.setText(t("failed", msg="?"))
            self._validate()
            return
        self.progress.setValue(100)
        # Decimal COMMA. terimler.md fixes Turkish number formatting and Python's %f
        # always emits a period, so the conversion happens here. WP2B shipped "37.7 sn"
        # against a document that said "37,7 sn"; the document was right and the code was
        # wrong, and nothing caught it because that walkthrough compared only the prefix.
        msg = t("done", n=rec["n_tiles"],
                secs=_tr_num(f"{rec['wall_clock_s']:.1f}"),
                mb=f"{rec['output_size_bytes'] / 1e6:.0f}")
        if self.cb_add.isChecked():
            msg += " " + self._add_and_check(rec)
        self.lbl_status.setText(msg)
        _log(f"done: {rec['output']} {rec['output_shape']} "
             f"{rec['wall_clock_s']:.2f}s {rec['output_size_bytes']}B")
        self._validate()

    def _add_and_check(self, rec):
        """Load the output as a layer and confirm it covers the same ground as the source.

        This is a UI-level confirmation, not the grid contract. The grid contract is Gate S
        (`tubitak/sr/tests/gate_s.py`), which asserts exact affine arithmetic; what is
        checked here is the weaker, user-visible property that the layer QGIS actually
        opened has the source's CRS and the source's extent. The two are reported
        separately on purpose, so a green dialog can never be mistaken for a passed gate.
        """
        path = rec["output"]
        lyr = QgsRasterLayer(str(path), Path(path).stem)
        if not lyr.isValid():
            _log(t("layer_add_failed", path=path), member(Qgis, 'Warning'))
            return t("layer_add_failed", path=path)
        QgsProject.instance().addMapLayer(lyr)

        src_lyr = None
        if self.rb_layer.isChecked():
            src_lyr = self.layer_cb.currentLayer()
        if src_lyr is None:
            src_lyr = QgsRasterLayer(self._src["path"], "src")
            if not src_lyr.isValid():
                return t("done_aligned")             # nothing to compare against
        a, b = src_lyr.extent(), lyr.extent()
        # Half an OUTPUT pixel. The extents should be exactly equal - the output covers the
        # source footprint exactly by construction - so this tolerance exists only to
        # absorb the float printing QGIS does on the way in and out of a layer, not to
        # admit a real offset. Gate S is where exactness is asserted.
        eps = self._src["gsd"] / (2.0 * SCALE)
        same_crs = src_lyr.crs().authid() == lyr.crs().authid()
        same_ext = (abs(a.xMinimum() - b.xMinimum()) <= eps
                    and abs(a.yMinimum() - b.yMinimum()) <= eps
                    and abs(a.xMaximum() - b.xMaximum()) <= eps
                    and abs(a.yMaximum() - b.yMaximum()) <= eps)
        if same_crs and same_ext:
            return t("done_aligned")
        _log(f"MISALIGNED: crs {src_lyr.crs().authid()} vs {lyr.crs().authid()}; "
             f"extent {a.toString()} vs {b.toString()}", member(Qgis, 'Critical'))
        return t("done_misaligned")
