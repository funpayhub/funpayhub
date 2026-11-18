from __future__ import annotations


__all__ = ['AccessControlMiddleware']

import html
import time
import random
import secrets
from typing import TYPE_CHECKING, Any
from contextlib import suppress
from collections.abc import Callable, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import (
    Message,
    CallbackQuery,
    TelegramObject,
    InputRichMessage,
    EphemeralMessageParameters,
)
from aiogram.exceptions import TelegramAPIError

from dothub.loggers import telegram_component as logger


if TYPE_CHECKING:
    from ..properties import TelegramProperties


SYSTEM_NOTIFICATIONS_PATH = ('system', 'system')
DENIAL_COOLDOWN = 3600
GITHUB_URL = 'https://github.com/funpayhub/funpayhub'
TELEGRAM_URL = 'https://t.me/funpay_hub'

FOOTER = (
    '<hr/>'
    '<footer>Хочешь такого же? '
    f'<a href="{GITHUB_URL}">💻 GitHub</a> · <a href="{TELEGRAM_URL}">💬 Telegram</a>'
    '</footer>'
)

ACCESS_GRANTED_TEXT = (
    '<table><tr><td align="center">'
    '🎉 <b>Доступ получен!</b><br/>Главное меню — /menu'
    '</td></tr></table>'
)

DENY_MESSAGES = (
    'Доступ закрыт. Клуб избранных сегодня без гостей.',
    'Извини, вход по спискам. Тебя там нет. Точно нет.',
    'Система посмотрела на тебя... и покачала головой.',
    'Доступ запрещён. Попробуй ещё раз. Где-нибудь в другом боте.',
    'Хорошая попытка. Но нет.',
    'Этот функционал доступен только тем, кому можно. Тебе не можно.',
    'Хаб вежливо делает вид, что вас здесь нет.',
    'Запрос отклонён без объяснения причин.',
    'Я бы пустил тебя… но не сегодня. И не завтра.',
    'Очень смело. Очень мимо.',
    'Попытка засчитана. Результат - отрицательный.',
    'Интерфейс вас не узнаёт. И не хочет.',
)

def access_denied_text() -> str:
    joke = html.escape(random.choice(DENY_MESSAGES))
    return f'<table><tr><td align="center">🔒 {joke}</td></tr></table>{FOOTER}'


class AccessControlMiddleware(BaseMiddleware):
    def __init__(self, properties: TelegramProperties) -> None:
        self._properties = properties
        self._notified_users: dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, (Message, CallbackQuery)):
            return await handler(event, data)

        user = event.from_user
        if user is None:
            return None

        if user.id in self._properties.bot.authorized_users.value:
            return await handler(event, data)

        if isinstance(event, CallbackQuery):
            if self._should_notify(user.id):
                await self._deny_callback(event)
            return None

        if event.chat.type != 'private':
            return None

        if self._is_password(event.text):
            await self._authorize(event)
            return None

        logger.warning(
            'User %s (%d) tried to access the Telegram bot via message.',
            user.username,
            user.id,
        )

        if self._should_notify(user.id):
            self._notified_users[user.id] = time.monotonic()
            await event.answer_rich(InputRichMessage(html=access_denied_text()))
        return None

    def _should_notify(self, user_id: int) -> bool:
        now = time.monotonic()
        if user_id not in self._notified_users:
            return True
        if now - self._notified_users[user_id] < DENIAL_COOLDOWN:
            return False
        del self._notified_users[user_id]
        return True

    async def _deny_callback(self, query: CallbackQuery) -> None:
        logger.warning(
            'User %s (%d) tried to access the Telegram bot via button.',
            query.from_user.username,
            query.from_user.id,
        )
        self._notified_users[query.from_user.id] = time.monotonic()
        try:
            await query.bot.send_rich_message(
                chat_id=None,
                rich_message=InputRichMessage(html=access_denied_text()),
                ephemeral_message_parameters=EphemeralMessageParameters(callback_query_id=query.id),
            )
        except Exception:
            logger.error('Unable to send an ephemeral denial message.', exc_info=True)

    def _is_password(self, text: str | None) -> bool:
        password = self._properties.bot.password.value
        if not password or not text:
            return False
        return secrets.compare_digest(text.encode(), password.encode())

    async def _authorize(self, message: Message) -> None:
        user = message.from_user
        assert user is not None

        await self._properties.bot.authorized_users.add_items(user.id)
        logger.warning(
            'User %s (%d) has been granted access to the Telegram bot.',
            user.username,
            user.id,
        )

        with suppress(TelegramAPIError):
            await message.delete()

        try:
            channel = self._properties.notifications.get_channel(
                SYSTEM_NOTIFICATIONS_PATH,
                from_root=True,
            )
            await channel.add_chat(message.chat.id, message.message_thread_id)
        except Exception:
            logger.error(
                'Unable to subscribe chat %d to system notifications.',
                message.chat.id,
                exc_info=True,
            )

        await message.answer_rich(InputRichMessage(html=ACCESS_GRANTED_TEXT))
