from __future__ import annotations

from typing import TYPE_CHECKING, Literal
from dataclasses import dataclass

from funpayhub.lib.telegram.fsm import StateFromQuery


if TYPE_CHECKING:
    from aiogram.types import Message


@dataclass
class ChangingMenuPage(StateFromQuery, identifier='fph:changin_page'):
    """
    Состояние смены страницы меню (клавиатуры).
    """

    mode: Literal['keyboard', 'text']
    """
    Режиме переключения страницы:
        'keyboard': переключаются страницы клавиатуры.
        'text': переключаются страницы текста.
    """

    max_pages: int
    """Максимальное кол-во страниц."""

    state_msg: Message
    """Объект сообщения, который был выслан вместе со стейтом."""
