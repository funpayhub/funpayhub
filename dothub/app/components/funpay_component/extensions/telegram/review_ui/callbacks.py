from __future__ import annotations

from hubplatform.telegram.callback_data import CallbackData


class AskRefund(CallbackData, identifier='app.fp.ask_refund'):
    order_id: str


class Refund(CallbackData, identifier='app.fp.refund'):
    order_id: str


class ReplyInChat(CallbackData, identifier='app.fp.repl_chat'):
    chat_id: int


class ReplyInReview(CallbackData, identifier='app.fp.repl_rev'):
    order_id: str
