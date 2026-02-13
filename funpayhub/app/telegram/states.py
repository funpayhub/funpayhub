from __future__ import annotations

from dataclasses import dataclass

from aiogram.types import Message

from funpayhub.lib.telegram.fsm import State


@dataclass
class SendingFunpayMessage(State, identifier='fph:sending_funpay_message'):
    message: Message
    to: int | str


@dataclass
class SendingReviewReply(State, identifier='fph:sending_review_reply'):
    message: Message
    order_id: str
