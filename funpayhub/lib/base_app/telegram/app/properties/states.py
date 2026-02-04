from __future__ import annotations

from typing import TYPE_CHECKING, Any
from dataclasses import dataclass

from funpayhub.lib.telegram.fsm import State


if TYPE_CHECKING:
    from aiogram.types import Message, CallbackQuery

    from funpayhub.lib.properties import ListParameter, MutableParameter
    from funpayhub.lib.telegram.callback_data import UnknownCallback


@dataclass
class ChangingParameterValue(State, identifier='fph:changing_parameter_value'):
    parameter: MutableParameter[Any]
    query: CallbackQuery
    message: Message
    callback_data: UnknownCallback = ...

    def __post_init__(self):
        if self.callback_data is Ellipsis:
            if hasattr(self.query, '__parsed__'):
                self.callback_data = getattr(self.query, '__parsed__')
            else:
                self.callback_data = UnknownCallback.parse(self.query.data)


@dataclass
class AddingListItem(State, identifier='fph:adding_list_item'):
    parameter: ListParameter[Any]
    query: CallbackQuery
    message: Message
    callback_data: UnknownCallback = ...

    def __post_init__(self):
        if self.callback_data is Ellipsis:
            if hasattr(self.query, '__parsed__'):
                self.callback_data = getattr(self.query, '__parsed__')
            else:
                self.callback_data = UnknownCallback.parse(self.query.data)
