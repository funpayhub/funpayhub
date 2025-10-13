from __future__ import annotations
from enum import StrEnum, UNIQUE, verify


TOGGLE_PARAM_BTN = 'toggle_parameter'
"""
Данным ID обозначаются кнопки параметров-переключателей.
Формат: `toggle_parameter:path.to.parameter`
"""


@verify(UNIQUE)
class MenuIds(StrEnum):
    FORMATTERS_LIST = 'fph:formatters_list'
    FORMATTER_INFO = 'fph:formatter_info'
    TG_CHAT_NOTIFICATIONS = 'fph:current-chat-notifications'