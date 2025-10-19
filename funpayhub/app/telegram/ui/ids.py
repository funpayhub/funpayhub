from enum import StrEnum, UNIQUE, verify


@verify(UNIQUE)
class MenuIds(StrEnum):
    properties_entry = 'properties_entry'
    param_value_manual_input = 'param_value_manual_input'
    formatters_list = 'formatters_list'
    formatter_info = 'formatter_info'
    hooks_list = 'hooks_list'
    hook_info = 'hook_info'
    tg_chat_notifications = 'tg_chat_notifications'


@verify(UNIQUE)
class ButtonIds(StrEnum):
    properties_entry = 'properties_entry'
    formatters_list = 'formatters_list'
    formatter_info = 'formatter_info'
    hooks_list = 'hooks_list'
    hook_info = 'hook_info'
    tg_chat_notifications = 'tg_chat_notifications'
    tg_chat_notification_info = 'tg_chat_notification_info'
