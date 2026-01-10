from __future__ import annotations


__all__ = ['IsAuthorizedMiddleware']


from typing import Any
from collections.abc import Callable, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject
from funpayhub.loggers import telegram as logger

from funpayhub.app.properties import FunPayHubProperties


class IsAuthorizedMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ):
        if not isinstance(event, (Message, CallbackQuery)):
            return await handler(event, data)

        from_user = event.from_user
        properties: FunPayHubProperties = data['properties']

        if from_user.id not in properties.telegram.general.authorized_users.value:
            logger.warning(
                'Пользователь %s (%d) пытается получить доступ к Telegram боту!',
                from_user.username,
                from_user.id,
            )
            return None

        return await handler(event, data)
