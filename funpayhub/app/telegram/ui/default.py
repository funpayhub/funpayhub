from .builders.properties_ui import builders
from .builders.properties_ui.registry import PropertiesUIRegistry
from .builders.properties_ui.context import PropertiesMenuRenderContext, PropertiesButtonRenderContext
from funpayhub.lib.telegram.ui.types import MenuRenderContext, ButtonRenderContext
from .builders import formatters_ui, notifications_ui
from .ids import MenuIds, ButtonIds


MENU_BUILDERS = {
    MenuIds.properties_entry: (PropertiesUIRegistry.build_menu, PropertiesMenuRenderContext),
    MenuIds.param_value_manual_input: (builders.param_value_manual_input_menu_builder, PropertiesMenuRenderContext),
    MenuIds.formatters_list: (formatters_ui.formatters_list_menu_builder, MenuRenderContext),
    MenuIds.formatter_info: (formatters_ui.formatter_info_menu_builder, MenuRenderContext),
    MenuIds.tg_chat_notifications: (notifications_ui.current_chat_notifications_menu_builder, MenuRenderContext),
}


BUTTON_BUILDERS = {
    ButtonIds.properties_entry: (PropertiesUIRegistry.build_button, PropertiesButtonRenderContext),
}


MENU_MODIFICATIONS = {
    MenuIds.properties_entry: {
        'fph:main_properties_menu_modification': (
            builders.PropertiesMenuModification.filter,
            builders.PropertiesMenuModification.modification
        ),
        'fph:add_formatters_list_button_modification': (
            builders.AddFormattersListButtonModification.filter,
            builders.AddFormattersListButtonModification.modification
        ),
        'fph:add_command_button_modification': (
            builders.AddCommandButtonModification.filter,
            builders.AddCommandButtonModification.modification
        )
    },
}