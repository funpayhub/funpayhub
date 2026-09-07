from __future__ import annotations


__all__ = ['MENU_MODS']


from funpayhub.app.telegram.ui.ids import MenuIds

from . import ui
from .router import router


MENU_MODS = {
    MenuIds.props_node: [
        ui.AddBlockUserButton,
        ui.AddRemoveUserButton,
    ],
}
