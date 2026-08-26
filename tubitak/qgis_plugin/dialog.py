"""The GenCP dialog. Shell only — it calls gencp_core and contains no generation logic.

Six sections, in the order the work package specifies:

  1 Input        reference layer picker; the read extent and CRS; tile count and a rough
                 time estimate
  2 Data source  online (Overpass) or a local vector file; CLC+ path; cannot proceed until
                 resolved
  3 Preview      THE RASTERISED INPUT, RENDERED ON SCREEN. Generation does not start until
                 the user confirms. This section is the point of the dialog: it is what
                 lets a user catch a bad render before trusting the output, so it shows a
                 real render at a real size, not a thumbnail.
  4 Model        weights path (configurable, not bundled-and-hardcoded), with the model's
                 file name and modification date shown
  5 Run          on a QgsTask, with a progress bar and a working Cancel
  6 Output       add as layer and/or write a GeoTIFF to a chosen path

Every numeric or geometric decision here is delegated: extents and tile grids come from
gencp_core.extent, rendering from gencp_core.rasterize, generation from
gencp_core.pipeline.
"""
from __future__ import annotations
import os
from pathlib import Path

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QImage, QPixmap
from qgis.PyQt.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout,
    QGroupBox, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QProgressBar,
    QPushButton, QRadioButton, QScrollArea, QVBoxLayout, QWidget,
)
from qgis.core import (
    Qgis, QgsApplication, QgsMapLayerProxyModel, QgsMessageLog, QgsProject,
    QgsRasterLayer,
)
from qgis.gui import QgsMapLayerComboBox

from .plugin import ensure_core_importable
from .qtcompat import member

ensure_core_importable()

TILE_PREVIEW_PX = 384


def _log(msg, level=member(Qgis, 'Info')):
    QgsMessageLog.logMessage(str(msg), "GenCP", level)


