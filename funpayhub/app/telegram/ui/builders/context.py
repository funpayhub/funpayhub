from __future__ import annotations

from typing import TYPE_CHECKING
from dataclasses import field, dataclass

from funpaybotengine.types import Message

from funpayhub.lib.telegram.ui import MenuContext


if TYPE_CHECKING:
    from funpayhub.app.telegram.routers.my_chats import MyChats


@dataclass(kw_only=True)
class NewMessageMenuContext(MenuContext):
    funpay_chat_name: str
    funpay_chat_id: int
    messages: list[Message] = field(default_factory=list)


@dataclass(kw_only=True)
class SendMessageMenuContext(MenuContext):
    funpay_chat_id: int | str
    funpay_chat_name: str


@dataclass
class MyChatsMenuContext(MenuContext):
    chats: MyChats
