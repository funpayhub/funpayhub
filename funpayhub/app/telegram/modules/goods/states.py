from __future__ import annotations

from typing import TYPE_CHECKING
from dataclasses import dataclass

from aiogram.types import Message

from funpayhub.lib.telegram.fsm import State


if TYPE_CHECKING:
    from funpayhub.lib.telegram.callback_data import UnknownCallback


@dataclass
class UploadingGoods(State, identifier='fph:uploading_goods'):
    source_id: str
    message: Message
    callback_data: UnknownCallback


@dataclass
class RemovingGoods(State, identifier='fph:removing_goods'):
    source_id: str
    message: Message
    callback_data: UnknownCallback


@dataclass
class AddingGoods(State, identifier='fph:adding_goods'):
    source_id: str
    message: Message
    callback_data: UnknownCallback


@dataclass
class AddingGoodsTxtSource(State, identifier='fph:adding_goods_txt_source'):
    message: Message
    callback_data: UnknownCallback
