from __future__ import annotations


__all__ = [
    'AddingCommand'
]


from typing import TYPE_CHECKING
from dataclasses import dataclass
from funpayhub.lib.telegram.fsm import State


if TYPE_CHECKING:
    from aiogram.types import Message
    from funpayhub.lib.telegram.callback_data import UnknownCallback


@dataclass
class AddingCommand(State, identifier='fph:adding_command'):
    message: Message
    callback_data: UnknownCallback