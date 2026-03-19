from __future__ import annotations

from typing import TYPE_CHECKING
from dataclasses import dataclass

from funpayhub.lib.telegram.fsm import StateFromQuery


if TYPE_CHECKING:
    from aiogram.types import Message


@dataclass
class UploadingGoods(StateFromQuery, identifier='fph:uploading_goods'):
    source_id: str
    state_message: Message


@dataclass
class RemovingGoods(StateFromQuery, identifier='fph:removing_goods'):
    source_id: str
    state_message: Message


@dataclass
class AddingGoods(StateFromQuery, identifier='fph:adding_goods'):
    source_id: str
    state_message: Message


@dataclass
class AddingGoodsTxtSource(StateFromQuery, identifier='fph:adding_goods_txt_source'):
    state_message: Message
