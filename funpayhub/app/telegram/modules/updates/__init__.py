from __future__ import annotations


__all__ = [
    'router',
    'MENUS',
]


from .ui import UpdateMenuBuilder, InstallUpdateMenuBuilder
from .router import router


MENUS = [
    UpdateMenuBuilder,
    InstallUpdateMenuBuilder,
]
