from __future__ import annotations


__all__ = [
    'TelegramApp',
    'MenuIds',
    'ButtonIds',
]

from .main import TelegramApp
from .app.properties.ui import NodeMenuIds, NodeButtonIds


class MenuIds(NodeMenuIds): ...


class ButtonIds(NodeButtonIds): ...
