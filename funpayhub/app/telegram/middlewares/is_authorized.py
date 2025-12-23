from __future__ import annotations


__all__ = ['IsAuthorizedMiddleware']


from typing import TYPE_CHECKING, Any
from collections.abc import Callable, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject


if TYPE_CHECKING:
    from funpayhub.app.telegram.main import Telegram


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
            from_id = event.query.from_user.id
        else:
            return await handler(event, data)

        tg: Telegram = data['tg']

        if from_id not in tg.authorized_users:
            return None

        return await handler(event, data)
