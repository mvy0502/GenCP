# ============================================================================
# GenCP - QGIS Python ortam raporu
#
# NASIL CALISTIRILIR
#   1. QGIS'te  Eklentiler > Python Konsolu  menusunu acin.
#   2. Bu dosyanin TAMAMINI kopyalayip konsola yapistirin ve Enter'a basin.
#   3. Ciktinin tamamini (veya masaustunuzde olusan gencp_ortam_raporu.txt
#      dosyasini) geri gonderin.
#
# Hicbir sey kurmaz, hicbir seyi degistirmez, internet gerektirmez.
# Eksik paket HATA VERMEZ - eksik oldugunu yazar; olcmek istedigimiz sey budur.
# ============================================================================
def _gencp_ortam_raporu():
    import sys, os, platform
    L = []
    def p(s=""):
        L.append(str(s)); print(s)

    p("=" * 62)
    p("GenCP ORTAM RAPORU")
    p("=" * 62)

    # --- interpreter -------------------------------------------------------
    p("python      : %s" % sys.version.split()[0])
    p("version_info: %s" % (tuple(sys.version_info)[:3],))
    try:
        import sysconfig
        abi = "cp%s%s" % (sys.version_info[0], sys.version_info[1])
        p("abi tag     : %s   platform=%s" % (abi, sysconfig.get_platform()))
    except Exception as e:
        p("abi tag     : ? (%s)" % type(e).__name__)
    p("machine     : %s   system=%s %s" % (platform.machine(), platform.system(),
                                           platform.release()))
    p("executable  : %s" % sys.executable)
    try:
        import site
        p("user site   : %s" % site.getusersitepackages())
    except Exception as e:
        p("user site   : ? (%s)" % type(e).__name__)

    # --- QGIS / Qt ---------------------------------------------------------
    try:
        from qgis.core import Qgis
        p("QGIS        : %s" % Qgis.QGIS_VERSION)
    except Exception as e:
        p("QGIS        : ? (%s)" % type(e).__name__)
    try:
        from qgis.PyQt.QtCore import QT_VERSION_STR, PYQT_VERSION_STR
        p("Qt / PyQt   : %s / %s" % (QT_VERSION_STR, PYQT_VERSION_STR))
    except Exception as e:
        p("Qt / PyQt   : ? (%s)" % type(e).__name__)

    # --- the measurement: which packages exist, and WHERE -------------------
    p("-" * 62)
    p("PAKETLER (VAR/YOK ve nereden geldigi)")
    for name in ("rasterio", "onnxruntime", "osmium", "numpy", "shapely", "pyproj"):
        try:
            m = __import__(name)
            ver = getattr(m, "__version__", getattr(m, "version", "?"))
            loc = getattr(m, "__file__", "?") or "?"
            p("  VAR  %-12s %-10s %s" % (name, str(ver)[:10], loc))
        except BaseException as e:
            p("  YOK  %-12s %s: %s" % (name, type(e).__name__, str(e)[:44]))

    # --- sys.path ----------------------------------------------------------
    p("-" * 62)
    p("sys.path (%d girdi)" % len(sys.path))
    for entry in sys.path:
        p("  %s" % (entry if entry else "(bos)"))
    p("=" * 62)

    # --- write it out so it can be copied off the machine -------------------
    for target in (os.path.join(os.path.expanduser("~"), "Desktop"),
                   os.path.expanduser("~"), os.getcwd()):
        try:
            f = os.path.join(target, "gencp_ortam_raporu.txt")
            with open(f, "w") as fh:
                fh.write("\n".join(L))
            p("Rapor dosyasi: %s" % f)
            break
        except BaseException:
            continue
    return "\n".join(L)

_gencp_ortam_raporu()
