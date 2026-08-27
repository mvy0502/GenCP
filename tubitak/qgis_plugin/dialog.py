"""The GenCP dialog. Shell only — it calls gencp_core and contains no generation logic.

Structured after Deepness (PUTvision/qgis-plugin-deepness), the closest comparator: a QGIS
plugin that runs ONNX models on rasters, published in SoftwareX. Its UI documentation states
the convention this file follows — "Almost every element in UI has its own 'tooltip', that
is a short help message displayed after hovering this element" — and its dialog is
label:value parameter rows with no explanatory prose, model parameters in their own section,
and one Run button.

So: no paragraphs. Every explanation is a tooltip from `strings.TIP`; the long form lives in
QUICKSTART.md. QGIS's own widgets are used rather than hand-rolled equivalents —
`QgsFileWidget`, `QgsProjectionSelectionWidget`, `QgsCollapsibleGroupBox`, `QgsMessageBar`,
`QgsMapLayerComboBox`.

    Girdi        reference layer; extent, CRS and tile count read back from it
    Model        weights file; one line saying whether the bands were calibrated on it
    Önizleme     OFF by default: one button that renders the tile on demand
    Çıktı        output file, output CRS, add-to-map
    Gelişmiş     COLLAPSED: data source, CLC+, tile overlap, confidence and layer options
    Çalıştırma   pinned below the scroll area, so Generate is visible at any window size

**The preview no longer gates generation**, and there is no confirmation checkbox. What it
guarded is covered elsewhere: the source checks refuse to run on a missing or unreadable
input, and the confidence layer quantifies thin input per pixel. (Gate R is a developer
test over three fixed tiles against stored originals - it protects the rasteriser from
regressing between releases, not the pixels of any particular run.) The preview stays as an
on-demand look, off by default.

**Two things stay visible** because they are safety properties, and a tooltip nobody hovers
is not a safeguard:

  1. The run's confidence verdict, one sentence, after a run - it says which parts of the
     raster should not be used.
  2. The warning when the loaded model is not the one the confidence bands were calibrated
     for. Without it, bands drawn for another arm read as if they had been measured.

Every numeric or geometric decision is delegated: extents and tile grids to
gencp_core.extent, rendering to gencp_core.rasterize, generation to gencp_core.pipeline,
the confidence score to gencp_core.confidence.
"""
from __future__ import annotations
import os
from pathlib import Path

from qgis.PyQt.QtCore import Qt, QSize
from qgis.PyQt.QtGui import QImage, QPixmap, QFont
from qgis.PyQt.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFormLayout, QGroupBox,
    QHBoxLayout, QLabel, QMessageBox, QProgressBar, QPushButton, QRadioButton,
    QScrollArea, QSpinBox, QVBoxLayout, QWidget,
)
from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtGui import QValidator
from qgis.core import (
    Qgis, QgsApplication, QgsCoordinateReferenceSystem, QgsMapLayerProxyModel,
    QgsMessageLog, QgsProject, QgsRasterLayer, QgsSettings,
)
from qgis.gui import (
    QgsCollapsibleGroupBox, QgsFileWidget, QgsMapLayerComboBox, QgsMessageBar,
    QgsProjectionSelectionWidget,
)

from .plugin import ensure_core_importable
from .qtcompat import member
from .strings import t, tip

ensure_core_importable()

TILE_PREVIEW_PX = 320
SETTINGS_PREFIX = "GenCP/"


def _log(msg, level=member(Qgis, 'Info')):
    QgsMessageLog.logMessage(str(msg), "GenCP", level)


def _enum(cls, name):
    """Nested-scoped enum member where Qt6 has one, flat where Qt5 does."""
    return getattr(getattr(cls, "StorageMode", cls), name, None) or getattr(cls, name)


#: The only overlap we have characterised. 640 m was measured, not chosen: it is where the
#: seam energy ratio sits at 1.008 across the reference set. Every other value the spin box
#: now accepts is legal and untested, which the tooltip says.
DEFAULT_OVERLAP_M = 640

