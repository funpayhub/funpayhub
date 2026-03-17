from __future__ import annotations

from typing import TYPE_CHECKING
from dataclasses import field

from funpayhub.lib.telegram.ui import MenuContextModel


if TYPE_CHECKING:
    from funpaybotengine.types import Message
    from funpaybotengine.dispatching.events import ReviewEvent


class NewMessageMenuContext(MenuContextModel):
    funpay_chat_name: str
    funpay_chat_id: int
    messages: list[Message] = field(default_factory=list)


class SendMessageMenuContext(MenuContextModel):
    funpay_chat_id: int | str
    funpay_chat_name: str


class FunPayStartNotificationMenuContext(MenuContextModel):
    error: Exception | None = None


class StateUIContext(MenuContextModel):
    text: str
    delete_on_clear: bool = True
    open_previous_on_clear: bool = False


class NewReviewNotificationMenuContext(MenuContextModel):
    review_event: ReviewEvent