class GenCPDialog(QDialog):
    def __init__(self, iface, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.setWindowTitle("GenCP — Synthetic Reference Generation")
        self.setMinimumWidth(660)
        self._extent = None
        self._crs = None
        self._preview_paths = []
        self._preview_index = 0
        self._task = None
        self._confirmed = False
        self._build_ui()
        self._refresh_extent()

    # ---------------------------------------------------------------- UI ----
    def _build_ui(self):
        outer = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        body = QWidget()
        lay = QVBoxLayout(body)
        scroll.setWidget(body)
        outer.addWidget(scroll, 1)

        # --- 1 Input ---
        g1 = QGroupBox("1 · Input")
        f1 = QFormLayout(g1)
        self.layer_box = QgsMapLayerComboBox()
        self.layer_box.setFilters(member(QgsMapLayerProxyModel, 'All'))
        self.layer_box.layerChanged.connect(self._refresh_extent)
        f1.addRow("Reference layer:", self.layer_box)
        self.lbl_extent = QLabel("—")
        self.lbl_extent.setWordWrap(True)
        f1.addRow("Extent:", self.lbl_extent)
        self.lbl_crs = QLabel("—")
        f1.addRow("CRS:", self.lbl_crs)
        self.lbl_tiles = QLabel("—")
        f1.addRow("Tiles / estimate:", self.lbl_tiles)
        self.overlap_box = QComboBox()
        for m in (0, 160, 320, 640, 960):
            self.overlap_box.addItem(
                f"{m} m" + (" (default, measured)" if m == 640 else
                            " (economy)" if m == 160 else ""), m)
        self.overlap_box.setCurrentIndex(3)
        self.overlap_box.currentIndexChanged.connect(self._refresh_extent)
        f1.addRow("Tile overlap:", self.overlap_box)
        lay.addWidget(g1)

        # --- 2 Data source ---
        g2 = QGroupBox("2 · Data source")
        f2 = QVBoxLayout(g2)
        row = QHBoxLayout()
        self.rb_online = QRadioButton("Online (Overpass)")
        self.rb_local = QRadioButton("Local vector file (.osm.pbf)")
        self.rb_local.setChecked(True)
        self.rb_online.toggled.connect(self._validate)
        row.addWidget(self.rb_online)
        row.addWidget(self.rb_local)
        row.addStretch(1)
        f2.addLayout(row)
        self.pbf_edit, pbf_row = self._file_row("Browse…", self._pick_pbf)
        f2.addLayout(pbf_row)
        self.clc_edit, clc_row = self._file_row("Browse…", self._pick_clc)
        f2.addWidget(QLabel("CLC+ Backbone raster:"))
        f2.addLayout(clc_row)
        self.lbl_src = QLabel("")
        self.lbl_src.setWordWrap(True)
        f2.addWidget(self.lbl_src)
        lay.addWidget(g2)
        self._prefill_paths()

        # --- 3 Preview ---
        g3 = QGroupBox("3 · Preview — the rasterised input the model will see")
        f3 = QVBoxLayout(g3)
        f3.addWidget(QLabel(
            "Check this render before generating. If the land cover, water or roads look "
            "wrong here, the generated image will be confidently wrong in the same way."))
        self.preview_label = QLabel("No preview yet.")
        self.preview_label.setAlignment(member(Qt, 'AlignCenter'))
        self.preview_label.setMinimumHeight(TILE_PREVIEW_PX)
        self.preview_label.setStyleSheet("border:1px solid palette(mid);")
        f3.addWidget(self.preview_label)
        prow = QHBoxLayout()
        self.btn_preview = QPushButton("Render preview tile")
        self.btn_preview.clicked.connect(self._render_preview)
        self.btn_prev = QPushButton("◀ Previous tile")
        self.btn_next = QPushButton("Next tile ▶")
        self.btn_prev.clicked.connect(lambda: self._step_preview(-1))
        self.btn_next.clicked.connect(lambda: self._step_preview(+1))
        self.btn_prev.setEnabled(False)
        self.btn_next.setEnabled(False)
        prow.addWidget(self.btn_preview)
        prow.addWidget(self.btn_prev)
        prow.addWidget(self.btn_next)
        prow.addStretch(1)
        f3.addLayout(prow)
        self.cb_confirm = QCheckBox(
            "I have looked at the rasterised input above and it is correct")
        self.cb_confirm.setEnabled(False)
        self.cb_confirm.toggled.connect(self._on_confirm)
        f3.addWidget(self.cb_confirm)
        lay.addWidget(g3)

        # --- 4 Model ---
        g4 = QGroupBox("4 · Model")
        f4 = QVBoxLayout(g4)
        self.model_edit, mrow = self._file_row("Browse…", self._pick_model)
        f4.addLayout(mrow)
        self.lbl_model = QLabel("No model selected.")
        self.lbl_model.setWordWrap(True)
        f4.addWidget(self.lbl_model)
        lay.addWidget(g4)
        self._prefill_model()

        # --- 5 Run ---
        g5 = QGroupBox("5 · Run")
        f5 = QVBoxLayout(g5)
        self.progress = QProgressBar()
        self.progress.setValue(0)
        f5.addWidget(self.progress)
        self.lbl_status = QLabel("Idle.")
        self.lbl_status.setWordWrap(True)
        f5.addWidget(self.lbl_status)
        rrow = QHBoxLayout()
        self.btn_run = QPushButton("Generate")
        self.btn_run.clicked.connect(self._start)
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self._cancel)
        self.btn_cancel.setEnabled(False)
        rrow.addWidget(self.btn_run)
        rrow.addWidget(self.btn_cancel)
        rrow.addStretch(1)
        f5.addLayout(rrow)
        lay.addWidget(g5)

        # --- 6 Output ---
        g6 = QGroupBox("6 · Output")
        f6 = QVBoxLayout(g6)
        self.cb_add_layer = QCheckBox("Add the result to the map as a layer")
        self.cb_add_layer.setChecked(True)
        self.cb_write = QCheckBox("Write a GeoTIFF to disk")
        self.cb_write.setChecked(True)
        self.cb_write.toggled.connect(self._validate)
        f6.addWidget(self.cb_add_layer)
        f6.addWidget(self.cb_write)
        self.out_edit, orow = self._file_row("Save as…", self._pick_out)
        f6.addLayout(orow)
        lay.addWidget(g6)

        lay.addStretch(1)
        self.buttons = QDialogButtonBox(member(QDialogButtonBox, 'Close'))
        self.buttons.rejected.connect(self.reject)
        outer.addWidget(self.buttons)

    def _file_row(self, btn_text, slot):
        edit = QLineEdit()
        btn = QPushButton(btn_text)
        btn.clicked.connect(slot)
        row = QHBoxLayout()
        row.addWidget(edit, 1)
        row.addWidget(btn)
        edit.textChanged.connect(self._validate)
        return edit, row

    # ------------------------------------------------------------ prefill ----
    def _repo_root(self):
        here = Path(__file__).resolve()
        for p in here.parents:
            if (p / "tubitak").is_dir():
                return p
        return None

    def _prefill_paths(self):
        root = self._repo_root()
        if not root:
            return
        clc = root / "tubitak/data/clcplus/CLMS_CLCplus_RASTER_2021_010m_eu_03035_V1_1.tif"
        if clc.is_file():
            self.clc_edit.setText(str(clc))

    def _prefill_model(self):
        root = self._repo_root()
        if not root:
            return
        d = root / "tubitak/data/plugin_models"
        # Never a bundled-and-hardcoded weights file: this only pre-fills the field with
        # something sensible if it happens to exist, and the user can always change it.
        for name in ("gencp_C3_fp32.onnx", "gencp_C2_fp32.onnx"):
            if (d / name).is_file():
                self.model_edit.setText(str(d / name))
                break
        self._describe_model()

    # ------------------------------------------------------------ handlers ---
    def _pick_pbf(self):
        p, _ = QFileDialog.getOpenFileName(self, "OSM extract", "",
                                           "OSM PBF (*.pbf *.osm.pbf);;All files (*)")
        if p:
            self.pbf_edit.setText(p)
            self.rb_local.setChecked(True)

    def _pick_clc(self):
        p, _ = QFileDialog.getOpenFileName(self, "CLC+ Backbone raster", "",
                                           "GeoTIFF (*.tif *.tiff);;All files (*)")
        if p:
            self.clc_edit.setText(p)

    def _pick_model(self):
        p, _ = QFileDialog.getOpenFileName(self, "ONNX generator", "",
                                           "ONNX model (*.onnx);;All files (*)")
        if p:
            self.model_edit.setText(p)
            self._describe_model()

    def _pick_out(self):
        p, _ = QFileDialog.getSaveFileName(self, "Write GeoTIFF", "gencp_reference.tif",
                                           "GeoTIFF (*.tif)")
        if p:
            self.out_edit.setText(p)

    def _describe_model(self):
        p = Path(self.model_edit.text().strip())
        if not p.is_file():
            self.lbl_model.setText("No model selected.")
            return
        import datetime
        st = p.stat()
        mt = datetime.datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        self.lbl_model.setText(
            f"<b>{p.name}</b><br>modified {mt} &middot; {st.st_size/1e6:.1f} MB"
            f"<br><span style='color:gray'>{p.parent}</span>")

    def _on_confirm(self, on):
        self._confirmed = bool(on)
        self._validate()

    # -------------------------------------------------------------- extent ---
    def _refresh_extent(self):
        layer = self.layer_box.currentLayer()
        if layer is None:
            self.lbl_extent.setText("—")
            self.lbl_crs.setText("—")
            self.lbl_tiles.setText("—")
            self._extent = self._crs = None
            self._invalidate_preview()
            self._validate()
            return
        r = layer.extent()
        crs = layer.crs()
        self._extent = (r.xMinimum(), r.yMinimum(), r.xMaximum(), r.yMaximum())
        self._crs = crs.authid() or crs.toWkt()
        self.lbl_extent.setText(
            f"{r.xMinimum():.2f}, {r.yMinimum():.2f} → {r.xMaximum():.2f}, "
            f"{r.yMaximum():.2f}  ({r.width():.0f} × {r.height():.0f} map units)")
        self.lbl_crs.setText(f"{crs.authid()} — {crs.description()}")
        try:
            from gencp_core import extent as ext
            e, work, _ = ext.resolve(self._extent, self._crs)
            est = ext.estimate(e, self.overlap_box.currentData())
            mins = est["seconds"] / 60.0
            self.lbl_tiles.setText(
                f"<b>{est['n_tiles']} tiles</b> → output {est['width']} × {est['height']} px "
                f"({est['megapixels']:.1f} Mpx) in {work}"
                f"<br><span style='color:gray'>rough estimate {mins:.1f} min on CPU — "
                f"an estimate, not a guarantee</span>")
        except Exception as e:                       # noqa: BLE001 - shown to the user
            self.lbl_tiles.setText(f"<span style='color:#a00'>{e}</span>")
        self._invalidate_preview()
        self._validate()

    def _invalidate_preview(self):
        self._preview_paths = []
        self._preview_index = 0
        self.cb_confirm.setChecked(False)
        self.cb_confirm.setEnabled(False)
        self.btn_prev.setEnabled(False)
        self.btn_next.setEnabled(False)
        self.preview_label.setText("No preview yet.")
        self.preview_label.setPixmap(QPixmap())

    # ------------------------------------------------------------- preview ---
    def _render_preview(self):
        if self._extent is None:
            return
        src_ok, why = self._source_ok()
        if not src_ok:
            QMessageBox.warning(self, "Data source", why)
            return
        self.lbl_status.setText("Rendering preview tile…")
        QgsApplication.processEvents()
        try:
            from gencp_core import extent as ext, pipeline
            e, work, _ = ext.resolve(self._extent, self._crs)
            tiles, _ = ext.tile_grid(e, self.overlap_box.currentData())
            tile = tiles[min(self._preview_index, len(tiles) - 1)]
            import tempfile
            d = Path(tempfile.mkdtemp(prefix="gencp_preview_"))
            paths = pipeline.render_inputs(
                [tile], work, d, pbf=self._pbf_or_none(), base_product="clcplus")
            p = list(paths.values())[0]
            self._show_preview(p, tile, len(tiles))
            self._preview_paths = [str(p)]
            self.cb_confirm.setEnabled(True)
            self.btn_prev.setEnabled(len(tiles) > 1)
            self.btn_next.setEnabled(len(tiles) > 1)
            self.lbl_status.setText("Preview rendered.")
        except Exception as e:                       # noqa: BLE001 - shown to the user
            _log(f"preview failed: {e}", member(Qgis, 'Warning'))
            self.lbl_status.setText(f"Preview failed: {e}")
            QMessageBox.critical(self, "Preview failed", str(e))

    def _step_preview(self, d):
        self._preview_index = max(0, self._preview_index + d)
        self.cb_confirm.setChecked(False)
        self._render_preview()

    def _show_preview(self, path, tile, n_tiles):
        from gencp_core import pipeline
        img = pipeline.preview_image(path).convert("RGB")
        w, h = img.size
        qimg = QImage(img.tobytes("raw", "RGB"), w, h, 3 * w, member(QImage, 'Format_RGB888')).copy()
        pm = QPixmap.fromImage(qimg).scaled(
            TILE_PREVIEW_PX, TILE_PREVIEW_PX, member(Qt, 'KeepAspectRatio'), member(Qt, 'FastTransformation'))
        self.preview_label.setPixmap(pm)
        i, j, tx, ty = tile
        self.preview_label.setToolTip(
            f"tile ({i},{j}) NW corner {tx:.1f}, {ty:.1f} — {w}×{h} px at 10 m")
        self.cb_confirm.setText(
            f"I have looked at tile ({i},{j}) of {n_tiles} above and the render is correct")

    # ------------------------------------------------------------ validation -
    def _pbf_or_none(self):
        if self.rb_local.isChecked():
            t = self.pbf_edit.text().strip()
            return t or None
        return None

    def _source_ok(self):
        if self.rb_local.isChecked():
            p = self.pbf_edit.text().strip()
            if not p:
                return False, "Choose a local .osm.pbf file, or switch to Overpass."
            if not Path(p).is_file():
                return False, f"OSM extract not found: {p}"
        clc = self.clc_edit.text().strip()
        if not clc:
            return False, "The CLC+ Backbone raster path is required."
        if not Path(clc).is_file():
            return False, f"CLC+ raster not found: {clc}"
        return True, ""

    def _validate(self):
        ok_src, why = self._source_ok()
        self.lbl_src.setText("" if ok_src else f"<span style='color:#a00'>{why}</span>")
        self.btn_preview.setEnabled(self._extent is not None and ok_src)
        model_ok = Path(self.model_edit.text().strip() or "/nonexistent").is_file()
        out_ok = (not self.cb_write.isChecked()) or bool(self.out_edit.text().strip())
        can_run = bool(self._extent is not None and ok_src and model_ok
                       and self._confirmed and out_ok and self._task is None)
        self.btn_run.setEnabled(can_run)
        if not self._confirmed and self._extent is not None and ok_src:
            self.lbl_status.setText(
                "Render and confirm the preview in section 3 before generating.")

    # ------------------------------------------------------------------ run --
    def _start(self):
        from gencp_core import extent as ext
        e, work, _ = ext.resolve(self._extent, self._crs)
        params = dict(
            extent_bbox=self._extent, crs=self._crs,
            model_path=self.model_edit.text().strip(),
            out_tif=self.out_edit.text().strip() if self.cb_write.isChecked() else None,
            pbf=self._pbf_or_none(), base_product="clcplus",
            overlap_m=float(self.overlap_box.currentData()),
        )
        clc = self.clc_edit.text().strip()
        if clc:
            os.environ["GENCP_CLC_PATH"] = clc
            try:
                from gencp_core import vectors
                vectors.CLC_PATH = Path(clc)  # honoured via GENCP_CLC_PATH too
            except Exception:                        # noqa: BLE001
                pass

        from .task import GenerateTask
        self._task = GenerateTask("GenCP synthetic reference", params)
        self._task.progressChanged.connect(
            lambda: (self.progress.setValue(int(self._task.progress())),
                     self.lbl_status.setText(self._task.message)))
        self._task.taskCompleted.connect(self._done)
        self._task.taskTerminated.connect(self._failed)
        self.btn_run.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.lbl_status.setText("Running on a background task — QGIS stays responsive.")
        QgsApplication.taskManager().addTask(self._task)

    def _cancel(self):
        if self._task is not None:
            self._task.cancel()
            self.lbl_status.setText("Cancelling…")

    def _done(self):
        task, self._task = self._task, None
        res = task.result or {}
        self.progress.setValue(100)
        out = res.get("output")
        msgs = []
        if out:
            msgs.append(f"wrote {out}")
            if self.cb_add_layer.isChecked():
                layer = QgsRasterLayer(out, Path(out).stem)
                if layer.isValid():
                    QgsProject.instance().addMapLayer(layer)
                    msgs.append("added as a layer")
                else:
                    msgs.append("layer failed to load")
        elif self.cb_add_layer.isChecked():
            msgs.append("nothing written to disk, so there is no file to add as a layer; "
                        "tick 'Write a GeoTIFF' to add the result to the map")
        seam = res.get("seam")
        if seam:
            msgs.append(f"seam energy ratio {seam['ratio']:.3f}")
        self.lbl_status.setText(" · ".join(msgs) or "Done.")
        self.btn_cancel.setEnabled(False)
        self._validate()
        self.iface.messageBar().pushMessage("GenCP", " · ".join(msgs), level=member(Qgis, 'Success'))

    def _failed(self):
        task, self._task = self._task, None
        self.btn_cancel.setEnabled(False)
        if task is not None and task.exception is not None:
            self.lbl_status.setText(f"Failed: {task.exception}")
            QMessageBox.critical(self, "Generation failed", str(task.exception))
        else:
            self.lbl_status.setText("Cancelled.")
        self._validate()
