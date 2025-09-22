from __future__ import annotations

from dataclasses import field, dataclass

from aiogram.types import Message, CallbackQuery

from funpayhub.lib.properties import MutableParameter


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
class ChangingPage(State):
    name: str = field(init=False, repr=False, default='changing_page')

    callback_query_obj: CallbackQuery
    callbacks_history: list[str]
    message: Message
    max_pages: int
    user_messages: list[Message]
