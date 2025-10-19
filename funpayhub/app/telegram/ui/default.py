from .builders.properties_ui import entry_menu_builder, entry_button_builder, builders
from .builders import formatters_ui, notifications_ui
from .ids import MenuIds, ButtonIds


MENU_BUILDERS = {
    MenuIds.properties_entry: entry_menu_builder,
    MenuIds.param_value_manual_input: builders.param_value_manual_input_menu_builder,
    MenuIds.formatters_list: formatters_ui.formatters_list_menu_builder,
    MenuIds.formatter_info: formatters_ui.formatter_info_menu_builder,
    MenuIds.tg_chat_notifications: notifications_ui.current_chat_notifications_menu_builder,
}


BUTTON_BUILDERS = {
    ButtonIds.properties_entry: entry_button_builder,
}


MENU_MODIFICATIONS = {
    MenuIds.properties_entry: {
        'fph:main_properties_menu_modification': (
            builders.PropertiesMenuModification.filter,
            builders.PropertiesMenuModification.modification
        )
    }
}