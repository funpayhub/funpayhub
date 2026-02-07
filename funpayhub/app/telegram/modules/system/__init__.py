from __future__ import annotations


__all__ = [
    'router',
    'MENUS',
]

from . import router
from .ui import ControlMenuBuilder


MENUS = [
    ControlMenuBuilder,
]
