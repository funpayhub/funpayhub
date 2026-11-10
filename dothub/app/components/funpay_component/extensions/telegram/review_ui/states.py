from __future__ import annotations

from dataclasses import dataclass

from hubplatform.telegram.fsm import State


@dataclass
class EnteringReviewChatReply(
    State,
    identifier='app:funpay_component:telegram_extension:review:entering_review_chat_reply',
):
    chat_id: int
    session_id: str | None = None


@dataclass
class EnteringReviewReply(
    State,
    identifier='app:funpay_component:telegram_extension:review:entering_review_reply',
):
    order_id: str
    session_id: str | None = None
