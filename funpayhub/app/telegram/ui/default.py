from .builders.properties_ui import entry_menu_builder, entry_button_builder
from .ids import MenuIds, ButtonIds


MENU_BUILDERS = {
    MenuIds.properties_entry: entry_menu_builder
}


BUTTON_BUILDERS = {
    ButtonIds.properties_entry: entry_button_builder,
}
