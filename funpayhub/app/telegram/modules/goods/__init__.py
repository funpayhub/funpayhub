from __future__ import annotations


__all__ = [
    'router',
    'MENUS',
    'MENUS_MODS',
]


from funpayhub.app.telegram.ui.ids import MenuIds

from .ui import (
    GoodsSourceInfoMenuBuilder,
    GoodsSourcesListMenuBuilder,
    AddRemoveButtonToGoodsSourceInfoModification,
)
from .router import router


MENUS = [
    GoodsSourcesListMenuBuilder,
    GoodsSourceInfoMenuBuilder,
]


MENUS_MODS = {
    MenuIds.goods_source_info: [AddRemoveButtonToGoodsSourceInfoModification],
}
