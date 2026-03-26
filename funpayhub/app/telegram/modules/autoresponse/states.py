from __future__ import annotations


__all__ = [
    'AddingCommand',
]


from typing import TYPE_CHECKING
from dataclasses import dataclass

from funpayhub.lib.telegram.fsm import StateFromQuery


if TYPE_CHECKING:
    from aiogram.types import Message


@dataclass
class AddingCommand(StateFromQuery, identifier='fph:adding_command'):
    state_message: Message
