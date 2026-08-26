"""Qt5/Qt6 enum compatibility.

QGIS 3.x ships PyQt5, where enum members are attributes of the class itself
(`Qt.AlignCenter`). QGIS 4.x ships PyQt6, where they live in a nested scoped enum
(`Qt.AlignmentFlag.AlignCenter`) and the flat name is gone. The plugin supports both, so
enum members are looked up through `member()` instead of being written one way and
crashing on the other.

This is a shell concern, not a generation concern, which is why it lives here and not in
gencp_core.
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
