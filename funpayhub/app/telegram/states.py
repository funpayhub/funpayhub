from __future__ import annotations

from dataclasses import dataclass

from aiogram.types import Message

from funpayhub.lib.telegram.fsm import StateFromQuery


@dataclass
class SendingFunpayMessage(StateFromQuery, identifier='fph:sending_funpay_message'):
    state_msg: Message
    to: int | str
