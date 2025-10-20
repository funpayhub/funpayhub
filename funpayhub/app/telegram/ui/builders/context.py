from funpayhub.lib.telegram.ui import MenuContext
from dataclasses import dataclass, field
from funpaybotengine.types import Message


@dataclass(kw_only=True)
class NewMessageMenuContext(MenuContext):
    funpay_chat_name: str
    funpay_chat_id: int
    messages: list[Message] = field(default_factory=list)
