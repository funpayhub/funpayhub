from __future__ import annotations

from typing import TYPE_CHECKING, Literal
from dataclasses import dataclass

from funpayhub.lib.telegram.fsm import State


if TYPE_CHECKING:
    from aiogram.types import Message, CallbackQuery

    from funpayhub.lib.telegram.callback_data import UnknownCallback


@dataclass
class ChangingMenuPage(State, identifier='fph:changin_page'):
    """
    Состояние смены страницы меню (клавиатуры).
    """

    mode: Literal['keyboard', 'text']
    """
    Режиме переключения страницы:
        'keyboard': переключаются страницы клавиатуры.
        'text': переключаются страницы текста.
    """

    query: CallbackQuery
    """Query, вызвавший состояние."""

    message: Message
    """Объект сообщения, который был выслан вместе со стейтом."""

    max_pages: int
    """Максимальное кол-во страниц."""

    callback_data: UnknownCallback = ...
    """Спарсенный query."""

    def __post_init__(self):
        if self.callback_data is Ellipsis:
            if hasattr(self.query, '__parsed__'):
                self.callback_data = getattr(self.query, '__parsed__')
            else:
                self.callback_data = UnknownCallback.parse(self.query.data)
