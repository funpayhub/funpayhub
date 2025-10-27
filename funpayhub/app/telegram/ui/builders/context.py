from __future__ import annotations

from dataclasses import field, dataclass

from funpaybotengine.types import Message

from funpayhub.lib.telegram.ui import MenuContext


@dataclass(kw_only=True)
class NewMessageMenuContext(MenuContext):
    funpay_chat_name: str
    funpay_chat_id: int
    messages: list[Message] = field(default_factory=list)
