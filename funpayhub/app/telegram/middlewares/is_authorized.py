from __future__ import annotations


__all__ = ['IsAuthorizedMiddleware']


import random
from typing import Any
from collections.abc import Callable, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject

from loggers import telegram as logger
from funpayhub.app.properties import FunPayHubProperties


messages = [
    'Доступ закрыт. Клуб избранных сегодня без гостей.',
    'Упс. Кажется, это меню не для тебя.',
    'Извините, вход по спискам. Тебя там нет. Точно нет.',
    'Система посмотрела на тебя... и покачала головой.',
    'Доступ запрещён. Попробуй ещё раз. Где-нибудь в другом боте.',
    'Хорошая попытка. Но нет.',
    'Этот функционал доступен только тем, кому можно. Тебе не можно.',
    'Хаб вежливо делает вид, что вас здесь нет.',
    'Запрос отклонён. Без объяснения причин.',
    'Я бы пустил тебя… но не сегодня. И не завтра.',
    'Очень смело. Очень мимо.',
    'Попытка засчитана. Результат — отрицательный.',
    'Интерфейс вас не узнаёт. И не хочет.',
]


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
            if isinstance(event, CallbackQuery):
                await event.answer(random.choice(messages), show_alert=True)
            return None

        return await handler(event, data)
