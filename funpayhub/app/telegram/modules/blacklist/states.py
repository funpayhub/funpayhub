from __future__ import annotations
from funpayhub.lib.telegram.fsm import StateFromQuery
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aiogram.types import Message


@dataclass
class BlockingUser(StateFromQuery, identifier='blocking_user'):
    state_msg: Message