class OverlapSpinBox(QSpinBox):
    """Tile overlap in metres, constrained to whole pixels of the output grid.

    Two constraints, both ENFORCED here rather than written down and hoped for:

    * **A whole multiple of the grid spacing.** An overlap of, say, 645 m steps the tile
      origin by a non-integer number of pixels. Every tile after the first then lands on a
      fractional pixel, the mosaic carries a sub-pixel shear, and the Gate G transform
      contract stops describing the file - silently, because the output still opens and
      still looks right. Qt's own validation is the enforcement point: a non-multiple never
      becomes this widget's value in the first place.
    * **Strictly smaller than one tile.** At or above ``TILE_M`` the stride is zero or
      negative and tiling does not terminate. ``extent.tile_grid`` already raises for this;
      the widget refuses earlier, where the user can see why.

    Both limits are read from ``gencp_core.extent`` rather than restated. The tile is
    2570 m, not 2560: the upstream chips are 257 px, which is the whole reason the
    Option-A GSD correction exists. A literal here would drift from the pipeline the first
    time that constant moved.
    """

    #: emitted with a ready-to-show sentence when the user's input was refused or snapped
    constraintViolated = pyqtSignal(str)

    def __init__(self, step_m, limit_m, parent=None):
        super().__init__(parent)
        self._step_m = int(step_m)
        self._limit_m = float(limit_m)
        # Largest whole multiple of the grid strictly below one tile.
        self._max_m = int((self._limit_m - 1e-9) // self._step_m) * self._step_m
        self.setRange(0, self._max_m)
        self.setSingleStep(self._step_m)
        self.setSuffix(t("overlap_suffix"))
        self.setAccelerated(True)

    def maximum_legal(self):
        return self._max_m

    def validate(self, text, pos):
        state, text, pos = super().validate(text, pos)
        stripped = text.replace(self.suffix(), "").strip()
        if not stripped:
            return state, text, pos
        try:
            v = int(stripped)
        except ValueError:
            return state, text, pos
        if v > self._max_m:
            self.constraintViolated.emit(
                t("overlap_too_large", m=v, limit=self._limit_m, max=self._max_m))
            return QValidator.State.Invalid, text, pos
        if state == QValidator.State.Acceptable and v % self._step_m:
            # Intermediate, not Invalid: the user may still be typing "64" on the way to
            # "640". It cannot be committed, which is what matters.
            return QValidator.State.Intermediate, text, pos
        return state, text, pos

    def fixup(self, text):
        """Called when focus leaves on a value Qt would not accept. Snap, and SAY SO."""
        stripped = text.replace(self.suffix(), "").strip()
        try:
            v = int(stripped)
        except ValueError:
            return text
        snapped = min(max(int(round(v / self._step_m)) * self._step_m, 0), self._max_m)
        if snapped != v:
            self.constraintViolated.emit(
                t("overlap_snapped", typed=v, m=snapped, step=self._step_m))
        return f"{snapped}{self.suffix()}"


class GenCPDialog(QDialog):
    def __init__(self, iface, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.settings = QgsSettings()
        self.setWindowTitle(t("window_title"))
        self.setMinimumSize(QSize(640, 420))
        self._extent = None
        self._crs = None
        self._preview_index = 0
        self._task = None
        self._extent_ok = False
        self._ui_ready = False
        self._build_ui()
        self._refresh_extent()
        self._connect_project_signals()
        self.resize(QSize(720, 700))

    # ------------------------------------------------------------- settings ----
    def _remember(self, key, value):
        if value:
            self.settings.setValue(SETTINGS_PREFIX + key, str(value))

    def _recall(self, key, default=""):
        """Project first, then QgsSettings, then the default.

        QgsSettings is per-PROFILE and cannot travel in a .qgz, so a demo or handover
        project carries its own paths. _remember writes only to settings, so ordinary use
        never mutates somebody's project file.
        """
        try:
            v, ok = QgsProject.instance().readEntry("GenCP", key, "")
            if ok and v:
                return str(v)
        except Exception:                            # noqa: BLE001
            pass
        return str(self.settings.value(SETTINGS_PREFIX + key, default) or default)

    # ------------------------------------------------------------------- UI ----
    def _file_widget(self, mode, filt, tip_key, on_change):
        w = QgsFileWidget()
        w.setStorageMode(_enum(QgsFileWidget, mode))
        w.setFilter(filt)
        w.setToolTip(tip(tip_key))
        w.fileChanged.connect(on_change)
        return w

    def _row(self, form, label_key, widget, tip_key=None):
        lab = QLabel(t(label_key))
        if tip_key:
            lab.setToolTip(tip(tip_key))
            widget.setToolTip(tip(tip_key))
        form.addRow(lab, widget)
        return widget

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(9, 9, 9, 9)
        outer.setSpacing(6)

        # Warnings go here - one line, dismissable, QGIS's own idiom - instead of the
        # coloured paragraph blocks this dialog used to grow.
        self.msgbar = QgsMessageBar()
        outer.addWidget(self.msgbar, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(getattr(getattr(QScrollArea, "Shape", QScrollArea), "NoFrame"))
        body = QWidget()
        lay = QVBoxLayout(body)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)
        scroll.setWidget(body)
        outer.addWidget(scroll, 1)

        def form_group(title_key):
            g = QGroupBox(t(title_key))
            f = QFormLayout(g)
            f.setLabelAlignment(member(Qt, 'AlignRight') | member(Qt, 'AlignVCenter'))
            f.setHorizontalSpacing(10)
            f.setVerticalSpacing(5)
            f.setContentsMargins(9, 6, 9, 6)
            lay.addWidget(g)
            return g, f

        # --- Girdi ---------------------------------------------------------
        _g1, f1 = form_group("sec_input")
        self.layer_box = QgsMapLayerComboBox()
        self.layer_box.setFilters(member(QgsMapLayerProxyModel, 'All'))
        self.layer_box.layerChanged.connect(self._refresh_extent)
        self._row(f1, "reference_layer", self.layer_box, "reference_layer")
        self.lbl_extent = QLabel(t("waiting"))
        self._row(f1, "extent", self.lbl_extent, "extent")
        self.lbl_crs = QLabel(t("waiting"))
        self._row(f1, "crs", self.lbl_crs, "crs")
        self.lbl_tiles = QLabel(t("waiting"))
        self._row(f1, "tiles_estimate", self.lbl_tiles, "tiles_estimate")

        # --- Model ---------------------------------------------------------
        _g2, f2 = form_group("sec_model")
        self.model_w = self._file_widget("GetFile", "ONNX (*.onnx)", "model_file",
                                         self._on_model_changed)
        self._row(f2, "model_file", self.model_w, "model_file")
        self.lbl_model = QLabel(t("model_none"))
        self.lbl_model.setWordWrap(True)
        f2.addRow("", self.lbl_model)
        # SAFETY PROPERTY 3 - stays visible. See the module docstring.
        self.lbl_model_calib = QLabel("")
        self.lbl_model_calib.setWordWrap(True)
        self.lbl_model_calib.setVisible(False)
        f2.addRow("", self.lbl_model_calib)

        # --- Önizleme (off by default) ------------------------------------
        # The preview no longer GATES generation and is no longer opened by default. What
        # it used to guard is covered elsewhere: the coverage checks refuse to run on
        # broken or non-covering inputs, and the confidence layer quantifies thin input.
        # (Gate R is a developer test over three fixed tiles against stored originals, not
        # a per-run check - it protects the rasteriser from regressing, not this run's
        # pixels.) What remains here is an on-demand look at what the model will see.
        g3 = QGroupBox(t("sec_preview"))
        f3 = QVBoxLayout(g3)
        f3.setContentsMargins(9, 6, 9, 6)
        f3.setSpacing(5)
        prow = QHBoxLayout()
        prow.setSpacing(6)
        self.btn_preview = QPushButton(t("preview_button"))
        self.btn_preview.setToolTip(tip("preview_button"))
        self.btn_preview.clicked.connect(self._render_preview)
        self.btn_prev = QPushButton(t("preview_prev"))
        self.btn_next = QPushButton(t("preview_next"))
        self.btn_prev.clicked.connect(lambda: self._step_preview(-1))
        self.btn_next.clicked.connect(lambda: self._step_preview(+1))
        self.btn_prev.setVisible(False)
        self.btn_next.setVisible(False)
        prow.addWidget(self.btn_preview)
        prow.addWidget(self.btn_prev)
        prow.addWidget(self.btn_next)
        prow.addStretch(1)
        self.lbl_osm = QLabel("")
        prow.addWidget(self.lbl_osm)
        f3.addLayout(prow)

        self.preview_label = QLabel("")
        self.preview_label.setAlignment(member(Qt, 'AlignCenter'))
        self.preview_label.setFixedHeight(TILE_PREVIEW_PX)
        self.preview_label.setMinimumWidth(TILE_PREVIEW_PX)
        self.preview_label.setToolTip(tip("preview_image"))
        self.preview_label.setStyleSheet("border:1px solid palette(mid);")
        self.preview_label.setVisible(False)
        f3.addWidget(self.preview_label)
        lay.addWidget(g3)

        # --- Çıktı ---------------------------------------------------------
        _g4, f4 = form_group("sec_output")
        self.out_w = self._file_widget("SaveFile", "GeoTIFF (*.tif)", "out_file",
                                       lambda _p: self._validate())
        self._row(f4, "out_file", self.out_w, "out_file")
        self.crs_w = QgsProjectionSelectionWidget()
        # Unset must read as a CHOICE, not as a fault. Left alone the widget shows
        # "invalid projection", which looks like something has gone wrong before the user
        # has touched anything. Unset here means "same as the reference layer", which is
        # both the default behaviour and the plain-language answer to request 2.2.
        try:
            self.crs_w.setOptionVisible(
                QgsProjectionSelectionWidget.CrsOption.CrsNotSet
                if hasattr(QgsProjectionSelectionWidget, "CrsOption")
                else QgsProjectionSelectionWidget.CrsNotSet, True)
            self.crs_w.setNotSetText(t("out_crs_same"))
        except Exception:                            # noqa: BLE001
            pass
        self.crs_w.crsChanged.connect(self._on_out_crs)
        self._row(f4, "out_crs", self.crs_w, "out_crs")
        self.lbl_out_crs = QLabel("")
        self.lbl_out_crs.setWordWrap(True)
        self.lbl_out_crs.setVisible(False)
        f4.addRow("", self.lbl_out_crs)
        self.cb_add_layer = QCheckBox(t("add_layers"))
        self.cb_add_layer.setChecked(True)
        self.cb_add_layer.setToolTip(tip("add_layers"))
        f4.addRow("", self.cb_add_layer)

        # --- Gelişmiş (collapsed) ------------------------------------------
        self.adv = QgsCollapsibleGroupBox(t("sec_advanced"))
        self.adv.setCollapsed(True)
        fa = QFormLayout(self.adv)
        fa.setLabelAlignment(member(Qt, 'AlignRight') | member(Qt, 'AlignVCenter'))
        fa.setHorizontalSpacing(10)
        fa.setVerticalSpacing(5)
        fa.setContentsMargins(9, 6, 9, 6)
        srow = QHBoxLayout()
        self.rb_online = QRadioButton(t("source_online"))
        self.rb_local = QRadioButton(t("source_local"))
        self.rb_local.setChecked(True)
        self.rb_online.toggled.connect(self._validate)
        srow.addWidget(self.rb_local)
        srow.addWidget(self.rb_online)
        srow.addStretch(1)
        sw = QWidget()
        sw.setLayout(srow)
        self._row(fa, "source", sw, "source")
        self.pbf_w = self._file_widget("GetFile", "OSM PBF (*.pbf *.osm.pbf)", "pbf_file",
                                       self._on_pbf_changed)
        self._row(fa, "pbf_file", self.pbf_w, "pbf_file")
        self.clc_w = self._file_widget("GetFile", "GeoTIFF (*.tif *.tiff)", "clc_file",
                                       self._on_clc_changed)
        self._row(fa, "clc_file", self.clc_w, "clc_file")
        from .plugin import ensure_core_importable as _eci
        _eci()
        from gencp_core import extent as _ext
        self.overlap_box = OverlapSpinBox(int(_ext.NOMINAL), _ext.TILE_M)
        self.overlap_box.setValue(DEFAULT_OVERLAP_M)
        self.overlap_box.valueChanged.connect(self._refresh_extent)
        self.overlap_box.constraintViolated.connect(self._on_overlap_refused)
        self._row(fa, "tile_overlap", self.overlap_box, "tile_overlap")
        self.cb_alpha = QCheckBox(t("confidence_alpha"))
        self.cb_alpha.setChecked(True)
        self.cb_alpha.setToolTip(tip("confidence_alpha"))
        fa.addRow("", self.cb_alpha)
        self.cb_band_layer = QCheckBox(t("confidence_band_layer"))
        self.cb_band_layer.setToolTip(tip("confidence_band_layer"))
        fa.addRow("", self.cb_band_layer)
        self.cb_osm_layer = QCheckBox(t("add_osm_layer"))
        self.cb_osm_layer.setChecked(True)
        self.cb_osm_layer.setToolTip(tip("add_osm_layer"))
        fa.addRow("", self.cb_osm_layer)
        lay.addWidget(self.adv)

        lay.addStretch(1)

        # --- Çalıştırma, pinned outside the scroll area ---------------------
        g6 = QGroupBox(t("sec_run"))
        f6 = QVBoxLayout(g6)
        f6.setContentsMargins(9, 6, 9, 6)
        f6.setSpacing(5)
        self.progress = QProgressBar()
        self.progress.setValue(0)
        f6.addWidget(self.progress)
        rrow = QHBoxLayout()
        rrow.setSpacing(6)
        self.btn_run = QPushButton(t("generate"))
        self.btn_run.setToolTip(tip("generate"))
        self.btn_run.clicked.connect(self._start)
        self.btn_run.setDefault(True)
        bf = QFont(self.btn_run.font())
        bf.setBold(True)
        self.btn_run.setFont(bf)
        self.btn_run.setMinimumHeight(30)
        self.btn_run.setMinimumWidth(120)
        self.btn_cancel = QPushButton(t("cancel"))
        self.btn_cancel.setToolTip(tip("cancel"))
        self.btn_cancel.clicked.connect(self._cancel)
        self.btn_cancel.setEnabled(False)
        self.lbl_status = QLabel(t("idle"))
        self.lbl_status.setWordWrap(True)
        rrow.addWidget(self.btn_run)
        rrow.addWidget(self.btn_cancel)
        rrow.addWidget(self.lbl_status, 1)
        f6.addLayout(rrow)
        # Run-level confidence verdict - one sentence, after a run. Kept: it is what tells
        # a user which parts of the raster they should not use.
        self.lbl_verdict = QLabel("")
        self.lbl_verdict.setWordWrap(True)
        self.lbl_verdict.setToolTip(tip("verdict"))
        self.lbl_verdict.setVisible(False)
        f6.addWidget(self.lbl_verdict)
        outer.addWidget(g6, 0)

        self.buttons = QDialogButtonBox(member(QDialogButtonBox, 'Close'))
        btn = self.buttons.button(member(QDialogButtonBox, 'Close'))
        if btn is not None:
            btn.setText(t("close"))
        self.buttons.rejected.connect(self.reject)
        outer.addWidget(self.buttons)

        # Prefills LAST: setting a widget's value emits its changed signal, which reaches
        # _validate, which reads widgets built above. Run mid-build this raised
        # AttributeError inside a Qt slot on every construction.
        self._ui_ready = True
        self._prefill()

    # -------------------------------------------------------------- prefill ---
    def _repo_root(self):
        for p in Path(__file__).resolve().parents:
            if (p / "tubitak").is_dir():
                return p
        return None

    def _prefill(self):
        root = self._repo_root()
        clc = self._recall("clc_path")
        if not clc and root:
            cand = root / ("tubitak/data/clcplus/"
                           "CLMS_CLCplus_RASTER_2021_010m_eu_03035_V1_1.tif")
            clc = str(cand) if cand.is_file() else ""
        if clc:
            self.clc_w.setFilePath(clc)
        pbf = self._recall("pbf_path")
        if pbf and Path(pbf).is_file():
            self.pbf_w.setFilePath(pbf)
        model = self._recall("model_path")
        if not model and root:
            d = root / "tubitak/data/plugin_models"
            for name in ("gencp_C2_fp32.onnx", "gencp_C3_fp32.onnx"):
                if (d / name).is_file():
                    model = str(d / name)
                    break
        if model:
            self.model_w.setFilePath(model)
        self._describe_model()
        out_dir = self._recall("out_dir")
        if out_dir and Path(out_dir).is_dir():
            self.out_w.setFilePath(str(Path(out_dir) / "gencp_reference.tif"))

    def _connect_project_signals(self):
        prj = QgsProject.instance()
        for sig in ("layersAdded", "layersRemoved"):
            try:
                getattr(prj, sig).connect(lambda *_a: self._refresh_extent())
            except Exception:                        # noqa: BLE001
                pass

    # ------------------------------------------------------------- handlers ---
    def _on_pbf_changed(self, p):
        # 2.3: set once, then remembered. It lives in the collapsed Advanced group so it
        # is never on the path of a routine run.
        self._remember("pbf_path", p)
        if p:
            self.rb_local.setChecked(True)
        self._validate()

    def _on_clc_changed(self, p):
        self._remember("clc_path", p)
        self._validate()

    def _on_model_changed(self, p):
        self._remember("model_path", p)
        self._describe_model()
        self._validate()

    def _on_out_crs(self, _crs):
        c = self.crs_w.crs()
        geo = c.isValid() and c.isGeographic()
        self.lbl_out_crs.setText(t("out_crs_geographic") if geo else "")
        self.lbl_out_crs.setVisible(bool(geo))

    def _describe_model(self):
        p = Path(self.model_w.filePath().strip() or "/nonexistent")
        if not p.is_file():
            self.lbl_model.setText(t("model_none"))
            self.lbl_model_calib.setVisible(False)
            return
        import datetime
        st = p.stat()
        self.lbl_model.setText(t(
            "model_desc", name=p.name, mb=st.st_size / 1e6,
            mtime=datetime.datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d")))
        from gencp_core import confidence as conf
        try:
            ok = conf.model_is_validated(p)
        except Exception:                            # noqa: BLE001
            ok = False
        if ok:
            self.lbl_model_calib.setText(t("model_calibrated_ok"))
            self.lbl_model_calib.setStyleSheet("")
        else:
            self.lbl_model_calib.setText(t(
                "model_not_calibrated",
                calib=conf.CALIBRATION["calibrated_model_file"]))
            self.lbl_model_calib.setStyleSheet("color:#b26a00;")
        self.lbl_model_calib.setVisible(True)

    def _on_overlap_refused(self, text):
        """The overlap widget refused or snapped a typed value. Never silent."""
        self._msg(text, member(Qgis, 'Warning'))

    def _msg(self, text, level=None):
        """One line in the message bar. Replaces the coloured paragraph blocks."""
        self.msgbar.clearWidgets()
        if text:
            self.msgbar.pushMessage("GenCP", text,
                                    level if level is not None else member(Qgis, 'Warning'),
                                    duration=0)

    # --------------------------------------------------------------- extent ---
    def _refresh_extent(self):
        layer = self.layer_box.currentLayer()
        if layer is None:
            for lbl in (self.lbl_extent, self.lbl_crs, self.lbl_tiles):
                lbl.setText(t("waiting"))
            self._extent = self._crs = None
            self._extent_ok = False
            self._invalidate_preview()
            self._validate()
            return
        r = layer.extent()
        crs = layer.crs()
        self._extent = (r.xMinimum(), r.yMinimum(), r.xMaximum(), r.yMaximum())
        authid = crs.authid() or ""
        # pyproj/rasterio cannot resolve a QGIS-local "USER:100001" authid; the WKT works.
        self._crs = crs.toWkt() if (not authid or authid.startswith("USER:")) else authid
        self.lbl_extent.setText(t("extent_value", xmin=r.xMinimum(), ymin=r.yMinimum(),
                                  xmax=r.xMaximum(), ymax=r.yMaximum(),
                                  w=r.width(), h=r.height()))
        self.lbl_crs.setText(crs.authid() or crs.description())
        try:
            from gencp_core import extent as ext
            e, work, _ = ext.resolve(self._extent, self._crs)
            est = ext.estimate(e, self.overlap_box.value())
            self.lbl_tiles.setText(t("tiles_value", n=est["n_tiles"], w=est["width"],
                                     h=est["height"], mins=est["seconds"] / 60.0))
            self._extent_ok = True
            self._msg("")
        except Exception as e:                       # noqa: BLE001 - shown to the user
            self.lbl_tiles.setText(t("unset"))
            self._extent_ok = False
            self._msg(str(e), member(Qgis, 'Critical'))
        self._invalidate_preview()
        self._validate()

    def _invalidate_preview(self):
        """Close the preview. It is off by default and returns to off when inputs change."""
        self._preview_index = 0
        self.btn_prev.setVisible(False)
        self.btn_next.setVisible(False)
        self.preview_label.setPixmap(QPixmap())
        self.preview_label.setVisible(False)
        if hasattr(self, "lbl_osm"):
            self.lbl_osm.setText("")

    # -------------------------------------------------------------- preview ---
    def _apply_clc_path(self):
        """Point gencp_core at the CLC+ raster before BOTH the preview and the run.

        Set only in _start() once, the preview rendered against gencp_core's default while
        the run used the user's file: two different base rasters under one checkbox saying
        the render is correct.
        """
        clc = self.clc_w.filePath().strip()
        if not clc:
            return
        os.environ["GENCP_CLC_PATH"] = clc
        try:
            from gencp_core import vectors
            vectors.CLC_PATH = Path(clc)
        except Exception:                            # noqa: BLE001
            pass

    def _render_preview(self):
        if self._extent is None:
            return
        ok, why = self._source_ok()
        if not ok:
            self._msg(why)
            self.adv.setCollapsed(False)
            return
        self.lbl_status.setText(t("preview_rendering"))
        self._apply_clc_path()
        QgsApplication.processEvents()
        try:
            import numpy as np
            from gencp_core import extent as ext, pipeline, confidence as conf
            e, work, _ = ext.resolve(self._extent, self._crs)
            tiles, _ = ext.tile_grid(e, self.overlap_box.value())
            tile = tiles[min(self._preview_index, len(tiles) - 1)]
            # The SAME cache directory pipeline.generate reads from, so the run consumes
            # the very file the user looked at rather than re-rendering and hoping.
            stats = {}
            paths = pipeline.render_inputs(
                [tile], work, pipeline.default_work_dir() / "render",
                pbf=self._pbf_or_none(), base_product="clcplus", stats_out=stats)
            img = pipeline.preview_image(list(paths.values())[0])
            self._show_preview(img, tile, len(tiles))

            rgb = np.asarray(img.convert("RGB"))
            idx, names = conf.class_map(rgb)
            b = conf.osm_class_breakdown(idx, names)
            self.lbl_osm.setText(t("osm_counts", roads=b["roads"],
                                   buildings=b["buildings"], water=b["water"],
                                   landuse=b["landuse"]))
            if b["total_osm_px"] == 0:
                self._msg(t("warn_zero_osm"))
            self._report_coverage(pipeline.coverage_warnings(stats, self._pbf_or_none()))
            self.btn_prev.setVisible(len(tiles) > 1)
            self.btn_next.setVisible(len(tiles) > 1)
            self.lbl_status.setText(t("idle"))
        except Exception as e:                       # noqa: BLE001 - shown to the user
            _log(f"preview failed: {e}", member(Qgis, 'Warning'))
            self.lbl_status.setText(t("preview_failed", err=e))
            QMessageBox.critical(self, t("preview_failed_title"), str(e))

    def _step_preview(self, d):
        self._preview_index = max(0, self._preview_index + d)
        self._render_preview()

    def _show_preview(self, img, tile, n_tiles):
        img = img.convert("RGB")
        w, h = img.size
        qimg = QImage(img.tobytes("raw", "RGB"), w, h, 3 * w,
                      member(QImage, 'Format_RGB888')).copy()
        self.preview_label.setPixmap(QPixmap.fromImage(qimg).scaled(
            TILE_PREVIEW_PX, TILE_PREVIEW_PX,
            member(Qt, 'KeepAspectRatio'), member(Qt, 'FastTransformation')))
        self.preview_label.setVisible(True)

    def _band_label(self, band):
        return {"red": t("band_red"), "amber": t("band_amber"),
                "green": t("band_green")}[band]

    def _report_coverage(self, items):
        """gencp_core returns structured facts; the Turkish rendering happens here."""
        for it in items or []:
            if it.get("kind") == "zero_osm":
                self._msg(t("warn_zero_osm_tiles", n=it["n"], total=it["total"],
                            source=it.get("source") or t("source_online")))
            elif it.get("kind") == "count_unavailable":
                self._msg(t("warn_count_unavailable", n=it["n"], total=it["total"]))

    # ----------------------------------------------------------- validation ---
    def _pbf_or_none(self):
        if self.rb_local.isChecked():
            return self.pbf_w.filePath().strip() or None
        return None

    def _source_ok(self):
        if self.rb_local.isChecked():
            p = self.pbf_w.filePath().strip()
            if not p:
                return False, t("err_pbf_empty")
            if not Path(p).is_file():
                return False, t("err_pbf_missing", path=p)
        clc = self.clc_w.filePath().strip()
        if not clc:
            return False, t("err_clc_empty")
        if not Path(clc).is_file():
            return False, t("err_clc_missing", path=clc)
        return True, ""

    def _confidence_on(self):
        """(produce, note). Never silently downgrades: bands measured on one model only."""
        if not (self.cb_alpha.isChecked() or self.cb_band_layer.isChecked()):
            return False, ""
        from gencp_core import confidence as conf
        m = self.model_w.filePath().strip()
        if not m or not Path(m).is_file():
            return False, ""
        if not conf.model_is_validated(m):
            return False, "uncalibrated"
        return True, ""

    def _validate(self):
        if not getattr(self, "_ui_ready", False):
            return
        ok_src, _why = self._source_ok()
        self.btn_preview.setEnabled(
            self._extent is not None and getattr(self, "_extent_ok", False) and ok_src)
        model_ok = Path(self.model_w.filePath().strip() or "/nonexistent").is_file()
        out_ok = bool(self.out_w.filePath().strip())
        # Nothing here gates on the preview having been opened. That was the point of
        # removing the confirmation checkbox, and leaving a hidden dependency behind would
        # have re-created it invisibly.
        can_run = bool(self._extent is not None and self._extent_ok and ok_src
                       and model_ok and out_ok and self._task is None)
        self.btn_run.setEnabled(can_run)
        if self._task is None:
            self.lbl_status.setText(
                t("idle") if can_run else self._blocker(ok_src, model_ok, out_ok))

    def _blocker(self, ok_src, model_ok, out_ok):
        """The one thing to do next, phrased as the fix."""
        if self._extent is None:
            return t("err_no_layer")
        if not self._extent_ok:
            return t("err_no_layer")
        if not ok_src:
            return self._source_ok()[1]
        if not model_ok:
            return t("err_model_missing")
        if not out_ok:
            return t("err_out_missing")
        return t("idle")

    # -------------------------------------------------------------------- run -
    def _start(self):
        from gencp_core import confidence as conf
        model = self.model_w.filePath().strip()
        conf_on, _ = self._confidence_on()
        out_crs = self.crs_w.crs()
        dst = out_crs.authid() if (out_crs.isValid() and out_crs.authid()) else None
        params = dict(
            extent_bbox=self._extent, crs=self._crs, model_path=model,
            out_tif=self.out_w.filePath().strip(),
            pbf=self._pbf_or_none(), base_product="clcplus",
            overlap_m=float(self.overlap_box.value()),
            dst_crs=dst,
            confidence=bool(conf_on),
            alpha_confidence=bool(conf_on and self.cb_alpha.isChecked()),
            band_layer=bool(conf_on and self.cb_band_layer.isChecked()),
            write_osm=bool(self.cb_osm_layer.isChecked()),
            stochastic_model=(str(conf.stochastic_model_for(model))
                              if (conf_on and conf.needs_stochastic()) else None),
        )
        self._apply_clc_path()
        for k, w in (("clc_path", self.clc_w), ("model_path", self.model_w)):
            self._remember(k, w.filePath().strip())
        if self._pbf_or_none():
            self._remember("pbf_path", self._pbf_or_none())
        if self.out_w.filePath().strip():
            self._remember("out_dir", str(Path(self.out_w.filePath().strip()).parent))

        from .task import GenerateTask
        self._task = GenerateTask("GenCP", params)
        self._task.progressChanged.connect(self._on_progress)
        self._task.taskCompleted.connect(self._done)
        self._task.taskTerminated.connect(self._failed)
        self.btn_run.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.lbl_status.setText(t("running"))
        QgsApplication.taskManager().addTask(self._task)

    def _on_progress(self):
        """A step name beats a percentage: it tells a slow step from a hung one."""
        if self._task is None:
            return
        self.progress.setValue(int(self._task.progress()))
        stage, _, counts = (self._task.message or "").partition(":")
        done, _, total = counts.strip().partition("/")
        key = {"render": "stage_render", "infer": "stage_infer",
               "confidence": "stage_confidence", "mosaic": "stage_mosaic"}.get(
                   stage.strip(), "stage_unknown")
        self.lbl_status.setText(t(key, done=done or "?", total=total or "?"))

    def _cancel(self):
        if self._task is not None:
            self._task.cancel()
            self.lbl_status.setText(t("cancelling"))

    def _add(self, path, style_bands=False, name=None):
        lyr = QgsRasterLayer(str(path), name or Path(path).stem)
        if not lyr.isValid():
            return None
        self._draw_rgb_opaque(lyr)
        if style_bands:
            try:
                self._style_bands(lyr)
            except Exception as e:                   # noqa: BLE001
                _log(f"confidence styling failed: {e}", member(Qgis, 'Warning'))
        QgsProject.instance().addMapLayer(lyr)
        return lyr

    def _draw_rgb_opaque(self, layer):
        """Draw bands 1-3 and IGNORE band 4, even though band 4 is a real alpha band.

        The alpha band carries CONFIDENCE for the downstream matcher, not opacity. GDAL and
        QGIS cannot know that: they see ColorInterp.alpha and composite with it, so the
        output was being drawn semi-transparently over whatever sat beneath it. Measured on
        the demo tile: alpha mean 108 of 255, never once fully opaque, 79% of pixels below
        half. Toggling the generated layer on and off therefore changed the picture far
        less than it should have, and a side-by-side against the reference underneath was
        showing a blend that sat 2.3x closer to the reference than the generated image
        actually is. A comparison tool that silently mixes the two things being compared is
        worse than no comparison.

        The FILE is untouched - the alpha band is still there and still means what the
        provenance says. This only fixes how QGIS draws it.
        """
        if layer.bandCount() < 4:
            return
        try:
            from qgis.core import QgsMultiBandColorRenderer, QgsContrastEnhancement
            prov = layer.dataProvider()
            r = QgsMultiBandColorRenderer(prov, 1, 2, 3)
            for band, setter in ((1, r.setRedContrastEnhancement),
                                 (2, r.setGreenContrastEnhancement),
                                 (3, r.setBlueContrastEnhancement)):
                ce = QgsContrastEnhancement(prov.dataType(band))
                ce.setMinimumValue(0)
                ce.setMaximumValue(255)
                setter(ce)
            layer.setRenderer(r)
            layer.triggerRepaint()
        except Exception as e:                       # noqa: BLE001
            _log(f"could not force opaque RGB rendering: {e}", member(Qgis, 'Warning'))

    def _style_bands(self, layer):
        """Paletted renderer with band names, so nobody configures symbology."""
        from gencp_core import confidence as conf
        from qgis.core import QgsPalettedRasterRenderer
        from qgis.PyQt.QtGui import QColor
        labels = {conf.BAND_RED: t("band_red"), conf.BAND_AMBER: t("band_amber"),
                  conf.BAND_GREEN: t("band_green")}
        classes = [QgsPalettedRasterRenderer.Class(
            int(v), QColor(*conf.BAND_COLOURS[v]), labels[v])
            for v in (conf.BAND_RED, conf.BAND_AMBER, conf.BAND_GREEN)]
        layer.setRenderer(QgsPalettedRasterRenderer(layer.dataProvider(), 1, classes))
        layer.triggerRepaint()

    def _done(self):
        task, self._task = self._task, None
        res = task.result or {}
        self.progress.setValue(100)
        out = res.get("output")
        if out and self.cb_add_layer.isChecked():
            self._add(out)
            # 2.5 - the preview made permanent, named as asked.
            if res.get("osm_output"):
                self._add(res["osm_output"], name=Path(out).stem + "_osm")
            if res.get("output_reprojected"):
                self._add(res["output_reprojected"])
            cinfo = res.get("confidence") or {}
            if cinfo.get("output"):
                self._add(cinfo["output"], style_bands=True)
        self._show_run_verdict((res.get("confidence") or {}).get("verdict"))
        self.lbl_status.setText(
            t("done_wrote", name=Path(out).name) if out else t("idle"))
        self.btn_cancel.setEnabled(False)
        self._validate()

    def _show_run_verdict(self, verdict):
        """SAFETY PROPERTY 2, run half: one sentence in the status area, plus a message-bar
        line only when the red share crosses the threshold."""
        if not verdict:
            return
        fr = verdict["fractions"]
        self.lbl_verdict.setText(t("verdict_line", green=fr["green"] * 100,
                                   amber=fr["amber"] * 100, red=fr["red"] * 100))
        self.lbl_verdict.setStyleSheet("")
        self.lbl_verdict.setVisible(True)
        if verdict["red_exceeds_threshold"]:
            self._msg(t("verdict_red_warning", red=fr["red"] * 100))

    def _failed(self):
        task, self._task = self._task, None
        self.btn_cancel.setEnabled(False)
        if task is not None and task.exception is not None:
            self.lbl_status.setText(t("failed", err=task.exception))
            QMessageBox.critical(self, t("failed_title"), str(task.exception))
        else:
            self.lbl_status.setText(t("cancelled"))
        self._validate()
