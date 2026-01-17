from __future__ import annotations
from typing import TYPE_CHECKING
from funpayhub.app.properties import FunPayHubProperties


if TYPE_CHECKING:
    from chat_sync.src.properties import ChatSyncProperties
    from chat_sync.src.types import BotRotater



async def is_setup(properties: FunPayHubProperties, chat_sync_rotater: BotRotater) -> bool:
    pl_props: ChatSyncProperties = properties.get_properties(['chat_sync'])  # type: ignore
    if not pl_props.sync_chat_id:
        return False
    if len(chat_sync_rotater) < 4:
        return False

    return True