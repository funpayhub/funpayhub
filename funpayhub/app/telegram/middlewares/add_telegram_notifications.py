from __future__ import annotations

from typing import TYPE_CHECKING
from aiogram import BaseMiddleware
from aiogram.types import Message

if TYPE_CHECKING:
    from funpayhub.app.properties import FunPayHubProperties


class AddNotificationsSection(BaseMiddleware):
    async def __call__(self, handler, event: Message, data):
        props: FunPayHubProperties = data['properties']
        notification_key = f'{event.chat.id}_{event.message_thread_id}'
        if notification_key not in props.telegram.notifications.entries:
            props.telegram.notifications.add_chat(event.chat.id, event.message_thread_id)
            props.telegram.notifications.save(same_file_only=True)

        await handler(event, data)
