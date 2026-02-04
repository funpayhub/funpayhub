from __future__ import annotations


__all__ = [
    'ROUTERS',
    'MENUS',
    'BUTTONS',
]

from .ui.router import Router as ui_router
from .properties.router import Router as properties_router
from .properties.ui.builders import NodeMenuBuilder, NodeButtonBuilder, AddListItemMenuBuilder


ROUTERS = [ui_router, properties_router]
MENUS = [NodeMenuBuilder, AddListItemMenuBuilder]
BUTTONS = [NodeButtonBuilder]
