from __future__ import annotations

from dataclasses import field, dataclass

from aiogram.types import Message, CallbackQuery

from funpayhub.lib.properties import MutableParameter
from funpayhub.lib.telegram.callbacks import SelectPage


class State:
    name: str = field(init=False, repr=False, default='state')


@dataclass
class ChangingParameterValueState(State):
    name: str = field(init=False, repr=False, default='changing_parameter_value')

    parameter: MutableParameter
    page: int
    menu_message: Message
    message: Message
    user_messages: list[Message]


@dataclass
class ChangingPage(State):
    name: str = field(init=False, repr=False, default='changing_page')

    query: CallbackQuery
    unpacked_query: SelectPage
    message: Message
    user_messages: list[Message]
