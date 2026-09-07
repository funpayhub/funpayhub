from __future__ import annotations


__all__ = [
    'InstallingZipPlugin',
]


from typing import TYPE_CHECKING
from dataclasses import dataclass

from funpayhub.lib.telegram.fsm import StateFromQuery


if TYPE_CHECKING:
    from aiogram.types import Message


@dataclass
class InstallingZipPlugin(StateFromQuery, identifier='fph:installing_zip_plugin'):
    state_message: Message


@dataclass
class AddingRepository(StateFromQuery, identifier='fph:adding_repository'):
    state_message: Message
