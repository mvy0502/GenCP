"""GenCP super-resolution QGIS plugin (Project 2).

Shell only. Every line of super-resolution logic lives in `sr_core`, which imports neither
Qt nor QGIS, so the chain stays testable without QGIS running and the upsampler stays a
setting rather than a rewrite.

This is a SEPARATE plugin from `tubitak/qgis_plugin` (Project 1, synthetic reference).
Project 1's plugin is used here as a pattern and is not modified, not imported, and not
loaded by this one. Nothing here imports `gencp_core`.
"""


def classFactory(iface):
    from .plugin import GenCPSRPlugin
    return GenCPSRPlugin(iface)
