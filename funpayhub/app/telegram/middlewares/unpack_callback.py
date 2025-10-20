from __future__ import annotations

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery

from funpayhub.lib.telegram.callback_data import CallbackData
from funpayhub.lib.telegram.callback_data.hashinator import BadHashError, HashinatorT1000


class UnpackMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: CallbackQuery, data):
        callback_data = event.data
        if HashinatorT1000.is_hash(event.data):
            try:
                HashinatorT1000.unhash(event.data)
            except BadHashError:
                await event.answer(text='Ваще не знаю че это за кнопка', show_alert=True)
                return
        parsed = CallbackData.parse(callback_data)

        print(f'Parsed: {callback_data}')
        print(f'Identifier: {parsed.identifier}')
        print(f'Data: {parsed.data}')
        print(f'History: {parsed.history}')

        data['unpacked_callback'] = parsed
        event.__dict__.update({'__parsed__': parsed, 'data': callback_data})
        await handler(event, data)
