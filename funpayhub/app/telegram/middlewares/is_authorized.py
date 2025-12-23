from __future__ import annotations


__all__ = ['IsAuthorizedMiddleware']


from typing import Any
from collections.abc import Callable, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject

from funpayhub.app.properties import FunPayHubProperties


class IsAuthorizedMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ):
        if isinstance(event, Message):
            from_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            from_id = event.from_user.id
        else:
            return await handler(event, data)

        properties: FunPayHubProperties = data['properties']

        if from_id not in properties.telegram.general.authorized_users.value:
            return None

        return await handler(event, data)
