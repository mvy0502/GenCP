"""The GenCP dialog. Shell only — it calls gencp_core and contains no generation logic.

Six sections, in the order the work is done:

  1 Girdi        reference layer; the read extent and CRS; tile count and a rough estimate
  2 Veri kaynağı online (Overpass) or a local vector file; CLC+ path. Once these are
                 remembered they collapse into an Advanced group, because a returning user
                 should not have to look at three absolute paths to press one button.
  3 Önizleme     THE RASTERISED INPUT, RENDERED ON SCREEN, with the OSM content of the tile
                 broken down by class beside it. Generation does not start until the user
                 confirms. The breakdown is what gives that confirmation something to bite
                 on: "is this correct?" is unanswerable when the tile is flat green.
  4 Model        weights path, with the model's file name and modification date
  5 Çıktı        add as layer and/or write a GeoTIFF; optionally a confidence layer,
                 auto-styled, with a plain-language verdict for the whole run
  6 Çalıştırma   on a QgsTask, with a stage-aware progress line and a working Cancel.
                 PINNED below the scroll area, so the primary action is visible at every
                 window size - it used to scroll off the bottom of a short window

Every numeric or geometric decision is delegated: extents and tile grids to
gencp_core.extent, rendering to gencp_core.rasterize, generation to gencp_core.pipeline,
the confidence score to gencp_core.confidence.

No Turkish literal appears in this file. Every user-visible string comes from strings.py;
a string missing from that module is a bug there, not here.
"""
from __future__ import annotations
import os
from pathlib import Path

from qgis.PyQt.QtCore import Qt, QSize
from qgis.PyQt.QtGui import QImage, QPixmap, QFont, QFontMetrics
from qgis.PyQt.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout,
    QGroupBox, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QProgressBar,
    QPushButton, QRadioButton, QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
)
from qgis.core import (
    Qgis, QgsApplication, QgsMapLayerProxyModel, QgsMessageLog, QgsProject,
    QgsRasterLayer, QgsSettings,
)
from qgis.gui import QgsMapLayerComboBox

from .plugin import ensure_core_importable
from .qtcompat import member
from .strings import t

ensure_core_importable()

TILE_PREVIEW_PX = 384
SETTINGS_PREFIX = "GenCP/"
# There is deliberately no hand-set "very little OSM data" threshold here any more. It was
# an unregistered guess sitting beside a registered measurement, and on the first tile it
# was tested against the two disagreed: 0.295% OSM so no warning, while the confidence
# layer put 33.6% of that same tile in the red band. The preview judgement now comes from
# the registered score and the registered band boundaries, so the two cannot diverge.

# Theme-aware. A solid #fff3cd panel is a light box punched into a dark UI under QGIS's
# Night Mapping theme; a translucent amber wash over palette(window) reads as a warning in
# BOTH themes, and the text colour comes from the palette so it stays legible either way.
WARN_STYLE = ("background: rgba(224,168,0,0.16); color: palette(window-text); "
              "border: 1px solid rgba(224,168,0,0.55); border-left: 4px solid #e0a800; "
              "padding: 6px;")
DANGER_STYLE = ("background: rgba(202,0,32,0.14); color: palette(window-text); "
                "border: 1px solid rgba(202,0,32,0.55); border-left: 4px solid #ca0020; "
                "padding: 6px;")
INFO_STYLE = ("border: 1px solid palette(mid); color: palette(window-text); padding: 6px;")
CALM_BOX = "QWidget { border:1px solid palette(mid); border-radius:4px; }"
ALERT_BOX = "QWidget { border:2px solid #e0a800; border-radius:4px; }"


def _log(msg, level=member(Qgis, 'Info')):
    QgsMessageLog.logMessage(str(msg), "GenCP", level)


def _policy(name):
    """QSizePolicy member, Qt5-flat or Qt6-scoped."""
    return getattr(getattr(QSizePolicy, "Policy", QSizePolicy), name)


class ElidedLabel(QLabel):
    """A label that elides its text in the MIDDLE and keeps the full text as a tooltip.

    Paths here are absolute and routinely 90 characters. Elided at the END they lose the
    file name, which is the only part anyone reads; elided in the middle they keep both the
    root and the name. It also stops a long path from setting the form's minimum width,
    which is what previously put a horizontal scrollbar under every section.
    """

    def __init__(self, text="", parent=None):
        super().__init__(parent)
        self._full = ""
        self.setSizePolicy(_policy("Ignored"), self.sizePolicy().verticalPolicy())
        self.setMinimumWidth(80)
        self.setText(text)

    def setText(self, text):
        self._full = text or ""
        self.setToolTip(self._full)
        super().setText(self._elided())

    def fullText(self):
        return self._full

    def _elided(self):
        fm = QFontMetrics(self.font())
        return fm.elidedText(self._full, member(Qt, 'ElideMiddle'),
                             max(60, self.width() - 4))

    def resizeEvent(self, e):
        super().resizeEvent(e)
        super().setText(self._elided())


def _collapsible(title):
    """QgsCollapsibleGroupBox where available, a plain QGroupBox where it is not.

    QGIS ships the collapsible box in 3.x and 4.x alike; the fallback keeps this file
    importable under bare Qt and adds no dependency either way.
    """
    try:
        from qgis.gui import QgsCollapsibleGroupBox
        g = QgsCollapsibleGroupBox(title)
        g.setCollapsed(True)
        return g
    except Exception:                                # noqa: BLE001
        return QGroupBox(title)


