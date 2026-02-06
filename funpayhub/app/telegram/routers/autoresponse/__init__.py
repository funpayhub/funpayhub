__all__ = ['router', 'MENU_MODS']


from .router import router
from .ui import AddCommandButtonModification, AddRemoveButtonToCommandModification
from funpayhub.app.telegram.ui.ids import MenuIds


MENU_MODS = {
    MenuIds.props_node: [
        AddCommandButtonModification,
        AddRemoveButtonToCommandModification,
    ],
}