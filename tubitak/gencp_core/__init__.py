"""gencp_core — the GenCP synthetic-reference generation chain, free of Qt and QGIS.

Nothing in this package imports `qgis` or `PyQt`. That is a hard rule, not tidiness:
the same core is what would run in an embedded or offline context later, and it is what
makes the chain testable without QGIS running. `tubitak/tests/test_no_qgis_imports.py`
enforces it.

Modules, in pipeline order:

    extent     read and validate a bbox + CRS, and lay out the tile grid
    vectors    OSM (local .osm.pbf or online Overpass) and CLC+ acquisition
    rasterize  the upstream rendering spec, lifted verbatim (Gate R: byte-identical)
    infer      ONNX inference over tiles
    mosaic     stitching, georeferencing, GeoTIFF write (Gate G: georeferencing contract)
"""
__all__ = ["extent", "vectors", "rasterize", "infer", "mosaic", "palette"]
TOOL_VERSION = "0.2.0"
