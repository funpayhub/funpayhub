from __future__ import annotations

from dataclasses import field

from funpaybotengine.types import Message
from funpaybotengine.dispatching.events import ReviewEvent
from funpaybotengine.dispatching import SaleStatusChangedEvent

from funpayhub.lib.telegram.ui import MenuContext


class NewMessageMenuContext(MenuContext):
    funpay_chat_name: str
    funpay_chat_id: int
    messages: list[Message] = field(default_factory=list)


class SendMessageMenuContext(MenuContext):
    funpay_chat_id: int | str
    funpay_chat_name: str


class FunPayStartNotificationMenuContext(MenuContext):
    error: Exception | None = None


class StateUIContext(MenuContext):
    text: str
    delete_on_clear: bool = True
    open_previous_on_clear: bool = False


class NewReviewNotificationMenuContext(MenuContext):
    review_event: ReviewEvent


class SaleClosedNotificationMenuContext(MenuContext):
    sale_event: SaleStatusChangedEvent