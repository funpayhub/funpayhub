from __future__ import annotations

from dataclasses import field, dataclass

from aiogram.types import Message, CallbackQuery

from funpayhub.lib.properties import MutableParameter
from funpayhub.lib.telegram.callback_data import CallbackData


class State:
    name: str = field(init=False, repr=False, default='state')


@dataclass
class ChangingParameterValueState(State):
    name: str = field(init=False, repr=False, default='changing_parameter_value')

    parameter: MutableParameter
    callback_query_obj: CallbackQuery
    callbacks_history: list[str]
    message: Message
    user_messages: list[Message]


@dataclass
class ChangingMenuPage(State):
    name: str = field(init=False, repr=False, default='changing_menu_page')

    callback_query_obj: CallbackQuery
    callback_data: CallbackData
    message: Message
    max_pages: int
    user_messages: list[Message]


@dataclass
class ChangingViewPage(State):
    name: str = field(init=False, repr=False, default='changing_view_page')

    callback_query_obj: CallbackQuery
    callback_data: CallbackData
    message: Message
    max_pages: int
    user_messages: list[Message]
