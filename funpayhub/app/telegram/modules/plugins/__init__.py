from __future__ import annotations


__all__ = [
    'router',
    'MENUS',
]


from .ui import (
    RepoInfoMenuBuilder,
    ReposListMenuBuilder,
    PluginInfoMenuBuilder,
    PluginsListMenuBuilder,
    InstallPluginMenuBuilder,
    RepoPluginInfoMenuBuilder,
)
from .router import router


MENUS = [
    PluginsListMenuBuilder,
    PluginInfoMenuBuilder,
    ReposListMenuBuilder,
    RepoInfoMenuBuilder,
    RepoPluginInfoMenuBuilder,
    InstallPluginMenuBuilder,
]
