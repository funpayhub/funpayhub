from __future__ import annotations


__all__ = [
    'router',
    'MENUS',
    'MENU_MODS',
]

from funpayhub.app.telegram.ui.ids import MenuIds

from .ui import (
    AddOfferButtonModification,
    AddAutoDeliveryRuleMenuBuilder,
    NewSaleNotificationMenuBuilder,
    ReplaceSourcesListButtonModification,
    AutoDeliveryGoodsSourcesListMenuBuilder,
    AddRemoveButtonToAutoDeliveryModification,
)
from .router import router


MENUS = [
    AddAutoDeliveryRuleMenuBuilder,
    AutoDeliveryGoodsSourcesListMenuBuilder,
    NewSaleNotificationMenuBuilder,
]

MENU_MODS = {
    MenuIds.props_node: [
        AddOfferButtonModification,
        AddRemoveButtonToAutoDeliveryModification,
        ReplaceSourcesListButtonModification,
    ],
}
