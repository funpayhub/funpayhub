from __future__ import annotations

from typing import TYPE_CHECKING
from dataclasses import dataclass

from funpayhub.lib.telegram.fsm import StateFromQuery


if TYPE_CHECKING:
    from aiogram.types import Message


@dataclass
class AddingAutoDeliveryRule(StateFromQuery, identifier='fph:adding_autodelivery_rule'):
    state_message: Message


@dataclass
class BindingGoodsSource(StateFromQuery, identifier='fph:binding_goods_source'):
    state_message: Message
    rule: str
