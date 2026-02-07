from __future__ import annotations

from typing import TYPE_CHECKING
from dataclasses import dataclass

from funpayhub.lib.telegram.fsm import State, StateFromQuery
from funpayhub.lib.telegram.callback_data import UnknownCallback


if TYPE_CHECKING:
    from aiogram.types import Message


@dataclass
class AddingAutoDeliveryRule(State, identifier='fph:adding_autodelivery_rule'):
    message: Message
    callback_data: UnknownCallback


@dataclass
class BindingGoodsSource(StateFromQuery, identifier='fph:binding_goods_source'):
    rule: str
