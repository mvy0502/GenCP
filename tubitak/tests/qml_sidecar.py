"""Does the .qml sidecar make a FRESH QGIS draw the file, or a blend of it?

This deliberately does NOT construct the plugin dialog. `_draw_rgb_opaque` fixes our own
renderer, which helps only people who generate through our dialog. The sidecar is the part
that has to work for someone who receives the .tif and opens it any other way, so this
loads the raster the way that person would - QgsRasterLayer over a contrasting background -
and measures what QGIS actually paints against what the file actually stores.

Magenta is the background because it appears nowhere in the imagery: any of it that reaches
the rendered pixels is blending, and it is unmistakable.

    QT_QPA_PLATFORM=offscreen GENCP_REPO_ROOT=$PWD \
      /Applications/QGIS-final-4_2_1.app/Contents/MacOS/QGIS-final-4_2_1 \
      --nologo --code tubitak/tests/qml_sidecar.py
"""
import os
import sys
from pathlib import Path

try:
    ROOT = Path(__file__).resolve().parents[2]
except NameError:                                  # pragma: no cover - --code path
    ROOT = Path(os.environ.get("GENCP_REPO_ROOT", os.getcwd())).resolve()
sys.path.insert(0, str(ROOT / "tubitak"))

OUT = Path(os.environ.get("GENCP_TEST_OUT", "/tmp/qml_sidecar.txt"))
_lines, _n, _bad = [], 0, 0


def check(what, ok, detail=""):
    global _n, _bad
    _n += 1
    if not ok:
        _bad += 1
    _lines.append(f"  [{'PASS' if ok else 'FAIL'}] {what}" + (f"  - {detail}" if detail else ""))


def render(layer):
    """What QGIS paints, over magenta, at the layer's own resolution."""
    import numpy as np
    from qgis.core import QgsMapSettings, QgsMapRendererParallelJob
    from qgis.PyQt.QtCore import QSize
    from qgis.PyQt.QtGui import QColor, QImage
    ms = QgsMapSettings()
    ms.setLayers([layer])
    ms.setBackgroundColor(QColor(255, 0, 255))
    ms.setOutputSize(QSize(layer.width(), layer.height()))
    ms.setExtent(layer.extent())
    ms.setDestinationCrs(layer.crs())
    job = QgsMapRendererParallelJob(ms)
    job.start()
    job.waitForFinished()
    im = job.renderedImage().convertToFormat(QImage.Format.Format_RGB32)
    ptr = im.bits()
    ptr.setsize(im.sizeInBytes())
    a = np.frombuffer(ptr, np.uint8).reshape(im.height(), im.bytesPerLine() // 4, 4)
    # .astype COPIES. Returning the bare slice returns a VIEW into the QImage's buffer,
    # which Qt frees when the image is collected - the first render then silently became
    # garbage as soon as the second one reused the memory, and this test reported 57 DN
    # against a file that renders at 2.31. A measurement tool holding a dangling pointer
    # is worse than no measurement, because it produces a number.
    return a[:, :im.width(), :3][:, :, ::-1].astype(float)


def main():
    import numpy as np
    import rasterio
    from qgis.core import QgsRasterLayer
    from gencp_core import mosaic

    tif = Path(os.environ.get("GENCP_QML_TIF",
                              ROOT / "tubitak/data/demo_out/gencp_reference.tif"))
    if not tif.exists():
        check("a 4-band output exists to test against", False, str(tif))
        return
    qml = tif.with_suffix(".qml")

    with rasterio.open(tif) as s:
        stored = np.moveaxis(s.read([1, 2, 3]), 0, -1).astype(float)
        nb, ci = s.count, [str(c).split(".")[-1] for c in s.colorinterp]
        alpha = s.read(4).astype(float) if nb >= 4 else None
    check("the file under test really carries an alpha band", nb >= 4,
          f"{nb} bands, colorinterp {ci}")
    if alpha is not None:
        check("and that alpha would visibly blend if honoured",
              alpha.max() < 255,
              f"alpha min {alpha.min():.0f} max {alpha.max():.0f} mean {alpha.mean():.1f}; "
              f"fully opaque pixels {(alpha >= 255).mean()*100:.1f}%")

    # 1. WITHOUT the sidecar: establishes that this measurement can fail.
    stash = None
    if qml.exists():
        stash = qml.read_text()
        qml.unlink()
    lay_before = QgsRasterLayer(str(tif), "no_qml", "gdal")   # strong reference held
    before = render(lay_before)
    d_before = float(np.abs(before - stored).mean())
    magenta_before = float(((before[:, :, 0] > 200) & (before[:, :, 1] < 60)
                            & (before[:, :, 2] > 200)).mean() * 100)

    # 2. WITH it, written by the shipping code path rather than by this test.
    mosaic.write_qml_sidecar(tif)
    check("write_qml_sidecar produced the file QGIS looks for", qml.exists(), qml.name)
    lay_after = QgsRasterLayer(str(tif), "with_qml", "gdal")  # strong reference held
    after = render(lay_after)
    d_after = float(np.abs(after - stored).mean())
    magenta_after = float(((after[:, :, 0] > 200) & (after[:, :, 1] < 60)
                           & (after[:, :, 2] > 200)).mean() * 100)

    _lines.append("")
    _lines.append("  mean |what QGIS draws - the RGB stored in the file|, over magenta:")
    _lines.append(f"    without the .qml : {d_before:8.2f} DN   "
                  f"(pure-magenta pixels {magenta_before:.2f}%)")
    _lines.append(f"    with the .qml    : {d_after:8.2f} DN   "
                  f"(pure-magenta pixels {magenta_after:.2f}%)")
    inner = np.abs(after - stored)[10:-10, 10:-10]
    _lines.append(f"    with the .qml, interior only: {inner.mean():.2f} DN, "
                  f"max {inner.max():.0f} DN, "
                  f"{(inner.mean(axis=2) > 8).mean()*100:.2f}% of pixels over 8 DN")
    _lines.append("")

    check("the measurement can fail: without the sidecar the render is a blend",
          d_before > 20.0, f"{d_before:.2f} DN")
    check("with the sidecar QGIS draws the stored RGB", d_after < 5.0, f"{d_after:.2f} DN")
    check("and no background bleeds through", magenta_after < 0.01,
          f"{magenta_after:.4f}% pure magenta")

    if stash is not None:
        qml.write_text(stash)


try:
    main()
except Exception:                                  # noqa: BLE001
    import traceback
    _lines.append("  [FAIL] harness crashed")
    _lines.append(traceback.format_exc())
    _bad += 1

_lines.append("=" * 72)
_lines.append(f"{_n - _bad}/{_n} checks passed")
_lines.append("=" * 72)
OUT.write_text("\n".join(_lines))
print("\n".join(_lines))
os._exit(2 if _bad else 0)
