"""GenCP synthetic-reference QGIS plugin.

Shell only. Every line of generation logic lives in `gencp_core`, which imports neither
Qt nor QGIS, so the chain stays testable without QGIS running and reusable in an embedded
or offline context later.
"""


def classFactory(iface):
    from .plugin import GenCPPlugin
    return GenCPPlugin(iface)
