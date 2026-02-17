from __future__ import annotations


__all__ = [
    'InstallingZipPlugin',
]


from typing import TYPE_CHECKING
from dataclasses import dataclass

from funpayhub.lib.telegram.fsm import State, StateFromQuery


if TYPE_CHECKING:
    from aiogram.types import Message, CallbackQuery

    from funpayhub.lib.telegram.callback_data import UnknownCallback


@dataclass
class InstallingZipPlugin(State, identifier='fph:installing_zip_plugin'):
    message: Message
    callback_query_obj: CallbackQuery
    callback_data: UnknownCallback


@dataclass
class AddingRepository(StateFromQuery, identifier='fph:adding_repository'):
    state_message: Message
