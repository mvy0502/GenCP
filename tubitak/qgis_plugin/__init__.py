"""GenCP synthetic-reference QGIS plugin.

Shell only. Every line of generation logic lives in `gencp_core`, which imports neither
Qt nor QGIS, so the chain stays testable without QGIS running and reusable in an embedded
or offline context later.
"""


def _extend_path_for_vendored():
    """Make `_vendor/` importable, but ONLY for packages this machine does not already have.

    Windows institution machines have no internet, so the Windows build of this plugin ships
    `onnxruntime` and `osmium` unpacked in `_vendor/`. Two rules govern it:

    * **A vendored copy must LOSE to a real installation.** `find_spec` is asked first, and
      `_vendor` is added only for the packages it cannot find. A vendored copy that silently
      overrode a working install would be a new silent-failure class - exactly what this
      project exists to avoid. `find_spec` is used rather than `import` because importing
      onnxruntime here would undo the deferral that WP12 was about.
    * **`rasterio` is deliberately NOT vendored.** It ships its own GDAL, and QGIS has
      already loaded a different GDAL into the same process. Two GDALs in one process is a
      known crash class; a dependency the user installs by hand beats a QGIS that crashes.

    On builds without a `_vendor/` directory - the cross-platform zip, and a checkout - this
    is a no-op. Returns the list of names the vendored directory was added for.
    """
    import importlib.util
    import os
    import sys

    vendor = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_vendor")
    if not os.path.isdir(vendor):
        return []
    needed = []
    for name in ("onnxruntime", "osmium"):
        try:
            found = importlib.util.find_spec(name) is not None
        except BaseException:                        # noqa: BLE001
            found = False                            # a broken install counts as absent
        if not found:
            needed.append(name)
    if needed and vendor not in sys.path:
        # APPENDED, not inserted: even here the vendored directory is searched last.
        sys.path.append(vendor)
        if os.name == "nt" and hasattr(os, "add_dll_directory"):
            # Windows resolves a native extension's sibling DLLs through this list, not
            # through sys.path. Without it a vendored onnxruntime imports and then fails
            # on its own .pyd. UNVERIFIED: no Windows machine was available to test it.
            for sub in ("onnxruntime/capi", "osmium.libs"):
                d = os.path.join(vendor, *sub.split("/"))
                if os.path.isdir(d):
                    try:
                        os.add_dll_directory(d)
                    except BaseException:            # noqa: BLE001
                        pass
    return needed


def classFactory(iface):
    _extend_path_for_vendored()
    from .plugin import GenCPPlugin
    return GenCPPlugin(iface)