class GenCPDialog(QDialog):
    def __init__(self, iface, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.settings = QgsSettings()
        self.setWindowTitle(t("window_title"))
        # Small enough to open fully on a short screen; the preview area starts collapsed
        # so all six section headers and the Generate button fit without scrolling.
        self.setMinimumSize(QSize(700, 460))
        self._extent = None
        self._crs = None
        self._preview_index = 0
        self._task = None
        self._confirmed = False
        self._extent_ok = False
        self._ui_ready = False
        self._build_ui()
        self._refresh_extent()
        self._connect_project_signals()
        self.resize(QSize(840, 760))

    # ------------------------------------------------------------- settings ----
    def _remember(self, key, value):
        if value:
            self.settings.setValue(SETTINGS_PREFIX + key, str(value))

    def _recall(self, key, default=""):
        """Project first, then QgsSettings, then the caller's default.

        QgsSettings is per-PROFILE, so it cannot travel in a .qgz. A demo or a handover
        project needs to carry its own paths, which is what the project entries are for.
        Reading them first means opening such a project just works; _remember still writes
        only to QgsSettings, so ordinary use never mutates somebody's project file.
        """
        try:
            v, ok = QgsProject.instance().readEntry("GenCP", key, "")
            if ok and v:
                return str(v)
        except Exception:                            # noqa: BLE001
            pass
        return str(self.settings.value(SETTINGS_PREFIX + key, default) or default)

    # ------------------------------------------------------------------- UI ----
    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 10, 10, 10)
        outer.setSpacing(8)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(getattr(getattr(QScrollArea, "Shape", QScrollArea), "NoFrame"))
        body = QWidget()
        lay = QVBoxLayout(body)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        scroll.setWidget(body)
        outer.addWidget(scroll, 1)

        # --- 1 Girdi -------------------------------------------------------
        g1 = QGroupBox(t("sec1"))
        g1v = QVBoxLayout(g1)
        g1v.setContentsMargins(10, 8, 10, 8)
        g1v.setSpacing(6)
        f1 = QFormLayout()
        f1.setLabelAlignment(member(Qt, 'AlignRight') | member(Qt, 'AlignVCenter'))
        f1.setHorizontalSpacing(12)
        f1.setVerticalSpacing(8)
        self.layer_box = QgsMapLayerComboBox()
        self.layer_box.setFilters(member(QgsMapLayerProxyModel, 'All'))
        self.layer_box.layerChanged.connect(self._refresh_extent)
        f1.addRow(t("reference_layer"), self.layer_box)
        # An empty combo with no explanation reads as broken. This says what is missing and
        # what to do about it, right where the missing thing would have been.
        self.lbl_layer_hint = QLabel("")
        self.lbl_layer_hint.setWordWrap(True)
        self.lbl_layer_hint.setVisible(False)
        self.lbl_layer_hint.setToolTip(t("no_raster_layer_tooltip"))
        self.lbl_extent = QLabel(t("waiting"))
        self.lbl_extent.setWordWrap(True)
        f1.addRow(t("extent"), self.lbl_extent)
        self.lbl_crs = QLabel(t("waiting"))
        self.lbl_crs.setWordWrap(True)
        f1.addRow(t("crs"), self.lbl_crs)
        self.lbl_tiles = QLabel(t("waiting"))
        self.lbl_tiles.setWordWrap(True)
        f1.addRow(t("tiles_estimate"), self.lbl_tiles)
        self.overlap_box = QComboBox()
        for m in (0, 160, 320, 640, 960):
            key = ("overlap_default" if m == 640 else
                   "overlap_economy" if m == 160 else "overlap_plain")
            self.overlap_box.addItem(t(key, m=m), m)
        self.overlap_box.setCurrentIndex(3)
        self.overlap_box.currentIndexChanged.connect(self._refresh_extent)
        f1.addRow(t("tile_overlap"), self.overlap_box)
        g1v.addLayout(f1)
        g1v.addWidget(self.lbl_layer_hint)
        lay.addWidget(g1)

        # --- 2 Veri kaynağı ------------------------------------------------
        g2 = QGroupBox(t("sec2"))
        f2 = QVBoxLayout(g2)
        f2.setSpacing(8)
        f2.setContentsMargins(10, 8, 10, 8)
        row = QHBoxLayout()
        self.rb_online = QRadioButton(t("source_online"))
        self.rb_local = QRadioButton(t("source_local"))
        self.rb_local.setChecked(True)
        self.rb_online.toggled.connect(self._validate)
        row.addWidget(self.rb_online)
        row.addWidget(self.rb_local)
        row.addStretch(1)
        f2.addLayout(row)
        self.lbl_summary = ElidedLabel("")
        f2.addWidget(self.lbl_summary)
        self.lbl_src = QLabel("")
        self.lbl_src.setWordWrap(True)
        f2.addWidget(self.lbl_src)

        self.adv = _collapsible(t("advanced"))
        fa = QFormLayout(self.adv)
        fa.setHorizontalSpacing(12)
        fa.setVerticalSpacing(8)
        fa.setContentsMargins(10, 8, 10, 8)
        self.pbf_edit, pbf_row = self._file_row(self._pick_pbf)
        fa.addRow(t("pbf_label"), pbf_row)
        self.clc_edit, clc_row = self._file_row(self._pick_clc)
        fa.addRow(t("clc_label"), clc_row)
        f2.addWidget(self.adv)
        lay.addWidget(g2)

        # --- 3 Önizleme ----------------------------------------------------
        g3 = QGroupBox(t("sec3"))
        f3 = QVBoxLayout(g3)
        f3.setSpacing(8)
        f3.setContentsMargins(10, 8, 10, 8)
        self.preview_hint = QLabel(t("preview_hint"))
        # Without word wrap this label's one-line sizeHint becomes the form's minimum
        # width, and a horizontal scrollbar appears under every section.
        self.preview_hint.setWordWrap(True)
        f3.addWidget(self.preview_hint)

        # Slim placeholder while there is nothing to preview. A 384 px empty box pushed
        # sections 4-6 and the Generate button below the fold, so a first-time user never
        # saw the primary action at all.
        self.preview_slim = QLabel(t("preview_needs_layer"))
        self.preview_slim.setWordWrap(True)
        self.preview_slim.setStyleSheet(INFO_STYLE)
        self.preview_slim.setMinimumHeight(44)
        f3.addWidget(self.preview_slim)

        # The image and the OSM panel live in one widget that is shown or hidden as a
        # whole, and the panel keeps a FIXED width whether or not it has content, so the
        # layout does not jump between the empty and populated states.
        self.preview_body = QWidget()
        img_row = QHBoxLayout(self.preview_body)
        img_row.setContentsMargins(0, 0, 0, 0)
        img_row.setSpacing(12)
        self.preview_label = QLabel(t("preview_press"))
        self.preview_label.setAlignment(member(Qt, 'AlignCenter'))
        self.preview_label.setWordWrap(True)
        self.preview_label.setFixedSize(TILE_PREVIEW_PX, TILE_PREVIEW_PX)
        self.preview_label.setStyleSheet("border:1px solid palette(mid);")
        img_row.addWidget(self.preview_label, 0)
        self.lbl_osm = QLabel(t("osm_placeholder"))
        self.lbl_osm.setWordWrap(True)
        self.lbl_osm.setAlignment(member(Qt, 'AlignTop'))
        self.lbl_osm.setMinimumWidth(210)
        img_row.addWidget(self.lbl_osm, 1)
        self.preview_body.setVisible(False)
        f3.addWidget(self.preview_body)

        prow = QHBoxLayout()
        prow.setSpacing(8)
        self.btn_preview = QPushButton(t("preview_button"))
        self.btn_preview.clicked.connect(self._render_preview)
        self.btn_prev = QPushButton(t("preview_prev"))
        self.btn_next = QPushButton(t("preview_next"))
        self.btn_prev.clicked.connect(lambda: self._step_preview(-1))
        self.btn_next.clicked.connect(lambda: self._step_preview(+1))
        self.btn_prev.setEnabled(False)
        self.btn_next.setEnabled(False)
        prow.addWidget(self.btn_preview)
        prow.addWidget(self.btn_prev)
        prow.addWidget(self.btn_next)
        prow.addStretch(1)
        f3.addLayout(prow)

        # The warning and the checkbox share one framed block, so the thing being confirmed
        # and the reason to hesitate cannot be read separately.
        self.confirm_box = QWidget()
        cb_lay = QVBoxLayout(self.confirm_box)
        cb_lay.setContentsMargins(10, 10, 10, 10)
        cb_lay.setSpacing(6)
        self.lbl_warn = QLabel("")
        self.lbl_warn.setWordWrap(True)
        self.lbl_warn.setVisible(False)
        cb_lay.addWidget(self.lbl_warn)
        self.cb_confirm = QCheckBox(t("confirm_generic"))
        self.cb_confirm.setEnabled(False)
        self.cb_confirm.toggled.connect(self._on_confirm)
        cb_lay.addWidget(self.cb_confirm)
        self.confirm_box.setStyleSheet(CALM_BOX)
        f3.addWidget(self.confirm_box)
        lay.addWidget(g3)

        # --- 4 Model -------------------------------------------------------
        g4 = QGroupBox(t("sec4"))
        f4 = QVBoxLayout(g4)
        f4.setSpacing(8)
        f4.setContentsMargins(10, 8, 10, 8)
        self.model_edit, mrow = self._file_row(self._pick_model)
        f4.addLayout(mrow)
        self.lbl_model = QLabel(t("model_none"))
        self.lbl_model.setWordWrap(True)
        f4.addWidget(self.lbl_model)
        # Which model SHIPS and which model the bands were CALIBRATED ON are two separate
        # decisions. This states the second one wherever the first is made, so one cannot
        # silently imply the other.
        self.lbl_model_calib = QLabel("")
        self.lbl_model_calib.setWordWrap(True)
        self.lbl_model_calib.setVisible(False)
        f4.addWidget(self.lbl_model_calib)
        lay.addWidget(g4)

        # --- 6 Çalıştırma (pinned below the scroll area, built here, placed later) --
        g5 = QGroupBox(t("sec5"))
        f5 = QVBoxLayout(g5)
        f5.setSpacing(8)
        f5.setContentsMargins(10, 8, 10, 8)
        self.progress = QProgressBar()
        self.progress.setValue(0)
        self.progress.setMinimumHeight(22)
        f5.addWidget(self.progress)
        self.lbl_status = QLabel(t("idle"))
        self.lbl_status.setWordWrap(True)
        f5.addWidget(self.lbl_status)
        rrow = QHBoxLayout()
        rrow.setSpacing(8)
        self.btn_run = QPushButton(t("generate"))
        self.btn_run.clicked.connect(self._start)
        # Primary action: default button, bold label, taller. Deliberately NOT a hardcoded
        # accent colour, which would look wrong in one of the two QGIS themes.
        self.btn_run.setDefault(True)
        self.btn_run.setAutoDefault(True)
        bf = QFont(self.btn_run.font())
        bf.setBold(True)
        self.btn_run.setFont(bf)
        self.btn_run.setMinimumHeight(32)
        self.btn_run.setMinimumWidth(140)
        self.btn_cancel = QPushButton(t("cancel"))
        self.btn_cancel.clicked.connect(self._cancel)
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.setMinimumHeight(32)
        rrow.addWidget(self.btn_run)
        rrow.addWidget(self.btn_cancel)
        rrow.addStretch(1)
        f5.addLayout(rrow)
        self._run_group = g5          # placed after the scroll area, not inside it

        # --- 5 Çıktı -------------------------------------------------------
        g6 = QGroupBox(t("sec6"))
        f6 = QVBoxLayout(g6)
        f6.setSpacing(8)
        f6.setContentsMargins(10, 8, 10, 8)
        self.cb_add_layer = QCheckBox(t("add_layer"))
        self.cb_add_layer.setChecked(True)
        self.cb_write = QCheckBox(t("write_tif"))
        self.cb_write.setChecked(True)
        self.cb_write.toggled.connect(self._validate)
        f6.addWidget(self.cb_add_layer)
        f6.addWidget(self.cb_write)
        self.out_edit, orow = self._file_row(self._pick_out, t("save_as"))
        f6.addLayout(orow)
        self.cb_confidence = QCheckBox(t("make_confidence"))
        self.cb_confidence.setChecked(True)
        self.cb_confidence.toggled.connect(self._validate)
        f6.addWidget(self.cb_confidence)
        cost = QLabel(t("confidence_cost"))
        cost.setEnabled(False)
        f6.addWidget(cost)
        self.lbl_conf_note = QLabel("")
        self.lbl_conf_note.setWordWrap(True)
        self.lbl_conf_note.setVisible(False)
        f6.addWidget(self.lbl_conf_note)
        self.lbl_verdict = QLabel("")
        self.lbl_verdict.setWordWrap(True)
        self.lbl_verdict.setVisible(False)
        f6.addWidget(self.lbl_verdict)
        # The Spearman / partial-rho sentence is real and stays available, but it is not
        # what a GIS analyst needs in the first two seconds. Prominent: the band shares and
        # the red-share warning. Behind a fold: the statistics.
        self.details = _collapsible(t("details"))
        fd = QVBoxLayout(self.details)
        fd.setContentsMargins(10, 8, 10, 8)
        self.lbl_scope = QLabel(t("verdict_scope"))
        self.lbl_scope.setWordWrap(True)
        fd.addWidget(self.lbl_scope)
        self.details.setVisible(False)
        f6.addWidget(self.details)
        lay.addWidget(g6)

        lay.addStretch(1)
        # The run controls sit OUTSIDE the scroll area, pinned above the Close button, so
        # the primary action is visible at every window size and scroll position. It used
        # to be the fifth of six scrolling sections and fell below the fold on a short
        # screen with nothing selected - a first-time user never saw the Generate button
        # at all. Pinning it also puts the sections in the order they are actually used:
        # choose the output path (5), then press Generate (6).
        outer.addWidget(self._run_group, 0)
        self.buttons = QDialogButtonBox(member(QDialogButtonBox, 'Close'))
        btn = self.buttons.button(member(QDialogButtonBox, 'Close'))
        if btn is not None:
            btn.setText(t("close"))
        self.buttons.rejected.connect(self.reject)
        outer.addWidget(self.buttons)

        # Prefills come LAST, and the ordering is load-bearing. Setting a QLineEdit's text
        # emits textChanged, connected to _validate, which reads widgets built above. Run
        # from the middle of _build_ui this raised AttributeError inside a Qt slot on every
        # construction, which QGIS turns into a modal error dialog.
        self._ui_ready = True
        self._prefill()

    def _connect_project_signals(self):
        """Repopulate when the project's layers change.

        QgsMapLayerComboBox tracks the project itself, but the surrounding explanation, the
        placeholders and the enabled/disabled state do not - so a user who loads a raster
        with this dialog open would otherwise still be looking at "no suitable layer".
        """
        prj = QgsProject.instance()
        for sig in ("layersAdded", "layersRemoved", "layersWillBeRemoved"):
            try:
                getattr(prj, sig).connect(self._on_project_layers_changed)
            except Exception:                        # noqa: BLE001 - signal set varies
                pass

    def _on_project_layers_changed(self, *_a):
        self._refresh_layer_hint()
        self._refresh_extent()

    def _refresh_layer_hint(self):
        n = self.layer_box.count()
        if n:
            self.lbl_layer_hint.setVisible(False)
            self.lbl_layer_hint.setText("")
            return
        self.lbl_layer_hint.setText(
            t("no_raster_layer") + "<br>" + t("no_raster_layer_hint"))
        self.lbl_layer_hint.setStyleSheet(INFO_STYLE)
        self.lbl_layer_hint.setVisible(True)

    def _set_advanced_collapsed(self, collapsed):
        try:
            self.adv.setCollapsed(bool(collapsed))
        except Exception:                            # noqa: BLE001 - QGroupBox fallback
            pass

    def _file_row(self, slot, btn_text=None):
        edit = QLineEdit()
        # A full CLC+ path is ~90 characters. Left to its own sizeHint the field widens the
        # whole form; this lets it shrink and scroll internally instead.
        edit.setMinimumWidth(180)
        btn = QPushButton(btn_text or t("browse"))
        btn.clicked.connect(slot)
        row = QHBoxLayout()
        row.setSpacing(8)
        row.addWidget(edit, 1)
        row.addWidget(btn)
        edit.textChanged.connect(self._validate)
        return edit, row

    # -------------------------------------------------------------- prefill ---
    def _repo_root(self):
        here = Path(__file__).resolve()
        for p in here.parents:
            if (p / "tubitak").is_dir():
                return p
        return None

    def _prefill(self):
        """Remembered paths first, repository defaults second, nothing third.

        A first-time user should be able to pick a reference layer and press Generate; a
        returning one should not have to re-find three absolute paths. Everything here is
        only a pre-fill and every field stays editable.
        """
        root = self._repo_root()
        clc = self._recall("clc_path")
        if not clc and root:
            cand = root / ("tubitak/data/clcplus/"
                           "CLMS_CLCplus_RASTER_2021_010m_eu_03035_V1_1.tif")
            clc = str(cand) if cand.is_file() else ""
        if clc:
            self.clc_edit.setText(clc)

        pbf = self._recall("pbf_path")
        if pbf and Path(pbf).is_file():
            self.pbf_edit.setText(pbf)

        model = self._recall("model_path")
        if not model and root:
            d = root / "tubitak/data/plugin_models"
            # Never bundled-and-hardcoded: this pre-fills only if the file happens to
            # exist. C2 is offered first because it is the arm the confidence bands were
            # calibrated on - see gencp_core/confidence.py CALIBRATION.
            for name in ("gencp_C2_fp32.onnx", "gencp_C3_fp32.onnx"):
                if (d / name).is_file():
                    model = str(d / name)
                    break
        if model:
            self.model_edit.setText(model)
        self._describe_model()

        out_dir = self._recall("out_dir")
        if out_dir and Path(out_dir).is_dir():
            self.out_edit.setText(str(Path(out_dir) / "gencp_reference.tif"))

        if self._recall("clc_path") or self._recall("model_path"):
            self.lbl_summary.setText(t("remembered"))
        self._update_source_summary()
        # If everything resolved, the paths are noise: collapse them away so the common
        # path is "pick a layer, press Generate". _validate reopens the group the moment
        # something stops resolving, because that is where the fix is.
        if self._source_ok()[0]:
            self._set_advanced_collapsed(True)

    # ------------------------------------------------------------- handlers ---
    def _pick_pbf(self):
        p, _ = QFileDialog.getOpenFileName(self, t("source_local"),
                                           self._recall("pbf_path"),
                                           "OSM PBF (*.pbf *.osm.pbf);;All files (*)")
        if p:
            self.pbf_edit.setText(p)
            self.rb_local.setChecked(True)
            self._remember("pbf_path", p)

    def _pick_clc(self):
        p, _ = QFileDialog.getOpenFileName(self, t("clc_label"), self._recall("clc_path"),
                                           "GeoTIFF (*.tif *.tiff);;All files (*)")
        if p:
            self.clc_edit.setText(p)
            self._remember("clc_path", p)

    def _pick_model(self):
        p, _ = QFileDialog.getOpenFileName(self, t("model_pick"),
                                           self._recall("model_path"),
                                           "ONNX (*.onnx);;All files (*)")
        if p:
            self.model_edit.setText(p)
            self._remember("model_path", p)
            self._describe_model()

    def _pick_out(self):
        start = self._recall("out_dir")
        default = str(Path(start) / "gencp_reference.tif") if start else "gencp_reference.tif"
        p, _ = QFileDialog.getSaveFileName(self, t("out_pick"), default, "GeoTIFF (*.tif)")
        if p:
            self.out_edit.setText(p)
            self._remember("out_dir", str(Path(p).parent))

    def _describe_model(self):
        p = Path(self.model_edit.text().strip() or "/nonexistent")
        if not p.is_file():
            self.lbl_model.setText(t("model_none"))
            return
        import datetime
        st = p.stat()
        mt = datetime.datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        self.lbl_model.setText(t("model_desc", name=p.name, mtime=mt, mb=st.st_size / 1e6))
        self._describe_calibration(p)

    def _describe_calibration(self, model_path):
        """Say, at the point the model is chosen, whether the bands were measured on it."""
        from gencp_core import confidence as conf
        try:
            ok = conf.model_is_validated(model_path)
        except Exception:                            # noqa: BLE001
            ok = False
        if ok:
            self.lbl_model_calib.setText(t("model_calibrated_ok"))
            self.lbl_model_calib.setStyleSheet("")
        else:
            self.lbl_model_calib.setText(t(
                "model_not_calibrated",
                calib=conf.CALIBRATION["calibrated_model_file"]))
            self.lbl_model_calib.setStyleSheet(WARN_STYLE)
            self.lbl_model_calib.setToolTip(t("model_not_calibrated_tooltip"))
        self.lbl_model_calib.setVisible(True)

    def _on_confirm(self, on):
        self._confirmed = bool(on)
        self._validate()

    # --------------------------------------------------------------- extent ---
    def _refresh_extent(self):
        layer = self.layer_box.currentLayer()
        if layer is None:
            for lbl in (self.lbl_extent, self.lbl_crs, self.lbl_tiles):
                lbl.setText(t("waiting"))
            self._extent = self._crs = None
            self._extent_ok = False
            self._invalidate_preview()
            self._set_preview_area(False)
            self._refresh_layer_hint()
            self._validate()
            return
        r = layer.extent()
        crs = layer.crs()
        self._extent = (r.xMinimum(), r.yMinimum(), r.xMaximum(), r.yMaximum())
        # pyproj cannot resolve a QGIS-local "USER:100001" authid, but it can read the WKT
        # the same CRS carries, so custom CRSs are passed on as WKT.
        authid = crs.authid() or ""
        self._crs = crs.toWkt() if (not authid or authid.startswith("USER:")) else authid
        self.lbl_extent.setText(t("extent_value", xmin=r.xMinimum(), ymin=r.yMinimum(),
                                  xmax=r.xMaximum(), ymax=r.yMaximum(),
                                  w=r.width(), h=r.height()))
        self.lbl_crs.setText(f"{crs.authid()} — {crs.description()}")
        try:
            from gencp_core import extent as ext
            e, work, _ = ext.resolve(self._extent, self._crs)
            est = ext.estimate(e, self.overlap_box.currentData())
            self.lbl_tiles.setText(
                t("tiles_value", n=est["n_tiles"], w=est["width"], h=est["height"],
                  mp=est["megapixels"], crs=work)
                + "<br><span style='color:gray'>"
                + t("tiles_estimate_note", mins=est["seconds"] / 60.0) + "</span>")
            self._extent_ok = True
        except Exception as e:                       # noqa: BLE001 - shown to the user
            self.lbl_tiles.setText(f"<span style='color:#a00'>{e}</span>")
            self._extent_ok = False
        self._invalidate_preview()
        self._set_preview_area(True)
        self._refresh_layer_hint()
        self._validate()

    def _set_preview_area(self, have_layer):
        """Collapse section 3 to one line until there is something to preview."""
        # With no layer, section 3 is ONE line. Advice about reading a preview, and a box
        # asking the user to confirm one, are both noise when there is no preview - and
        # together they were ~180 px of the empty form, which is what pushed Generate below
        # the fold on a short screen.
        self.preview_slim.setVisible(not have_layer)
        self.preview_hint.setVisible(bool(have_layer))
        self.preview_body.setVisible(bool(have_layer))
        self.confirm_box.setVisible(bool(have_layer))
        for b in (self.btn_preview, self.btn_prev, self.btn_next):
            b.setVisible(bool(have_layer))

    def _invalidate_preview(self):
        self._preview_index = 0
        self.cb_confirm.setChecked(False)
        self.cb_confirm.setEnabled(False)
        self.cb_confirm.setText(t("confirm_generic"))
        self.btn_prev.setEnabled(False)
        self.btn_next.setEnabled(False)
        self.preview_label.setText(t("preview_press"))
        self.preview_label.setPixmap(QPixmap())
        if hasattr(self, "lbl_osm"):
            self.lbl_osm.setText(t("osm_placeholder"))
        if hasattr(self, "lbl_warn"):
            self.lbl_warn.setVisible(False)
            self.lbl_warn.setText("")
            self.confirm_box.setStyleSheet(CALM_BOX)

    # -------------------------------------------------------------- preview ---
    def _apply_clc_path(self):
        """Point gencp_core at the CLC+ raster in section 2.

        Called before the PREVIEW as well as before the run. It used to be inlined in
        _start() only, so the preview rendered against whatever default gencp_core had
        while the run used the user's file: two different base rasters under one checkbox
        saying "I looked at the render above and it is correct".
        """
        clc = self.clc_edit.text().strip()
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
            QMessageBox.warning(self, t("sec2"), why)
            return
        self.lbl_status.setText(t("preview_rendering"))
        self._apply_clc_path()
        QgsApplication.processEvents()
        try:
            import numpy as np
            from gencp_core import extent as ext, pipeline, confidence as conf
            e, work, _ = ext.resolve(self._extent, self._crs)
            tiles, _ = ext.tile_grid(e, self.overlap_box.currentData())
            tile = tiles[min(self._preview_index, len(tiles) - 1)]
            # Deliberately the SAME cache directory pipeline.generate uses, so the run
            # consumes the very file the user looked at rather than re-rendering and
            # hoping the second render matches.
            d = pipeline.default_work_dir() / "render"
            stats = {}
            paths = pipeline.render_inputs(
                [tile], work, d, pbf=self._pbf_or_none(), base_product="clcplus",
                stats_out=stats)
            img = pipeline.preview_image(list(paths.values())[0])
            self._show_preview(img, tile, len(tiles))

            idx, names = conf.class_map(np.asarray(img.convert("RGB")))
            breakdown = conf.osm_class_breakdown(idx, names)
            frac = float(conf.osm_mask(idx, names).mean())
            self._show_osm_content(breakdown, frac)

            # The judgement about this tile comes from the SAME registered score and the
            # SAME band boundaries the output layer will use, computed on the very tile
            # being shown. It replaced a hand-set 0.2%-of-pixels threshold that
            # contradicted the layer on the first tile it was tried on: 0.295% OSM, no
            # warning, while the layer put 33.6% of that tile in the red band. Two
            # indicators of one thing, one measured and one guessed, is worse than either.
            # Since registration 2 the score is conf_D, so this needs no inference at all.
            sig = conf.signals(np.asarray(img.convert("RGB")))
            score = conf.deployed_score(sig["conf_D"])
            verdict = conf.run_verdict(score)
            self._show_warnings(
                pipeline.coverage_warnings(stats, self._pbf_or_none()),
                breakdown, verdict)

            self.cb_confirm.setEnabled(True)
            self.btn_prev.setEnabled(len(tiles) > 1)
            self.btn_next.setEnabled(len(tiles) > 1)
            self.lbl_status.setText(
                t("preview_done_counts", total=breakdown["total_osm_px"]))
        except Exception as e:                       # noqa: BLE001 - shown to the user
            _log(f"preview failed: {e}", member(Qgis, 'Warning'))
            self.lbl_status.setText(t("preview_failed", err=e))
            QMessageBox.critical(self, t("preview_failed_title"), str(e))

    def _step_preview(self, d):
        self._preview_index = max(0, self._preview_index + d)
        self.cb_confirm.setChecked(False)
        self._render_preview()

    def _show_preview(self, img, tile, n_tiles):
        img = img.convert("RGB")
        w, h = img.size
        qimg = QImage(img.tobytes("raw", "RGB"), w, h, 3 * w,
                      member(QImage, 'Format_RGB888')).copy()
        pm = QPixmap.fromImage(qimg).scaled(
            TILE_PREVIEW_PX, TILE_PREVIEW_PX,
            member(Qt, 'KeepAspectRatio'), member(Qt, 'FastTransformation'))
        self.preview_label.setPixmap(pm)
        i, j, tx, ty = tile
        self.preview_label.setToolTip(f"({i},{j})  {tx:.1f}, {ty:.1f}  {w}x{h} @ 10 m")
        self.cb_confirm.setText(t("confirm_tile", i=i, j=j, n=n_tiles))

    def _show_osm_content(self, b, frac):
        """What is actually in this tile, by class.

        "4 OSM feature(s) in this tile" is not a number anyone can judge. Which four, and
        of what kind, is - and it is what makes the confirmation checkbox answerable.
        """
        def cell(n):
            return t("osm_px", n=n) if n else t("osm_none")
        self.lbl_osm.setText(
            f"<b>{t('osm_breakdown_title')}</b>"
            f"<table cellspacing='3'>"
            f"<tr><td>{t('osm_roads')}</td><td align='right'>{cell(b['roads'])}</td></tr>"
            f"<tr><td>{t('osm_buildings')}</td><td align='right'>{cell(b['buildings'])}</td></tr>"
            f"<tr><td>{t('osm_water')}</td><td align='right'>{cell(b['water'])}</td></tr>"
            f"<tr><td>{t('osm_landuse')}</td><td align='right'>{cell(b['landuse'])}</td></tr>"
            f"</table>"
            f"<span style='color:gray'>{frac * 100:.3f}%</span>")

    def _render_coverage(self, items):
        """Turkish rendering of gencp_core's STRUCTURED coverage facts.

        gencp_core returns numbers and a `kind`, never prose: it used to return English
        sentences that the dialog then displayed under a Turkish heading, which is how a
        half-translated warning box got shipped.
        """
        out = []
        for it in items or []:
            if it.get("kind") == "zero_osm":
                tiles = ", ".join(f"({i},{j})" for i, j in it.get("tiles", []))
                more = t("warn_more_tiles", n=it["more"]) if it.get("more") else ""
                src = it.get("source") or t("warn_zero_osm_source_overpass")
                out.append(t("warn_zero_osm_tiles", n=it["n"], total=it["total"],
                             tiles=tiles, more=more, source=src))
            elif it.get("kind") == "count_unavailable":
                out.append(t("warn_count_unavailable", n=it["n"], total=it["total"]))
        return out

    def _show_warnings(self, msgs, breakdown=None, verdict=None):
        """Warnings go inside the confirmation frame, directly above the checkbox.

        A tile with no OSM data renders as clean CLC+ land cover and looks like
        countryside, not like a failure. The user is about to tick a box saying the render
        is correct; this is what gives that box something to bite on, so the two are drawn
        as one block and the frame itself changes colour.
        """
        from gencp_core import confidence as conf
        parts = self._render_coverage(msgs) if msgs and isinstance(
            (msgs or [{}])[0], dict) else list(msgs or [])
        severity = "warn" if parts else "info"
        if breakdown is not None and breakdown["total_osm_px"] == 0:
            # A fact, and it stays a warning whatever the score says. conf_D measures how
            # much INPUT information the tile carries, and CLC+ land-cover variety alone
            # can put a tile in the green band with zero OSM features in it. Those are two
            # different statements and the user needs both.
            parts.insert(0, t("osm_zero_warning"))
            severity = "warn"
        if verdict is not None:
            band = verdict["mean_band"]
            px = conf.CALIBRATION["band_median_px"][band]
            if band == "red":
                parts.insert(0, t("preview_band_red", px=f"{px:.1f}".replace(".", ",")))
                severity = "danger"
            elif band == "amber":
                parts.insert(0, t("preview_band_amber", px=f"{px:.1f}".replace(".", ",")))
                severity = "warn"
            else:
                # Green is not a warning, but silence would leave the user with nothing to
                # weigh the checkbox against, so it is stated calmly.
                parts.append(t("preview_band_green", px=f"{px:.1f}".replace(".", ",")))
                # Only calm the frame if nothing ELSE raised a flag.
                if severity != "warn":
                    severity = "info"
        if not parts:
            self.lbl_warn.setVisible(False)
            self.lbl_warn.setText("")
            self.confirm_box.setStyleSheet(CALM_BOX)
            return
        self.lbl_warn.setText("<br><br>".join(parts))
        self.lbl_warn.setStyleSheet(
            {"danger": DANGER_STYLE, "warn": WARN_STYLE, "info": INFO_STYLE}[severity])
        self.lbl_warn.setVisible(True)
        self.confirm_box.setStyleSheet(CALM_BOX if severity == "info" else ALERT_BOX)
        if severity != "info":
            for m in parts:
                _log(m, member(Qgis, 'Warning'))

    # ----------------------------------------------------------- validation ---
    def _pbf_or_none(self):
        if self.rb_local.isChecked():
            return self.pbf_edit.text().strip() or None
        return None

    def _update_source_summary(self):
        clc = Path(self.clc_edit.text().strip() or "")
        if self.rb_local.isChecked():
            pbf = Path(self.pbf_edit.text().strip() or "")
            if pbf.name and clc.name:
                self.lbl_summary.setText(t("source_summary_ok", pbf=pbf.name, clc=clc.name))
                return
        elif clc.name:
            self.lbl_summary.setText(t("source_summary_overpass", clc=clc.name))
            return
        self.lbl_summary.setText("")

    def _source_ok(self):
        if self.rb_local.isChecked():
            p = self.pbf_edit.text().strip()
            if not p:
                return False, t("err_pbf_empty")
            if not Path(p).is_file():
                return False, t("err_pbf_missing", path=p)
        clc = self.clc_edit.text().strip()
        if not clc:
            return False, t("err_clc_empty")
        if not Path(clc).is_file():
            return False, t("err_clc_missing", path=clc)
        return True, ""

    def _confidence_state(self):
        """(will_produce, note). Never silently downgrades the score.

        The bands were calibrated on one arm with one stochastic export. Offering them for
        a different model would be inventing a validation, so the layer is withheld and the
        note says exactly which file is missing or which model is wrong.
        """
        if not self.cb_confidence.isChecked():
            return False, ""
        from gencp_core import confidence as conf
        model = self.model_edit.text().strip()
        if not model or not Path(model).is_file():
            return False, ""
        if not conf.model_is_validated(model):
            return False, t("confidence_not_validated")
        if conf.needs_stochastic() and conf.stochastic_model_for(model) is None:
            name = Path(model).stem.replace("_fp32", "_stochastic_fp32") + ".onnx"
            return False, t("confidence_no_stochastic", name=name)
        return True, ""

    def _validate(self):
        # Signals can fire while _build_ui is still running; the widgets below may not
        # exist yet. See the note where the prefills are called.
        if not getattr(self, "_ui_ready", False):
            return
        ok_src, why = self._source_ok()
        self._update_source_summary()
        self.lbl_src.setText("" if ok_src else f"<span style='color:#a00'>{why}</span>")
        if not ok_src:
            # The fix is inside the Advanced group, so open it rather than pointing at a
            # collapsed box. Never auto-collapse here: the user may be mid-edit.
            self._set_advanced_collapsed(False)
        self.btn_preview.setEnabled(
            self._extent is not None and getattr(self, "_extent_ok", False) and ok_src)

        _will, note = self._confidence_state()
        self.lbl_conf_note.setText(note)
        self.lbl_conf_note.setVisible(bool(note))
        if note:
            self.lbl_conf_note.setStyleSheet(WARN_STYLE)

        model_ok = Path(self.model_edit.text().strip() or "/nonexistent").is_file()
        out_ok = (not self.cb_write.isChecked()) or bool(self.out_edit.text().strip())
        can_run = bool(self._extent is not None and getattr(self, "_extent_ok", False)
                       and ok_src and model_ok and self._confirmed and out_ok
                       and self._task is None)
        self.btn_run.setEnabled(can_run)
        if self._task is None and not can_run:
            self.lbl_status.setText(self._first_blocker(ok_src, model_ok, out_ok))

    def _first_blocker(self, ok_src, model_ok, out_ok):
        """The one thing to do next, phrased as the fix rather than the fault."""
        if self._extent is None:
            return t("err_no_layer")
        if not self._extent_ok:
            return self.lbl_tiles.text()
        if not ok_src:
            return self._source_ok()[1]
        if not model_ok:
            return t("err_model_missing")
        if not out_ok:
            return t("err_out_missing")
        if not self._confirmed:
            return t("err_not_confirmed")
        return t("idle")

    # -------------------------------------------------------------------- run -
    def _start(self):
        from gencp_core import confidence as conf
        model = self.model_edit.text().strip()
        will_conf, _note = self._confidence_state()
        params = dict(
            extent_bbox=self._extent, crs=self._crs, model_path=model,
            out_tif=self.out_edit.text().strip() if self.cb_write.isChecked() else None,
            pbf=self._pbf_or_none(), base_product="clcplus",
            overlap_m=float(self.overlap_box.currentData()),
            confidence=bool(will_conf),
            stochastic_model=(str(conf.stochastic_model_for(model))
                              if (will_conf and conf.needs_stochastic()) else None),
        )
        self._apply_clc_path()
        self._remember("clc_path", self.clc_edit.text().strip())
        self._remember("model_path", model)
        if self.out_edit.text().strip():
            self._remember("out_dir", str(Path(self.out_edit.text().strip()).parent))
        if self._pbf_or_none():
            self._remember("pbf_path", self._pbf_or_none())

        from .task import GenerateTask
        self._task = GenerateTask("GenCP", params)
        self._task.progressChanged.connect(self._on_progress)
        self._task.taskCompleted.connect(self._done)
        self._task.taskTerminated.connect(self._failed)
        self.btn_run.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.lbl_verdict.setVisible(False)
        self.lbl_status.setText(t("running_note"))
        QgsApplication.taskManager().addTask(self._task)

    def _on_progress(self):
        """A step name beats a percentage: it tells a slow step from a hung one."""
        if self._task is None:
            return
        self.progress.setValue(int(self._task.progress()))
        raw = self._task.message or ""
        stage, _, counts = raw.partition(":")
        done, _, total = counts.strip().partition("/")
        key = {"render": "stage_render", "infer": "stage_infer",
               "confidence": "stage_confidence", "mosaic": "stage_mosaic"}.get(
                   stage.strip(), "stage_unknown")
        self.lbl_status.setText(t(key, done=done or "?", total=total or "?"))

    def _cancel(self):
        if self._task is not None:
            self._task.cancel()
            self.lbl_status.setText(t("cancelling"))

    def _style_confidence_layer(self, layer):
        """Paletted renderer carrying the band names, so nobody configures symbology.

        The GeoTIFF already has a colour table, but QGIS will happily open a single-band
        uint8 raster as a grey ramp. Setting the renderer explicitly is what guarantees the
        legend reads "Kırmızı - kullanmayın" rather than "1".
        """
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
        msgs = []
        if out:
            msgs.append(t("wrote", path=Path(out).name))
            if self.cb_add_layer.isChecked():
                layer = QgsRasterLayer(out, Path(out).stem)
                if layer.isValid():
                    QgsProject.instance().addMapLayer(layer)
                    msgs.append(t("added_layer"))
                else:
                    msgs.append(t("layer_failed"))
        elif self.cb_add_layer.isChecked():
            msgs.append(t("no_file_to_add"))

        cinfo = res.get("confidence") or {}
        cpath = cinfo.get("output")
        if cpath and self.cb_add_layer.isChecked():
            clayer = QgsRasterLayer(cpath, Path(cpath).stem)
            if clayer.isValid():
                try:
                    self._style_confidence_layer(clayer)
                except Exception as e:               # noqa: BLE001
                    _log(f"confidence styling failed: {e}", member(Qgis, 'Warning'))
                QgsProject.instance().addMapLayer(clayer)
        self._show_verdict(cinfo.get("verdict"))

        seam = res.get("seam")
        if seam:
            msgs.append(t("seam", ratio=seam["ratio"]))
        warns = res.get("warnings") or []
        self._show_warnings(warns)
        self.lbl_status.setText(" · ".join(msgs) or t("done"))
        self.btn_cancel.setEnabled(False)
        self._validate()
        self.iface.messageBar().pushMessage(
            "GenCP", " · ".join(msgs),
            level=member(Qgis, 'Warning' if warns else 'Success'))

    def _show_verdict(self, verdict):
        """One line for the whole run, in plain language, with its scope attached."""
        if not verdict:
            self.lbl_verdict.setVisible(False)
            self.details.setVisible(False)
            return
        fr = verdict["fractions"]
        band_label = {"red": t("band_red"), "amber": t("band_amber"),
                      "green": t("band_green")}[verdict["mean_band"]]
        html = [f"<b>{t('verdict_title')}</b>",
                t("verdict_line", green=fr["green"] * 100, amber=fr["amber"] * 100,
                  red=fr["red"] * 100, band=band_label)]
        if verdict["red_exceeds_threshold"]:
            html.append(t("verdict_red_warning", red=fr["red"] * 100,
                          thr=verdict["red_warn_fraction"] * 100))
        self.lbl_verdict.setText("<br>".join(html))
        self.lbl_verdict.setStyleSheet(
            WARN_STYLE if verdict["red_exceeds_threshold"] else INFO_STYLE)
        self.lbl_verdict.setVisible(True)
        self.details.setVisible(True)

    def _failed(self):
        task, self._task = self._task, None
        self.btn_cancel.setEnabled(False)
        if task is not None and task.exception is not None:
            self.lbl_status.setText(t("failed", err=task.exception))
            QMessageBox.critical(self, t("failed_title"), str(task.exception))
        else:
            self.lbl_status.setText(t("cancelled"))
        self._validate()
