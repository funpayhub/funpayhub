from __future__ import annotations

from funpayhub.lib.translater import _


__all__ = ['IsAuthorizedMiddleware']


import random
from typing import Any
from collections.abc import Callable, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject

from funpayhub.loggers import telegram as logger

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


answered_users = set()


class IsAuthorizedMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ):
        if not isinstance(event, (Message, CallbackQuery)):
            return await handler(event, data)

        properties: FunPayHubProperties = data['properties']
        authorized = properties.telegram.general.authorized_users.value

        if event.from_user.id in authorized:
            return await handler(event, data)

        if isinstance(event, CallbackQuery):
            await event.answer(random.choice(messages), show_alert=True)
            return None

        if event.chat.type != 'private':
            return None

        if event.text == properties.telegram.general.password.value:
            logger.warning(
                _('Пользователь %s (%d) получил доступ к Telegram боту!'),
                event.from_user.username,
                event.from_user.id,
            )
            await properties.telegram.general.authorized_users.add_item(event.from_user.id)
            await properties.telegram.notifications.system.add_item(
                f'{event.chat.id}.{event.message_thread_id}',
            )
            await event.answer_animation(
                'CAACAgIAAyEFAASIhDzaAAEBtElpj7bfPSwOh-oXPd0AAROIKNIS8J8AAkiXAAI6nHhIKHcQ9ltBktA6BA',
            )
            await event.answer('Доступ получен!')
        else:
            logger.warning(
                _('Пользователь %s (%d) пытается получить доступ к Telegram боту!'),
                event.from_user.username,
                event.from_user.id,
            )
            if event.from_user.id not in answered_users:
                await event.answer(
                    '🔐 <b>Отправьте пароль, который вы вводили при первичной настройке FPH.</b>',
                )
                answered_users.add(event.from_user.id)
