from __future__ import annotations


__all__ = ['UnpackMiddleware']


from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery

from funpayhub.lib.telegram.callback_data import CallbackData
from funpayhub.lib.telegram.callback_data.hashinator import BadHashError, HashinatorT1000
from loggers import telegram as logger


class UnpackMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: CallbackQuery, data) -> None:
        callback_data = event.data
        if HashinatorT1000.is_hash(event.data):
            try:
                HashinatorT1000.unhash(event.data)
            except BadHashError:
                await event.answer(text='@whodax нагло стырил эту кнопку.', show_alert=True)
                return
        parsed = CallbackData.parse(callback_data)

        data['unpacked_callback'] = parsed
        event.__dict__.update({'__parsed__': parsed, 'data': callback_data})
        logger.debug(
            'Unpacked callback data: %s\nCallback: %s\nData: %s\nHistory: %s',
            event.data,
            parsed.identifier,
            parsed.data,
            parsed.history
        )
        await handler(event, data)
