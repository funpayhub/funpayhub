from __future__ import annotations

from .ids import MenuIds
from .builders import other_ui, message_ui, formatters_ui, notifications_ui, control_ui
from .builders.properties_ui import builders
from .builders.properties_ui.registry import PropertiesEntryMenuBuilder, PropertiesEntryButtonBuilder


MENU_BUILDERS = (
    PropertiesEntryMenuBuilder,
    formatters_ui.FormatterListMenuBuilder,
    formatters_ui.FormatterInfoMenuBuilder,
    notifications_ui.NotificationsMenuBuilder,
    message_ui.NewMessageNotificationMenuBuilder,
    message_ui.SendMessageMenuBuilder,
    other_ui.AddCommandMenuBuilder,
    control_ui.ControlMenuBuilder,
)

# MENU_BUILDERS = {
#     MenuIds.properties_entry: (EntriesUIRegistry.build_menu, EntryMenuContext),
#     MenuIds.param_value_manual_input: (
#         builders.param_value_manual_input_menu_builder,
#         EntryMenuContext,
#     ),
#     MenuIds.formatters_list: (formatters_ui.formatters_list_menu_builder, MenuContext),
#     MenuIds.formatter_info: (formatters_ui.formatter_info_menu_builder, MenuContext),
#     MenuIds.tg_chat_notifications: (
#         notifications_ui.curr_chat_notifications_menu_builder,
#         MenuContext,
#     ),
#     MenuIds.new_funpay_message: (message_ui.message_menu_builder, NewMessageMenuContext),
#     MenuIds.add_list_item: (builders.add_list_item_menu_builder, EntryMenuContext),
#     MenuIds.add_command: (other_ui.add_command_menu_builder, MenuContext),
#     MenuIds.control: (control_ui.control_ui_menu_builder, MenuContext),
#     MenuIds.send_funpay_message: (message_ui.send_message_menu_builder, SendMessageMenuContext),
# }

BUTTON_BUILDERS = (
    PropertiesEntryButtonBuilder,
)

# BUTTON_BUILDERS = {
#     ButtonIds.properties_entry: (
#         EntriesUIRegistry.build_button,
#         EntryButtonContext,
#     ),
# }


MENU_MODIFICATIONS = {
    MenuIds.properties_entry: (
        builders.PropertiesMenuModification,
        builders.AddFormattersListButtonModification,
        builders.AddCommandButtonModification,
    )
}
