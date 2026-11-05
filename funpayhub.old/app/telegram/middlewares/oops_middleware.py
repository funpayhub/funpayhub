from __future__ import annotations

from funpayhub.lib.translater import _en


__all__ = [
    'OopsMiddleware',
]

from typing import Any, TypeVar
from collections.abc import Callable, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject
from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter

from funpayhub.loggers import telegram as logger

from funpayhub.lib.translater import Translater


T = TypeVar('T')


class OopsMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        translater: Translater = data['translater']

        from funpayhub.lib.exceptions import TranslatableException

        try:
            return await handler(event, data)
        except TelegramRetryAfter as e:
            if isinstance(event, CallbackQuery):
                await event.answer(
                    translater.translate(
                        '🗣️👾⏳🤐\n'
                        'Бот отправил слишком много запросов Telegram, '
                        'и теперь нужно подождать {} сек.!\n'
                        'Подожди и попробуй снова.',
                    ).format(e.retry_after),
                    show_alert=True,
                )
                return None

        except TelegramBadRequest:
            logger.debug(_en('Telegram bad request!'), exc_info=True)
            pass

        except TranslatableException as e:
            logger.error(_en('Caught an error!'), exc_info=True)
            if isinstance(event, CallbackQuery):
                await event.answer(e.format_args(translater.translate(e.message)), show_alert=True)
            elif isinstance(event, Message):
                await event.answer(e.format_args(translater.translate(e.message)))

        except Exception:
            logger.error(_en('Caught an error!'), exc_info=True)
            if isinstance(event, CallbackQuery):
                await event.answer(
                    translater.translate(
                        '🫨🤬😵☠️\n'
                        'Упс! Произошла какая-то ошибка, которую никто не смог предвидеть!\n'
                        'Сообщи об этом разработчику! (Ну или живи с этим).',
                    ),
                    show_alert=True,
                )
            elif isinstance(event, Message):
                await event.reply(
                    translater.translate(
                        '🫨🤬😵☠️\n'
                        'Упс! Произошла какая-то ошибка, которую никто не смог предвидеть!\n'
                        'Сообщи об этом разработчику! (Ну или живи с этим).',
                    ),
                )
