from __future__ import annotations


__all__ = ['MENU_MODS', 'MENUS', 'router']


from funpayhub.app.telegram.ui.ids import MenuIds

from .ui import (
    BindToOfferMenu,
    BindToOfferButtonModification,
    ReplaceNameWithOfferNameModification,
    AddRemoveButtonToFirstResponseModification,
)
from .router import router as router


MENU_MODS = {
    MenuIds.props_node: [
        BindToOfferButtonModification,
        AddRemoveButtonToFirstResponseModification,
        ReplaceNameWithOfferNameModification,
    ],
}

MENUS = [
    BindToOfferMenu,
]
