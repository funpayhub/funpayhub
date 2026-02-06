from __future__ import annotations


__all__ = [
    'router',
    'MENUS',
]


from .ui import PluginInfoMenuBuilder, PluginsListMenuBuilder
from .router import router


MENUS = [
    PluginsListMenuBuilder,
    PluginInfoMenuBuilder,
]
