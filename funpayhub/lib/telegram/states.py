from __future__ import annotations

from dataclasses import field, dataclass

from aiogram.types import Message, CallbackQuery
from typing import Any

from funpayhub.lib.properties import MutableParameter, ListParameter
from funpayhub.lib.telegram.callback_data import CallbackData, UnknownCallback


class State:
    name: str = field(init=False, repr=False, default='state')


@dataclass
class ChangingParameterValueState(State):
    name: str = field(init=False, repr=False, default='changing_parameter_value')

    parameter: MutableParameter[Any]
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


@dataclass
class AddingListItem(State):
    name: str = field(init=False, repr=False, default='adding_list_item')

    parameter: ListParameter[Any]
    callback_query_obj: CallbackQuery
    callback_data: UnknownCallback
    message: Message
    user_messages: list[Message] = field(default_factory=list)