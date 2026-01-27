from __future__ import annotations

from typing import TYPE_CHECKING
from dataclasses import field, dataclass

from funpaybotengine.types import Message

from funpayhub.lib.telegram.ui import MenuContext


if TYPE_CHECKING:
    from updater import UpdateInfo


@dataclass(kw_only=True)
class NewMessageMenuContext(MenuContext):
    funpay_chat_name: str
    funpay_chat_id: int
    messages: list[Message] = field(default_factory=list)


@dataclass(kw_only=True)
class SendMessageMenuContext(MenuContext):
    funpay_chat_id: int | str
    funpay_chat_name: str


@dataclass(kw_only=True)
class UpdateMenuContext(MenuContext):
    update_info: UpdateInfo | None = None


@dataclass(kw_only=True)
class InstallUpdateMenuContext(MenuContext):
    instance_id: str


@dataclass(kw_only=True)
class PluginMenuContext(MenuContext):
    plugin_id: str


@dataclass(kw_only=True)
class FunPayStartNotificationMenuContext(MenuContext):
    error: Exception | None = None


@dataclass(kw_only=True)
class GoodsInfoMenuContext(MenuContext):
    source_id: str


@dataclass(kw_only=True)
class StateUIContext(MenuContext):
    text: str
    delete_on_clear: bool = True
    open_previous_on_clear: bool = False