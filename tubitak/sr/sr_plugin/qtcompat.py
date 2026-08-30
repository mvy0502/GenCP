"""Qt5/Qt6 enum compatibility.

QGIS 3.x ships PyQt5, where enum members are attributes of the class itself
(`Qt.AlignCenter`). QGIS 4.x ships PyQt6, where they live in a nested scoped enum
(`Qt.AlignmentFlag.AlignCenter`) and the flat name is gone. Enum members are therefore
looked up through `member()` instead of being written one way and crashing on the other.

This is a byte-for-byte reimplementation of the same helper in `tubitak/qgis_plugin`.
It is duplicated rather than imported ON PURPOSE: importing it would make this plugin
depend on Project 1's plugin package being present and importable, which would couple two
plugins that must be installable independently. The duplication is 15 lines and is the
cheaper of the two costs.
"""
from __future__ import annotations
import enum


def member(cls, name):
    """Return the enum member `name` from `cls`, Qt5-flat or Qt6-scoped."""
    v = getattr(cls, name, None)
    if v is not None:
        return v
    for attr in dir(cls):
        sub = getattr(cls, attr, None)
        if isinstance(sub, type) and issubclass(sub, enum.Enum):
            v = getattr(sub, name, None)
            if v is not None:
                return v
    raise AttributeError(f"{cls.__name__} has no enum member {name!r} (Qt5 or Qt6)")
