from __future__ import annotations

from typing import Any, TYPE_CHECKING
from dataclasses import field, dataclass

from aiogram.types import Message, CallbackQuery

from funpayhub.lib.properties import ListParameter, MutableParameter
from funpayhub.lib.telegram.callback_data import CallbackData
import funpayhub.lib.telegram.callbacks as cbs
import warnings


class State:
    if TYPE_CHECKING:
        __identifier__: str


    def __init_subclass__(cls, **kwargs: Any) -> None:
        if 'identifier' not in kwargs:
            raise ValueError(
                f'identifier required, usage example: '
                f"`class {cls.__name__}(State, identifier='my_state'): ...`",
            )
        cls.__identifier__ = kwargs.pop('identifier')

        super().__init_subclass__(**kwargs)

    @property
    def name(self) -> str:
        warnings.warn('`.name` is deprecated. Use `.identifier`.', DeprecationWarning)
        return self.__identifier__

    @property
    def identifier(self) -> str:
        return self.__identifier__



@dataclass
class ChangingParameterValueState(State, identifier='changing_parameter_value'):
    parameter: MutableParameter[Any]
    callback_query_obj: CallbackQuery
    callbacks_history: list[str]
    message: Message
    user_messages: list[Message]


@dataclass
class ChangingMenuPage(State, identifier='changing_menu_page'):
    callback_query_obj: CallbackQuery
    callback_data: CallbackData
    message: Message
    max_pages: int
    user_messages: list[Message]


@dataclass
class ChangingViewPage(State, identifier='changing_view_page'):
    callback_query_obj: CallbackQuery
    callback_data: CallbackData
    message: Message
    max_pages: int
    user_messages: list[Message]


@dataclass
class AddingListItem(State, identifier='adding_list_item'):
    parameter: ListParameter[Any]
    callback_query_obj: CallbackQuery
    callback_data: cbs.ListParamAddItem
    message: Message
    user_messages: list[Message] = field(default_factory=list)
