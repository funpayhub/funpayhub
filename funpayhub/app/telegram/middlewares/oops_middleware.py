from __future__ import annotations


__all__ = [
    'OopsMiddleware',
]

from typing import Any, TypeVar
from collections.abc import Callable, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject
from aiogram.exceptions import TelegramRetryAfter

from loggers import telegram as logger
from funpayhub.lib.translater import Translater


T = TypeVar('T')


class OopsMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        # todo: move to error handler?

        translater: Translater = data['translater']

        try:
            await handler(event, data)

        except TelegramRetryAfter as e:
            if isinstance(event, CallbackQuery):
                await event.answer(
                    translater.translate('$oops_ratelimit').format(e.retry_after),
                    show_alert=True,
                )
                return

        except Exception:
            if isinstance(event, CallbackQuery):
                await event.answer(translater.translate('$oops'), show_alert=True)
            elif isinstance(event, Message):
                await event.reply(translater.translate('$oops'))
            logger.error('Caught an error!', exc_info=True)
            raise
