from __future__ import annotations


__all__ = ['router', 'MENU_MODS']


from funpayhub.app.telegram.ui.ids import MenuIds

from .ui import AddCommandButtonModification, AddRemoveButtonToCommandModification
from .router import router


MENU_MODS = {
    MenuIds.props_node: [
        AddCommandButtonModification,
        AddRemoveButtonToCommandModification,
    ],
}
